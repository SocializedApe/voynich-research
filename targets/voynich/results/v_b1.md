# v_b1: adversarial re-check of b1_segmentation.py

Script v_b1.py (stdlib only, seeded; nothing imported from b1/a1/a3/a4), runtime 40 s, full numbers in v_b1.json. b1 values are read from git HEAD:targets/voynich/results/b1.json.

**Verdict: numbers HOLD; two readings CORRECTED; one parse defect found upstream of b1.** Every deterministic number in b1.md reproduces: exactly in the as-is re-run, and to b1's stored precision in an independent re-implementation (counts, types, hapax, Zipf, length, all entropies, positional lock, MI, and the pair-violation order cost; a printed 3-decimal value can differ by one in the last place from rounding the same 4-decimal number). Length-matched values differ only by the resampling draw (<= 0.002; 10 seeds span 0.162-0.165 for CERTAIN merge-a3). The conclusion b1 supports also stands: no syllabic writing of Latin or Italian reproduces the Voynich profile. But (1) the one close match in b1's own match table, CV syllables against Voynich h2 with spaces, comes from the token shape: a language-free generator of C/V/CV tokens gives 2.10-2.16 bits. The syl2 length match is just as much an arithmetic consequence of the chunk size. (2) One sixth of the length-matched syllable sample is drawn from about 22 rare long syllables, mostly syllabifier artefacts ('troiae', 'graius'). Without them la_verse scores 0.255, not 0.192, and at equal length the gap to Voynich is larger than b1's single figure. (3) The ZL parse (parse_ivtff.py, re-used by b1 for ALL and CERTAIN) deletes the 740 '<->' drawing-interruption tags that sit between glyphs, gluing 655 spurious compounds (mean 9.7 glyphs), and it deletes the 394 {..} ligature groups together with their glyphs. The '<->' positions behave like certain spaces (break score 0.7534 against 0.8161 for '.' and 0.0363 inside words). Reading them as breaks moves merged word-length variance 2.48 -> 2.12, pair violation 0.160 -> 0.145 and hapax 69.5 -> 67.7 %. Those are NOTES 4.2-4.4 figures, not only b1 figures.

## 1. Re-run of b1 as-is (11 Oct 2026)

- First attempt: FileNotFoundError, `data/ZL3b-n.txt` (the raw IVTFF file, git-ignored) was not on this machine. Once the coordinator fetched it ("Version 3b of 13/05/2025"; parse_ivtff.py reproduces the committed TSV), the full run took 14 s.
- `git diff --stat`: 633 changed lines in results/b1.json, 28 in results/b1.md. A field-by-field comparison of the JSON shows that every Part 1 value and every Latin Part 2 value is identical to the commit, apart from the runtimes. Only the six Italian rows and the Italian corpus counts moved.
- Why: `../vatican5/corpus_it.txt` here (26,486,052 bytes, identical to the main checkout's copy) holds the same Nuntiaturberichte OCR in a different document order. b1 takes "the first N tokens". The September sample began 'cumque predictus fcrdiuandu s rex nuper in romanorum regem', which sits at character 0 of this file. This file instead begins with OCR noise and German ('hitii hlf siifii ... die uerfruhte reise des bischofs'). As-is, the Italian rows come out as words 6758 types / 66.5 % hapax (committed 6758 / 66.5), syl 1718 / 44.2 (committed 1718 / 44.2).
- b1's own code, with the Italian text anchored at that offset, reproduces all six committed Italian rows exactly (anchored re-run, v_b1.json 'rerun_it_anchored'; independent check below: all agree).
- The working-tree results/b1.json and b1.md were restored to the committed versions after the re-run. As-is, they would carry the noisy file-start Italian sample. The as-is values are kept in v_b1.json 'rerun'.
- Consequence: "the first N tokens of corpus_it.txt" is not a stable sample definition across copies of that file. v_b1 anchors the Italian sample by its first words. Any script that reads IT_CORPUS from the start (a1, a3, a4, a5, b-series) needs the same check before its Italian rows are compared with September values.

## 2. Claims

Row values: types / hapax % types / length mean/var / Zipf 1-1000 / h2 with spaces / h2 no spaces / locked frac / MI symbol;position / pair-violation / length-matched pair-violation. "re-run" = b1 as-is on 11 Oct (Italian rows: b1 code on the anchored sample); "independent" = v_b1.py.

| claim in b1.md | b1 value | re-run value | independent value | verdict |
|---|---|---|---|---|
| Split re-parse reproduces the TSV; P lines | True; 4130 | True; 4130 | True; 4130 | confirmed |
| ALL: words before filter, dropped, N | 34310, {'?': 98, 'nonEVA': 153}, 34059 | 34310, {'?': 98, 'nonEVA': 153}, 34059 | 34310, {'?': 98, 'nonEVA': 153}, 34059 | confirmed |
| Uncertain spaces joined; CERTAIN before filter, dropped, N; words containing a join | 2458; 31852, {'?': 98, 'nonEVA': 152}, 31602; 2183 | 2458; 31852, {'?': 98, 'nonEVA': 152}, 31602; 2183 | 2458; 31852, {'?': 98, 'nonEVA': 152}, 31602; 2183 | confirmed (the raw P-line text holds 2464 commas, including any inside comments or next to deleted markup; 2458 of them join two words) |
| Joined words: n, mean raw length, share already ALL types | 2151, 7.85, 0.345 | same | 2151, 7.85, 0.345 | confirmed |
| Part 1 row ALL/raw | 7182 / 69.5 / 5.07/3.73 / -1.040 / 2.114 / 2.307 / 0.316 / 0.696 / 0.157 | 7182 / 69.5 / 5.07/3.73 / -1.040 / 2.114 / 2.307 / 0.316 / 0.696 / 0.157 | 7182 / 69.5 / 5.07/3.73 / -1.040 / 2.114 / 2.307 / 0.316 / 0.696 / 0.157 | confirmed |
| Part 1 row ALL/merge_a3 | 6897 / 69.1 / 4.11/2.48 / -1.056 / 2.341 / 2.635 / 0.240 / 0.690 / 0.160 | 6897 / 69.1 / 4.11/2.48 / -1.056 / 2.341 / 2.635 / 0.240 / 0.690 / 0.160 | 6897 / 69.1 / 4.11/2.48 / -1.056 / 2.341 / 2.635 / 0.240 / 0.690 / 0.160 | confirmed |
| Part 1 row ALL/merge2_a1 | 7182 / 69.5 / 3.80/2.36 / -1.040 / 2.505 / 2.865 / 0.355 / 0.713 / 0.175 | 7182 / 69.5 / 3.80/2.36 / -1.040 / 2.505 / 2.865 / 0.355 / 0.713 / 0.175 | 7182 / 69.5 / 3.80/2.36 / -1.040 / 2.505 / 2.865 / 0.355 / 0.713 / 0.175 | confirmed |
| Part 1 row CERTAIN/raw | 8102 / 72.8 / 5.46/4.06 / -1.005 / 2.127 / 2.307 / 0.368 / 0.663 / 0.175 / 0.161 | 8102 / 72.8 / 5.46/4.06 / -1.005 / 2.127 / 2.307 / 0.368 / 0.663 / 0.175 / 0.161 | 8102 / 72.8 / 5.46/4.06 / -1.005 / 2.127 / 2.307 / 0.368 / 0.663 / 0.175 / 0.162 | confirmed (length-matched value differs only by resampling draw, <=0.002) |
| Part 1 row CERTAIN/merge_a3 | 7792 / 72.4 / 4.43/2.79 / -1.018 / 2.360 / 2.635 / 0.240 / 0.662 / 0.179 / 0.162 | 7792 / 72.4 / 4.43/2.79 / -1.018 / 2.360 / 2.635 / 0.240 / 0.662 / 0.179 / 0.162 | 7792 / 72.4 / 4.43/2.79 / -1.018 / 2.360 / 2.634 / 0.240 / 0.662 / 0.179 / 0.163 | confirmed (length-matched value differs only by resampling draw, <=0.002) |
| Part 1 row CERTAIN/merge2_a1 | 8102 / 72.8 / 4.09/2.72 / -1.005 / 2.527 / 2.865 / 0.323 / 0.684 / 0.194 / 0.176 | 8102 / 72.8 / 4.09/2.72 / -1.005 / 2.527 / 2.865 / 0.323 / 0.684 / 0.194 / 0.176 | 8102 / 72.8 / 4.09/2.72 / -1.005 / 2.527 / 2.865 / 0.323 / 0.684 / 0.194 / 0.178 | confirmed (length-matched value differs only by resampling draw, <=0.002) |
| Part 1 row ALL_trunc/raw | 6810 / 69.4 / 5.06/3.74 / -1.038 / 2.118 / 2.313 / 0.316 / 0.696 / 0.159 | 6810 / 69.4 / 5.06/3.74 / -1.038 / 2.118 / 2.313 / 0.316 / 0.696 / 0.159 | 6810 / 69.4 / 5.06/3.74 / -1.038 / 2.118 / 2.313 / 0.316 / 0.696 / 0.159 | confirmed |
| Part 1 row ALL_trunc/merge_a3 | 6556 / 69.1 / 4.10/2.49 / -1.059 / 2.346 / 2.641 / 0.240 / 0.690 / 0.162 | 6556 / 69.1 / 4.10/2.49 / -1.059 / 2.346 / 2.641 / 0.240 / 0.690 / 0.162 | 6556 / 69.1 / 4.10/2.49 / -1.059 / 2.346 / 2.641 / 0.240 / 0.690 / 0.162 | confirmed |
| Part 1 row ALL_trunc/merge2_a1 | 6810 / 69.4 / 3.80/2.38 / -1.038 / 2.505 / 2.866 / 0.355 / 0.712 / 0.177 | 6810 / 69.4 / 3.80/2.38 / -1.038 / 2.505 / 2.866 / 0.355 / 0.712 / 0.177 | 6810 / 69.4 / 3.80/2.38 / -1.038 / 2.505 / 2.866 / 0.355 / 0.712 / 0.177 | confirmed |
| ALL -> CERTAIN movement: h2 no spaces, h2 with spaces, mean length, pair-viol as-is, pair-viol length-matched (merge-a3) | <=0.0006; +0.013 to +0.023; +0.29 to +0.39; +0.017 to +0.019; 0.1596 -> 0.1622 | same | <=0.0006; +0.013 to +0.023; +0.29 to +0.39; +0.017 to +0.019; 0.1596 -> 0.1618-0.1646 (10 seeds) | confirmed |
| Part 1 heading: ALL = "every IVTFF comma a break" | commas only | same | true for commas; but 740 '<->' breaks between glyphs are deleted (655 clean glued tokens) and 394 {..} ligature groups are dropped with their glyphs | corrected (see 3.1) |
| Corpora: words -> syllables, syllables/word, words spanned by N syllables | la_prose 135590 -> 281698, 2.078, 16004; la_verse 63791 -> 143406, 2.248, 15099; it 713709 -> 1313361, 1.84, 18757 | Latin same; it (file start) 699408 -> 1340563 | la_prose 135590 -> 281698, 2.078, 16004; la_verse 63791 -> 143406, 2.248, 15099; it (anchored, 4M chars) 708235 -> 1328747, 1.876, 18757 | Latin confirmed; Italian totals not reproducible (file order), the 18,757 words actually used confirmed |
| Syllabifier examples (17 words, syl and CV) | as listed | same | all identical: True | confirmed |
| Part 2 row la_prose/words | 9479 / 67.5 / 5.42/7.90 / -0.957 / 3.322 / 3.501 / 0.125 / 0.176 / 0.365 / 0.365 | 9479 / 67.5 / 5.42/7.90 / -0.957 / 3.322 / 3.501 / 0.125 / 0.176 / 0.365 / 0.365 | 9479 / 67.5 / 5.42/7.90 / -0.957 / 3.323 / 3.501 / 0.125 / 0.176 / 0.365 / 0.365 | confirmed |
| Part 2 row la_prose/syl | 1497 / 28.8 / 2.53/0.61 / -1.355 / 2.985 / 3.518 / 0.250 / 0.395 / 0.277 / 0.259 | 1497 / 28.8 / 2.53/0.61 / -1.355 / 2.985 / 3.518 / 0.250 / 0.395 / 0.277 / 0.259 | 1497 / 28.8 / 2.53/0.61 / -1.355 / 2.984 / 3.518 / 0.250 / 0.395 / 0.277 / 0.259 | confirmed |
| Part 2 row la_prose/cv | 119 / 5.9 / 1.83/0.14 / -1.731 / 2.112 / 3.225 / 0.875 / 0.992 / 0.000 / - | 119 / 5.9 / 1.83/0.14 / -1.731 / 2.112 / 3.225 / 0.875 / 0.992 / 0.000 / - | 119 / 5.9 / 1.83/0.14 / -1.731 / 2.112 / 3.225 / 0.875 / 0.991 / 0.000 / - | confirmed |
| Part 2 row la_prose/syl2 | 5831 / 47.1 / 3.96/1.95 / -0.872 / 3.289 / 3.507 / 0.000 / 0.166 / 0.372 / 0.363 | 5831 / 47.1 / 3.96/1.95 / -0.872 / 3.289 / 3.507 / 0.000 / 0.166 / 0.372 / 0.363 | 5831 / 47.1 / 3.96/1.94 / -0.872 / 3.289 / 3.507 / 0.000 / 0.166 / 0.372 / 0.363 | confirmed |
| Part 2 row la_prose/cv2 | 2321 / 25.2 / 2.87/1.18 / -0.956 / 2.706 / 3.218 / 0.042 / 0.492 / 0.271 / 0.294 | 2321 / 25.2 / 2.87/1.18 / -0.956 / 2.706 / 3.218 / 0.042 / 0.492 / 0.271 / 0.294 | 2321 / 25.2 / 2.87/1.18 / -0.956 / 2.706 / 3.218 / 0.042 / 0.492 / 0.271 / 0.293 | confirmed (length-matched value differs only by resampling draw, <=0.002) |
| Part 2 row la_prose/syl_shuf | 4346 / 52.2 / 2.53/0.61 / -1.054 / 3.405 / 3.893 / 0.000 / 0.036 / 0.488 / 0.459 | 4346 / 52.2 / 2.53/0.61 / -1.054 / 3.405 / 3.893 / 0.000 / 0.036 / 0.488 / 0.459 | 4366 / 53.2 / 2.53/0.61 / -1.050 / 3.403 / 3.891 / 0.000 / 0.038 / 0.489 / 0.453 | null row; own shuffle seed, values agree to +-0.01 (pair-viol 0.49 vs 0.49) |
| Part 2 row la_verse/words | 11368 / 59.9 / 5.76/4.88 / -0.698 / 3.364 / 3.509 / 0.091 / 0.177 / 0.360 / 0.363 | 11368 / 59.9 / 5.76/4.88 / -0.698 / 3.364 / 3.509 / 0.091 / 0.177 / 0.360 / 0.363 | 11368 / 59.9 / 5.76/4.88 / -0.698 / 3.364 / 3.509 / 0.091 / 0.177 / 0.360 / 0.361 | confirmed (length-matched value differs only by resampling draw, <=0.002) |
| Part 2 row la_verse/syl | 1509 / 25.4 / 2.56/0.56 / -1.257 / 2.975 / 3.511 / 0.182 / 0.421 / 0.260 / 0.192 | 1509 / 25.4 / 2.56/0.56 / -1.257 / 2.975 / 3.511 / 0.182 / 0.421 / 0.260 / 0.192 | 1509 / 25.4 / 2.56/0.56 / -1.257 / 2.975 / 3.511 / 0.182 / 0.421 / 0.260 / 0.191 | confirmed (length-matched value differs only by resampling draw, <=0.002) |
| Part 2 row la_verse/cv | 101 / 1.0 / 1.86/0.12 / -1.296 / 2.115 / 3.228 / 0.864 / 1.004 / 0.000 / - | 101 / 1.0 / 1.86/0.12 / -1.296 / 2.115 / 3.228 / 0.864 / 1.004 / 0.000 / - | 101 / 1.0 / 1.86/0.12 / -1.296 / 2.115 / 3.227 / 0.864 / 1.004 / 0.000 / - | confirmed |
| Part 2 row la_verse/syl2 | 6817 / 44.1 / 4.17/1.93 / -0.715 / 3.319 / 3.510 / 0.000 / 0.180 / 0.359 / 0.354 | 6817 / 44.1 / 4.17/1.93 / -0.715 / 3.319 / 3.510 / 0.000 / 0.180 / 0.359 / 0.354 | 6817 / 44.1 / 4.17/1.93 / -0.715 / 3.319 / 3.510 / 0.000 / 0.180 / 0.359 / 0.354 | confirmed |
| Part 2 row la_verse/cv2 | 2521 / 22.8 / 3.03/1.00 / -0.848 / 2.758 / 3.225 / 0.000 / 0.474 / 0.277 / 0.297 | 2521 / 22.8 / 3.03/1.00 / -0.848 / 2.758 / 3.225 / 0.000 / 0.474 / 0.277 / 0.297 | 2521 / 22.8 / 3.03/1.00 / -0.848 / 2.758 / 3.225 / 0.000 / 0.474 / 0.277 / 0.297 | confirmed |
| Part 2 row la_verse/syl_shuf | 4609 / 53.4 / 2.56/0.56 / -1.002 / 3.423 / 3.890 / 0.000 / 0.028 / 0.489 / 0.405 | 4609 / 53.4 / 2.56/0.56 / -1.002 / 3.423 / 3.890 / 0.000 / 0.028 / 0.489 / 0.405 | 4635 / 53.6 / 2.56/0.56 / -1.002 / 3.421 / 3.891 / 0.000 / 0.028 / 0.488 / 0.398 | null row; own shuffle seed, values agree to +-0.01 (pair-viol 0.49 vs 0.49) |
| Part 2 row it/words | 6758 / 66.5 / 4.54/6.58 / -1.024 / 3.205 / 3.451 / 0.048 / 0.221 / 0.351 / 0.318 | 6758 / 66.5 / 4.54/6.58 / -1.024 / 3.205 / 3.451 / 0.048 / 0.221 / 0.351 / 0.318 | 6758 / 66.5 / 4.54/6.58 / -1.024 / 3.205 / 3.451 / 0.048 / 0.221 / 0.351 / 0.317 | confirmed (length-matched value differs only by resampling draw, <=0.002) |
| Part 2 row it/syl | 1718 / 44.2 / 2.50/0.74 / -1.439 / 2.831 / 3.450 / 0.190 / 0.428 / 0.216 / 0.259 | 1718 / 44.2 / 2.50/0.74 / -1.439 / 2.831 / 3.450 / 0.190 / 0.428 / 0.216 / 0.259 | 1718 / 44.2 / 2.50/0.74 / -1.439 / 2.831 / 3.449 / 0.190 / 0.428 / 0.216 / 0.259 | confirmed |
| Part 2 row it/cv | 100 / 4.0 / 1.85/0.13 / -1.614 / 2.053 / 3.119 / 0.762 / 0.988 / 0.000 / - | 100 / 4.0 / 1.85/0.13 / -1.614 / 2.053 / 3.119 / 0.762 / 0.988 / 0.000 / - | 100 / 4.0 / 1.85/0.13 / -1.614 / 2.053 / 3.119 / 0.762 / 0.988 / 0.000 / - | confirmed |
| Part 2 row it/syl2 | 4941 / 55.0 / 3.71/2.62 / -0.979 / 3.135 / 3.446 / 0.048 / 0.239 / 0.330 / 0.335 | 4941 / 55.0 / 3.71/2.62 / -0.979 / 3.135 / 3.446 / 0.048 / 0.239 / 0.330 / 0.335 | 4941 / 55.0 / 3.71/2.62 / -0.979 / 3.135 / 3.446 / 0.048 / 0.239 / 0.330 / 0.336 | confirmed |
| Part 2 row it/cv2 | 1996 / 30.9 / 2.74/1.20 / -1.130 / 2.591 / 3.116 / 0.048 / 0.562 / 0.246 / 0.281 | 1996 / 30.9 / 2.74/1.20 / -1.130 / 2.591 / 3.116 / 0.048 / 0.562 / 0.246 / 0.281 | 1996 / 30.9 / 2.74/1.20 / -1.130 / 2.591 / 3.116 / 0.048 / 0.562 / 0.246 / 0.280 | confirmed |
| Part 2 row it/syl_shuf | 4354 / 59.4 / 2.50/0.74 / -1.145 / 3.325 / 3.795 / 0.000 / 0.024 / 0.491 / 0.479 | 4354 / 59.4 / 2.50/0.74 / -1.145 / 3.325 / 3.795 / 0.000 / 0.024 / 0.491 / 0.479 | 4325 / 57.9 / 2.50/0.74 / -1.149 / 3.326 / 3.797 / 0.000 / 0.024 / 0.487 / 0.477 | null row; own shuffle seed, values agree to +-0.01 (pair-viol 0.49 vs 0.49) |
| Match table: cv rows give h2 with spaces 2.053-2.115 against Voynich raw 2.114 | 2.112 / 2.115 / 2.053 | same | 2.112 / 2.115 / 2.053; a random C/V/CV generator with no language gives 2.157 / 2.147 / 2.101; without spaces cv h2 = 3.225 / 3.227 / 3.119 (Voynich 2.307) | numbers confirmed; reading corrected: a match by construction, no evidence (3.3) |
| Match table: syl2 length 3.71-4.17 inside 'len mean vs 4.1-5.1' | 3.96 / 4.17 / 3.71 | same | 3.96 / 4.17 / 3.71 = syllable length x 1.57 / 1.63 / 1.48 syllables per chunk | confirmed; by construction (the chunk size was chosen to match) |
| Match table: syllable pair-viol length-matched 0.259 / 0.192 / 0.259 against 0.160 | as stated | same | 0.259 (10 seeds 0.258-0.2616) / 0.191 (10 seeds 0.1882-0.1911) / 0.259 (10 seeds 0.2553-0.2607) | confirmed as numbers; la_verse 0.19 is a tail artefact (0.255 on lengths 1-5), see 3.4; the per-length gap is larger |
| Match table targets: hapax 69-70 %, locked 0.21-0.31, MI 0.69-0.73 | as stated | same | b1's own Voynich rows: hapax 69.1-69.5, locked 0.24 / 0.316 / 0.355 (merge-a3 / raw / merge2), MI 0.690-0.713; with '<->' as a break hapax 67.3-67.7, MI 0.718-0.721 | corrected (range 0.24-0.36; 0.21-0.31 is v_a5's merged/Currier/v101 range) |

## 3. Method critique

### 3.1 IVTFF parse

Commas against periods: correct. In IVTFF '.' is a certain word space and ',' an uncertain one; P text has 27730 periods and 2464 commas. The boundary score below puts commas at 0.4715 (half of them look like breaks, 0.5416), between certain spaces (0.8161) and word-internal glyph pairs (0.0363). That is what 'uncertain' should look like, and it means ALL and CERTAIN are the two extremes; the truth lies between them. Because nothing moves much from one extreme to the other, the bracketing is enough.

Two other markups are mishandled, here and in parse_ivtff.py, so in every a- and b-script number:

- `<->` (drawing interruption): 746 in P text, 740 directly between two glyphs, 0 next to a separator. Deleting the tag glues the flanking pieces: 655 clean tokens, mean 9.7 raw glyphs, e.g. ochydcho, shydksheey, damsochey, cphoaldar, okaldolchey, ctheyykol, kychol, darshol, chodyschody, otchalypchaiin. The two halves look like ordinary words (ochy|dcho, dam|sochey, okal|dolchey, cthey|ykol). Boundary score at the 738 scored '<->' positions: 0.7534 (0.8211 above one half), close to '.' and far from within-word. They are word breaks.
- `{..}` (ligature / unusual glyph groups, e.g. {ikh}, {cthh}, {ch'}, {ith}, {ckhh}, {ck}): 394 in P text, 16 of them a whole word. The regex `\{[^}]*\}` -> '' drops the glyphs, so '{ck}eo' becomes 'eo'. These are glyphs, not comments; inline comments are `<!..>`.

| parse | tokens | types | hapax % | merged len mean/var | var/(mean-1) merged | h2 merged | pair-viol merged | locked merged | MI merged |
|---|---|---|---|---|---|---|---|---|---|
| b1 ALL (TSV) | 34059 | 7182 | 69.5 | 4.111/2.480 | 0.797 | 2.635 | 0.1596 | 0.240 | 0.690 |
| '<->' = break | 34800 | 6804 | 67.1 | 4.024/2.120 | 0.701 | 2.635 | 0.1442 | 0.280 | 0.717 |
| braces kept | 33974 | 7296 | 70.0 | 4.132/2.494 | 0.796 | 2.646 | 0.1605 | 0.259 | 0.692 |
| both fixed | 34719 | 6934 | 67.7 | 4.045/2.122 | 0.697 | 2.646 | 0.1450 | 0.296 | 0.718 |
| b1 CERTAIN | 31602 | 8102 | 72.8 | 4.427/2.793 | 0.815 | 2.634 | 0.1787 | 0.240 | 0.662 |
| CERTAIN, both fixed | 32260 | 7893 | 71.3 | 4.349/2.345 | 0.700 | 2.645 | 0.1640 | 0.259 | 0.687 |

Consequence for b1: the ALL vs CERTAIN contrast keeps its sign and size (CERTAIN_fix vs ALL_fix: hapax 67.7 -> 71.3, length-matched pair violation 0.145 -> 0.161). The absolute Voynich figures quoted in NOTES move, though: merged word-length variance 2.48 -> 2.12 (dispersion 0.797 -> 0.697, so even more under-dispersed), pair violation 0.160 -> 0.145 (more rigid), hapax 69.5 -> 67.7 %, merged locked fraction 0.24 -> 0.30, MI 0.690 -> 0.718. h2 does not move (<= 0.011). Variance, rigidity, locking and MI move away from language. Hapax moves toward it: 67.7 % is inside v_a5's single-book range (57.0-68.7 %), so the remark that Voynich hapax is 'above every language' no longer holds. No exclusion verdict depends on hapax, but the 4.2-4.4 tables should be regenerated from a corrected TSV (outside this check: parse_ivtff.py is not b1).

### 3.2 Syllabifier

The rule as documented is the rule as coded: my implementation, written from the docstring, reproduces every syllable count, the 17 examples and every syl/cv/syl2/cv2 row. As a syllabifier it has three defects; only the second is documented:

- 'æ' and 'œ' are not vowels. The Confessiones edition prints them: 684 of the first 16,004 words (4.3 %) contain one. 'quæ' -> one vowel-less syllable 'quæ', CV 'q'; 'vitæ' -> 'vitæ'; 'sæculorum' -> 'sæcu lo rum'. This is undocumented.
- A maximal vowel run is one nucleus, so hiatus is never split ('confessiones' -> 'sio', 'misericordia' -> 'dia'): 9.1% / 10.1% / 14.3% of nuclei (prose / verse / Italian) have two or more vowel letters. This one is documented.
- The Italian corpus spells v as u ('auere', 'uenire'), so 'auere' -> 'aue re' and 'uenire' -> 'ue ni re'.

Corrected variant (ligatures folded to ae/oe; hiatus split except Latin ae oe au eu and the Italian glides; Italian u before a vowel at word start or after a vowel read as v):

| corpus/variant | b1 rule: types / hapax / len / h2 sp / pair-viol lm | corrected rule: same |
|---|---|---|
| la_prose/syl | 1497 / 28.8 / 2.53 / 2.984 / 0.259 | 925 / 18.5 / 2.33 / 2.890 / 0.207 |
| la_prose/cv | 119 / 5.9 / 1.83 / 2.112 / - | 113 / 6.2 / 1.77 / 2.116 / - |
| la_prose/syl2 | 5831 / 47.1 / 3.96 / 3.289 / 0.363 | 5076 / 43.2 / 3.75 / 3.249 / 0.354 |
| la_prose/cv2 | 2321 / 25.2 / 2.87 / 2.706 / 0.293 | 2333 / 25.5 / 2.84 / 2.773 / 0.285 |
| la_verse/syl | 1509 / 25.4 / 2.56 / 2.975 / 0.191 | 1023 / 16.5 / 2.40 / 2.913 / 0.247 |
| la_verse/cv | 101 / 1.0 / 1.86 / 2.115 / - | 101 / 1.0 / 1.81 / 2.128 / - |
| la_verse/syl2 | 6817 / 44.1 / 4.17 / 3.319 / 0.354 | 6180 / 41.7 / 3.95 / 3.294 / 0.357 |
| la_verse/cv2 | 2521 / 22.8 / 3.03 / 2.758 / 0.297 | 2609 / 22.8 / 2.98 / 2.816 / 0.291 |
| it/syl | 1718 / 44.2 / 2.50 / 2.831 / 0.259 | 1326 / 38.7 / 2.40 / 2.778 / 0.275 |
| it/cv | 100 / 4.0 / 1.85 / 2.053 / - | 105 / 3.8 / 1.86 / 2.093 / - |
| it/syl2 | 4941 / 55.0 / 3.71 / 3.135 / 0.336 | 4639 / 52.9 / 3.60 / 3.114 / 0.333 |
| it/cv2 | 1996 / 30.9 / 2.74 / 2.591 / 0.280 | 2184 / 32.6 / 2.79 / 2.665 / 0.284 |

The syllabifier choices move the length-matched pair violation of syllables by up to 0.06 in either direction and syllable types by up to 38 %. Every variant stays far from Voynichese on vocabulary (types, hapax, Zipf) and on length-matched rigidity (0.21-0.36 against 0.16). The defects are real but do not change the conclusion.

### 3.3 Is a match with Voynich non-trivial or built in?

- **cv and h2 with spaces: built in.** A CV token is consonant + vowel, then a space. After a vowel the next symbol is always the space, which is 0 bits at 35% of positions. h2 with spaces is then P(space) x H(first letter) + P(consonant) x H(vowel | consonant) = 1.47 + 0.64 bits for Latin prose (verse 1.44 + 0.67, Italian 1.40 + 0.65). Drawing every letter independently into the same C/V/CV shapes, with no language at all, gives 2.157 / 2.147 / 2.101 (prose / verse / Italian). Without spaces the cv streams have h2 3.12-3.23, Voynich 2.31. Voynich reaches its 2.114 by a different route: space 0.53, vowel-class 0.82, consonant-class 0.76 bits. The cv rows also have 100-119 types, 1-6 % hapax and MI about 1.0: they match nothing else.
- **cv and pair violation 0.000: built in.** A two-symbol C+V token cannot violate a C-before-V order. b1 already prints it as "as-is" with no length-matched value.
- **syl2 and length: built in.** Mean syl2 length = mean syllable length (2.50-2.56) x syllables per chunk (1.57 / 1.63 / 1.48). The docstring says the chunking was added to test hypothesis (a). That is legitimate, but the length agreement it buys is not evidence.
- **syl and syl2, everything else: not built in.** These rows are honest tests and they fail: syllables give 1,497-1,718 types and 25-44 % hapax against 7,182 and 69.5 %, Zipf -1.26 to -1.44 against -1.04, and h2 with spaces 2.83-2.99. Bisyllabic chunks give 4,941-6,817 types, 44-55 % hapax and h2 with spaces 3.13-3.32. MI is 0.17-0.43 against 0.69-0.71. Locking is 0-0.25; only Latin prose syllables (0.25) reach the Voynich range of 0.24-0.36.
- **Rigidity depends on the cut rule.** An open-syllable cut (every consonant cluster goes to the next onset) gives pair violation 0.221 / 0.202 / 0.146 as-is and 0.265 / 0.232 / 0.229 length-matched. v_a3's cut after every vowel gave 0.108 length-matched, more rigid than Voynich. So syllabic units can be made more or less rigid than Voynichese by choosing the cut. A pair-violation mismatch alone would not exclude syllabic writing; the vocabulary statistics do.

### 3.4 Length-matched pair violation

The procedure is fair in form: the same resampler and the same order refit as the Voynich and v_a3 controls, with the order fitted on the resampled sample. It is weak for sub-word units. 16.4% of Voynich merged tokens have 6 or more symbols. In the Aeneid syllable pool there are 21 syllable types of length 6 and 1 of length 7, so one sixth of the "length-matched" sample is about 22 syllables drawn over and over. Most of them are artefacts of the undivided vowel run (troiae, troiam, graius, graiae, aeaeae, proiec). Matched on lengths 1-5 only, la_verse/syl scores 0.255, not 0.191. Under the global order it is 0.21-0.31 at every length from 2 to 5. cv2 has nothing longer than 4 symbols (cov 0.62), so the 38 % of the target that has length 5 or more is filled with length-4 tokens; it is not length-matched. More seeds do not help: the 10-seed spread is <= 0.006, because the bias is structural. The fair comparison is per length with the order refitted at each length (no resampling):

| corpus | L2 | L3 | L4 | L5 | L6 |
|---|---|---|---|---|---|
| ZL ALL merge-a3 | 0.022 (124) | 0.059 (509) | 0.125 (1289) | 0.135 (1798) | 0.148 (1608) |
| ZL ALL raw | 0.033 (71) | 0.089 (236) | 0.090 (598) | 0.108 (1166) | 0.136 (1526) |
| la_prose/words | 0.124 (40) | 0.208 (168) | 0.280 (408) | 0.346 (841) | 0.333 (1138) |
| la_prose/syl | 0.173 (141) | 0.246 (623) | 0.239 (507) | 0.267 (151) | 0.197 (43) |
| la_prose/syl2 | 0.169 (79) | 0.259 (418) | 0.353 (1256) | 0.366 (2085) | 0.332 (1338) |
| la_prose/cv2 | 0.000 (88) | 0.365 (274) | 0.267 (1939) | - | - |
| la_prose/open-syllable cut | 0.087 (116) | 0.200 (685) | 0.227 (694) | 0.226 (253) | 0.256 (58) |
| la_verse/words | 0.079 (36) | 0.178 (140) | 0.298 (577) | 0.338 (1473) | 0.350 (2035) |
| la_verse/syl | 0.152 (141) | 0.236 (664) | 0.228 (550) | 0.244 (127) | 0.077 (21) |
| la_verse/syl2 | 0.149 (76) | 0.230 (431) | 0.348 (1478) | 0.365 (2400) | 0.335 (1736) |
| la_verse/cv2 | 0.000 (84) | 0.318 (299) | 0.274 (2132) | - | - |
| la_verse/open-syllable cut | 0.065 (119) | 0.185 (743) | 0.222 (842) | 0.277 (242) | 0.191 (45) |
| it/words | 0.050 (138) | 0.113 (374) | 0.252 (551) | 0.309 (938) | 0.294 (990) |
| it/syl | 0.131 (161) | 0.177 (724) | 0.199 (527) | 0.275 (198) | 0.205 (62) |
| it/syl2 | 0.080 (135) | 0.143 (449) | 0.319 (1088) | 0.334 (1613) | 0.311 (1022) |
| it/cv2 | 0.000 (76) | 0.307 (247) | 0.267 (1653) | - | - |
| it/open-syllable cut | 0.072 (138) | 0.106 (705) | 0.160 (580) | 0.271 (225) | 0.221 (74) |

(types of that length in brackets.) At every length from 2 to 5, Latin and Italian syllables are 1.6 to 8 times less rigid than merged Voynichese (2 to 5 times against raw EVA). The open-syllable cut comes closest, Italian at length 4 (0.160 against 0.125), and still falls short at every length.

### 3.5 A real CV-rigid language (extension, not in b1)

NOTES section 2 names 'a language with rigid consonant-vowel syllables written syllabically'. b1 approximates it by deleting letters from Latin (cv); that destroys the vocabulary and makes the cv rows uninformative. data/corpora holds a Hawaiian Bible in the missionary orthography ((C)V only; 7 native consonant letters, about 2 % foreign letters in names, no okina or macrons; starts 'kinohi i kinohi hana ke akua i ka lani a me ka') and a Maori Bible (macrons folded, wh/ng as one symbol). Same battery, same N:

| corpus | types | hapax % | len mean/var | Zipf | h2 sp | h2 | locked | MI | pair-viol | length-matched |
|---|---|---|---|---|---|---|---|---|---|---|
| haw/words | 1266 | 37.3 | 3.08/4.54 | -1.526 | 2.589 | 2.850 | 0.050 | 0.364 | 0.336 | 0.318 |
| haw/mora | 81 | 6.2 | 1.57/0.24 | -2.304 | 1.784 | 2.843 | 0.750 | 0.990 | 0.000 | - |
| haw/syl | 147 | 10.9 | 1.75/0.35 | -2.192 | 1.920 | 2.846 | 0.750 | 0.889 | 0.000 | 0.000 |
| haw/syl2 | 926 | 27.6 | 2.56/1.36 | -1.634 | 2.445 | 2.848 | 0.050 | 0.449 | 0.236 | 0.238 |
| mri/words | 1463 | 33.8 | 3.20/3.89 | -1.366 | 2.542 | 2.827 | 0.000 | 0.458 | 0.297 | 0.294 |
| mri/mora | 52 | 0.0 | 1.68/0.22 | -1.459 | 1.817 | 2.823 | 0.667 | 0.999 | 0.000 | - |
| mri/syl | 116 | 6.0 | 1.83/0.31 | -2.008 | 1.895 | 2.822 | 0.733 | 1.000 | 0.000 | 0.000 |
| mri/syl2 | 920 | 21.2 | 2.72/1.57 | -1.578 | 2.428 | 2.825 | 0.067 | 0.531 | 0.236 | 0.235 |
| ZL ALL raw / merge-a3 | 7182 / 6897 | 69.5 | 5.07/3.73 | -1.040 | 2.114 / 2.341 | 2.307 / 2.635 | 0.316 / 0.24 | 0.696 | 0.157 / 0.160 | - |

A real CV language written syllabically reaches Voynich-level h2 with spaces and below (syllables 1.9, pairs 2.4), with more positional locking than Voynich (0.67-0.75 against 0.24-0.36). It does so with 116-147 syllable types and 6-11 % hapax, and even its ordinary words give only 1266-1463 types (h2 2.83-2.85; the published Hawaiian figure is 2.77). Its syllable pairs are less rigid than Voynichese, length-matched (0.24 against 0.16). Caveat: both texts are Bibles, a repetitive genre, and the comparison is two languages, not a survey.

### 3.6 Corpus cleanliness

The file-start Italian sample (OCR noise, some German) raises hapax to 66.5 % for words and 55.0 % for syllable pairs, above Voynich's 69.5 %. Vocabulary statistics measure the text's noise as much as its language. The vocabulary argument above rests on clean corpora (Gutenberg Latin, the Bibles, the anchored Italian sample, which still contains about 8 % Latin per v_a3). The same caution applies to Voynich's own 69.5 %: transcription disagreement inflates it too (SOURCES: 45 % of running tokens differ across transcribers).

### 3.7 Does b1.md overstate?

b1.md states no conclusion in prose: it has two tables and a match table. The risk is in how the match table reads. It puts cv h2 with spaces (2.05-2.12) beside 'Voy 2.114', and syl2 length inside the 4.1-5.1 target, with no note that both agreements are built into the token shape. Its target line gives hapax 69.7 (NOTES's a2-filter figure; b1's own rows are 69.1-69.5) and locked 0.21-0.31 (b1's own Voynich rows are 0.24-0.36). The docstring's 'syllabically written Latin' is Latin syllables spelled in the Latin alphabet and used as tokens. It is not a syllabary (one sign per syllable), which a 19-33 glyph inventory could not carry for Latin's 1,500 syllables or even Hawaiian's 147 without glyph groups. The glyph-group case is hypothesis (a), still open.

## 4. Corrected wording

For a b1 summary, and for NOTES section 2 where it says the segmentation gap "was not tested":

> b1 and v_b1 (October 2026) closed the two untested cases. (i) Uncertain spaces: joining all 2,458 IVTFF commas that separate words (CERTAIN) changes h2 by at most 0.023 bits and length-matched pair violation by +0.002 to +0.005 (0.160 -> 0.162-0.165). Hapax rises 69.5 -> 72.8 % and mean word length by 0.3-0.4 symbols. The commas themselves sit halfway between word breaks and word-internal junctures, so ALL and CERTAIN bracket the truth. (ii) Syllabic writing: Latin prose, Latin verse and Italian written as syllables, as CV syllables or as bisyllabic chunks, and Hawaiian and Maori written as morae or syllables, reproduce no Voynich profile. Syllable-sized tokens give 50-1,700 types and 0-44 % hapax at 34,059 tokens (Voynich 7,182 and 69.5 %), and Zipf -1.26 to -2.30 (Voynich -1.04). At every length from 2 to 5, Latin and Italian syllables are 1.6 to 8 times less rigid than merged Voynichese. The only exact-looking agreements, CV syllables on h2 with spaces and bisyllabic chunks on mean length, are fixed by the token shape (a random C/V/CV generator gives the same h2). Voynich tokens behave like words in their vocabulary and like a rigid template inside. The exclusion now covers syllable-as-token writing of Latin, Italian and two CV-rigid languages. A script in which glyph groups spell syllables inside word-sized tokens is hypothesis (a) and stays live.

Add to NOTES section 3: the ZL parse deletes the 746 '<->' drawing-interruption tags (740 between glyphs, behaving as word breaks) and the 394 {..} ligature groups with their glyphs. Re-parsed, merged length variance is 2.12 (not 2.48), pair violation 0.145 (not 0.160) and hapax 67.7 % (not 69.5 in this filter, 69.7 in a2's). The first two move away from language. Hapax moves into the single-book language range (57.0-68.7 %, v_a5), so 'Voynich hapax is above every language' should be dropped. Until parse_ivtff.py is fixed and a1-a6 are re-run, quote these as 'about'.

## 5. Checked / not checked

**Checked.** b1 re-run as-is: Part 1 and the Latin rows are identical to the commit. The Italian rows are identical once the sample is anchored at the September start, and differ as-is because corpus_it.txt is in a different document order. Independently re-implemented and matched: the IVTFF P-locus parse (split mode = TSV token list), the CERTAIN join counts, the a3/a1 glyph merges, the clean filter, entropies with and without spaces and within words, Zipf, length statistics, positional lock and MI, the pair-violation linear-order cost (own search with 42 starts gives b1's figure to 3 decimals in every non-shuffled row, so b1's 12-restart search is not under-optimised), the length-matched resampler (10 seeds), and the syllabifier against all 17 examples and every syllable count. Attacks run: IVTFF markup audit and corrected parse; boundary-likeness of '.', ',' and '<->'; h2 decomposition and a language-free CV generator; syllabifier sensitivity; open-syllable cut; per-length pair violation with refit; Hawaiian and Maori controls; corpus-order and corpus-noise sensitivity of the Italian rows.

**Not checked.** Corpora other than the three b1 uses plus the two Bibles. The Bible files were in data/corpora on 11 Oct; I did not verify their provenance beyond the first words. Per-Currier-language splits of CERTAIN. Whether '<->' was ever meant to be a word space in the IVTFF definition: the evidence here is statistical, and the IVTFF 2.0 PDF was not consulted. The effect of the corrected parse on a1-a6 beyond the statistics listed in 3.1. Syllabification against a dictionary (the variants are rule-based both ways).

**User must verify.** Whether to regenerate the TSV with '<->' as a break and braces kept, and re-run a1-a6/b1 (it changes NOTES 4.2-4.4 figures); which Italian sample is canonical (anchor by first words or ship a fixed sample file); the corrected wording in section 4 before it goes into NOTES. All output unvalidated until user review.

