# Which process gives the Voynich word-internal profile? (12 Nov 2026)

Script `oddities.py` (rule in its docstring). Reproduce: `python phase2/build.py`, `python phase2/build2.py`, `python phase2/oddities.py` from `targets/voynich`.

Window per feature (Voynich range widened by a quarter of the natural sd): m_tail_family 1.75 to 1.92; p_jsd_final_med 0.65 to 0.83; m_suffix_trie 0.31 to 0.35; m_prefix_trie 0.39 to 0.45; c_h2 1.80 to 2.40; t_merge_len 2.99 to 3.75; w_len_skew -0.06 to 0.40; s_len_ac1_x 0.02 to 0.16.

| text | chunks | features inside (of 8), mean | best single chunk | m_tail_family | p_jsd_final_med | m_suffix_trie | m_prefix_trie | c_h2 | t_merge_len | w_len_skew | s_len_ac1_x |
|---|---|---|---|---|---|---|---|---|---|---|---|
| voynich: ZL units | 8 | 8 | 8 | **1.85** | **0.74** | **0.33** | **0.42** | **2.15** | **3.37** | **0.15** | **0.10** |
| voynich: IT units | 8 | 7 | 8 | **1.79** | **0.73** | **0.34** | **0.44** | **2.18** | **3.35** | 0.68 | **0.10** |
| voynich: ZL EVA characters | 8 | 7 | 7 | 1.70 | **0.75** | **0.34** | **0.40** | **2.03** | **3.58** | **0.02** | **0.13** |
| mimic: naibbe | 4 | 5 | 5 | 2.26 | **0.74** | **0.31** | 0.37 | **2.13** | **3.40** | **0.12** | -0.03 |
| mimic: lang8 | 4 | 4 | 6 | 1.71 | **0.73** | 0.36 | **0.44** | **2.17** | **3.27** | 0.66 | 0.01 |
| generated: topic | 40 | 4 | 5 | 2.77 | 0.30 | **0.32** | 0.34 | **2.33** | **3.67** | -0.35 | **0.12** |
| cipher: taxonomic | 50 | 3 | 4 | 3.71 | 0.29 | 0.41 | **0.45** | 2.50 | **3.10** | **0.00** | 0.00 |
| mimic: autocopist | 6 | 3 | 4 | 2.06 | 0.50 | 0.27 | **0.45** | 2.61 | **3.02** | 0.47 | **0.12** |
| mimic: rugg | 4 | 3 | 4 | 2.25 | **0.67** | 0.30 | 0.35 | 2.44 | **3.21** | **-0.01** | 0.28 |
| cipher: posverbose | 50 | 2 | 4 | 1.08 | **0.76** | 0.53 | 0.53 | 2.46 | **3.27** | 0.93 | -0.09 |
| generated: chain | 40 | 2 | 4 | 3.03 | 0.52 | **0.31** | 0.38 | 2.64 | **3.19** | -0.19 | -0.00 |
| generated: table | 40 | 2 | 4 | 2.43 | 0.37 | **0.34** | 0.35 | **2.06** | 3.96 | -0.33 | -0.00 |
| generated: selfcite | 40 | 2 | 2 | 1.10 | 0.10 | 0.54 | 0.55 | 3.63 | 2.02 | **0.12** | **0.04** |
| generated: selfcite2 | 40 | 2 | 2 | 1.20 | 0.09 | 0.56 | 0.56 | 3.61 | 2.19 | **0.13** | **0.05** |
| natural: Quichua-NT | 4 | 2 | 2 | 1.08 | 0.29 | 0.46 | **0.44** | 2.80 | **3.27** | 0.82 | -0.01 |
| natural: Vietnamese-tok | 4 | 2 | 2 | 1.30 | 0.36 | 0.51 | 0.54 | 2.78 | 2.59 | **0.31** | **0.08** |
| cipher: digraphic | 50 | 1 | 2 | 0.94 | **0.66** | 0.65 | 0.66 | 3.12 | 2.30 | 1.03 | -0.09 |
| natural: Turkish | 4 | 1 | 2 | 1.06 | 0.13 | 0.53 | 0.46 | 3.36 | 2.53 | 0.57 | **0.03** |
| natural: gutenberg:la-gutenberg | 4 | 1 | 2 | 1.11 | 0.19 | 0.51 | 0.48 | 3.31 | 2.46 | **0.35** | 0.02 |
| mimic: volunteers | 2 | 1 | 1 | 1.07 | 0.02 | 0.58 | 0.57 | 3.87 | 2.13 | 1.14 | **0.11** |
| natural: Arabic | 4 | 1 | 1 | 1.14 | 0.14 | 0.50 | 0.51 | 3.54 | 2.50 | 0.54 | **0.05** |
| natural: Hebrew | 4 | 1 | 1 | 1.22 | 0.29 | 0.45 | 0.48 | 3.37 | 2.42 | **0.32** | -0.00 |
| natural: Hindi | 4 | 1 | 1 | 0.50 | 0.23 | 0.53 | 0.53 | 2.64 | 2.17 | 1.46 | **0.03** |
| natural: Korean | 4 | 1 | 1 | 1.31 | 0.52 | 0.55 | 0.59 | 3.38 | 2.36 | 0.61 | **0.03** |
| cipher: anagram | 50 | 0 | 3 | 1.07 | 0.37 | 0.57 | 0.51 | 2.66 | 2.70 | 0.94 | -0.10 |
| cipher: abbrev | 50 | 0 | 2 | 1.01 | 0.41 | 0.57 | 0.53 | 3.28 | 2.52 | 0.75 | -0.10 |
| cipher: abjad | 49 | 0 | 2 | 1.07 | 0.14 | 0.46 | 0.46 | 2.92 | 2.43 | 1.22 | -0.07 |
| cipher: homophonic | 50 | 0 | 2 | 1.10 | 0.22 | 0.60 | 0.59 | 4.00 | 2.05 | 0.98 | -0.09 |
| cipher: nulls | 50 | 0 | 2 | 1.06 | 0.15 | 0.58 | 0.55 | 3.50 | 2.22 | 1.00 | -0.08 |
| cipher: respace | 50 | 0 | 2 | 1.10 | 0.01 | 0.49 | 0.49 | 3.51 | 2.28 | 0.96 | -0.00 |
| cipher: verbose | 50 | 0 | 2 | 1.06 | 0.24 | 0.52 | 0.51 | 2.48 | 4.31 | 0.92 | -0.09 |
| generated: bag | 50 | 0 | 2 | 1.10 | 0.23 | 0.54 | 0.53 | 3.11 | 2.66 | 0.98 | 0.00 |
| generated: blockshuffle | 50 | 0 | 2 | 1.08 | 0.23 | 0.54 | 0.53 | 3.11 | 2.65 | 0.99 | 0.01 |
| generated: markov2 | 50 | 0 | 2 | 1.17 | 0.23 | 0.50 | 0.51 | 3.09 | 2.45 | 1.77 | -0.00 |
| generated: markov3 | 50 | 0 | 2 | 1.15 | 0.23 | 0.48 | 0.47 | 3.09 | 2.59 | 1.37 | -0.00 |
| generated: wordchain | 50 | 0 | 2 | 1.09 | 0.22 | 0.54 | 0.53 | 3.16 | 2.55 | 0.96 | -0.09 |
| other: numerals | 10 | 0 | 2 | 1.64 | 0.13 | 0.28 | 0.38 | 1.48 | 3.98 | 1.95 | -0.00 |
| cipher: codebook | 50 | 0 | 1 | 1.04 | 0.18 | 0.60 | 0.60 | 3.06 | 2.25 | 0.81 | -0.06 |
| generated: markov1 | 50 | 0 | 1 | 1.08 | 0.21 | 0.57 | 0.59 | 3.09 | 2.30 | 1.89 | 0.01 |

Natural sources: 67; features inside the window, mean 0.3, maximum 2 (the eight best are listed above).
