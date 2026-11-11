# Slot generator v6: transition rule x context-free location habit, with a length budget (10 Nov 2026)

Script `slots6.py` (variants in its docstring).
Exponents (a context, b location) from product.py dev pages: opener 1.0, 0.75, middle 1.0, 0.75, ending 1.0, 0.75.

- opener ctx: d 0.54, 0.67; passed up book 0.17, context 0.13
- opener loc: d 0.62, 0.75, 0.86, 0.80, 0.80, 0.85, 0.96; passed up book 0.41, lang 0.52, hand 0.68, section 0.55, quire 0.43, page 0.70, line 0.97
- opener tree: d 0.51, 0.86, 0.89, 0.91, 0.89, 0.88, 0.92, 0.95; passed up book 0.18, context 0.56, lang 0.70, hand 0.80, section 0.77, quire 0.70, page 0.87, line 0.98
- middle loc: d 1.00, 0.99, 0.99, 0.98, 0.97, 0.95, 0.99; passed up book 0.99, lang 0.97, hand 0.97, section 0.94, quire 0.84, page 0.86, line 0.99
- middle tree: d 0.99, 0.92, 0.95, 0.98, 0.97, 0.95, 0.96, 0.98; passed up book 0.98, context 0.71, lang 0.80, hand 0.91, section 0.89, quire 0.82, page 0.94, line 0.99
- ending ctx: d 0.58, 0.46; passed up book 0.12, context 0.10
- ending loc: d 0.44, 0.56, 0.71, 0.73, 0.68, 0.84, 0.97; passed up book 0.28, lang 0.41, hand 0.45, section 0.48, quire 0.35, page 0.69, line 0.98
- ending tree: d 0.37, 0.66, 0.81, 0.90, 0.88, 0.89, 0.91, 0.95; passed up book 0.10, context 0.35, lang 0.60, hand 0.81, section 0.81, quire 0.82, page 0.92, line 0.99

Match rule as b3; held-out = the 30 items outside hybrid_model.TUNED_B3.

| text | matched/37 | held-out/30 | between scribes / within | same scribe other doc / within | JSD A vs B | JSD quire halves in cell | edge X within | edge X across line | Voynich types share | types/token | length sd (chars) | 9+ chars |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| voynich_ZL | 37 | 30 | 2.96 [2.18-3.59] | 2.00 [1.87-2.15] | 0.101 | 0.052 (4) | 0.0597 | 0.0010 | 1.00 | 0.202 | 1.79 | 0.024 |
| autocopist_s19 | 12 | 11 | | | | | | | | | | |
| autocopist_s7 | 15 | 14 | | | | | | | | | | |
| len5_s19 | 24 | 21 | 1.41 [1.34-1.49] | 1.19 [1.15-1.24] | 0.028 | 0.038 (4) | 0.1292 | 0.0006 | 0.57 | 0.182 | 2.59 | 0.121 |
| len5_s7 | 28 | 24 | 1.54 [1.46-1.63] | 1.28 [1.20-1.36] | 0.026 | 0.041 (4) | 0.0582 | 0.0004 | 0.57 | 0.153 | 2.73 | 0.097 |
| len5_s3 | 26 | 22 | 1.91 [1.66-2.11] | 1.36 [1.28-1.46] | 0.041 | 0.049 (4) | 0.0495 | 0.0012 | 0.59 | 0.152 | 2.97 | 0.134 |
| len5_s11 | 24 | 21 | 1.89 [1.55-2.18] | 1.34 [1.29-1.41] | 0.059 | 0.040 (4) | 0.0313 | 0.0011 | 0.51 | 0.141 | 2.53 | 0.086 |
| len5_s23 | 25 | 21 | 1.79 [1.66-2.01] | 1.31 [1.26-1.37] | 0.046 | 0.045 (4) | 0.0336 | 0.0004 | 0.55 | 0.183 | 2.71 | 0.130 |
| prod6_s19 | 3 | 3 | 2.43 [1.93-2.87] | 1.74 [1.52-2.02] | 0.030 | 0.019 (4) | 0.0729 | 0.0000 | 0.00 | 0.023 | 2.82 | 0.288 |
| prod6_s7 | 8 | 8 | 2.62 [2.23-3.03] | 1.87 [1.46-2.48] | 0.038 | 0.036 (4) | 0.0000 | 0.0000 | 0.63 | 0.024 | 2.04 | 0.045 |
| prod6g_s19 | 29 | 25 | 1.45 [1.37-1.54] | 1.29 [1.21-1.37] | 0.018 | 0.034 (4) | 0.0010 | 0.0006 | 0.66 | 0.168 | 2.62 | 0.111 |
| prod6g_s7 | 21 | 17 | 1.46 [1.33-1.60] | 1.25 [1.18-1.34] | 0.029 | 0.028 (4) | 0.0018 | -0.0007 | 0.54 | 0.150 | 2.58 | 0.160 |
| prod6g_s3 | 22 | 19 | 1.39 [1.32-1.50] | 1.26 [1.20-1.33] | 0.015 | 0.041 (4) | 0.0034 | -0.0001 | 0.55 | 0.188 | 2.70 | 0.139 |
| prod6g_s11 | 23 | 20 | 1.27 [1.20-1.34] | 1.15 [1.10-1.21] | 0.021 | 0.032 (4) | 0.0019 | -0.0002 | 0.72 | 0.148 | 2.52 | 0.056 |
| prod6g_s23 | 24 | 20 | 1.32 [1.24-1.40] | 1.23 [1.12-1.34] | 0.013 | 0.032 (4) | 0.0020 | 0.0017 | 0.65 | 0.187 | 2.66 | 0.116 |
| prod6t_s19 | 30 | 25 | 1.49 [1.40-1.57] | 1.29 [1.17-1.41] | 0.012 | 0.037 (4) | 0.0379 | 0.0003 | 0.86 | 0.201 | 1.92 | 0.035 |
| prod6t_s7 | 29 | 24 | 1.44 [1.38-1.49] | 1.31 [1.26-1.36] | 0.010 | 0.033 (4) | 0.0384 | 0.0004 | 0.87 | 0.187 | 1.94 | 0.033 |
| prod6t_s3 | 28 | 23 | 1.49 [1.43-1.56] | 1.35 [1.28-1.43] | 0.012 | 0.039 (4) | 0.0406 | 0.0006 | 0.87 | 0.187 | 1.93 | 0.033 |
| prod6t_s11 | 30 | 25 | 1.48 [1.36-1.69] | 1.34 [1.24-1.45] | 0.020 | 0.041 (4) | 0.0371 | -0.0006 | 0.87 | 0.197 | 1.93 | 0.033 |
| prod6t_s23 | 30 | 25 | 1.43 [1.38-1.49] | 1.31 [1.25-1.38] | 0.012 | 0.034 (4) | 0.0412 | 0.0006 | 0.86 | 0.197 | 1.95 | 0.035 |
| prod6e_s19 | 29 | 24 | 1.46 [1.37-1.56] | 1.31 [1.22-1.42] | 0.011 | 0.033 (4) | 0.0432 | -0.0010 | 0.86 | 0.198 | 1.96 | 0.036 |
| prod6e_s7 | 29 | 24 | 1.44 [1.38-1.52] | 1.33 [1.28-1.39] | 0.013 | 0.037 (4) | 0.0408 | 0.0002 | 0.86 | 0.198 | 1.93 | 0.035 |
| prod6e_s3 | 31 | 26 | 1.42 [1.37-1.48] | 1.32 [1.26-1.38] | 0.012 | 0.035 (4) | 0.0403 | 0.0001 | 0.87 | 0.197 | 1.93 | 0.037 |
| prod6e_s11 | 28 | 23 | 1.44 [1.36-1.53] | 1.34 [1.24-1.45] | 0.014 | 0.035 (4) | 0.0424 | 0.0018 | 0.86 | 0.200 | 1.93 | 0.035 |
| prod6e_s23 | 28 | 23 | 1.50 [1.42-1.58] | 1.34 [1.26-1.41] | 0.015 | 0.040 (4) | 0.0409 | -0.0002 | 0.87 | 0.198 | 1.95 | 0.036 |

Realised share passed up (seed 19) against the fit:
- len5 opener tree: book 0.21 (fit 0.18), context 0.50 (fit 0.56), lang 0.61 (fit 0.70), hand 0.74 (fit 0.80), section 0.69 (fit 0.77), quire 0.69 (fit 0.70), page 0.86 (fit 0.87), line 0.99 (fit 0.98)
- len5 middle tree: book 0.96 (fit 0.98), context 0.70 (fit 0.71), lang 0.80 (fit 0.80), hand 0.92 (fit 0.91), section 0.90 (fit 0.89), quire 0.83 (fit 0.82), page 0.93 (fit 0.94), line 0.99 (fit 0.99)
- len5 ending tree: book 0.08 (fit 0.10), context 0.35 (fit 0.35), lang 0.61 (fit 0.60), hand 0.78 (fit 0.81), section 0.80 (fit 0.81), quire 0.81 (fit 0.82), page 0.93 (fit 0.92), line 1.00 (fit 0.99)
- prod6 opener loc: book 0.08 (fit 0.41), lang 0.13 (fit 0.52), hand 0.32 (fit 0.68), section 0.36 (fit 0.55), quire 0.38 (fit 0.43), page 0.63 (fit 0.70), line 0.97 (fit 0.97)
- prod6 opener ctx: book 0.07 (fit 0.17), context 0.00 (fit 0.13)
- prod6 middle tree: book 0.93 (fit 0.98), context 0.46 (fit 0.71), lang 0.74 (fit 0.80), hand 0.89 (fit 0.91), section 0.82 (fit 0.89), quire 0.79 (fit 0.82), page 0.85 (fit 0.94), line 0.98 (fit 0.99)
- prod6 ending loc: book 0.11 (fit 0.28), lang 0.22 (fit 0.41), hand 0.35 (fit 0.45), section 0.39 (fit 0.48), quire 0.30 (fit 0.35), page 0.63 (fit 0.69), line 0.98 (fit 0.98)
- prod6 ending ctx: book 0.01 (fit 0.12), context 0.06 (fit 0.10)
- prod6g opener loc: book 0.38 (fit 0.41), lang 0.48 (fit 0.52), hand 0.60 (fit 0.68), section 0.47 (fit 0.55), quire 0.48 (fit 0.43), page 0.66 (fit 0.70), line 0.97 (fit 0.97)
- prod6g opener ctx: book 0.15 (fit 0.17), context 0.13 (fit 0.13)
- prod6g middle tree: book 0.93 (fit 0.98), context 0.70 (fit 0.71), lang 0.79 (fit 0.80), hand 0.93 (fit 0.91), section 0.84 (fit 0.89), quire 0.81 (fit 0.82), page 0.90 (fit 0.94), line 0.99 (fit 0.99)
- prod6g ending loc: book 0.30 (fit 0.28), lang 0.38 (fit 0.41), hand 0.43 (fit 0.45), section 0.48 (fit 0.48), quire 0.34 (fit 0.35), page 0.69 (fit 0.69), line 0.98 (fit 0.98)
- prod6g ending ctx: book 0.11 (fit 0.12), context 0.13 (fit 0.10)
- prod6t opener loc: book 0.38 (fit 0.41), lang 0.47 (fit 0.52), hand 0.62 (fit 0.68), section 0.52 (fit 0.55), quire 0.47 (fit 0.43), page 0.69 (fit 0.70), line 0.97 (fit 0.97)
- prod6t middle loc: book 0.99 (fit 0.99), hand 0.96 (fit 0.97), section 0.94 (fit 0.94), quire 0.88 (fit 0.84), page 0.90 (fit 0.86)
- prod6t ending loc: book 0.35 (fit 0.28), lang 0.38 (fit 0.41), hand 0.46 (fit 0.45), section 0.48 (fit 0.48), quire 0.33 (fit 0.35), page 0.68 (fit 0.69), line 0.98 (fit 0.98)
- prod6e opener loc: book 0.29 (fit 0.41), lang 0.50 (fit 0.52), hand 0.64 (fit 0.68), section 0.51 (fit 0.55), quire 0.48 (fit 0.43), page 0.68 (fit 0.70), line 0.97 (fit 0.97)
- prod6e middle loc: book 0.98 (fit 0.99), hand 0.95 (fit 0.97), section 0.95 (fit 0.94), quire 0.84 (fit 0.84), page 0.89 (fit 0.86)
- prod6e ending loc: book 0.28 (fit 0.28), lang 0.42 (fit 0.41), hand 0.44 (fit 0.45), section 0.47 (fit 0.48), quire 0.34 (fit 0.35), page 0.69 (fit 0.69), line 0.98 (fit 0.98)

Missed items per generated text (value vs Voynich):

- len5_s19: b_len_sd 2.590 vs 1.788; b_len1 0.043 vs 0.032; b_len9 0.121 vs 0.024; d_adj_exact 0.013 vs 0.00841; d_adj_ld1 0.032 vs 0.042; e_cover 0.577 vs 0.651; e_w10 0.205 vs 0.276; e_prev2 0.326 vs 0.414; g_len_last 5.635 vs 4.735; g_gal_init 0.139 vs 0.223; h_peak_log2s 11.000 vs 9.000; j_jacc_excess 0.041 vs 0.037; k_jsd_halves 0.014 vs 0.062
- len5_s7: b_len_sd 2.732 vs 1.788; b_len1 0.152 vs 0.032; b_len9 0.097 vs 0.024; d_adj_exact 0.019 vs 0.00841; e_ratio 1.014 vs 1.140; g_gal_init 0.060 vs 0.223; h_peak_log2s 10.000 vs 9.000; i_tok_acc 0.073 vs 0.024; k_jsd_halves 0.014 vs 0.062
- len5_s3: b_len_sd 2.974 vs 1.788; b_len1 0.165 vs 0.032; b_len9 0.134 vs 0.024; d_adj_exact 0.035 vs 0.00841; d_adj_ld1 0.056 vs 0.042; e_ratio 1.005 vs 1.140; g_gal_init 0.115 vs 0.223; h_peak_log2s 10.000 vs 9.000; h_peak_R 0.384 vs 0.310; i_tok_acc 0.118 vs 0.024; k_jsd_halves 0.028 vs 0.062
- len5_s11: b_len_sd 2.528 vs 1.788; b_len1 0.094 vs 0.032; b_len9 0.086 vs 0.024; d_adj_exact 0.055 vs 0.00841; d_adj_ld1 0.079 vs 0.042; e_w10 0.356 vs 0.276; e_w10_shuf 0.358 vs 0.242; e_ratio 0.995 vs 1.140; g_len_first 4.592 vs 5.429; g_gal_init 0.100 vs 0.223; i_tok_acc 0.143 vs 0.024; j_jacc_excess 0.044 vs 0.037; k_jsd_halves 0.030 vs 0.062
- len5_s23: b_len_sd 2.707 vs 1.788; b_len1 0.018 vs 0.032; b_len9 0.130 vs 0.024; d_adj_exact 0.021 vs 0.00841; d_adj_ld1 0.036 vs 0.042; e_cover 0.561 vs 0.651; e_w10 0.214 vs 0.276; e_prev2 0.324 vs 0.414; e_ratio 1.008 vs 1.140; h_peak_log2s 10.000 vs 9.000; i_tok_acc 0.066 vs 0.024; k_jsd_halves 0.024 vs 0.062
- prod6_s19: a_h1_raw 3.331 vs 3.870; a_h2_raw 1.019 vs 2.111; a_h3_raw 0.721 vs 1.841; a_h2_mrg 1.027 vs 2.345; a_h3_mrg 0.739 vs 2.114; b_len_mean 6.160 vs 4.990; b_len_sd 2.824 vs 1.788; b_len1 0 vs 0.032; b_len9 0.288 vs 0.024; c_zipf -1.450 vs -1.041; c_ttr 0.023 vs 0.202; c_hapax_types 0.499 vs 0.680; c_hapax_tokens 0.011 vs 0.137; c_heaps 0.556 vs 0.732; d_adj_exact 0.205 vs 0.00841; d_adj_ld1 0.240 vs 0.042; e_cover 0.900 vs 0.651; e_w10 0.755 vs 0.276; e_prev2 0.827 vs 0.414; e_w10_shuf 0.754 vs 0.242; e_ratio 1.001 vs 1.140; f_irrev 0.295 vs 0.095; f_lock 1.000 vs 0.643; g_len_first 6.248 vs 5.429; g_len_mid 6.136 vs 4.957; g_len_last 6.228 vs 4.735; g_gal_init 1.000 vs 0.223; g_gal_mid 1.000 vs 0.063; h_peak_log2s 8.000 vs 9.000; i_tok_acc 0.297 vs 0.024; i_char_bits 0.742 vs 1.873; j_one_page 0.553 vs 0.683; j_jacc_excess 0.073 vs 0.037; k_jsd_halves 0.017 vs 0.062
- prod6_s7: a_h1_raw 3.095 vs 3.870; a_h2_raw 0.953 vs 2.111; a_h3_raw 0.806 vs 1.841; a_h2_mrg 0.985 vs 2.345; a_h3_mrg 0.837 vs 2.114; b_len_sd 2.039 vs 1.788; b_len1 0 vs 0.032; c_zipf -1.442 vs -1.041; c_ttr 0.024 vs 0.202; c_hapax_types 0.540 vs 0.680; c_hapax_tokens 0.013 vs 0.137; c_heaps 0.562 vs 0.732; d_adj_exact 0.258 vs 0.00841; d_adj_ld1 0.325 vs 0.042; e_cover 0.913 vs 0.651; e_w10 0.785 vs 0.276; e_prev2 0.851 vs 0.414; e_w10_shuf 0.781 vs 0.242; e_ratio 1.005 vs 1.140; f_irrev 0.265 vs 0.095; f_lock 1.000 vs 0.643; g_gal_init 0.999 vs 0.223; g_gal_mid 1.000 vs 0.063; h_peak_log2s 8.000 vs 9.000; i_tok_acc 0.444 vs 0.024; i_char_bits 0.827 vs 1.873; j_one_page 0.569 vs 0.683; j_jacc_excess 0.076 vs 0.037; k_jsd_halves 0.030 vs 0.062
- prod6g_s19: b_len_sd 2.617 vs 1.788; b_len1 0.056 vs 0.032; b_len9 0.111 vs 0.024; d_adj_exact 0.011 vs 0.00841; g_gal_init 0.022 vs 0.223; h_peak_R 0.203 vs 0.310; j_jacc_excess 0.027 vs 0.037; k_jsd_halves 0.012 vs 0.062
- prod6g_s7: a_h3_mrg 1.882 vs 2.114; b_len_sd 2.575 vs 1.788; b_len1 0.00255 vs 0.032; b_len9 0.160 vs 0.024; d_adj_exact 0.012 vs 0.00841; d_adj_ld1 0.052 vs 0.042; e_w10_shuf 0.310 vs 0.242; e_ratio 1.017 vs 1.140; f_lock 0.748 vs 0.643; g_len_last 5.560 vs 4.735; g_gal_init 0.067 vs 0.223; h_peak_log2s 11.000 vs 9.000; h_peak_R 0.146 vs 0.310; i_tok_acc 0.038 vs 0.024; j_jacc_excess 0.031 vs 0.037; k_jsd_halves 0.017 vs 0.062
- prod6g_s3: b_len_sd 2.701 vs 1.788; b_len1 0.047 vs 0.032; b_len9 0.139 vs 0.024; d_adj_exact 0.00927 vs 0.00841; d_adj_ld1 0.029 vs 0.042; e_cover 0.575 vs 0.651; e_w10 0.210 vs 0.276; e_prev2 0.333 vs 0.414; e_ratio 1.022 vs 1.140; g_len_last 5.545 vs 4.735; g_gal_init 0.016 vs 0.223; h_peak_log2s 11.000 vs 9.000; h_peak_R 0.172 vs 0.310; j_jacc_excess 0.022 vs 0.037; k_jsd_halves 0.012 vs 0.062
- prod6g_s11: b_len_sd 2.517 vs 1.788; b_len1 0.130 vs 0.032; d_adj_exact 0.018 vs 0.00841; d_adj_ld1 0.066 vs 0.042; e_w10 0.350 vs 0.276; e_w10_shuf 0.347 vs 0.242; e_ratio 1.009 vs 1.140; g_len_first 4.257 vs 5.429; g_gal_init 0.030 vs 0.223; h_peak_log2s 11.000 vs 9.000; h_peak_R 0.133 vs 0.310; i_tok_acc 0.061 vs 0.024; j_jacc_excess 0.022 vs 0.037; k_jsd_halves 0.013 vs 0.062
- prod6g_s23: b_len_sd 2.658 vs 1.788; b_len1 0.040 vs 0.032; b_len9 0.116 vs 0.024; d_adj_ld1 0.026 vs 0.042; e_cover 0.566 vs 0.651; e_w10 0.196 vs 0.276; e_prev2 0.316 vs 0.414; e_ratio 1.011 vs 1.140; g_gal_init 0.029 vs 0.223; h_peak_log2s 11.000 vs 9.000; h_peak_R 0.157 vs 0.310; j_jacc_excess 0.022 vs 0.037; k_jsd_halves 0.00869 vs 0.062
- prod6t_s19: d_adj_exact 0.00623 vs 0.00841; d_adj_ld1 0.027 vs 0.042; e_w10 0.207 vs 0.276; e_ratio 1.006 vs 1.140; h_peak_R 0.107 vs 0.310; j_jacc_excess 0.015 vs 0.037; k_jsd_halves 0.00772 vs 0.062
- prod6t_s7: d_adj_exact 0.00643 vs 0.00841; d_adj_ld1 0.028 vs 0.042; e_w10 0.216 vs 0.276; e_ratio 1.024 vs 1.140; h_peak_log2s 8.000 vs 9.000; h_peak_R 0.105 vs 0.310; j_jacc_excess 0.016 vs 0.037; k_jsd_halves 0.00769 vs 0.062
- prod6t_s3: d_adj_exact 0.00649 vs 0.00841; d_adj_ld1 0.029 vs 0.042; e_w10 0.213 vs 0.276; e_ratio 1.018 vs 1.140; h_peak_log2s 8.000 vs 9.000; h_peak_R 0.110 vs 0.310; i_tok_acc 0.015 vs 0.024; j_jacc_excess 0.018 vs 0.037; k_jsd_halves 0.00953 vs 0.062
- prod6t_s11: d_adj_exact 0.00678 vs 0.00841; d_adj_ld1 0.029 vs 0.042; e_w10 0.214 vs 0.276; e_ratio 1.019 vs 1.140; h_peak_R 0.117 vs 0.310; j_jacc_excess 0.020 vs 0.037; k_jsd_halves 0.012 vs 0.062
- prod6t_s23: d_adj_exact 0.00646 vs 0.00841; d_adj_ld1 0.027 vs 0.042; e_w10 0.202 vs 0.276; h_peak_R 0.106 vs 0.310; i_tok_acc 0.014 vs 0.024; j_jacc_excess 0.015 vs 0.037; k_jsd_halves 0.0096 vs 0.062
- prod6e_s19: d_adj_exact 0.00629 vs 0.00841; d_adj_ld1 0.028 vs 0.042; e_w10 0.203 vs 0.276; e_ratio 1.024 vs 1.140; h_peak_R 0.088 vs 0.310; i_tok_acc 0.013 vs 0.024; j_jacc_excess 0.00964 vs 0.037; k_jsd_halves 0.012 vs 0.062
- prod6e_s7: d_adj_exact 0.00568 vs 0.00841; d_adj_ld1 0.025 vs 0.042; e_w10 0.197 vs 0.276; e_prev2 0.332 vs 0.414; h_peak_R 0.109 vs 0.310; i_tok_acc 0.012 vs 0.024; j_jacc_excess 0.014 vs 0.037; k_jsd_halves 0.00832 vs 0.062
- prod6e_s3: d_adj_exact 0.00594 vs 0.00841; d_adj_ld1 0.027 vs 0.042; e_w10 0.205 vs 0.276; h_peak_R 0.117 vs 0.310; j_jacc_excess 0.021 vs 0.037; k_jsd_halves 0.00944 vs 0.062
- prod6e_s11: d_adj_exact 0.00571 vs 0.00841; d_adj_ld1 0.027 vs 0.042; e_w10 0.196 vs 0.276; e_prev2 0.331 vs 0.414; e_ratio 1.018 vs 1.140; h_peak_R 0.107 vs 0.310; i_tok_acc 0.013 vs 0.024; j_jacc_excess 0.018 vs 0.037; k_jsd_halves 0.00975 vs 0.062
- prod6e_s23: d_adj_exact 0.00637 vs 0.00841; d_adj_ld1 0.028 vs 0.042; e_w10 0.199 vs 0.276; e_prev2 0.333 vs 0.414; e_ratio 1.015 vs 1.140; h_peak_R 0.115 vs 0.310; i_tok_acc 0.013 vs 0.024; j_jacc_excess 0.018 vs 0.037; k_jsd_halves 0.00989 vs 0.062

Runtime 17 s.
