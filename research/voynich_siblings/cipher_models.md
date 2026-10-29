# Building a cipher of Latin that reproduces the Voynich profile: rounds 1-5 and a first test on the real text

28 Oct 2026. Script: `cipher_models.py` (variants of Greshko's Naibbe cipher, his own tables), `sandhi_test.py`.
Every text is generated from Latin (`lang/corpora/la-gutenberg.txt`) and poured into the ZL line skeleton (fixed
parse); profile items as in `code_vs_generator.md`. Distance = mean absolute relative deviation from Voynich over
seven items (h2, start/end, edge coupling, hapax share, share of types on one page, long-range D(256), adjacent
identical tokens).

## Why

For decryption to be possible, Voynichese has to be a cipher; for an attack to be designed, its *kind* of cipher has
to be pinned down. No published mechanism reproduces the whole profile (code_vs_generator.md; Rozanova & Temerev
2026). This is a search for a hand-executable, period-plausible cipher of Latin that does, built from parts that
15th-century ciphers used: homophone tables, a key that changes by section, boundary spelling, nulls, careless
spacing.

## Rounds

| Round | Change | Best distance | What it fixed / what broke |
|---|---|---|---|
| 0 | Naibbe as published | 0.57 | low entropy and start/end right; edge coupling 0.002, hapax 0.39, page locality 0.39, long range 0.004 all wrong |
| 1 | chained tables (table of the next token set by the last glyph of the current one); drift (2-3 of 6 tables per page) | 0.42 | chaining makes edge coupling (0.10) but also ties start to end inside the word; drift makes long-range clustering (0.39-0.42) |
| 2 | chain only the opening half of the next token; scribal variation (e/ee, k/t, ch/sh, qo-) | 0.42 | chaining alone gives edge 0.034 with start/end intact (0.048); with drift the chained table is rarely active and the coupling vanishes; variation raises hapax a little and h2 too much |
| 3 | chain index into the page's active tables; missed spaces | 0.44 | bug: missed spaces never fired; chaining through 2-3 tables carries too little to couple |
| 4 | boundary spelling (sandhi: a prefix written before a word, fixed by the last glyph of the previous word); missed spaces fixed | 0.23 | sandhi 0.4 gives edge 0.076 with start/end 0.038; missed spaces 0.15 give hapax 0.73 and one-page 0.74 |
| 5 | null words (a small set inserted at random) | **0.19** | nulls raise adjacent repeats (0.40%, Voynich 0.94%) but also start/end dependence; trade-off |

Best round-5 variant (drift 2 tables per page, missed spaces 0.10, sandhi 0.25, nulls 0.10 from 8 words):

| | Voynich | model | Naibbe |
|---|---|---|---|
| h2 | 2.280 | 2.369 | 2.318 |
| start/end (k = 1) | 0.039 | 0.055 | 0.052 |
| edge coupling | 0.055 | 0.053 | 0.002 |
| hapax share | 0.680 | 0.683 | 0.390 |
| types on one page | 0.683 | 0.695 | 0.391 |
| long range D(256) | 0.287 | 0.210 | 0.004 |
| adjacent identical % | 0.935 | 0.401 | 0.166 |

## A test of the model on the real text (`sandhi_test.py`)

If boundary spelling is the mechanism, the coupling lives in a detachable opening element (qo, q, o, y, d, s) and the
glyph after it is independent of the previous word.

| | opener dependence | dependence of the glyph after the opener | share of words with an opener |
|---|---|---|---|
| Voynich, certain spaces | 0.039 | **0.026** | 0.47 |
| sandhi model | 0.070 | 0.011 | 0.65 |
| Naibbe | 0.001 | 0.001 | 0.54 |
| Latin (letters) | 0.013 | 0.013 | 0.18 |

In Voynich the coupling is not confined to the detachable opener: the next glyph is coupled too, twice as much as in
Latin. Pure boundary spelling is therefore refuted as the whole story. The pattern fits better a choice of the next
word's whole opening (a table, a code group) that depends on how the previous word ended: the chained-table rule of
round 2, which needs a drift design that keeps it effective.

## Rounds 6-8: keeping the chain effective

| Round | Change | Best distance | Result |
|---|---|---|---|
| 6 | split: the opening table is chained over all six tables, only the suffix table follows the page subset | 0.28 | chain 0.7 alone gives edge 0.054-0.060 with start/end 0.052, but long range collapses (D256 0.02-0.04) |
| 7 | a new chaining rule for every page | 0.31 | **the edge coupling vanishes (0.002)**: pooled over the book, 200 different page rules average out. Voynich's strong pooled coupling therefore implies one boundary rule for the whole manuscript (consistent with Rozanova & Temerev's quire-stable edge coupling), while its vocabulary is page-specific |
| 8 | global chain on openings + page-specific suffix tables + page-specific null words (a few per page) | **0.13** | every item near Voynich at once |

Round-8 model (`model_check.py`): chain 0.7 global, suffix tables 2 per page, missed spaces 0.10, sandhi 0.10, nulls
0.15 from 3 page-specific null words; four seeds.

| | h2 | start/end | edge | hapax | one page | D256 | adj % | distance | opener dep. | core dep. |
|---|---|---|---|---|---|---|---|---|---|---|
| Voynich | 2.280 | 0.039 | 0.054 | 0.680 | 0.683 | 0.289 | 0.935 | | 0.039 | 0.026 |
| model, 4 seeds | 2.32-2.42 | 0.041-0.063 | 0.039-0.051 | 0.63-0.65 | 0.64-0.66 | 0.38-0.41 | 0.81-0.96 | 0.13-0.20 | 0.034-0.052 | 0.021-0.045 |

Unlike the pure sandhi model (core 0.011), the chained-opening model spreads the coupling into the glyph after the
opener as Voynich does: the hypothesis "the next word's opening was chosen by a rule from how the previous word
ended, one rule for the whole book" survives the first test on the real text. Caution: five parameters were tuned on
seven statistics; the held-out test is the b3 battery (next).

## Held-out test on the b3 battery (`model_holdout.py`)

The b3 battery (targets/voynich/results/b3.md) has 37 items and a match rule fixed in advance. Four overlap with the
tuning statistics; 33 are held out.

| Corpus | matches, all 37 | matches, 33 held out |
|---|---|---|
| autocopist s19 / s7 | 12 / 15 | 11 / 14 |
| Naibbe (Latin, unmodified) | 20 | 19 |
| round-8 model s19 / s7 | 23 / 23 | 19 / 20 |

**On the held-out items the model is no better than plain Naibbe.** Its gains are on what it was tuned to. Held-out
items it misses, with Voynich / model (s19) / autocopist s19:

| Item | Voynich | model | autocopist |
|---|---|---|---|
| near-copy within 10 tokens (e_w10) | 0.276 | 0.155 | 0.333 |
| near-copy excess over within-page shuffle (e_ratio) | 1.14 | 0.96 | 1.22 |
| adjacent tokens at edit distance <= 1 (d_adj_ld1) | 0.042 | 0.015 | 0.079 |
| adjacent-page vocabulary excess (j_jacc_excess) | 0.037 | 0.005 | 0.004 |
| drift between manuscript halves (k_jsd_halves) | 0.062 | 0.005 | 0.024 |
| line-initial gallows (g_gal_init) | 0.223 | 0.042 | 0.307 |
| word length sd / share >= 9 (b_len_sd, b_len9) | 1.79 / 0.024 | 2.46 / 0.096 | 2.11 / 0.091 |

The misses are the copying signatures (near-copies close by, page-to-page continuity, slow drift) plus the
line-initial gallows and the length spread (the missed-space rule makes words too long). No cipher variant here
produces them; the self-citation generator produces the near-copies but fails the cipher-like items (h2, edge
coupling, f_lock, prediction). So Voynichese combines a cipher-like layer (low entropy, a book-wide boundary rule,
page-specific vocabulary) with a copy-and-modify layer. Either a scribe who copied and varied nearby words while
enciphering, or a generator with richer rules than the autocopist's. A hybrid (cipher output edited by local
copying) is the obvious next model; it should be scored on the held-out items only.

## Status*

Not a decipherment and not a claim about what the Voynich cipher is. It shows that period-plausible parts can bring a
cipher of Latin to within about 0.19 of Voynich on seven profile items, three times closer than Naibbe, and it turns
the edge coupling into a testable statement about the real text, of which the first form (sandhi) failed and the
second (chained choice of the opening) is next. Single seed per variant so far; the final model needs several seeds,
the b3 battery, and both Currier languages separately.
