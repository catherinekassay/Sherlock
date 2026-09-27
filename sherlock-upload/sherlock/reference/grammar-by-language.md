# First-language grammar profiles: forensic reference

A reference for the translation-analyst subagent and the grammar and dialect skills. It covers how the grammar of Chinese, Japanese, Hindi/Urdu and Arabic can show through in English written by speakers of those languages. For Romance languages, German, Russian and Danish, see the mood reference (`mood-by-language.md`). For punctuation, see `punctuation-by-language.md`.

**Sources**, all Wikipedia articles supplied by Kit on 26 September 2026 and summarized here in our own words: *Chinese language*, *Chinese grammar*, *Japanese language*, *Honorific speech in Japanese*, *Hindi*, *Hindustani grammar*, *Arabic*, *Indian English*.

**Labels:**
- **[source]** facts from those articles
- **[inference]** expected effects on English that follow from those facts but aren't stated in the articles (including effects suggested by the tool that summarized the pages)
- **[general knowledge]** anything else

## Ground rules

- **These are tendencies of learners, not fingerprints of a nationality.** Many unrelated languages produce the same patterns (for example, no articles: Chinese, Japanese, Hindi, Russian and others). **Report the languages a pattern is consistent with, never a nationality, ethnicity or immigration status.**
- **Fluent and highly educated writers show few of these patterns,** and skilled translators remove them (see the translation tests of 26 September 2026). Their absence proves nothing.
- **Several patterns also occur in native varieties of English** (for example, a missing third-person -s in some dialects). Report the variety, never ethnicity.
- **Look for clusters,** not single hits: several independent patterns from the same profile.
- **Check every clue against all plausible languages before scoring it.** Many "Romance-looking" idioms are equally Hindi, such as "dying of hunger," "with my own eyes," "with all my heart," and heavy "completely." In a 26 September 2026 test, a Hindi-source text was misread as Spanish because these weren't cross-checked. See *Lessons from a missed case* at the end of this file.

## Quick lookup: pattern → consistent-with

| Pattern in English | Consistent with |
|---|---|
| Missing articles ("I went to store"), or uncertain a / the | Chinese, Japanese, Hindi/Urdu (no articles) [source]; also Russian and other Slavic languages [general knowledge] |
| "the" with general or abstract nouns ("The life is hard") | Arabic (the definite article *al-* is used with generic and abstract nouns) [general knowledge]; also French, Spanish, Italian, German (see the mood reference) |
| Missing plural -s, especially on non-human nouns ("two book") | Chinese (plural marking only for people and pronouns) [source]; Japanese (no grammatical number) [source] |
| Missing past tense, with time shown by a time word ("Yesterday I go to store") | Chinese (no tense inflection; aspect particles and time words instead) [source → inference] |
| Missing third-person -s ("She go") | Chinese, Japanese (no person agreement) [source]; also Scandinavian languages (mood reference) |
| Missing "to be" before an adjective ("He happy") | Chinese (adjectives work like verbs, with no copula) [source]; Arabic (no present-tense copula) [general knowledge] |
| Missing subject or object ("Went to the market. Was very crowded.") | Chinese, Japanese (subjects and objects can be dropped when understood) [source]; Hindi/Urdu, Arabic, Spanish and Italian also allow this [general knowledge] |
| Topic first, then a comment ("This book, I read it already") | Chinese, Japanese (topic-prominent languages) [source] |
| he / she mix-ups | Chinese (he, she and it sound the same, *tā*) [source]; Japanese (no English-style gendered pronouns) [source → inference]; also Finnish, Hungarian, Turkish, Persian (mood reference) |
| Questions without inversion ("You like coffee?") or with the question word in place ("You went where?") | Chinese (the particle 吗 and question words that stay in place) [source]. Weak evidence: also casual native speech. |
| Verbs strung together without "and" or "to" ("Go buy milk come home") | Chinese (serial verb constructions) [source → inference] |
| Verb at the end, or heavy modifiers before the noun | Japanese, Hindi/Urdu (subject-object-verb order) [source]; Chinese (modifiers before the noun) [source] |
| Honorific name suffixes in English ("Tanaka-san," "Sharma-ji") | Japanese (-san, -sama, -kun, -chan, -sensei, -senpai) [source]; Hindi/Urdu (-ji) [general knowledge] |
| Heavy deference and humble formulas ("I humbly request," "kindly," "your good self") | Hindi/Urdu (three-level formal pronouns and formal registers) [source → inference]; Indian English letter conventions [general knowledge]; Japanese humble and polite speech [source → inference] |
| "do the needful," "prepone," "today itself," "discuss about" | Indian English, a variety of English [general knowledge; see the mood reference] |
| Romanized Hindi mixed into English ("Hinglish") | Hindi/Urdu. Romanized Hindi is the dominant form of Hindi online. [source] |
| Right-to-left marks, Arabic comma ، or question mark ؟, Eastern Arabic digits | Arabic-script input [general knowledge; see the punctuation reference] |
| "b" for "p," or "f" for "v," in spelling | Arabic (no /p/ or /v/ sounds) [general knowledge]. Mostly a speech feature; rare in writing. |
| l / r confusion in spelling | Japanese (l and r aren't distinguished) [general knowledge]. Mostly a speech feature. |

## Chinese

**Facts [source]:**
- **Varieties:** Mandarin (about 66% of speakers), plus Min (including Hokkien and Teochew), Wu (including Shanghainese) and Yue (including Cantonese). Many are **not mutually intelligible**.
- **Writing:** Simplified characters are used in mainland China and Singapore. Traditional characters are used in Taiwan, Hong Kong and Macau. Pinyin is the standard romanization of Mandarin.
- **Almost no inflection:** words have one form, with no marking for tense, number or person. Grammar is shown by word order and particles.
- **Aspect, not tense:** particles (了 *le*, 过 *guo*, 着 *zhe*) mark aspect, and time is shown with time words ("yesterday," "now").
- **Plural 们** is limited to pronouns and nouns for people.
- **Classifiers:** most nouns need a measure word to be counted (一瓶酒, "one bottle wine").
- **Word order:** subject-verb-object, but modifiers (including relative clauses) come **before** the noun, and time and place phrases come before the verb.
- **Topic-prominent:** sentences start with the topic (known information).
- **Partly pro-drop:** subjects can be left out when understood.
- **Adjectives work like verbs,** without a copula.
- **Questions:** yes/no questions add 吗 without changing word order. Question words stay in place. There's also an "A-not-A" form ("like not like").
- **Other features:** serial verb constructions; 把 *ba* (object before the verb) and 被 *bèi* (passive, often unmarked).
- **Negation:** two negators: 不 *bù*, and 没 *méi* for "have" and completed actions.
- **Pronouns:** 他, 她 and 它 are all pronounced *tā*.

**Signs in English [inference]:**
- missing tense ("Yesterday I go"), missing plural -s, missing articles
- missing "is" with adjectives ("He happy")
- dropped subjects
- topic-first sentences
- uninverted questions
- strung-together verbs
- he / she confusion
- "have / not have" negation confusion
- underused or unmarked passives ("The book finished reading")

**Punctuation:** see the Chinese section of the punctuation reference (the list comma 、, six-dot ellipsis ……, title marks 《》, and so on).

## Japanese

**Facts [source]:**
- **Word order:** subject-object-verb.
- **Topic and subject:** topic-prominent, with the topic marked by は *wa* and the subject by が *ga*. Particles and postpositions do the work English does with word order.
- **Dropping:** subjects and objects are often left out when they can be inferred. Pronouns are often left out too.
- **Nouns:** no grammatical number, no gender, and **no articles**.
- **Verbs** change for tense and voice, **not for person**. Adjectives also change form.
- **Writing:** kanji, hiragana and katakana are mixed, with katakana used for loanwords. Five vowels, timed in morae.
- **Politeness (keigo):** three kinds:
  - **polite** (*teineigo*: *desu / masu*)
  - **respectful**, for superiors and customers (*sonkeigo*: *suru* → *nasaru*)
  - **humble**, to lower oneself (*kenjōgo*: *suru* → *itasu*, *morau* → *itadaku*)
- **In-group and out-group (*uchi / soto*):** with outsiders, you speak **humbly about your own company or family**. Honorific prefixes *o-* and *go-* (*o-cha, go-han*). Name suffixes: *-san* (neutral), *-sama* (customers, higher status), *-kun* (juniors, boys), *-chan* (children, close friends), *-sensei* (teachers, doctors), *-senpai* (seniors).
- **Keigo is often taught at the company,** sometimes from scripts ("manual keigo").

**Signs in English [inference]:**
- missing articles and plurals
- missing third-person -s
- dropped subjects ("Went to Tokyo yesterday")
- verb-final phrasing and heavy modifiers before the noun
- honorific suffixes carried into English ("Suzuki-san")
- **humble self-reference and heavy apology in business English** ("We are deeply sorry for the inconvenience," "please kindly," set formulas)
- **uneven politeness,** such as formulas from a company script next to plainer text

## Hindi / Urdu (Hindustani)

**Facts [source]:**
- **One grammar, two registers:** Hindi and Urdu share their grammar and core vocabulary. Hindi is written in Devanagari, Urdu in Perso-Arabic script.
- **Vocabulary sources:** Sanskrit, Persian and Arabic, English loanwords (*kameṭī*, "committee"), and Portuguese loans.
- **Romanized Hindi ("Hinglish")** dominates online. One YouTube comment study found 52% romanized Hindi, 46% English and 1% Devanagari.
- **Word order:** subject-object-verb, with **postpositions** after the noun: *ne*, *ko*, *se* ("with"), *mẽ* ("in"), *par* ("on"), *kā / ke / kī* ("of").
- **Gender:** every noun is masculine or feminine, and adjectives and verbs agree with it.
- **Three levels of "you":** *tū* (intimate), *tum* (familiar), *āp* (formal).
- **Aspect:** three aspects (perfective, habitual, progressive), with tense built from participles plus "be."
- **Ergativity:** in the transitive perfective, the verb agrees with the object and the subject takes *ne*.
- **Moods:** presumptive, subjunctive, contrafactual and imperative, beyond the indicative (see the mood reference: "He **will be** in the office now").
- **No articles.**

**Signs in English [inference and general knowledge]:**
- article errors
- "of" and "on / in" preposition choices following the postpositions
- verb-final phrasing in long sentences
- presumptive "will / must"
- formal register and deference ("kindly," "respected sir," "your good self")
- the "-ji" suffix
- Hinglish code-mixing (the dialect script's Hindi / Urdu word list)
- Indian English conventions: "do the needful," "prepone," "today itself," ":-" before lists, and affectionate ",,," (see the punctuation reference)

### Hindi signs in English, expanded

The Hindi-Urdu section above lists the grammar. This section lists how it tends to surface in English, both in the writing of Hindi speakers and in translations from Hindi. **Check them as a cluster.**

**Sourced from Wikipedia's *Indian English* article [source]:**
- **Tags:** *na* used as a tag meaning "isn't it?"; "**is it so?**" meaning "oh, really?"
- **Vocabulary:** "do the needful," "prepone," "out of station," "kindly adjust," "revert" (meaning "reply"), "pass out" (meaning "graduate"), "updation," "upgradation," "tiffin," "hotel" (meaning "restaurant"), "freeship," "foreign-returned"
- **Mass nouns used as count nouns:** "evidences," "equipments," "trainings"
- **Numbers:** lakh / crore grouping (1,00,000)
- **Spelling: British** ("colour," "travelling," "realise," "practise"). American spelling in a translation from Hindi comes from the translator or tool, not the author.

**Patterns from Hindi grammar and idiom [general knowledge]:**

| Pattern in English | Hindi source | Notes |
|---|---|---|
| Frequent tag questions, including the invariant "**isn't it?**" after any subject ("You are coming, isn't it?"), and "**no?**" / "**na?**" | *…, hai na?* / *na?* | One of the most reliable signs. In translations, it shows up as an unusually high rate of tag questions of any form. |
| Overuse of "completely / absolutely / totally / fully" | *bilkul*, *poori tarah*, *ekdum* | Very frequent intensifiers |
| "with my own eyes," "with all my heart," "from the heart" | *apni aankhon se*, *poore dil se*, *dil se* | Also Romance; don't use alone |
| "dying of hunger," "dying of laughter" | *bhookh se marna*, *hans hans ke mar jaana* | Also Romance |
| Reduplication ("slowly slowly," "small small," "hot hot tea") | *dheere dheere*, *chhote chhote* | Distinctive when present |
| Emphatic "itself / only" ("today itself," "now only," "here only") | *aaj hi*, *abhi hi*, *yahin* (the particle *hi*) | Distinctive |
| Present tense with "since" ("I am here since morning") | *subah se yahan hoon* | Also French, Spanish, German, Russian |
| Progressive with stative verbs ("I am knowing," "she is having two sons," "I am understanding") | Hindi progressive forms | Distinctive when frequent |
| "do one thing" (introducing an instruction) | *ek kaam karo* | Distinctive |
| "cousin-brother / cousin-sister" | Hindi has no word for "cousin"; kin terms are gendered | Distinctive |
| "What is your good name?" | *aapka shubh naam* | Distinctive |
| Names repeated where English would use he / she | *vah / woh* doesn't mark gender, so translators substitute names | **Translations especially**: a high rate of names as sentence subjects |
| "God" exclamations and invocations | *Bhagwan / Ram / Allah* in everyday speech | Weak; check for real-world religious references |
| Similes and imagery from Indian life ("red as a Kashmiri apple," laddus, monsoon) | Cultural | Real-world cultural references are **legitimate** evidence (not story world) |
| Respect suffix "-ji," and "sir / madam / uncle / aunty" for non-relatives | Hindi address | Distinctive |
| "Hinglish" words: *yaar, arre, achha, bas, chalo, na, kya, matlab* | Code-mixing | The dialect script lists these |

**In translated text,** fluent translators remove many of these. The ones that survive best are **tag-question rate, intensifier rate, name repetition in place of pronouns, "own eyes / all heart" idioms, and cultural similes.** A translator or tool may also impose American spelling and punctuation.

## Arabic

**Facts [source]:**
- **Varieties:** "Arabic" usually means Standard Arabic (Classical and Modern Standard). Regional spoken varieties are **not necessarily mutually intelligible**, so speakers switch between very different formal and everyday forms (diglossia).
- **Writing:** the Arabic script is an **abjad** written **right to left**, with vowels usually left out.
- **Grammar:** Classical and Modern Standard Arabic keep three grammatical cases.

**Facts [general knowledge]** (not covered by the article summary):
- **Articles:** the definite article *al-* is also used with generic and abstract nouns, and there's no indefinite article.
- **No present-tense "to be"** in simple descriptive sentences.
- **Word order:** verb-subject-object is common in Modern Standard Arabic, subject-verb-object in dialects.
- **Gender** extends to "you." There's a **dual** number and many irregular ("broken") plurals.
- **Relative clauses** often repeat the pronoun ("the book that I read **it**").
- **Sounds:** no /p/ or /v/.
- **Punctuation:** its own marks (، ؛ ؟) and optional Eastern Arabic digits.

**Signs in English:**
- "the" with general nouns ("The honesty is important")
- missing "a"
- missing "is / are" ("He very tall")
- repeated pronouns in relative clauses ("the man who I saw him")
- sentences starting with the verb
- very long sentences joined by "and"
- punctuation and number-format traits from the punctuation reference

**Arabic vs French in polished translation (confirmed case, 27 September 2026):**
- **Many calques fit both.** Literary Arabic and French produce the same English: "nothing but" (*سوى* / *ne… que*), "as though" (*وكأن* / *comme si*), "composed herself" (*تمالكت نفسها* / *se ressaisit*), "had not stopped [doing]" (*لم يتوقف عن* / *n'avait cessé de*), narration by epithet ("the witch," "the wizard"), "a carpet of stars." Don't count these for French when Arabic is possible.
- **Small leans toward Arabic:** "we could say" for a general statement (*يمكننا القول*; French *on* is usually rendered "one"), "gave / let out" + an action noun ("gave a short exhale," "gave a faint nod," from verb + verbal noun), and "?!" (*؟!*).
- **Corpus context decides it.** In the confirmed case, one corpus piece was built on Arabic-only wordplay (the Arabic alphabet, with a lisp pun on *salām ʿalaykum*), which settled a text that alone looked French. Writers from Arabic-speaking countries often also write in French, so a French-looking surface doesn't rule Arabic out.

## What the scripts check

The grammar script flags missing -s ("She go"), missing "to be" before common adjectives ("He happy"), and a missing plural after number words ("two book"), alongside the mood, word-order and punctuation checks. The dialect script lists Japanese honorific name suffixes and common Hinglish words as code-switching candidates. Article use and function-word rates come from the orthography script's function-word profile and stylometry `compare`. An unusually low rate of "the" and "a" is **weak** evidence of a language without articles: compare it with the other texts in the case, not with an absolute number.

## Lessons from a missed case (26 September 2026)

A Hindi-source translated text was predicted as Spanish. Four causes:
1. **One foreign morpheme in a character's dialogue was over-weighted.** A Spanish-looking diminutive ("-ito") was a character's playful nickname. That's character voice, not the author's language.
2. **Clues weren't cross-checked.** "Dying of hunger," "with his own eyes," "with all his heart" and heavy "completely" were read as Spanish, but all fit Hindi at least as well.
3. **The translation-style signals that favor Hindi were missed:** a high tag-question rate, and heavy name repetition in place of he / she.
4. **Corpus context was ignored.** Other pieces in the same translated corpus had real-world Indian cultural references ("-ji," "laddus," "red as a Kashmiri apple").

**Rules that follow:**
- Score every clue against every plausible language.
- Never rest a language conclusion on a single feature, especially one inside dialogue.
- When a corpus is one translated set, use real-world cultural references across all its pieces as context for the likely source language.
