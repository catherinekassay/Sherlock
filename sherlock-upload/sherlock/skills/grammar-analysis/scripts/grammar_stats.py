#!/usr/bin/env python3
"""Grammar measurements for forensic authorship comparison.

Measures sentence length, punctuation habits, passive voice candidates,
tense markers and mood markers for one or more text files.

Usage:
    python3 grammar_stats.py FILE [FILE ...] [--newline-breaks] [--json]

--newline-breaks  treat every line break as a sentence boundary
                  (use for chat logs, texts and social media posts)
"""
import argparse
import json
import re
import statistics
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

PUNCTUATION = {
    "period": r"(?<!\.)\.(?!\.)",
    "comma": r",",
    "semicolon": r";",
    "colon": r":(?![)(DPp/])",
    "exclamation": r"!",
    "question": r"\?",
    "ellipsis": r"\.{3,}|…",
    "em_dash": r"—|(?<!-)--(?!-)",
    "en_dash": r"–",
    "spaced_hyphen": r"\s-\s",
    "parenthesis": r"\(",
    "straight_double_quote": r"\"",
    "curly_double_quote": r"[“”]",
    "straight_apostrophe": r"(?<=[A-Za-z])'(?=[A-Za-z])",
    "curly_apostrophe": r"(?<=[A-Za-z])’(?=[A-Za-z])",
    "repeated_!_or_?": r"[!?]{2,}",
    "space_before_punct": r"[A-Za-z] +[,.;:!?](?!\S*[A-Za-z]{2})",
    "double_space_after_period": r"\.  (?=\S)",
    "no_space_after_comma": r",(?=[A-Za-z])",
}

BE_FORMS = r"(?:am|is|are|was|were|be|been|being|'s|'re|get|gets|got|gotten|getting)"
IRREGULAR_PARTICIPLES = (
    "made|done|seen|given|taken|known|written|told|found|held|kept|left|lost|"
    "paid|put|read|said|sent|set|shown|sold|spent|stolen|thought|brought|bought|"
    "built|caught|chosen|driven|eaten|fallen|felt|forgotten|hidden|hit|hurt|led|"
    "meant|met|run|shot|shut|spoken|struck|taught|thrown|won|beaten|bitten|broken|"
    "cut|born|borne|drawn|forgiven|frozen|grown|hung|laid|ridden|risen|shaken|sworn|torn|worn"
)
PASSIVE_RE = re.compile(
    rf"\b{BE_FORMS}\s+(?:\w+ly\s+|not\s+|never\s+)?(?:[a-z]+ed|{IRREGULAR_PARTICIPLES})\b(?:\s+by\b)?",
    re.IGNORECASE,
)

TENSE_MARKERS = {
    "past": r"\b(?:was|were|had|did|[a-z]{3,}ed)\b",
    "present": r"\b(?:am|is|are|has|does|do|don't|doesn't|isn't|aren't)\b",
    "future": r"\b(?:will|shall|won't|'ll|going to|gonna)\b",
    "perfect": r"\b(?:has|have|had|'ve)\s+(?:not\s+|never\s+|already\s+|just\s+)?(?:[a-z]+ed|been|done|gone|seen|made|had|got|gotten|taken|given)\b",
    "progressive": r"\b(?:am|is|are|was|were|be|been|'m|'re|'s)\s+[a-z]+ing\b",
}

MOOD_MARKERS = {
    "modal_would": r"\bwould\b|'d\b",
    "modal_could": r"\bcould\b",
    "modal_should": r"\bshould\b",
    "modal_might_may": r"\b(?:might|may)\b",
    "modal_must": r"\bmust\b",
    "modal_can": r"\b(?:can|can't|cannot)\b",
    "subjunctive_were": r"\b(?:if|as if|as though|wish)\s+(?:I|he|she|it)\s+were\b",
    "subjunctive_mandative": r"\b(?:suggest|insist|demand|recommend|require|request|propose)(?:s|ed)?\s+that\s+\w+\s+(?:be|not)\b",
    "conditional_if": r"\bif\b",
    "please_imperative": r"\bplease\b",
}

# Candidate calques of "que / dass / чтобы + subjunctive" and conditional-mood transfer.
# Read every hit in context; see reference/mood-by-language.md for what each is consistent with.
MOOD_TRANSFER = {
    "want / would like + that + clause": r"\b(?:want|wants|wanted|wanting|would like|'d like)\s+that\s+(?:I|you|he|she|we|they|it|him|her|them)\s+\w+",
    "before/without/until that + clause": r"\b(?:before|without|until|till)\s+that\s+(?:I|you|he|she|we|they|it)\s+\w+",
    "'for that' meaning 'so that'": r"\bfor\s+that\s+(?:I|you|he|she|we|they|it)\s+(?:can|could|may|might|understand|know|see|come|go|be|have|do|get|feel|learn)\b",
    "'would' in an if-clause": r"(?<!\bas )(?<!\bAs )(?<!\beven )\bif\s+(?:\w+\s+){1,3}?would\b",
    "future after when/if/as soon as": r"\b(?:when|as soon as|once|if|until|before|after)\s+(?:I|you|he|she|we|they|it)\s+will\b",
    "verb before pronoun after fronted adverb (V2)": r"(?:^|[.!?]\s+)(?:Yesterday|Today|Tomorrow|Then|Now|Here|There|Later|Afterwards|Suddenly|Soon|Therefore|Also)\s+(?:went|came|was|were|had|did|said|saw|got|goes|comes|is|are|has|have|will|would|can|could|must|should)\s+(?:I|he|she|we|they|you)\b",
    "'not' before the verb": r"(?<!\bdid )(?<!\bdo )(?<!\bdoes )(?<!\bcould )(?<!\bwould )(?<!\bshould )(?<!\bcan )(?<!\bwill )(?<!\bmust )(?<!\bhad )(?<!\bhave )\b(?:I|you|he|she|we|they)\s+not\s+(?:came|went|had|was|were|did|saw|knew|wanted|liked|come|go|know|want|like|have|has|understand|understood)\b",
}

# Hindi / Indian English transfer candidates (see reference/grammar-by-language.md, Hindi sections).
HINDI_TRANSFER = {
    "invariant 'isn't it?' tag after a non-'it' subject": r"\b(?:you|he|she|they|we|I)\b[^.?!\n]{2,80},\s*isn['’]t it\?",
    "'na?' / 'no?' tag": r",\s*(?:na|no)\?",
    "emphatic 'itself' / 'only' after a time or place word": r"\b(?:today|now|tomorrow|yesterday|here|there|tonight)\s+(?:itself\b|only(?=\s*[.,!?;]))",
    "reduplicated adverb or adjective (slowly slowly)": r"\b(slowly|quickly|small|big|little|hot|different|nice|soft|sweet|fast|one by one by)\s+\1\b",
    "progressive with a stative verb (am knowing)": r"\b(?:am|is|are|was|were)\s+(?:knowing|understanding|wanting|believing|owning|belonging)\b",
    "present tense with 'since' (am here since morning)": r"\b(?:am|is|are)\b[^.?!\n]{0,30}\bsince\s+(?:morning|yesterday|last\s+\w+|\d+\s+\w+|two|three|four|five|many|a\s+long)",
    "'do one thing'": r"\bdo one thing\b",
    "'cousin-brother / cousin-sister'": r"\bcousin[- ](?:brother|sister)\b",
    "'good name'": r"\byour good name\b",
    "mass noun used as count noun (evidences, equipments)": r"\b(?:evidences|equipments|trainings|furnitures|informations|advices|luggages|feedbacks)\b",
}
TAG_QUESTION = r",\s+(?:is|isn['’]t|are|aren['’]t|was|wasn['’]t|do|don['’]t|does|doesn['’]t|did|didn['’]t|will|won['’]t|can|can['’]t|would|wouldn['’]t|have|haven['’]t|has|hasn['’]t)\s+(?:he|she|you|it|they|I|we|there)\?|,\s*(?:right|no|na|yes|okay|ok)\?"
INTENSIFIERS = r"\b(?:completely|absolutely|totally|fully|entirely|utterly)\b"

# Punctuation habits carried over from other languages (see reference/punctuation-by-language.md).
PUNCT_TRANSFER = {
    "comma before that/if/whether clause": r"(?<!,\s)(?<!,\s\w\s)(?<!,\s\w\w\s)(?<!,\s\w\w\w\s)(?<!,\s\w\w\w\w\s)\b(?:know|knew|think|thought|say|said|believe|believed|hope|hoped|see|saw|mean|meant|feel|felt|ask|asked|wonder|wondered|explain|explained)\s*,\s+(?:that(?!['’]s|\s+is\b)|if|whether)\b",
    "comma before to-infinitive": r"\b(?:decided|decide|tried|try|forgot|forget|began|begin|started|start|planned|plan|promised|promise|refused|refuse|agreed|agree|wanted|want|hoped|hope|intend|intended)\s*,\s+to\s+\w+",
    "period/comma after closing quote following ? or !": r"[?!][\"\u201d\u00bb]\s*[.,]",
    "inverted question/exclamation mark": r"[\u00bf\u00a1]",
}
AUX_BEFORE = {"did", "does", "do", "will", "would", "can", "could", "should", "shall", "may", "might", "must",
              "let", "make", "makes", "made", "help", "helps", "helped", "watch", "watched", "saw", "see", "hear",
              "heard", "to", "didn't", "doesn't", "won't", "can't", "couldn't", "wouldn't", "shouldn't", "mustn't"}
BARE_VERBS = r"go|have|do|want|know|come|say|make|think|need|live|work|get|take|see|feel|seem|try"


COPULA_ADJ = (r"happy|sad|tired|busy|angry|hungry|sick|ready|fine|good|bad|late|sorry|beautiful|tall|short|"
              r"rich|poor|young|afraid|free|nervous|lazy|smart|kind|nice|different")
BE_FORMS_BEFORE = {"am", "is", "are", "was", "were", "be", "been", "being", "isn't", "aren't", "wasn't", "weren't",
                   "to", "for", "with", "at", "from", "about", "of", "than", "like", "on", "in", "by"}
OBJECT_VERBS = {"make", "makes", "made", "making", "keep", "keeps", "kept", "keeping", "find", "finds", "found",
                "get", "gets", "got", "leave", "left", "consider", "considered", "call", "called", "let", "see",
                "saw", "want", "wanted", "like", "liked", "prefer", "hold", "held", "set", "drive", "drove", "push"}
COUNT_NOUNS = (r"year|day|month|week|hour|minute|book|thing|friend|student|person|car|house|child|country|"
               r"city|problem|question|way|brother|sister|room|time|dollar|kilometer|mile|page|song|game")
COMPOUND_NEXT = {"old", "period", "plan", "contract", "program", "programme", "course", "degree", "term", "long",
                 "stint", "span", "gap", "window", "run", "trip", "journey", "drive", "walk", "wait", "delay"}


def copula_candidates(sentences, limit=5):
    """'He happy' style: pronoun directly followed by a common adjective, no 'be'."""
    found = []
    for i, s in enumerate(sentences, 1):
        if s.rstrip().endswith("?"):
            continue  # casual native questions drop "are": "You ready?"
        for m in re.finditer(rf"(\w+['’]?\w*)?\s*\b(I|he|she|we|they|you|it)\s+(?:very\s+|so\s+|really\s+|too\s+)?({COPULA_ADJ})\b",
                             s, re.IGNORECASE):
            prev = (m.group(1) or "").lower().replace("’", "'")
            if prev in BE_FORMS_BEFORE:
                continue  # "are you ready", "to you"
            if m.group(2).lower() in ("it", "you") and prev in OBJECT_VERBS:
                continue  # "make it good", "keep you busy"
            found.append({"sentence": i, "match": m.group(0).strip(), "context": s[:200]})
    return found[:limit]


def plural_candidates(sentences, limit=5):
    """'two book' style: number word + singular count noun (skips compounds like 'two year old')."""
    found = []
    pat = rf"(\ba\s+|\ban\s+|\bthe\s+)?\b(two|three|four|five|six|seven|eight|nine|ten|several|many|few|both)\s+({COUNT_NOUNS})\b(?:[\s-]+(\w+))?"
    for i, s in enumerate(sentences, 1):
        for m in re.finditer(pat, s, re.IGNORECASE):
            if m.group(1) or (m.group(4) or "").lower() in COMPOUND_NEXT:
                continue  # "a two year contract", "two year old"
            found.append({"sentence": i, "match": m.group(0).strip(), "context": s[:200]})
    return found[:limit]


def missing_s_candidates(sentences, limit=5):
    """'he go', 'she have' where no auxiliary or causative verb comes right before the pronoun."""
    found = []
    for i, s in enumerate(sentences, 1):
        for m in re.finditer(rf"\b(\w+['’]?\w*)\s+(he|she)\s+({BARE_VERBS})\b", s, re.IGNORECASE):
            if m.group(1).lower().replace("’", "'") in AUX_BEFORE:
                continue
            found.append({"sentence": i, "match": m.group(0), "context": s[:200]})
        m = re.match(rf"\W*(He|She)\s+({BARE_VERBS})\b", s)
        if m:
            found.append({"sentence": i, "match": m.group(0), "context": s[:200]})
    return found[:limit]

IMPERATIVE_STARTERS = {
    "go", "come", "get", "give", "take", "let", "make", "tell", "send", "call",
    "stop", "do", "don't", "look", "listen", "wait", "keep", "leave", "bring",
    "put", "remember", "check", "help", "try", "stay", "find", "read", "write",
    "meet", "pick", "show", "think", "consider", "note", "see", "be", "never", "please",
}

SUBORDINATORS = [
    "because", "since", "although", "though", "even though", "while", "whereas", "if", "unless",
    "until", "when", "whenever", "where", "wherever", "after", "before", "once", "so that",
    "as long as", "as soon as", "in order to", "whether", "which", "who", "whom", "whose",
]
CONNECTORS = [
    "and", "but", "so", "or", "yet", "however", "therefore", "thus", "moreover", "furthermore",
    "additionally", "also", "plus", "besides", "anyway", "anyhow", "nevertheless", "nonetheless",
    "meanwhile", "otherwise", "instead", "still", "then", "hence", "consequently", "indeed",
    "in addition", "on the other hand", "in fact", "as a result", "that said", "having said that",
]
OPENER_TYPES = {
    "first-person pronoun": {"i", "i'm", "i've", "i'd", "i'll", "we", "we're", "my", "our"},
    "second-person": {"you", "you're", "your"},
    "coordinating conjunction": {"and", "but", "so", "or", "yet", "plus"},
    "discourse marker": {"well", "anyway", "honestly", "basically", "like", "ok", "okay", "look", "listen",
                         "yeah", "yes", "no", "oh", "lol", "actually", "literally", "also", "now", "right"},
    "connective adverb": {"however", "therefore", "moreover", "furthermore", "additionally", "also",
                          "consequently", "nevertheless", "meanwhile", "thus", "hence", "finally"},
    "determiner / article": {"the", "a", "an", "this", "that", "these", "those"},
    "subordinator": {"because", "since", "although", "though", "while", "if", "when", "after", "before", "once"},
}
# (full form regex, contracted form regex); "I have"/"have not" are left out because
# possessive "have" often cannot contract, which would distort the rate.
CONTRACTION_PAIRS = {
    "do not / don't": (r"\bdo not\b", r"\bdon['’]?t\b"),
    "does not / doesn't": (r"\bdoes not\b", r"\bdoesn['’]?t\b"),
    "did not / didn't": (r"\bdid not\b", r"\bdidn['’]?t\b"),
    "cannot / can't": (r"\bcan ?not\b", r"\bcan['’]?t\b"),
    "will not / won't": (r"\bwill not\b", r"\bwon['’]?t\b"),
    "would not / wouldn't": (r"\bwould not\b", r"\bwouldn['’]?t\b"),
    "could not / couldn't": (r"\bcould not\b", r"\bcouldn['’]?t\b"),
    "should not / shouldn't": (r"\bshould not\b", r"\bshouldn['’]?t\b"),
    "is not / isn't": (r"\bis not\b", r"\bisn['’]?t\b"),
    "are not / aren't": (r"\bare not\b", r"\baren['’]?t\b"),
    "was not / wasn't": (r"\bwas not\b", r"\bwasn['’]?t\b"),
    "I am / I'm": (r"\bI am\b", r"\bI['’]?m\b"),
    "I will / I'll": (r"\bI will\b", r"\bI['’]ll\b"),
    "you are / you're": (r"\byou are\b", r"\byou['’]re\b"),
    "we are / we're": (r"\bwe are\b", r"\bwe['’]re\b"),
    "they are / they're": (r"\bthey are\b", r"\bthey['’]re\b"),
    "it is / it's": (r"\bit is\b", r"\bit['’]s\b"),
    "that is / that's": (r"\bthat is\b", r"\bthat['’]s\b"),
    "let us / let's": (r"\blet us\b", r"\blet['’]s\b"),
}


def phrase_counts(phrases, text):
    """Count phrases longest first, so "even though" is not also counted as "though"."""
    counts = {}
    for phrase in sorted(phrases, key=len, reverse=True):
        pattern = r"\b" + re.escape(phrase) + r"\b"
        counts[phrase] = len(re.findall(pattern, text, re.IGNORECASE))
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)
    return counts


def clause_complexity(text, sentences):
    n = max(1, len(sentences))
    subs = phrase_counts(SUBORDINATORS, text)
    conns = phrase_counts(CONNECTORS, text)
    initial_conj = sum(1 for s in sentences if re.match(r"\W*(and|but|so|or|yet|plus)\b", s, re.I))
    commas_per_sentence = round(text.count(",") / n, 2)
    return {
        "subordinators_per_sentence": round(sum(subs.values()) / n, 2),
        "subordinators": sorted(((k, v) for k, v in subs.items() if v), key=lambda x: -x[1]),
        "connectors": sorted(((k, v) for k, v in conns.items() if v), key=lambda x: -x[1]),
        "sentences_starting_with_conjunction": initial_conj,
        "commas_per_sentence": commas_per_sentence,
    }


def sentence_openers(sentences):
    firsts = []
    pairs = []
    for s in sentences:
        ws = [w.lower().replace("’", "'") for w in WORD_RE.findall(s)]
        if ws:
            firsts.append(ws[0])
            if len(ws) > 1:
                pairs.append(" ".join(ws[:2]))
    n = max(1, len(firsts))
    types = {name: round(100 * sum(1 for w in firsts if w in words) / n, 1) for name, words in OPENER_TYPES.items()}
    return {
        "top_first_words": Counter(firsts).most_common(15),
        "top_first_two_words": [p for p in Counter(pairs).most_common(10) if p[1] >= 2],
        "opener_type_percent": types,
    }


def contraction_rate(text):
    rows = {}
    total_full = total_short = 0
    for name, (full, short) in CONTRACTION_PAIRS.items():
        f = len(re.findall(full, text, re.IGNORECASE))
        c = len(re.findall(short, text, re.IGNORECASE))
        if f or c:
            rows[name] = {"full": f, "contracted": c}
        total_full += f
        total_short += c
    total = total_full + total_short
    return {
        "full_forms": total_full,
        "contracted_forms": total_short,
        "contraction_rate_percent": round(100 * total_short / total, 1) if total else None,
        "by_pair": rows,
    }


def split_sentences(text, newline_breaks):
    blocks = re.split(r"\n\s*\n" if not newline_breaks else r"\n+", text)
    sentences = []
    for block in blocks:
        block = " ".join(block.split())
        if not block:
            continue
        sentences.extend(split_flat(block))
    return [s for s in sentences if WORD_RE.search(s)]


def per_thousand(count, words):
    return round(count * 1000 / words, 2) if words else 0.0


def examples(pattern, sentences, limit=8):
    found = []
    for i, sentence in enumerate(sentences, 1):
        for match in re.finditer(pattern, sentence, re.IGNORECASE):
            found.append({"sentence": i, "match": match.group(0), "context": sentence[:200]})
            if len(found) >= limit:
                return found
    return found


def analyze(path, newline_breaks):
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    words = WORD_RE.findall(text)
    word_count = len(words)
    sentences = split_sentences(text, newline_breaks)
    lengths = [len(WORD_RE.findall(s)) for s in sentences]

    length_stats = {}
    if lengths:
        length_stats = {
            "sentences": len(lengths),
            "mean": round(statistics.mean(lengths), 2),
            "median": statistics.median(lengths),
            "stdev": round(statistics.stdev(lengths), 2) if len(lengths) > 1 else 0.0,
            "min": min(lengths),
            "max": max(lengths),
            "bands": {
                "1-5": sum(1 for n in lengths if n <= 5),
                "6-10": sum(1 for n in lengths if 6 <= n <= 10),
                "11-20": sum(1 for n in lengths if 11 <= n <= 20),
                "21-30": sum(1 for n in lengths if 21 <= n <= 30),
                "31+": sum(1 for n in lengths if n > 30),
            },
            "ends_without_terminal_punct": sum(1 for s in sentences if not re.search(r"[.!?…\"”')]$", s)),
        }

    punctuation = {}
    for name, pattern in PUNCTUATION.items():
        count = len(re.findall(pattern, text))
        punctuation[name] = {"count": count, "per_1000_words": per_thousand(count, word_count)}

    passive_matches = examples(PASSIVE_RE.pattern, sentences, limit=12)
    passive_count = len(PASSIVE_RE.findall(text))

    tense = {}
    for name, pattern in TENSE_MARKERS.items():
        count = len(re.findall(pattern, text, re.IGNORECASE))
        tense[name] = {"count": count, "per_1000_words": per_thousand(count, word_count)}

    mood = {}
    for name, pattern in MOOD_MARKERS.items():
        count = len(re.findall(pattern, text, re.IGNORECASE))
        mood[name] = {"count": count, "per_1000_words": per_thousand(count, word_count)}
    imperative_candidates = [
        {"sentence": i, "context": s[:200]}
        for i, s in enumerate(sentences, 1)
        if WORD_RE.findall(s) and WORD_RE.findall(s)[0].lower() in IMPERATIVE_STARTERS
    ]
    sentence_types = {
        "declarative_or_other": sum(1 for s in sentences if not re.search(r"[!?]$", s)),
        "question": sum(1 for s in sentences if s.endswith("?")),
        "exclamation": sum(1 for s in sentences if s.endswith("!")),
        "imperative_candidates": len(imperative_candidates),
    }

    return {
        "file": str(path),
        "words": word_count,
        "sentence_length": length_stats,
        "punctuation": punctuation,
        "voice": {
            "passive_candidates": passive_count,
            "passive_per_100_sentences": round(passive_count * 100 / len(sentences), 2) if sentences else 0.0,
            "examples": passive_matches,
        },
        "tense_markers": tense,
        "tense_shift_sample": [
            {"sentence": i, "context": s[:200]}
            for i, s in enumerate(sentences, 1)
            if re.search(TENSE_MARKERS["past"], s, re.I) and re.search(TENSE_MARKERS["present"], s, re.I)
        ][:8],
        "mood_markers": mood,
        "sentence_types": sentence_types,
        "imperative_examples": imperative_candidates[:8],
        "subjunctive_examples": examples(
            MOOD_MARKERS["subjunctive_were"] + "|" + MOOD_MARKERS["subjunctive_mandative"], sentences
        ),
        "mood_transfer_candidates": {name: examples(pat, sentences, limit=5) for name, pat in MOOD_TRANSFER.items()},
        "punctuation_transfer_candidates": {name: examples(pat, sentences, limit=5) for name, pat in PUNCT_TRANSFER.items()},
        "hindi_transfer_candidates": {name: examples(pat, sentences, limit=5) for name, pat in HINDI_TRANSFER.items()},
        "translation_signal_rates": {
            "tag questions per 1000 words": per_thousand(len(re.findall(TAG_QUESTION, text, re.IGNORECASE)), word_count),
            "intensifiers (completely/absolutely/...) per 1000 words": per_thousand(len(re.findall(INTENSIFIERS, text, re.IGNORECASE)), word_count),
        },
        "missing_s_candidates": missing_s_candidates(sentences),
        "copula_candidates": copula_candidates(sentences),
        "plural_candidates": plural_candidates(sentences),
        "clause_complexity": clause_complexity(text, sentences),
        "sentence_openers": sentence_openers(sentences),
        "contractions": contraction_rate(text),
    }


def print_report(result):
    print(f"=== {result['file']} ({result['words']} words) ===")
    if result["words"] < 500:
        print("WARNING: under 500 words; rates are unstable.")
    sl = result["sentence_length"]
    if sl:
        print(f"\nSentence length: {sl['sentences']} sentences, mean {sl['mean']}, median {sl['median']}, "
              f"stdev {sl['stdev']}, range {sl['min']}-{sl['max']}")
        print("  bands: " + ", ".join(f"{k}: {v}" for k, v in sl["bands"].items()))
        print(f"  sentences ending without terminal punctuation: {sl['ends_without_terminal_punct']}")
    print("\nPunctuation (count / per 1000 words):")
    for name, v in result["punctuation"].items():
        if v["count"]:
            print(f"  {name:28} {v['count']:5}  {v['per_1000_words']}")
    voice = result["voice"]
    print(f"\nPassive voice candidates: {voice['passive_candidates']} "
          f"({voice['passive_per_100_sentences']} per 100 sentences) - verify each by reading")
    for ex in voice["examples"]:
        print(f"  [s{ex['sentence']}] {ex['match']!r}: {ex['context']}")
    print("\nTense markers (count / per 1000 words):")
    for name, v in result["tense_markers"].items():
        print(f"  {name:14} {v['count']:5}  {v['per_1000_words']}")
    if result["tense_shift_sample"]:
        print("  sentences mixing past and present markers (check for real shifts):")
        for ex in result["tense_shift_sample"]:
            print(f"    [s{ex['sentence']}] {ex['context']}")
    print("\nMood markers (count / per 1000 words):")
    for name, v in result["mood_markers"].items():
        if v["count"]:
            print(f"  {name:22} {v['count']:5}  {v['per_1000_words']}")
    print("  sentence types: " + ", ".join(f"{k}: {v}" for k, v in result["sentence_types"].items()))
    for ex in result["imperative_examples"]:
        print(f"    imperative? [s{ex['sentence']}] {ex['context']}")
    for ex in result["subjunctive_examples"]:
        print(f"    subjunctive [s{ex['sentence']}] {ex['match']!r}: {ex['context']}")
    transfer = {k: v for k, v in result["mood_transfer_candidates"].items() if v}
    print("  mood-transfer candidates (possible second-language or translation interference; read in context):")
    if not transfer:
        print("    none found")
    for name, exs in transfer.items():
        for ex in exs:
            print(f"    {name}: [s{ex['sentence']}] {ex['match']!r}: {ex['context']}")
    for ex in result["missing_s_candidates"]:
        print(f"    missing third-person -s: [s{ex['sentence']}] {ex['match']!r}: {ex['context']}")
    for ex in result["copula_candidates"]:
        print(f"    missing 'to be' before adjective: [s{ex['sentence']}] {ex['match']!r}: {ex['context']}")
    for ex in result["plural_candidates"]:
        print(f"    missing plural after number word: [s{ex['sentence']}] {ex['match']!r}: {ex['context']}")
    htransfer = {k: v for k, v in result["hindi_transfer_candidates"].items() if v}
    print("  Hindi / Indian English candidates (see reference/grammar-by-language.md):")
    if not htransfer:
        print("    none found")
    for name, exs in htransfer.items():
        for ex in exs:
            print(f"    {name}: [s{ex['sentence']}] {ex['match']!r}: {ex['context']}")
    print("  translation-signal rates (compare across the case's texts; no fixed threshold):")
    for name, v in result["translation_signal_rates"].items():
        print(f"    {name}: {v}")
    ptransfer = {k: v for k, v in result["punctuation_transfer_candidates"].items() if v}
    print("  punctuation-transfer candidates (habits from other languages; see reference/punctuation-by-language.md):")
    if not ptransfer:
        print("    none found")
    for name, exs in ptransfer.items():
        for ex in exs:
            print(f"    {name}: [s{ex['sentence']}] {ex['match']!r}: {ex['context']}")

    cc = result["clause_complexity"]
    pairs = lambda items: ", ".join(f"{k} ({v})" for k, v in items) or "none"
    print("\nClause complexity:")
    print(f"  subordinators per sentence: {cc['subordinators_per_sentence']}  |  commas per sentence: {cc['commas_per_sentence']}")
    print(f"  subordinators: {pairs(cc['subordinators'])}")
    print(f"  connectors: {pairs(cc['connectors'])}")
    print(f"  sentences starting with and/but/so/or/yet/plus: {cc['sentences_starting_with_conjunction']}")

    so = result["sentence_openers"]
    print("\nSentence openers:")
    print(f"  first words: {pairs(so['top_first_words'])}")
    print(f"  repeated first two words: {pairs(so['top_first_two_words'])}")
    print("  opener types (% of sentences): " + ", ".join(f"{k} {v}" for k, v in so["opener_type_percent"].items() if v))

    ct = result["contractions"]
    rate = "n/a" if ct["contraction_rate_percent"] is None else f"{ct['contraction_rate_percent']}%"
    print(f"\nContraction rate: {rate} contracted ({ct['contracted_forms']} contracted, {ct['full_forms']} full)")
    for name, v in ct["by_pair"].items():
        print(f"  {name:24} full {v['full']:3}  contracted {v['contracted']:3}")
    print()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="+")
    parser.add_argument("--newline-breaks", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results = [analyze(f, args.newline_breaks) for f in args.files]
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for r in results:
            print_report(r)


if __name__ == "__main__":
    main()
