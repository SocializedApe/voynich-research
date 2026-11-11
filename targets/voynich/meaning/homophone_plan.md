# Whole-word code with homophones: two planned tests (written 29 Oct 2026; both run 29 Oct 2026: H2 power check failed, H1 not a fit)

Status: H2 run (`homclass.py`, results `homclass_results.json`); its power check failed, so H2 cannot
decide at Voynich's length. H1 run (`habitcode.py`, `habitcode_results.json`): not a fit.

## Why the hypothesis needs a new test

The whole-word code of a real text, written out by a copying scribe, is one of the open hypotheses
(`../HYPOTHESES_2026-10-28.md` s2). Its standing rests on a tie on b3 (24-25/30 held-out, #12) and on the homophony
sweep (#25, `robustness.py`): Voynich's previous-word signal (+0.105 bits/word) falls between K 4 and 8 code words per
frequent word for Latin (0.149 / 0.081) and near K 16 for Italian (0.120).

But the homophony needed for that signal breaks two other items (#37, `stemcode.py`):

| Need | K required | Measured |
|---|---|---|
| word signal at Voynich's +0.105 | 4-8 (Latin), ~16 (Italian) | `robustness.py` |
| 3-word phrase repeats near Voynich's 144 | low | K 8: 2-9 |
| scribe ratios near 2.96 / 2.00 | - | K 8: 1.2-1.4 / 1.0-1.2 |

Every code tested so far picks a homophone at random on each use. Random choice erases phrase repeats and raises the
within-document floor, as it does for the ciphers (#26, #34). So the hypothesis survives only in a form not yet run:
homophones chosen by habit. And no test so far asks whether Voynich contains homophone classes at all.

## Test H2 first: are there homophone classes in Voynich? (model-free)

Homophones of one plaintext word are interchangeable: they share neighbouring words and pages while looking unrelated.
Improvised text and letter ciphers have no reason to produce such classes among dissimilar words.

Protocol:

1. Power check (synthetic, known answer). Pliny (Latin) and the Italian control, cut to Voynich length (about 34,800
   tokens, fixed parse). Encode with K 4, 8, 16 homophones per word with at least 5 tokens, with random choice and with
   habitual choice (H1's generator at its default setting). Negative controls: the improviser (s 0.6, p 0.2), round-8
   cipher + copying scribe, Naibbe, shuffled Voynich.
2. For every word type with at least 10 tokens: a context vector of left and right neighbours (smoothed counts,
   PPMI) plus a page-occurrence vector. Cluster (agglomerative, cosine; number of clusters chosen by silhouette, not by
   the answer).
3. Score on the synthetic codes: ARI of clusters against the true homophone sets, counting only pairs of words at
   glyph edit distance >= 3 (so spelling near-variants and copying-scribe edits do not count).
4. Score that needs no answer, computed on every text: the excess of context similarity among dissimilar pairs
   (edit distance >= 3) in the top 1% of similarities over a page-shuffled null (200 permutations).

Pass rule for the power check: at K 8 with habitual choice, ARI >= 0.3 and the no-answer score above every negative
control's 95th percentile. If the power check fails, the test cannot decide at Voynich's length; record that and stop.

Reading, only if the power check passes: Voynich at or below the negative controls counts against a homophonic word
code (at the K values that pass). Voynich above them would be the first positive evidence for a meaning-bearing word
unit; follow up by listing the classes and checking they are not one scribe's or one section's vocabulary (repeat
within hand 2 B pages only).

## Test H1: homophones chosen by habit (generative)

Nomenclator users had favourite homophones and used them in runs. Generator:

- Plaintext: Pliny for A pages, the Italian control for B pages (as `stemcode.py`); Latin-only control.
- Each word with at least 5 tokens gets K homophones (K 4, 8, 16).
- Each scribe (ZL hand) draws a preference over each word's homophones: Dirichlet(alpha_s).
- Each quire perturbs it: Dirichlet around the scribe's preference with concentration alpha_q.
- Within a page, reuse the last homophone of that word with probability rho, else draw from the quire preference.
- Copying scribe from `duel.py` on top, unchanged.
- Grid: alpha_s 0.1 / 0.5 / 2, alpha_q 5 / 20 / inf, rho 0 / 0.5 / 0.8. Chosen on the scribe ratios only, as in
  `convention.py`.

Why it might work where random choice failed: across the book many homophones are in use (low word signal); inside a
page one dominates (phrase repeats return); scribes favour different homophones from one codebook (between-scribe ratio
up, shared rules kept); quires shift the preference (quire-scale drift, #32, which nothing so far supplies). #33 found
habits ineffective on round-8, but there chaining and page table subsets drowned them; in a word code the homophone
choice is the token.

Code-word vocabulary (the known weak point; stemcode's composed cores failed b3 at 6-7/30). Run both and report both:
(a) Voynich word types by rank (borrowed vocabulary, flagged as in #12);
(b) words from the improviser's template generator (template borrowed, words not).

Measures: scribe ratios (between, same scribe other document; Voynich 2.96 [2.18-3.59], 2.00 [1.87-2.15]),
rules / habits (0.891 / +0.307), k_jsd_halves (0.062), 3- and 4-word repeats (144 / 1), previous-word signal (+0.105),
b3 items (37, held-out 30).

Pass rule: both scribe ratios inside Voynich's intervals, 3-word repeats 72-216, word signal 0.07-0.15, and held-out b3
at least 26/30 (the improviser + convention layer's 24 plus the 2-item margin of `duel.py`). Any of these missed: not a
fit, and the result is reported as a trade-off as in #33.

## Order and cost

H2's power check first: cheap, and it decides whether a decisive test exists at this length. Then H1 (grid of 27
settings x 2 vocabularies x 2 plaintext set-ups, three seeds at the chosen point). Scripts to write:
`meaning/homclass.py` (H2), `meaning/habitcode.py` (H1).

## H2 result (29 Oct 2026)

Points the plan left open, fixed in `homclass.py` before the run: habitual choice = H1's grid middle (alpha_s 0.5,
alpha_q 20, rho 0.5); code words = distinct improviser-template words; every code through the copying scribe;
page-shuffled null = tokens shuffled within each page (keeps page vectors, breaks neighbours); a control's 95th
percentile = its excess E plus its null's 95th percentile above the null mean.

| text | types >= 10 | excess E | ARI |
|---|---|---|---|
| Latin K 4 / 8 / 16, random | 279 / 252 / 166 | +0.020 / +0.015 / +0.001 | 0.11 / 0.13 / 0.11 |
| Latin K 4 / 8 / 16, habit | 309 / 262 / 209 | +0.008 / +0.003 / +0.006 | 0.00 / 0.01 / 0.01 |
| Italian K 4 / 8 / 16, random | 454 / 443 / 375 | +0.008 / +0.010 / +0.002 | 0.27 / 0.25 / 0.06 |
| Italian K 4 / 8 / 16, habit | 454 / 421 / 410 | +0.002 / -0.001 / -0.002 | 0.02 / 0.04 / 0.01 |
| improviser / round-8 + scribe / Naibbe / shuffled Voynich | 434 / 434 / 456 / 489 | +0.000 / +0.000 / -0.001 / -0.000 | |
| Voynich | 489 | +0.0023 (null 95% +0.0010) | |

Highest control 95th percentile: +0.0013. Power check at K 8 habit: ARI 0.008 (Latin), 0.041 (Italian), both far
under 0.3; the score passes for Latin (+0.0032) and fails for Italian (-0.0014). **FAIL: H2 cannot decide at Voynich's
length.** Habitual choice is what defeats it: a page (and a quire) mostly uses one homophone per word, so homophones
of one word rarely share pages or neighbour patterns; even random choice reaches only ARI 0.11-0.27.

Not a reading, recorded only: Voynich's excess (+0.0023) is above every control's 95th percentile, the size of the
habit codes' excess (Latin K 4-16 habit +0.003-0.008, Italian about 0). Under the pass rule this decides nothing.

## H1 result (29 Oct 2026)

Fixed in `habitcode.py` before the run: K 8 for the grid and the pass rule (K 4 / 16 as sensitivity at the chosen
point); pass judged on the Pliny A / Italian B set-up (LI) on the mean of three seeds; LL (Latin on both) a control.

Grid (27 settings x 2 vocabularies x 2 set-ups, 108 texts): the between-scribe ratio never exceeded about 1.5 and the
same-scribe ratio about 1.35 anywhere (Voynich 2.96 [2.18-3.59], 2.00 [1.87-2.15]). Chosen points and results (mean of
seeds 0-2, K 8):

| set-up | alpha_s / alpha_q / rho | between / same | rules / habits | 3-word repeats | word signal | held-out b3 | misses |
|---|---|---|---|---|---|---|---|
| Voynich | | 2.96 / 2.00 | 0.891 / +0.307 | 144 | +0.105 | | |
| LI vocab | 2 / 20 / 0.8 | 1.29 / 1.24 | 0.961 / +0.020 | 25 | +0.071 | 5.3 | ratios, repeats, b3 |
| LI template | 0.1 / inf / 0.8 | 1.46 / 1.26 | 0.854 / +0.088 | 87 | +0.201 | 6.0 | ratios, signal, b3 |
| LL vocab (control) | 0.1 / 5 / 0.8 | 1.24 / 1.19 | 0.943 / +0.019 | 28 | +0.088 | 5.7 | |
| LL template (control) | 0.1 / 5 / 0.5 | 1.39 / 1.22 | 0.898 / +0.067 | 29 | +0.092 | 6.7 | |

K 4 / 16 (LI, seed 0) move the word signal and repeats (template K 4: 137 repeats, signal +0.275; vocab K 16: signal
+0.029) but not the scribe ratios (1.30-1.52) or b3 (5-7 held-out). k_jsd_halves 0.005-0.012 (Voynich 0.062).

**Not a fit.** Habitual homophone choice does what the plan hoped for phrase repeats (template: 82-93, from 2-9 under
random choice), but it cannot make the scribes differ: a word code shares one vocabulary across hands, and preferring
different homophones of it moves the between-scribe ratio from about 1.3 only to about 1.5, half of Voynich's. The
habits score (+0.02 to +0.10 against +0.307) says the same. Held-out b3 stays at 5-8 of 30, far under the 24 of the
improviser + convention layer. Together with H2 (homophone classes undetectable at this length), the homophonic
whole-word code survives no test run so far; its scribe ratios fail by a factor of two across the whole grid.
