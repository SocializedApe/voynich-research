# Hybrid model: a cipher of Latin written out by a copying scribe. Results, 28 Oct 2026

Script: `hybrid_model.py` (protocol committed in bc7cc98a before the first run; one crash fix after, protocol unchanged).
Base cipher: round-8 model of `cipher_models.py`. Scribe: with probability Q per token writes a near-copy of one of
his last W words on the page (edited with probability E: e/ee, k/t, ch/sh, o/a, o-/qo- added or dropped, final -y),
and opens a line with a gallows-led variant with probability G; missed spaces M.

## Protocol (fixed in advance)

Tuning: the seven profile items of `cipher_models.TARGET` plus three b3 items (e_w10, g_gal_init, b_len_sd); grid of
48 settings, seed 19, distance on these ten. Test: the best three settings, seeds 19 and 7, on the b3 battery;
reported score = matches on the 30 b3 items not used for tuning.

## Tuning grid, best three (ten-item distance)

| Setting (Q, W, E, G, M) | distance | edge | e_w10 | g_gal_init | b_len_sd | adj % |
|---|---|---|---|---|---|---|
| Voynich | | 0.054 | 0.276 | 0.223 | 1.788 | 0.935 |
| 0.15, 8, 0.9, 0.2, 0.05 | 0.150 | 0.025 | 0.269 | 0.241 | 2.104 | 1.016 |
| 0.15, 8, 0.9, 0.2, 0.00 | 0.157 | 0.024 | 0.276 | 0.243 | 1.772 | 0.984 |
| 0.15, 30, 0.9, 0.2, 0.05 | 0.177 | 0.025 | 0.199 | 0.241 | 2.092 | 0.857 |

## Held-out test (b3 battery, 30 items not used for tuning)

| Corpus | all 37 | held-out 30 | held-out misses |
|---|---|---|---|
| autocopist s19 / s7 | 12 / 15 | 11 / 14 | entropies, Zipf, vocabulary growth, f_lock, prediction, page items |
| Naibbe (Latin) | 20 | 19 | near-copy items, f_irrev, MZ peak, page continuity, drift |
| round-8 cipher model | 23 | 19 | as Naibbe plus length tail |
| hybrid 0 (0.15, 8, 0.9, 0.2, 0.05) s19 / s7 | 27 / 29 | **23 / 25** | b_len1, (b_len9), (e_cover, e_w10_shuf), e_ratio, (h_peak_R), j_jacc_excess, k_jsd_halves |
| hybrid 1 (0.15, 8, 0.9, 0.2, 0.00) s19 / s7 | 28 / 28 | **24 / 24** | b_len1, (e_w10_shuf), e_ratio, f_irrev, (h_peak_R), j_jacc_excess, k_jsd_halves |
| hybrid 2 (0.15, 30, 0.9, 0.2, 0.05) s19 / s7 | 27 / 32 | **23 / 26** | b_len1, d_adj_ld1, (b_len9, e_cover, e_w10_shuf), j_jacc_excess, k_jsd_halves |

## Reading*

1. A cipher of Latin of the round-8 kind, written out by a scribe who replaces about one word in seven by an edited
   copy of one of his last few words, matches 23-26 of 30 held-out statistics, against 19 for Naibbe and for the
   cipher alone and 11-14 for the self-citation generator. Neither layer alone comes close; together they do. This
   is the best fit to the b3 battery so far.
2. Cost: the copying overwrites chained words, so the edge coupling falls to about half of Voynich's (0.025 against
   0.054), a tuning item the hybrid now misses. A copying rule that keeps word openings (copies endings, or copies
   only among words with the same opening) would keep it.
3. Every hybrid still misses: single-glyph tokens (b_len1), adjacent-page vocabulary similarity (j_jacc_excess) and
   drift between the manuscript halves (k_jsd_halves). The last two point the same way: the model draws its page
   tables and null words independently per page, while Voynich changes gradually, so the next round is a slow
   drift (tables and nulls as a random walk through the pages). Those two items will then be tuning items, and the
   held-out pool shrinks to 28.
4. What this does and does not show. It is not a decipherment. It shows that a two-layer process (a period-plausible
   cipher and a copying scribe) reproduces most of what is measured, so "cipher" and "copying" are not exclusive
   hypotheses, as the field has mostly treated them. If the cipher layer is real, about 85% of tokens would carry
   plaintext and 15% would be scribal copies; an attack would first have to identify and discard the copies
   (near-duplicates of a recent word on the same page), then work on the remainder.

Limits: two seeds; one plaintext (Latin, Gutenberg); Greshko's tables, not tables fitted to Voynich; b3's match
rule (10% or the autocopist spread) is generous on some items; held-out items are not independent of tuned ones
(e_prev2 and e_w10 are related).

## Round 2 (`hybrid_model2.py`, protocol committed before the run): slow drift and opening-preserving copying

Tuning items: round 1's ten plus j_jacc_excess and k_jsd_halves; 28 held out. Grid of 16, best three on the battery:

| Corpus | all 37 | held-out 28 | edge |
|---|---|---|---|
| Naibbe (Latin) | 20 | 19 | 0.002 |
| round-1 hybrid best (s19) | 27 | 23 | 0.025 |
| R_T 0.1, R_N 0.1, same_open, Q 0.25 (s19 / s7) | 25 / 28 | 19 / 23 | 0.032 / 0.027 |
| R_T 0.1, R_N 0.1, any, Q 0.15 (s19 / s7) | 27 / 28 | 22 / 23 | 0.023 / 0.020 |
| R_T 0.1, R_N 0.1, same_open, Q 0.15 (s19 / s7) | 24 / 27 | 19 / 22 | 0.038 / 0.032 |

Slow drift brings adjacent-page similarity to 0.029-0.031 (Voynich 0.037; round 1 about 0.005) but not the drift
between halves (0.02 against 0.062), and moves the long-range peak to the wrong scale (h_peak_log2s now missed).
Opening-preserving copying keeps more edge coupling (0.03-0.04) but loses near-copy items. On the held-out items
round 2 does not beat round 1. The remaining misses trade against each other; round 1 stays the best model.

## Test of the hybrid's mechanism on the real text (`copy_split_test.py`, predictions committed before the run)

Words split by whether they are a near-copy (edit distance <= 1) of one of the previous 8 words on the page; edge
coupling (last unit of the previous word -> first unit of the word) measured in each group against a permutation null.

| Text | near-copies: n, coupling | other words: n, coupling | ratio other / copy |
|---|---|---|---|
| **Voynich** | 6,814, **0.075** | 19,787, 0.057 | **0.76** |
| hybrid round 1, s19 / s7 | 6,746 / 7,194, 0.008 / 0.010 | 19,855 / 19,407, 0.042 / 0.033 | 5.6 / 3.5 |
| pure cipher (round 8) | 3,387, 0.035 | 23,214, 0.058 | 1.6 |
| autocopist s19 / s7 | 6,648 / 9,433, 0.003 / 0.004 | 16,410 / 18,464, 0.004 / 0.002 | about 1, both near zero |

**The hybrid's prediction fails.** In Voynich the near-copy words obey the boundary rule more strongly than the other
words; in the hybrid they barely obey it, because the copying layer overwrites chained words. So the copying in
Voynichese is not a layer laid over a cipher: whatever makes the near-copies also makes the boundary coupling. One
integrated process is indicated, for instance a copy-and-modify scribe whose choice of source or edit depends on how
the previous word ended, or a chained cipher fed highly repetitive plaintext (the same plaintext in the same context
gives near-identical, equally coupled words). The round-1 hybrid remains the best fit to the b3 battery, but its
mechanism is refuted; the battery fit alone was not evidence for it.

## Candidate 2: a chained cipher of formulaic Latin (`copy_split_test2.py`, decision rule committed before the run)

Plaintext: Apicius, De re coquinaria 1-5, and Cato, De agri cultura (The Latin Library; 22,387 words); control: the
Latin prose corpus. Rule: survives if ratio other/copy < 1 with both seeds and near-copy share >= 15%; fails if the
ratio is >= 1 with both seeds.

| Text | near-copy share | copy coupling | other coupling | ratio other/copy |
|---|---|---|---|---|
| Voynich | **0.256** | 0.076 | 0.057 | **0.76** |
| chained, formulaic, s19 / s7 | 0.090 / 0.125 | 0.087 / 0.074 | 0.077 / 0.059 | 0.89 / 0.79 |
| chained, prose, s19 / s7 | 0.089 / 0.130 | 0.087 / 0.071 | 0.079 / 0.056 | 0.91 / 0.78 |
| chained + null words, formulaic, s19 / s7 | 0.127 / 0.150 | 0.033 / 0.037 | 0.058 / 0.047 | 1.76 / 1.28 |
| chained + null words, prose, s19 / s7 | 0.127 / 0.157 | 0.035 / 0.035 | 0.058 / 0.046 | 1.68 / 1.30 |

**Verdict by the rule: undecided** (ratio < 1 with both seeds, but the near-copy share is 9-13%, under 15%).

Reading*: (1) a chained cipher without nulls reproduces the direction of Voynich's copy split: near-copies arise in
the same boundary context and inherit the coupling. (2) The formulaic plaintext is not the cause: prose gives the same
ratio and the same near-copy share; repetitive text did not add near-copies. (3) Null words reverse the pattern
(uncoupled copies), so frequent nulls in Voynichese are disfavoured. (4) What remains unexplained is the quantity:
Voynich has about twice the near-copies of any cipher here, and they carry the boundary rule. A copier whose choice
of source or edit depends on the previous word's ending (candidate 1) is the mechanism left to test for that.

## Candidate 1: a context-sensitive copier (`candidate1.py`, protocol committed before the run)

A pure generator: each word an (edited) copy of a recent word on the page or of the previous page's tail; source words
weighted by 1 + K when their own predecessor ended like the word just written (K = 0: plain copier, the control);
fresh slot words with probability F; line-initial gallows G = 0.2. Grid of 48 on the hybrid's ten tuning items.

Grid: best distance 0.58 (F 0.15, K 16, W 30, E 0.9, carry 50); the K = 0 control 0.60. Edge coupling 0.000-0.002 in
every setting, h2 about 3.0 (Voynich 2.28), adjacent repeats and long range far too high.

| Run | held-out (30) | near-copy share | ratio other/copy | edge |
|---|---|---|---|---|
| Voynich | | 0.256 | 0.76 | 0.055 |
| autocopist s19 / s7 | 11 / 14 | 0.288 / 0.338 | 0.99 / 0.52 | 0.002 / 0.001 |
| K 16, s19 / s7 | 8 / 9 | 0.414 / 0.415 | 0.55 / 0.21 | 0.002 / 0.002 |
| K 0 (control), s19 / s7 | 8 / 9 | 0.412 / 0.406 | 0.16 / -0.00 | 0.000 / -0.001 |
| K 4, s19 / s7 | 9 / 8 | 0.413 / 0.416 | 0.40 / 0.35 | 0.001 / 0.001 |

**Verdict by the letter of the rule: undecided** (ratio < 1 with share >= 0.20 in several runs, but held-out 8-9, far
under 23). **In substance: fails.** The rule had a loophole: it did not require the coupling to exist. Here both
couplings are near zero (edge 0.000-0.002), so the ratio is noise; the context rule produces no boundary habit (K = 16
is no different from the K = 0 control), and the copier does worse than the autocopist on the held-out items.

So a source-choosing copier does not generate a book-wide boundary rule. Of everything tested, only chaining (the
encoding of a word set by how the previous word ended, one rule for the book) produces Voynich's boundary coupling
and the right direction of the copy split; what no mechanism yet produces is that coupling together with Voynich's
abundance of near-copies (26%).

## Context-table test of chaining (`context_tables.py`, decision rule committed before the run): invalid

Idea: endings of the previous word that select the same encoding table should be interchangeable (same distribution of
openings after them) and fall into a few discrete groups. Pairwise permutation tests (Jensen-Shannon divergence of the
following word's opening, 200 permutations, 95th percentile), contexts with >= 300 occurrences.

| Text | contexts | indistinguishable pairs | clique groups |
|---|---|---|---|
| Voynich | 8 | 0 / 28 | 0 |
| chained cipher, six real tables (positive control) | 9 | 0 / 36 | 0 |
| Latin (letters) | 10 | 3 / 45 | 3 |
| autocopist s19 | 11 | 11 / 55 | 0 |

**The positive control fails, so the test is invalid and says nothing about Voynich.** The design assumed that two
endings selecting the same table have identical continuations. They do not: an ending also carries information about
the plaintext letter it encodes, and the next plaintext letter depends on it (Latin is not a random letter sequence),
so the continuation depends on the plaintext as well as on the table; with thousands of tokens per ending, small
plaintext differences are significant. Without the plaintext the two effects cannot be separated this way. A valid
version would need a model that separates them (a latent-table model fitted jointly with a plaintext language model)
or a property the plaintext cannot produce. Recorded as a failed design, not as a result.
