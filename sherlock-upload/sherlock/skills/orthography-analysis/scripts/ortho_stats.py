#!/usr/bin/env python3
"""Orthography measurements for forensic authorship comparison.

Measures capitalization habits, emoji and emoticon use, word and function-word
frequencies, and misspelling / malapropism candidates.

Every misspelling or malapropism hit is a CANDIDATE for human review.

Usage:
    python3 ortho_stats.py FILE [FILE ...] [--dict PATH] [--json]
"""
import argparse
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

# Initialisms such as U.S. or e.g. count as one word, not separate letters.
WORD_RE = re.compile(r"(?:\b[A-Za-z]\.){2,}|[^\W\d_]+(?:['’][^\W\d_]+)*")  # letters incl. accented (é, è, ñ)

ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "prof", "st", "vs", "etc", "jr", "sr", "inc",
    "ltd", "no", "vol", "fig", "approx", "dept", "est", "ch", "pp", "p",
}
INITIALISM_END = re.compile(r"(?:\b[A-Za-z]\.){2,}$")


def split_flat(flat):
    """Split one block of text into sentences, without breaking after Mr. or U.S."""
    parts = re.split(r"(?<=[.!?…])\s+", flat)
    sentences, buffer = [], ""
    for i, part in enumerate(parts):
        buffer = f"{buffer} {part}" if buffer else part
        following = parts[i + 1] if i + 1 < len(parts) else ""
        last = re.search(r"([A-Za-z]+)\.$", buffer)
        if following and last and last.group(1).lower() in ABBREVIATIONS:
            continue
        if following and INITIALISM_END.search(buffer) and not following[0].isupper():
            continue  # "the U.S. have been" is one sentence; "the U.S. Then" is two
        sentences.append(buffer)
        buffer = ""
    if buffer:
        sentences.append(buffer)
    return sentences

EMOJI_BASE = "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF]"
# One emoji = a base symbol plus any skin-tone / variation modifiers and ZWJ-joined parts.
EMOJI_RE = re.compile(EMOJI_BASE + "(?:[\U0001F3FB-\U0001F3FF️]|‍" + EMOJI_BASE + ")*")
EMOTICON_RE = re.compile(r"(?<!\w)(?:[:;=8][-'^o]?[)(DPpOo/\\|\]\[*]|<3|\^_\^|xD|XD|:'\(|-_-|¯\\_\(ツ\)_/¯)(?!\w)")

# Classic stylometric function-word list (Mosteller & Wallace style, extended).
FUNCTION_WORDS = [
    "the", "a", "an", "and", "but", "or", "so", "of", "to", "in", "on", "at", "by", "for",
    "with", "from", "about", "into", "upon", "as", "than", "that", "which", "who", "what",
    "this", "there", "then", "if", "because", "while", "though", "although", "just", "very",
    "really", "also", "not", "no", "all", "any", "some", "i", "me", "my", "you", "your",
    "he", "she", "it", "we", "they", "is", "was", "be", "been", "have", "had", "do", "can",
    "would", "will", "should", "could", "might", "must", "shall", "one", "only", "even",
]

MISSING_APOSTROPHE = {
    "dont", "cant", "wont", "im", "ive", "youre", "thats", "doesnt", "didnt", "isnt", "arent",
    "wasnt", "werent", "couldnt", "shouldnt", "wouldnt", "hes", "shes", "theyre", "theyve",
    "weve", "youve", "whats", "hasnt", "havent", "hadnt", "aint", "youll",
}

CONFUSABLES = {
    "their/there/they're": r"\b(?:their|there|they'?re)\b",
    "your/you're": r"\b(?:your|you'?re)\b",
    "its/it's": r"\b(?:its|it'?s)\b",
    "then/than": r"\b(?:then|than)\b",
    "to/too/two": r"\b(?:to|too|two)\b",
    "lose/loose": r"\b(?:lose|loose)\b",
    "affect/effect": r"\b(?:affect|effect)s?\b",
    "accept/except": r"\b(?:accept|except)\b",
    "whose/who's": r"\b(?:whose|who'?s)\b",
    "were/where/we're": r"\b(?:were|where|we'?re)\b",
}
MALAPROPISM_CANDIDATES = {
    "could/should/would of": r"\b(?:could|should|would|must|might) of\b",
    "for all intensive purposes": r"\bfor all intensive purposes\b",
    "irregardless": r"\birregardless\b",
    "supposably": r"\bsupposably\b",
    "on accident": r"\bon accident\b",
    "nip it in the butt": r"\bnip (?:it|this|that) in the butt\b",
    "case and point": r"\bcase and point\b",
    "one in the same": r"\bone in the same\b",
    "escape goat": r"\bescape ?goat\b",
    "mute point": r"\bmute point\b",
    "peak/pique interest": r"\bpeak(?:ed|s)? (?:my|your|his|her|their|our) interest\b",
    "tow the line": r"\btow(?:ed|ing|s)? the line\b",
    "Old-timer's disease": r"\bold ?timers? disease\b",
    "expresso": r"\bexpresso\b",
    "pacifically (specifically)": r"\bpacifically\b",
    "prostrate (prostate)": r"\bprostrate cancer\b",
    "wreckless": r"\bwreckless\b",
}


EMPHASIS_PATTERNS = {
    "stretched words (sooo, nooo)": r"\b[A-Za-z]*([A-Za-z])\1{2,}[A-Za-z]*\b",
    "repeated !": r"!{2,}",
    "repeated ?": r"\?{2,}",
    "?! or !? combos": r"[?!]*(?:\?!|!\?)[?!]*",
    "repeated commas (,, or ,,,)": r",{2,}",
    "asterisk emphasis *word*": r"(?<![\w*])\*[^*\s][^*\n]{0,40}?\*(?![\w*])",
    "underscore emphasis _word_": r"(?<![\w_])_[^_\s][^_\n]{0,40}?_(?![\w_])",
    "tilde ~": r"~",
    "clap emphasis (word 👏 word)": r"\w+ ?👏 ?\w+",
    "spaced letters (s o  m u c h)": r"\b(?:[A-Za-z] ){3,}[A-Za-z]\b",
    "scare quotes around one word": r"[\"“][A-Za-z]+[\"”]",
}
NOT_STRETCHED = {"www", "zzz", "hmm", "mmm", "shh", "brrr", "ahhh"}

FORMAT_PATTERNS = {
    "numbers": {
        "digits 1-9 standing alone": r"(?<![\d.,:/$£€-])\b[1-9]\b(?![\d.,:/%])",
        "spelled one-nine": r"\b(?:one|two|three|four|five|six|seven|eight|nine)\b",
        "thousands with comma (1,000)": r"\b\d{1,3}(?:,\d{3})+\b",
        "thousands without comma (1000+, not years)": r"(?<![\d,.$-])\b(?!(?:19|20)\d\d\b)[1-9]\d{3,}\b(?![,-]\d)",
        "k shorthand (5k)": r"\b\d+(?:\.\d+)?k\b",
        "ordinals with digits (1st, 22nd)": r"\b\d+(?:st|nd|rd|th)\b",
    },
    "times": {
        "3pm (no space, lowercase)": r"\b\d{1,2}(?::\d{2})?(?:am|pm)\b",
        "3 pm (space, lowercase)": r"\b\d{1,2}(?::\d{2})? (?:am|pm)\b",
        "3PM / 3 PM (uppercase)": r"\b\d{1,2}(?::\d{2})? ?(?:AM|PM)\b",
        "3 p.m. / 3 a.m. (dotted)": r"\b\d{1,2}(?::\d{2})? ?[ap]\.m\.",
        "24-hour (15:00)": r"\b(?:1[3-9]|2[0-3]):[0-5]\d\b",
        "o'clock": r"\bo['’]clock\b",
    },
    "dates": {
        "numeric with slashes (9/26/26)": r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b",
        "numeric with dots or dashes (26.09.2026)": r"\b\d{1,2}[.-]\d{1,2}[.-]\d{2,4}\b",
        "ISO (2026-09-26)": r"\b\d{4}-\d{2}-\d{2}\b",
        "month first (Sept 26, September 26th)": r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.? \d{1,2}(?:st|nd|rd|th)?\b",
        "day first (26 September, 26th of Sept)": r"\b\d{1,2}(?:st|nd|rd|th)?(?: of)? (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\b",
    },
    "money": {
        "$5 (symbol before)": r"[$£€]\s?\d",
        "$5.00 (always cents)": r"[$£€]\s?\d+\.\d{2}\b",
        "5$ / 5€ (symbol after)": r"\b\d+(?:[.,]\d+)?\s?[$£€]",
        "5 dollars / bucks (words)": r"\b\d+(?:\.\d+)? ?(?:dollars?|bucks|quid|pounds?|euros?|grand)\b",
        "USD / GBP codes": r"\b(?:USD|GBP|EUR|CAD|AUD)\b",
    },
    "other symbols": {
        "percent sign %": r"\d+(?:\.\d+)? ?%",
        "word percent / per cent": r"\b(?:percent|per cent)\b",
        "ampersand &": r"&",
        "slash pairs (and/or, him/her)": r"\b[A-Za-z]+/[A-Za-z]+\b",
        "plus sign for and": r"\w \+ \w",
    },
}


def emphasis_habits(text, sentences):
    result = {}
    for name, pattern in EMPHASIS_PATTERNS.items():
        hits = []
        for i, s in enumerate(sentences, 1):
            for m in re.finditer(pattern, s):
                if name.startswith("stretched") and m.group(0).lower() in NOT_STRETCHED:
                    continue
                hits.append({"sentence": i, "match": m.group(0), "context": s[:160]})
        if hits:
            result[name] = {"count": len(hits), "forms": Counter(h["match"] for h in hits).most_common(10),
                            "examples": hits[:3]}
    return result


def formatting_habits(text):
    found = {}
    for group, patterns in FORMAT_PATTERNS.items():
        rows = {}
        for name, pattern in patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                rows[name] = {"count": len(matches), "forms": Counter(matches).most_common(6)}
        if rows:
            found[group] = rows
    lines = text.splitlines()
    content = [ln for ln in lines if ln.strip()]
    layout = {
        "lines": len(content),
        "mean_line_length_chars": round(sum(len(ln) for ln in content) / len(content), 1) if content else 0,
        "blank_line_paragraph_breaks": len(re.findall(r"\n\s*\n", text)),
        "lines_ending_mid_sentence": sum(1 for a, b in zip(lines, lines[1:])
                                         if a.strip() and b.strip() and not re.search(r"[.!?:;,)\"”]$", a.strip())
                                         and b.strip()[0].islower()),
        "indented_lines": sum(1 for ln in content if re.match(r"(?: {2,}|\t)\S", ln)),
        "double_spaces_between_words": len(re.findall(r"\w  +\w", text)),
        "two_spaces_after_sentence": len(re.findall(r"[.!?]  +[A-Z]", text)),
        "trailing_spaces": sum(1 for ln in lines if ln != ln.rstrip(" \t") and ln.strip()),
        "list_marker_lines": Counter(m for m in re.findall(r"^\s*([-*•>]|\d+[.)]|[a-z][.)])\s", text, re.M)).most_common(5),
    }
    return {"symbols_and_formats": found, "layout": layout}


def system_spellcheck(words):
    """Return the subset of words the macOS spell checker also rejects, or None if unavailable."""
    if not words:
        return set()
    script = (
        'ObjC.import("AppKit"); function run(argv) { var sc = $.NSSpellChecker.sharedSpellChecker; '
        'return argv.filter(function (w) { return sc.checkSpellingOfStringStartingAt(w, 0).length > 0; }).join("\\n"); }'
    )
    try:
        out = subprocess.run(["osascript", "-l", "JavaScript", "-e", script, *words],
                             capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return {w for w in out.stdout.split("\n") if w}


def load_dictionary(path):
    p = Path(path)
    if not p.exists():
        return None
    return {w.strip().lower() for w in p.read_text(errors="ignore").splitlines() if w.strip()}


def known(word, dictionary):
    if word in dictionary:
        return True
    for suffix, repl in (("'s", ""), ("s", ""), ("es", ""), ("ed", ""), ("ed", "e"), ("d", ""),
                         ("ing", ""), ("ing", "e"), ("ly", ""), ("ies", "y"), ("ied", "y"), ("iest", "y"), ("ier", "y"), ("ily", "y"),
                         ("er", ""), ("est", ""), ("n't", ""), ("'ll", ""), ("'re", ""), ("'ve", ""), ("'d", "")):
        if word.endswith(suffix) and word[: -len(suffix)] + repl in dictionary:
            return True
    return False


def sentences_of(text):
    sentences = []
    for line in text.splitlines():
        sentences.extend(split_flat(" ".join(line.split())))
    return [s for s in sentences if WORD_RE.search(s)]


def context_hits(pattern, sentences, limit=5):
    hits = []
    for i, s in enumerate(sentences, 1):
        for m in re.finditer(pattern, s, re.IGNORECASE):
            hits.append({"sentence": i, "match": m.group(0), "context": s[:200]})
    return len(hits), hits[:limit]


def analyze(path, dictionary):
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    raw_words = WORD_RE.findall(text)
    tokens = [w.lower().replace("’", "'") for w in raw_words]
    n = len(tokens)
    sentences = sentences_of(text)
    lines = [ln for ln in text.splitlines() if WORD_RE.search(ln)]

    first_words = [WORD_RE.findall(s)[0] for s in sentences if WORD_RE.findall(s)]
    mid_caps = Counter()
    for s in sentences:
        ws = WORD_RE.findall(s)
        for w in ws[1:]:
            if w[0].isupper() and not w.isupper() and w != "I" and not w.startswith("I'"):
                mid_caps[w] += 1
    capitalization = {
        "sentences": len(first_words),
        "sentence_initial_lowercase": sum(1 for w in first_words if w[0].islower()),
        "lowercase_i_pronoun": len(re.findall(r"(?<![A-Za-z'’])i(?=['’]|\s|$)", text)),
        "uppercase_I_pronoun": len(re.findall(r"(?<![A-Za-z'’])I(?=['’]|\s|$)", text)),
        "all_caps_words_3plus": Counter(w for w in raw_words if len(w) >= 3 and w.isupper() and "." not in w).most_common(15),
        "lines_entirely_lowercase": sum(1 for ln in lines if not re.search(r"[A-Z]", ln)),
        "lines_total": len(lines),
        "mid_sentence_capitalized_words": mid_caps.most_common(20),
    }

    emojis = Counter(EMOJI_RE.findall(text))
    emoticons = Counter(EMOTICON_RE.findall(text))
    line_end_emoji = sum(1 for ln in lines if EMOJI_RE.search(ln.strip()[-4:] if ln.strip() else ""))
    emoji_info = {
        "emoji_total": sum(emojis.values()),
        "emoji_per_1000_words": round(sum(emojis.values()) * 1000 / n, 2) if n else 0.0,
        "emoji_types": emojis.most_common(20),
        "repeated_emoji_runs": len(re.findall(r"(" + EMOJI_RE.pattern + r")\1+", text)),
        "lines_ending_in_emoji": line_end_emoji,
        "emoticons": emoticons.most_common(15),
    }

    counts = Counter(tokens)
    frequency = {
        "top_words": counts.most_common(30),
        "function_words_per_1000": {w: round(counts[w] * 1000 / n, 2) for w in FUNCTION_WORDS if counts[w]} if n else {},
    }

    misspellings = {}
    if dictionary is not None:
        unknown = Counter()
        for raw, low in zip(raw_words, tokens):
            if raw[0].isupper() and raw != raw.upper() and raw.lower() != "i":
                continue  # skip likely proper nouns
            if low in MISSING_APOSTROPHE or low in {"lol", "idk", "omg", "ok", "okay"} or "." in low:
                continue
            if len(low) > 1 and not known(low, dictionary):
                unknown[low] += 1
        confirmed = system_spellcheck(list(unknown))
        if confirmed is not None:
            unknown = Counter({w: c for w, c in unknown.items() if w in confirmed})
            misspellings["checked_with"] = "word list + macOS spell checker (flagged only if both reject it)"
        else:
            misspellings["checked_with"] = "word list only (macOS spell checker unavailable; expect false positives)"
        misspellings["not_in_dictionary"] = unknown.most_common(40)
    else:
        misspellings["not_in_dictionary"] = "dictionary not found; read the text manually"
    misspellings["missing_apostrophe_contractions"] = Counter(t for t in tokens if t in MISSING_APOSTROPHE).most_common(20)
    misspellings["apostrophe_contractions_used"] = sum(1 for t in tokens if "'" in t and not t.endswith("'s"))

    confusables = {}
    for name, pattern in CONFUSABLES.items():
        count, hits = context_hits(pattern, sentences, limit=6)
        if count:
            confusables[name] = {"count": count, "examples": hits}
    malapropisms = {}
    for name, pattern in MALAPROPISM_CANDIDATES.items():
        count, hits = context_hits(pattern, sentences)
        if count:
            malapropisms[name] = {"count": count, "examples": hits}

    return {
        "file": str(path),
        "words": n,
        "capitalization": capitalization,
        "emoji": emoji_info,
        "word_frequency": frequency,
        "misspelling_candidates": misspellings,
        "homophone_contexts_to_check": confusables,
        "malapropism_candidates": malapropisms,
        "emphasis": emphasis_habits(text, sentences),
        "formatting": formatting_habits(text),
    }


def fmt_pairs(pairs):
    return ", ".join(f"{a} ({c})" for a, c in pairs) or "none"


def print_report(r):
    print(f"=== {r['file']} ({r['words']} words) ===")
    if r["words"] < 500:
        print("WARNING: under 500 words; frequency measures are unstable.")
    c = r["capitalization"]
    print("\nCapitalization:")
    print(f"  sentence-initial lowercase: {c['sentence_initial_lowercase']} of {c['sentences']} sentences")
    print(f"  pronoun 'i' lowercase: {c['lowercase_i_pronoun']}  |  'I' uppercase: {c['uppercase_I_pronoun']}")
    print(f"  lines entirely lowercase: {c['lines_entirely_lowercase']} of {c['lines_total']}")
    print(f"  ALL-CAPS words (3+ letters): {fmt_pairs(c['all_caps_words_3plus'])}")
    print(f"  mid-sentence capitalized words (proper nouns or odd caps): {fmt_pairs(c['mid_sentence_capitalized_words'])}")
    e = r["emoji"]
    print("\nEmoji and emoticons:")
    print(f"  emoji: {e['emoji_total']} ({e['emoji_per_1000_words']} per 1000 words): {fmt_pairs(e['emoji_types'])}")
    print(f"  repeated emoji runs: {e['repeated_emoji_runs']}  |  lines ending in emoji: {e['lines_ending_in_emoji']}")
    print(f"  emoticons: {fmt_pairs(e['emoticons'])}")
    f = r["word_frequency"]
    print("\nWord frequency:")
    print(f"  top words: {fmt_pairs(f['top_words'])}")
    print("  function words per 1000: " + ", ".join(f"{w} {v}" for w, v in f["function_words_per_1000"].items()))
    m = r["misspelling_candidates"]
    print("\nMisspelling candidates:")
    nd = m["not_in_dictionary"]
    print(f"  possible misspellings: {fmt_pairs(nd) if isinstance(nd, list) else nd}")
    if m.get("checked_with"):
        print(f"  checked with: {m['checked_with']}")
    print(f"  contractions missing apostrophe: {fmt_pairs(m['missing_apostrophe_contractions'])}")
    print(f"  contractions with apostrophe: {m['apostrophe_contractions_used']}")
    print("\nHomophone contexts to check (read each for wrong-word use):")
    for name, v in r["homophone_contexts_to_check"].items():
        print(f"  {name}: {v['count']}")
        for ex in v["examples"]:
            print(f"      [s{ex['sentence']}] {ex['match']!r}: {ex['context']}")
    print("\nMalapropism / eggcorn candidates:")
    if not r["malapropism_candidates"]:
        print("  none from the built-in list (read the text for others)")
    for name, v in r["malapropism_candidates"].items():
        for ex in v["examples"]:
            print(f"  {name}: [s{ex['sentence']}] {ex['context']}")

    print("\nEmphasis habits:")
    if not r["emphasis"]:
        print("  none found")
    for name, v in r["emphasis"].items():
        print(f"  {name}: {v['count']}  forms: {fmt_pairs(v['forms'])}")
        for ex in v["examples"][:2]:
            print(f"      [s{ex['sentence']}] {ex['context']}")

    fm = r["formatting"]
    print("\nFormatting (numbers, times, dates, money, symbols):")
    if not fm["symbols_and_formats"]:
        print("  none found")
    for group, rows in fm["symbols_and_formats"].items():
        print(f"  {group}:")
        for name, v in rows.items():
            print(f"    {name:42} {v['count']:3}  e.g. {fmt_pairs(v['forms'])}")
    lay = fm["layout"]
    print("  layout: " + ", ".join(f"{k.replace('_', ' ')} {v if not isinstance(v, list) else fmt_pairs(v)}"
                                   for k, v in lay.items()))
    print()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="+")
    parser.add_argument("--dict", default="/usr/share/dict/words")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    dictionary = load_dictionary(args.dict)
    results = [analyze(f, dictionary) for f in args.files]
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for r in results:
            print_report(r)


if __name__ == "__main__":
    main()
