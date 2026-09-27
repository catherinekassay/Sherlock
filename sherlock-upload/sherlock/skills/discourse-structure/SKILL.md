---
name: discourse-structure
description: Forensic discourse structure analysis for authorship attribution. Profiles how a writer opens and closes messages (greetings, sign-offs, signatures, P.S.), how they paragraph, how they organize content (lists, headings, paragraph-opening markers, where requests and questions go), and which formulaic phrases they rely on, then compares questioned and known texts. Use when comparing emails, letters, messages or posts for authorship, or when asked about someone's greetings, sign-offs, paragraphing or message structure in a forensic context.
---

# Discourse structure analysis

This skill profiles how a writer organizes a whole message, as opposed to the sentence- and word-level habits covered by the other skills. It covers four features: **openings, closings, paragraph habits, and organization**. Greetings and sign-offs are often among the most consistent and distinctive habits in emails and letters, because people write them on autopilot.

## 1. Set up the case

- Label texts as **Q** (questioned) and **K** (known, per candidate), as in the other Sherlock skills. Ask if the roles are unclear.
- Record the genre, medium, recipient and relationship for each message. Openings and closings depend heavily on who the message is to (a boss, a friend, a stranger) and the platform (email, text, letter, forum post). Compare messages to similar recipients whenever possible.
- Check for text that the writer didn't type: email client signatures, "Sent from my iPhone," quoted replies, forwarded content and templates. Exclude or label it before analysis.

## 2. Measure

Run the bundled script on all texts (path is relative to this skill's base directory):

```
python3 scripts/discourse_stats.py Q1.txt K-Smith-1.txt K-Jones-1.txt
```

If a file contains several messages, such as an email thread or chat export, pass `--separator` with a pattern for the line between messages so each one's opening and closing is analyzed separately:

```
python3 scripts/discourse_stats.py K-Smith-emails.txt --separator '^-{3,}$'
```

Add `--json` for machine-readable output. The greeting and sign-off lists cover common forms only, so read the start and end of every message yourself.

## 3. Read closely for each feature

**Openings**
- Record the exact greeting form, including capitalization and punctuation: "Hi Sarah," vs "Hi Sarah!" vs "Hi Sarah -" vs "Sarah," vs no greeting at all.
- Note what comes right after the greeting: a pleasantry ("Hope you're well"), an apology ("Sorry for the delay"), or straight to business.
- Note whether the writer changes greeting by recipient, and if so, how consistently.

**Closings**
- Record the exact sign-off with punctuation and line layout: "Thanks!" vs "Thanks," vs "Thank you," vs "Cheers," on its own line, followed by a full name, first name, initial or nothing.
- Look at P.S. use, "Sent from" device lines, and closing pleasantries before the sign-off ("Have a great weekend").
- A distinctive sign-off, used consistently across K and present in Q, is strong evidence. A generic one ("Thanks,") is weak alone.

**Paragraph habits**
- Look at how many paragraphs, how long they are, whether the writer uses one-sentence paragraphs, and whether paragraphs are separated by blank lines or single line breaks.
- Note whether the writer puts everything in one block, or breaks after almost every sentence.

**Organization**
- Note where the main point or request appears: first sentence, buried in the middle, or at the end.
- Look at lists and headings (bullets, numbering, "Next steps:"), paragraph-opening markers ("Also," "Anyway," "So," "Firstly"), and where questions go (for example, always ending with a question).
- Look at formulaic phrases like "let me know," "hope this helps," "just wanted to," "quick question," "please find attached." Their combination and placement matters more than any single one. Common phrases also show up in dialect analysis, so count each feature in only one dimension when combining results.

## 4. Compare

For each feature, judge **consistency** (stable across one candidate's known texts sent to similar recipients) and **distinctiveness** (unusual for this medium and relationship). Account for recipient: a candidate who writes "Hey!" to friends and "Dear Dr. Lee," to professors hasn't been inconsistent. Compare Q with K messages sent to a similar kind of recipient.

Watch for **imitation**: greetings and sign-offs are easy to copy. A Q text that matches K perfectly on these surface features but differs in deeper habits (sentence structure, function words, error patterns) may be an imitation. Flag that pattern for the case report.

## 5. Report

Use the shared Sherlock format:

**Texts analyzed**: a table with ID, role, candidate, medium, recipient/relationship, word count, and notes (quoted or template text removed, and so on)

**Feature comparison table**

| Feature | Q | K-[candidate] | Consistent in K? | Distinctiveness | Points toward |
|---|---|---|---|---|---|

Quote the exact openings and closings, with punctuation and line breaks, for every text.

**Discourse-dimension summary**: a graded statement (no support / limited / moderate / strong support for common versus different authorship) for **this dimension only**

**Limitations**: few messages, different recipients or platforms, client-added signatures or templates, possible imitation of surface features

## Rules

- Quote exactly, including punctuation, capitalization and line breaks.
- Never state certainty about authorship.
- Remove text the writer didn't type (auto-signatures, quoted replies, forwarded content) from the analysis, and say that you did.
