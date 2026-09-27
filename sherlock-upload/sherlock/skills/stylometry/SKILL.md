---
name: stylometry
description: Measured authorship verification for Sherlock. Computes a numeric same-author score with the General Impostors method on topic-resistant features (function-word frequencies and masked character n-grams), converts it into a calibrated likelihood ratio and a Sherlock conclusion using a reference corpus of texts by known authors, finds the rare words, phrases and sentence constructions a questioned text shares with each candidate (markers), and gives a within-text baseline that needs no corpus. Use in every Sherlock case alongside the qualitative skills, whenever the user asks for a measured or statistical authorship test, or to calibrate Sherlock on texts whose authors are known.
---

# Stylometry

The other Sherlock skills rely on judgment about how distinctive a feature is. This skill measures it. It asks one question: are these two texts closer to each other than to texts by other writers of the same genre? It then uses texts with known authors to learn how often that happens when the author really is the same.

## What it needs

A **reference corpus**: plain-text writing by many other people, grouped by genre and author. Point the scripts at it with `--corpus DIR`, or set the `SHERLOCK_CORPUS` environment variable. By default they look for a `corpus/` folder in the current working directory.

```
corpus/
  academic-essays/
    writer01/  essay1.txt  essay2.txt
    writer02/  essay1.txt
    ...
  fiction/
    ...
```

- One folder per genre, then one folder per author. Author folder names can be anonymous IDs.
- **For the impostor test:** at least 20 authors per genre (50 or more is better).
- **For calibration:** at least 10 authors with 2 or more texts each (30 or more is better).
- Texts should be similar in length and type to the case texts.
- **Never** put a case text, or any writing by a candidate author, in the genre being used for that case. Otherwise a candidate becomes their own impostor. If a candidate's writing is in the corpus for calibration, use `--exclude-author` when verifying.

Check the corpus first:

```
python3 scripts/stylometry.py corpus-info
```

## Workflow

Paths are relative to this skill's base directory. Use the analysis copies of the case texts, with source quotations removed and character voices set aside, as the other skills describe.

### 1. Baseline (always, no corpus needed)

```
python3 scripts/stylometry.py compare A.txt B.txt
```

This reports:
- **Whole-text similarity** on function words and masked character 4-grams. On their own these numbers mean little.
- **The biggest function-word differences** between the texts. These are useful for the report, for example "A uses 'the' twice as often."
- **A within-text baseline:** both texts are split into chunks, and the similarity *between* A and B is compared with how similar each text is *to itself*. A ratio near 1.00 means A and B are about as alike as each text is internally. Ratios well below 1 mean they differ more than a single text varies. Genre and topic lower the ratio too, so this is a diagnostic, not a conclusion.

Use `--chunk` to change the chunk size. Each text needs at least two chunks.

### 2. Impostors test (when a corpus exists for the genre)

```
python3 scripts/stylometry.py verify A.txt B.txt --genre academic-essays
```

- Choose the genre folder that matches the case texts. If A and B are in different genres, use the questioned text's genre and record the mismatch.
- **The score (0 to 1)** is the share of rounds in which A and B were closer to each other than to every impostor, over 200 rounds with random feature subsets, in both directions.
- **If the genre is calibrated**, the script gives a likelihood ratio (how many times more likely this score is under same authorship than different authorship) and a Sherlock conclusion on a two-way scale, from "strong support for different authors" to "strong support for same author."
- **If the genre isn't calibrated**, report the score descriptively only. Don't turn it into a conclusion.

### 3. Distinctive markers (whenever a corpus exists)

```
python3 scripts/stylometry.py markers Q.txt --genre romance
```

This automates the most useful step of the qualitative skills: finding what Q shares with each candidate that is **rare among the other writers in the corpus**.

**What it compares:**
- **Phrases:** 1 to 4 words, with punctuation and sentence starts kept.
- **Construction patterns:** 3 to 5 tokens, with content words masked. These catch habits like "To which…" fragments, or dialogue tags with the verb before the name (`, " said [Name]`).
- **Names are masked,** so "explained Anna" and "said Maria" count as the same habit.

**How it scores:** each shared item is weighted by how few other authors use it, and more heavily when both texts repeat it. By default an item counts only if at most 10% of the other authors use it (`--max-share`).

**The ranking:** candidates are ranked by how far their score sits above what their text length predicts, in standard deviations (the "vs length" column), because longer texts share more by chance.

**The marker list:** for the top candidates (`--show`), or one author (`--candidate`), it lists the strongest shared markers, with the example from each text. Variants of the same habit are grouped into one line.

**Reading the result**
- **A high rank alone is not a conclusion.** When the true author isn't in the corpus, *someone* still ranks first. In testing, removing the true author let an unrelated writer rise to +2.2.
- **Judge the markers' quality:**
  - **Real matches share distinctive constructions and idioms,** often several of them: "on bent knee," "To which…" fragments, "It had been … since," a recurring dialogue-tag order.
  - **Chance leaders share mostly single common-looking words and generic patterns.**
- **Discount:** topic words, character names that slipped through masking, and phrases from a shared prompt.
- **Combine with verify:** a candidate that tops both `verify` and `markers`, with strong markers, is the pattern seen in confirmed matches.
- **Validation so far:**
  - **Two confirmed cases:** the true author ranked first in both, at +2.3 and +3.0, with the runner-up at +1.2 and +1.5.
  - **Attribution test on 8 known texts** (fiction-hackathon, 16 writers):

    | Method | True author ranked #1 | In top 3 |
    |---|---|---|
    | Markers | 5 of 8 | 5 of 8 |
    | Impostors | 3 of 8 | 6 of 8 |
    | **Both combined** | **5 of 8** | **6 of 8** |

  - **The methods catch different writers**, so always run both. For several candidates, standardize each method's scores across the candidates and add them.
- **Don't dismiss a strong markers match as "just topic" without evidence.** In a blind test, the strongest match in the corpus (+3.55) was set aside as fantasy vocabulary, and it was a true same-author pair.
- **Repeat writers in the pool suppress impostors scores.** When comparing Q with candidate B, leave B's other texts out of the pool (`--exclude-author`), and treat low impostors scores as weak evidence.

Use `--exclude-author` to leave an author out, and `--json` for machine-readable output.

### 4. Attribution: several candidate authors (whenever a corpus exists)

```
python3 scripts/stylometry.py attribute Q.txt --genre fiction-hackathon
```

This runs both methods and combines them in one step. It's the approach that did best in validation: the true author ranked first in 5 of 8 known texts, and in the top 3 in 6 of 8.

**What it does:**
- **Impostors:** runs the test for Q against every text by each candidate author, keeping all of that author's texts out of the impostor pool. Each author's best-matching text counts.
- **Markers:** runs the markers ranking.
- **Combines the two:** standardizes each method's scores across the candidates and adds them.

**What it reports:**
- a ranking with the impostors score, markers z and combined score for every author
- the leader and its margin over number 2
- whether both methods put the leader first
- the leader's strongest shared markers

**Reading the result:**
- **A real match has a clear margin, both methods agreeing, and distinctive markers.**
- **A small margin, disagreeing methods, or generic markers mean no conclusion.**
- **The ranking is uncalibrated,** so it doesn't give a likelihood ratio.
- **Candidates in a different form** (a poem among prose texts, a script, all-dialogue): **the measured methods can't evaluate them.** A true match can rank last, as happened in a blind test where the author's poem scored 0.02. `attribute` can't detect form automatically, so check the candidates' form by reading. Report such candidates as not evaluable, and cap the leader's support.
- **Stylized prose** (heavy repetition, fragment lists, an unusual narrator such as a non-human voice): it's still prose, but its vocabulary is deliberately narrow, so it **shares few rare markers with anything, and its markers z comes out low even for the true author.** In a blind test (27 September 2026), the true match had the worst markers score (−1.53 to −1.72) but led impostors in every length-matched run (0.40 to 0.50, against ≤0.27 for the rest). A combined score can hide this. For such candidates, don't let a negative markers z outweigh an impostors lead. Report the two methods separately.
- **Standard step: a narration-only, equal-length run.** When Q's dialogue differs from the candidates' (a much higher or lower dialogue share, or dialogue in a different format such as text messages in brackets), strip all dialogue from Q and every candidate, cut all texts to the same length (the shortest narration, e.g. `--length 200`), and rerun `attribute` with a few seeds. Report it next to the full-text run. In two confirmed blind cases (27 September 2026), the full-text impostors leader was wrong and the narration-only equal-length leader was the true author.
- **Prefer length-matched impostors runs.** When Q is much longer than the candidates, run `--length` at about the candidates' length so every text is cut equally; the default 1,000 words compares all of Q with a whole short piece, which skewed rankings in two blind cases.
- **Short candidates:** `attribute` warns when a candidate has under 400 words, or under 40% of Q's length. **The measured methods can't show a match for texts that short.** In a test, a 266-word true match ranked second behind a longer text that shared only generic dialogue formatting. For short candidates, compare **habit rates per 1,000 words** (for example, dialogue verbs, ellipsis habits, epithets, tag + "-ing"), since rates work at any length.

### 5. Calibration (once per genre, and again when the corpus grows)

```
python3 scripts/stylometry.py calibrate --genre academic-essays --length 500
```

- This runs the impostors test on same-author and different-author pairs from the corpus, and reports accuracy, AUC (how well scores separate the two groups: 0.5 is guessing, 1.0 is perfect) and a table of what each score means.
- It saves `calibration.json` in the genre folder.
- Set `--length` near the typical case length. Short texts are harder, and calibrating at the right length keeps the conclusions honest. `verify` truncates texts to the calibrated length automatically and warns when a case is far from it.
- The strongest conclusion is capped by the size of the calibration set. With 30 pairs per side, the likelihood ratio can't exceed 31.
- **Report the accuracy and AUC with every calibrated result.** If AUC is below about 0.75, say that the method doesn't separate writers well in this genre yet, and give the measured result little weight.
- **Calibrations built on fewer than 30 same-author pairs are provisional.** `verify` labels them.
  - Report the ratio as indicative only, and **never let it anchor the case conclusion.**
  - **Never turn a low score into "support for different authors."** In the first calibration (fiction-all, 26 September 2026: 5 writers, 9 same-author pairs, AUC 0.93 in-sample), a leave-one-writer-out check pointed the wrong way for 4 of 9 true pairs. All four belonged to writers B and C, whose style varies a lot between stories.
  - Validate any calibration by holding out one writer at a time: calibrate on the other writers, then check whether the held-out writer's pairs point the right way.
- **Unlabeled texts can hide repeat writers.** Very high "different-author" scores in calibration may be undiscovered same-author pairs. Check them with the corpus owner before treating them as errors.

## How the result combines with the qualitative skills

- **A calibrated result is the anchor.** In the case report, start the overall conclusion from the calibrated stylometry conclusion. The qualitative evidence from grammar, dialect, orthography and discourse can move it by one step at most, unless there is a highly distinctive shared or conflicting marker, such as a rare misspelling. Explain any adjustment.
- **Don't double count.** The measured score already reflects function words, punctuation spacing and word-length patterns. Qualitative features of those kinds (for example "similar use of 'though'," "spaced dashes") are already inside the score. Treat them as illustrations, not extra evidence. Content-level features stay separate: shared metaphors, rare misspellings, dialect items, greetings and sign-offs.
- **Differences can only be blamed on genre with evidence.** Use the within-text baseline, or a cross-genre comparison from the corpus, to show that such a difference is typical. Otherwise the difference counts.
- **Uncalibrated results** are reported descriptively and don't set the conclusion.
- **Markers are qualitative evidence with measured rarity.** List the strongest ones in the evidence matrix, and state how many other authors in the corpus use each.

## Report section

Add this section to the case report or dimension summary:

**Stylometry**
- **Corpus:** genre, number of authors and texts, calibration date, accuracy and AUC
- **Texts:** words analyzed (after truncation)
- **Baseline:** whole-text similarities, within vs between chunk similarity, and the between/within ratio
- **Impostors score:** overall, function words, and masked character n-grams
- **Likelihood ratio and conclusion:** or "uncalibrated: no conclusion"
- **Biggest function-word differences:** 3 to 5 examples
- **Markers:** the candidate ranking (vs-length score), plus the 5 to 10 strongest markers for the leading candidates, each with its rarity and example quotes
- **Limitations:** length, genre mismatch, corpus size and representativeness, and possible AI editing (AI editing removes a writer's function-word habits)

## Rules

- Never use a case text, or text by a candidate author, as an impostor.
- Never present an uncalibrated score as a conclusion.
- Always report calibration accuracy and AUC alongside a calibrated result, so readers know how reliable the method is for this genre.
- Stylometry measures style similarity. It cannot rule out imitation, co-authorship or heavy editing, so pair it with the qualitative skills and AI screening.
