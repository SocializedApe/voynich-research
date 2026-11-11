# Slot generator v7: borrowed tables x drawn tilts x copying (11 Nov 2026)

Script `slots7.py` (variants in its docstring).

Log-tilt sd by level (lang, hand, section, quire), from Voynich by moments: opener 0.39, 0.19, 0.24, 0.13; middle 0.40, 0.21, 0.24, 0.13; ending 0.83, 0.22, 0.25, 0.18.

| text | matched/37 | held-out/30 | between scribes / within | same scribe other doc / within | JSD A vs B | JSD quire halves in cell | edge X within | edge X across line | Voynich types share | types/token | length sd (chars) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| voynich_ZL | 37 | 30 | 2.96 [2.18-3.59] | 2.00 [1.87-2.15] | 0.101 | 0.052 (4) | 0.0597 | 0.0010 | 1.00 | 0.202 | 1.79 |
| autocopist_s19 | 12 | 11 | | | | | | | | | |
| autocopist_s7 | 15 | 14 | | | | | | | | | |
| prod6e_s19 | 29 | 24 | 1.46 [1.37-1.56] | 1.31 [1.22-1.42] | 0.011 | 0.033 (4) | 0.0432 | -0.0010 | 0.86 | 0.198 | 1.96 |
| prod6e_s7 | 29 | 24 | 1.44 [1.38-1.52] | 1.33 [1.28-1.39] | 0.013 | 0.037 (4) | 0.0408 | 0.0002 | 0.86 | 0.198 | 1.93 |
| prod6e_s3 | 31 | 26 | 1.42 [1.37-1.48] | 1.32 [1.26-1.38] | 0.012 | 0.035 (4) | 0.0403 | 0.0001 | 0.87 | 0.197 | 1.93 |
| prod6e_s11 | 28 | 23 | 1.44 [1.36-1.53] | 1.34 [1.24-1.45] | 0.014 | 0.035 (4) | 0.0424 | 0.0018 | 0.86 | 0.200 | 1.93 |
| prod6e_s23 | 28 | 23 | 1.50 [1.42-1.58] | 1.34 [1.26-1.41] | 0.015 | 0.040 (4) | 0.0409 | -0.0002 | 0.87 | 0.198 | 1.95 |
| tilt7_q0_s19 | 27 | 23 | 1.26 [1.11-1.38] | 1.05 [1.00-1.09] | 0.032 | 0.031 (4) | 0.0314 | 0.0005 | 0.86 | 0.199 | 2.08 |
| tilt7_q0_s7 | 29 | 24 | 1.60 [1.18-1.96] | 1.10 [1.05-1.16] | 0.051 | 0.031 (4) | 0.0394 | 0.0023 | 0.86 | 0.207 | 1.95 |
| tilt7_q0_s3 | 24 | 20 | 1.35 [1.09-1.58] | 1.04 [1.00-1.07] | 0.037 | 0.028 (4) | 0.0332 | 0.0005 | 0.85 | 0.215 | 1.99 |
| tilt7_q0_s11 | 26 | 21 | 1.21 [1.11-1.31] | 1.02 [0.98-1.07] | 0.023 | 0.024 (4) | 0.0490 | -0.0003 | 0.84 | 0.218 | 1.95 |
| tilt7_q0_s23 | 25 | 20 | 1.40 [1.17-1.56] | 1.06 [1.02-1.09] | 0.042 | 0.029 (4) | 0.0408 | 0.0030 | 0.82 | 0.244 | 1.96 |
| tilt7_q10_s19 | 31 | 25 | 1.36 [1.20-1.46] | 1.14 [1.09-1.18] | 0.032 | 0.035 (4) | 0.0249 | 0.0010 | 0.86 | 0.195 | 2.08 |
| tilt7_q10_s7 | 32 | 25 | 1.65 [1.23-2.03] | 1.13 [1.09-1.17] | 0.050 | 0.031 (4) | 0.0327 | 0.0021 | 0.86 | 0.203 | 1.94 |
| tilt7_q10_s3 | 28 | 24 | 1.44 [1.16-1.70] | 1.10 [1.05-1.16] | 0.036 | 0.030 (4) | 0.0258 | -0.0016 | 0.85 | 0.213 | 1.99 |
| tilt7_q10_s11 | 27 | 22 | 1.30 [1.19-1.39] | 1.12 [1.08-1.15] | 0.022 | 0.024 (4) | 0.0370 | -0.0009 | 0.84 | 0.217 | 1.95 |
| tilt7_q10_s23 | 25 | 20 | 1.52 [1.28-1.69] | 1.15 [1.11-1.20] | 0.043 | 0.032 (4) | 0.0327 | -0.0000 | 0.81 | 0.243 | 1.94 |
| tilt7_q20_s19 | 30 | 25 | 1.45 [1.31-1.60] | 1.23 [1.16-1.31] | 0.032 | 0.037 (4) | 0.0202 | -0.0019 | 0.86 | 0.193 | 2.08 |
| tilt7_q20_s7 | 32 | 26 | 1.74 [1.28-2.17] | 1.20 [1.15-1.24] | 0.054 | 0.035 (4) | 0.0263 | 0.0035 | 0.86 | 0.199 | 1.96 |
| tilt7_q20_s3 | 29 | 24 | 1.57 [1.28-1.84] | 1.22 [1.18-1.26] | 0.039 | 0.032 (4) | 0.0200 | 0.0024 | 0.84 | 0.211 | 1.99 |
| tilt7_q20_s11 | 30 | 24 | 1.43 [1.30-1.56] | 1.22 [1.17-1.27] | 0.024 | 0.027 (4) | 0.0296 | 0.0026 | 0.84 | 0.213 | 1.95 |
| tilt7_q20_s23 | 25 | 19 | 1.56 [1.32-1.73] | 1.21 [1.17-1.26] | 0.043 | 0.036 (4) | 0.0251 | -0.0006 | 0.81 | 0.239 | 1.95 |
| notilt7_q10_s19 | 26 | 21 | 1.08 [1.04-1.11] | 1.08 [1.05-1.11] | 0.003 | 0.021 (4) | 0.0308 | 0.0006 | 0.85 | 0.221 | 1.96 |
| notilt7_q10_s7 | 26 | 21 | 1.08 [1.05-1.12] | 1.08 [1.05-1.12] | 0.003 | 0.019 (4) | 0.0325 | -0.0019 | 0.85 | 0.220 | 1.94 |
| notilt7_q10_s3 | 26 | 21 | 1.05 [1.02-1.10] | 1.05 [1.01-1.10] | 0.003 | 0.020 (4) | 0.0319 | 0.0019 | 0.85 | 0.217 | 1.93 |
| notilt7_q10_s11 | 26 | 21 | 1.08 [1.04-1.11] | 1.07 [1.04-1.12] | 0.003 | 0.019 (4) | 0.0311 | 0.0005 | 0.85 | 0.218 | 1.94 |
| notilt7_q10_s23 | 26 | 21 | 1.05 [1.01-1.08] | 1.04 [1.00-1.10] | 0.003 | 0.020 (4) | 0.0304 | 0.0011 | 0.85 | 0.219 | 1.94 |

Missed items per generated text (value vs Voynich):

- tilt7_q0_s19: b_len_sd 2.079 vs 1.788; b_len1 0.060 vs 0.032; d_adj_exact 0.00611 vs 0.00841; d_adj_ld1 0.028 vs 0.042; e_w10 0.208 vs 0.276; e_ratio 0.996 vs 1.140; h_peak_log2s 11.000 vs 9.000; h_peak_R 0.090 vs 0.310; j_jacc_excess 0.016 vs 0.037; k_jsd_halves 0.014 vs 0.062
- tilt7_q0_s7: d_adj_exact 0.00514 vs 0.00841; d_adj_ld1 0.025 vs 0.042; e_w10 0.204 vs 0.276; e_ratio 0.998 vs 1.140; h_peak_log2s 11.000 vs 9.000; h_peak_R 0.088 vs 0.310; j_jacc_excess 0.016 vs 0.037; k_jsd_halves 0.018 vs 0.062
- tilt7_q0_s3: b_len_sd 1.988 vs 1.788; b_len1 0.040 vs 0.032; d_adj_exact 0.00451 vs 0.00841; d_adj_ld1 0.024 vs 0.042; e_cover 0.574 vs 0.651; e_w10 0.187 vs 0.276; e_prev2 0.316 vs 0.414; e_ratio 0.995 vs 1.140; h_peak_log2s 11.000 vs 9.000; h_peak_R 0.097 vs 0.310; i_tok_acc 0.012 vs 0.024; j_jacc_excess 0.020 vs 0.037; k_jsd_halves 0.016 vs 0.062
- tilt7_q0_s11: d_adj_exact 0.00399 vs 0.00841; d_adj_ld1 0.023 vs 0.042; e_cover 0.572 vs 0.651; e_w10 0.179 vs 0.276; e_prev2 0.305 vs 0.414; e_w10_shuf 0.173 vs 0.242; h_peak_log2s 11.000 vs 9.000; h_peak_R 0.079 vs 0.310; i_tok_acc 0.013 vs 0.024; j_jacc_excess 0.015 vs 0.037; k_jsd_halves 0.00994 vs 0.062
- tilt7_q0_s23: d_adj_exact 0.00382 vs 0.00841; d_adj_ld1 0.019 vs 0.042; e_cover 0.534 vs 0.651; e_w10 0.152 vs 0.276; e_prev2 0.267 vs 0.414; e_w10_shuf 0.151 vs 0.242; e_ratio 1.006 vs 1.140; h_peak_log2s 11.000 vs 9.000; h_peak_R 0.117 vs 0.310; i_tok_acc 0.00964 vs 0.024; j_jacc_excess 0.020 vs 0.037; k_jsd_halves 0.016 vs 0.062
- tilt7_q10_s19: b_len_sd 2.080 vs 1.788; b_len1 0.060 vs 0.032; d_adj_ld1 0.034 vs 0.042; h_peak_R 0.110 vs 0.310; j_jacc_excess 0.021 vs 0.037; k_jsd_halves 0.014 vs 0.062
- tilt7_q10_s7: d_adj_ld1 0.031 vs 0.042; h_peak_log2s 10.000 vs 9.000; h_peak_R 0.103 vs 0.310; j_jacc_excess 0.019 vs 0.037; k_jsd_halves 0.018 vs 0.062
- tilt7_q10_s3: b_len_sd 1.986 vs 1.788; b_len1 0.040 vs 0.032; d_adj_exact 0.00749 vs 0.00841; d_adj_ld1 0.029 vs 0.042; e_w10 0.223 vs 0.276; h_peak_R 0.121 vs 0.310; i_tok_acc 0.012 vs 0.024; j_jacc_excess 0.018 vs 0.037; k_jsd_halves 0.016 vs 0.062
- tilt7_q10_s11: d_adj_exact 0.00632 vs 0.00841; d_adj_ld1 0.027 vs 0.042; e_w10 0.210 vs 0.276; e_prev2 0.331 vs 0.414; e_w10_shuf 0.180 vs 0.242; h_peak_log2s 11.000 vs 9.000; h_peak_R 0.083 vs 0.310; i_tok_acc 0.013 vs 0.024; j_jacc_excess 0.013 vs 0.037; k_jsd_halves 0.010 vs 0.062
- tilt7_q10_s23: b_len1 0.025 vs 0.032; d_adj_exact 0.00594 vs 0.00841; d_adj_ld1 0.024 vs 0.042; e_cover 0.546 vs 0.651; e_w10 0.180 vs 0.276; e_prev2 0.288 vs 0.414; e_w10_shuf 0.154 vs 0.242; h_peak_log2s 11.000 vs 9.000; h_peak_R 0.138 vs 0.310; i_tok_acc 0.00959 vs 0.024; j_jacc_excess 0.022 vs 0.037; k_jsd_halves 0.017 vs 0.062
- tilt7_q20_s19: b_len_sd 2.081 vs 1.788; b_len1 0.059 vs 0.032; d_adj_exact 0.012 vs 0.00841; e_ratio 1.260 vs 1.140; h_peak_R 0.147 vs 0.310; j_jacc_excess 0.015 vs 0.037; k_jsd_halves 0.014 vs 0.062
- tilt7_q20_s7: d_adj_exact 0.00965 vs 0.00841; d_adj_ld1 0.035 vs 0.042; h_peak_R 0.133 vs 0.310; j_jacc_excess 0.017 vs 0.037; k_jsd_halves 0.019 vs 0.062
- tilt7_q20_s3: b_len_sd 1.992 vs 1.788; b_len1 0.039 vs 0.032; d_adj_exact 0.010 vs 0.00841; e_ratio 1.333 vs 1.140; h_peak_R 0.163 vs 0.310; i_tok_acc 0.012 vs 0.024; j_jacc_excess 0.019 vs 0.037; k_jsd_halves 0.018 vs 0.062
- tilt7_q20_s11: d_adj_exact 0.00723 vs 0.00841; d_adj_ld1 0.031 vs 0.042; e_ratio 1.313 vs 1.140; h_peak_R 0.113 vs 0.310; i_tok_acc 0.012 vs 0.024; j_jacc_excess 0.015 vs 0.037; k_jsd_halves 0.011 vs 0.062
- tilt7_q20_s23: b_len1 0.025 vs 0.032; d_adj_ld1 0.028 vs 0.042; e_cover 0.564 vs 0.651; e_w10 0.219 vs 0.276; e_prev2 0.322 vs 0.414; e_w10_shuf 0.156 vs 0.242; e_ratio 1.403 vs 1.140; h_peak_log2s 10.000 vs 9.000; h_peak_R 0.162 vs 0.310; i_tok_acc 0.00973 vs 0.024; j_jacc_excess 0.016 vs 0.037; k_jsd_halves 0.018 vs 0.062
- notilt7_q10_s19: d_adj_exact 0.00471 vs 0.00841; d_adj_ld1 0.023 vs 0.042; e_cover 0.565 vs 0.651; e_w10 0.189 vs 0.276; e_prev2 0.304 vs 0.414; e_w10_shuf 0.156 vs 0.242; h_peak_log2s 7.000 vs 9.000; h_peak_R 0.033 vs 0.310; i_tok_acc 0.013 vs 0.024; j_jacc_excess 0.00594 vs 0.037; k_jsd_halves 0.00352 vs 0.062
- notilt7_q10_s7: d_adj_exact 0.00517 vs 0.00841; d_adj_ld1 0.022 vs 0.042; e_cover 0.568 vs 0.651; e_w10 0.187 vs 0.276; e_prev2 0.303 vs 0.414; e_w10_shuf 0.157 vs 0.242; h_peak_log2s 8.000 vs 9.000; h_peak_R 0.029 vs 0.310; i_tok_acc 0.013 vs 0.024; j_jacc_excess 0.0043 vs 0.037; k_jsd_halves 0.00332 vs 0.062
- notilt7_q10_s3: d_adj_exact 0.00557 vs 0.00841; d_adj_ld1 0.024 vs 0.042; e_cover 0.570 vs 0.651; e_w10 0.192 vs 0.276; e_prev2 0.307 vs 0.414; e_w10_shuf 0.161 vs 0.242; h_peak_log2s 7.000 vs 9.000; h_peak_R 0.028 vs 0.310; i_tok_acc 0.012 vs 0.024; j_jacc_excess 0.00554 vs 0.037; k_jsd_halves 0.00362 vs 0.062
- notilt7_q10_s11: d_adj_exact 0.0058 vs 0.00841; d_adj_ld1 0.024 vs 0.042; e_cover 0.567 vs 0.651; e_w10 0.191 vs 0.276; e_prev2 0.305 vs 0.414; e_w10_shuf 0.163 vs 0.242; h_peak_log2s 6.000 vs 9.000; h_peak_R 0.032 vs 0.310; i_tok_acc 0.014 vs 0.024; j_jacc_excess 0.00621 vs 0.037; k_jsd_halves 0.00353 vs 0.062
- notilt7_q10_s23: d_adj_exact 0.0054 vs 0.00841; d_adj_ld1 0.024 vs 0.042; e_cover 0.568 vs 0.651; e_w10 0.188 vs 0.276; e_prev2 0.303 vs 0.414; e_w10_shuf 0.160 vs 0.242; h_peak_log2s 7.000 vs 9.000; h_peak_R 0.033 vs 0.310; i_tok_acc 0.012 vs 0.024; j_jacc_excess 0.00874 vs 0.037; k_jsd_halves 0.00326 vs 0.062

Runtime 10 s.
