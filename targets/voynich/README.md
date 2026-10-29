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

## Where this leaves the hypotheses

Best supported: meaningless text, made page by page by several people from one shared, learned word template, each
with strong personal habits, working with page-level material. Not random gibberish (free invention lacks the
template), and not a cipher or code of a real text in any form tested here.

Still open: a two-key nomenclator with more than half its words miscopied (Zhang & Sheng), which would leave the text
unreadable anyway; units of two letters, syllables or nulls in a verbose cipher; other plaintext languages.

What no tested model reproduces: the drift of glyph statistics between parts of the book (Currier A/B and quire to
quire, 0.050 within sections against 0.004-0.007 for a real topical text). Any explanation has to produce that drift
together with template-built words, page-specific vocabulary, the scribe differences and the absence of repeated
phrases.

## Files

- `HYPOTHESES_2026-10-28.md`: every test in order (#1-#45 plus the 29 Oct homophone tests), and the hypothesis table.
- `meaning/README.md`, `verbose/README.md`, `glyphs/README.md`, `controls2/README.md`: detailed tables per programme.
- `data/`: ZL3b transliteration (René Zandbergen, voynich.nu), parsed to words.
- Bulky regenerable data (language-model tables, transformer checkpoints) is archived in the private Kaggle dataset
  socializedape/voynich-archive.
