# Slot-level reinforcing improviser v5: chained slots, each in the context of the previous (10 Nov 2026)

Script `slots5.py`. Fitted (d; theta; share passed up), levels book > context > lang > hand > section > quire > page > line:
- opener: d 0.51, 0.86, 0.89, 0.91, 0.89, 0.88, 0.92, 0.95; theta 33.9, 2.2, 3.2, 5.3, 4.1, 3.7, 2.6, 1.7; passed up book 0.18, context 0.56, lang 0.70, hand 0.80, section 0.77, quire 0.70, page 0.87, line 0.98; kept ['book', 'context', 'lang', 'hand', 'section', 'quire', 'page', 'line']
- middle: d 0.99, 0.92, 0.96, 0.98, 0.97, 0.94, 0.96, 0.98; theta 2.4, 1.2, 2.4, 2.9, 2.1, 1.8, 1.9, 1.7; passed up book 0.99, context 0.69, lang 0.83, hand 0.92, section 0.89, quire 0.77, page 0.92, line 1.00; kept ['book', 'context', 'lang', 'hand', 'section', 'quire', 'page', 'line']
- ending: d 0.57, 0.68, 0.79, 0.87, 0.87, 0.85, 0.88, 0.94; theta 11.2, 1.9, 3.9, 4.7, 3.2, 2.9, 3.0, 1.3; passed up book 0.22, context 0.34, lang 0.53, hand 0.71, section 0.76, quire 0.69, page 0.86, line 0.99; kept ['book', 'context', 'lang', 'hand', 'section', 'quire', 'page', 'line']

Self-consistency: share passed up in generation (seed 19) against the fit, per kept level:
- opener: book 0.18 (fit 0.18), context 0.56 (fit 0.56), lang 0.60 (fit 0.70), hand 0.70 (fit 0.80), section 0.71 (fit 0.77), quire 0.67 (fit 0.70), page 0.86 (fit 0.87), line 0.99 (fit 0.98)
- middle: book 0.98 (fit 0.99), context 0.64 (fit 0.69), lang 0.82 (fit 0.83), hand 0.90 (fit 0.92), section 0.88 (fit 0.89), quire 0.81 (fit 0.77), page 0.91 (fit 0.92), line 0.99 (fit 1.00)
- ending: book 0.23 (fit 0.22), context 0.31 (fit 0.34), lang 0.53 (fit 0.53), hand 0.70 (fit 0.71), section 0.72 (fit 0.76), quire 0.67 (fit 0.69), page 0.86 (fit 0.86), line 0.99 (fit 0.99)

Match rule as b3; held-out = the 30 items outside hybrid_model.TUNED_B3. Scribe ratios as scribe_ratio.py.

| text | matched/37 | held-out/30 | between scribes / within | same scribe other doc / within | JSD A vs B | JSD quire halves in cell | edge X within | edge X across line | Voynich types share |
|---|---|---|---|---|---|---|---|---|---|
| voynich_ZL | 37 | 30 | 2.96 [2.18-3.59] | 2.00 [1.87-2.15] | 0.101 | 0.052 (4) | 0.0597 | 0.0010 | 1.00 |
| autocopist_s19 | 12 | 11 | | | | | | | |
| autocopist_s7 | 15 | 14 | | | | | | | |
| chain5_s19 | 28 | 24 | 1.78 [1.58-1.95] | 1.38 [1.29-1.48] | 0.044 | 0.046 (4) | 0.0495 | 0.0011 | 0.59 |
| chain5_s7 | 23 | 20 | 1.67 [1.49-1.83] | 1.39 [1.31-1.47] | 0.040 | 0.058 (4) | 0.0615 | 0.0010 | 0.50 |
| chain5_s3 | 29 | 25 | 1.74 [1.64-1.84] | 1.43 [1.36-1.49] | 0.037 | 0.053 (4) | 0.0497 | 0.0034 | 0.58 |
| chain5_s11 | 25 | 22 | 2.03 [1.83-2.20] | 1.48 [1.40-1.58] | 0.053 | 0.057 (4) | 0.0466 | 0.0010 | 0.57 |
| chain5_s23 | 23 | 20 | 1.76 [1.62-1.87] | 1.38 [1.31-1.45] | 0.044 | 0.052 (4) | 0.0442 | -0.0007 | 0.53 |

## Items, all corpora

### a-d: characters, word length, vocabulary, adjacency

| corpus | h0 raw | h1 raw | h2 raw | h3 raw | h2 mrg | h3 mrg | len mean | len sd | len=1 | len>=9 | Zipf | TTR | hapax/types | hapax/tokens | Heaps | adj exact | adj LD<=1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| voynich_ZL | 4.700 ✓ | 3.870 ✓ | 2.111 ✓ | 1.841 ✓ | 2.345 ✓ | 2.114 ✓ | 4.990 ✓ | 1.788 ✓ | 0.032 ✓ | 0.024 ✓ | -1.041 ✓ | 0.202 ✓ | 0.680 ✓ | 0.137 ✓ | 0.732 ✓ | 0.00841 ✓ | 0.042 ✓ |
| autocopist_s19 | 4.322 ✓ | 3.873 ✓ | 2.684 ✗ | 2.361 ✗ | 3.014 ✗ | 2.676 ✗ | 5.463 ✓ | 2.111 ✗ | 0.000416 ✗ | 0.091 ✗ | -0.772 ✗ | 0.397 ✗ | 0.706 ✓ | 0.280 ✗ | 0.914 ✗ | 0.00182 ✗ | 0.079 ✗ |
| autocopist_s7 | 4.322 ✓ | 3.815 ✓ | 2.497 ✗ | 2.281 ✗ | 2.691 ✗ | 2.463 ✗ | 4.616 ✓ | 2.022 ✗ | 0.00603 ✗ | 0.051 ✓ | -0.965 ✓ | 0.279 ✓ | 0.697 ✓ | 0.194 ✓ | 0.818 ✓ | 0.00252 ✗ | 0.085 ✗ |
| chain5_s19 | 4.700 ✓ | 3.777 ✓ | 2.306 ✓ | 1.851 ✓ | 2.594 ✓ | 2.109 ✓ | 5.320 ✓ | 2.793 ✗ | 0.123 ✗ | 0.131 ✗ | -1.058 ✓ | 0.186 ✓ | 0.675 ✓ | 0.125 ✓ | 0.747 ✓ | 0.026 ✗ | 0.043 ✓ |
| chain5_s7 | 4.700 ✓ | 3.861 ✓ | 2.311 ✓ | 1.911 ✓ | 2.579 ✓ | 2.148 ✓ | 5.661 ✓ | 2.897 ✗ | 0.022 ✗ | 0.141 ✗ | -0.977 ✓ | 0.200 ✓ | 0.654 ✓ | 0.131 ✓ | 0.804 ✓ | 0.016 ✗ | 0.035 ✗ |
| chain5_s3 | 4.700 ✓ | 3.837 ✓ | 2.247 ✓ | 1.948 ✓ | 2.486 ✓ | 2.162 ✓ | 5.135 ✓ | 2.567 ✗ | 0.029 ✓ | 0.093 ✗ | -1.044 ✓ | 0.183 ✓ | 0.654 ✓ | 0.119 ✓ | 0.763 ✓ | 0.015 ✗ | 0.039 ✓ |
| chain5_s11 | 4.644 ✓ | 3.847 ✓ | 2.372 ✗ | 1.989 ✓ | 2.655 ✓ | 2.273 ✓ | 5.159 ✓ | 2.911 ✗ | 0.077 ✗ | 0.132 ✗ | -0.966 ✓ | 0.217 ✓ | 0.684 ✓ | 0.148 ✓ | 0.764 ✓ | 0.015 ✗ | 0.040 ✓ |
| chain5_s23 | 4.700 ✓ | 3.866 ✓ | 2.348 ✗ | 1.970 ✓ | 2.578 ✓ | 2.191 ✓ | 5.503 ✓ | 2.638 ✗ | 0.018 ✗ | 0.115 ✗ | -0.970 ✓ | 0.222 ✓ | 0.663 ✓ | 0.147 ✓ | 0.789 ✓ | 0.00899 ✓ | 0.027 ✗ |

### e-g: self-citation, slot grammar, line position

| corpus | sc cover | sc <=10 | sc prev2 | sc <=10 shuf | sc ratio | irrev bigr | pos lock | len first | len mid | len last | gallows init | gallows mid |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| voynich_ZL | 0.651 ✓ | 0.276 ✓ | 0.414 ✓ | 0.242 ✓ | 1.140 ✓ | 0.095 ✓ | 0.643 ✓ | 5.429 ✓ | 4.957 ✓ | 4.735 ✓ | 0.223 ✓ | 0.063 ✓ |
| autocopist_s19 | 0.760 ✗ | 0.333 ✗ | 0.473 ✓ | 0.273 ✓ | 1.218 ✓ | 0.110 ✓ | 0.443 ✗ | 5.977 ✓ | 5.425 ✓ | 5.099 ✓ | 0.307 ✗ | 0.248 ✗ |
| autocopist_s7 | 0.785 ✗ | 0.379 ✗ | 0.549 ✗ | 0.333 ✗ | 1.137 ✓ | 0.185 ✗ | 0.543 ✗ | 5.232 ✓ | 4.551 ✓ | 4.395 ✓ | 0.383 ✗ | 0.417 ✗ |
| chain5_s19 | 0.602 ✓ | 0.249 ✓ | 0.371 ✓ | 0.245 ✓ | 1.016 ✗ | 0.105 ✓ | 0.660 ✓ | 5.169 ✓ | 5.351 ✓ | 5.283 ✓ | 0.045 ✗ | 0.062 ✓ |
| chain5_s7 | 0.562 ✗ | 0.214 ✗ | 0.328 ✗ | 0.213 ✓ | 1.004 ✗ | 0.095 ✓ | 0.647 ✓ | 6.089 ✓ | 5.608 ✓ | 5.562 ✗ | 0.048 ✗ | 0.048 ✓ |
| chain5_s3 | 0.602 ✓ | 0.249 ✓ | 0.377 ✓ | 0.250 ✓ | 0.996 ✗ | 0.110 ✓ | 0.594 ✓ | 5.248 ✓ | 5.133 ✓ | 5.046 ✓ | 0.087 ✗ | 0.074 ✓ |
| chain5_s11 | 0.584 ✗ | 0.265 ✓ | 0.381 ✓ | 0.263 ✓ | 1.007 ✗ | 0.065 ✓ | 0.565 ✓ | 4.952 ✓ | 5.176 ✓ | 5.258 ✓ | 0.010 ✗ | 0.084 ✓ |
| chain5_s23 | 0.553 ✗ | 0.198 ✗ | 0.312 ✗ | 0.196 ✓ | 1.011 ✗ | 0.105 ✓ | 0.603 ✓ | 5.401 ✓ | 5.519 ✓ | 5.506 ✗ | 0.045 ✗ | 0.141 ✓ |

### h-k: long range, predictability, page level, drift

| corpus | MZ peak log2 s | MZ peak R | tok pred | char 3g bits | types 1 page | adj Jaccard xs | JSD halves | JSD odd/even |
|---|---|---|---|---|---|---|---|---|
| voynich_ZL | 9.000 ✓ | 0.310 ✓ | 0.024 ✓ | 1.873 ✓ | 0.683 ✓ | 0.037 ✓ | 0.062 ✓ | 0.00292 ✓ |
| autocopist_s19 | 9.000 ✓ | 0.514 ✗ | 0.00645 ✗ | 2.484 ✗ | 0.800 ✗ | 0.0036 ✗ | 0.024 ✗ | 0.014 ✗ |
| autocopist_s7 | 9.000 ✓ | 0.448 ✗ | 0.016 ✓ | 2.358 ✗ | 0.769 ✗ | 0.00332 ✗ | 0.019 ✗ | 0.00884 ✗ |
| chain5_s19 | 10.000 ✗ | 0.336 ✓ | 0.085 ✗ | 1.889 ✓ | 0.696 ✓ | 0.039 ✓ | 0.024 ✗ | 0.00377 ✓ |
| chain5_s7 | 10.000 ✗ | 0.372 ✓ | 0.032 ✓ | 1.948 ✓ | 0.674 ✓ | 0.043 ✗ | 0.022 ✗ | 0.00341 ✓ |
| chain5_s3 | 11.000 ✗ | 0.396 ✗ | 0.029 ✓ | 1.986 ✓ | 0.676 ✓ | 0.039 ✓ | 0.022 ✗ | 0.00417 ✓ |
| chain5_s11 | 11.000 ✗ | 0.410 ✗ | 0.036 ✗ | 2.030 ✓ | 0.703 ✓ | 0.037 ✓ | 0.036 ✗ | 0.0036 ✓ |
| chain5_s23 | 11.000 ✗ | 0.360 ✓ | 0.037 ✗ | 2.006 ✓ | 0.684 ✓ | 0.038 ✓ | 0.026 ✗ | 0.00303 ✓ |

Missed items per generated text (value vs Voynich):

- chain5_s19: b_len_sd 2.793 vs 1.788; b_len1 0.123 vs 0.032; b_len9 0.131 vs 0.024; d_adj_exact 0.026 vs 0.00841; e_ratio 1.016 vs 1.140; g_gal_init 0.045 vs 0.223; h_peak_log2s 10.000 vs 9.000; i_tok_acc 0.085 vs 0.024; k_jsd_halves 0.024 vs 0.062
- chain5_s7: b_len_sd 2.897 vs 1.788; b_len1 0.022 vs 0.032; b_len9 0.141 vs 0.024; d_adj_exact 0.016 vs 0.00841; d_adj_ld1 0.035 vs 0.042; e_cover 0.562 vs 0.651; e_w10 0.214 vs 0.276; e_prev2 0.328 vs 0.414; e_ratio 1.004 vs 1.140; g_len_last 5.562 vs 4.735; g_gal_init 0.048 vs 0.223; h_peak_log2s 10.000 vs 9.000; j_jacc_excess 0.043 vs 0.037; k_jsd_halves 0.022 vs 0.062
- chain5_s3: b_len_sd 2.567 vs 1.788; b_len9 0.093 vs 0.024; d_adj_exact 0.015 vs 0.00841; e_ratio 0.996 vs 1.140; g_gal_init 0.087 vs 0.223; h_peak_log2s 11.000 vs 9.000; h_peak_R 0.396 vs 0.310; k_jsd_halves 0.022 vs 0.062
- chain5_s11: a_h2_raw 2.372 vs 2.111; b_len_sd 2.911 vs 1.788; b_len1 0.077 vs 0.032; b_len9 0.132 vs 0.024; d_adj_exact 0.015 vs 0.00841; e_cover 0.584 vs 0.651; e_ratio 1.007 vs 1.140; g_gal_init 0.010 vs 0.223; h_peak_log2s 11.000 vs 9.000; h_peak_R 0.410 vs 0.310; i_tok_acc 0.036 vs 0.024; k_jsd_halves 0.036 vs 0.062
- chain5_s23: a_h2_raw 2.348 vs 2.111; b_len_sd 2.638 vs 1.788; b_len1 0.018 vs 0.032; b_len9 0.115 vs 0.024; d_adj_ld1 0.027 vs 0.042; e_cover 0.553 vs 0.651; e_w10 0.198 vs 0.276; e_prev2 0.312 vs 0.414; e_ratio 1.011 vs 1.140; g_len_last 5.506 vs 4.735; g_gal_init 0.045 vs 0.223; h_peak_log2s 11.000 vs 9.000; i_tok_acc 0.037 vs 0.024; k_jsd_halves 0.026 vs 0.062

Runtime 271 s.
