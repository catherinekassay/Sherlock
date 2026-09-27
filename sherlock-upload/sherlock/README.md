# Sherlock: forensic authorship analysis for Claude Code

Sherlock is a Claude Code plugin for **forensic linguistic analysis**, focused on **authorship attribution**. It answers the question "how strongly does the language of this text support or undermine the idea that a particular person wrote it?"

It combines a measured stylometry test with close qualitative reading, and reports conclusions on a graded two-way scale: from **strong support for same author**, through **no support either way**, to **strong support for different authors**. It never claims certainty.

## What's included

| Component | Type | What it does |
|---|---|---|
| `case-report` | Skill | Runs a whole case: intake, a suitability check, AI and translation screening, all analyses, combined evaluation and a written report |
| `stylometry` | Skill | Measured authorship tests: `compare` (a within-text baseline), `verify` (the General Impostors method), `markers` (rare shared phrases and constructions), `attribute` (ranks candidate authors, combining both methods), `calibrate` (turns scores into likelihood ratios using texts with known authors) and `corpus-info` |
| `grammar-analysis` | Skill | Sentence length, punctuation, tense, voice, mood, clause complexity, sentence openers, contraction rate, plus checks for second-language and translation transfer |
| `dialect-analysis` | Skill | Phrases, slang, dialect grammar, acronyms, vocabulary level, regional spelling, code-switching and register shifts |
| `orthography-analysis` | Skill | Capitalization, emoji, word frequency, misspellings and malapropisms, emphasis habits, and number, date and money formats |
| `discourse-structure` | Skill | Greetings, sign-offs, paragraphing, organization and formulaic phrases |
| `translation-analyst` | Subagent | Translated or second-language text. It preloads the skills above and sorts every finding by whether it reflects the author, the translator, first-language interference or machine translation. |
| `ai-text-screener` | Subagent | Screens for AI-generated or AI-edited text before any style comparison |
| `reference/` | Reference files | Punctuation by language; grammatical mood by language; first-language grammar profiles (Chinese, Japanese, Hindi/Urdu, Arabic) |

## Requirements

- **Python 3.9+** (standard library only; nothing to install).
- **macOS is optional:** the orthography script also checks spelling with the macOS spell checker when it's available, and falls back to the system word list otherwise.
- **A reference corpus is optional,** but the measured stylometry commands need one (see below).

## Quick start

```
/plugin marketplace add <path-or-repo-containing-this-marketplace>
/plugin install sherlock@kit-local
```

Then describe a case, for example "Run Sherlock on these two texts," or call a skill directly: `/sherlock:case-report`, `/sherlock:grammar-analysis`, and so on.

## The reference corpus

The `verify`, `markers`, `attribute` and `calibrate` commands compare texts with writing by other people. Lay the corpus out like this:

```
corpus/
  <genre>/
    <author-id>/
      <text>.txt
```

Point the scripts at it with `--corpus DIR`, or set `SHERLOCK_CORPUS`. By default they look for `./corpus`.
- **Size:** use at least 20 authors per genre for impostors. For calibration, use at least 5 writers with two or more texts each, and 30 or more same-author pairs before trusting the ratios.
- **What to exclude:** never put a questioned text, or writing by a candidate author, in the genre used for that case.
- **Privacy:** only include writing you have permission to use. No corpus ships with the plugin.

## Validation so far

These results come from the author's own test corpora: original English fiction in three genres, and seven translated fiction corpora from different language communities (Spanish, Hindi, Russian, French, Chinese, Arabic, German).

- **Blind cases** (the answer was committed in writing before it was revealed):
  - **Authorship: 8 of 10 correct.** Both misses taught a rule now built in: a true match written as a poem (prose measurements can't evaluate verse), and a stylized prose piece that the markers test undervalued.
  - **Native language of a translated or pasted text: 7 of 8 correct.** The miss (Hindi called Spanish from one nickname) led to the cross-checking rules and a stronger Hindi profile.
- **Calibration** (69 writers, 12 with two or more texts, 16 same-author pairs), checked by holding out one writer at a time:
  - same-author pairs judged the right way: **11 of 16**
  - different-author pairs judged the right way: **44 of 48 (92%)**
  - different authors wrongly given moderate-or-stronger same-author support: **2 of 48**

  **High scores are reliable. Low scores are not evidence of different authors:** writers whose style changes by genre, stylized prose and very short texts score low even with themselves. Calibrations with fewer than 30 same-author pairs are marked **provisional**. They never anchor a conclusion, and they never turn a low score into "support for different authors."
- **The second-language and translation transfer checks** caught all planted examples. After tuning, they raised 3 false alarms or fewer across 40 native-English texts.

## Limitations and responsible use

- **An analytical aid, not an expert opinion.** Any use in legal, academic-integrity, employment or disciplinary proceedings needs review by a qualified forensic linguist, and the chain of custody of the texts must be confirmed.
- **Short texts (under about 500 words), genre mismatches and heavy editing** limit every conclusion. Sherlock reports these limits rather than forcing a result.
- **The scripts are English-only.** Other languages are analyzed qualitatively.
- **Sherlock never infers race, ethnicity, nationality, immigration status or other protected characteristics** from language. First-language and dialect patterns are reported as "consistent with" a language or variety, nothing more.
- **AI-text detection is unreliable,** especially for second-language writers. The AI screener gives graded indications, not verdicts.
