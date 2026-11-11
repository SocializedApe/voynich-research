# Phase 2: linguistic features and classifiers, second round with structured generators (12 Nov 2026); training rows from features.csv + features2.csv

Scripts `features.py`, `build.py`, `model.py` (protocol and the rule for a verdict in the docstring of `model.py`, written before the Voynich rows were looked at). Reproduce from `targets/voynich`: `python phase2/corpora2.py`, `python lines/fetch_mss.py`, `python phase2/build.py`, `python phase2/model.py`.

Training chunks 1278 (natural 229, cipher 549, generated 500), 68 features, 4,000 tokens a chunk.

## Checks on the models

| check | logistic | forest | boosting |
|---|---|---|---|
| C1 leave-source-out AUC | 0.994 | 1.000 | 1.000 |
| C1 leave-source-out accuracy | 0.972 | 0.998 | 0.996 |
| C3 other genres called meaningful (n 29) | 0.52 | 0.97 | 1.00 |

C2, a process left out of training, share of its chunks put on the right side:

| process (truth) | n | logistic | forest | boosting |
|---|---|---|---|---|
| abbrev (meaningful) | 50 | 1.00 | 1.00 | 1.00 |
| abjad (meaningful) | 49 | 0.90 | 1.00 | 1.00 |
| anagram (meaningful) | 50 | 1.00 | 1.00 | 1.00 |
| bag (generated) | 50 | 1.00 | 1.00 | 1.00 |
| blockshuffle (generated) | 50 | 0.72 | 0.78 | 0.18 |
| chain (generated) | 40 | 1.00 | 1.00 | 1.00 |
| codebook (meaningful) | 50 | 0.68 | 1.00 | 1.00 |
| digraphic (meaningful) | 50 | 0.98 | 1.00 | 1.00 |
| homophonic (meaningful) | 50 | 0.26 | 0.96 | 0.98 |
| markov1 (generated) | 50 | 0.54 | 0.98 | 1.00 |
| markov2 (generated) | 50 | 1.00 | 1.00 | 1.00 |
| markov3 (generated) | 50 | 1.00 | 1.00 | 1.00 |
| nulls (meaningful) | 50 | 1.00 | 0.98 | 0.96 |
| posverbose (meaningful) | 50 | 1.00 | 1.00 | 1.00 |
| respace (meaningful) | 50 | 0.30 | 0.72 | 0.86 |
| selfcite (generated) | 40 | 0.12 | 1.00 | 1.00 |
| selfcite2 (generated) | 40 | 1.00 | 1.00 | 1.00 |
| table (generated) | 40 | 1.00 | 1.00 | 1.00 |
| taxonomic (meaningful) | 50 | 0.12 | 1.00 | 1.00 |
| topic (generated) | 40 | 0.05 | 0.23 | 0.30 |
| verbose (meaningful) | 50 | 0.44 | 1.00 | 1.00 |
| wordchain (generated) | 50 | 0.00 | 0.00 | 0.00 |

## Held-out texts: mimics (truth known) and Voynich

| text | chunks | P(meaningful) logistic | forest | boosting | 3-class: natural / cipher / generated | distance (percentile of training) | chunks in distribution |
|---|---|---|---|---|---|---|---|
| mimic: autocopist | 6 | 0.01 | 0.37 | 0.00 | 0.00 / 0.00 / 1.00 | 9.3 (0.99) | 0 |
| mimic: lang8 | 4 | 0.01 | 0.21 | 0.34 | 0.00 / 0.13 / 0.87 | 6.0 (0.92) | 4 |
| mimic: naibbe | 4 | 0.01 | 0.08 | 0.00 | 0.00 / 0.00 / 1.00 | 6.8 (0.95) | 3 |
| mimic: rugg | 4 | 0.00 | 0.51 | 0.52 | 0.00 / 0.95 / 0.05 | 24.1 (1.00) | 0 |
| mimic: volunteers | 2 | 0.57 | 0.49 | 0.08 | 0.00 / 0.42 / 0.58 | 6.0 (0.92) | 2 |
| voynich: IT units | 8 | 0.46 | 0.39 | 0.26 | 0.00 / 0.53 / 0.47 | 7.0 (0.95) | 2 |
| voynich: ZL EVA characters | 8 | 0.28 | 0.37 | 0.28 | 0.00 / 0.76 / 0.24 | 6.8 (0.95) | 4 |
| voynich: ZL units | 8 | 0.27 | 0.41 | 0.17 | 0.00 / 0.78 / 0.22 | 7.0 (0.96) | 3 |

Novelty threshold (95th percentile of training distances) 6.8; median 3.3.

## Conditions and verdict

- C1 leave-source-out AUC >= 0.95: met
- C2 leave-process-out mean recall >= 0.8, none under 0.5: NOT met
- C3 other genres recall >= 0.9: met
- C4 all mimic families on the right side: NOT met
- C5 at least 6 of 8 Voynich chunks in distribution: NOT met

**Verdict: no verdict (failed: C2 leave-process-out mean recall >= 0.8, none under 0.5; C4 all mimic families on the right side; C5 at least 6 of 8 Voynich chunks in distribution)**

## Description: nearest training chunks to the Voynich chunks (ZL units; count among the 10 nearest of each of 8 chunks)

- natural / plain / Syriac-NT: 10
- generated / table / table33: 8
- cipher / posverbose / Syriac-NT: 7
- natural / plain / manuscript:bnf_fr_844-manuscritDuRoi: 5
- generated / table / table8: 5
- natural / plain / manuscript:bnf_fr_22549-septSages: 4
- generated / table / table34: 4
- generated / blockshuffle / Hebrew: 4
- generated / blockshuffle / Quichua-NT: 4
- generated / table / table37: 3
- generated / table / table11: 3
- natural / plain / Hebrew: 2
- cipher / anagram / Syriac-NT: 2
- generated / table / table35: 2
- generated / table / table0: 2

## Description: where Voynich sits, feature by feature

z = (Voynich mean - kind mean) / kind sd on standardised features; the 25 features furthest from natural language first.

| feature | Voynich | natural median | percentile in natural | z natural | z cipher | z generated |
|---|---|---|---|---|---|---|
| m_tail_family | 1.853 | 1.089 | 1.00 | +6.0 | +0.6 | +0.4 |
| p_jsd_final_med | 0.744 | 0.190 | 1.00 | +5.3 | +1.8 | +3.6 |
| m_suffix_trie | 0.330 | 0.537 | 0.00 | -4.3 | -2.6 | -1.5 |
| c_h2 | 2.148 | 3.151 | 0.00 | -3.8 | -1.6 | -1.8 |
| t_merge_len | 3.369 | 2.620 | 1.00 | +3.0 | +1.0 | +1.1 |
| m_stem_family | 1.407 | 1.103 | 1.00 | +2.5 | -0.0 | -0.0 |
| m_prefix_trie | 0.422 | 0.520 | 0.00 | -2.3 | -1.5 | -0.8 |
| c_h3 | 1.868 | 2.338 | 0.02 | -2.3 | -0.9 | -0.9 |
| z_wordid_x | -0.298 | -1.496 | 0.99 | +2.2 | +1.4 | +0.4 |
| s_near_adj_x | 0.015 | -0.004 | 0.98 | +2.2 | +1.6 | +1.4 |
| p_jsd_init_final | 0.636 | 0.315 | 0.98 | +2.2 | +0.4 | +0.7 |
| c_h2_over_h1 | 0.557 | 0.752 | 0.05 | -2.2 | -1.0 | -1.5 |
| w_len_skew | 0.155 | 0.871 | 0.00 | -2.0 | -1.3 | -0.7 |
| s_len_ac1_x | 0.100 | -0.088 | 1.00 | +2.0 | +1.9 | +1.4 |
| c_h3_over_h2 | 0.869 | 0.746 | 1.00 | +2.0 | +1.3 | +1.1 |
| p_double | 0.047 | 0.007 | 0.97 | +1.9 | +0.7 | +2.1 |
| l_ld1_share | 0.862 | 0.475 | 0.93 | +1.9 | +1.2 | +0.9 |
| s_len_hurst | 0.598 | 0.519 | 0.97 | +1.8 | +2.2 | +1.1 |
| t_pieces_per_symbol | 0.405 | 0.553 | 0.00 | -1.8 | -1.1 | -1.0 |
| m_trie_asym | 0.091 | -0.008 | 0.95 | +1.8 | +2.0 | +2.0 |
| p_h_final | 0.633 | 0.839 | 0.10 | -1.7 | -1.3 | -1.0 |
| m_suffix_pref | 1.185 | 0.413 | 0.97 | +1.7 | +1.8 | +1.5 |
| p_h_init | 0.871 | 0.972 | 0.09 | -1.6 | +0.1 | -0.4 |
| w_len_cv | 0.364 | 0.505 | 0.07 | -1.6 | -0.5 | -0.6 |
| t_merge_at_end | 0.725 | 0.474 | 0.90 | +1.5 | +1.3 | +1.7 |

Features where Voynich is inside the middle 90% of natural languages (45 of 68): c_h1, c_h2_over_h1, c_alpha_eff, p_vowel_share, p_cv_alt_excess, p_h_init, p_h_final, p_jsd_init_med, w_len_mean, w_len_sd, w_len_cv, w_len1, w_type_len_mean, w_type_len_var_over_mean, w_brevity, l_ttr, l_hapax_types, l_zipf_slope, l_zipf_curv, l_h_word, l_top1, l_top10, l_heaps, l_ld1_share, l_ld1_mean, m_trie_asym, m_succ_var, m_pred_var, t_pieces_per_word, t_top20_cover, t_piece_entropy, t_merge_at_start, t_merge_at_end, t_whole_words, s_w10_x, s_sandhi_x, s_first_first_x, d_half_jsd_x, d_cluster_x, d_new_late_x, s_rep_adj, s_burst_top, s_burst_mid, s_burst_diff, z_bpc.

Most used features (random forest importance): s_bigram_mi_x 0.092, s_burst_mid 0.075, s_rep_adj 0.071, s_sandhi_x 0.069, d_half_jsd_x 0.067, s_irrev_x 0.064, s_first_first_x 0.061, d_cluster_x 0.054, s_class_rank_x 0.051, s_agree_last_x 0.048, s_rep_adj_x 0.041, s_burst_top 0.032, z_wordid_x 0.020, d_new_late_x 0.018, s_w10_x 0.017.

Runtime 136 s.
