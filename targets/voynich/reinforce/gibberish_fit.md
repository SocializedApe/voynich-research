# The gibberish volunteers with their own lines and pages: line tests and fits (10 Nov 2026)

Script `volunteers.py` (docstring has the loader and the definitions). Every earlier use of the Gaskell-Bowern volunteers in this
repository poured their words into the Voynich skeleton; here their own lines, pages and writers are kept.

## Corpus

| | writers | pages | lines | tokens | types | words/line | units/word | letters/word |
|---|---|---|---|---|---|---|---|---|
| gibberish | 38 | 88 | 1617 | 10049 | 6840 | 6.21 | 4.91 | 4.95 |
| voynich ZL | 6 | 207 | 4130 | 34834 | 7021 | 8.43 | 4.46 | 4.99 |

## Coupling of adjacent words: inside a line, across a line break, across a paragraph break

X = normalised excess MI(last unit of the first word; first unit of the next) over shuffles (lines/boundaries.py); interior pairs
for within; lag2 = one word skipped. "page null" = the shuffle is done within each page, which removes writer and page
heterogeneity from the excess. Controls are poured into the volunteers' skeleton (same lines, pages, writers).

| text | within | within lag2 | line break | para break | first to second | within, page null | lag2, page null | line break, page null |
|---|---|---|---|---|---|---|---|---|
| gibberish | 0.0090 (5371) | 0.0062 (4000) | 0.0095 (1444) | -0.0109 (85) | 0.0100 (1502) | 0.0026 (5371) | 0.0021 (4000) | 0.0012 (1444) |
| gibberish_DA | 0.0559 (242) | -0.0014 (143) | -0.0104 (102) |  | 0.0299 (108) | 0.0441 (242) | 0.0054 (143) | -0.0013 (102) |
| gibberish_DC | 0.0094 (5129) | 0.0063 (3857) | 0.0121 (1342) | -0.0110 (85) | 0.0040 (1394) | 0.0037 (5129) | -0.0004 (3857) | 0.0047 (1342) |
| latin | 0.0186 (5371) | -0.0004 (4000) | 0.0228 (1444) | 0.0318 (85) | 0.0220 (1502) | 0.0188 (5371) | 0.0001 (4000) | 0.0232 (1444) |
| english | 0.0175 (5371) | 0.0082 (4000) | 0.0146 (1444) | 0.0244 (85) | 0.0178 (1502) | 0.0168 (5371) | 0.0072 (4000) | 0.0161 (1444) |
| autocopist_s19 | 0.0034 (4632) | 0.0021 (3328) | -0.0010 (1444) | -0.0006 (85) | 0.0025 (1484) | 0.0015 (4632) | 0.0000 (3328) | -0.0018 (1444) |
| voynich_poured | 0.0367 (5371) | -0.0001 (4000) | 0.0297 (1444) | 0.0153 (85) | 0.0460 (1502) | 0.0358 (5371) | -0.0003 (4000) | 0.0292 (1444) |
| voynich | 0.0597 (22557) | 0.0029 (18665) | -0.0001 (3390) | 0.0105 (533) |  | 0.0586 (22557) | 0.0018 (18665) | -0.0014 (3390) |

Per writer (within-line X, 20 shuffles, writers with >= 50 interior pairs: 35 of 38): median 0.0148, quartiles 0.0047 / 0.0369, min -0.0267, max 0.0575; writers above 0.02: 15, above 0.04: 5.
Across a line break per writer (where >= 50 breaks): DA_01 -0.003, DA_02 0.003, DC_01 0.004, DC_06 0.018, DC_11 0.005, DC_15 0.012, DC_16 0.025, DC_27 0.008, DC_31 0.021, DC_36 0.010.

Writers ranked by within-line X: DC_23 0.057 (120w), DA_02 0.053 (356w), DC_32 0.049 (281w), DC_33 0.046 (188w), DC_37 0.043 (317w), DC_18 0.040 (421w), DC_06 0.039 (368w), DC_16 0.038 (338w), DC_28 0.037 (215w), DC_42 0.036 (342w), DC_29 0.032 (184w), DC_41 0.025 (150w), DC_35 0.025 (267w), DC_25 0.023 (157w), DC_04 0.023 (270w), DC_08 0.019 (247w), DC_01 0.016 (364w), DC_40 0.015 (330w), DC_27 0.015 (332w), DC_20 0.013 (274w), DC_15 0.011 (480w), DC_38 0.011 (292w), DC_26 0.009 (228w), DC_21 0.008 (305w), DC_34 0.007 (276w), DC_09 0.006 (218w), DC_30 0.005 (322w), DA_01 0.000 (210w), DC_39 -0.002 (312w), DC_05 -0.009 (200w), DC_31 -0.010 (355w), DC_12 -0.011 (207w), DC_03 -0.021 (251w), DC_11 -0.026 (223w), DC_10 -0.027 (221w).

Writer by writer against 200 shuffles of his own pairs (no heterogeneity in the null), writers with >= 50 interior pairs: 35; z >= 3 in 5, z >= 2 in 10, median z 1.23. The same page by page for Voynich, pages with >= 50 interior pairs: 128; z >= 3 in 62, z >= 2 in 81, median z 2.95; median page size 146 words.
Writers with z >= 2: DC_18 X 0.038 z 4.2 (421w), DA_02 X 0.055 z 4.1 (356w), DC_37 X 0.044 z 4.1 (317w), DC_32 X 0.048 z 3.8 (281w), DC_33 X 0.058 z 3.0 (188w), DC_16 X 0.037 z 2.9 (338w), DC_06 X 0.040 z 2.8 (368w), DC_42 X 0.038 z 2.5 (342w), DC_35 X 0.025 z 2.2 (267w), DC_23 X 0.046 z 2.1 (120w).

## Position profile: are line-first and line-last words different?

JSD of the first-unit distribution at a position against the interior pool (lines of >= 6 words) and mean word length there; null =
words shuffled within each line (20 reps). Positions 1, 2 from the start and -2, -1 from the end.

| text | jsd 1 (null) | jsd 2 (null) | jsd -2 (null) | jsd -1 (null) | len 1 (null) | len -1 (null) | len pool |
|---|---|---|---|---|---|---|---|
| gibberish | 0.012 (0.006) | 0.009 (0.007) | 0.006 (0.006) | 0.007 (0.007) | 4.97 (4.70) | 5.01 (4.74) | 4.59 |
| gibberish_DA |  |  |  |  |  |  |  |
| gibberish_DC | 0.013 (0.008) | 0.009 (0.008) | 0.006 (0.007) | 0.008 (0.008) | 4.91 (4.68) | 4.97 (4.73) | 4.58 |
| latin | 0.005 (0.004) | 0.007 (0.005) | 0.002 (0.005) | 0.004 (0.004) | 5.82 (5.76) | 5.71 (5.74) | 5.74 |
| english | 0.005 (0.006) | 0.005 (0.005) | 0.005 (0.005) | 0.009 (0.006) | 4.53 (4.40) | 4.35 (4.41) | 4.40 |
| autocopist_s19 | 0.028 (0.005) | 0.006 (0.005) | 0.005 (0.005) | 0.006 (0.006) | 5.36 (4.95) | 4.57 (4.95) | 4.84 |
| voynich_poured | 0.005 (0.006) | 0.005 (0.006) | 0.009 (0.005) | 0.006 (0.005) | 4.61 (4.73) | 4.72 (4.71) | 4.74 |
| voynich (lines/boundaries) | 0.205 (0.002) | 0.020 (0.002) | 0.010 (0.002) | 0.049 (0.002) | 5.44 (5.01) | 4.65 (5.01) | 4.96 |

## Near-copy geometry: is a near-copy in the line above, at the same position?

lines/copy_geometry.py: token pairs at Levenshtein <= 1 between a line and the line above, interior positions; align1 = |position
difference| <= 1, as a ratio to null A (words shuffled within each line) and null B (column shuffle); nearest = where the nearest
earlier near-copy of a token on the page is (same line / one line above / two / three or more), observed and within-page shuffle.

| text | events | align1 / null A | align1 / null B | same index / null B | nearest same, above1, above2, above3+ | shuffled |
|---|---|---|---|---|---|---|
| gibberish | 615 | 1.097 (z 2.2) | 1.064 (z 2.2) | 1.128 (z 2.4) | 0.063, 0.082, 0.052, 0.162 | 0.069, 0.084, 0.047, 0.157 |
| gibberish_DA | 20 | 1.269 (z 1.0) | 1.129 (z 0.9) | 1.357 (z 1.4) | 0.053, 0.080, 0.067, 0.210 | 0.078, 0.092, 0.060, 0.182 |
| gibberish_DC | 595 | 1.087 (z 1.8) | 1.077 (z 1.8) | 1.172 (z 1.9) | 0.063, 0.082, 0.051, 0.159 | 0.065, 0.085, 0.047, 0.157 |
| latin | 107 | 0.936 (z -0.4) | 0.890 (z -0.6) | 0.626 (z -1.8) | 0.013, 0.026, 0.017, 0.084 | 0.013, 0.022, 0.019, 0.086 |
| english | 558 | 1.041 (z 0.9) | 1.012 (z 0.3) | 0.851 (z -2.0) | 0.059, 0.120, 0.077, 0.186 | 0.069, 0.112, 0.067, 0.191 |
| autocopist_s19 | 1178 | 1.090 (z 2.8) | 1.060 (z 1.8) | 1.176 (z 2.4) | 0.155, 0.226, 0.117, 0.248 | 0.139, 0.190, 0.110, 0.263 |
| voynich_poured | 743 | 0.977 (z -0.9) | 1.042 (z 1.1) | 1.024 (z 0.3) | 0.121, 0.152, 0.085, 0.212 | 0.100, 0.140, 0.089, 0.242 |
| voynich (lines/copy_geometry) | 6004 | 1.031 (z 1.8) | 0.988 (z -0.7) | 1.001 (z 0.0) | 0.141, 0.180, 0.092, 0.237 | 0.119, 0.172, 0.101, 0.257 |

## Whole-word re-use: hierarchical Pitman-Yor fit on book > batch > writer > page > line

hpy.py fit, 100 sweeps, posterior means over the second half; passed up = share of draws at a level that opened a new table
(were not a re-use at that level). Controls poured into the volunteers' skeleton: each "writer" is then a run of 80-480 words of the
control, each "page" a run of the size of that volunteer's page.

| text | tokens | types | log2 p/token | d book | d batch | d writer | d page | d line | theta book | theta batch | theta writer | theta page | theta line | passed up book | passed up batch | passed up writer | passed up page | passed up line |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gibberish | 10049 | 6840 | -11.020 | 1.00 | 1.00 | 0.91 | 0.96 | 1.00 | 15.8 | 0.3 | 2.5 | 5.5 | 1.4 | 0.996 | 0.991 | 0.797 | 0.933 | 0.997 |
| latin | 10049 | 4869 | -11.494 | 0.96 | 0.98 | 1.00 | 1.00 | 1.00 | 5.3 | 4.4 | 1.1 | 2.1 | 1.1 | 0.779 | 0.919 | 0.997 | 1.000 | 0.998 |
| english | 10049 | 2118 | -8.859 | 0.91 | 0.94 | 0.97 | 0.98 | 1.00 | 7.6 | 1.1 | 3.4 | 3.3 | 1.4 | 0.494 | 0.737 | 0.946 | 0.967 | 0.999 |
| autocopist_s19 | 9303 | 3720 | -9.948 | 0.98 | 0.97 | 1.00 | 0.70 | 1.00 | 2.7 | 9.4 | 2.7 | 30.1 | 1.8 | 0.847 | 0.849 | 0.989 | 0.763 | 1.000 |
| voynich_poured | 10049 | 2907 | -9.739 | 0.92 | 0.96 | 0.98 | 0.99 | 0.99 | 6.1 | 27.4 | 3.9 | 1.2 | 1.7 | 0.552 | 0.827 | 0.960 | 0.980 | 0.997 |

For reference, the Voynich fit on its own hierarchy (fit.md), passed up per level: book 0.526, hand 0.816, section 0.838, quire 0.872, page 0.949, line 0.996; the same for the poured gibberish of that run: book 0.934, hand 0.999, section 1.000, quire 0.964, page 0.819, line 0.996.

## The ending habit per writer, and the chain inside the word

scribe_ratio.py with 100-word docs (HALF 50): JSD between docs of different scribes / JSD between the two halves of a doc, and the
same for docs of the same scribe; on glyph bigrams (the repository's scribe ratio), on last units alone, on last two units, on first
units alone. Writers are the volunteers' scribes; Voynich hands 1-3 are Davis's.

| scribes | split | between scribes / within | same scribe other doc / within | docs |
|---|---|---|---|---|
| gibberish writers | bigrams | 2.31 [2.06-2.57] | 1.19 [1.06-1.36] | 83 |
| gibberish writers | ending | 3.40 [2.90-3.97] | 1.35 [1.05-1.74] | 83 |
| gibberish writers | opener | 2.68 [2.23-3.21] | 1.28 [1.07-1.54] | 83 |
| gibberish writers | last2 | 2.39 [2.11-2.70] | 1.23 [1.04-1.49] | 83 |
| voynich hands 1-3 | bigrams | 2.29 [1.82-2.59] | 1.69 [1.63-1.74] | 328 |
| voynich hands 1-3 | ending | 2.13 [1.87-2.54] | 1.75 [1.62-1.89] | 328 |
| voynich hands 1-3 | opener | 2.16 [1.77-2.57] | 1.65 [1.52-1.78] | 328 |
| voynich hands 1-3 | last2 | 2.20 [1.74-2.51] | 1.61 [1.54-1.68] | 328 |

Chain inside the word: normalised excess MI over a shuffle (20 reps), words of >= 2 units (>= 3 for ending given first).

| text | ending given preceding unit | second given first | ending given first | length given first |
|---|---|---|---|---|
| gibberish | 0.0940 (9523) | 0.1097 (9523) | 0.0198 (8352) | 0.0300 (10049) |
| voynich | 0.5575 (33697) | 0.4074 (33697) | 0.0414 (30783) | 0.1114 (34834) |

## Slot models with the neutral split on the volunteers

Split: first unit | the rest | last unit. Location model: slots4.py form (no context); chain model: slots5.py form (each slot in the
context of the unit before it, context directly under book). 60 sweeps, 10 at fixed hyperparameters. log2 p/token = held-in
predictive log-likelihood of the fitted restaurant (same data for both models of a slot, so the difference is the value of the context).

### location model, levels book > batch > writer > page > line

| slot | values | log2 p/token | d book | d batch | d writer | d page | d line | theta book | theta batch | theta writer | theta page | theta line | up book | up batch | up writer | up page | up line |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| opener | 28 | -4.119 | 0.34 | 0.37 | 0.63 | 0.85 | 1.00 | 27.1 | 20.2 | 7.0 | 7.6 | 1.6 | 0.34 | 0.13 | 0.40 | 0.81 | 1.00 |
| middle | 4351 | -9.062 | 1.00 | 1.00 | 0.91 | 0.96 | 1.00 | 1.5 | 1.4 | 3.1 | 2.8 | 1.7 | 1.00 | 1.00 | 0.81 | 0.93 | 1.00 |
| ending | 29 | -3.791 | 0.44 | 0.57 | 0.58 | 0.84 | 0.99 | 17.9 | 11.6 | 7.1 | 6.0 | 1.8 | 0.29 | 0.26 | 0.36 | 0.76 | 0.99 |

### chain model, levels book > context > batch > writer > page > line

| slot | values | log2 p/token | d book | d context | d batch | d writer | d page | d line | theta book | theta context | theta batch | theta writer | theta page | theta line | up book | up context | up batch | up writer | up page | up line |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| opener | 28 | -4.297 | 0.48 | 0.96 | 0.90 | 0.79 | 0.94 | 0.98 | 14.0 | 8.9 | 8.4 | 2.8 | 2.4 | 1.2 | 0.08 | 0.96 | 0.91 | 0.78 | 0.96 | 1.00 |
| middle | 4351 | -8.304 | 1.00 | 1.00 | 1.00 | 0.87 | 0.94 | 0.98 | 4.3 | 2.3 | 1.8 | 0.8 | 1.3 | 1.2 | 1.00 | 1.00 | 1.00 | 0.79 | 0.93 | 1.00 |
| ending | 29 | -2.979 | 0.48 | 0.90 | 0.86 | 0.62 | 0.87 | 0.93 | 9.6 | 4.7 | 1.8 | 0.9 | 1.7 | 1.2 | 0.13 | 0.79 | 0.77 | 0.51 | 0.90 | 0.99 |

Gain of the chain model over the location model, bits per token: opener -0.178, middle +0.758, ending +0.812.

## Slot models with the neutral split on the Voynich

Split: first unit | the rest | last unit. Location model: slots4.py form (no context); chain model: slots5.py form (each slot in the
context of the unit before it, context directly under book). 60 sweeps, 10 at fixed hyperparameters. log2 p/token = held-in
predictive log-likelihood of the fitted restaurant (same data for both models of a slot, so the difference is the value of the context).

### location model, levels book > lang > hand > section > quire > page > line

| slot | values | log2 p/token | d book | d lang | d hand | d section | d quire | d page | d line | theta book | theta lang | theta hand | theta section | theta quire | theta page | theta line | up book | up lang | up hand | up section | up quire | up page | up line |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| opener | 28 | -3.270 | 0.55 | 0.76 | 0.77 | 0.79 | 0.69 | 0.79 | 0.97 | 13.8 | 8.0 | 8.9 | 7.2 | 5.5 | 5.9 | 2.0 | 0.27 | 0.53 | 0.56 | 0.51 | 0.30 | 0.63 | 0.98 |
| middle | 3094 | -7.427 | 1.00 | 0.99 | 0.99 | 0.97 | 0.96 | 0.97 | 0.99 | 0.9 | 1.2 | 4.4 | 5.3 | 4.0 | 2.4 | 1.6 | 1.00 | 0.96 | 0.94 | 0.88 | 0.85 | 0.93 | 0.99 |
| ending | 27 | -2.475 | 0.40 | 0.81 | 0.85 | 0.78 | 0.72 | 0.76 | 0.96 | 26.1 | 4.3 | 3.4 | 5.7 | 3.1 | 2.9 | 2.2 | 0.25 | 0.52 | 0.60 | 0.50 | 0.31 | 0.54 | 0.98 |

### chain model, levels book > context > lang > hand > section > quire > page > line

| slot | values | log2 p/token | d book | d context | d lang | d hand | d section | d quire | d page | d line | theta book | theta context | theta lang | theta hand | theta section | theta quire | theta page | theta line | up book | up context | up lang | up hand | up section | up quire | up page | up line |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| opener | 28 | -2.997 | 0.42 | 0.79 | 0.85 | 0.85 | 0.83 | 0.82 | 0.89 | 0.95 | 23.9 | 6.2 | 3.3 | 7.0 | 5.7 | 5.2 | 2.8 | 1.5 | 0.16 | 0.53 | 0.68 | 0.72 | 0.65 | 0.63 | 0.84 | 0.99 |
| middle | 3094 | -6.312 | 1.00 | 0.87 | 0.93 | 0.97 | 0.96 | 0.96 | 0.97 | 0.97 | 10.6 | 4.4 | 3.6 | 2.0 | 1.9 | 2.6 | 1.9 | 1.4 | 0.99 | 0.56 | 0.71 | 0.93 | 0.87 | 0.88 | 0.96 | 0.99 |
| ending | 27 | -1.083 | 0.40 | 0.62 | 0.77 | 0.86 | 0.85 | 0.75 | 0.77 | 0.89 | 11.2 | 1.2 | 1.7 | 2.1 | 1.7 | 1.7 | 1.9 | 1.5 | 0.19 | 0.24 | 0.53 | 0.70 | 0.66 | 0.47 | 0.72 | 0.98 |

Gain of the chain model over the location model, bits per token: opener +0.274, middle +1.116, ending +1.392.

