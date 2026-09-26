---
name: case-report
description: Runs a full Sherlock forensic authorship case from intake to final report. Organizes the questioned and known texts, checks they are suitable, screens for translation and AI involvement with the subagents, runs the measured stylometry test and the grammar, dialect, orthography and discourse-structure analyses, then combines every dimension into one overall conclusion with a graded strength rating and a written case report. Use when the user wants a complete authorship analysis, an overall conclusion, a case report, or says something like "run Sherlock on this case" or "who wrote this?"
---

# Sherlock case report

This skill is the overall Sherlock model. It runs a whole authorship case and combines the separate analyses into one conclusion. Work through the stages in order, and tell the user briefly which stage you're on as you go.

The other Sherlock skills live next to this one. From this skill's base directory:

| Dimension | Instructions | Script |
|---|---|---|
| Grammar | `../grammar-analysis/SKILL.md` | `../grammar-analysis/scripts/grammar_stats.py` |
| Dialect and vocabulary | `../dialect-analysis/SKILL.md` | `../dialect-analysis/scripts/dialect_stats.py` |
| Orthography | `../orthography-analysis/SKILL.md` | `../orthography-analysis/scripts/ortho_stats.py` |
| Discourse structure | `../discourse-structure/SKILL.md` | `../discourse-structure/scripts/discourse_stats.py` |
| Stylometry (measured) | `../stylometry/SKILL.md` | `../stylometry/scripts/stylometry.py` |

Read each dimension's SKILL.md before running that analysis, and follow its method.

## Stage 1: Intake

1. **Collect the texts.** Save each text as its own plain-text file in a case folder, exactly as received. Never correct anything.
2. **Label them.** Questioned texts are Q1, Q2... Known texts are grouped by candidate: K-Smith-1, K-Smith-2... Ask the user if roles are unclear.
3. **Record the details of each text** in a materials table: source, date, medium (email, text, letter, post), recipient, device or software if known, how it was obtained, word count, and whether it was transcribed, translated, edited or excerpted.
4. **State the question as two competing propositions.** For example:
   - Proposition A: Smith wrote Q1.
   - Proposition B: someone other than Smith wrote Q1, from a relevant group of possible writers (for example, other employees with access to the account).
   If there are several candidates, say whether the list is **closed** (the writer is definitely one of them) or **open** (it could be someone else entirely). Most real cases are open, which calls for more caution.

## Stage 2: Suitability check

Before analyzing, decide whether the material can support a comparison, and tell the user:

- **Amount:** under about 500 words of Q or of K per candidate makes most measures unreliable. Under about 100 words, only very distinctive features (a rare misspelling, a unique sign-off) can carry any weight.
- **Comparability:** are Q and K in similar genres, media, registers and time periods? A text message and a formal report are hard to compare.
- **Integrity:** is anything edited, templated, co-written, quoted or auto-generated?

Also check the **reference corpus** (`python3 ../stylometry/scripts/stylometry.py corpus-info`). Is there a genre folder matching the case texts, and is it calibrated? If not, tell the user the conclusion will rest on qualitative judgment only and will be less decisive, and say what corpus material would fix that.

**Push for better material before running.** If the case is cross-genre, or either side is under 500 words, tell the user which additional texts would make the result more decisive, such as known writing in the same genre as the questioned text. Ask whether they can provide it. Proceed only once they've answered.

If the material is too weak, say so and explain what additional known writing would help. You can still proceed with clearly limited conclusions if the user wants.

## Stage 3: Screening

Run these with the Agent tool before the style analysis. They can run in parallel.

- **`ai-text-screener`** on every Q text, and on K texts if there's any doubt. AI writing or editing replaces a person's own habits, so a text assessed as likely AI-influenced should not be compared as though the person wrote it.
- **`translation-analyst`** for any text that is translated, may be machine-translated, or was written by someone writing outside their first language.

Give each subagent the file paths, the Q/K labels and the case details from Stage 1. Record their findings, and adjust which features can be used. For example, surface style in a translated text reflects the translator, not the author.

## Stage 4: Dimension analyses

First run the stylometry skill: `compare` always, and `verify` plus `markers` when a corpus exists for the genre. With several candidate authors, use `attribute`, which combines both methods. Record:
- the impostors score, and the likelihood ratio and conclusion if calibrated, plus the calibration accuracy and AUC
- the markers ranking and the strongest shared markers for the leading candidates

When several candidates are compared, a candidate that leads on both `verify` and `markers`, with distinctive markers, is the pattern seen in confirmed matches. A leader with only weak markers may be a chance leader, especially if the true author might not be in the corpus.

Then run all four qualitative dimension analyses on every text, following each skill's SKILL.md. Run the four scripts on all the case files at once, then do the close reading each skill describes. Each dimension produces:
- a feature comparison table
- quoted examples
- a graded conclusion for that dimension only
- its limitations

## Stage 5: Combine the evidence

This is the step that makes Sherlock more than four separate reports.

0. **Anchor on the measured result.** If a calibrated stylometry conclusion exists, the case matches its conditions (same genre, similar length), **and the calibration is not provisional** (30 or more same-author pairs), start from it. A provisional calibration is reported as indicative only. The qualitative evidence can move the conclusion by **one step at most**, unless there is a highly distinctive content-level marker, such as a rare misspelling or a unique phrase, shared or conflicting. State the starting point, any adjustment and the reason. With no calibrated result, the conclusion rests on steps 1 to 6 and should say so.
1. **Build the evidence matrix.** List every feature rated moderate or high in any dimension, with the direction it points (common or different authorship), its consistency, its distinctiveness, and which dimension it came from.
2. **Remove double counting.** Some features measure the same underlying habit. Count each habit once, in whichever dimension describes it best:
   - Contraction rate (grammar) and missing apostrophes (orthography)
   - Common phrases (dialect) and formulaic phrases (discourse)
   - All-caps acronyms (dialect) and all-caps emphasis (orthography)
   - Register shifts (dialect) and politeness or mood (grammar)
   - Regional spelling (dialect) and date or money formats (orthography), when both point to the same country
   - Function-word habits, punctuation spacing and dash style are already inside the stylometry score. When a stylometry result exists, list those qualitative features as illustrations, not as extra evidence.
3. **Weigh independence.** Several independent, consistent and distinctive features that all point the same way are much stronger than many weak or related ones. One highly distinctive shared feature, such as a rare misspelling used the same way in Q and K, can outweigh many common ones.
4. **Account for counter-evidence.** List features that point against common authorship. Explain whether each is explained by genre, recipient, time, device or editing, or whether it is a real difference. **A difference can only be blamed on genre with evidence**, such as the stylometry within-text baseline, a cross-genre comparison in the corpus, or a well-established genre convention you can name. Without that, the difference counts against common authorship. The same standard applies to similarities blamed on shared training or topic.
5. **Consider alternative explanations** for any match:
   - A shared community, dialect or workplace style (many people share it)
   - Imitation or deliberate disguise (surface features match but deeper habits don't, or errors are inconsistent)
   - Co-authorship, editing by someone else, templates, or AI assistance
   - For multiple candidates, whether a feature separates this candidate from the others or is shared by all of them
6. **Reach the overall conclusion** on the Sherlock scale. The scale runs in **both directions**. Differences that are consistent and unexplained should produce conclusions that support different authorship, just as shared features support the same author.
   - **Strong / moderate / limited support for the same author**
   - **No support either way:** the evidence doesn't favor either proposition
   - **Limited / moderate / strong support for different authors**

   Meaning of each strength:
   - **Limited:** the evidence slightly favors one side (a likelihood ratio of about 1.5 to 3, or 1/3 to 1/1.5 for different authors)
   - **Moderate:** the evidence clearly favors one side, with notable limitations (about 3 to 10)
   - **Strong:** the evidence strongly favors one side across several independent, distinctive features or a calibrated measured result, with no major unexplained counter-evidence (above 10)

   The overall conclusion should not be stronger than the evidence allows. Short texts, genre mismatch or unresolved screening concerns cap it, whatever the individual dimensions show. With several candidates in an open set, rank them by strength of support. Never declare a winner by elimination.

## Stage 6: Write the case report

Save the report as `case-report.md` in the case folder, using this structure:

1. **Case summary:** the question, the propositions, and the overall conclusion in two or three sentences
2. **Materials:** the Stage 1 table
3. **Suitability:** the Stage 2 assessment
4. **Screening results:** AI and translation findings and how they changed the analysis
5. **Stylometry:** the measured result in the format from the stylometry skill
6. **Findings by dimension:** for each of grammar, dialect, orthography and discourse, a short summary, the key features table and the dimension conclusion
7. **Combined evaluation:** the starting point from stylometry (if any), the evidence matrix after removing double counting, the counter-evidence, and the alternative explanations considered
8. **Conclusion:** the overall graded conclusion with the reasoning behind it
9. **Limitations:** everything that limits the conclusion
10. **Appendix:** the raw script outputs for each text

If the user wants a Word or PDF version, offer to create one after the Markdown report is done.

## Rules

- Quote texts exactly and never correct them.
- Never state certainty or say "X wrote this." Report the strength of support for one proposition over another.
- Never infer race, ethnicity, nationality, immigration status or other protected characteristics from language.
- Say clearly that the report is an analytical aid. Any use in legal, employment or disciplinary proceedings needs review by a qualified forensic linguist, who would also need to confirm the chain of custody of the texts.
