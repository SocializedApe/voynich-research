# v_a1 -- adversarial re-check of a1

## Redundancy table (no spaces, 150k letters for languages/controls; Voynich full size)

| sample | inv | h1 | h2 | h1-h2 | h2/h1 |
|---|---|---|---|---|---|
| ZL A raw | 24 | 3.832 | 2.353 | 1.479 | 0.614 |
| ZL A merge2 | 37 | 3.989 | 2.939 | 1.050 | 0.737 |
| ZL B raw | 24 | 3.859 | 2.182 | 1.677 | 0.565 |
| ZL B merge2 | 38 | 4.028 | 2.690 | 1.338 | 0.668 |
| ZL ALL raw | 25 | 3.865 | 2.311 | 1.554 | 0.598 |
| ZL ALL merge2 | 39 | 4.039 | 2.870 | 1.170 | 0.710 |
| GC ALL raw | 70 | 4.153 | 2.897 | 1.256 | 0.698 |
| la | 24 | 4.025 | 3.510 | 0.515 | 0.872 |
| de | 33 | 4.160 | 3.391 | 0.769 | 0.815 |
| en | 30 | 4.184 | 3.601 | 0.583 | 0.861 |
| fr | 40 | 4.196 | 3.592 | 0.604 | 0.856 |
| da | 36 | 4.218 | 3.652 | 0.567 | 0.866 |
| nl | 34 | 4.117 | 3.461 | 0.656 | 0.841 |
| sv | 36 | 4.341 | 3.683 | 0.657 | 0.849 |
| no | 32 | 4.193 | 3.576 | 0.617 | 0.853 |
| is | 43 | 4.525 | 3.878 | 0.648 | 0.857 |
| fi | 31 | 3.997 | 3.453 | 0.544 | 0.864 |
| it (italian windows only) | 21 | 3.941 | 3.450 | 0.491 | 0.875 |
| LAT-verbose12 | 12 | 3.328 | 2.707 | 0.620 | 0.814 |
| LAT-verbose6 | 6 | 2.562 | 2.289 | 0.272 | 0.894 |
| LAT-verbose20 | 19 | 3.652 | 2.737 | 0.914 | 0.750 |
| LAT-verbose24 (8/12/rest) | 22 | 4.102 | 2.916 | 1.186 | 0.711 |
| LAT-verbose24 (0/24/rest) | 20 | 3.901 | 2.325 | 1.576 | 0.596 |
| LAT-novowel | 21 | 3.659 | 3.515 | 0.144 | 0.961 |

## Books actually in each 150k sample (letters)

- la: {'corp_la_227.txt': 150002}  a1 h2 3.51 / recomputed 3.51 / folded a-z 3.51 (inv 24)
- de: {'corp_de_35312.txt': 129732, 'corp_de_50285.txt': 20268}  a1 h2 3.391 / recomputed 3.391 / folded a-z 3.335 (inv 26)
- en: {'corp_en_1342.txt': 150002}  a1 h2 3.601 / recomputed 3.601 / folded a-z 3.601 (inv 26)
- fr: {'corp_fr_18143.txt': 129737, 'corp_fr_19919.txt': 20265}  a1 h2 3.592 / recomputed 3.592 / folded a-z 3.467 (inv 26)
- da: {'corp_da_24747.txt': 103789, 'corp_da_36942.txt': 46215}  a1 h2 3.652 / recomputed 3.652 / folded a-z 3.574 (inv 25)
- nl: {'corp_nl_76186.txt': 80372, 'corp_nl_76280.txt': 69636}  a1 h2 3.461 / recomputed 3.461 / folded a-z 3.456 (inv 26)
- sv: {'corp_sv_48961.txt': 127665, 'corp_sv_59341.txt': 22336}  a1 h2 3.683 / recomputed 3.683 / folded a-z 3.509 (inv 26)
- no: {'corp_no_30027.txt': 129742, 'corp_no_43724.txt': 20262}  a1 h2 3.576 / recomputed 3.576 / folded a-z 3.488 (inv 26)
- is: {'corp_is_15178.txt': 103791, 'corp_is_16696.txt': 17852, 'corp_is_16846.txt': 15302, 'corp_is_17025.txt': 13056}  a1 h2 3.876 / recomputed 3.878 / folded a-z 3.601 (inv 26)
- fi: {'corp_fi_75789.txt': 55187, 'corp_fi_78071.txt': 29402}  a1 h2 3.453 / recomputed 3.453 / folded a-z 3.319 (inv 26)

## Latin per book (50k letters)

- corp_la_227.txt: h1 4.024 h2 3.507 h1-h2 0.517 H_word 11.225 en_stop 0.019
- corp_la_33849.txt: h1 4.048 h2 3.528 h1-h2 0.52 H_word 10.223 en_stop 0.033
- corp_la_50280.txt: h1 4.128 h2 3.63 h1-h2 0.497 H_word 9.975 en_stop 0.267
- Aeneid+Confessions 150k: h1 4.045 h2 3.543 h1-h2 0.503 H_word 11.568 en_stop None

## Italian corpus

{"window_counts_200w_first4MB": {"la": 97, "it": 3471}, "share_of_first_150k_sample_windows": {"la": 1, "it": 164}, "latin_windows_only_150k": null, "german_windows_only_150k": null}
- a1_it_150k_mixed: h1 3.942 h2 3.451 h1-h2 0.491 H_word 9.825 hapax 0.666
- italian_windows_only_150k: h1 3.941 h2 3.45 h1-h2 0.491 H_word 9.821 hapax 0.666

## Voynich recomputed vs a1

{"ZL A raw": {"h1": 3.832, "h2": 2.353, "h2_within": 2.128}, "ZL A merge2": {"h1": 3.989, "h2": 2.939, "h2_within": 2.684}, "ZL B raw": {"h1": 3.859, "h2": 2.182, "h2_within": 1.924}, "ZL B merge2": {"h1": 4.028, "h2": 2.69, "h2_within": 2.437}, "ZL ALL raw": {"h1": 3.865, "h2": 2.311, "h2_within": 2.065}, "ZL ALL merge2": {"h1": 4.039, "h2": 2.87, "h2_within": 2.621}}
- ZL A raw: h1 3.832 h2 2.353 h2_sp 2.169 h2_within 2.128 H_word 9.856 hapax 0.722
- ZL B raw: h1 3.859 h2 2.182 h2_sp 1.999 h2_within 1.924 H_word 9.817 hapax 0.686
- ZL ALL raw: h1 3.865 h2 2.311 h2_sp 2.117 h2_within 2.065 H_word 10.271 hapax 0.697
- ZL A merge2: h1 3.989 h2 2.939 h2_sp 2.578 h2_within 2.684 H_word 9.856 hapax 0.722
- ZL B merge2: h1 4.028 h2 2.69 h2_sp 2.358 h2_within 2.437 H_word 9.817 hapax 0.686
- ZL ALL merge2: h1 4.039 h2 2.87 h2_sp 2.509 h2_within 2.621 H_word 10.271 hapax 0.697
- GC ALL raw: h1 4.153 h2 2.897 h2_sp 2.533 h2_within 2.6 H_word 10.516 hapax 0.702
- Miller-Madow h2: ZL ALL raw 2.312, GC ALL 2.904

## Hygiene
{"ZL_dropped": {"?": 98, "non a-z": 96}, "ZL_offending_chars": {"@": 73, ";": 73, "1": 61, "9": 9, "2": 19, "0": 14, "3": 16, "'": 23, "6": 19, "5": 23, "7": 15, "8": 16, "4": 18}, "ZL_kept_words": 34116, "GC_dropped": {"@": 273, "?": 45}, "GC_kept_words": 36385, "GC_symbol_inventory": "!#$%&(*+123456789ABCDEFGHIJKLMNPQRSTUVWXYZ\\abcdefghijklmnopqrstuvwxyz|", "ZL_lang_counts": {"A": 10715, "B": 22862, "?": 539}}

## Extra checks
{
 "GC_reserved_chars": {
  "words_with_!": 42,
  "words_with_%": 133,
  "of_words": 36385,
  "GC_ALL_h2_after_stripping_!_%": 2.893,
  "a1_GC_ALL_h2": 2.897
 },
 "latin_word_entropy_by_genre": {
  "Aeneid_H_w@10715/22862/34116": [
   11.34,
   11.84,
   12.05
  ],
  "Confessions_prose_H_w@10715/22862/34116": [
   10.26,
   10.53,
   10.76
  ],
  "Confessions_types": [
   3985,
   6990,
   9486
  ],
  "Confessions_hapax": [
   0.71,
   0.69,
   0.67
  ],
  "Confessions_150k": {
   "h1": 4.036,
   "h2": 3.504,
   "h2/h1": 0.868,
   "h1-h2": 0.533,
   "mean_wlen": 5.394
  },
  "phrasebook_corp_la_50280_english_stopword_token_share": 0.267
 },
 "italian_150k_stopword_token_shares": {
  "it": 0.238,
  "la": 0.081,
  "de": 0.002
 },
 "verbose_controls_mean_wlen": {
  "verbose6": 14.05,
  "verbose12": 10.07,
  "verbose20": 8.66,
  "verbose24_8/12/rest": 7.64,
  "verbose24_0/24/rest": 11.52,
  "Voynich_ZL_raw_ALL": 5.07,
  "Voynich_ZL_merge2_ALL": 3.8
 }
}
