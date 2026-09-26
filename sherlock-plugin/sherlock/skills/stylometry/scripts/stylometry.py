#!/usr/bin/env python3
"""Measured authorship verification for Sherlock.

Turns "do these two texts share an author?" into a score that can be
checked against texts whose authors are known.

Commands
  compare A.txt B.txt
      Similarity between two texts, the biggest function-word differences,
      and a within-text baseline (how similar each text is to itself).
      Needs no reference corpus.

  verify A.txt B.txt --corpus DIR --genre GENRE
      General Impostors test (Koppel & Winter 2014): in many rounds with
      random feature subsets, is B closer to A than to texts by other
      writers ("impostors") from the same genre? Score 0-1. If the genre
      has been calibrated, the score is converted to a likelihood ratio
      and a Sherlock conclusion.

  calibrate --corpus DIR --genre GENRE [--length WORDS]
      Runs the impostors test on same-author and different-author pairs
      drawn from the corpus, measures accuracy, and saves what each score
      means. Needs at least ~10 authors with 2+ texts each.

  markers Q.txt --corpus DIR --genre GENRE
      Finds words, phrases and masked sentence constructions that Q shares
      with each candidate author and that few other corpus authors use.
      Ranks candidates (adjusted for text length) and lists each leading
      candidate's strongest markers with example quotes.

  attribute Q.txt --corpus DIR --genre GENRE
      Ranks every candidate author for Q by combining the impostors test
      (each author's own other texts kept out of the pool) and the markers
      ranking. Reports the leader, its margin and its strongest markers.

  corpus-info --corpus DIR
      Summarizes the reference corpus and flags problems.

Corpus layout
  DIR/<genre>/<author>/<any name>.txt   one folder per author

Features (both topic-resistant)
  function words   relative frequencies of ~150 common grammatical words
  masked char 4-grams   text distortion (Stamatatos 2017): every word that is
      not a function word has its letters replaced by '*', then 4-character
      sequences are counted. Keeps punctuation, spacing and function-word
      habits; hides topic vocabulary.
"""
import argparse
import hashlib
import json
import math
import os
import random
import re
import statistics
import sys
from collections import Counter
from datetime import date
from pathlib import Path

WORD_RE = re.compile(r"(?:\b[A-Za-z]\.){2,}|[^\W\d_]+(?:['’][^\W\d_]+)*")

FUNCTION_WORDS = [
    "a", "about", "above", "after", "again", "against", "all", "almost", "along", "already", "also",
    "although", "always", "am", "among", "an", "and", "another", "any", "anyway", "are", "around", "as",
    "at", "be", "because", "been", "before", "behind", "being", "below", "between", "both", "but", "by",
    "can", "could", "did", "do", "does", "down", "during", "each", "either", "enough", "even", "ever",
    "every", "few", "for", "from", "had", "has", "have", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "however", "i", "if", "in", "into", "is", "it", "its", "itself", "just",
    "less", "like", "many", "may", "me", "might", "more", "most", "much", "must", "my", "myself",
    "neither", "never", "no", "nor", "not", "now", "of", "off", "often", "on", "once", "one", "only",
    "or", "other", "our", "ours", "out", "over", "own", "perhaps", "quite", "rather", "really", "same",
    "shall", "she", "should", "since", "so", "some", "still", "such", "than", "that", "the", "their",
    "them", "themselves", "then", "there", "these", "they", "this", "those", "though", "through", "thus",
    "to", "too", "toward", "towards", "under", "until", "up", "upon", "us", "very", "was", "we", "well",
    "were", "what", "when", "where", "whether", "which", "while", "who", "whom", "whose", "why", "will",
    "with", "within", "without", "would", "yet", "you", "your", "yours", "yourself",
]
FW_SET = set(FUNCTION_WORDS)
TOP_NGRAMS = 1000
PROVISIONAL_BELOW = 30  # calibrations built on fewer same-author pairs are indicative only


# ------------------------------------------------------------------ text handling

def normalize(text):
    """Remove differences that come from software, not the writer."""
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("–", "—")  # Word turns " - " into an en dash; treat both dash types alike
    return re.sub(r"[ \t]+", " ", re.sub(r"\s*\n\s*", "\n", text)).strip()


def truncate_words(text, limit):
    if not limit:
        return text
    for i, m in enumerate(WORD_RE.finditer(text), 1):
        if i == limit:
            return text[: m.end()]
    return text


def distort(text):
    def mask(m):
        w = m.group(0)
        return w if w.lower() in FW_SET else "*" * len(w)
    return re.sub(r"\d", "#", WORD_RE.sub(mask, text)).lower()


class Doc:
    def __init__(self, text, label, author=None, genre=None, limit=None):
        self.label, self.author, self.genre = label, author, genre
        text = truncate_words(normalize(text), limit)
        self.hash = hashlib.sha1(re.sub(r"\W+", "", text.lower()).encode()).hexdigest()
        self.text = text
        tokens = [t.lower().replace("’", "'") for t in WORD_RE.findall(text)]
        self.words = len(tokens)
        self.fw = Counter(t for t in tokens if t in FW_SET)
        d = distort(text)
        self.cg = Counter(d[i:i + 4] for i in range(len(d) - 3))
        self.cg_total = max(1, sum(self.cg.values()))
        self.vec = {}

    def build(self, ngram_feats):
        n = max(1, self.words)
        self.vec["fw"] = [self.fw.get(w, 0) / n for w in FUNCTION_WORDS]
        self.vec["cg"] = [self.cg.get(g, 0) / self.cg_total for g in ngram_feats]


def load_doc(path, limit=None, author=None, genre=None):
    return Doc(Path(path).read_text(encoding="utf-8", errors="replace"), str(path), author, genre, limit)


def choose_ngrams(docs, top=TOP_NGRAMS):
    total = Counter()
    for d in docs:
        for g, c in d.cg.items():
            total[g] += c / d.cg_total
    return [g for g, _ in total.most_common(top)]


# ------------------------------------------------------------------ similarity

def minmax(a, b, idx=None):
    idx = range(len(a)) if idx is None else idx
    num = den = 0.0
    for i in idx:
        x, y = a[i], b[i]
        if x < y:
            num += x; den += y
        else:
            num += y; den += x
    return num / den if den else 0.0


def impostors(a, b, pool, rng, iterations=100, per_round=10, rate=0.5):
    """Share of rounds (both directions) where A and B are closer to each other than to any impostor."""
    results = {}
    for kind in ("fw", "cg"):
        va, vb = a.vec[kind], b.vec[kind]
        n_feats = len(va)
        wins = 0
        for _ in range(iterations):
            idx = rng.sample(range(n_feats), max(1, int(n_feats * rate)))
            imps = rng.sample(pool, min(per_round, len(pool)))
            s_ab = minmax(va, vb, idx)
            wins += s_ab > max(minmax(va, im.vec[kind], idx) for im in imps)
            wins += s_ab > max(minmax(vb, im.vec[kind], idx) for im in imps)
        results[kind] = wins / (2 * iterations)
    results["score"] = (results["fw"] + results["cg"]) / 2
    return results


# ------------------------------------------------------------------ corpus

def load_corpus(root, genre, limit=None, exclude_hashes=()):
    base = Path(root) / genre
    if not base.is_dir():
        sys.exit(f"No genre folder '{genre}' in {root}. Run corpus-info to see what's there.")
    docs = []
    for author_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        for f in sorted(author_dir.glob("*.txt")):
            d = load_doc(f, limit, author_dir.name, genre)
            if d.words >= 50 and d.hash not in exclude_hashes:
                docs.append(d)
    return docs


def corpus_info(root):
    root = Path(root)
    if not root.is_dir():
        sys.exit(f"Corpus folder not found: {root}")
    print(f"Corpus: {root}")
    for genre_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        authors = {}
        for author_dir in sorted(p for p in genre_dir.iterdir() if p.is_dir()):
            files = list(author_dir.glob("*.txt"))
            words = [len(WORD_RE.findall(f.read_text(encoding="utf-8", errors="replace"))) for f in files]
            authors[author_dir.name] = words
        multi = sum(1 for w in authors.values() if len(w) >= 2)
        all_words = [w for ws in authors.values() for w in ws]
        print(f"\n  {genre_dir.name}: {len(authors)} authors, {len(all_words)} texts, "
              f"{multi} authors with 2+ texts")
        if all_words:
            print(f"    words per text: median {statistics.median(all_words):.0f}, "
                  f"range {min(all_words)}-{max(all_words)}")
        if len(authors) < 20:
            print("    ! fewer than 20 authors: impostor pool is small, scores will be noisy")
        if multi < 10:
            print("    ! fewer than 10 authors with 2+ texts: not enough for calibration")
        cal = genre_dir / "calibration.json"
        print(f"    calibration: {'yes (' + json.loads(cal.read_text())['date'] + ')' if cal.exists() else 'not yet'}")


# ------------------------------------------------------------------ calibration maths

def fit_logistic(xs, ys, ridge=0.1, iters=100):
    a = b = 0.0
    for _ in range(iters):
        g0 = g1 = h00 = h01 = h11 = 0.0
        for x, y in zip(xs, ys):
            p = 1 / (1 + math.exp(-max(-30, min(30, a + b * x))))
            w = p * (1 - p)
            g0 += y - p; g1 += (y - p) * x
            h00 += w; h01 += w * x; h11 += w * x * x
        g1 -= ridge * b; h11 += ridge; h00 += 1e-9
        det = h00 * h11 - h01 * h01
        if abs(det) < 1e-12:
            break
        a += (h11 * g0 - h01 * g1) / det
        b += (h00 * g1 - h01 * g0) / det
    return a, b


def auc(same, diff):
    wins = sum((s > d) + 0.5 * (s == d) for s in same for d in diff)
    return wins / (len(same) * len(diff)) if same and diff else float("nan")


def likelihood_ratio(score, cal):
    logit = cal["a"] + cal["b"] * score
    prior_logit = math.log(cal["prior"] / (1 - cal["prior"]))
    # A calibration set of n pairs per side can't justify a ratio much beyond n: cap it there.
    cap = min(cal["n_same"], cal["n_diff"]) + 1
    return max(1 / cap, min(cap, math.exp(logit - prior_logit)))


def verbal(lr):
    if lr >= 10:
        return "strong support for same author"
    if lr >= 3:
        return "moderate support for same author"
    if lr >= 1.5:
        return "limited support for same author"
    if lr > 1 / 1.5:
        return "no support either way"
    if lr > 1 / 3:
        return "limited support for different authors"
    if lr > 1 / 10:
        return "moderate support for different authors"
    return "strong support for different authors"


# ------------------------------------------------------------------ commands

def cmd_compare(args):
    a, b = load_doc(args.a), load_doc(args.b)
    feats = choose_ngrams([a, b])
    for d in (a, b):
        d.build(feats)
    print(f"A: {a.label} ({a.words} words)\nB: {b.label} ({b.words} words)")
    print("\nWhole-text similarity (min-max, 0 = nothing shared, 1 = identical profiles):")
    print(f"  function words:      {minmax(a.vec['fw'], b.vec['fw']):.3f}")
    print(f"  masked char 4-grams: {minmax(a.vec['cg'], b.vec['cg']):.3f}")
    print("  On their own these numbers mean little; use verify with a corpus to learn what is typical.")

    print("\nBiggest function-word differences (per 1,000 words):")
    rows = []
    for w in FUNCTION_WORDS:
        ra, rb = 1000 * a.fw.get(w, 0) / max(1, a.words), 1000 * b.fw.get(w, 0) / max(1, b.words)
        if ra + rb >= 2:
            rows.append((abs(ra - rb) / math.sqrt(ra + rb + 1), w, ra, rb))
    for _, w, ra, rb in sorted(rows, reverse=True)[:15]:
        print(f"  {w:10} A {ra:6.1f}   B {rb:6.1f}")

    size = args.chunk
    chunks = {}
    for name, d in (("A", a), ("B", b)):
        spans = [m.end() for i, m in enumerate(WORD_RE.finditer(d.text), 1) if i % size == 0]
        starts = [0] + spans
        pieces = [d.text[s:e] for s, e in zip(starts, spans)]
        chunks[name] = [Doc(p, f"{name}{i}") for i, p in enumerate(pieces, 1)]
    print(f"\nWithin-text baseline ({size}-word chunks: A has {len(chunks['A'])}, B has {len(chunks['B'])}):")
    if len(chunks["A"]) < 2 or len(chunks["B"]) < 2:
        print(f"  Each text needs at least {2 * size} words for this check (use --chunk to lower the chunk size).")
        return
    all_chunks = chunks["A"] + chunks["B"]
    cfeats = choose_ngrams(all_chunks, 500)
    for c in all_chunks:
        c.build(cfeats)
    for kind, label in (("fw", "function words"), ("cg", "masked char 4-grams")):
        def sims(xs, ys, same):
            return [minmax(x.vec[kind], y.vec[kind]) for i, x in enumerate(xs) for j, y in enumerate(ys) if not same or i < j]
        wa, wb, between = sims(chunks["A"], chunks["A"], True), sims(chunks["B"], chunks["B"], True), sims(chunks["A"], chunks["B"], False)
        within = wa + wb
        ratio = statistics.mean(between) / statistics.mean(within)
        print(f"  {label}: within A {statistics.mean(wa):.3f}, within B {statistics.mean(wb):.3f}, "
              f"between A and B {statistics.mean(between):.3f}  (between / within = {ratio:.2f})")
    print("  A ratio near 1.00 means A's chunks resemble B's about as much as they resemble each other.\n"
          "  Lower ratios mean the texts differ more than each text varies internally. Genre and topic\n"
          "  differences also lower the ratio, so treat this as a diagnostic, not a conclusion.")


def cmd_verify(args):
    rng = random.Random(args.seed)
    cal_path = Path(args.corpus) / args.genre / "calibration.json"
    cal = json.loads(cal_path.read_text()) if cal_path.exists() else None
    limit = args.length or (cal["length"] if cal else None)
    a, b = load_doc(args.a, limit), load_doc(args.b, limit)
    pool = load_corpus(args.corpus, args.genre, limit or max(a.words, b.words), {a.hash, b.hash})
    pool = [d for d in pool if d.author not in set(args.exclude_author or [])]
    if len(pool) < 10:
        sys.exit(f"Only {len(pool)} usable impostor texts in '{args.genre}'; need at least 10 (ideally 50+).")
    feats = choose_ngrams(pool + [a, b])
    for d in pool + [a, b]:
        d.build(feats)
    # Drop impostors that are near-copies of the case texts (e.g. the same essay saved twice).
    pool = [d for d in pool if max(minmax(d.vec["cg"], a.vec["cg"]), minmax(d.vec["cg"], b.vec["cg"])) < 0.9]
    r = impostors(a, b, pool, rng, args.iterations, args.per_round)

    print(f"A: {a.label} ({a.words} words analyzed)\nB: {b.label} ({b.words} words analyzed)")
    print(f"Impostor pool: {len(pool)} texts by {len({d.author for d in pool})} other writers, genre '{args.genre}'")
    print(f"\nImpostors score: {r['score']:.2f}   (function words {r['fw']:.2f}, masked char 4-grams {r['cg']:.2f})")
    print("  = share of rounds in which A and B were closer to each other than to every impostor.")
    if cal:
        lr = likelihood_ratio(r["score"], cal)
        print(f"\nCalibrated on {cal['n_same']} same-author and {cal['n_diff']} different-author pairs "
              f"({cal['length']} words each; accuracy {cal['accuracy']:.0%}, AUC {cal['auc']:.2f}).")
        print(f"  Likelihood ratio: {lr:.2f}  (how many times more likely this score is if the author is the same)")
        if cal["n_same"] < PROVISIONAL_BELOW:
            print(f"  PROVISIONAL calibration (only {cal['n_same']} same-author pairs; {PROVISIONAL_BELOW}+ needed).")
            print("  Report the ratio as indicative only; it must not anchor the case conclusion.")
            if lr < 1:
                print("  Low scores are NOT reported as support for different authors under a provisional calibration:")
                print("  in validation, writers whose style varies by story scored low with themselves.")
                print("  Sherlock conclusion: no conclusion from this score")
            else:
                print(f"  Sherlock conclusion (indicative): {verbal(lr)}")
        else:
            print(f"  Sherlock conclusion: {verbal(lr)}")
        if abs(max(a.words, b.words) - cal["length"]) > 0.5 * cal["length"] or min(a.words, b.words) < 0.5 * cal["length"]:
            print(f"  ! Case texts differ a lot from the calibrated length ({cal['length']} words); "
                  "re-run calibrate with --length near the case length.")
    else:
        print("\nThis genre is not calibrated yet, so the score can't be turned into a conclusion.")
        print("  As a description only: near 1 = B looked more like A than any impostor almost every round;")
        print("  near 0 = some impostor almost always looked closer. Run calibrate to learn what scores mean.")
    if args.json:
        print(json.dumps({"a": a.label, "b": b.label, "result": r, "pool": len(pool),
                          "likelihood_ratio": likelihood_ratio(r["score"], cal) if cal else None}, indent=2))


def cmd_calibrate(args):
    rng = random.Random(args.seed)
    docs = load_corpus(args.corpus, args.genre, args.length)
    by_author = {}
    for d in docs:
        by_author.setdefault(d.author, []).append(d)
    multi = [au for au, ds in by_author.items() if len(ds) >= 2]
    if len(by_author) < 12 or len(multi) < 5:
        sys.exit(f"Need at least 12 authors and 5 with 2+ texts; found {len(by_author)} authors, {len(multi)} with 2+.")
    feats = choose_ngrams(docs)
    for d in docs:
        d.build(feats)

    same_pairs = []
    for au in multi:
        ds = by_author[au]
        pairs = [(x, y) for i, x in enumerate(ds) for y in ds[i + 1:]]
        rng.shuffle(pairs)
        same_pairs += pairs[:3]
    rng.shuffle(same_pairs)
    same_pairs = same_pairs[: args.pairs]
    diff_pairs = []
    while len(diff_pairs) < len(same_pairs):
        x, y = rng.sample(docs, 2)
        if x.author != y.author:
            diff_pairs.append((x, y))

    scores = {"same": [], "diff": []}
    total = len(same_pairs) + len(diff_pairs)
    for label, pairs in (("same", same_pairs), ("diff", diff_pairs)):
        for x, y in pairs:
            pool = [d for d in docs if d.author not in (x.author, y.author)]
            pool = rng.sample(pool, min(args.pool, len(pool)))
            scores[label].append(impostors(x, y, pool, rng, args.iterations, args.per_round)["score"])
            done = len(scores["same"]) + len(scores["diff"])
            if done % 10 == 0:
                print(f"  {done}/{total} pairs scored", file=sys.stderr)

    xs = scores["same"] + scores["diff"]
    ys = [1] * len(scores["same"]) + [0] * len(scores["diff"])
    a_, b_ = fit_logistic(xs, ys)
    prior = len(scores["same"]) / len(xs)
    cal = {"genre": args.genre, "length": args.length, "date": str(date.today()), "a": a_, "b": b_, "prior": prior,
           "n_same": len(scores["same"]), "n_diff": len(scores["diff"]),
           "auc": auc(scores["same"], scores["diff"]), "iterations": args.iterations, "per_round": args.per_round}
    cal["accuracy"] = sum((1 / (1 + math.exp(-(a_ + b_ * x))) >= 0.5) == bool(y) for x, y in zip(xs, ys)) / len(xs)
    out = Path(args.corpus) / args.genre / "calibration.json"
    out.write_text(json.dumps(cal, indent=2))

    print(f"\nCalibration for '{args.genre}' at {args.length} words per text")
    print(f"  pairs: {cal['n_same']} same-author, {cal['n_diff']} different-author")
    print(f"  mean score: same {statistics.mean(scores['same']):.2f}, different {statistics.mean(scores['diff']):.2f}")
    print(f"  AUC {cal['auc']:.2f} (0.5 = guessing, 1.0 = perfect)   accuracy {cal['accuracy']:.0%}")
    print("\n  score -> likelihood ratio -> Sherlock conclusion")
    for s in [i / 10 for i in range(11)]:
        lr = likelihood_ratio(s, cal)
        print(f"   {s:.1f}  ->  {lr:8.2f}  ->  {verbal(lr)}")
    if cal["n_same"] < PROVISIONAL_BELOW:
        print(f"\n  PROVISIONAL: only {cal['n_same']} same-author pairs ({PROVISIONAL_BELOW}+ needed). These are in-sample figures;")
        print("  validate by holding out one writer at a time before trusting the ratios.")
    print(f"\nSaved to {out}")


# ------------------------------------------------------------------ distinctive markers

PUNCT_RE = re.compile(r'[,.;:!?"()—…]|-{2,}|\.{3,}')
TOKEN_RE = re.compile(r"(?:\b[A-Za-z]\.){2,}|[^\W\d_]+(?:'[^\W\d_]+)*|\.{3,}|-{2,}|[,.;:!?\"()—…]")
SENT_END = {".", "!", "?", "…", "..."}


def marker_tokens(text):
    """Tokens with character offsets. Adds <S> at sentence starts and masks proper names as <N>."""
    text = normalize(text)
    out = [("<S>", 0)]
    prev = "<S>"
    for m in TOKEN_RE.finditer(text):
        tok, pos = m.group(0), m.start()
        if tok[0].isalpha() or tok[0].isdigit():
            gap = text[out[-1][1]:pos] if out else ""
            starts_sentence = prev in ("<S>",) or prev in SENT_END or (prev == '"' and len(out) > 1 and out[-2][0] in SENT_END | {"<S>"})
            if "\n" in gap and prev not in ("<S>",):
                out.append(("<S>", pos)); starts_sentence = True
            if tok[0].isupper() and not starts_sentence and tok != "I" and not tok.startswith("I'") and "." not in tok:
                tok = "<N>"
            else:
                tok = tok.lower()
        out.append((tok, pos))
        if tok in SENT_END:
            out.append(("<S>", pos + len(m.group(0))))
            prev = "<S>"
        else:
            prev = tok
    return out, text


def marker_items(text):
    """Map each candidate marker to (count, first char offset). Word phrases 1-4 tokens; skeletons 3-5."""
    toks, norm = marker_tokens(text)
    words = [t for t, _ in toks]
    items = {}

    def add(key, pos):
        if key in items:
            c, first, allpos = items[key]
            allpos.append(pos)
            items[key] = (c + 1, first, allpos)
        else:
            items[key] = (1, pos, [pos])

    skel = [t if (t in FW_SET or t in ("<S>", "<N>") or PUNCT_RE.fullmatch(t)) else "*" for t in words]
    for i in range(len(words)):
        for n in (1, 2, 3, 4):
            gram = words[i:i + n]
            if len(gram) < n:
                break
            content = [g for g in gram if g not in ("<S>", "<N>") and not PUNCT_RE.fullmatch(g)]
            if not content:
                continue
            if n == 1 and (gram[0] in FW_SET or len(gram[0]) < 4):
                continue
            if n > 1 and all(g in FW_SET for g in content) and len(content) < 2:
                continue
            add(("phrase", " ".join(gram)), toks[i][1])
        for n in (3, 4, 5):
            gram = skel[i:i + n]
            if len(gram) < n:
                break
            if sum(g != "*" for g in gram) < 2 or all(g == "*" for g in gram[1:]):
                continue
            if not any(g in FW_SET for g in gram) and "<N>" not in gram:
                continue
            add(("pattern", " ".join(gram)), toks[i][1])
    return items, norm


def snippet(text, pos, width=70):
    start = max(0, text.rfind(" ", 0, max(0, pos - 25)) + 1)
    s = text[start:start + width].replace("\n", " ")
    return ("…" if start else "") + s.strip() + "…"


def display(kind, key):
    return key.replace("<S>", "[sentence start]").replace("<N>", "[Name]")


def text_hash(text):
    return hashlib.sha1(re.sub(r"\W+", "", normalize(text).lower()).encode()).hexdigest()


def load_authors(base, q_hash, excluded=()):
    """{author: [(file name, text, path)]} for a genre folder, leaving out the questioned text itself."""
    authors = {}
    for author_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        if author_dir.name in excluded:
            continue
        texts = []
        for f in sorted(author_dir.glob("*.txt")):
            t = f.read_text(encoding="utf-8", errors="replace")
            if text_hash(t) != q_hash:
                texts.append((f.name, t, f))
        if texts:
            authors[author_dir.name] = texts
    return authors


def marker_ranking(q_text, authors, max_share=0.1):
    """Score each author on rare markers shared with Q. Returns (results sorted by z, profiles, q_items, q_norm)."""
    q_items, q_norm = marker_items(q_text)
    profiles = {}
    for au, texts in authors.items():
        merged = {}
        for name, t, _ in texts:
            its, norm = marker_items(t)
            for k, (c, p, _) in its.items():
                if k not in merged:
                    merged[k] = [0, name, norm, p]
                merged[k][0] += c
        profiles[au] = merged
    doc_freq = Counter()
    for prof in profiles.values():
        for k in prof:
            if k in q_items:
                doc_freq[k] += 1

    results = []
    for au, prof in profiles.items():
        n_others = len(profiles) - 1
        max_df = max(0, int(max_share * n_others))
        found = []
        for k in q_items.keys() & prof.keys():
            df_others = doc_freq[k] - 1
            if df_others > max_df:
                continue
            reps = min(q_items[k][0], prof[k][0])
            weight = math.log2((n_others + 1) / (df_others + 1)) * (1 + math.log2(reps))
            found.append((weight, df_others, reps, k))
        found.sort(key=lambda x: (-x[0], -len(x[3][1])))
        # Variants of one habit ("said [Name]", ', " said', ', " * [Name]') occur at the same places in Q.
        # A marker whose Q occurrences mostly overlap a stronger kept marker's is the same habit: skip it,
        # so one habit isn't listed many times.
        kept, covered = [], []
        for f in found:
            spots = q_items[f[3]][2]
            hits = sum(1 for s in spots if any(abs(s - c) < 30 for c in covered))
            if hits >= max(1, len(spots) / 2):
                continue
            kept.append(f)
            covered.extend(spots)
        # Ranking uses every shared rare marker (a habit that recurs in many forms is real evidence, and all
        # candidates are treated alike); the displayed list uses the de-duplicated markers for readability.
        results.append({"author": au, "score": sum(f[0] for f in found), "exclusive": sum(1 for f in kept if f[1] == 0),
                        "markers": kept, "words": sum(len(WORD_RE.findall(t)) for _, t, _ in authors[au])})

    # Longer candidate texts share more items by chance: compare each score with what its length predicts.
    xs = [math.log(max(2, r["words"])) for r in results]; ys = [r["score"] for r in results]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs) or 1
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    resid = [y - (my + slope * (x - mx)) for x, y in zip(xs, ys)]
    sd = statistics.pstdev(resid) or 1
    for r, e in zip(results, resid):
        r["z"] = e / sd
    results.sort(key=lambda r: -r["z"])
    return results, profiles, q_items, q_norm


def print_marker_list(r, profiles, q_items, q_norm, top):
    print(f"\n=== {r['author']}: top shared rare markers")
    if not r["markers"]:
        print("  none")
    for weight, df, reps, (kind, key) in r["markers"][:top]:
        prof = profiles[r["author"]][(kind, key)]
        rarity = "no other author" if df == 0 else f"{df} other author{'s' if df > 1 else ''}"
        print(f"  [{kind}] {display(kind, key)!r}  (Q {q_items[(kind, key)][0]}x, candidate {prof[0]}x; {rarity})")
        print(f"      Q: {snippet(q_norm, q_items[(kind, key)][1])}")
        print(f"      C: {snippet(prof[2], prof[3])}   [{prof[1]}]")


MARKER_ADVICE = ("Markers are candidates: read each in context. Discount topic words, character names that slipped\n"
                 "through, and phrases from a shared prompt. Construction patterns and function-word phrases are the\n"
                 "most reliable signs of an individual writer. Don't dismiss a strong match as 'just topic' without evidence.")


def genre_dir(args):
    base = Path(args.corpus) / args.genre
    if not base.is_dir():
        sys.exit(f"No genre folder '{args.genre}' in {args.corpus}.")
    return base


def cmd_markers(args):
    q_text = Path(args.q).read_text(encoding="utf-8", errors="replace")
    base = genre_dir(args)
    authors = load_authors(base, text_hash(q_text), set(args.exclude_author or []))
    if len(authors) < 4:
        sys.exit(f"Need at least 4 authors in '{args.genre}' to judge rarity; found {len(authors)}.")
    results, profiles, q_items, q_norm = marker_ranking(q_text, authors, args.max_share)

    print(f"Questioned text: {args.q} ({len(WORD_RE.findall(q_text))} words)")
    print(f"Corpus: {base} ({len(profiles)} authors). A marker counts as rare if at most "
          f"{args.max_share:.0%} of the other authors use it.\n")
    print(f"{'rank':4} {'author':38} {'words':>6} {'exclusive':>9} {'score':>7} {'vs length':>9}")
    for i, r in enumerate(results, 1):
        print(f"{i:4} {r['author']:38} {r['words']:6} {r['exclusive']:9} {r['score']:7.1f} {r['z']:+9.2f}")
    print("\n'exclusive' = markers shared with Q that no other author uses. 'vs length' = how far the score is\n"
          "above (+) or below (-) what the candidate's length predicts, in standard deviations.")
    show = [r for r in results if r["author"] == args.candidate] if args.candidate else results[: args.show]
    for r in show:
        print_marker_list(r, profiles, q_items, q_norm, args.top)
    print("\n" + MARKER_ADVICE)
    if args.json:
        print(json.dumps([{k: v for k, v in r.items() if k != "markers"} | {"markers": [
            {"kind": m[3][0], "marker": m[3][1], "weight": round(m[0], 2), "other_authors": m[1], "repeats": m[2]}
            for m in r["markers"][:50]]} for r in results], indent=2))


def standardize(scores):
    mean = statistics.mean(scores.values())
    sd = statistics.pstdev(scores.values()) or 1
    return {k: (v - mean) / sd for k, v in scores.items()}


def cmd_attribute(args):
    q_text = Path(args.q).read_text(encoding="utf-8", errors="replace")
    base = genre_dir(args)
    authors = load_authors(base, text_hash(q_text), set(args.exclude_author or []))
    if len(authors) < 5:
        sys.exit(f"Need at least 5 candidate authors in '{args.genre}'; found {len(authors)}.")

    # 1. Impostors: for each candidate author, Q against each of their texts, with every text by that author
    #    left out of the pool (so an author's other texts never compete against them). Best text counts.
    q = Doc(q_text, args.q, limit=args.length)
    docs = {au: [Doc(t, name, author=au, limit=args.length) for name, t, _ in texts] for au, texts in authors.items()}
    every = [d for ds in docs.values() for d in ds]
    feats = choose_ngrams(every + [q])
    for d in every + [q]:
        d.build(feats)
    imp, imp_text = {}, {}
    for au, ds in docs.items():
        pool = [d for d in every if d.author != au]
        best = None
        for d in ds:
            s = impostors(q, d, pool, random.Random(args.seed), args.iterations, args.per_round)["score"]
            if best is None or s > best[0]:
                best = (s, d.label)
        imp[au], imp_text[au] = best

    # 2. Markers ranking, 3. combine: standardize each method across candidates, then add.
    mresults, profiles, q_items, q_norm = marker_ranking(q_text, authors, args.max_share)
    mz = {r["author"]: r["z"] for r in mresults}
    zi = standardize(imp)
    combined = {au: zi[au] + mz[au] for au in authors}
    order = sorted(authors, key=lambda au: -combined[au])

    print(f"Questioned text: {args.q} ({len(WORD_RE.findall(q_text))} words; {q.words} used for impostors)")
    print(f"Corpus: {base} ({len(authors)} candidate authors, {len(every)} texts)")
    print(f"Impostors: {args.iterations} rounds per text, texts cut to {args.length} words; "
          f"markers: rare = used by at most {args.max_share:.0%} of other authors\n")
    print(f"{'rank':4} {'author':38} {'texts':>5} {'impostors':>9} {'markers z':>9} {'combined':>9}")
    for i, au in enumerate(order, 1):
        print(f"{i:4} {au:38} {len(authors[au]):5} {imp[au]:9.2f} {mz[au]:+9.2f} {combined[au]:+9.2f}")
    lead, second = order[0], order[1]
    margin = combined[lead] - combined[second]
    print(f"\nLeader: {lead}  (best matching text: {imp_text[lead]})")
    print(f"Margin over #2 ({second}): {margin:.2f}")
    agree = imp[lead] == max(imp.values()) and mz[lead] == max(mz.values())
    print(f"Both methods rank the leader first: {'yes' if agree else 'no'}")

    for au in order[: args.show]:
        r = next(x for x in mresults if x["author"] == au)
        print_marker_list(r, profiles, q_items, q_norm, args.top)

    print("\nHow to read this")
    print("  - Someone always ranks first, even when the true author isn't in the corpus. A match needs a clear\n"
          "    margin AND distinctive shared markers (unusual constructions or idioms, several of them).")
    print("  - A leader that tops both methods with strong markers is the pattern seen in confirmed matches.\n"
          "    A leader with a small margin or only generic markers is not evidence of authorship.")
    print("  - Validation so far (fiction, 16 authors, 8 known texts): the combined ranking put the true author\n"
          "    first 5 of 8 times and in the top 3 6 of 8 times. It is uncalibrated: it ranks, it doesn't\n"
          "    give a likelihood ratio.")
    print("\n" + MARKER_ADVICE)
    if args.json:
        print(json.dumps([{"author": au, "texts": len(authors[au]), "impostors": round(imp[au], 3),
                           "best_text": imp_text[au], "markers_z": round(mz[au], 3), "combined": round(combined[au], 3)}
                          for au in order], indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    corpus_default = os.environ.get("SHERLOCK_CORPUS", "corpus")  # or pass --corpus

    p = sub.add_parser("compare", help="similarity and within-text baseline, no corpus needed")
    p.add_argument("a"); p.add_argument("b")
    p.add_argument("--chunk", type=int, default=250, help="words per chunk for the baseline (default 250)")
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser("verify", help="impostors test against a reference corpus")
    p.add_argument("a"); p.add_argument("b")
    p.add_argument("--corpus", default=corpus_default)
    p.add_argument("--genre", required=True)
    p.add_argument("--length", type=int, help="truncate all texts to this many words (default: calibrated length)")
    p.add_argument("--iterations", type=int, default=200)
    p.add_argument("--per-round", type=int, default=10)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--exclude-author", action="append",
                   help="corpus author folder to leave out of the impostor pool (repeatable); "
                        "use when a case text's author is also in the corpus")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("calibrate", help="learn what scores mean from texts with known authors")
    p.add_argument("--corpus", default=corpus_default)
    p.add_argument("--genre", required=True)
    p.add_argument("--length", type=int, default=500, help="words per text, match your usual case length (default 500)")
    p.add_argument("--pairs", type=int, default=100, help="max same-author pairs (same number of different pairs)")
    p.add_argument("--pool", type=int, default=50, help="impostors sampled per pair")
    p.add_argument("--iterations", type=int, default=100)
    p.add_argument("--per-round", type=int, default=10)
    p.add_argument("--seed", type=int, default=1)
    p.set_defaults(func=cmd_calibrate)

    p = sub.add_parser("markers", help="find rare words, phrases and constructions Q shares with each candidate")
    p.add_argument("q")
    p.add_argument("--corpus", default=corpus_default)
    p.add_argument("--genre", required=True)
    p.add_argument("--candidate", help="show markers for this author folder only")
    p.add_argument("--show", type=int, default=2, help="how many top-ranked authors to list markers for (default 2)")
    p.add_argument("--top", type=int, default=12, help="markers to list per author (default 12)")
    p.add_argument("--max-share", type=float, default=0.1,
                   help="a marker is rare if at most this share of other authors use it (default 0.1)")
    p.add_argument("--exclude-author", action="append", help="author folder to leave out entirely (repeatable)")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_markers)

    p = sub.add_parser("attribute", help="rank candidate authors for Q by impostors + markers combined")
    p.add_argument("q")
    p.add_argument("--corpus", default=corpus_default)
    p.add_argument("--genre", required=True)
    p.add_argument("--length", type=int, default=1000, help="words per text for the impostors test (default 1000)")
    p.add_argument("--iterations", type=int, default=150)
    p.add_argument("--per-round", type=int, default=10)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--max-share", type=float, default=0.1)
    p.add_argument("--show", type=int, default=2, help="how many top candidates to list markers for (default 2)")
    p.add_argument("--top", type=int, default=8, help="markers to list per candidate (default 8)")
    p.add_argument("--exclude-author", action="append", help="author folder to leave out entirely (repeatable)")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_attribute)

    p = sub.add_parser("corpus-info", help="summarize the reference corpus")
    p.add_argument("--corpus", default=corpus_default)
    p.set_defaults(func=lambda a: corpus_info(a.corpus))

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
