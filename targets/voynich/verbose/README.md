# Verbose cipher: a gated attack (started 28-29 Oct 2026)

Status: closed (29 Oct 2026). The gated pipeline breaks every synthetic verbose cipher built for it (plain,
homophonic with spaces carrying no word boundaries, abbreviated Latin, positional) blind, and finds nothing in any
Voynich Currier or scribe group, in Latin, Italian, German, Catalan or abbreviated Latin. See 'Conclusion' at the end.

## Why a verbose cipher

In a verbose cipher every plaintext letter is written as a short group of glyphs (2-3, possibly with a few
alternative groups per letter); a word is a string of such groups. The case for testing it:

- Glyph statistics. A 24-glyph verbose cipher of Latin with 2-3-glyph codes reproduces Voynich's character entropies
  (h1 3.90, h2 2.33 against Voynich 3.87, 2.31; `../NOTES.md` 4.1, `../a1_charstats.py`). No one-sign-per-letter
  system can: substitution, homophones, nulls and nomenclators keep h2 at or above the plaintext's (2.8-4.4 in 17
  real 15th-century ciphertexts, `../results/c3.md`), while Voynich lies near 2.0.
- Free invention does not give the template. Improvised gibberish (Gaskell & Bowern volunteers) and a period invented
  language (Enochian, 1584) have language-like h2 and no adjacent repeats (`../meaning/README.md`).
- Across every text run on the b3 battery (b3, c1, controls2), only Naibbe-type letter-unit ciphers and Markov chains
  trained on Voynich sit in Voynich's corner of h2, token predictability and type-token ratio together; whole-word
  codes with homophones multiply the vocabulary 2-4 times (`../controls2/`, `../HYPOTHESES_2026-10-28.md`).

What the other studies fix for the design: Currier A and B are not one system under two glyph keys (no glyph mapping
links them, nor a scribe's two styles; `../meaning/keymap*.py`), so A and B must be attacked separately. Word spaces
behave like the boundaries of template units, not of plaintext words (`../glyphs/README.md` s5), so the attack works
on glyph streams without relying on Voynich spaces as plaintext word boundaries.

## Plan

1. Gate (synthetic, known answer): break a Voynich-like verbose cipher of Latin blind. Pass: similarity >= 0.80 of the
   first 3,000 decrypted letters to the plaintext. Until a gate passes, no Voynich run is interpreted.
2. Units on Voynich: cut the glyph stream into units chosen without any plaintext, by the settings the gate validates.
3. Solve each system separately (herbal A, about 11,000 words; herbal B), against Latin and Italian, with
   shuffled-text controls and a success rule fixed before the run. A validated pipeline that finds nothing makes a
   simple verbose cipher of Latin or Italian unlikely, which is itself a result.

## Gate 1 (`gate.py`, 28 Oct 2026, about 2 hours on 2 threads)

Plaintext Pliny (Latin normalisation), cipher `a1_charstats.verbose_cipher_map` over 24 glyphs with 0 one-glyph,
24 two-glyph and the rest three-glyph codes (seed 6), word spaces kept. Pipeline without the table: SentencePiece
unigram units (vocabulary K, pieces up to 4 glyphs, learned on the cipher words) -> `attack_v0.solve` (unit ->
letter, 5-gram Latin model without spaces), best objective of 3 seeds.

| Words | K | units used | words cut exactly at code boundaries | similarity | per-char LM score |
|---|---|---|---|---|---|
| 11,000 | 30 | 25 | 38.6% | **0.797** (fail by 0.003) | **-2.462** |
| 11,000 | 40 | 32 | 37.5% | 0.742 | -2.592 |
| 11,000 | 60 | 49 | 12.9% | 0.051 | -2.942 |
| 20,000 | 30 | 29 | 0.0% | 0.067 | -2.685 |
| 20,000 | 40 | 39 | 0.0% | 0.103 | -2.773 |
| 20,000 | 60 | 56 | 5.0% | 0.093 | -2.880 |

Best blind decryption: `munerumetetocetuoercumetuenominealiiocaeliumaapapeliliareliistuitcuius`; plaintext:
`mundumethocquodcumquenominealiocaelumappellarelibuitcuius` ('... nomine alio caelum appellare libuit cuius').

- Failed by the rule, by 0.003. Where the units are close to the codes, the solver nearly reads the text.
- The units, not the solver, are the bottleneck. With more text SentencePiece merges frequent pairs of codes into
  single pieces and the segmentation collapses (0% exact at 20,000 words).
- The best setting is recognisable without the answer: the highest per-character LM score (-2.462) is also the most
  accurate run. On Voynich, where there is no answer, the same score can choose the units.

## Gate 2 (`gate2.py`, 29 Oct 2026): passed

As gate 1, with SentencePiece pieces capped at 3 glyphs and K in (30, 36, 42, 50, 60); per text size the K with the
best per-character LM score is chosen without the answer, and only that run decides.

| Words | K | pieces used (by length) | segmentation exact | similarity | per-char |
|---|---|---|---|---|---|
| 11,000 | 30 | 25 (14 one, 11 two) | 38.6% | 0.801 | -2.467 |
| 11,000 | 36 | 28 (11, 17) | 88.5% | 0.967 | -2.019 |
| 11,000 | **42 (chosen)** | 22 (2, 20) | 100.0% | **1.000** | **-1.946** |
| 11,000 | 50, 60 | 21 (two-glyph) | 100.0% | 1.000 | -1.946 |
| 20,000 | 30 | 25 (14, 11) | 38.6% | 0.773 | -2.494 |
| 20,000 | 36 | 26 (9, 17) | 87.8% | 0.963 | -2.062 |
| 20,000 | 42 | 22 (2, 20) | 100.0% | 0.119 (solver stuck) | -2.941 |
| 20,000 | 50, **60 (chosen)** | 21 (two-glyph) | 100.0% | **1.000** | **-1.997** |

Pass at both sizes. With pieces capped at the code length the unit model recovers the code table exactly, and the blind
choice by LM score also screens out a stuck solver run (20,000 words, K 42). Limits: this cipher turned out to use only
two-glyph codes, no alternative codes, and its spaces are the plaintext's word boundaries; Voynich differs on all three.

## Gate 3 and exploratory Voynich run (`gate3.py`, `voy1.py`; protocols in the scripts)

The local run of `gate3.py` was stopped after its first setting (K 36: similarity 0.092; log `gate3_run.log`) once the
GPU calibration below had run gate 3 at every setting (passed, 0.989).

### Exploratory Voynich run (`voy1.py`, gate-2 pipeline): no signal

| Text | language | chosen K | per-char | shuffled control | verdict |
|---|---|---|---|---|---|
| herbal A (7,953 words) | Latin | 50 | -2.814 | -1.720 (degenerate 'iiii...') | no signal |
| herbal A | Italian | 50 | -2.875 | -2.566 (degenerate) | no signal |
| herbal B (3,453 words) | Latin | 36 | -2.885 | -1.659 (degenerate) | no signal |
| herbal B | Italian | 36 | -2.783 | -2.523 (degenerate) | no signal |

All four score at the level of failed synthetic runs (-2.8 to -2.9; solved ones -1.95 to -2.0). Every shuffled control
collapsed into strings of 'i' (Roman-numeral runs in the training corpora reward them), so the rule's 'beat the
shuffle' clause was void; the sweep (`kaggle_pkg/`) replaces it by a letter-KL degeneracy guard and key stability
between independently solved halves. Not conclusive: the pipeline is validated only on gate 2.

## The sweep (`kaggle_pkg/`, `prepare.py`)

Self-contained package (numpy, sentencepiece; no repository imports, no internet), written by `prepare.py`:
`solver.py` (the attack_v0 annealer with incremental scoring of the changed order-5 windows and swap moves; checked
equal to a full recomputation to 2e-7 relative on every language), `sweep.py` (job grid, sharding, all cores, one
JSON line per job, resumable, deadline), `analyze.py` (decision rule), and `data/` (texts, synthetic ciphers with
their plaintext, the lang/ letter-only order-5 tables and letter frequencies for Latin, Italian 1490-1620, German
1470-1610 and Catalan).

Grid (1,392 jobs): texts Voynich A herbal, B herbal, A all, B all, hand 1 pharmaceutical, hand 2 biological, hand 3
stars, and the calibration ciphers syn_gate2 and syn_gate3; languages la, it, de, ca (calibration: la); variants raw and
nogal (line-initial gallows dropped); K 36, 42, 50; parts full, h1, h2, shuf; seeds 1, 2.

Decision rule (in `analyze.py`, fixed before any result): per cell the best-objective seed; key stability = agreement
of the keys solved independently on the two halves (weighted by unit counts; chance about 0.06-0.08); degenerate =
letter KL > 0.15; K chosen blind by the best non-degenerate per-character score; SIGNAL if per-char >= -2.2, not
degenerate, stability >= 0.5, and per-char >= shuffled + 0.3 (stability >= 0.7 if the control is degenerate). Only
read if the calibration ciphers give SIGNAL with similarity >= 0.8 and no shuffled Voynich control passes.

Cost: one 64,000-unit job took 44 minutes on the shared local CPU (decryption exact). Tier 1 (288 jobs: A/B herbal and
all, Latin and Italian, K 42 and 50, plus calibration) runs on four Kaggle CPU sessions since 29 Oct, 13:10
(`socializedape/voynich-verbose-s0..s3`, dataset `socializedape/voynich-verbose`, 11-hour deadline). Tier 2 (the other
1,104 jobs) waits for a GPU solver that scores many annealing chains at once.

## GPU solver and calibration (`kaggle_pkg/gpu_sweep.py`, 29 Oct 2026)

All annealing chains of one (text, variant, language) run as one batch on a T4 (3 K x 4 parts x 2 seeds x 4 restarts =
96 chains), each rescored in full at every step; same objective and moves as solver.py (objective agreement with the CPU
recomputation checked exactly). A batch of 24 jobs takes 7-9 minutes, about 100 times the CPU rate per job.

Calibration on Kaggle (`voynich-verbose-gpucal`, results in `kaggle_results/gpucal/`), decision rule of analyze.py:

| Cipher | chosen K (blind) | per-char | letter KL | key stability (halves) | shuffled control | similarity | verdict |
|---|---|---|---|---|---|---|---|
| syn_gate2 (verbose24 Latin) | 42 | -1.946 | 0.007 | 1.00 | -1.682 (degenerate, KL 1.74) | 1.000 | SIGNAL |
| syn_gate3 (homophones, 2-3-glyph codes, unaligned spaces) | 50 | -1.955 | 0.007 | 1.00 | -1.672 (degenerate) | 0.989 | SIGNAL |

Gate 3 passes in the sweep (K 36: 0.09; K 42: 0.74-0.78; K 50: 0.989): with enough units the pipeline breaks a
homophonic verbose cipher whose spaces carry no plaintext word boundaries, and the halves give identical keys. The
calibration condition of the rule is met. Full GPU sweep of all Voynich texts launched (`voynich-verbose-gpufull`).

## Tier 1 result (CPU, `kaggle_results/tier1_cpu/`, 288 jobs, 29 Oct): no signal

Four Kaggle CPU sessions, 37-60 minutes each. Calibration passes again on the CPU engine (syn_gate2 SIGNAL, similarity
1.000; syn_gate3 SIGNAL, 0.989; stability 1.00). Every Voynich cell (A herbal, B herbal, A all, B all x Latin, Italian x
raw, nogal) is 'all degenerate' by the rule: no setting gives a decryption whose letter frequencies match the language.
Diagnostics regardless of the guard (best-objective seed per cell, K 42 and 50):

| | Voynich, 32 cells | solved synthetic |
|---|---|---|
| per-character LM score | -2.76 to -2.92 | -1.95 |
| letter KL to the language | 0.15 to 0.29 | 0.007 |
| key stability between halves | 0.00 to 0.66, erratic | 1.00 |

No cell approaches a decryption; the best (A herbal, Latin, raw, K 42: -2.760) is as far from -1.95 as any failed
synthetic run. Caveat on the rule: failed cells reach stability up to 0.66 because both halves start from the same
frequency-matched key, so the chance level is far above the 0.06-0.08 assumed; it must be measured on shuffled halves
before a signal could rest on stability (it decided nothing here: every Voynich cell fails per-char and KL).

## Full GPU sweep (`kaggle_results/gpufull/`, 1,344 jobs, 90 minutes on 2 x T4, 29 Oct): no signal

Every Voynich text (A herbal, B herbal, A all, B all, hand 1 pharmaceutical, hand 2 biological, hand 3 stars) x Latin,
Italian, German 1470-1610, Catalan x raw and nogal x K 36, 42, 50, with halves and shuffled controls. By the rule: 55
of 56 cells 'all degenerate' (no setting gives letter frequencies matching the language); the one cell passing the
guard (hand 2 biological, Italian, nogal, K 42: per-char -2.797, KL 0.142, stability 0.45) is no signal.

Best full decryption per text and language (any K, variant, seed):

| Text | Latin | Italian | German | Catalan |
|---|---|---|---|---|
| A herbal | -2.791 | -2.843 | -2.806 | -2.850 |
| B herbal | -2.754 | -2.793 | -2.802 | -2.970 |
| A all | -2.783 | -2.809 | -2.880 | -2.962 |
| B all | -2.770 | -2.777 | -2.777 | -2.807 |
| hand 1 pharmaceutical | -2.740 | -2.784 | -2.726 | -2.863 |
| hand 2 biological | -2.659 | -2.671 | -2.657 | -2.804 |
| hand 3 stars | -2.766 | -2.792 | -2.802 | -2.813 |
| solved synthetic (gates 2, 3) | -1.95 | | | |

Letter KL of these best runs 0.17-0.57 (solved synthetic 0.007). The highest score (hand 2 biological, German, K 36,
-2.657, KL 0.42) is the language model's commonest material, 'nteneenddenegenterinegesenerern...'. The tier-1 CPU run
gives the same picture for its subset with the other engine.

Reading: a verbose cipher in which each unit of 1-3 glyphs stands for one letter of Latin, Italian, German or Catalan
(homophones allowed, spaces free) would have been found: the same pipeline breaks such a cipher, built with Voynich-like
statistics, blind and exactly. Not tested: units standing for two letters, a syllable or nothing; the same glyph group
meaning different letters by word position; abbreviated plaintext; other languages; more than 50 units.

## Next

1. Fix the stability null (measure agreement on shuffled halves) before any signal may rest on it.
2. Positional units: tag each unit by its slot (word-initial, medial, final) so that the same glyph group may stand for
   different letters by position, as Voynich's slot grammar invites; calibrate on a positional synthetic first.
3. Abbreviated plaintext: Latin with the standard medieval abbreviations (-us, -um, con-, per-, pro-, -que as single
   signs), a language model trained on that, and a synthetic gate built from it.
4. Units of two letters or none (nulls), and K up to 100, each with its own synthetic gate.
5. More languages, if corpora exist: Occitan, Czech, Middle High German, Hebrew in transliteration.

## Tier 3: abbreviated Latin (`abbrev.py`, `kaggle_pkg/analyze3.py`; launched 29 Oct)

Medieval Latin scribes wrote frequent pieces as signs; if Voynich enciphers abbreviated Latin, decryptions must be judged
against abbreviated Latin. Transform (fixed in `abbrev.py` before any run), on each normalised Latin word: et -> '&',
est -> '=', initial con-/com- -> '7', per -> 'P', initial pro- -> 'R', initial prae- -> 'B', final -que -> 'Q', final
-rum -> 'M', final -us -> '9', final -m after a vowel and n before a consonant -> '~' (macron). One word-final sign per
word (militibusque -> militibusQ, where a scribe might write militib9Q). Alphabet 21 letters + 10 signs. On the Latin
corpus the transform shortens the text to 95.3%; signs per 1,000 symbols: ~ 44.7, 9 10.5, & 3.9, 7 3.5, Q 3.5,
P 3.0, M 2.8, R 2.0, = 1.4, B 0.9. Sample: 'reuertere~tur i~terea ea legione qua~ secu~ habebat militibusQ ...
7uenera~t ... sequanoM'.

Model: order-5 letter-only model of the abbreviated corpus (lang DenseLM, 31 symbols); abbreviated Pliny scores
-2.046 per symbol under it. Gate 4 (calibration): abbreviated Pliny, 11,000 words, enciphered as gate 3 (39 codes for
31 symbols, homophones, unaligned spaces; seed 9). Grid: seven Voynich texts x raw, nogal x K 42, 50, 60 x parts full,
h1, h2, shuf and s1, s2 (the two halves of the shuffled stream, to measure the chance level of key stability) x seeds
1, 2 (540 jobs, GPU). Rule (analyze3.py): calibration must reach similarity >= 0.8 and stability - null >= 0.3; its
per-character score minus 0.25 is the threshold PC*; a Voynich cell is SIGNAL at its blind K if per-char >= PC*,
letter KL <= 0.15, stability >= 0.5 and stability - null >= 0.3.

### Tier 3 result (`kaggle_results/tier3/`, 540 jobs, 29 Oct): calibration fails on stability; no Voynich cell near a decryption

By the rule: calibration FAILS, so no Voynich cell is interpreted. Gate 4 itself is decrypted (K 60: similarity
0.998, per-char -2.083, letter KL 0.008, stability 0.99), but its stability margin over the measured null is 0.23
(null 0.76) against the required 0.3.

The null is the finding: key agreement between the two halves of a shuffled stream is 0.72-0.89 on every text. Both
halves start from the same frequency-matched key and end with the frequent units on the same letters whether or not
anything is decrypted, so stability as defined (all units, weighted by count) barely separates a solution from noise,
and the chance level of 0.06-0.08 assumed in analyze.py was wrong (tiers 1 and 2 were decided by per-char and KL, so
their verdicts stand). A usable stability measure must exclude what the frequency-matched start fixes, e.g. agreement
on units outside the most frequent ones, or agreement of the decrypted text of the two halves under each other's keys.

On the two criteria that work, every Voynich cell (seven texts x raw, nogal x K 42, 50, 60) is far from the calibration:
per-char -2.750 to -2.962 against -2.083 (threshold -2.333), letter KL 0.240 to 0.427 against 0.008, all degenerate by
the guard. The best (hand 2 biological, raw, K 42, -2.750) is the level of a failed run. Abbreviated Latin, one unit per
symbol, shows no sign of a decryption; this is a diagnostic reading, not the rule's verdict.

## Tier 4: positional units (`positional.py`, `kaggle_pkg/analyze4.py`; launched 29 Oct)

The earlier sweeps let several glyph groups stand for one letter (homophones), but never one group for several letters.
In a positional system the same group means different letters by its place in the cipher word, as Voynich's rigid slot
grammar invites (q 99% word-initial, n 99% and y 87% final; Naibbe's separate head and tail tables). Every unit is tagged
start / mid / end of a word of two or more units, or only (a one-unit word), and the tagged units are solved as separate
symbols (herbal B at K 42: 126 symbols).

Gate 5 (calibration): Pliny, 11,000 words; a pool of 30 codes; four position tables drawn independently from the same
pool, so 27 of the 30 codes stand for two or more letters by position; cipher words of 1, 2, 3 ... codes with breaks
carrying no plaintext boundaries (seed 10). Grid (720 jobs): seven Voynich texts x Latin, Italian, German, abbreviated
Latin x K 42, 50, and gate 5 at K 36-60, each with full, halves, shuffled control and shuffled halves, two seeds.

Rule (analyze4.py, fixed before results): key stability is judged as its normalised excess over the measured chance
level, (stability - null) / (1 - null) >= 0.5 (on the tier-3 numbers gate 4 would score 0.96 and every Voynich cell
negative); the per-character threshold is gate 5's score minus 0.25, for every language; calibration must reach
similarity >= 0.8 and normalised stability >= 0.5; a Voynich cell is SIGNAL at its blind K if per-char >= threshold,
letter KL <= 0.15 and normalised stability >= 0.5.

### Tier 4 result (`kaggle_results/tier4/`, 720 jobs, 29 Oct): calibration passes, no signal

Calibration passes: gate 5 (positional, 27 of 30 codes ambiguous by position) at K 60, similarity 1.000, per-char
-1.946, KL 0.007, stability 1.00 against a null of 0.70 (normalised 1.00); threshold PC* = -2.196. Every Voynich cell
(seven texts x Latin, Italian, German, abbreviated Latin) is 'no signal' or 'all degenerate'. Positional tags give the
solver more symbols, and scores rise (per-char -2.32 to -2.74 against -2.66 to -2.97 untagged), but no cell combines the
threshold with matching letter frequencies.

The highest-scoring cell, hand 2 biological in German (K 50: per-char -2.324, normalised stability 0.67), is the German
model's commonest material: 'ndstdenerunseneruneninenendenddenstundenarinemdereninsten...', with e 29% and n 26% of the
letters (German about 16% and 10%; KL 0.35, flagged degenerate). Both halves fall into the same attractor ('en', 'er',
'den'), which Voynich's own repetitiveness (qokeedy qokeedy, chedy chedy) fits easily; the shuffled control, without that
repetition, scores -3.78. Not a decryption.

## Where the verbose programme stands (29 Oct 2026)

Validated pipeline (gates 2-5: plain, homophonic with unaligned spaces, abbreviated Latin, positional; all broken blind,
setting chosen blind) against every Voynich Currier and scribe group:

| Plaintext model | units | result |
|---|---|---|
| Latin, Italian, German 1470-1610, Catalan | 36-50, one letter each | no signal (tiers 1, full sweep) |
| abbreviated Latin (ten scribal signs) | 42-60 | far from a decryption (tier 3; rule void on the stability flaw) |
| Latin, Italian, German, abbreviated Latin, positional (one group, several letters) | 42-50 x 4 positions | no signal (tier 4) |

Excluded at this level: a verbose cipher in which each glyph group of 1-3 glyphs (fixed or by position in the word,
with homophones and arbitrary spaces) stands for one letter or scribal sign of Latin, Italian, German or Catalan. Still
open: units standing for two letters, a syllable or nothing (nulls); other plaintext languages; more than about 60 units
per position; a nomenclator layer (code words for frequent words beside the letter cipher).

## Conclusion (29 Oct 2026)

1. Within what was built and calibrated, the simple verbose family is excluded: no Voynich text group decrypts as a
   cipher in which each glyph group of 1-3 glyphs (fixed, or by position in the word; homophones allowed; spaces free)
   stands for one letter or scribal sign of Latin, Italian, German 1470-1610, Catalan or abbreviated Latin. The best
   Voynich cells reach per-char -2.3 to -2.7 only as degenerate attractors of the language model (letter KL 0.15-0.57),
   against -1.95 to -2.08 and KL 0.007-0.008 for every solved synthetic.
2. This agrees with Zhang & Sheng (arXiv 2610.34499, 25 Oct 2026), who reach the same verdict independently with
   calibrated solvers over 16 languages and more cipher families (Naibbe, word codes, syllable and word-class codes,
   one-key nomenclators); only a nomenclator with a second key whose scribe miscopies more than half of the words
   survives their tests in 9 of 16 languages. Tier 5 here (a nomenclator layer: `nomen.py`, la-nom / it-nom models and
   gate 7 built) was shelved unrun, as it would largely repeat their Cipher-MN.
3. Known limits of this pipeline, untested: copying noise (the synthetics are clean; Voynich was copied by up to five
   scribes), the full homophony of Greshko's real Naibbe tables (hundreds of glyph strings per letter; the sweep stopped
   at 60 units), medieval rather than classical Latin spelling in the language models, non-prose plaintext (lists,
   recipes, names), and units of more than 3 glyphs.
4. Reading, with the rest of the session (`../HYPOTHESES_2026-10-28.md` section 2): the evidence favours meaningless
   text produced page by page by several makers from one shared, rigid word template over any cipher tested here or by
   Zhang & Sheng.

Data archive (29 Oct 2026): the git-ignored `kaggle_pkg/data/` (language-model tables, texts, synthetic ciphers) and the transformer checkpoints `tfm/kaggle_run1/models/`, `tfm/kaggle_calib/models/` are archived in the private Kaggle dataset socializedape/voynich-archive and deleted locally (restore from `cyphersolver/`: `kaggle datasets download socializedape/voynich-archive --unzip`).
