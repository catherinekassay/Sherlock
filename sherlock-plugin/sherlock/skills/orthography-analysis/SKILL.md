---
name: orthography-analysis
description: Forensic orthography analysis for authorship attribution. Profiles capitalization habits (all-caps, all-lowercase, lowercase "i"), emoji and emoticon use, word and function-word frequency, misspellings, missing apostrophes, homophone confusions and malapropisms, emphasis habits (stretched words, repeated punctuation, asterisks), and formatting of numbers, dates, times and money, plus spacing and line breaks, in questioned and known texts, then compares them. Use when comparing writing samples for authorship, or when asked about someone's spelling, capitalization, emoji or word-frequency habits in a forensic context.
---

# Orthography analysis

This skill profiles how a writer puts words on the page and compares questioned text against known writing. It covers five features: **capitalization and emoji, word frequency, misspellings/malapropisms, emphasis habits, and formatting**. Spelling errors that are consistent and unusual are some of the strongest individual evidence in authorship work.

## 1. Set up the case

- Label texts as **Q** (questioned) and **K** (known, per candidate), as in the other Sherlock skills. Ask if the roles are unclear.
- Record the **device and software** for each text whenever it's known or can be inferred: phone keyboard, desktop, email client, handwritten and transcribed. Autocorrect, auto-capitalization and predictive text change orthography heavily. Two texts from different devices can differ for that reason alone.
- If the texts were transcribed from handwriting or images, note it. Transcription can introduce or remove errors.

## 2. Measure

Run the bundled script on all texts (path is relative to this skill's base directory):

```
python3 scripts/ortho_stats.py Q1.txt K-Smith-1.txt K-Jones-1.txt
```

The misspelling check flags a word only when both the system word list (`/usr/share/dict/words`) and the macOS spell checker reject it, which removes most false alarms from the old word list. It skips capitalized words to avoid proper nouns. It still misses things: real-word errors like "form" for "from" or "grate" for "great," and some common typos the macOS checker accepts (such as "teh"). Treat every hit as a candidate, and read the texts for errors it misses.

## 3. Read closely for each feature

**Capitalization and emoji**
- Look at sentence-initial capitals, lowercase "i," texts written entirely in lowercase, all-caps for emphasis vs acronyms, capitalization of nouns mid-sentence, and title case in odd places.
- For emoji, note which ones are used, how often, where they appear (end of message, replacing words, mid-sentence), repetition ("😂😂😂"), skin-tone choices, and emoticons (":)" vs ":-)" vs "=)"). Emoji choice is often very individual.
- Consider whether auto-capitalization explains the pattern. Consistent lowercase on a phone that auto-capitalizes is a deliberate habit and more meaningful.

**Word frequency**
- Look at the **function-word profile** (the, of, and, to, just, really, so...). Function words are used unconsciously and are a well-established basis for stylometric attribution. Compare rates per 1,000 words across texts.
- Also note content words that the writer uses unusually often ("literally," "basically," "honestly").
- Function-word comparisons need length to be reliable, ideally 1,000 words or more per text. With shorter texts, report the pattern as indicative only.

**Misspellings and malapropisms**
- Sort each error into a type, because the type is often more telling than the word:
  - **Typographical**: adjacent-key slips, doubled or dropped letters. These are often random and weak evidence.
  - **Phonetic / cognitive**: spelling a word as it sounds ("definately," "seperate," "alot"). These are often stable personal habits and strong evidence.
  - **Homophone confusion**: their/there/they're, your/you're, its/it's, then/than, to/too. The script lists every use for review. Mark only the confusions.
  - **Missing apostrophes**: "dont," "cant," "im." Note whether this is consistent or mixed with apostrophe use.
  - **Malapropisms and eggcorns**: a similar-sounding wrong word or phrase ("for all intensive purposes," "could of," "escape goat," "on accident").
  - **Deliberate nonstandard spelling**: "u," "ur," "tho," "thru," stretched words ("sooo"). These are style choices, not errors.
- An error only matters if you check whether the writer spells the same word **correctly** elsewhere. Record both the error rate and consistency, such as "'definately' 4 of 4 times in K, 2 of 2 in Q."
- Watch for **disguise**: deliberately inserted errors tend to be inconsistent, cluster on easy words, and appear alongside correct spelling of harder words.

**Emphasis habits**
- Look at stretched words ("sooo," "nooo," "yesss"), including which letter gets repeated and how many times. Some writers always stretch the vowel, others the last letter.
- Look at repeated punctuation ("!!!," "??," "?!"), asterisk or underscore emphasis ("*really*"), tildes ("~"), clap emoji between words, spaced-out letters, and quotation marks around single words.
- Repeated commas (",," or ",,,") are a distinct habit. In Indian English informal writing they can express warmth and care (reported by Kit; see the punctuation reference). They can also be a Hindi-style ditto mark, or just a typo. Read the context, and note whether the tone is affectionate.
- Compare the exact forms, not just whether emphasis appears: "!!!" vs "!!" vs "!!!!!" is often a stable personal choice.
- All-caps emphasis is covered under capitalization. Use both together.

**Formatting**
- The script records how numbers, times, dates and money are written. Each has several competing forms, and people tend to stick to one:
  - Numbers: digits or words for one to nine, "1,000" or "1000," "5k"
  - Times: "3pm," "3 pm," "3 PM," "3 p.m.," "15:00"
  - Dates: month first ("9/26," "Sept 26") or day first ("26/9," "26 September"), ordinals ("26th")
  - Money: "$5," "$5.00," "5$," "5 bucks"
  - Symbols: "%" vs "percent," "&," "and/or," "+"
- Some forms also point to a region or training: day-first dates and 24-hour times suggest non-US conventions, and "5$" often reflects French or Quebec conventions. Report these as consistent with a convention, not as proof of origin.
- For quotation marks, spacing, decimal and thousands separators, or any non-English punctuation (such as «…», „…", ¿, full-width marks, or a space before ? and !), check `${CLAUDE_PLUGIN_ROOT}/reference/punctuation-by-language.md`. It lists which languages and regions use each convention. If a text may be translated or written by a non-native writer, hand it to the `translation-analyst` agent.
- Layout habits cover blank lines vs single line breaks between paragraphs, line length, lines that break mid-sentence, indentation, two spaces after a period, double spaces, trailing spaces, and list markers. These can be very individual but are also shaped by the app or device, so record the medium.

## 4. Compare

For each feature, judge **consistency** (stable across one candidate's known texts) and **distinctiveness** (unusual in the general population for this medium). A shared rare misspelling, used the same way in Q and K and spelled correctly by few people, is strong evidence. Common errors ("alot," your/you're) are weak on their own but can add up in combination. A consistent K habit missing from comparable Q text is evidence against common authorship.

## 5. Report

Use the shared Sherlock format:

**Texts analyzed**: a table with ID, role, candidate, medium, device/software if known, word count, and notes

**Feature comparison table**

| Feature | Q | K-[candidate] | Consistent in K? | Distinctiveness | Points toward |
|---|---|---|---|---|---|

**Error inventory**: a table with each misspelling or malapropism, its error type, the text IDs and counts, and whether the correct form also appears

Give quoted examples with text ID and sentence number for every feature rated moderate or high.

**Orthography-dimension summary**: a graded statement (no support / limited / moderate / strong support for common versus different authorship) for **this dimension only**

**Limitations**: text length, device or autocorrect differences, transcription, possible deliberate disguise, and dictionary gaps

## Rules

- Quote exactly, keeping every error, capital and emoji. Never correct the text.
- Don't treat nonstandard spelling as a sign of low intelligence or education without other evidence.
- Never state certainty about authorship.
