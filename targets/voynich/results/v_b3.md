# v_b3: adversarial verification of b3 (generator bake-off)

Runtime 110.7 s.  ZL3b-n locus P: 34116 tokens, 207 pages, 4130 lines (own csv loader; identical token list to a4.load_zl: True).  Own LD<=1 test vs DP Levenshtein: 40010 pairs, 0 disagreements.  Nothing below imports b3 or a4 for a checked quantity; a4.lang_words (Latin file loading), a4.Autocopist and b3.Naibbe (generators under test) are reused, and b3.battery is used only in section 5 (port vs shipped, 37 items) as the instrument for port-vs-shipped.

## 0. Re-run of b3_bakeoff.py as-is (11 Oct 2026, corpora and Naibbe repo downloaded today)

Changed values against the committed b3.json: 72, all in full:italian, short:italian.  Tolerances changed: none.  Naibbe port check identical: True.  Every other corpus (ZL, A, B, Latin, English, both autocopists, both Rugg tables, the three Naibbe ciphertexts, gibberish) reproduces to the last digit.

| corpus | full committed | full re-run | short committed | short re-run |
|---|---|---|---|---|
| voynich_ZL | 37 | 37 | 37 | 37 |
| voynich_A | 27 | 27 | 37 | 37 |
| voynich_B | 34 | 34 | 19 | 19 |
| latin | 9 | 9 | 10 | 10 |
| italian | 14 | 9 | 12 | 8 |
| english | 9 | 9 | 9 | 9 |
| autocopist_s19 | 9 | 9 | 10 | 10 |
| autocopist_s7 | 9 | 9 | 14 | 14 |
| rugg_grille | 8 | 8 | 10 | 10 |
| rugg_sorted | 14 | 14 | 13 | 13 |
| naibbe_pliny | 17 | 17 | 17 | 17 |
| naibbe_pliny_lines | 17 | 17 | 17 | 17 |
| naibbe_divcom | 17 | 17 | 16 | 16 |
| gaskell_gibberish | 9 | 9 | 9 | 9 |

Why Italian moved: a4.lang_words("it") reads targets/vatican5/corpus_it.txt, a git-ignored file that vatican5/build_it_lm.py regenerates from Nuntiaturberichte OCR.  The September run read a build that opened "cumque predictus fcrdiuandu s rex nuper in romanorum regem electus" (a Latin passage; v_a4.md) with top words et(1443), di(1287), che(1280), a(633), non(549), la(545); the copy in this checkout (built 14 Sept on this machine) opens with OCR debris and German editorial text ("hitii hlf siifii r um fr roi iilii i li tiii l ...") and has top words di(1167), et(1003), che(877), a(713), per(580), la(559).  Neither build is a clean Italian text; the Italian row is not reproducible from the repository and should be read as "OCR nunciature Italian, build-dependent".

## 1. Claims in b3.md against the numbers

b3 value = committed b3.json / b3.md; re-run = b3_bakeoff.py run today; independent = this script (own code, 20-item subset, same corpora).

| claim in b3.md | b3 value | re-run value | independent value | verdict |
|---|---|---|---|---|
| B pages fail 18/37 (short) | 18 | 18 | - | confirmed |
| three Naibbe score best, 17/37 full and short | 17/17/17 full; 17/17/16 short | 17/17/17; 17/17/16 | subset (20 items) naibbe_pliny 7 full / 7 short | corrected: divcom short is 16; "17 full, 16-17 short" |
| Rugg-sorted and Italian next (13-14) | rugg_sorted 14/13, italian 14/12 | rugg_sorted 14/13, italian 9/8 | - | corrected: Italian short was 12 in Sept, and is 9 full / 8 short with today's corpus_it.txt (not reproducible); autocopist_s7 short is 14 |
| others trail at 8-14 | latin 9/10, english 9/9, ac19 9/10, ac7 9/14, grille 8/10, gibberish 9/9 | same | - | confirmed (the 14 is ac7 short, which ties the "next" group) |
| every non-Voynich corpus fails adj exact, adj LD<=1, sc <=10, MZ peak R and (full) JSD halves | full all-fail list: len sd, len=1, adj exact, adj LD<=1, sc <=10, sc prev2, MZ peak R, tok pred, JSD halves | full all-fail list: len sd, len=1, hapax/tokens, adj exact, adj LD<=1, sc <=10, sc prev2, MZ peak R, tok pred, types 1 page, JSD halves | own rule, 5 corpora: all fail adj exact, adj LD<=1, sc <=10, MZ peak R, JSD halves | confirmed as arithmetic; but MZ peak R is also failed by voynich_A/B and JSD halves by voynich_A/B: both items reward the A+B mixture, which no single-regime generator was given |
| JSD halves 0.063; languages 0.003-0.007, autocopist 0.02, Rugg 0.003-0.01, Naibbe 0.002 | 0.063; la 0.0025 it 0.0053 en 0.0073 | 0.063; it 0.0050 | ZL 0.0626, la 0.0025, naibbe 0.0018, ac19 0.0213 | confirmed |
| languages: h2/h3 about 1 bit too high | h2 +1.20..+1.25 (la, en), it +1.09 | h2 +1.20..+1.30; h3 +0.72..+1.18 | latin h2 +1.25, h3 +0.98 | confirmed for h2 (+1.1 to +1.3); h3 is +0.7 to +1.0 (Sept); wording "0.7-1.3 bits" |
| languages: positional lock 0.26-0.35 vs 0.64 | 0.261-0.352 | 0.261-0.329 | latin 0.325, ZL 0.644 | confirmed |
| autocopist reproduces the Zipf neighbourhood | -0.825 / -0.859 vs -1.040, tol 0.104 | fails (both seeds, full and short) | ac19 -0.825 vs -1.040, mark False | corrected: the autocopist fails Zipf in both seeds at both lengths |
| autocopist reproduces sc ratio and MZ peak position | ratio 1.196/1.155; peak 2^9 | same | ratio 1.196 (20 shuffles 1.193 +- 0.009); peak 2^9 | confirmed |
| autocopist: a 1-bit excess in glyph entropy | h2 raw +0.43..+0.46, h2 mrg +0.44..+0.62 | same | ac19 h2 raw +0.43, mrg +0.62 | corrected: the excess is 0.4-0.6 bits, not 1 bit |
| autocopist: TTR 0.34-0.38 vs 0.21, Heaps 0.85-0.88 vs 0.74, gallows mid 0.26-0.37 vs 0.065, token pred near zero | TTR 0.342-0.381; tok pred 0.0080/0.0103 | same | TTR 0.381; tok pred 0.0080 vs 0.0249 | confirmed |
| Rugg grille hapax/types 0.06, MZ R 2.0; sorted 9 % exact repeats | 0.057, 2.05; 0.089 | same | not recomputed | confirmed (re-run) |
| Naibbe matches character entropies, word length, positional lock, char predictability and Zipf slope | Zipf -0.921 / -0.888 vs -1.040 (tol 0.104) | Zipf fails (all three, full and short) | Zipf -0.921, mark False; h2 raw mark True, lock mark True, char3g mark True | corrected: Zipf is a Naibbe fail; the rest confirmed |
| Naibbe: R(s) about 0.003 bits at every scale, vs 0.29 real, 0.08-0.16 languages | peak 0.0031 / 0.0037; languages 0.082-0.160 | max |R| 0.0085; italian now 0.057 | peak 0.0031; 20 shuffles 0.0025; real 0.287 | confirmed in substance: |R| <= 0.009 at every scale; language range 0.06-0.16 with today's Italian |
| Naibbe: too few hapaxes, sc ratio 0.96-0.98 vs 1.13, no line-initial gallows preference | hapax/types 0.411; ratio 0.977/0.962/0.961 | same | ratio 0.977 (20 shuffles 0.984 +- 0.009) | confirmed |
| gibberish: h2 3.9 bits, positional lock 0.14 | 3.947, 0.144 | same | pooled 3.946, 0.144; per writer median h2 3.07 vs Voynich chunks 1.92, lock 0.32 vs 0.68 | confirmed; the pooled h2 mixes 38 writers, but the per-writer comparison at equal size gives the same verdict |
| long-range and drift items demand what neither (Naibbe, autocopist) supplies | autocopist MZ R 0.472/0.469 vs 0.287 | same | ac19 R 0.472 | corrected: the autocopist overshoots the long-range peak (0.47 vs 0.29) rather than lacking it; only the A-to-B drift (JSD halves) is missing from both |
| first 10,053 ZL tokens are almost entirely Currier-A herbal pages, so voynich_A short is nearly the same text | - | - | {'A': 7378, 'B': 2675} tokens by page language (73% A); last page f58v | corrected: herbal pages f1r-f58v, but only about three quarters Currier A (the Currier-B herbal leaves fall inside); voynich_A short and voynich_ZL short still agree on 37/37 items |
| naibbe_pliny_lines: 1,063 shipped lines; 207 pages | 1,063 lines; table 200 pages, 1044 lines | same | 1063 non-empty lines, 32.7 tokens/line | corrected: the construction yields 200 pages (1,044 lines used), not 207 |
| gibberish 38 files, 10,075 clean tokens | 38, 10075 | 10075 | 38, 10075 | confirmed |
| port re-encrypts Pliny close to the shipped file (34,625 vs 34,764 tokens) | 34625 vs 34764 | same | own transcription identical to port: True; 10 seeds 34625-34828 | confirmed (see 6) |
| pre-registered: battery and rule fixed before any score was computed | asserted in docstring and section 6 | - | script and results first appear in one commit (f1a99b941, 16 Sept) | not reproducible from the record: no timestamp separates the battery from the results; NOTES.md section 7 (15 Sept) named the idea and a different item list |

## 2. Independent recomputation of the subset (full length)

Max relative difference to b3 per corpus over the 20 items (b3 re-run values): voynich_ZL 0.001 (h2 mrg); latin 0.00045 (char 3g bits); naibbe_pliny 0.00078 (h2 mrg); autocopist_s19 0.00076 (h2 mrg); autocopist_s7 0.00061 (h2 mrg); gaskell_gibberish 0.00046 (h2 mrg).  Short battery: voynich_ZL 0.0019; latin 0.00082; naibbe_pliny 0.0015; autocopist_s19 0.0014; autocopist_s7 0.0011; gaskell_gibberish 0.00085.

Mark disagreements with b3 under the same rule (subset): short:autocopist_s7: h2 mrg.

| corpus | h2 raw | h3 raw | h2 mrg | h3 mrg | Zipf | TTR | hapax/types | hapax/tokens | adj exact | adj LD<=1 | sc cover | sc <=10 | sc <=10 shuf | sc ratio | pos lock | MZ peak log2 s | MZ peak R | tok pred | char 3g bits | JSD halves | matched (subset) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| voynich_ZL | 2.117 ✓ | 1.856 ✓ | 2.351 ✓ | 2.133 ✓ | -1.040 ✓ | 0.212 ✓ | 0.697 ✓ | 0.148 ✓ | 0.00815 ✓ | 0.041 ✓ | 0.643 ✓ | 0.269 ✓ | 0.238 ✓ | 1.130 ✓ | 0.644 ✓ | 10.000 ✓ | 0.287 ✓ | 0.025 ✓ | 1.887 ✓ | 0.063 ✓ | 20/20 |
| latin | 3.364 ✗ | 2.834 ✗ | 3.385 ✗ | 2.840 ✗ | -0.698 ✗ | 0.334 ✗ | 0.599 ✗ | 0.200 ✗ | 0.000322 ✗ | 0.000879 ✗ | 0.196 ✗ | 0.035 ✗ | 0.034 ✗ | 1.030 ✓ | 0.325 ✗ | 11.000 ✓ | 0.082 ✗ | 0.034 ✗ | 2.876 ✗ | 0.00254 ✗ | 2/20 |
| naibbe_pliny | 2.081 ✓ | 1.794 ✓ | 2.294 ✓ | 2.043 ✓ | -0.921 ✗ | 0.163 ✗ | 0.411 ✗ | 0.067 ✗ | 0.00158 ✗ | 0.013 ✗ | 0.529 ✗ | 0.152 ✗ | 0.156 ✗ | 0.977 ✗ | 0.628 ✓ | 9.000 ✓ | 0.00313 ✗ | 0.021 ✗ | 1.809 ✓ | 0.00178 ✗ | 7/20 |
| autocopist_s19 | 2.551 ✗ | 2.252 ✗ | 2.974 ✗ | 2.651 ✗ | -0.825 ✗ | 0.381 ✗ | 0.722 ✓ | 0.275 ✗ | 0.00127 ✗ | 0.076 ✗ | 0.749 ✗ | 0.329 ✗ | 0.275 ✗ | 1.196 ✓ | 0.457 ✗ | 9.000 ✓ | 0.472 ✗ | 0.00804 ✗ | 2.375 ✗ | 0.021 ✗ | 3/20 |
| autocopist_s7 | 2.579 ✗ | 2.331 ✗ | 2.791 ✗ | 2.521 ✗ | -0.859 ✗ | 0.342 ✗ | 0.711 ✓ | 0.243 ✗ | 0.00181 ✗ | 0.077 ✗ | 0.766 ✗ | 0.336 ✗ | 0.291 ✗ | 1.155 ✓ | 0.493 ✗ | 9.000 ✓ | 0.469 ✗ | 0.010 ✗ | 2.414 ✗ | 0.022 ✗ | 3/20 |
| gaskell_gibberish | 3.946 ✗ | 3.549 ✗ | 4.012 ✗ | 3.558 ✗ | -0.656 ✗ | 0.200 ✓ | 0 ✗ | 0 ✗ | 0.00533 ✗ | 0.020 ✗ | 0.371 ✗ | 0.146 ✗ | 0.120 ✗ | 1.218 ✓ | 0.144 ✗ | 9.000 ✓ | 0.576 ✗ | 0.542 ✗ | 3.732 ✗ | 0.003 ✗ | 3/20 |

Short (first 10,053 tokens):

| corpus | h2 raw | h3 raw | h2 mrg | h3 mrg | Zipf | TTR | hapax/types | hapax/tokens | adj exact | adj LD<=1 | sc cover | sc <=10 | sc <=10 shuf | sc ratio | pos lock | MZ peak log2 s | MZ peak R | tok pred | char 3g bits | JSD halves | matched (subset) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| voynich_ZL | 2.194 ✓ | 1.920 ✓ | 2.481 ✓ | 2.249 ✓ | -0.992 ✓ | 0.325 ✓ | 0.725 ✓ | 0.236 ✓ | 0.00826 ✓ | 0.046 ✓ | 0.498 ✓ | 0.259 ✓ | 0.229 ✓ | 1.131 ✓ | 0.609 ✓ | 8.000 ✓ | 0.150 ✓ | 0.026 ✓ | 2.003 ✓ | 0.040 ✓ | 20/20 |
| latin | 3.360 ✗ | 2.784 ✗ | 3.380 ✗ | 2.787 ✗ | -0.678 ✗ | 0.485 ✗ | 0.694 ✓ | 0.337 ✗ | 0.000199 ✗ | 0.00109 ✗ | 0.117 ✗ | 0.035 ✗ | 0.034 ✗ | 1.029 ✓ | 0.328 ✗ | 10.000 ✗ | 0.053 ✗ | 0.031 ✗ | 2.910 ✗ | 0.00798 ✗ | 2/20 |
| naibbe_pliny | 2.088 ✓ | 1.794 ✓ | 2.300 ✓ | 2.034 ✓ | -0.877 ✗ | 0.297 ✓ | 0.574 ✗ | 0.171 ✗ | 0.00119 ✗ | 0.013 ✗ | 0.387 ✗ | 0.141 ✗ | 0.144 ✗ | 0.979 ✗ | 0.622 ✓ | 9.000 ✗ | 0.0014 ✗ | 0.017 ✗ | 1.838 ✓ | 0.00374 ✗ | 7/20 |
| autocopist_s19 | 2.506 ✗ | 2.191 ✗ | 2.906 ✗ | 2.539 ✗ | -0.756 ✗ | 0.468 ✗ | 0.718 ✓ | 0.336 ✗ | 0.00119 ✗ | 0.076 ✗ | 0.680 ✗ | 0.376 ✗ | 0.322 ✗ | 1.166 ✓ | 0.445 ✗ | 8.000 ✓ | 0.356 ✗ | 0.00817 ✗ | 2.375 ✗ | 0.036 ✓ | 4/20 |
| autocopist_s7 | 2.551 ✗ | 2.262 ✗ | 2.731 ✗ | 2.404 ✓ | -0.797 ✗ | 0.438 ✗ | 0.715 ✓ | 0.313 ✗ | 0.00249 ✗ | 0.082 ✗ | 0.690 ✗ | 0.382 ✗ | 0.326 ✗ | 1.171 ✓ | 0.502 ✗ | 8.000 ✓ | 0.339 ✗ | 0.00973 ✗ | 2.441 ✗ | 0.022 ✗ | 4/20 |
| gaskell_gibberish | 3.961 ✗ | 3.560 ✗ | 4.027 ✗ | 3.569 ✗ | -0.630 ✗ | 0.679 ✗ | 0.852 ✗ | 0.579 ✗ | 0.00537 ✗ | 0.021 ✗ | 0.297 ✗ | 0.143 ✗ | 0.134 ✗ | 1.069 ✓ | 0.142 ✗ | 9.000 ✗ | 0.591 ✗ | 0.026 ✓ | 4.036 ✗ | 0.066 ✗ | 2/20 |

Shuffle noise (b3 uses one within-page shuffle for e and three token shuffles for h):

| corpus | sc ratio, seed 1 | sc ratio, 20 shuffles mean +- sd [min, max] | MZ peak R, 3 shuffles | MZ peak R, 20 shuffles | peak log2 s, 3 / 20 |
|---|---|---|---|---|---|
| voynich_ZL | 1.130 | 1.124 +- 0.005 [1.114, 1.132] | 0.2873 | 0.2903 | 10 / 9 |
| latin | 1.030 | 1.012 +- 0.020 [0.986, 1.053] | 0.0820 | 0.0824 | 11 / 11 |
| naibbe_pliny | 0.977 | 0.984 +- 0.009 [0.964, 1.006] | 0.0031 | 0.0025 | 9 / 9 |
| autocopist_s19 | 1.196 | 1.193 +- 0.009 [1.177, 1.214] | 0.4723 | 0.4733 | 9 / 9 |
| gaskell_gibberish | 1.218 | 1.209 +- 0.011 [1.190, 1.229] | 0.5761 | 0.5751 | 9 / 9 |

## 3. Is the tolerance rule fair?

Block jackknife over 20 contiguous page groups gives the sampling SE of each item on the real text.  tol/SE < 2 means the rule is stricter than the real text's own sampling noise (a candidate identical in law to Voynichese would fail often); tol/SE > 10 means the item is nearly free.  A-B = difference between the Currier A and B pages (b3 re-run), the text's own heterogeneity.

| item | real | tol | tol/real | SE (jackknife) | tol/SE | A - B |
|---|---|---|---|---|---|---|
| h2 raw | 2.117 | 0.212 | 0.100 | 0.036 | 5.833 | 0.172 |
| h3 raw | 1.856 | 0.186 | 0.100 | 0.034 | 5.392 | 0.164 |
| h2 mrg | 2.351 | 0.235 | 0.100 | 0.049 | 4.762 | 0.267 |
| h3 mrg | 2.133 | 0.213 | 0.100 | 0.048 | 4.421 | 0.263 |
| Zipf | -1.040 | 0.104 | 0.100 | 0.031 | 3.349 | 0.074 |
| TTR | 0.212 | 0.039 | 0.182 | 0.019 | 2.032 | 0.100 |
| hapax/types | 0.697 | 0.070 | 0.100 | 0.00791 | 8.813 | 0.036 |
| hapax/tokens | 0.148 | 0.032 | 0.214 | 0.015 | 2.169 | 0.080 |
| adj exact | 0.00815 | 0.000815 | 0.100 | 0.000922 | 0.884 | 0.000171 |
| adj LD<=1 | 0.041 | 0.00413 | 0.100 | 0.00216 | 1.910 | 0.00449 |
| sc cover | 0.643 | 0.064 | 0.100 | 0.033 | 1.943 | -0.198 |
| sc <=10 | 0.269 | 0.027 | 0.100 | 0.016 | 1.691 | -0.024 |
| sc <=10 shuf | 0.238 | 0.024 | 0.100 | 0.015 | 1.566 | -0.014 |
| sc ratio | 1.130 | 0.113 | 0.100 | 0.019 | 5.893 | -0.037 |
| pos lock | 0.644 | 0.064 | 0.100 | 0.016 | 3.925 | -0.030 |
| MZ peak log2 s | 10.000 | 1.000 | 0.100 | 2.494 | 0.401 | 0 |
| MZ peak R | 0.287 | 0.029 | 0.100 | 0.031 | 0.922 | -0.040 |
| tok pred | 0.025 | 0.00249 | 0.100 | 0.00208 | 1.198 | 0.00326 |
| char 3g bits | 1.887 | 0.189 | 0.100 | 0.039 | 4.799 | 0.206 |
| JSD halves | 0.063 | 0.00626 | 0.100 | 0.017 | 0.372 | 0.017 |

Items of the 37 whose tolerance is at least the real value itself (any value between 0 and twice the real value matches), full: g_gal_mid, k_jsd_oddeven; short: g_gal_mid.
Items whose full-length tolerance is set by the autocopist seed spread rather than 10 %: b_len1, b_len9, c_ttr, c_hapax_tokens, f_irrev, g_gal_init, g_gal_mid, k_jsd_oddeven.

Noise-aware re-score (match iff |v - real| <= max(tol, 2 sqrt(SE_real^2 + SE_corpus^2)), subset of 20, full length): latin 2 -> 2 (gains none); naibbe_pliny 7 -> 9 (gains TTR, tok pred); autocopist_s19 3 -> 4 (gains sc <=10 shuf).

Family-weighted count of b3's own 37 marks (re-run json; 10 families, each scored as the share of its items matched, so the six correlated entropy items count once):

| corpus | items full | family score full (of 10) | items short | family score short |
|---|---|---|---|---|
| voynich_ZL | 37 | 10.0 | 37 | 10.0 |
| voynich_A | 27 | 6.85 | 37 | 10.0 |
| voynich_B | 34 | 8.97 | 19 | 5.37 |
| latin | 9 | 2.43 | 10 | 2.35 |
| italian | 9 | 2.18 | 8 | 1.68 |
| english | 9 | 2.23 | 9 | 2.23 |
| autocopist_s19 | 9 | 2.35 | 10 | 2.65 |
| autocopist_s7 | 9 | 2.05 | 14 | 3.3 |
| rugg_grille | 8 | 2.05 | 10 | 2.38 |
| rugg_sorted | 14 | 3.63 | 13 | 3.25 |
| naibbe_pliny | 17 | 4.3 | 17 | 3.97 |
| naibbe_pliny_lines | 17 | 4.3 | 17 | 3.97 |
| naibbe_divcom | 17 | 4.3 | 16 | 3.8 |
| gaskell_gibberish | 9 | 2.08 | 9 | 2.25 |

## 4. Gibberish at equal size

38 files, 10075 tokens (per file min/max/median [79, 480, 268.5]); 164 non-ASCII letters before accent stripping; 9 hyphenated line breaks split into two tokens.  Each writer's file is compared, as one page, with 40 random runs of the same number of consecutive Voynich tokens (all metrics on the run as one page).

| metric | gibberish median [IQR] | Voynich chunks median [IQR] | gibberish files inside Voynich 5-95 % |
|---|---|---|---|
| h2_raw | 3.070 [2.866, 3.273] | 1.918 [1.773, 2.014] | 0/38 |
| ttr | 0.749 [0.597, 0.844] | 0.701 [0.634, 0.755] | 18/38 |
| hapax_types | 0.857 [0.809, 0.910] | 0.799 [0.762, 0.834] | 18/38 |
| adj_exact | 0.00295 [0, 0.00683] | 0.00687 [0.00357, 0.011] | 31/38 |
| adj_ld1 | 0.013 [0.00518, 0.025] | 0.040 [0.030, 0.051] | 14/38 |
| sc_w10 | 0.133 [0.087, 0.204] | 0.264 [0.220, 0.309] | 12/38 |
| sc_ratio | 0.996 [0.855, 1.108] | 1.160 [1.086, 1.250] | 20/38 |
| pos_lock | 0.320 [0.254, 0.398] | 0.684 [0.640, 0.730] | 1/38 |

Whole-manuscript short reference (every third page from f1r, 68 pages, Currier {'A': 41, 'B': 24, '?': 3}) instead of the herbal-A opening; subset matches out of 20: latin 2 -> 1; naibbe_pliny 7 -> 8; autocopist_s19 4 -> 3; autocopist_s7 4 -> 2; gaskell_gibberish 2 -> 3.

## 5. Naibbe port fidelity

- Own transcription of naibbe.py (v1) with random.Random(19) vs b3.Naibbe(seed 19) on Pliny: identical token stream: True (34625 tokens, retries 1353 / 1353).
- Shipped ciphertext decrypted with the shipped tables (a token in the unigram glyph set is a unigram; otherwise every prefix + suffix split is a candidate) against the shipped plaintext, cleaned as naibbe.py cleans it: 1063 of 1063 lines exact; token kinds {'uni': 16887, 'bi': 17630, 'amb': 247} (amb = more than one split, resolved by the plaintext).  No bigram token equals a unigram glyph, so UNAMBIGUOUS was on.  Share of one-letter units 0.486 (RESPACING 17 gives 17/36 = 0.472 plus the forced last letter of each line).
- Deck.  Table shares among unigram tokens (52 cards: alpha .385, beta .154 each, gamma .077 each; 78 cards: alpha .359, beta1 .179, beta2/3 .141, gamma .090), and the variance over lines of the number of alpha cards among the first 40 visible cards (a deck reshuffled at every line start is hypergeometric, about 2.2-2.7; one deck running across lines is larger):

| text | unigram tokens | unigram share | alpha | beta1 | beta2 | beta3 | gamma1 | gamma2 | chi2 vs 52 | chi2 vs 78 | alpha in first 40 cards: lines, mean, var |
|---|---|---|---|---|---|---|---|---|---|---|---|
| shipped Pliny | 16887 | 0.486 | 0.384 | 0.156 | 0.153 | 0.153 | 0.075 | 0.078 | 1.8 | 184.0 | 906, 14.58, 2.80 |
| port (= own transcription), 52 cards, seed 19 | 16609 | 0.480 | 0.387 | 0.151 | 0.154 | 0.159 | 0.076 | 0.074 | 6.4 | 254.4 | 906, 14.56, 2.70 |
| own 78-card control | 16625 | 0.480 | 0.360 | 0.182 | 0.137 | 0.141 | 0.090 | 0.090 | 228.6 | 2.3 | 906, 13.47, 4.65 |
| own 52-card control, one deck across lines | 16747 | 0.483 | 0.385 | 0.153 | 0.156 | 0.154 | 0.077 | 0.075 | 1.6 | 215.3 | 906, 14.62, 4.46 |

- Ten seeds of the port on the Pliny plaintext (token counts [34625, 34691, 34717, 34726, 34661, 34828, 34656, 34694, 34641, 34732]; shipped 34764); subset matches per seed [7, 7, 7, 7, 7, 7, 8, 7, 7, 7]:

| item | shipped | port mean +- sd [min, max] | z(shipped) | 78-card mean | b3 tol |
|---|---|---|---|---|---|
| h2 raw | 2.081 | 2.085 +- 0.00285 [2.080, 2.088] | -1.431 | 2.101 | 0.212 |
| h3 raw | 1.794 | 1.798 +- 0.00276 [1.795, 1.804] | -1.558 | 1.814 | 0.186 |
| h2 mrg | 2.294 | 2.297 +- 0.00356 [2.291, 2.301] | -0.799 | 2.312 | 0.235 |
| h3 mrg | 2.043 | 2.047 +- 0.00269 [2.042, 2.051] | -1.357 | 2.060 | 0.213 |
| Zipf | -0.921 | -0.907 +- 0.00442 [-0.917, -0.900] | -3.235 | -0.910 | 0.104 |
| TTR | 0.163 | 0.164 +- 0.000657 [0.163, 0.165] | -2.442 | 0.171 | 0.039 |
| hapax/types | 0.411 | 0.414 +- 0.00423 [0.407, 0.419] | -0.867 | 0.409 | 0.070 |
| hapax/tokens | 0.067 | 0.068 +- 0.000854 [0.066, 0.069] | -1.479 | 0.070 | 0.032 |
| adj exact | 0.00158 | 0.00132 +- 0.000161 [0.00106, 0.00164] | 1.622 | 0.00145 | 0.000815 |
| adj LD<=1 | 0.013 | 0.013 +- 0.000452 [0.012, 0.014] | 0.441 | 0.013 | 0.00413 |
| sc cover | 0.529 | 0.527 +- 0.00222 [0.523, 0.531] | 0.952 | 0.518 | 0.064 |
| sc <=10 | 0.152 | 0.147 +- 0.00123 [0.145, 0.149] | 4.212 | 0.143 | 0.027 |
| sc <=10 shuf | 0.156 | 0.152 +- 0.00223 [0.149, 0.155] | 1.448 | 0.148 | 0.024 |
| sc ratio | 0.977 | 0.964 +- 0.016 [0.937, 0.989] | 0.827 | 0.968 | 0.113 |
| pos lock | 0.628 | 0.631 +- 0.00174 [0.627, 0.634] | -1.789 | 0.622 | 0.064 |
| MZ peak log2 s | 9.000 | 10.200 +- 0.919 [9.000, 11.000] | -1.306 | 9.000 | 1.000 |
| MZ peak R | 0.00313 | 0.00537 +- 0.00275 [0.00217, 0.00989] | -0.813 | 0.00283 | 0.029 |
| tok pred | 0.021 | 0.021 +- 0.00114 [0.020, 0.023] | 0.073 | 0.020 | 0.00249 |
| char 3g bits | 1.809 | 1.814 +- 0.00301 [1.809, 1.819] | -1.396 | 1.829 | 0.189 |
| JSD halves | 0.00178 | 0.00173 +- 0.000104 [0.00155, 0.00193] | 0.541 | 0.00167 | 0.00626 |

- Full 37-item battery (b3.battery as instrument, b3's tolerances): port seed 19 matches 17 full / 17 short; shipped 17 / 17.  Items whose mark differs: full none, short none.  Items where port and shipped differ by more than tol: ['j_jacc_excess'].

## 6. Naibbe long range: cipher property or skeleton artefact?

Pouring only cuts the flat token stream into lines and pages; it never reorders tokens (assert: True), and R(s) is computed on the flat stream, so the skeleton cannot remove long-range structure.  R(s) with 10 shuffles (random.Random(707)); divcom own transcription = b3 port: True.

| sequence | tokens | types | peak log2 s | peak R | 16 | 32 | 64 | 128 | 256 | 512 | 1024 | 2048 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| naibbe_pliny ciphertext (first N) | 34116 | 5555 | 10 | 0.0040 | -0.00781 | -0.00773 | -0.00706 | -0.00599 | -0.00327 | 0.00402 | 0.00402 | -0.000612 |
| naibbe_pliny decrypted letter units (first N) | 34116 | 384 | 9 | 0.0195 | -0.017 | -0.00457 | 0.00388 | 0.00845 | 0.018 | 0.019 | 0.017 | 0.011 |
| Pliny NH 16 plaintext words (whole book) | 8998 | 4176 | 10 | 0.0999 | 0.00205 | 0.019 | 0.036 | 0.060 | 0.079 | 0.094 | 0.100 | 0.088 |
| naibbe_divcom ciphertext (first N) | 34116 | 5255 | 8 | 0.0039 | -0.00748 | -0.0051 | -0.000833 | 0.00237 | 0.00394 | 0.00238 | 0.000779 | 0.000602 |
| naibbe_divcom decrypted letter units | 34116 | 304 | 8 | 0.0253 | -0.016 | -0.0065 | 0.00964 | 0.019 | 0.025 | 0.023 | 0.019 | 0.014 |
| Divina Commedia plaintext words (lines encrypted) | 13061 | 3313 | 9 | 0.0556 | 0.000454 | 0.021 | 0.035 | 0.047 | 0.055 | 0.056 | 0.047 | 0.042 |
| latin control, same word count as Pliny | 8998 | 4534 | 11 | 0.0556 | 0.00836 | 0.014 | 0.021 | 0.027 | 0.038 | 0.052 | 0.055 | 0.056 |
| voynich_ZL, same token count as Pliny words | 8998 | 2972 | 8 | 0.1431 | 0.047 | 0.086 | 0.118 | 0.141 | 0.143 | 0.125 | 0.115 | 0.108 |
| voynich_ZL (full) | 34116 | 7236 | 9 | 0.2915 | 0.066 | 0.114 | 0.173 | 0.234 | 0.283 | 0.291 | 0.290 | 0.279 |

Hybrid probe (first half Naibbe-Pliny ciphertext, second half Naibbe-Dante ciphertext, poured): JSD halves 0.0033 (real 0.0626), MZ peak R 0.0276 at 2^11; subset matches 7/20.

## 7. Method critique

1. **Reproducibility.**  The re-run reproduces every committed number except the 72 Italian values (36 items, full and short).  The Italian control reads a git-ignored file that vatican5/build_it_lm.py rebuilds from Nuntiaturberichte OCR; the September build and the one in this checkout differ (section 0), and neither is clean Italian (Latin passages, German editorial text, OCR debris; v->u, j->i, k->c, w->u, y->i, so its h0 and the "gallows" items are not comparable).  Italian drops from 14/12 to 9/8.  Freeze a corpus file under data/ with a checksum or drop the row.
2. **"Pre-registered" is not supported by the record.**  The battery and rule sit in BATTERY_TEXT inside b3_bakeoff.py; the docstring and section 6 say they were fixed before any score was computed.  The script, b3.json and b3.md first appear together in commit f1a99b941 (16 Sept, "Commit all pending working files"), and the hard-coded CONCLUSION, which quotes the scores, is in the same file.  NOTES.md section 7 (commit f602841aa, 15 Sept) called for a pre-registered bake-off one day earlier, but with a different list (illustration-by-scribe co-clustering, A/B separability, the f and p rules), none of which is in b3.  The items were also chosen after a1-a6 had shown, on the same transcription, where Voynichese is extreme.  Accurate wording: "battery and match rule written into the script before the scores were tabulated (self-reported, no external timestamp)".
3. **The tolerance rule.**  (a) The 10 % band ignores sampling noise.  A 20-block page jackknife puts tol below two standard errors on adj exact (tol/SE 0.88), adj LD<=1 (1.9), sc cover (1.9), sc <=10 (1.7), sc <=10 shuf (1.6), MZ peak R (0.92), tok pred (1.2), JSD halves (0.37) and MZ peak position (0.40).  That covers all six subset items b3 lists as failed by every non-Voynich corpus at full length (adj exact, adj LD<=1, sc <=10, MZ peak R, tok pred, JSD halves), so a text from the same process as Voynichese would often fail them too.  The candidates still miss them by many standard errors (Naibbe adj exact -7.0, adj LD<=1 -12.5, sc <=10 -7.2, MZ peak R -8.8 combined SE; Latin -8.5 to -18.6).  A noise-aware rule (max(tol, 2 x combined SE)) moves only a few marks: Naibbe 7 -> 9 of 20 (TTR, tok pred), autocopist 3 -> 4, Latin 2 -> 2.  The ranking holds.  (b) Some items are generous: hapax/types tol/SE 8.8, h2/h3 4.4-5.9, sc ratio 5.9.  On gallows mid and JSD odd/even the autocopist seed spread makes tol at least the real value, so anything between 0 and about twice the real value matches.  (c) The spread term, one generator's seed-to-seed difference, sets the tolerance on 8 of 37 items for every candidate.  (d) Correlated items count separately: six entropy items, five self-citation items.  Weighting each of 10 families equally gives Naibbe 4.3/10, Rugg-sorted 3.6 and the rest 2.0-2.4 (full length).  The order is unchanged, but Naibbe's 17/37 includes all six entropy items.  (e) Some marks sit on a knife edge: autocopist_s7 short h2 mrg passes in b3 (|diff| 0.247 vs tol 0.249) and fails under this script's estimator (0.250 vs 0.248); the two h2 estimators differ by 0.002 bits.  (f) The MZ peak position is noise: jackknife SE 2.5 octaves, and the ZL peak moves from 2^10 with 3 shuffles to 2^9 with 20.  b3 notes this in section 6; the item should not be scored.
4. **Two "all-fail" items measure the real text's composition.**  JSD halves and MZ peak R on ZL are inflated by the A+B mixture (the first half of the pages is mostly A, the second mostly B).  The Currier A pages and the Currier B pages each fail both items under the same rule (b3's own reference rows).  No generator was given two regimes, so every one fails these items by construction.  That says nothing new about any family beyond "single regime".
5. **Gibberish.**  The full battery cycles 10,075 tokens four times, so hapax and one-page types are 0 by construction; b3 says so.  The short battery is the same size, but it pools 38 writers and pours them across ZL pages, so pages straddle writers.  At equal size per writer (each file against 40 Voynich runs of the same token count), h2 is 3.07 vs 1.92 (0/38 files inside the Voynich 5-95 % band) and positional lock 0.32 vs 0.68 (1/38 files inside).  The exclusion stands.  The writer changes do create drift: gibberish short JSD halves 0.066 and MZ R 0.59 are above the real short values (0.040, 0.150), so a multi-writer text fails these items by having too much drift.  Minor: 9 hyphenated line breaks split into two tokens; 164 accented letters stripped.  The short reference (first 10,053 ZL tokens) is herbal f1r-f58v, about 73 % Currier A and 27 % B, not "almost entirely A".  Using every third page of the whole manuscript instead moves subset scores by at most 2 (Latin 2 -> 1, Naibbe 7 -> 8, autocopist 4 -> 3 / 4 -> 2, gibberish 2 -> 3).
6. **The Naibbe port is faithful.**  An independent line-by-line transcription of naibbe.py (v1) reproduces b3.Naibbe token for token (34,625 tokens, 1,353 retries; Dante also identical).  The shipped ciphertext decrypts exactly to the shipped plaintext (1,063/1,063 lines), and no bigram token equals a unigram glyph, so UNAMBIGUOUS was on.  The unigram table shares fit the 52-card deck (chi2 1.8, against 184 for 78 cards).  The per-line variance of alpha cards among the first 40 (2.80) matches a deck reshuffled at every line (port 2.70; one-running-deck control 4.46).  So the shipped file was made with naibbe.py's v1 configuration, not v2's 78-card default, which closes b3's "not checked" item.  On the battery the port matches the shipped file at b3's resolution: identical marks on all 37 items (17 full, 17 short).  Only adj Jaccard xs differs by more than tol (0.0061 vs 0.0108; both fail).  Against 10 seeds the shipped file lies just outside the seed range on Zipf (-0.921 vs -0.917 to -0.900) and sc <=10 (0.152 vs 0.145 to 0.149).  Both gaps are under a fifth of tol; the cause was not identified.
7. **The missing long-range structure in Naibbe comes from the cipher, not the skeleton.**  Pouring never reorders tokens, and R(s) runs on the flat stream: naibbe_pliny and naibbe_pliny_lines have the same R.  The plaintext carries topic structure: Pliny NH 16 words R 0.100 at 8,998 words, against 0.056 for the Latin control and 0.143 for Voynich at the same count.  The decrypted 1-2-letter units the cipher actually encodes keep 0.020, and the ciphertext 0.004 (Dante: 0.056 -> 0.025 -> 0.004).  Respacing into letter units removes most of the word-level signal, and the homophonic table draws remove the rest.  Hybrid probe: Naibbe-Pliny ciphertext followed by Naibbe-Dante ciphertext, a Latin-to-Italian switch in the plaintext, gives JSD halves 0.0033 (real 0.063) and MZ R 0.028.  With fixed tables Naibbe flattens even a change of language, so b3's open hybrid ("a Naibbe-like encoding of a text with real topic structure") would not supply the A/B drift unless the tables or the respacing themselves changed between A and B.  Naibbe also has no line mechanism, so "no line-initial gallows preference" follows from its specification; keeping the shipped line breaks gives 0.033.
8. **Some items depend on the alphabet.**  The gallows items (k, t, p, f) and the merged-glyph items (ch, sh, in, ee) are defined on EVA.  On Latin, English, Italian and the gibberish they count ordinary letters: Latin "gallows init" 0.199 matches Voynich 0.223 by accident, and the Italian build has no k at all.  Matches and fails on these items carry no meaning for non-EVA corpora.
9. **Shuffle noise is small.**  The sc ratio from one shuffle and from 20 shuffles: ZL 1.130 vs 1.124 +- 0.005, autocopist 1.196 vs 1.193 +- 0.009, Naibbe 0.977 vs 0.984 +- 0.009.  The MZ peak R from 3 and from 20 shuffles agrees within 0.003 bits.  b3's single shuffle is adequate.

## 8. Corrected wording for the b3 conclusion (section 5)

Under a rule that the real text's own Currier-B pages fail on 18 of 37 items (short battery), no generator or control comes close to Voynichese.  The three Naibbe ciphertexts score best (17/37 at full length, 16-17 short; 4.3 of 10 item families).  Rugg-sorted is next at full length (14; 13 short, where autocopist_s7 reaches 14).  The autocopist, Rugg grille, Latin, English and human gibberish trail at 8-10 (autocopist_s7 short: 14).  The Italian control is not reproducible: its git-ignored OCR corpus was rebuilt, giving 14/12 in September and 9/8 today.  It is left out of the ranking.  The counts are a ranking under a deliberately narrow rule, not pass/fail verdicts.  On adjacency, self-citation, MZ peak height, token predictability and half-to-half drift the 10 % tolerance is narrower than twice the real text's own sampling error.  The candidates miss those items by many standard errors, though, so the ranking survives a noise-aware rule.  Every non-Voynich corpus fails the adjacent-repeat rates (exact and LD<=1), self-citation within 10 tokens, the MZ peak height and (full length) the first-half/second-half glyph-bigram divergence (JSD halves 0.063 bits; language controls 0.003-0.007, autocopist 0.02, Rugg 0.003-0.01, Naibbe 0.002).  The last two are also failed by the Currier A and B pages on their own.  They measure the A+B mixture of the real text, which no generator was given.  By family: natural language is excluded by the conditional character entropies (h2 1.1-1.3 bits and h3 0.7-1.0 bits too high), positional lock (0.26-0.35 vs 0.64) and character 3-gram cross-entropy.  The autocopist reproduces the self-citation ratio and the MZ peak position but fails the Zipf slope (-0.83 to -0.86 vs -1.04).  It is excluded by vocabulary growth (TTR 0.34-0.38 vs 0.21, hapax/tokens, Heaps 0.85-0.88 vs 0.74), a 0.4-0.6-bit excess in glyph entropy, gallows in line-interior position (0.26-0.37 vs 0.065), near-zero token predictability, and a long-range peak that overshoots (0.47 vs 0.29 bits).  The Rugg grille is excluded by an almost hapax-free vocabulary that changes wholesale every four pages (hapax/types 0.06, MZ peak R 2.0 bits); the sorted variant by 9 % exact adjacent repeats.  The Naibbe cipher matches the character entropies, mean word length, positional lock and character predictability to within tolerance but misses the Zipf slope (-0.89 to -0.92 vs -1.04).  It is excluded by the absence of long-range structure (|R(s)| <= 0.009 bits at every scale, vs 0.29 for the real text and 0.08-0.16 for Latin and English).  That is a property of the cipher, which cuts the plaintext into one- and two-letter units (Pliny plaintext 0.10 -> letter units 0.02 -> ciphertext 0.004), not of the page skeleton.  It is further excluded by too few hapaxes, weak self-citation (ratio 0.96-0.98 vs 1.13) and no line-initial gallows preference (it has no line mechanism).  Human gibberish is excluded by character entropy (h2 3.9 bits pooled; 3.1 per writer against 1.9 for Voynich runs of the same length) and the absence of slot grammar (positional lock 0.14 pooled; 0.32 per writer against 0.68).  No single family therefore remains compatible as written.  The glyph-level items favour a verbose-cipher-like encoding (Naibbe).  The self-citation ratio favours a copy-and-modify process, though the autocopist overshoots the absolute self-citation and long-range levels.  The drift items demand a regime change between A and B that none of the generators was built to have.  A Naibbe encoding of a topically structured or bilingual plaintext under fixed tables does not supply that change (Pliny-then-Dante ciphertext: JSD halves 0.003, MZ R 0.03); a cipher account would need the tables or the respacing themselves to change between A and B.  The bake-off does not exclude such hybrids, nor an autocopist with a tighter glyph grammar and a drifting source, and it says nothing about meaning.  (Title and section 0: replace "pre-registered" with "fixed battery, written into the script before the scores were tabulated".)

## 9. Checked / not checked

- Checked: b3_bakeoff.py re-run as-is on 11 Oct 2026 with today's 38 Gutenberg files, the Naibbe repo at f2675ec and the 38 Gaskell & Bowern files.  Every committed value is identical except Italian, and the cause is identified (section 0).  results/b3.json and b3.md in the working tree now hold the re-run (only the Italian rows differ); `git checkout -- results/b3.json results/b3.md` restores the committed version.
- Checked: 20 of the 37 items recomputed with independent code (own TSV loader, conditional entropy, glyph merge, LD<=1 test, self-citation, positional lock, MZ R(s), predictability, JSD) on voynich_ZL, latin, naibbe_pliny, autocopist_s19, autocopist_s7 and gaskell_gibberish, full and short.  Maximum relative difference from b3 is 0.2 %.  The causes are b3's h2, which drops each page's last bigram, and its 3-gram model, whose context count includes unfollowed bigrams.  One mark differs (autocopist_s7 short h2 mrg, on the boundary).
- Checked: the own LD<=1 test against a DP Levenshtein on 40,010 pairs (0 disagreements); the seed-1 within-page shuffle and b3's three MZ shuffles replicated exactly; 20-shuffle noise for both.
- Checked: the match rule re-implemented; 20-block jackknife SE for ZL, Latin, Naibbe-Pliny and autocopist_s19; a noise-aware re-score; a family-weighted re-count of b3's 37 marks.
- Checked: gibberish per writer at equal size against Voynich runs of the same length; a whole-manuscript short reference.
- Checked: the Naibbe port against an independent transcription of naibbe.py (identical); the shipped ciphertext decrypted against the shipped plaintext (exact); the deck (52 cards, reshuffled per line); 10 port seeds and 3 78-card runs on the subset; port vs shipped on all 37 items (b3.battery used as the instrument).
- Checked: Naibbe long range on plaintext words, decrypted units and ciphertext; that pouring preserves token order; a Pliny-then-Dante hybrid.
- Checked: every sentence of b3 section 5 against the committed and re-run numbers (section 1 table).
- Not checked: the other 17 items (h0, h1, the length items, Heaps, sc prev2, irrev bigr, the line-position items, types on one page, adj Jaccard xs, JSD odd/even) were not recomputed independently.  Their values only reproduce on re-run.
- Not checked: English, the two Rugg generators, the voynich_A / voynich_B rows and naibbe_pliny_lines were not recomputed (re-run only).  The autocopist's fidelity to Timm's Java code is a4's caveat (v_a4).
- Not checked: which corpus_it.txt build the September run used.  The file is git-ignored; only its first words survive, in v_a4.md.
- Not checked: why the shipped Naibbe file sits just outside the 10-seed range on Zipf and sc <=10.  The structure is identical; the gaps are under a fifth of tol.
- Not checked: completeness of the 38 Gaskell & Bowern files against the paper (10,075 tokens here, about 10,053 reported).
- User must verify: the corrected wording before anything reaches NOTES.md or docs/ (neither edited here).
