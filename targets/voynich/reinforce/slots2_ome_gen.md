# Slot-level reinforcing improviser v2, scheme ome (opener | middle | ending) (10 Nov 2026)

Script `slots2.py`. Fitted (d; theta; share passed up) per slot, levels book > lang > hand > section > quire > page > line:
- opener: d 0.62, 0.75, 0.86, 0.80, 0.80, 0.85, 0.96; theta 35.0, 19.6, 11.8, 9.9, 5.3, 3.9, 1.7; passed up 0.41, 0.52, 0.68, 0.55, 0.43, 0.70, 0.97
- middle: d 1.00, 0.99, 0.99, 0.98, 0.97, 0.95, 0.99; theta 6.2, 0.7, 0.9, 5.3, 3.1, 2.0, 1.9; passed up 0.99, 0.97, 0.97, 0.94, 0.84, 0.86, 0.99
- ending: d 0.44, 0.56, 0.71, 0.73, 0.68, 0.84, 0.97; theta 29.4, 24.6, 11.3, 12.7, 11.2, 5.2, 2.4; passed up 0.28, 0.41, 0.45, 0.48, 0.35, 0.69, 0.98

Match rule as b3; held-out = the 30 items outside hybrid_model.TUNED_B3. Scribe ratios as scribe_ratio.py.

| text | matched/37 | held-out/30 | between scribes / within | same scribe other doc / within | JSD A vs B | JSD quire halves in cell | edge X within | edge X across line | Voynich types share |
|---|---|---|---|---|---|---|---|---|---|
| voynich_ZL | 37 | 30 | 2.96 [2.18-3.59] | 2.00 [1.87-2.15] | 0.101 | 0.052 (4) | 0.0597 | 0.0010 | 1.00 |
| autocopist_s19 | 12 | 11 | | | | | | | |
| autocopist_s7 | 15 | 14 | | | | | | | |
| ome_s19 | 14 | 12 | 3.74 [3.31-4.38] | 2.19 [1.93-2.51] | 0.141 | 0.109 (4) | 0.0091 | 0.0105 | 0.51 |
| ome_gallows_s19 | 13 | 12 | 3.65 [3.22-4.26] | 2.15 [1.89-2.47] | 0.139 | 0.109 (4) | 0.0091 | 0.0058 | 0.50 |
| ome_s7 | 15 | 15 | 3.08 [2.71-3.44] | 2.02 [1.87-2.19] | 0.085 | 0.101 (4) | 0.0026 | 0.0020 | 0.50 |
| ome_gallows_s7 | 15 | 14 | 3.01 [2.64-3.37] | 1.99 [1.84-2.15] | 0.084 | 0.100 (4) | 0.0026 | 0.0007 | 0.49 |
| ome_s3 | 15 | 15 | 3.00 [2.79-3.30] | 1.98 [1.72-2.29] | 0.089 | 0.091 (4) | 0.0024 | 0.0031 | 0.54 |
| ome_gallows_s3 | 14 | 13 | 2.92 [2.73-3.20] | 1.95 [1.69-2.24] | 0.088 | 0.091 (4) | 0.0024 | 0.0027 | 0.54 |

## Items, all corpora

### a-d: characters, word length, vocabulary, adjacency

| corpus | h0 raw | h1 raw | h2 raw | h3 raw | h2 mrg | h3 mrg | len mean | len sd | len=1 | len>=9 | Zipf | TTR | hapax/types | hapax/tokens | Heaps | adj exact | adj LD<=1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| voynich_ZL | 4.700 ✓ | 3.870 ✓ | 2.111 ✓ | 1.841 ✓ | 2.345 ✓ | 2.114 ✓ | 4.990 ✓ | 1.788 ✓ | 0.032 ✓ | 0.024 ✓ | -1.041 ✓ | 0.202 ✓ | 0.680 ✓ | 0.137 ✓ | 0.732 ✓ | 0.00841 ✓ | 0.042 ✓ |
| autocopist_s19 | 4.322 ✓ | 3.873 ✓ | 2.684 ✗ | 2.361 ✗ | 3.014 ✗ | 2.676 ✗ | 5.463 ✓ | 2.111 ✗ | 0.000416 ✗ | 0.091 ✗ | -0.772 ✗ | 0.397 ✗ | 0.706 ✓ | 0.280 ✗ | 0.914 ✗ | 0.00182 ✗ | 0.079 ✗ |
| autocopist_s7 | 4.322 ✓ | 3.815 ✓ | 2.497 ✗ | 2.281 ✗ | 2.691 ✗ | 2.463 ✗ | 4.616 ✓ | 2.022 ✗ | 0.00603 ✗ | 0.051 ✓ | -0.965 ✓ | 0.279 ✓ | 0.697 ✓ | 0.194 ✓ | 0.818 ✓ | 0.00252 ✗ | 0.085 ✗ |
| ome_s19 | 4.700 ✓ | 3.877 ✓ | 2.435 ✗ | 2.116 ✗ | 2.739 ✗ | 2.459 ✗ | 5.673 ✓ | 2.796 ✗ | 0.030 ✓ | 0.150 ✗ | -0.946 ✓ | 0.340 ✗ | 0.749 ✗ | 0.255 ✗ | 0.823 ✓ | 0.00767 ✓ | 0.033 ✗ |
| ome_gallows_s19 | 4.700 ✓ | 3.885 ✓ | 2.450 ✗ | 2.131 ✗ | 2.757 ✗ | 2.476 ✗ | 5.680 ✓ | 2.796 ✗ | 0.030 ✓ | 0.150 ✗ | -0.943 ✓ | 0.348 ✗ | 0.754 ✗ | 0.263 ✗ | 0.827 ✓ | 0.00761 ✓ | 0.032 ✗ |
| ome_s7 | 4.700 ✓ | 3.844 ✓ | 2.337 ✗ | 2.050 ✗ | 2.598 ✓ | 2.321 ✓ | 5.689 ✓ | 2.691 ✗ | 0.023 ✗ | 0.132 ✗ | -0.943 ✓ | 0.325 ✗ | 0.751 ✗ | 0.244 ✗ | 0.837 ✗ | 0.00723 ✗ | 0.030 ✗ |
| ome_gallows_s7 | 4.700 ✓ | 3.852 ✓ | 2.359 ✗ | 2.070 ✗ | 2.623 ✓ | 2.343 ✗ | 5.694 ✓ | 2.690 ✗ | 0.022 ✗ | 0.132 ✗ | -0.940 ✓ | 0.336 ✗ | 0.757 ✗ | 0.254 ✗ | 0.842 ✗ | 0.00683 ✗ | 0.029 ✗ |
| ome_s3 | 4.700 ✓ | 3.850 ✓ | 2.343 ✗ | 2.063 ✗ | 2.657 ✓ | 2.429 ✗ | 5.564 ✓ | 2.730 ✗ | 0.030 ✓ | 0.138 ✗ | -0.983 ✓ | 0.316 ✓ | 0.754 ✗ | 0.238 ✗ | 0.850 ✗ | 0.00698 ✗ | 0.033 ✗ |
| ome_gallows_s3 | 4.700 ✓ | 3.858 ✓ | 2.364 ✗ | 2.083 ✗ | 2.682 ✗ | 2.451 ✗ | 5.575 ✓ | 2.731 ✗ | 0.030 ✓ | 0.139 ✗ | -0.978 ✓ | 0.326 ✗ | 0.758 ✗ | 0.247 ✗ | 0.851 ✗ | 0.00663 ✗ | 0.032 ✗ |

### e-g: self-citation, slot grammar, line position

| corpus | sc cover | sc <=10 | sc prev2 | sc <=10 shuf | sc ratio | irrev bigr | pos lock | len first | len mid | len last | gallows init | gallows mid |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| voynich_ZL | 0.651 ✓ | 0.276 ✓ | 0.414 ✓ | 0.242 ✓ | 1.140 ✓ | 0.095 ✓ | 0.643 ✓ | 5.429 ✓ | 4.957 ✓ | 4.735 ✓ | 0.223 ✓ | 0.063 ✓ |
| autocopist_s19 | 0.760 ✗ | 0.333 ✗ | 0.473 ✓ | 0.273 ✓ | 1.218 ✓ | 0.110 ✓ | 0.443 ✗ | 5.977 ✓ | 5.425 ✓ | 5.099 ✓ | 0.307 ✗ | 0.248 ✗ |
| autocopist_s7 | 0.785 ✗ | 0.379 ✗ | 0.549 ✗ | 0.333 ✗ | 1.137 ✓ | 0.185 ✗ | 0.543 ✗ | 5.232 ✓ | 4.551 ✓ | 4.395 ✓ | 0.383 ✗ | 0.417 ✗ |
| ome_s19 | 0.555 ✗ | 0.217 ✗ | 0.335 ✗ | 0.213 ✓ | 1.017 ✗ | 0.075 ✓ | 0.550 ✓ | 5.604 ✓ | 5.682 ✓ | 5.677 ✗ | 0.177 ✓ | 0.157 ✓ |
| ome_gallows_s19 | 0.550 ✗ | 0.213 ✗ | 0.330 ✗ | 0.209 ✓ | 1.021 ✗ | 0.075 ✓ | 0.547 ✓ | 5.664 ✓ | 5.682 ✓ | 5.677 ✗ | 0.345 ✗ | 0.157 ✓ |
| ome_s7 | 0.545 ✗ | 0.200 ✗ | 0.314 ✗ | 0.199 ✓ | 1.005 ✗ | 0.065 ✓ | 0.676 ✓ | 5.736 ✓ | 5.671 ✓ | 5.754 ✗ | 0.058 ✗ | 0.055 ✓ |
| ome_gallows_s7 | 0.540 ✗ | 0.196 ✗ | 0.309 ✗ | 0.195 ✓ | 1.007 ✗ | 0.070 ✓ | 0.659 ✓ | 5.772 ✓ | 5.671 ✓ | 5.754 ✗ | 0.254 ✓ | 0.055 ✓ |
| ome_s3 | 0.563 ✗ | 0.215 ✗ | 0.330 ✗ | 0.217 ✓ | 0.991 ✗ | 0.075 ✓ | 0.563 ✓ | 5.558 ✓ | 5.569 ✓ | 5.528 ✗ | 0.043 ✗ | 0.045 ✓ |
| ome_gallows_s3 | 0.556 ✗ | 0.210 ✗ | 0.324 ✗ | 0.213 ✓ | 0.988 ✗ | 0.085 ✓ | 0.550 ✓ | 5.652 ✓ | 5.569 ✓ | 5.528 ✗ | 0.230 ✓ | 0.045 ✓ |

### h-k: long range, predictability, page level, drift

| corpus | MZ peak log2 s | MZ peak R | tok pred | char 3g bits | types 1 page | adj Jaccard xs | JSD halves | JSD odd/even |
|---|---|---|---|---|---|---|---|---|
| voynich_ZL | 9.000 ✓ | 0.310 ✓ | 0.024 ✓ | 1.873 ✓ | 0.683 ✓ | 0.037 ✓ | 0.062 ✓ | 0.00292 ✓ |
| autocopist_s19 | 9.000 ✓ | 0.514 ✗ | 0.00645 ✗ | 2.484 ✗ | 0.800 ✗ | 0.0036 ✗ | 0.024 ✗ | 0.014 ✗ |
| autocopist_s7 | 9.000 ✓ | 0.448 ✗ | 0.016 ✓ | 2.358 ✗ | 0.769 ✗ | 0.00332 ✗ | 0.019 ✗ | 0.00884 ✗ |
| ome_s19 | 11.000 ✗ | 0.472 ✗ | 0.00987 ✗ | 2.173 ✗ | 0.774 ✗ | 0.032 ✗ | 0.071 ✗ | 0.00819 ✗ |
| ome_gallows_s19 | 11.000 ✗ | 0.461 ✗ | 0.00955 ✗ | 2.190 ✗ | 0.778 ✗ | 0.031 ✗ | 0.070 ✗ | 0.00824 ✗ |
| ome_s7 | 11.000 ✗ | 0.378 ✗ | 0.015 ✓ | 2.099 ✗ | 0.772 ✗ | 0.029 ✗ | 0.062 ✓ | 0.0055 ✓ |
| ome_gallows_s7 | 11.000 ✗ | 0.366 ✓ | 0.015 ✗ | 2.120 ✗ | 0.777 ✗ | 0.028 ✗ | 0.061 ✓ | 0.00553 ✓ |
| ome_s3 | 11.000 ✗ | 0.387 ✗ | 0.014 ✗ | 2.112 ✗ | 0.773 ✗ | 0.036 ✓ | 0.051 ✗ | 0.00607 ✓ |
| ome_gallows_s3 | 11.000 ✗ | 0.377 ✗ | 0.014 ✗ | 2.134 ✗ | 0.777 ✗ | 0.034 ✓ | 0.050 ✗ | 0.00615 ✓ |

Missed items per generated text (value vs Voynich):

- ome_s19: a_h2_raw 2.435 vs 2.111; a_h3_raw 2.116 vs 1.841; a_h2_mrg 2.739 vs 2.345; a_h3_mrg 2.459 vs 2.114; b_len_sd 2.796 vs 1.788; b_len9 0.150 vs 0.024; c_ttr 0.340 vs 0.202; c_hapax_types 0.749 vs 0.680; c_hapax_tokens 0.255 vs 0.137; d_adj_ld1 0.033 vs 0.042; e_cover 0.555 vs 0.651; e_w10 0.217 vs 0.276; e_prev2 0.335 vs 0.414; e_ratio 1.017 vs 1.140; g_len_last 5.677 vs 4.735; h_peak_log2s 11.000 vs 9.000; h_peak_R 0.472 vs 0.310; i_tok_acc 0.00987 vs 0.024; i_char_bits 2.173 vs 1.873; j_one_page 0.774 vs 0.683; j_jacc_excess 0.032 vs 0.037; k_jsd_halves 0.071 vs 0.062; k_jsd_oddeven 0.00819 vs 0.00292
- ome_gallows_s19: a_h2_raw 2.450 vs 2.111; a_h3_raw 2.131 vs 1.841; a_h2_mrg 2.757 vs 2.345; a_h3_mrg 2.476 vs 2.114; b_len_sd 2.796 vs 1.788; b_len9 0.150 vs 0.024; c_ttr 0.348 vs 0.202; c_hapax_types 0.754 vs 0.680; c_hapax_tokens 0.263 vs 0.137; d_adj_ld1 0.032 vs 0.042; e_cover 0.550 vs 0.651; e_w10 0.213 vs 0.276; e_prev2 0.330 vs 0.414; e_ratio 1.021 vs 1.140; g_len_last 5.677 vs 4.735; g_gal_init 0.345 vs 0.223; h_peak_log2s 11.000 vs 9.000; h_peak_R 0.461 vs 0.310; i_tok_acc 0.00955 vs 0.024; i_char_bits 2.190 vs 1.873; j_one_page 0.778 vs 0.683; j_jacc_excess 0.031 vs 0.037; k_jsd_halves 0.070 vs 0.062; k_jsd_oddeven 0.00824 vs 0.00292
- ome_s7: a_h2_raw 2.337 vs 2.111; a_h3_raw 2.050 vs 1.841; b_len_sd 2.691 vs 1.788; b_len1 0.023 vs 0.032; b_len9 0.132 vs 0.024; c_ttr 0.325 vs 0.202; c_hapax_types 0.751 vs 0.680; c_hapax_tokens 0.244 vs 0.137; c_heaps 0.837 vs 0.732; d_adj_exact 0.00723 vs 0.00841; d_adj_ld1 0.030 vs 0.042; e_cover 0.545 vs 0.651; e_w10 0.200 vs 0.276; e_prev2 0.314 vs 0.414; e_ratio 1.005 vs 1.140; g_len_last 5.754 vs 4.735; g_gal_init 0.058 vs 0.223; h_peak_log2s 11.000 vs 9.000; h_peak_R 0.378 vs 0.310; i_char_bits 2.099 vs 1.873; j_one_page 0.772 vs 0.683; j_jacc_excess 0.029 vs 0.037
- ome_gallows_s7: a_h2_raw 2.359 vs 2.111; a_h3_raw 2.070 vs 1.841; a_h3_mrg 2.343 vs 2.114; b_len_sd 2.690 vs 1.788; b_len1 0.022 vs 0.032; b_len9 0.132 vs 0.024; c_ttr 0.336 vs 0.202; c_hapax_types 0.757 vs 0.680; c_hapax_tokens 0.254 vs 0.137; c_heaps 0.842 vs 0.732; d_adj_exact 0.00683 vs 0.00841; d_adj_ld1 0.029 vs 0.042; e_cover 0.540 vs 0.651; e_w10 0.196 vs 0.276; e_prev2 0.309 vs 0.414; e_ratio 1.007 vs 1.140; g_len_last 5.754 vs 4.735; h_peak_log2s 11.000 vs 9.000; i_tok_acc 0.015 vs 0.024; i_char_bits 2.120 vs 1.873; j_one_page 0.777 vs 0.683; j_jacc_excess 0.028 vs 0.037
- ome_s3: a_h2_raw 2.343 vs 2.111; a_h3_raw 2.063 vs 1.841; a_h3_mrg 2.429 vs 2.114; b_len_sd 2.730 vs 1.788; b_len9 0.138 vs 0.024; c_hapax_types 0.754 vs 0.680; c_hapax_tokens 0.238 vs 0.137; c_heaps 0.850 vs 0.732; d_adj_exact 0.00698 vs 0.00841; d_adj_ld1 0.033 vs 0.042; e_cover 0.563 vs 0.651; e_w10 0.215 vs 0.276; e_prev2 0.330 vs 0.414; e_ratio 0.991 vs 1.140; g_len_last 5.528 vs 4.735; g_gal_init 0.043 vs 0.223; h_peak_log2s 11.000 vs 9.000; h_peak_R 0.387 vs 0.310; i_tok_acc 0.014 vs 0.024; i_char_bits 2.112 vs 1.873; j_one_page 0.773 vs 0.683; k_jsd_halves 0.051 vs 0.062
- ome_gallows_s3: a_h2_raw 2.364 vs 2.111; a_h3_raw 2.083 vs 1.841; a_h2_mrg 2.682 vs 2.345; a_h3_mrg 2.451 vs 2.114; b_len_sd 2.731 vs 1.788; b_len9 0.139 vs 0.024; c_ttr 0.326 vs 0.202; c_hapax_types 0.758 vs 0.680; c_hapax_tokens 0.247 vs 0.137; c_heaps 0.851 vs 0.732; d_adj_exact 0.00663 vs 0.00841; d_adj_ld1 0.032 vs 0.042; e_cover 0.556 vs 0.651; e_w10 0.210 vs 0.276; e_prev2 0.324 vs 0.414; e_ratio 0.988 vs 1.140; g_len_last 5.528 vs 4.735; h_peak_log2s 11.000 vs 9.000; h_peak_R 0.377 vs 0.310; i_tok_acc 0.014 vs 0.024; i_char_bits 2.134 vs 1.873; j_one_page 0.777 vs 0.683; k_jsd_halves 0.050 vs 0.062

Runtime 285 s.
