# controls2: checks 1-3 (29 Oct 2026): more languages, Arabic-manual ciphers, syllable ciphers

Script `controls2/run_controls.py`; design and match rule in its docstring (fixed before any score).

| corpus | check | b3 matches /37 | h2 with space | h2 no space | a_h2_raw | b_len_mean | b_len_sd | c_zipf | c_ttr | c_hapax_types | d_adj_exact | e_w10 | f_irrev | f_lock |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| voynich_ZL |  | 37 | 2.109 | 2.321 | 2.111 | 4.990 | 1.788 | -1.041 | 0.202 | 0.680 | 0.00841 | 0.276 | 0.095 | 0.643 |
| autocopist_s19 |  | 12 |  |  | 2.684 | 5.463 | 2.111 | -0.772 | 0.397 | 0.706 | 0.00182 | 0.333 | 0.110 | 0.443 |
| autocopist_s7 |  | 15 |  |  | 2.497 | 4.616 | 2.022 | -0.965 | 0.279 | 0.697 | 0.00252 | 0.379 | 0.185 | 0.543 |
| turkish | 1 | 14 | 3.376 | 3.616 | 3.377 | 5.556 | 2.748 | -0.912 | 0.212 | 0.581 | 0.000603 | 0.124 | 0.090 | 0.254 |
| hungarian | 1 | 15 | 3.504 | 3.744 | 3.505 | 5.316 | 3.080 | -0.924 | 0.201 | 0.557 | 0.00121 | 0.169 | 0.045 | 0.326 |
| vietnamese | 1 | 11 | 2.894 | 3.642 | 2.896 | 3.109 | 0.954 | -1.187 | 0.048 | 0.235 | 0.00141 | 0.190 | 0.650 | 0.298 |
| vietnamese_fold | 1 | 10 | 2.589 | 3.164 | 2.591 | 3.109 | 0.954 | -1.564 | 0.023 | 0.133 | 0.00253 | 0.361 | 0.536 | 0.342 |
| chinese_pinyin_syl | 1 | 10 | 2.309 | 3.042 | 2.312 | 2.760 | 0.849 | -1.509 | 0.00999 | 0.040 | 0.00603 | 0.498 | 0.862 | 0.354 |
| chinese_pinyin_word | 1 | 19 | 2.741 | 3.037 | 2.743 | 4.244 | 2.046 | -1.076 | 0.110 | 0.494 | 0.00304 | 0.248 | 0.215 | 0.392 |
| arabic_voc | 1 | 10 | 3.180 | 3.313 | 3.181 | 7.356 | 2.458 | -0.860 | 0.294 | 0.636 | 0.000287 | 0.088 | 0.110 | 0.465 |
| arabic_cons | 1 | 12 | 3.733 | 4.065 | 3.735 | 4.420 | 1.560 | -0.868 | 0.245 | 0.594 | 0.000316 | 0.136 | 0.050 | 0.286 |
| homo_la | 2 | 5 | 4.521 | 4.867 | 4.523 | 5.766 | 2.209 | -0.728 | 0.818 | 0.935 | 0 | 0.010 | 0.010 | 0.096 |
| homonull_la | 2 | 3 | 4.772 | 5.090 | 4.773 | 6.637 | 2.684 | -0.661 | 0.889 | 0.962 | 0 | 0.00522 | 0.010 | 0.081 |
| letword_la | 2 | 10 | 3.047 | 3.367 | 3.048 | 4.629 | 1.079 | -1.241 | 0.00201 | 0.029 | 0.00703 | 0.200 | 0.531 | 0.191 |
| polyb_la | 2 | 11 | 2.126 | 1.990 | 2.126 | 11.532 | 4.418 | -0.699 | 0.332 | 0.598 | 0.000316 | 0.023 | 0.020 | 1.000 |
| homo_it | 2 | 7 | 4.369 | 4.871 | 4.371 | 4.536 | 2.561 | -1.019 | 0.562 | 0.892 | 0.000172 | 0.086 | 0.045 | 0.067 |
| homonull_it | 2 | 9 | 4.625 | 5.089 | 4.628 | 5.217 | 3.039 | -0.903 | 0.673 | 0.919 | 0.000172 | 0.052 | 0.050 | 0.058 |
| letword_it | 2 | 12 | 2.987 | 3.307 | 2.989 | 4.577 | 1.080 | -0.898 | 0.00172 | 0 | 0.012 | 0.219 | 0.563 | 0.193 |
| polyb_it | 2 | 13 | 2.084 | 1.949 | 2.084 | 9.072 | 5.122 | -1.029 | 0.196 | 0.664 | 0.000746 | 0.097 | 0.111 | 1.000 |
| syl_la | 3 | 10 | 2.447 | 3.155 | 2.449 | 3.052 | 0.995 | -1.232 | 0.048 | 0.277 | 0.00253 | 0.378 | 0.538 | 0.606 |
| sylword_la | 3 | 7 | 2.995 | 3.156 | 2.996 | 6.779 | 2.673 | -0.699 | 0.331 | 0.598 | 0.000316 | 0.031 | 0.300 | 0.568 |
| sylhomo_la | 3 | 9 | 2.832 | 3.442 | 2.834 | 4.132 | 1.273 | -0.680 | 0.269 | 0.553 | 0.000373 | 0.097 | 0.503 | 0.501 |
| syl_it | 3 | 8 | 2.454 | 3.187 | 2.457 | 2.866 | 0.993 | -1.409 | 0.050 | 0.439 | 0.00184 | 0.465 | 0.474 | 0.619 |
| sylword_it | 3 | 15 | 2.974 | 3.185 | 2.975 | 5.198 | 2.948 | -1.028 | 0.196 | 0.665 | 0.000746 | 0.149 | 0.265 | 0.604 |
| sylhomo_it | 3 | 8 | 2.764 | 3.339 | 2.766 | 4.022 | 1.271 | -0.796 | 0.211 | 0.564 | 0.000172 | 0.137 | 0.477 | 0.570 |
| syl_tr | 3 | 8 | 2.320 | 3.030 | 2.322 | 3.013 | 1.081 | -1.568 | 0.030 | 0.212 | 0.00591 | 0.470 | 0.556 | 0.640 |
| sylword_tr | 3 | 10 | 2.907 | 3.034 | 2.908 | 7.277 | 3.613 | -0.912 | 0.212 | 0.581 | 0.000603 | 0.108 | 0.342 | 0.665 |
| sylhomo_tr | 3 | 8 | 2.822 | 3.446 | 2.824 | 3.995 | 1.370 | -0.743 | 0.218 | 0.511 | 0.000746 | 0.150 | 0.513 | 0.517 |

Voynich merged-glyph h2: with space 2.497, no space 2.882.

## Items matched, per corpus

- **voynich_ZL** (37): a_h0_raw, a_h1_raw, a_h2_raw, a_h3_raw, a_h2_mrg, a_h3_mrg, b_len_mean, b_len_sd, b_len1, b_len9, c_zipf, c_ttr, c_hapax_types, c_hapax_tokens, c_heaps, d_adj_exact, d_adj_ld1, e_cover, e_w10, e_prev2, e_w10_shuf, e_ratio, f_irrev, f_lock, g_len_first, g_len_mid, g_len_last, g_gal_init, g_gal_mid, h_peak_log2s, h_peak_R, i_tok_acc, i_char_bits, j_one_page, j_jacc_excess, k_jsd_halves, k_jsd_oddeven
- **autocopist_s19** (12): a_h0_raw, a_h1_raw, b_len_mean, c_hapax_types, e_prev2, e_w10_shuf, e_ratio, f_irrev, g_len_first, g_len_mid, g_len_last, h_peak_log2s
- **autocopist_s7** (15): a_h0_raw, a_h1_raw, b_len_mean, b_len9, c_zipf, c_ttr, c_hapax_types, c_hapax_tokens, c_heaps, e_ratio, g_len_first, g_len_mid, g_len_last, h_peak_log2s, i_tok_acc
- **turkish** (14): a_h0_raw, b_len_mean, b_len1, c_zipf, c_ttr, c_hapax_tokens, c_heaps, e_ratio, f_irrev, g_len_first, g_len_mid, g_gal_mid, j_one_page, k_jsd_oddeven
- **hungarian** (15): a_h0_raw, b_len_mean, c_zipf, c_ttr, c_hapax_tokens, c_heaps, e_ratio, f_irrev, g_len_first, g_len_mid, g_len_last, g_gal_init, g_gal_mid, h_peak_log2s, k_jsd_oddeven
- **vietnamese** (11): a_h3_mrg, b_len9, c_zipf, c_heaps, e_cover, e_prev2, e_w10_shuf, g_gal_init, g_gal_mid, h_peak_log2s, k_jsd_oddeven
- **vietnamese_fold** (10): a_h0_raw, a_h1_raw, a_h2_mrg, a_h3_mrg, b_len9, d_adj_ld1, g_gal_init, g_gal_mid, h_peak_log2s, k_jsd_oddeven
- **chinese_pinyin_syl** (10): a_h0_raw, a_h1_raw, a_h2_raw, a_h3_raw, a_h2_mrg, a_h3_mrg, b_len9, g_gal_mid, i_char_bits, k_jsd_oddeven
- **chinese_pinyin_word** (19): a_h0_raw, a_h1_raw, a_h3_mrg, b_len_mean, b_len9, c_zipf, c_ttr, c_hapax_tokens, c_heaps, e_cover, e_w10, e_prev2, e_w10_shuf, e_ratio, g_len_mid, g_len_last, g_gal_mid, h_peak_log2s, k_jsd_oddeven
- **arabic_voc** (10): a_h0_raw, a_h1_raw, c_zipf, c_ttr, c_hapax_types, c_hapax_tokens, f_irrev, g_gal_mid, j_one_page, k_jsd_oddeven
- **arabic_cons** (12): a_h0_raw, b_len_mean, b_len9, c_zipf, c_ttr, c_hapax_tokens, f_irrev, g_len_mid, g_len_last, g_gal_mid, j_one_page, k_jsd_oddeven
- **homo_la** (5): b_len_mean, g_len_first, g_len_mid, g_gal_mid, k_jsd_oddeven
- **homonull_la** (3): g_gal_mid, h_peak_log2s, k_jsd_oddeven
- **letword_la** (10): a_h0_raw, a_h1_raw, b_len_mean, b_len9, e_prev2, e_w10_shuf, g_len_mid, g_len_last, g_gal_mid, k_jsd_oddeven
- **polyb_la** (11): a_h2_raw, a_h3_raw, a_h2_mrg, a_h3_mrg, c_hapax_tokens, c_heaps, e_ratio, f_irrev, g_gal_mid, i_char_bits, k_jsd_oddeven
- **homo_it** (7): b_len_mean, c_zipf, f_irrev, g_len_mid, g_len_last, g_gal_mid, k_jsd_oddeven
- **homonull_it** (9): b_len_mean, c_zipf, f_irrev, g_len_first, g_len_mid, g_len_last, g_gal_mid, h_peak_log2s, k_jsd_oddeven
- **letword_it** (12): a_h0_raw, a_h1_raw, b_len_mean, b_len9, c_zipf, e_prev2, e_w10_shuf, g_len_mid, g_len_last, g_gal_mid, h_peak_log2s, k_jsd_oddeven
- **polyb_it** (13): a_h2_raw, a_h3_raw, a_h2_mrg, c_zipf, c_ttr, c_hapax_types, c_hapax_tokens, c_heaps, f_irrev, g_gal_mid, i_char_bits, j_one_page, k_jsd_oddeven
- **syl_la** (10): a_h1_raw, a_h2_mrg, a_h3_mrg, b_len1, b_len9, c_zipf, d_adj_ld1, f_lock, g_gal_mid, k_jsd_oddeven
- **sylword_la** (7): a_h1_raw, c_hapax_tokens, c_heaps, e_ratio, f_lock, g_gal_mid, k_jsd_oddeven
- **sylhomo_la** (9): a_h1_raw, b_len9, c_ttr, c_hapax_tokens, c_heaps, g_len_mid, g_len_last, g_gal_mid, k_jsd_oddeven
- **syl_it** (8): a_h1_raw, a_h2_mrg, a_h3_mrg, b_len9, f_lock, g_gal_mid, h_peak_log2s, k_jsd_oddeven
- **sylword_it** (15): a_h1_raw, b_len_mean, b_len1, c_zipf, c_ttr, c_hapax_types, c_hapax_tokens, c_heaps, f_lock, g_len_first, g_len_mid, g_len_last, g_gal_mid, j_one_page, k_jsd_oddeven
- **sylhomo_it** (8): a_h1_raw, b_len9, c_ttr, c_hapax_tokens, c_heaps, f_lock, g_gal_mid, k_jsd_oddeven
- **syl_tr** (8): a_h2_mrg, a_h3_mrg, b_len9, f_lock, g_gal_mid, h_peak_log2s, h_peak_R, k_jsd_oddeven
- **sylword_tr** (10): a_h1_raw, c_zipf, c_ttr, c_hapax_tokens, c_heaps, e_ratio, f_lock, g_gal_mid, j_one_page, k_jsd_oddeven
- **sylhomo_tr** (8): a_h1_raw, b_len9, c_ttr, c_hapax_tokens, c_heaps, g_gal_mid, i_tok_acc, k_jsd_oddeven
