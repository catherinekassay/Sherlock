#!/usr/bin/env python3
"""Dialect and vocabulary measurements for forensic authorship comparison.

Surfaces repeated phrases, slang and dialect marker candidates, nonstandard
grammar structures (double negatives, demonstrative "them"), acronyms, and
vocabulary sophistication / education-level indicators.

Every hit is a CANDIDATE for human review, not a finding.

Usage:
    python3 dialect_stats.py FILE [FILE ...] [--json]
"""
import argparse
import json
import re
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


# Marker candidates grouped by the kind of variety they are often associated with.
# Associations are tendencies, not diagnoses; many have spread well beyond their origin.
DIALECT_MARKERS = {
    "Southern US / AAE / widespread informal": [
        r"\by'?all\b", r"\bain'?t\b", r"\bfinna\b", r"\bfixing to\b", r"\bmight could\b",
        r"\bmight should\b", r"\bused to could\b",
    ],
    "AAE features (verify carefully)": [
        r"\b(?:he|she|they|it|we|you) be \w+ing\b", r"\bbeen had\b", r"\bdone (?:\w+ed|told|went|gone)\b",
        r"\b(?:he|she|it) don'?t\b",
    ],
    "Midland / Pittsburgh / Appalachian": [
        r"\byinz\b", r"\bn(?:ee)?ds? (?:\w+ed)\b", r"\bwants (?:out|in)\b", r"\bpositive anymore\b", r"\bred up\b",
    ],
    "Northeast US": [r"\byouse\b", r"\bwicked\b", r"\bgrinder\b", r"\bon line\b"],
    "British / Irish / Commonwealth": [
        r"\bwhilst\b", r"\bamongst\b", r"\bfortnight\b", r"\breckon\b", r"\bquid\b", r"\bmate\b",
        r"\bcheers\b", r"\binnit\b", r"\bbloody\b", r"\bgutted\b", r"\bproper\b", r"\bcuppa\b",
        r"\bye\b", r"\bwee\b", r"\bgrand\b", r"\bdifferent to\b", r"\bhave got\b",
    ],
    "Verb leveling (was/were, don't/doesn't)": [
        r"\b(?:we|you|they) was\b", r"(?<!if )(?<!wish )(?<!though )(?<!as if )\b(?:I|he|she|it) were\b(?! to)", r"\bthey is\b",
    ],
    "Contracted informal forms": [
        r"\bgonna\b", r"\bwanna\b", r"\bgotta\b", r"\bkinda\b", r"\bsorta\b", r"\blemme\b",
        r"\bgimme\b", r"\bdunno\b", r"\bcuz\b", r"\bcoz\b", r"\btryna\b", r"\bboutta\b",
    ],
    "Current internet / youth slang": [
        r"\bnoc?ap\b", r"\blowkey\b", r"\bhighkey\b", r"\bbet\b", r"\bsus\b", r"\bbussin\b",
        r"\bslay\b", r"\bdeadass\b", r"\bbruh\b", r"\bfam\b", r"\bperiodt?\b", r"\bvibes?\b",
        r"\brizz\b", r"\bmid\b(?!-)", r"\bgoated\b", r"\bsheesh\b",
    ],
}

NEGATORS = r"\b(?:not|no|never|nothing|nobody|none|nowhere|neither|nor|ain'?t|hardly|barely|scarcely|\w+n['’]t|dont|cant|wont|didnt|doesnt|isnt|arent|wasnt|werent|couldnt|wouldnt|shouldnt|havent|hasnt|hadnt)\b"
DEMONSTRATIVE_PATTERNS = {
    "this": r"\bthis\b",
    "that": r"\bthat\b",
    "these": r"\bthese\b",
    "those": r"\bthose\b",
    "them + noun (demonstrative them?)": r"\bthem (?!(?:all|both|and|or|to|in|on|at|for|with|from|up|out|off|down|back|again|too|now|then|so|as|is|are|was|were|the|a|an|that|this|about|over|into|i|you|he|she|we|they|it)\b)[a-z]+s\b",
    "this here / that there": r"\b(?:this here|that there|these here|those there)\b",
    "proximal 'this' in narrative (this guy / this one time)": r"\bthis (?:guy|girl|dude|lady|man|woman|one time|kid)\b",
}

CHAT_ACRONYMS = {
    "lol", "lmao", "lmfao", "rofl", "idk", "idc", "tbh", "tbf", "smh", "imo", "imho", "ngl",
    "brb", "btw", "omg", "omfg", "fr", "frfr", "rn", "wyd", "hbu", "wbu", "ily", "ikr", "irl",
    "fyi", "afaik", "iirc", "jk", "nvm", "np", "ty", "thx", "pls", "plz", "ppl", "bc", "b4",
    "u", "ur", "r", "y", "k", "kk", "ok", "wtf", "stfu", "af", "asap", "dm", "fomo", "tl;dr",
}

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "at", "for", "with", "is",
    "are", "was", "were", "be", "it", "that", "this", "i", "you", "he", "she", "we", "they",
    "my", "your", "his", "her", "our", "their", "me", "him", "us", "them", "so", "as", "if",
}


_OUR = "colo|favo|hono|labo|neighbo|behavio|humo|flavo|rumo|harbo|vapo|vigo|savo|endeavo|armo|odo|parlo|rigo|tumo"
_RE_WORDS = [("center", "centre"), ("theater", "theatre"), ("fiber", "fibre"), ("liter", "litre"),
             ("caliber", "calibre"), ("somber", "sombre"), ("specter", "spectre"), ("luster", "lustre")]
_LL = "travel|cancel|model|label|fuel|signal|level|marvel|counsel|jewel|total|equal|dial|channel|tunnel|quarrel"
_ISE_SUFFIX = "(?:e|es|ed|ing|ation|ations|er|ers)"
# Common words spelled -ise in American English too; never counted as British.
US_VALID_ISE = {
    "advis", "exercis", "surpris", "promis", "otherwis", "likewis", "clockwis", "wis", "ris", "aris", "sunris",
    "compromis", "compris", "enterpris", "supervis", "televis", "revis", "improvis", "despis", "devis",
    "disguis", "expertis", "franchis", "merchandis", "premis", "rais", "prais", "nois", "pois", "cruis",
    "bruis", "concis", "precis", "paradis", "treatis", "chastis", "circumcis", "incis", "excis", "advertis",
    "apprais", "demis", "mis", "vis", "wis", "tis", "dis", "cris",
}

# label -> (American regex or None, British/Commonwealth regex); matched against whole lowercase words.
REGIONAL_SPELLINGS = {
    "-or / -our": (rf"(?:{_OUR})r(?:s|ed|ing|ite|ites|able|ful|hood|hoods|less)?",
                   rf"(?:{_OUR})ur(?:s|ed|ing|ite|ites|able|ful|hood|hoods|less)?"),
    "-er / -re": ("(?:" + "|".join(us for us, _ in _RE_WORDS) + ")(?:s|ed)?",
                  "(?:" + "|".join(uk for _, uk in _RE_WORDS) + ")(?:s|d)?"),
    "-ize / -ise": (rf"[a-z]{{2,}}iz{_ISE_SUFFIX}", rf"[a-z]{{2,}}is{_ISE_SUFFIX}"),
    "-yze / -yse": (r"(?:analy|paraly|cataly)z(?:e|es|ed|ing|er|ers)", r"(?:analy|paraly|cataly)s(?:e|ed|ing|er|ers)"),
    "-l- / -ll-": (rf"(?:{_LL})(?:ed|ing|er|ers)", rf"(?:{_LL})l(?:ed|ing|er|ers)"),
    "-ense / -ence": (r"(?:defense|offense|pretense)s?", r"(?:defence|offence|pretence)s?"),
    "gray / grey": (r"gray(?:s|ed|ing|ish)?", r"grey(?:s|ed|ing|ish)?"),
    "jewelry / jewellery": (r"jewelry", r"jewellery"),
    "catalog / catalogue": (r"catalog(?:s|ed|ing)?", r"catalogue(?:s|d)?"),
    "program / programme": (None, r"programmes?"),
    "aluminum / aluminium": (r"aluminum", r"aluminium"),
    "pajamas / pyjamas": (r"pajamas", r"pyjamas"),
    "mom / mum": (r"moms?|mommy|momma", r"mums?|mummy"),
    "math / maths": (None, r"maths"),
    "fulfill / fulfil": (r"fulfill(?:s|ment)?", r"fulfil(?:s|ment)?"),
    "enroll / enrol": (r"enroll(?:s|ment)?", r"enrol(?:s|ment)?"),
    "skeptic / sceptic": (r"skeptic(?:s|al|ism)?", r"sceptic(?:s|al|ism)?"),
    "plow / plough": (r"plow(?:s|ed|ing)?", r"plough(?:s|ed|ing)?"),
    "learned / learnt, spelled / spelt, dreamed / dreamt": (None, r"learnt|spelt|dreamt|leapt|spilt|smelt"),
    "check / cheque": (None, r"cheques?"),
    "tire / tyre": (None, r"tyres?"),
    "aging / ageing": (r"aging", r"ageing"),
    "maneuver / manoeuvre": (r"maneuver(?:s|ed|ing)?", r"manoeuvre(?:s|d)?|manoeuvring"),
    "pediatric / paediatric": (r"pediatric(?:s|ian|ians)?", r"paediatric(?:s|ian|ians)?"),
    "diaper / nappy": (r"diapers?", r"napp(?:y|ies)"),
    "ass / arse": (None, r"arse(?:s|hole|holes)?"),
}


def regional_spelling(tokens):
    us, uk = Counter(), Counter()
    tokens = [re.sub(r"'s$", "", t) for t in tokens]
    for label, (us_re, uk_re) in REGIONAL_SPELLINGS.items():
        for t in tokens:
            if uk_re and re.fullmatch(uk_re, t):
                if label == "-ize / -ise" and t[: t.rindex("is") + 2] in US_VALID_ISE:
                    continue
                uk[f"{label}: {t}"] += 1
            elif us_re and re.fullmatch(us_re, t):
                if label == "-ize / -ise":
                    stem = t[: t.rindex("iz") + 2]
                    if stem.endswith("siz") or stem in {"priz", "seiz"}:
                        continue  # size, prize, seize: same spelling everywhere
                us[f"{label}: {t}"] += 1
    return us, uk


# Frequent function words and discourse particles from languages often mixed with English.
CODE_SWITCH_WORDS = {
    "Spanish": {"que", "pero", "porque", "pues", "bueno", "oye", "verdad", "gracias", "hermano", "hermana", "mija",
                "mijo", "nada", "mucho", "muy", "estoy", "está", "esta", "sí", "qué", "cómo", "órale", "ándale",
                "dios", "abuela", "abuelo", "tía", "tío", "chisme", "pendejo", "claro", "vamos", "ahorita", "chale",
                "neta", "güey", "wey", "vato", "chica", "chico", "familia", "también", "entonces", "cuando", "donde"},
    "French": {"mais", "alors", "voilà", "oui", "merci", "très", "c'est", "bien", "donc", "quoi", "bah", "ouais", "putain"},
    "Tagalog": {"po", "opo", "naman", "lang", "talaga", "ano", "kasi", "sige", "ate", "kuya", "diba", "grabe", "hay", "sana"},
    "Hindi / Urdu (romanized)": {"yaar", "acha", "accha", "haan", "nahi", "nahin", "kya", "bas", "arre", "bhai",
                                 "ji", "matlab", "chalo", "theek", "bhi", "hai", "hain", "kyun", "abhi"},
    "Arabic (romanized)": {"yalla", "wallah", "wallahi", "inshallah", "habibi", "habibti", "mashallah", "khalas",
                           "alhamdulillah", "yani", "ya3ni", "akhi"},
    "Portuguese": {"obrigado", "obrigada", "então", "né", "tudo", "saudade", "valeu", "legal", "gente"},
    "Italian": {"allora", "ciao", "mamma", "dai", "cazzo", "boh", "magari", "prego", "tipo"},
    "German": {"genau", "doch", "danke", "bitte", "naja", "quatsch", "scheiße", "jawohl", "mensch"},
    "Korean / Japanese (romanized)": {"oppa", "unnie", "aigoo", "daebak", "omo", "kawaii", "sugoi", "baka",
                                      "senpai", "desu", "arigato", "hai"},
    "Yiddish (also common in US English)": {"oy", "schmuck", "chutzpah", "kvetch", "mensch", "shlep", "schlep", "nosh", "bubbe"},
}
AMBIGUOUS_WITH_ENGLISH = {"legal", "tipo", "hai", "hay", "ate", "bien", "dai", "bas", "mamma", "gente", "esta",
                          "donde", "po", "ji", "sana", "chico", "chica", "familia", "mensch"}
SCRIPTS = {
    "Cyrillic": r"[Ѐ-ӿ]", "Greek": r"[Ͱ-Ͽ]", "Arabic": r"[؀-ۿ]",
    "Hebrew": r"[֐-׿]", "Devanagari": r"[ऀ-ॿ]", "Chinese (Han)": r"[一-鿿]",
    "Japanese kana": r"[぀-ヿ]", "Korean Hangul": r"[가-힯]", "Thai": r"[฀-๿]",
}


def code_switching(text, sentences):
    found = {}
    for language, words in CODE_SWITCH_WORDS.items():
        hits = []
        for i, s in enumerate(sentences, 1):
            for w in re.findall(r"[^\W\d_]+(?:'[^\W\d_]+)?", s.lower()):
                if w in words:
                    hits.append({"sentence": i, "word": w, "ambiguous": w in AMBIGUOUS_WITH_ENGLISH, "context": s[:200]})
        # Words that are also ordinary English only count once the language shows up unambiguously.
        if any(not h["ambiguous"] for h in hits):
            found[language] = {
                "count": len(hits),
                "unambiguous": sum(1 for h in hits if not h["ambiguous"]),
                "words": Counter(h["word"] for h in hits).most_common(10),
                "examples": [h for h in hits if not h["ambiguous"]][:4] or hits[:2],
            }
    honorifics = Counter(re.findall(r"\b[A-Z][a-z]+-(?:san|sama|kun|chan|sensei|senpai|ji)\b", text))
    if honorifics:
        found["Honorific name suffixes (Japanese -san/-sama/-kun/-chan/-sensei/-senpai; Hindi/Urdu -ji)"] = {
            "count": sum(honorifics.values()), "unambiguous": sum(honorifics.values()),
            "words": honorifics.most_common(10),
            "examples": [{"sentence": 0, "word": w, "ambiguous": False, "context": w} for w in list(honorifics)[:4]]}
    accented = Counter(w for w in re.findall(r"[^\W\d_]+", text) if re.search(r"[À-ÿĀ-ž]", w))
    scripts = {name: len(re.findall(p, text)) for name, p in SCRIPTS.items() if re.search(p, text)}
    return {"word_candidates": found, "accented_words": accented.most_common(15), "non_latin_characters": scripts}


INFORMAL_MARKERS = re.compile(
    r"\b(?:lol|lmao|omg|idk|tbh|smh|ngl|gonna|wanna|gotta|kinda|sorta|yeah|yep|nope|hey|yo|dude|bro|guys|"
    r"stuff|cool|awesome|super|totally|literally|like|ok|okay|u|ur|cuz)\b|[!?]{2,}|:\)|:\(|<3", re.IGNORECASE)
CONTRACTION = re.compile(r"\b\w+(?:n['’]t|['’](?:m|re|ve|ll|d|s))\b|\b(?:dont|cant|wont|im|ive|didnt|doesnt|isnt)\b", re.IGNORECASE)


def segment_text(text):
    blocks = [b for b in re.split(r"\n\s*\n", text) if WORD_RE.search(b)]
    if len(blocks) >= 2:
        return blocks
    lines = [ln for ln in text.splitlines() if WORD_RE.search(ln)]
    return ["\n".join(lines[i:i + 10]) for i in range(0, len(lines), 10)] or [text]


def register_profile(text):
    segments = []
    for n, seg in enumerate(segment_text(text), 1):
        words = WORD_RE.findall(seg)
        if len(words) < 15:
            continue
        wc = len(words)
        mwl = sum(len(w) for w in words) / wc
        contr = 100 * len(CONTRACTION.findall(seg)) / wc
        informal = 100 * len(INFORMAL_MARKERS.findall(seg)) / wc
        personal = 100 * len(re.findall(r"\b(?:I|me|my|you|your|we|us|our)\b", seg, re.IGNORECASE)) / wc
        index = round((mwl - 4.0) * 25 - contr * 2 - informal * 4 - personal * 0.5, 1)
        segments.append({
            "segment": n, "words": wc, "mean_word_length": round(mwl, 2),
            "contractions_per_100": round(contr, 1), "informal_markers_per_100": round(informal, 1),
            "personal_pronouns_per_100": round(personal, 1), "formality_index": index,
            "starts": " ".join(seg.split())[:80],
        })
    flagged = []
    if len(segments) >= 2:
        idx = sorted(s["formality_index"] for s in segments)
        median = idx[len(idx) // 2]
        flagged = [s["segment"] for s in segments if abs(s["formality_index"] - median) >= 35]
    return {"segments": segments, "shift_flagged_segments": flagged}


def syllables(word):
    word = word.lower().strip("'’")
    if len(word) <= 3:
        return 1
    word = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", word)
    word = re.sub(r"^y", "", word)
    return max(1, len(re.findall(r"[aeiouy]{1,2}", word)))


def mattr(tokens, window=100):
    if len(tokens) < window:
        return round(len(set(tokens)) / len(tokens), 3) if tokens else 0.0
    ratios = [len(set(tokens[i:i + window])) / window for i in range(len(tokens) - window + 1)]
    return round(sum(ratios) / len(ratios), 3)


def sentences_of(text):
    sentences = []
    for line in text.splitlines():
        sentences.extend(split_flat(" ".join(line.split())))
    return [s for s in sentences if WORD_RE.search(s)]


def find_all(pattern, sentences, limit=6, flags=re.IGNORECASE):
    hits = []
    for i, sentence in enumerate(sentences, 1):
        for m in re.finditer(pattern, sentence, flags):
            hits.append({"sentence": i, "match": m.group(0), "context": sentence[:200]})
    return len(hits), hits[:limit]


def analyze(path):
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    raw_words = WORD_RE.findall(text)
    tokens = [w.lower().replace("’", "'") for w in raw_words]
    n = len(tokens)
    sentences = sentences_of(text)

    # Repeated phrases (n-grams that are not made only of stopwords)
    phrases = {}
    for size in (2, 3, 4):
        grams = Counter(
            " ".join(tokens[i:i + size]) for i in range(n - size + 1)
            if not all(t in STOPWORDS for t in tokens[i:i + size])
        )
        phrases[f"{size}-grams"] = [{"phrase": g, "count": c} for g, c in grams.most_common(15) if c >= 2]

    markers = {}
    for group, patterns in DIALECT_MARKERS.items():
        group_hits = []
        for pattern in patterns:
            count, hits = find_all(pattern, sentences, limit=3)
            if count:
                group_hits.append({"pattern": pattern, "count": count, "examples": hits})
        if group_hits:
            markers[group] = group_hits

    double_negatives = []
    for i, sentence in enumerate(sentences, 1):
        negs = re.findall(NEGATORS, sentence, re.IGNORECASE)
        if len(negs) >= 2:
            double_negatives.append({"sentence": i, "negators": negs, "context": sentence[:200]})

    demonstratives = {}
    for name, pattern in DEMONSTRATIVE_PATTERNS.items():
        count, hits = find_all(pattern, sentences, limit=4)
        demonstratives[name] = {"count": count, "per_1000_words": round(count * 1000 / n, 2) if n else 0.0}
        if count and ("them" in name or "here" in name or "narrative" in name):
            demonstratives[name]["examples"] = hits

    upper_acronyms = Counter(
        w for w in re.findall(r"\b(?:[A-Z]{2,6}s?|(?:[A-Z]\.){2,5})(?=\W|$)", text) if w not in {"I", "OK"}
    )
    chat_acronyms = Counter(t for t in tokens if t in CHAT_ACRONYMS)

    word_lengths = [len(t) for t in tokens]
    syl = [syllables(t) for t in tokens]
    sentence_count = max(1, len(sentences))
    fk_grade = 0.39 * (n / sentence_count) + 11.8 * (sum(syl) / n) - 15.59 if n else 0.0
    reading_ease = 206.835 - 1.015 * (n / sentence_count) - 84.6 * (sum(syl) / n) if n else 0.0
    counts = Counter(tokens)

    vocabulary = {
        "tokens": n,
        "types": len(counts),
        "type_token_ratio": round(len(counts) / n, 3) if n else 0.0,
        "mattr_100": mattr(tokens),
        "hapax_ratio": round(sum(1 for c in counts.values() if c == 1) / len(counts), 3) if counts else 0.0,
        "mean_word_length": round(sum(word_lengths) / n, 2) if n else 0.0,
        "pct_words_7plus_letters": round(100 * sum(1 for x in word_lengths if x >= 7) / n, 1) if n else 0.0,
        "pct_polysyllabic_3plus": round(100 * sum(1 for s in syl if s >= 3) / n, 1) if n else 0.0,
        "flesch_kincaid_grade": round(fk_grade, 1),
        "flesch_reading_ease": round(reading_ease, 1),
        "longest_words": sorted({t for t in tokens if len(t) >= 10}, key=len, reverse=True)[:20],
    }

    us_spell, uk_spell = regional_spelling(tokens)

    return {
        "file": str(path),
        "words": n,
        "repeated_phrases": phrases,
        "dialect_marker_candidates": markers,
        "double_negative_candidates": double_negatives[:10],
        "double_negative_candidate_count": len(double_negatives),
        "demonstratives": demonstratives,
        "acronyms": {
            "uppercase": upper_acronyms.most_common(20),
            "chat_style": chat_acronyms.most_common(20),
        },
        "vocabulary": vocabulary,
        "regional_spelling": {"american": us_spell.most_common(20), "british_commonwealth": uk_spell.most_common(20),
                              "american_total": sum(us_spell.values()), "british_total": sum(uk_spell.values())},
        "code_switching": code_switching(text, sentences),
        "register": register_profile(text),
    }


def print_report(r):
    print(f"=== {r['file']} ({r['words']} words) ===")
    if r["words"] < 500:
        print("WARNING: under 500 words; vocabulary measures are unstable.")
    print("\nRepeated phrases:")
    for size, items in r["repeated_phrases"].items():
        if items:
            print(f"  {size}: " + "; ".join(f"{i['phrase']} ({i['count']})" for i in items))
    print("\nDialect / slang marker candidates:")
    if not r["dialect_marker_candidates"]:
        print("  none from the built-in list (read the text for others)")
    for group, hits in r["dialect_marker_candidates"].items():
        print(f"  {group}:")
        for h in hits:
            print(f"    {h['count']}x  {h['examples'][0]['match']!r}: {h['examples'][0]['context']}")
    print(f"\nDouble negative candidates: {r['double_negative_candidate_count']} "
          "(most will be standard; check for negative concord)")
    for d in r["double_negative_candidates"]:
        print(f"  [s{d['sentence']}] {d['negators']}: {d['context']}")
    print("\nDemonstratives (count / per 1000 words):")
    for name, v in r["demonstratives"].items():
        print(f"  {name:55} {v['count']:4}  {v['per_1000_words']}")
        for ex in v.get("examples", []):
            print(f"      [s{ex['sentence']}] {ex['match']!r}: {ex['context']}")
    print("\nAcronyms:")
    print("  all-caps tokens (acronyms or shouting): " + (", ".join(f"{a} ({c})" for a, c in r["acronyms"]["uppercase"]) or "none"))
    print("  chat-style: " + (", ".join(f"{a} ({c})" for a, c in r["acronyms"]["chat_style"]) or "none"))
    v = r["vocabulary"]
    print("\nVocabulary / education-level indicators:")
    for key in ("types", "type_token_ratio", "mattr_100", "hapax_ratio", "mean_word_length",
                "pct_words_7plus_letters", "pct_polysyllabic_3plus", "flesch_kincaid_grade", "flesch_reading_ease"):
        print(f"  {key:26} {v[key]}")
    print("  longest words: " + ", ".join(v["longest_words"]))

    rs = r["regional_spelling"]
    print(f"\nRegional spelling: American {rs['american_total']}  |  British/Commonwealth {rs['british_total']}")
    print("  American: " + (", ".join(f"{w} ({c})" for w, c in rs["american"]) or "none"))
    print("  British/Commonwealth: " + (", ".join(f"{w} ({c})" for w, c in rs["british_commonwealth"]) or "none"))

    cs = r["code_switching"]
    print("\nCode-switching candidates (check each: loanwords and names are common):")
    if not (cs["word_candidates"] or cs["accented_words"] or cs["non_latin_characters"]):
        print("  none found")
    for language, v in cs["word_candidates"].items():
        print(f"  {language}: {v['count']} hits ({v['unambiguous']} unambiguous): "
              + ", ".join(f"{w} ({c})" for w, c in v["words"]))
        for ex in v["examples"]:
            print(f"      [s{ex['sentence']}] {ex['word']!r}: {ex['context']}")
    if cs["accented_words"]:
        print("  accented words: " + ", ".join(f"{w} ({c})" for w, c in cs["accented_words"]))
    if cs["non_latin_characters"]:
        print("  non-Latin script characters: " + ", ".join(f"{k} ({v})" for k, v in cs["non_latin_characters"].items()))

    rg = r["register"]
    print("\nRegister by segment (formality index: higher = more formal; compare segments, not texts):")
    if not rg["segments"]:
        print("  text too short to segment")
    for s in rg["segments"]:
        flag = "  <-- SHIFT?" if s["segment"] in rg["shift_flagged_segments"] else ""
        print(f"  seg {s['segment']:2} ({s['words']:4} w) index {s['formality_index']:6}  word len {s['mean_word_length']}  "
              f"contr/100 {s['contractions_per_100']}  informal/100 {s['informal_markers_per_100']}  "
              f"I-you/100 {s['personal_pronouns_per_100']}{flag}")
        print(f"      \"{s['starts']}...\"")
    print()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="+")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results = [analyze(f) for f in args.files]
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for r in results:
            print_report(r)


if __name__ == "__main__":
    main()
