#!/usr/bin/env python3
"""Discourse structure measurements for forensic authorship comparison.

Profiles greetings, sign-offs, signatures, paragraphing, organizing devices
(lists, headings, paragraph-opening markers), questions and formulaic
phrases for one or more text files.

A file can hold one message or several. For email threads or chat exports,
pass --separator with a regular expression that matches the line between
messages, so each message's opening and closing are analyzed separately.

Usage:
    python3 discourse_stats.py FILE [FILE ...] [--separator REGEX] [--json]

Example:
    python3 discourse_stats.py emails.txt --separator '^-{3,}$'
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


GREETING_RE = re.compile(
    r"^(?:dear|hi|hey|hello|hiya|heya|hey there|yo|sup|howdy|greetings|good (?:morning|afternoon|evening|day)|"
    r"morning|evening|to whom it may concern|hallo|ahoy|all|team|folks|everyone)\b",
    re.IGNORECASE,
)
CLOSING_RE = re.compile(
    r"^(?:thanks?(?: again| so much| a lot| in advance)?|thank you(?: so much| again| in advance)?|thx|tx|ty|many thanks|"
    r"cheers|best(?: regards| wishes)?|all the best|regards|kind regards|warm(?:est)? regards|rgds|sincerely|"
    r"yours(?: truly| sincerely| faithfully)?|respectfully|cordially|talk soon|speak soon|ttyl|love|lots of love|"
    r"xo+|xoxo|hugs|take care|peace|later|see (?:you|ya)|stay safe|have a (?:good|great|nice) (?:one|day|weekend)|"
    r"with gratitude|gratefully|until next time|bye)\b[^\n]{0,20}$",
    re.IGNORECASE,
)
DEVICE_SIGNATURE_RE = re.compile(r"^(?:sent from my|get outlook for|sent via|sent with)\b", re.IGNORECASE)
PARAGRAPH_MARKERS = [
    "first", "firstly", "second", "secondly", "third", "also", "additionally", "moreover", "furthermore",
    "anyway", "anyways", "so", "finally", "lastly", "in conclusion", "to summarize", "to sum up", "overall",
    "that said", "honestly", "just", "btw", "by the way", "oh", "ok", "okay", "well", "however", "now",
    "on another note", "separately", "unrelated", "fyi", "p.s.", "ps",
]
FORMULAS = [
    "let me know", "please let me know", "feel free", "hope this helps", "hope you're well", "hope you are well",
    "hope this finds you well", "hope all is well", "just wanted to", "just checking in", "just following up",
    "following up", "quick question", "sorry for the late reply", "sorry for the delay", "no worries",
    "any questions", "looking forward", "thanks for reaching out", "as discussed", "as per", "per our conversation",
    "please find attached", "attached is", "at your earliest convenience", "if you have any questions",
    "don't hesitate", "do not hesitate", "circle back", "touch base", "reach out", "going forward",
    "hope that makes sense", "does that make sense", "long story short", "to be honest", "at the end of the day",
]


def split_messages(text, separator):
    if not separator:
        return [text]
    parts = re.split(separator, text, flags=re.MULTILINE)
    return [p for p in parts if WORD_RE.search(p)]


def sentences_in(block):
    flat = " ".join(block.split())
    return [s for s in split_flat(flat) if WORD_RE.search(s)]


def punctuation_after(line):
    m = re.search(r"([,:!.\-—–]+)\s*$", line.strip())
    return m.group(1) if m else "(none)"


def analyze_message(msg):
    lines = [ln.rstrip() for ln in msg.strip().splitlines()]
    content = [ln for ln in lines if ln.strip()]
    info = {"greeting": None, "greeting_punct": None, "closing": None, "closing_punct": None,
            "signature": None, "device_signature": None, "postscript": False}
    if not content:
        return info

    first = content[0].strip()
    name_only = re.fullmatch(r"[A-Z][a-z]+(?: [A-Z][a-z]+)?\s*[,:!\-—]", first)
    if GREETING_RE.match(first) or name_only:
        info["greeting"] = first[:60]
        info["greeting_punct"] = punctuation_after(first)

    tail = content[-4:]
    for idx, line in enumerate(tail):
        s = line.strip()
        if DEVICE_SIGNATURE_RE.match(s):
            info["device_signature"] = s[:60]
        elif CLOSING_RE.match(s) and not info["closing"]:
            info["closing"] = s[:60]
            info["closing_punct"] = punctuation_after(s)
            after = [t.strip() for t in tail[idx + 1:] if not DEVICE_SIGNATURE_RE.match(t.strip())]
            if after and len(after[0]) <= 40:
                info["signature"] = after[0]
    info["postscript"] = bool(re.search(r"^\s*p\.?\s?s\.?\b", msg, re.IGNORECASE | re.MULTILINE))
    return info


def analyze(path, separator):
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    messages = split_messages(text, separator)
    per_message = [analyze_message(m) for m in messages]

    paragraphs = [p for p in re.split(r"\n\s*\n", text) if WORD_RE.search(p)]
    body_paragraphs = [p for p in paragraphs if len(WORD_RE.findall(p)) > 6]
    sent_counts = [len(sentences_in(p)) for p in body_paragraphs]
    word_counts = [len(WORD_RE.findall(p)) for p in body_paragraphs]
    blank_line_breaks = len(re.findall(r"\n\s*\n", text))
    single_breaks = len(re.findall(r"[^\n]\n(?!\s*\n)[^\n]", text))

    paragraph_openers = Counter()
    for p in paragraphs:
        start = p.strip().lower()
        for marker in sorted(PARAGRAPH_MARKERS, key=len, reverse=True):
            if re.match(re.escape(marker) + r"\b", start):
                paragraph_openers[marker] += 1
                break

    all_sentences = sentences_in(text)
    questions = [s for s in all_sentences if s.rstrip().endswith("?")]
    last_para_questions = 0
    for msg in messages:
        body = [b for b in re.split(r"\n\s*\n", msg) if len(WORD_RE.findall(b)) >= 3
                and not CLOSING_RE.match(b.strip().splitlines()[0].strip())
                and not DEVICE_SIGNATURE_RE.match(b.strip())]
        if body:
            last_para_questions += sum(1 for s in sentences_in(body[-1]) if s.endswith("?"))
    formulas = Counter()
    lower = text.lower().replace("’", "'")
    for f in FORMULAS:
        c = len(re.findall(r"\b" + re.escape(f) + r"\b", lower))
        if c:
            formulas[f] = c

    count = len(per_message)
    return {
        "file": str(path),
        "words": len(WORD_RE.findall(text)),
        "messages": count,
        "openings": {
            "with_greeting": sum(1 for m in per_message if m["greeting"]),
            "greeting_forms": Counter(m["greeting"] for m in per_message if m["greeting"]).most_common(10),
            "greeting_punctuation": Counter(m["greeting_punct"] for m in per_message if m["greeting"]).most_common(),
        },
        "closings": {
            "with_closing": sum(1 for m in per_message if m["closing"]),
            "closing_forms": Counter(m["closing"] for m in per_message if m["closing"]).most_common(10),
            "closing_punctuation": Counter(m["closing_punct"] for m in per_message if m["closing"]).most_common(),
            "signatures": Counter(m["signature"] for m in per_message if m["signature"]).most_common(5),
            "device_signatures": Counter(m["device_signature"] for m in per_message if m["device_signature"]).most_common(3),
            "postscripts": sum(1 for m in per_message if m["postscript"]),
        },
        "paragraphing": {
            "paragraphs": len(paragraphs),
            "body_paragraphs": len(body_paragraphs),
            "mean_sentences_per_paragraph": round(statistics.mean(sent_counts), 2) if sent_counts else 0,
            "mean_words_per_paragraph": round(statistics.mean(word_counts), 1) if word_counts else 0,
            "single_sentence_paragraphs": sum(1 for n in sent_counts if n == 1),
            "blank_line_breaks": blank_line_breaks,
            "single_line_breaks": single_breaks,
        },
        "organization": {
            "bulleted_lines": len(re.findall(r"^\s*[-*•]\s", text, re.MULTILINE)),
            "numbered_lines": len(re.findall(r"^\s*(?:\d+|[a-z])[.)]\s", text, re.MULTILINE)),
            "heading_like_lines": len(re.findall(r"^[^\n.!?]{2,50}:\s*$|^[A-Z][A-Z ]{3,40}$", text, re.MULTILINE)),
            "paragraph_opening_markers": paragraph_openers.most_common(10),
        },
        "questions": {
            "total": len(questions),
            "in_last_paragraph": last_para_questions,
            "examples": [q[:150] for q in questions[:5]],
        },
        "formulaic_phrases": formulas.most_common(15),
    }


def fmt(pairs):
    return ", ".join(f"{k!r} ({v})" for k, v in pairs) or "none"


def print_report(r):
    print(f"=== {r['file']} ({r['words']} words, {r['messages']} message(s)) ===")
    o, c = r["openings"], r["closings"]
    print("\nOpenings:")
    print(f"  messages with a greeting: {o['with_greeting']} of {r['messages']}")
    print(f"  greeting forms: {fmt(o['greeting_forms'])}")
    print(f"  punctuation after greeting: {fmt(o['greeting_punctuation'])}")
    print("\nClosings:")
    print(f"  messages with a sign-off: {c['with_closing']} of {r['messages']}")
    print(f"  sign-off forms: {fmt(c['closing_forms'])}")
    print(f"  punctuation after sign-off: {fmt(c['closing_punctuation'])}")
    print(f"  name/signature lines: {fmt(c['signatures'])}")
    print(f"  device signatures: {fmt(c['device_signatures'])}  |  P.S. used: {c['postscripts']}")
    p = r["paragraphing"]
    print("\nParagraphing:")
    print(f"  paragraphs: {p['paragraphs']} ({p['body_paragraphs']} body paragraphs over 6 words)")
    print(f"  mean sentences per paragraph: {p['mean_sentences_per_paragraph']}  |  mean words: {p['mean_words_per_paragraph']}")
    print(f"  single-sentence paragraphs: {p['single_sentence_paragraphs']}")
    print(f"  blank-line breaks: {p['blank_line_breaks']}  |  single line breaks: {p['single_line_breaks']}")
    g = r["organization"]
    print("\nOrganization:")
    print(f"  bulleted lines: {g['bulleted_lines']}  |  numbered lines: {g['numbered_lines']}  |  heading-like lines: {g['heading_like_lines']}")
    print(f"  paragraph-opening markers: {fmt(g['paragraph_opening_markers'])}")
    q = r["questions"]
    print(f"\nQuestions: {q['total']} total, {q['in_last_paragraph']} in a message's final body paragraph")
    for ex in q["examples"]:
        print(f"  {ex}")
    print(f"\nFormulaic phrases: {fmt(r['formulaic_phrases'])}")
    print()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="+")
    parser.add_argument("--separator", help="regex matching the line between messages, e.g. '^-{3,}$'")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results = [analyze(f, args.separator) for f in args.files]
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for r in results:
            print_report(r)


if __name__ == "__main__":
    main()
