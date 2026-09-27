---
name: grammar-analysis
description: Forensic grammar analysis for authorship attribution. Profiles sentence length, punctuation habits, tense consistency, active vs passive voice, grammatical mood (indicative, imperative, subjunctive, conditional, modals), clause complexity and connectors, sentence openers, and contraction rate in questioned and known texts, then compares them. Use when comparing writing samples to identify or support an author, or when asked about someone's sentence structure, punctuation style, tense or voice habits in a forensic or authorship context.
---

# Grammar analysis

This skill profiles the grammatical habits of a writer and compares questioned text against known writing. It covers eight features: **sentence length, punctuation, tense consistency, passive/active voice, mood consistency, clause complexity, sentence openers, and contraction rate**.

## 1. Set up the case

- Label every text before analyzing it: **Q** for a questioned document (Q1, Q2...) and **K** for known writing, one set per candidate (K-Smith-1, K-Smith-2...). If the user hasn't said which is which, ask.
- Note the genre, medium and register of each text (email, text message, letter, social post, formal report). Grammar shifts a lot with medium, so a text message and a business letter from the same person will differ.
- If any text is translated, hand that part to the `translation-analyst` agent. If AI involvement is suspected, run the `ai-text-screener` agent first, because AI editing replaces much of a writer's grammar.

## 2. Measure

Run the bundled script on all texts at once (path is relative to this skill's base directory):

```
python3 scripts/grammar_stats.py Q1.txt K-Smith-1.txt K-Jones-1.txt
```

Add `--newline-breaks` for chat logs, texts and social posts where each line is its own message. Add `--json` if you need to process the numbers further.

The script's output is a starting point. Passive voice, tense and mood hits are pattern matches that include false positives and miss things. Read the texts yourself and confirm every example you cite.

## 3. Read closely for each feature

**Sentence length**
- Compare mean, median and spread, not just the average. A writer who mixes very short and very long sentences is different from one who is uniformly medium.
- Note run-on sentences, comma splices, fragments used for effect, and whether messages end without terminal punctuation.

**Punctuation**
- Look at rates per 1,000 words and at habits: Oxford comma, semicolon use (correct or not), dashes (em dash, double hyphen, or spaced hyphen), ellipsis style (`...` vs `…`, two dots, four dots), `!!`/`?!`, spacing before punctuation, two spaces after a period, straight vs curly quotes and apostrophes.
- Curly quotes and some dashes are often inserted by software such as Word or phone keyboards. Treat them as evidence of the device or software rather than of the person, unless the known texts come from the same setup.

**Tense consistency**
- Identify the base tense of each narrative or passage, then find the shifts. Decide whether each shift is motivated (for example, moving from background to current state) or unmotivated (narrating an event and switching tense mid-story).
- Record habits such as narrative present ("so he comes up to me and says"), heavy perfect aspect, or "would" for past habits.

**Passive / active voice**
- Confirm each passive candidate by reading it. Separate true passives ("was delivered by the courier") from adjectival uses ("I was tired," "was supposed to").
- Note whether the writer drops the agent (which can signal evasion in forensic contexts), uses "get" passives ("got fired") versus "be" passives, and uses passives about the same share of the time in Q and K.

**Mood consistency**
- Profile how the writer does commands and requests: bare imperatives ("Send it"), softened ones ("Please send," "Could you send"), or indirect ones ("It would be great if...").
- Note subjunctive use ("if I were," "I insist he be") versus indicative in the same slots ("if I was"), preferences among modals (would/could/should/might/must), and the mix of questions and exclamations.
- Flag abrupt changes in mood or politeness within one text. These can mark a change of writer or a copied-in passage.
- **Mood transfer:** the script lists "mood-transfer candidates":
  - "want that + clause" ("I want that you come")
  - "before / without / until that + clause"
  - "for that" meaning "so that"
  - "would" in an if-clause
  - future tense after "when" or "if"

  - verb before a pronoun after a fronted adverb ("Yesterday went I")
  - "not" before the verb ("because he not came")
  - a missing -s after he / she ("She go")
  - a missing "to be" before an adjective ("He happy")
  - a missing plural after a number word ("two book")

  For which languages each pattern fits, see `${CLAUDE_PLUGIN_ROOT}/reference/grammar-by-language.md` (Chinese, Japanese, Hindi/Urdu, Arabic) and the mood reference (Romance languages, German, Russian, Danish).
- **Hindi / Indian English candidates:** "isn't it?" after any subject, "na? / no?" tags, "today itself / now only," reduplication ("slowly slowly"), "am knowing," "is here since morning," "do one thing," "cousin-brother," "your good name," "evidences / equipments." These raised no false alarms across 40 native-English texts in testing. The dialect script lists Indian English vocabulary ("prepone," "out of station," "do the needful," lakh / crore, "-ji").
- **Translation-signal rates:** tag questions and intensifiers ("completely," "absolutely"…) per 1,000 words. Native English fiction in testing averaged 0.3 and 0.4 (maximum 2.0 each). Higher rates suggest translation or second-language writing. Compare across the case's texts.

  These can signal second-language writing or translation, so hand such texts to the `translation-analyst` agent.
- **Punctuation transfer:** the script also lists:
  - a comma before "that / if" ("I know, that…") or before a "to" infinitive ("He decided, to read")
  - a period after a closing quotation mark following ? or ! (`"Why?".`)
  - ¿ ¡

  See `${CLAUDE_PLUGIN_ROOT}/reference/punctuation-by-language.md`.
- **Tested on 26 September 2026:** these checks caught all 13 planted examples. Across 40 native-English texts they raised 3 false alarms: "if he would" meaning *willing to* (twice), and a comma before an explanatory "to have…" (once). Treat a single hit as weak evidence, and look for several different kinds. Real English subjunctives ("insist that he be," "if I were") are formal native usage, not interference. See `${CLAUDE_PLUGIN_ROOT}/reference/mood-by-language.md`.

**Clause complexity**
- Look at how the writer builds sentences: mostly simple sentences, chains joined with "and" and "but," or embedded subordinate clauses ("because," "although," "which," "whereas").
- Note preferred connectors. Writers tend to have favorites ("however" vs "but," "though" at the end of a sentence, "that said," "plus," "anyway"), and connector choice is largely unconscious.
- The script counts every "so" and "like" as a candidate connector. Check whether each is actually joining clauses ("so we left") or doing something else ("so good").
- Compare subordinators per sentence and commas per sentence across texts of similar genre only. Formal writing naturally has more subordination.

**Sentence openers**
- Look at habitual first words and first two words ("So basically," "Honestly I," "I think"). A repeated opener across Q and K is a useful individual habit.
- Compare the share of sentences that open with "I," with a conjunction ("And," "But," "So"), with a discourse marker ("Well," "Anyway," "Honestly"), or with a connective adverb ("However," "Additionally").
- Check whether the writer varies openers or repeats one pattern. Some writers start most sentences with "I."

**Contraction rate**
- The script compares full and contracted forms for common pairs (do not / don't, I am / I'm, it is / it's...) and gives the share contracted.
- Contraction rate is fairly stable for a person within a register but shifts with formality, so compare like with like.
- Look at the pattern as well as the rate: some writers contract negatives ("don't," "can't") but not pronouns plus verbs ("I am"), or the reverse.
- Apostrophe-less forms ("dont," "im") count as contracted here. Whether the apostrophe is there is an orthography question, so don't count that difference twice.

## 4. Compare

For each feature, decide two things:
1. **Consistency:** does the feature appear in a similar way across all the known texts from one candidate? A habit that varies inside the known set is weak evidence.
2. **Distinctiveness:** how unusual is the feature among writers in general for this genre? Common features (standard comma use in formal email) carry little weight. Rare, consistent ones ("I insist he be" in text messages) carry more.

Only features that are both consistent and distinctive support a link between Q and K. Differences count too: a stable K habit that is absent from Q is evidence against a match.

## 5. Report

Use this format, which the other Sherlock skills also use:

**Texts analyzed**: a table with ID, role (Q/K), candidate, genre/medium, word count, and notes (translated, possibly AI-edited, and so on)

**Feature comparison table**

| Feature | Q | K-[candidate] | Consistent in K? | Distinctiveness | Points toward |
|---|---|---|---|---|---|

Under the table, give quoted examples with text ID and sentence number for every feature marked moderate or high.

**Grammar-dimension summary**: two or three sentences on what the grammatical evidence shows. Use a graded scale (no support / limited / moderate / strong support for common authorship versus different authorship). This conclusion covers **only the grammar dimension**. Overall authorship conclusions should combine all dimensions.

**Limitations**: text length (under about 500 words per text makes rates unreliable), genre or medium mismatch, time gap between texts, possible editing, autocorrect or AI, and script heuristics that were not confirmed by reading.

## Rules

- Quote the texts exactly, including errors. Never correct or normalize them.
- Never state certainty or say "the author is X." Report how strongly the evidence supports one proposition over another.
- If the texts are too short or too different in genre to compare, say so instead of forcing a result.
