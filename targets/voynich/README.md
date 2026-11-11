# Voynich manuscript: what the tests showed

Status: research notes, not a decipherment. Local only.

## Human writing

<!-- Your own words go here: why you did this, what you think the manuscript is, what surprised you, what you would
try next. Keep opinion here and results below. -->

## Caveat

Exploratory work, done with an LLM coding agent over a few sessions (27-30 Oct 2026), not reviewed by anyone else.
Many tests were run, and some generators were tuned on the same statistics they are scored on (the b3 battery holds 30
of its 37 items out of the tuning). Protocols and pass rules were written down before each run, and failures are kept.
Trust the results below more than the rest of the folder; the full chain of 45+ tests is in
`HYPOTHESES_2026-10-28.md`.

## The main results (strongest evidence first)

### 1. Voynich's scribes differ as much as people inventing gibberish, and no cipher tested makes them differ that much

Split each scribe's text (Davis's hands, ZL transcription) into 200-word documents and compare glyph-pair statistics
between scribes against the variation within one document:

| text | between scribes / within document | same scribe, other document / within |
|---|---|---|
| Voynich | 2.97 [2.29-3.46] | 2.00 |
| Gibberish volunteers (Gaskell & Bowern 2022) | 3.16 [2.63-3.81] | |
| Real scribes copying a real text (Auchinleck MS, six Middle English scribes) | 1.42 [1.33-1.55] | 1.32 |
| Naibbe / round-8 cipher, scribes with shared or own tables | 1.02-1.63 | 1.00-1.31 |
| A cipher system per scribe (tables from each hand's own words) | 2.11 | 1.44 |
| Whole-word homophonic code, homophones chosen by scribe and quire habit (108 settings) | at most about 1.5 | at most about 1.35 |

A cipher's random choices raise the within-document variation, so its scribes look alike; a per-scribe system breaks
the word rules the scribes share (result 2). Every cipher and code family tested falls short by about half.
Scripts: `meaning/scribe_ratio.py`, `cipher_scribes.py`, `scribe_systems.py`, `duel.py`, `habitcode.py`.

### 2. One shared, rigid word template, with personal habits on top

One scribe's glyph trigrams cover another scribe's words at 0.89 of the scribe's own rate (Auchinleck scribes 0.85;
separate cipher tables 0.47-0.64), while the habit gap is +0.31 bits/unit (Auchinleck +0.18, one shared cipher +0.06).
Word spaces are mostly fixed by the glyphs (74%, natural languages 34-46%). Free word invention does not produce this
(result 4). Currier A and B
are a difference of habit inside the one system (rules 0.83-0.86 across A/B), not two keys: the best glyph-for-glyph
mapping closes 1% of the A-B gap, against 100% for a re-keyed control.
Scripts: `meaning/scribe_systems.py`, `enochian.py`, `keymap.py`, `glyphs/`.

### 3. A real topical text laid out leaf by leaf (Pliny) matches Voynich's page vocabulary, but not its drift

No earlier study we found uses a matched real text this way. Pliny's Naturalis Historia (Latin) was poured into the
manuscript's own leaf layout, each section taking the matching subject: herbal leaves from the plant books (XX-XXIII),
pharmaceutical from the medicine books (XXIV-XXV), recipes from XXVI-XXVII, astronomical and zodiac from II,
balneological from XXXI. The same books were also run as one continuous stream, and as a word code and a letter cipher.

| | Voynich | Pliny, leaf by leaf | what it means |
|---|---|---|---|
| words specific to their leaf (ratio to random pages) | 1.81 | 1.78 | page-specific vocabulary is what a real topical text gives |
| glyph-statistics drift within a section (k_jsd) | 0.050 | 0.004-0.007 | the drift is ten times too large for a change of subject |

The leaf locality survives a word code but a letter cipher destroys it (0.006), so it favours a word-level unit over a
letter cipher. The drift points the other way: something changes the writing itself from part to part of the book,
across Currier A/B and quire to quire (A +0.012, B +0.027 JSD within one hand and section, 6-8x Pliny). No model
tested here reproduces it. Scripts: `meaning/pliny.py`, `ab_internal.py`.

### 4. Not a 'received' language like Enochian: free invention does not make Voynich's word template

Dee's Enochian Calls (1584, as printed by Casaubon 1659; 2,513 words) against Voynich, modern gibberish volunteers and
real Latin and Italian, 1,000-word samples:

| text | h1 - h2 (bits) | adjacent repeats | type-token ratio |
|---|---|---|---|
| Enochian | 0.69 | 0.000 | 0.71 |
| Gibberish volunteers | 0.60 | 0.001 | 0.83 |
| Latin (Pliny) / Italian | 0.63 / 0.80 | 0.001 | 0.68 / 0.50 |
| Voynich herbal A / B | 1.66 / 1.70 | 0.021 / 0.007 | 0.52 / 0.53 |

Enochian behaves like ordinary language and like modern gibberish. Voynich alone has the highly predictable glyph
sequence (large h1 - h2) and the repeated adjacent words. Whatever made Voynich, it was not free invention of words:
it was a learned, rigid template. A 2022 paper at the Malta Voynich conference ("Fingerprinting Gibberish", Sloane
MS 3188) reached the same verdict from other measures (hapax rate) on a different Enochian source; this is an
independent confirmation. Script: `meaning/enochian.py`.

### 5. Simple verbose ciphers are excluded, with calibrated solvers

A blind solver was first shown to break Voynich-like verbose ciphers of Latin (synthetic gates: 0.989-1.000 recovered,
including homophones, 2-3 glyph codes and meaningless spaces, and a positional variant). Then every Voynich group
(Currier A/B, scribe groups, sections) was attacked as Latin, Italian, German, Catalan and abbreviated Latin, with
fixed and positional units (about 2,900 jobs): every cell stayed at the failed level (per-character score -2.3 to
-3.0 against -1.95 for the solved synthetics). A one-glyph-group = one-letter verbose cipher of these languages is
excluded within the tested range. Zhang & Sheng (arXiv 2610.34499, Oct 2026) reach the same conclusion
independently. Scripts: `verbose/`.

### 6. No repeated phrases, which leaves a crib attack nothing to anchor on

In 30,000 tokens Voynich has 134 repeated 3-word phrases, 1 repeated 4-word phrase and none of 5 words; natural
languages 926-1,585 / 221-559 / 66-292. Random choices of spelling (Naibbe: 113 / 1 / 0) erase phrase repeats the
same way. Script: `meaning/phrase_repeats.py`.

### 7. Whole-word codes, including homophonic ones, do not fit

With little homophony, a word code keeps too much word-to-word predictability; with enough to bring it down to
Voynich's level (4-16 code words per frequent word), the phrase repeats vanish (random choice) or the scribes stop
differing (habitual choice: between-scribe ratio about 1.5 against 2.97, held-out b3 5-8/30). Homophone classes
cannot be found directly at Voynich's length: the method fails its own power check on synthetic codes (ARI 0.01-0.04
against the required 0.3). Scripts: `meaning/robustness.py`, `stemcode.py`, `habitcode.py`, `homclass.py`;
protocols in `meaning/homophone_plan.md`.

### 8. The text does not follow its pictures

A plant drawn twice (herbal page and pharmaceutical page) brings no shared words to the second page (percentile 0.32
against 0.5; the test detects same-leaf vocabulary at 0.65, p 0.0015). Herbal pages share no opening formula, and
zodiac labels carry no positional day or degree names (aligned similarity 0.320 against 0.319 shuffled). Yet pages and
leaves do have their own vocabulary, as strongly as a real topical text (result 3).
Scripts: `meaning/duplicates.py`, `formula.py`, `zodiac.py`.

### 9. The line is the unit of production (10 Nov 2026)

The last glyph of a word predicts the first glyph of the next (normalised MI 0.060, three times Latin's 0.019), but
only inside a line: across a line break it is 0.0004, while Latin and English poured into the same lines carry
theirs across unchanged (0.019 inside, 0.022 across). It is strictly adjacent (lag 2: 0.003). The line also has a
shaped start and end two words deep (word 1 JSD 0.205 from interior words, word 2 0.020; last word 0.049,
penultimate 0.010). The boundary rule is one rule with an A/B modification (PMI-matrix correlation within A or B
0.92-0.94, A vs B 0.77; the two B hands 0.93). And near-copies are not taken from the word above: against a null
that keeps position vocabulary, vertical alignment is 1.01 (the autocopist, which copies from the same position by
construction, shows 1.04 with same-index 1.22); the near-copy locality is in the same line. Whatever made the text
worked line by line, with a word-to-word memory that restarts at each line. A cipher of running prose does not do
this; an itemised plaintext or a clerk restarting a chained table at each line would. Scripts: `lines/`.

### 10. Where re-use lives, and a generator fitted by likelihood (10 Nov 2026)

A hierarchical Pitman-Yor model (book > hand > section > quire > page > line) fitted to the word tokens: Voynich
re-uses whole words at the hand, section and quire levels (13-18% of draws at each), 5% at the page, none at the
line; Pliny laid out leaf by leaf 2-7% at every level, English 4-8%, the autocopist 27% at the page only, gibberish
volunteers 18% at the page. The hierarchy saves 0.23 bits/token over a flat model (English 0.02). Whole-word re-use
is weak at the page because the locality is in near-copies, so the model was moved to word parts (opener, middle,
ending): with nothing tuned on the battery, a version with the slots chained inside the word reaches 25 of 30
held-out items (the best count of any model here), the line-bound coupling (0.05 of 0.06, zero across lines) and
the quire drift, but only half the A/B convention; a version with independent slots reproduces both scribe
ratios (2.5-2.95 / 1.7-2.0 against 2.96 / 2.00) and the A/B drift as a faithful sample of its fit, but breaks the
words. The ending convention is context-free and the chain is context-bound, and one tree cannot hold both: the
duel of #33 in fitted form. Scripts and caveats: `reinforce/README.md`.

### 11. Human improvisers, read with their own lines and pages (10 Nov 2026)

The Gaskell-Bowern volunteers' transcriptions keep their written lines, page breaks and paragraphs (38 writers, 88
pages, 10,049 words), which every earlier use here threw away by pouring the words into the Voynich skeleton. Read
as written, with the tests and fits of sections 9 and 10 (and Voynich refitted with a script-neutral word split so
that both get one model), the volunteers have the scribe-level habits and none of the line-level or book-level
structure. Each writer has an ending habit more distinctive than a Voynich hand's (scribe ratio on last units 3.40
against 2.13), re-uses his own words at 20% of draws (a hand 18%), and keeps that habit as a context-free layer on
top of a within-word chain (ending re-use at the writer 64%, 49% once the preceding unit is known). But adjacent
words are not coupled at all (0.003 inside a line against Voynich's 0.059; five of 35 writers show some, against 62
of 128 Voynich pages of the same size), so there is nothing to restart at a line; the line-first word has no
vocabulary of its own (JSD 0.012 against 0.205) and the last word is longer, not shorter; the within-word chain is
four to six times weaker (excess MI 0.09 against 0.56; 0.8 against 1.4 bits in the fitted model); and no word stock
is shared between writers (the root of the fit is a pass-through), where Voynich takes 47% of its root draws from a
stock shared across hands (English in the same skeleton 51%, Latin 22%; 0.68 types per token against 0.20). The
one thing they do that Voynich does not is align a near-copy weakly under its source (1.06, z 2.2). Casual
improvisation by untrained writers gives the personal habits, not the line structure, the chain or the shared
stock; whether a practised writer of one taught system would is untested, there being no such sample. Tables:
`reinforce/gibberish_fit.md`.

## 12. Second session of 10-11 Nov 2026: lines are composed, not wrapped; the word needs a length budget

- The first word of a line is as much longer as wrapping any text would make it (+0.41 to +0.46 of +0.48 glyphs),
  but it is not the word that did not fit: its length is unrelated to the space left on the line above (r -0.01;
  wrapping 0.09-0.38). The last word is built to the remaining space in a vocabulary of its own, with endings (-am,
  -om) that Currier A and B share, and the A/B ending convention weakens by 40% there. A text wrapped from a
  stream, copied from an exemplar with other line breaks or enciphered word by word would show the overflow
  signal. Tables: `lines/README.md` s5-6.
- Word parts share a length budget (a longer start is followed by a shorter middle and ending); the Naibbe cipher
  has it too. The scribe and language habits are close to context-free in held-out likelihood. A generator that
  borrows the book's transition tables reaches 23-26 of 30 held-out battery items, the best and steadiest so far,
  but loses the A/B and scribe convention, which does not emerge from re-use and has to be a parameter of the
  language and the hand. Tables: `reinforce/README.md` s4.

Reproduce: `lines/wrapping.py`, `lines/edges.py`, `reinforce/lengths.py`, `reinforce/product.py`, `reinforce/slots6.py`;
exact commands in the Reproduce tables of `lines/README.md` and `reinforce/README.md`.

## 13. 11 Nov 2026: five follow-ups

Lines are filled to a margin and are not list items, and no rate of trimming the overflow word reproduces both the
missing overflow signal and the last-word length; the line-final -am/-om words are a line-end form used at a fixed
rate, not padding; labels follow the word recipe without the line effects or the length budget; a generator with the
convention drawn as a graded preference carries a quarter to a half of the A/B difference (the convention is a few
endings switched on or off), and with 10% copying of nearby stems its best seeds reach 32 of 37 battery items; a
verbose cipher with a nomenclator layer gives no signal (Kaggle, calibration passed). Tables: `lines/README.md` s7,
`reinforce/README.md` s4.4, `verbose/README.md` tier 5.

Reproduce: `python lines/listcipher.py`, `python lines/lineend.py`, `python lines/labels.py`, `python
reinforce/slots7.py generate tilt7_q0 tilt7_q10 tilt7_q20 notilt7_q10` then `report`, and for the cipher tier
`verbose/kaggle_pkg/build_kernel5.py` (Kaggle) or `gpu_sweep.py --tier 5` then `analyze5.py`; all from
`targets/voynich`, prerequisites in the Reproduce sections of the three READMEs.

## 14. 11 Nov 2026: generator v8

The scribes' convention is a few large switches (one value in twenty to fifty per level; a language changes a switched
ending by a factor of about 40), measured by the fourth moment of the log-ratios. The battery does not separate that
from a graded preference, and section 13's 'a quarter to a half' was partly an exponent of 0.75 in that generator: at
full strength a graded preference carries a third to most of the A/B difference. Voynich's own convention on slot
frequencies gives three quarters of the A/B difference; with separate transition tables for A and B the generator
gives 0.092-0.095 of 0.101 and 31-33 of 37 battery items on every seed. Languages A and B differ in how word parts
follow one another, not only in which parts they prefer. No variant passes 33 of 37; the clustering beyond the page is
closer and not reached. Table: `reinforce/README.md` s4.5.

Reproduce (from `targets/voynich`): `python reinforce/slots8.py generate norm8 cat8 emp8 cat8p emp8p lang8`, then
`python reinforce/slots8.py report` -> `reinforce/slots8_gen.md`.

## Where this leaves the hypotheses

Best supported: meaningless text, made page by page by several people from one shared, learned word template, each
with strong personal habits, working with page-level material. Not random gibberish (free invention, section 11, has the personal habits but not the shared
stock, the chain between words or the line structure), and not a cipher or code of a real text in any form tested here.

Still open: a two-key nomenclator with more than half its words miscopied (Zhang & Sheng), which would leave the text
unreadable anyway; units of two letters, syllables or nulls in a verbose cipher; other plaintext languages.

What no tested model reproduces: the drift of glyph statistics between parts of the book (Currier A/B and quire to
quire, 0.050 within sections against 0.004-0.007 for a real topical text). Any explanation has to produce that drift
together with template-built words, page-specific vocabulary, the scribe differences and the absence of repeated
phrases.

## Files

- `HYPOTHESES_2026-10-28.md`: every test in order (#1-#63 plus the 29 Oct homophone tests), and the hypothesis table.
- `meaning/README.md`, `verbose/README.md`, `glyphs/README.md`, `controls2/README.md`, `lines/README.md`, `reinforce/README.md`: detailed tables per programme.
- `data/`: ZL3b transliteration (René Zandbergen, voynich.nu), parsed to words.
- Bulky regenerable data (language-model tables, transformer checkpoints) is archived in the private Kaggle dataset
  socializedape/voynich-archive.
