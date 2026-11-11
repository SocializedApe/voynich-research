# Slot-level reinforcing improviser v4: opener in context | middle | ending (10 Nov 2026)

Script `slots4.py`. Fitted (d; theta; share passed up):
- opener: d 0.66, 0.88, 0.88, 0.92, 0.91, 0.87, 0.92, 0.95; theta 7.2, 3.0, 4.1, 3.6, 3.5, 3.3, 2.7, 1.5; passed up book 0.22, context 0.62, lang 0.70, hand 0.81, section 0.78, quire 0.65, page 0.89, line 0.99; kept in generation ['book', 'context', 'lang', 'hand', 'section', 'quire', 'page', 'line']
- middle: d 1.00, 0.99, 0.99, 0.98, 0.97, 0.95, 0.99; theta 6.2, 0.7, 0.9, 5.3, 3.1, 2.0, 1.9; passed up book 0.99, lang 0.97, hand 0.97, section 0.94, quire 0.84, page 0.86, line 0.99; kept in generation ['book', 'hand', 'section', 'quire', 'page']
- ending: d 0.44, 0.56, 0.71, 0.73, 0.68, 0.84, 0.97; theta 29.4, 24.6, 11.3, 12.7, 11.2, 5.2, 2.4; passed up book 0.28, lang 0.41, hand 0.45, section 0.48, quire 0.35, page 0.69, line 0.98; kept in generation ['book', 'lang', 'hand', 'section', 'quire', 'page', 'line']

Self-consistency: share passed up in generation (seed 19) against the fit, per kept level:
- opener: book 0.10 (fit 0.22), context 0.60 (fit 0.62), lang 0.61 (fit 0.70), hand 0.77 (fit 0.81), section 0.72 (fit 0.78), quire 0.65 (fit 0.65), page 0.85 (fit 0.89), line 0.98 (fit 0.99)
- middle: book 0.96 (fit 0.99), hand 0.93 (fit 0.97), section 0.93 (fit 0.94), quire 0.84 (fit 0.84), page 0.84 (fit 0.86)
- ending: book 0.31 (fit 0.28), lang 0.43 (fit 0.41), hand 0.37 (fit 0.45), section 0.45 (fit 0.48), quire 0.33 (fit 0.35), page 0.64 (fit 0.69), line 0.98 (fit 0.98)

Match rule as b3; held-out = the 30 items outside hybrid_model.TUNED_B3. Scribe ratios as scribe_ratio.py.

| text | matched/37 | held-out/30 | between scribes / within | same scribe other doc / within | JSD A vs B | JSD quire halves in cell | edge X within | edge X across line | Voynich types share |
|---|---|---|---|---|---|---|---|---|---|
| voynich_ZL | 37 | 30 | 2.96 [2.18-3.59] | 2.00 [1.87-2.15] | 0.101 | 0.052 (4) | 0.0597 | 0.0010 | 1.00 |
| autocopist_s19 | 12 | 11 | | | | | | | |
| autocopist_s7 | 15 | 14 | | | | | | | |
| ome4_s19 | 20 | 18 | 2.71 [2.17-3.11] | 1.71 [1.62-1.81] | 0.054 | 0.059 (4) | 0.0639 | 0.0063 | 0.43 |
| ome4_s7 | 20 | 18 | 2.69 [2.47-2.99] | 1.68 [1.57-1.77] | 0.097 | 0.080 (4) | 0.0507 | 0.0079 | 0.51 |
| ome4_s3 | 21 | 19 | 2.49 [2.02-2.96] | 1.81 [1.60-2.03] | 0.067 | 0.069 (4) | 0.0443 | 0.0002 | 0.57 |
| ome4_s11 | 13 | 13 | 2.78 [2.52-2.98] | 1.74 [1.61-1.86] | 0.097 | 0.090 (4) | 0.0525 | 0.0077 | 0.49 |
| ome4_s23 | 15 | 14 | 2.95 [2.57-3.38] | 1.97 [1.78-2.18] | 0.069 | 0.085 (4) | 0.0670 | 0.0113 | 0.52 |

## Items, all corpora

### a-d: characters, word length, vocabulary, adjacency

| corpus | h0 raw | h1 raw | h2 raw | h3 raw | h2 mrg | h3 mrg | len mean | len sd | len=1 | len>=9 | Zipf | TTR | hapax/types | hapax/tokens | Heaps | adj exact | adj LD<=1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| voynich_ZL | 4.700 ✓ | 3.870 ✓ | 2.111 ✓ | 1.841 ✓ | 2.345 ✓ | 2.114 ✓ | 4.990 ✓ | 1.788 ✓ | 0.032 ✓ | 0.024 ✓ | -1.041 ✓ | 0.202 ✓ | 0.680 ✓ | 0.137 ✓ | 0.732 ✓ | 0.00841 ✓ | 0.042 ✓ |
| autocopist_s19 | 4.322 ✓ | 3.873 ✓ | 2.684 ✗ | 2.361 ✗ | 3.014 ✗ | 2.676 ✗ | 5.463 ✓ | 2.111 ✗ | 0.000416 ✗ | 0.091 ✗ | -0.772 ✗ | 0.397 ✗ | 0.706 ✓ | 0.280 ✗ | 0.914 ✗ | 0.00182 ✗ | 0.079 ✗ |
| autocopist_s7 | 4.322 ✓ | 3.815 ✓ | 2.497 ✗ | 2.281 ✗ | 2.691 ✗ | 2.463 ✗ | 4.616 ✓ | 2.022 ✗ | 0.00603 ✗ | 0.051 ✓ | -0.965 ✓ | 0.279 ✓ | 0.697 ✓ | 0.194 ✓ | 0.818 ✓ | 0.00252 ✗ | 0.085 ✗ |
| ome4_s19 | 4.700 ✓ | 3.868 ✓ | 2.138 ✓ | 1.742 ✓ | 2.471 ✓ | 2.177 ✓ | 6.305 ✗ | 2.796 ✗ | 0.015 ✗ | 0.211 ✗ | -0.982 ✓ | 0.291 ✓ | 0.744 ✓ | 0.217 ✓ | 0.805 ✓ | 0.011 ✗ | 0.033 ✗ |
| ome4_s7 | 4.700 ✓ | 3.901 ✓ | 2.316 ✓ | 2.059 ✗ | 2.614 ✓ | 2.352 ✗ | 5.311 ✓ | 2.754 ✗ | 0.065 ✗ | 0.127 ✗ | -0.982 ✓ | 0.309 ✓ | 0.760 ✗ | 0.235 ✗ | 0.831 ✗ | 0.00858 ✓ | 0.032 ✗ |
| ome4_s3 | 4.700 ✓ | 3.810 ✓ | 2.381 ✗ | 2.089 ✗ | 2.654 ✓ | 2.396 ✗ | 5.294 ✓ | 2.784 ✗ | 0.043 ✗ | 0.127 ✗ | -1.008 ✓ | 0.313 ✓ | 0.755 ✗ | 0.237 ✗ | 0.818 ✓ | 0.007 ✗ | 0.040 ✓ |
| ome4_s11 | 4.700 ✓ | 3.803 ✓ | 2.405 ✗ | 2.102 ✗ | 2.696 ✗ | 2.395 ✗ | 5.398 ✓ | 2.759 ✗ | 0.039 ✗ | 0.129 ✗ | -1.001 ✓ | 0.336 ✗ | 0.768 ✗ | 0.258 ✗ | 0.828 ✗ | 0.00637 ✗ | 0.033 ✗ |
| ome4_s23 | 4.700 ✓ | 3.881 ✓ | 2.311 ✓ | 1.961 ✓ | 2.585 ✓ | 2.258 ✓ | 6.115 ✗ | 2.854 ✗ | 0.018 ✗ | 0.178 ✗ | -0.956 ✓ | 0.351 ✗ | 0.769 ✗ | 0.270 ✗ | 0.840 ✗ | 0.00528 ✗ | 0.020 ✗ |

### e-g: self-citation, slot grammar, line position

| corpus | sc cover | sc <=10 | sc prev2 | sc <=10 shuf | sc ratio | irrev bigr | pos lock | len first | len mid | len last | gallows init | gallows mid |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| voynich_ZL | 0.651 ✓ | 0.276 ✓ | 0.414 ✓ | 0.242 ✓ | 1.140 ✓ | 0.095 ✓ | 0.643 ✓ | 5.429 ✓ | 4.957 ✓ | 4.735 ✓ | 0.223 ✓ | 0.063 ✓ |
| autocopist_s19 | 0.760 ✗ | 0.333 ✗ | 0.473 ✓ | 0.273 ✓ | 1.218 ✓ | 0.110 ✓ | 0.443 ✗ | 5.977 ✓ | 5.425 ✓ | 5.099 ✓ | 0.307 ✗ | 0.248 ✗ |
| autocopist_s7 | 0.785 ✗ | 0.379 ✗ | 0.549 ✗ | 0.333 ✗ | 1.137 ✓ | 0.185 ✗ | 0.543 ✗ | 5.232 ✓ | 4.551 ✓ | 4.395 ✓ | 0.383 ✗ | 0.417 ✗ |
| ome4_s19 | 0.566 ✗ | 0.227 ✗ | 0.343 ✓ | 0.223 ✓ | 1.017 ✗ | 0.080 ✓ | 0.701 ✓ | 6.286 ✗ | 6.313 ✗ | 6.270 ✗ | 0.042 ✗ | 0.065 ✓ |
| ome4_s7 | 0.554 ✗ | 0.215 ✗ | 0.329 ✗ | 0.215 ✓ | 0.999 ✗ | 0.085 ✓ | 0.678 ✓ | 5.105 ✓ | 5.338 ✓ | 5.344 ✓ | 0.032 ✗ | 0.016 ✓ |
| ome4_s3 | 0.572 ✗ | 0.251 ✓ | 0.368 ✓ | 0.245 ✓ | 1.023 ✗ | 0.070 ✓ | 0.656 ✓ | 5.327 ✓ | 5.289 ✓ | 5.311 ✓ | 0.160 ✓ | 0.084 ✓ |
| ome4_s11 | 0.541 ✗ | 0.217 ✗ | 0.330 ✗ | 0.213 ✓ | 1.017 ✗ | 0.050 ✓ | 0.768 ✗ | 5.451 ✓ | 5.386 ✓ | 5.413 ✓ | 0.00346 ✗ | 0.012 ✓ |
| ome4_s23 | 0.502 ✗ | 0.160 ✗ | 0.265 ✗ | 0.156 ✗ | 1.029 ✓ | 0.090 ✓ | 0.670 ✓ | 5.998 ✓ | 6.131 ✗ | 6.131 ✗ | 0.038 ✗ | 0.057 ✓ |

### h-k: long range, predictability, page level, drift

| corpus | MZ peak log2 s | MZ peak R | tok pred | char 3g bits | types 1 page | adj Jaccard xs | JSD halves | JSD odd/even |
|---|---|---|---|---|---|---|---|---|
| voynich_ZL | 9.000 ✓ | 0.310 ✓ | 0.024 ✓ | 1.873 ✓ | 0.683 ✓ | 0.037 ✓ | 0.062 ✓ | 0.00292 ✓ |
| autocopist_s19 | 9.000 ✓ | 0.514 ✗ | 0.00645 ✗ | 2.484 ✗ | 0.800 ✗ | 0.0036 ✗ | 0.024 ✗ | 0.014 ✗ |
| autocopist_s7 | 9.000 ✓ | 0.448 ✗ | 0.016 ✓ | 2.358 ✗ | 0.769 ✗ | 0.00332 ✗ | 0.019 ✗ | 0.00884 ✗ |
| ome4_s19 | 11.000 ✗ | 0.312 ✓ | 0.032 ✓ | 1.785 ✓ | 0.764 ✗ | 0.031 ✗ | 0.026 ✗ | 0.00555 ✓ |
| ome4_s7 | 11.000 ✗ | 0.366 ✓ | 0.025 ✓ | 2.109 ✗ | 0.776 ✗ | 0.034 ✓ | 0.058 ✓ | 0.00561 ✓ |
| ome4_s3 | 10.000 ✗ | 0.252 ✓ | 0.020 ✓ | 2.138 ✗ | 0.774 ✗ | 0.026 ✗ | 0.033 ✗ | 0.00583 ✓ |
| ome4_s11 | 10.000 ✗ | 0.318 ✓ | 0.017 ✓ | 2.151 ✗ | 0.785 ✗ | 0.030 ✗ | 0.050 ✗ | 0.00476 ✓ |
| ome4_s23 | 11.000 ✗ | 0.325 ✓ | 0.011 ✗ | 2.002 ✓ | 0.787 ✗ | 0.030 ✗ | 0.043 ✗ | 0.00413 ✓ |

Missed items per generated text (value vs Voynich):

- ome4_s19: b_len_mean 6.305 vs 4.990; b_len_sd 2.796 vs 1.788; b_len1 0.015 vs 0.032; b_len9 0.211 vs 0.024; d_adj_exact 0.011 vs 0.00841; d_adj_ld1 0.033 vs 0.042; e_cover 0.566 vs 0.651; e_w10 0.227 vs 0.276; e_ratio 1.017 vs 1.140; g_len_first 6.286 vs 5.429; g_len_mid 6.313 vs 4.957; g_len_last 6.270 vs 4.735; g_gal_init 0.042 vs 0.223; h_peak_log2s 11.000 vs 9.000; j_one_page 0.764 vs 0.683; j_jacc_excess 0.031 vs 0.037; k_jsd_halves 0.026 vs 0.062
- ome4_s7: a_h3_raw 2.059 vs 1.841; a_h3_mrg 2.352 vs 2.114; b_len_sd 2.754 vs 1.788; b_len1 0.065 vs 0.032; b_len9 0.127 vs 0.024; c_hapax_types 0.760 vs 0.680; c_hapax_tokens 0.235 vs 0.137; c_heaps 0.831 vs 0.732; d_adj_ld1 0.032 vs 0.042; e_cover 0.554 vs 0.651; e_w10 0.215 vs 0.276; e_prev2 0.329 vs 0.414; e_ratio 0.999 vs 1.140; g_gal_init 0.032 vs 0.223; h_peak_log2s 11.000 vs 9.000; i_char_bits 2.109 vs 1.873; j_one_page 0.776 vs 0.683
- ome4_s3: a_h2_raw 2.381 vs 2.111; a_h3_raw 2.089 vs 1.841; a_h3_mrg 2.396 vs 2.114; b_len_sd 2.784 vs 1.788; b_len1 0.043 vs 0.032; b_len9 0.127 vs 0.024; c_hapax_types 0.755 vs 0.680; c_hapax_tokens 0.237 vs 0.137; d_adj_exact 0.007 vs 0.00841; e_cover 0.572 vs 0.651; e_ratio 1.023 vs 1.140; h_peak_log2s 10.000 vs 9.000; i_char_bits 2.138 vs 1.873; j_one_page 0.774 vs 0.683; j_jacc_excess 0.026 vs 0.037; k_jsd_halves 0.033 vs 0.062
- ome4_s11: a_h2_raw 2.405 vs 2.111; a_h3_raw 2.102 vs 1.841; a_h2_mrg 2.696 vs 2.345; a_h3_mrg 2.395 vs 2.114; b_len_sd 2.759 vs 1.788; b_len1 0.039 vs 0.032; b_len9 0.129 vs 0.024; c_ttr 0.336 vs 0.202; c_hapax_types 0.768 vs 0.680; c_hapax_tokens 0.258 vs 0.137; c_heaps 0.828 vs 0.732; d_adj_exact 0.00637 vs 0.00841; d_adj_ld1 0.033 vs 0.042; e_cover 0.541 vs 0.651; e_w10 0.217 vs 0.276; e_prev2 0.330 vs 0.414; e_ratio 1.017 vs 1.140; f_lock 0.768 vs 0.643; g_gal_init 0.00346 vs 0.223; h_peak_log2s 10.000 vs 9.000; i_char_bits 2.151 vs 1.873; j_one_page 0.785 vs 0.683; j_jacc_excess 0.030 vs 0.037; k_jsd_halves 0.050 vs 0.062
- ome4_s23: b_len_mean 6.115 vs 4.990; b_len_sd 2.854 vs 1.788; b_len1 0.018 vs 0.032; b_len9 0.178 vs 0.024; c_ttr 0.351 vs 0.202; c_hapax_types 0.769 vs 0.680; c_hapax_tokens 0.270 vs 0.137; c_heaps 0.840 vs 0.732; d_adj_exact 0.00528 vs 0.00841; d_adj_ld1 0.020 vs 0.042; e_cover 0.502 vs 0.651; e_w10 0.160 vs 0.276; e_prev2 0.265 vs 0.414; e_w10_shuf 0.156 vs 0.242; g_len_mid 6.131 vs 4.957; g_len_last 6.131 vs 4.735; g_gal_init 0.038 vs 0.223; h_peak_log2s 11.000 vs 9.000; i_tok_acc 0.011 vs 0.024; j_one_page 0.787 vs 0.683; j_jacc_excess 0.030 vs 0.037; k_jsd_halves 0.043 vs 0.062

Runtime 136 s.
