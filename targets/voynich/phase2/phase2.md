# Phase 2: linguistic features and classifiers (11 Nov 2026)

Scripts `features.py`, `build.py`, `model.py` (protocol and the rule for a verdict in the docstring of `model.py`, written before the Voynich rows were looked at). Reproduce from `targets/voynich`: `python phase2/corpora2.py`, `python lines/fetch_mss.py`, `python phase2/build.py`, `python phase2/model.py`.

Training chunks 908 (natural 229, cipher 399, generated 280), 68 features, 4,000 tokens a chunk.

## Checks on the models

| check | logistic | forest | boosting |
|---|---|---|---|
| C1 leave-source-out AUC | 1.000 | 1.000 | 0.999 |
| C1 leave-source-out accuracy | 0.999 | 1.000 | 0.999 |
| C3 other genres called meaningful (n 29) | 1.00 | 1.00 | 1.00 |

C2, a process left out of training, share of its chunks put on the right side:

| process (truth) | n | logistic | forest | boosting |
|---|---|---|---|---|
| abjad (meaningful) | 49 | 0.98 | 1.00 | 1.00 |
| anagram (meaningful) | 50 | 1.00 | 1.00 | 1.00 |
| bag (generated) | 50 | 0.94 | 1.00 | 1.00 |
| codebook (meaningful) | 50 | 1.00 | 1.00 | 0.56 |
| digraphic (meaningful) | 50 | 1.00 | 1.00 | 1.00 |
| homophonic (meaningful) | 50 | 0.94 | 1.00 | 0.98 |
| markov1 (generated) | 50 | 0.98 | 1.00 | 1.00 |
| markov2 (generated) | 50 | 1.00 | 1.00 | 1.00 |
| markov3 (generated) | 50 | 1.00 | 1.00 | 1.00 |
| nulls (meaningful) | 50 | 1.00 | 1.00 | 1.00 |
| respace (meaningful) | 50 | 1.00 | 1.00 | 1.00 |
| selfcite (generated) | 40 | 0.00 | 0.00 | 0.00 |
| table (generated) | 40 | 1.00 | 1.00 | 1.00 |
| verbose (meaningful) | 50 | 0.90 | 1.00 | 1.00 |

## Held-out texts: mimics (truth known) and Voynich

| text | chunks | P(meaningful) logistic | forest | boosting | 3-class: natural / cipher / generated | distance (percentile of training) | chunks in distribution |
|---|---|---|---|---|---|---|---|
| mimic: autocopist | 6 | 0.00 | 0.78 | 0.72 | 0.11 / 0.57 / 0.33 | 10.1 (0.99) | 0 |
| mimic: lang8 | 4 | 0.03 | 0.53 | 0.95 | 0.00 / 1.00 / 0.00 | 6.6 (0.93) | 4 |
| mimic: naibbe | 4 | 0.03 | 0.13 | 0.06 | 0.00 / 0.00 / 1.00 | 7.2 (0.95) | 2 |
| mimic: rugg | 4 | 0.27 | 0.83 | 1.00 | 0.00 / 1.00 / 0.00 | 25.9 (1.00) | 0 |
| mimic: volunteers | 2 | 0.84 | 0.70 | 1.00 | 0.00 / 1.00 / 0.00 | 6.7 (0.94) | 2 |
| voynich: IT units | 8 | 0.34 | 0.89 | 1.00 | 0.00 / 1.00 / 0.00 | 7.7 (0.96) | 1 |
| voynich: ZL EVA characters | 8 | 0.28 | 0.87 | 1.00 | 0.00 / 1.00 / 0.00 | 7.5 (0.96) | 1 |
| voynich: ZL units | 8 | 0.29 | 0.89 | 1.00 | 0.00 / 1.00 / 0.00 | 7.6 (0.96) | 1 |

Novelty threshold (95th percentile of training distances) 7.1; median 3.5.

## Conditions and verdict

- C1 leave-source-out AUC >= 0.95: met
- C2 leave-process-out mean recall >= 0.8, none under 0.5: NOT met
- C3 other genres recall >= 0.9: met
- C4 all mimic families on the right side: NOT met
- C5 at least 6 of 8 Voynich chunks in distribution: NOT met

**Verdict: no verdict (failed: C2 leave-process-out mean recall >= 0.8, none under 0.5; C4 all mimic families on the right side; C5 at least 6 of 8 Voynich chunks in distribution)**

## Description: nearest training chunks to the Voynich chunks (ZL units; count among the 10 nearest of each of 8 chunks)

- natural / plain / Syriac-NT: 12
- generated / table / table33: 8
- generated / table / table34: 6
- cipher / digraphic / Quichua-NT: 6
- natural / plain / manuscript:bnf_fr_844-manuscritDuRoi: 5
- natural / plain / manuscript:bnf_fr_22549-septSages: 5
- generated / table / table0: 5
- natural / plain / Hebrew: 5
- generated / table / table23: 4
- generated / table / table37: 4
- generated / table / table1: 4
- cipher / anagram / Syriac-NT: 3
- generated / table / table20: 3
- generated / table / table27: 2
- generated / table / table12: 2

## Description: where Voynich sits, feature by feature

z = (Voynich mean - kind mean) / kind sd on standardised features; the 25 features furthest from natural language first.

| feature | Voynich | natural median | percentile in natural | z natural | z cipher | z generated |
|---|---|---|---|---|---|---|
| m_tail_family | 1.853 | 1.089 | 1.00 | +6.0 | +4.1 | +1.0 |
| p_jsd_final_med | 0.744 | 0.190 | 1.00 | +5.3 | +2.4 | +4.4 |
| m_suffix_trie | 0.330 | 0.537 | 0.00 | -4.3 | -3.0 | -2.0 |
| c_h2 | 2.148 | 3.151 | 0.00 | -3.8 | -1.8 | -1.8 |
| t_merge_len | 3.369 | 2.620 | 1.00 | +3.0 | +1.1 | +1.2 |
| m_stem_family | 1.407 | 1.103 | 1.00 | +2.5 | +1.6 | +0.3 |
| m_prefix_trie | 0.422 | 0.520 | 0.00 | -2.3 | -1.5 | -1.0 |
| c_h3 | 1.868 | 2.338 | 0.02 | -2.3 | -1.2 | -1.0 |
| z_wordid_x | -0.298 | -1.496 | 0.99 | +2.2 | +1.2 | +0.1 |
| s_near_adj_x | 0.015 | -0.004 | 0.98 | +2.2 | +1.9 | +1.6 |
| p_jsd_init_final | 0.636 | 0.315 | 0.98 | +2.2 | +0.8 | +0.8 |
| c_h2_over_h1 | 0.557 | 0.752 | 0.05 | -2.2 | -1.0 | -1.4 |
| w_len_skew | 0.155 | 0.871 | 0.00 | -2.0 | -1.6 | -1.0 |
| s_len_ac1_x | 0.100 | -0.088 | 1.00 | +2.0 | +1.9 | +3.8 |
| c_h3_over_h2 | 0.869 | 0.746 | 1.00 | +2.0 | +1.1 | +0.7 |
| p_double | 0.047 | 0.007 | 0.97 | +1.9 | +0.7 | +2.2 |
| l_ld1_share | 0.862 | 0.475 | 0.93 | +1.9 | +1.4 | +1.2 |
| s_len_hurst | 0.598 | 0.519 | 0.97 | +1.8 | +2.1 | +1.4 |
| t_pieces_per_symbol | 0.405 | 0.553 | 0.00 | -1.8 | -1.3 | -1.1 |
| m_trie_asym | 0.091 | -0.008 | 0.95 | +1.8 | +2.4 | +2.4 |
| p_h_final | 0.633 | 0.839 | 0.10 | -1.7 | -2.0 | -1.2 |
| m_suffix_pref | 1.185 | 0.413 | 0.97 | +1.7 | +1.9 | +2.5 |
| p_h_init | 0.871 | 0.972 | 0.09 | -1.6 | -0.2 | -0.5 |
| w_len_cv | 0.364 | 0.505 | 0.07 | -1.6 | -1.5 | -1.0 |
| t_merge_at_end | 0.725 | 0.474 | 0.90 | +1.5 | +1.2 | +1.6 |

Features where Voynich is inside the middle 90% of natural languages (45 of 68): c_h1, c_h2_over_h1, c_alpha_eff, p_vowel_share, p_cv_alt_excess, p_h_init, p_h_final, p_jsd_init_med, w_len_mean, w_len_sd, w_len_cv, w_len1, w_type_len_mean, w_type_len_var_over_mean, w_brevity, l_ttr, l_hapax_types, l_zipf_slope, l_zipf_curv, l_h_word, l_top1, l_top10, l_heaps, l_ld1_share, l_ld1_mean, m_trie_asym, m_succ_var, m_pred_var, t_pieces_per_word, t_top20_cover, t_piece_entropy, t_merge_at_start, t_merge_at_end, t_whole_words, s_w10_x, s_sandhi_x, s_first_first_x, d_half_jsd_x, d_cluster_x, d_new_late_x, s_rep_adj, s_burst_top, s_burst_mid, s_burst_diff, z_bpc.

Most used features (random forest importance): s_sandhi_x 0.163, s_first_first_x 0.108, s_agree_last_x 0.096, d_half_jsd_x 0.072, s_bigram_mi_x 0.067, s_burst_mid 0.063, s_rep_adj 0.048, d_cluster_x 0.043, s_class_rank_x 0.042, s_irrev_x 0.034, z_wordid_x 0.031, s_burst_top 0.026, d_new_late_x 0.020, s_w10_x 0.016, c_h3 0.014.

Runtime 64 s.
