---
name: dialect-analysis
description: Forensic dialect and vocabulary analysis for authorship attribution and author profiling. Identifies characteristic phrases, slang, regional and social dialect grammar (double negatives, demonstrative "them," verb leveling, habitual be), acronyms and chat abbreviations, vocabulary sophistication including education-level indicators, American vs British/Commonwealth spelling, code-switching between languages, and register shifts within a text. Use when comparing writing samples for authorship, profiling an unknown writer's region, age group or education, or when asked about someone's word choice, slang or dialect in a forensic context.
---

# Dialect and vocabulary analysis

This skill identifies the language varieties and vocabulary habits in a text, both to compare questioned and known writing and to profile an unknown writer. It covers eight features: **common phrases, slang, dialect grammar structures, acronyms, vocabulary level (including education indicators), regional spelling, code-switching, and register shifts**.

## 1. Set up the case

- Label texts as **Q** (questioned) and **K** (known, per candidate), as in the other Sherlock skills. Ask if the roles are unclear.
- Note the genre, medium, audience and date of each text. Slang and acronyms depend heavily on medium (texts vs letters), audience (friends vs employer) and time, since slang dates quickly.
- Send translated texts to the `translation-analyst` agent. Non-native English features belong there too, because second-language patterns can look like dialect.

## 2. Measure

Run the bundled script on all texts (path is relative to this skill's base directory):

```
python3 scripts/dialect_stats.py Q1.txt K-Smith-1.txt K-Jones-1.txt
```

The built-in marker lists only cover common cases. Every hit is a candidate to check by reading, and the texts will contain features the lists don't include. Read the full texts yourself.

## 3. Read closely for each feature

**Common phrases**
- Look for repeated multi-word expressions, pet phrases, fillers, openers and sign-offs ("at the end of the day," "just saying," "hope this helps," "not gonna lie").
- The strongest evidence is an unusual phrase that appears in both Q and K. Check how common a phrase is in general before weighting it. A web search for the exact phrase can help estimate this.

**Slang**
- List slang with what it means and where it comes from: region, age group, online community, or profession.
- Record approximate dates for slang. A term that peaked in a particular year can help date a text or show that Q and K come from different periods.

**Dialect grammar structures**
- Check each candidate by reading it:
  - **Double negatives / negative concord**: "ain't never," "don't know nothing." Separate these from standard double negation ("not unhappy") and from sentences that simply contain two negative words.
  - **Demonstratives**: "them boys" (demonstrative *them*), "this here," "that there," narrative "this guy," and how often *this* is used compared with *that*.
  - **Verb leveling**: "we was," "he don't," "they is."
  - **Other structures**: habitual *be* ("she be working"), completive *done*, *needs + participle* ("needs washed"), multiple modals ("might could"), positive *anymore*, "y'all" or "yinz" as plural *you*.
- Several of these features are associated with African American English or with particular regional varieties. Describe them in neutral linguistic terms, and remember that people pick up features from media, friends and online communities. **Never infer race or ethnicity from dialect features.** Report the variety the features are consistent with, not who the writer is.

**Acronyms**
- Separate professional or technical acronyms (they suggest an occupation or field: "PO," "SOP," "HIPAA"), chat abbreviations ("idk," "tbh," "smh"), and all-caps words used for shouting, which the script lists with acronyms.
- Record casing habits ("LOL" vs "lol") and consistency. Cross-check with the orthography skill.

**Vocabulary and education level**
- The script reports lexical diversity (MATTR is more reliable than type-token ratio for texts of different lengths), word length, share of polysyllabic words and Flesch-Kincaid grade.
- These measures describe the **text**, not the writer's education. They move with genre, topic and audience. A highly educated person writes simply in a text message.
- Stronger education indicators come from reading:
  - Correct, natural use of low-frequency or academic words, compared with overreaching (a sophisticated word used slightly wrong, which may be a malapropism, so check with the orthography skill)
  - Specialist or professional vocabulary
  - Control of complex syntax and formal register when the context calls for it
  - Consistency: a writer who can move between registers shows more command than one stuck in one register
- Express education level as a broad band with reasoning, such as "consistent with post-secondary education, possibly professional or academic writing experience," never as a specific qualification.

**Regional spelling**
- The script counts American forms (color, organize, center, traveled, gray) against British and Commonwealth forms (colour, organise, centre, travelled, grey).
- Consistent use of one system is common and only mildly useful. **Mixed** use is more telling: for example, Canadian writing often combines "colour" with "organize," and Australians often use "-ise" with "program." Mixed use can also reflect a writer who moved countries, learned English in one system and lives in another, or uses a spell-checker set to a different region.
- Check the spell-checker question first. A text written in Word with the language set to US English will have had British spellings flagged or auto-corrected.
- Some "British" forms are also used in the US ("towards," "learnt" in some regions), so treat single instances as weak evidence.

**Code-switching**
- The script flags common words from other languages, accented words and non-Latin scripts. Every hit needs checking: many are loanwords used by all English speakers ("café," "ciao," "chutzpah") or names.
- True code-switching means the writer moves between languages inside a sentence or conversation ("Pero like, no pressure"). Record which languages, where the switches happen (greetings, emotional moments, family terms, whole clauses), and how often.
- Code-switching patterns can be quite individual: which words someone always says in the heritage language, and whether they use accents correctly ("está" vs "esta").
- Report the languages as linguistic features. Code-switching does not establish nationality, ethnicity or immigration status. Send cases where the questioned text may be a translation to the `translation-analyst` agent.

**Register shifts**
- The script splits each text into segments (paragraphs, or blocks of 10 lines for chat logs) and gives each a rough formality index. The index combines word length, contractions, informal markers and personal pronouns. It is only meaningful for comparing segments within the same text, not between different texts.
- A flagged segment differs sharply from the rest of the text. Read it and decide whether the shift is expected (a formal letter with a friendly closing paragraph) or suspicious (a casual message with one suddenly polished paragraph, which can mean copied, AI-written or co-written text).
- Across texts, compare how the candidate moves between registers: a writer who stays casual even in formal settings, or who shifts cleanly, shows a habit that can be compared with Q.

## 4. Compare

For each feature, judge **consistency** (stable across one candidate's known texts) and **distinctiveness** (unusual for this genre, place and time). Dialect features are often shared by a whole community, so they may show the writer belongs to a group rather than identify an individual. Say which of these a feature does:
- **Profiling**: narrows the population (region, age group, community, education band)
- **Individuating**: a combination rare enough to separate this writer from others in that population

Differences matter too: a dialect feature used consistently in K and absent in Q, with a comparable genre, counts against common authorship.

## 5. Report

Use the shared Sherlock format:

**Texts analyzed**: a table with ID, role, candidate, genre/medium, date, word count, and notes

**Feature comparison table**

| Feature | Q | K-[candidate] | Consistent in K? | Distinctiveness | Profiling or individuating | Points toward |
|---|---|---|---|---|---|---|

Give quoted examples with text ID and sentence number for every feature rated moderate or high.

**Writer profile (if requested or if there is no known text)**: the regional variety, age or community indicators, and education band, each with its evidence and confidence

**Dialect-dimension summary**: a graded statement (no support / limited / moderate / strong support for common versus different authorship) for **this dimension only**

**Limitations**: text length, genre, audience or date mismatch, limits of the built-in marker lists, deliberate disguise (people can imitate dialect or suppress it in formal writing), and second-language influence

## Rules

- Quote exactly and never correct the text.
- Use neutral, descriptive language for all varieties. Nonstandard does not mean incorrect or less educated.
- Never infer race, ethnicity, nationality or protected characteristics from linguistic features.
- Never state certainty about authorship or identity.
