# v_a6: adversarial re-check of a6_structure.py
P tokens: A=10768, B=22905, all P=34212 (a6 reported 10768 / 22905 / 34212).

## A. Data hygiene
96 of 34212 P tokens (0.28%) contain non-letters (IVTFF '@nnn;' codes, apostrophes): e.g. ['@192;chy', '@130;tol', "qo'ky", "e'a'iin", '@163;schoraiin', "q'o", '@135;otchoshor', '@135;odaiin']. Negligible for rates, but they are spurious 'types' in the sharing statistics.

## B. Sub-word rates (% tokens A / B)
| feature | ZL P (a6 set) | ZL all loci | Takahashi IT2a P |
|---|---|---|---|
| ends -edy | 0.2 / 17.34 | 0.19 / 17.08 | 0.2 / 17.57 |
| contains ed | 0.29 / 20.84 | 0.29 / 20.69 | 0.33 / 21.09 |
| ends -eedy | 0.07 / 5.11 | 0.06 / 5.02 | 0.08 / 5.18 |
| starts l- | 0.81 / 5.75 | 0.81 / 5.63 | 0.63 / 5.61 |
| ends -ain | 2.12 / 5.95 | 2.14 / 5.79 | 2.09 / 6.22 |
| ends -dy | 6.19 / 23.72 | 6.29 / 23.55 | 6.28 / 24.07 |
| starts qo- | 9.99 / 17.72 | 9.75 / 17.19 | 10.25 / 17.94 |
| contains ee | 7.36 / 14.9 | 7.3 / 14.67 | 7.5 / 15.07 |
| contains cho | 16.12 / 2.7 | 15.93 / 2.63 | 16.51 / 2.79 |
| ends -or | 10.42 / 3.84 | 10.32 / 3.92 | 10.96 / 4.06 |
| ends -ol | 14.52 / 7.08 | 14.36 / 7.0 | 15.0 / 7.53 |
| starts d- | 14.74 / 6.61 | 14.63 / 6.68 | 15.11 / 6.73 |
| gallows in bench | 9.12 / 4.02 | 8.98 / 3.92 | 9.92 / 4.28 |
| contains eo | 11.22 / 6.92 | 11.18 / 6.77 | 11.65 / 7.1 |
After 'ch' (n, % by next char): A (3844, {'o': 46.1, 'e': 24.5, 'y': 15.0, 'a': 6.8, 'c': 2.3, 'k': 1.6}), B (6135, {'e': 60.1, 'd': 11.5, 'o': 10.1, 'y': 5.5, 'c': 5.3, 'a': 3.1}); after 'sh': A (1353, {'o': 47.2, 'e': 31.3, 'y': 11.2, 'a': 4.7, 'c': 1.9, '$': 1.3}), B (2830, {'e': 70.8, 'o': 9.9, 'd': 5.7, 'c': 4.3, 'y': 3.9, 'a': 2.6})

## C. Per-folio separation (197 labelled folios with >=30 P tokens)
- ends -edy: A max 2.42 (median 0.0), B min 3.23 (median 14.33); leave-one-out threshold accuracy 99.5%; extreme A [('f89r1', 2.42), ('f88v', 2.31), ('f89r2', 1.42)], lowest B [('f55r', 3.23), ('f86v5', 3.6), ('f95v2', 3.64)]; histogram (2%-bins) {'0-2': 112, '2-4': 5, '4-6': 2, '6-8': 7, '8-10': 8, '10-12': 10, '12-14': 8, '14-16': 12, '16-18': 4, '18-20': 4, '20-22': 2, '22-24': 6, '24-26': 3, '26-28': 1, '28-30': 4, '30-32': 2, '32-34': 4, '36-38': 1, '38-40': 1, '40-42': 1}
- contains ed: A max 3.7 (median 0.0), B min 3.86 (median 17.95); leave-one-out threshold accuracy 99.5%; extreme A [('f27v', 3.7), ('f89r1', 2.42), ('f89r2', 2.37)], lowest B [('f86v5', 3.86), ('f55r', 4.03), ('f33v', 5.43)]; histogram (2%-bins) {'0-2': 110, '2-4': 5, '4-6': 2, '6-8': 3, '8-10': 7, '10-12': 6, '12-14': 8, '14-16': 8, '16-18': 7, '18-20': 6, '20-22': 4, '22-24': 3, '24-26': 7, '26-28': 3, '28-30': 5, '30-32': 2, '32-34': 1, '34-36': 5, '36-38': 1, '38-40': 2, '42-44': 1, '48-50': 1}
- contains cho: A max 40.59 (median 17.54), B min 0.0 (median 2.55); leave-one-out threshold accuracy 95.4%; extreme A [('f56r', 40.59), ('f49v', 40.15), ('f2v', 40.0)], lowest B [('f26v', 0.0), ('f31r', 0.0), ('f40r', 0.0)]; histogram (2%-bins) {'0-2': 35, '2-4': 31, '4-6': 16, '6-8': 9, '8-10': 18, '10-12': 7, '12-14': 11, '14-16': 8, '16-18': 9, '18-20': 7, '20-22': 17, '22-24': 7, '24-26': 9, '26-28': 1, '28-30': 2, '30-32': 5, '32-34': 1, '34-36': 1, '40-42': 3}
- ends -dy: A max 21.54 (median 5.36), B min 11.09 (median 23.53); leave-one-out threshold accuracy 92.9%; extreme A [('f88v', 21.54), ('f93v', 20.29), ('f11v', 18.18)], lowest B [('f107r', 11.09), ('f80r', 11.29), ('f111v', 12.74)]; histogram (2%-bins) {'0-2': 17, '2-4': 25, '4-6': 25, '6-8': 15, '8-10': 14, '10-12': 6, '12-14': 14, '14-16': 8, '16-18': 5, '18-20': 5, '20-22': 10, '22-24': 15, '24-26': 6, '26-28': 5, '28-30': 3, '30-32': 6, '32-34': 6, '34-36': 2, '36-38': 4, '38-40': 3, '40-42': 2, '46-48': 1}

## Corpus check (Gutenberg markers found in all used files; English function words per 1000 in first nA words; first words)
- da_24747: n=53382, eng fw/1000=9.6, starts 'produced by louise hope steen christensen and the online distributed proofreading team'
- da_36942: n=70157, eng fw/1000=7.6, starts 'johannes v jensen kongens fald gyldendalske boghandel nordisk forlag kjøbenhavn kristiania london'
- no_30027: n=60299, eng fw/1000=12.1, starts 'transcriber s note spelling in this first edition of sult old spelling'
- sv_59341: n=65126, eng fw/1000=3.8, starts 'produced by gun britt carlsson eva eriksson jens sadowski and the online'
- de_50285: n=74066, eng fw/1000=18.6, starts 'dr mabuse der spieler ullstein bücher eine sammlung zeitgenössischer romane dr mabuse'
- de_56156: n=39545, eng fw/1000=19.8, starts 'anmerkungen zur transkription der vorliegende text wurde anhand der erschienenen buchausgabe so'
- nl_76280: n=66108, eng fw/1000=36.0, starts 'wonderreizen jules verne mathias sandorf een verijdelde samenzwering dokter antekirrt amsterdam uitgevers'
- fr_19919: n=97523, eng fw/1000=0.1, starts 'produced by chuck greif and www ebooksgratuits com paul féval les habits'
- la_227: n=63914, eng fw/1000=11.4, starts 'publi vergili maronis aeneidos liber i arma virumque cano troiae qui primus'
- la_33849: n=84007, eng fw/1000=22.4, starts 's aurelii augustini confessiones post editionem parisiensem novissimam ad fidem codicum oxoniensium'
- it: n=1224054, eng fw/1000=13.7, starts 'cumque predictus fcrdiuandu s rex nuper in romanorum regem electus et in'

## D. Largest single word-final / word-initial pattern shift between the two sides (% of tokens)
a6 claims no natural-language pair shifts one word-final pattern from 0.2% to 17%. For each pair: top-3 features by absolute difference, and top-3 by ratio among features with >=3% on one side.
- Voynich A vs B(random nA): abs [('-dy', 6.19, 23.63), ('-edy', 0.2, 17.23), ('-y', 31.35, 44.88)]; ratio [('-edy', 0.2, 17.23, 88.3), ('ct-', 3.62, 0.2, 17.7), ('cth-', 3.62, 0.2, 17.7)]
- Voynich A half vs A half: abs [('sh-', 9.73, 7.9), ('s-', 13.95, 12.11), ('-o', 4.85, 6.56)]; ratio [('ok-', 4.27, 5.79, 1.4), ('-o', 4.85, 6.56, 1.4), ('sho-', 5.01, 3.8, 1.3)]
- Danish vs Norwegian: abs [('-e', 12.44, 20.71), ('-g', 10.09, 15.76), ('-t', 8.58, 13.82)]; ratio [('-aa', 3.45, 0.04, 69.1), ('-å', 0, 3.45, 68.9), ('-jeg', 0.65, 5.03, 7.7)]
- Danish vs Swedish: abs [('-t', 8.58, 15.95), ('-er', 8.4, 2.52), ('-g', 10.09, 4.93)]; ratio [('oc-', 0, 3.84, 76.9), ('-och', 0, 3.63, 72.6), ('och-', 0, 3.63, 72.6)]
- Danish vs Danish: abs [('-e', 12.44, 21.46), ('-de', 3.51, 8.35), ('-r', 13.87, 9.27)]; ratio [('-ede', 0.4, 3.19, 8.0), ('-han', 0.82, 3.46, 4.2), ('-an', 1.4, 3.79, 2.7)]
- English vs English: abs [('h-', 7.83, 4.92), ('th-', 8.81, 11.52), ('s-', 6.43, 9.01)]; ratio [('he-', 3.1, 1.44, 2.2), ('-a', 2.19, 3.77, 1.7), ('h-', 7.83, 4.92, 1.6)]
- German vs German: abs [('-er', 11.91, 7.23), ('-r', 15.8, 11.75), ('-ch', 5.11, 8.32)]; ratio [('ic-', 0.71, 3.44, 4.9), ('ich-', 0.71, 3.44, 4.9), ('er-', 4.89, 1.73, 2.8)]
- German vs Dutch: abs [('-n', 21.84, 30.2), ('-en', 13.52, 21.32), ('-r', 15.8, 8.06)]; ratio [('va-', 0.05, 3.72, 74.5), ('-van', 0, 3.47, 69.5), ('van-', 0, 3.45, 68.9)]
- Vergil vs Augustine: abs [('-e', 17.81, 11.28), ('e-', 6.95, 13.02), ('-ue', 6.22, 1.42)]; ratio [('-ue', 6.22, 1.42, 4.4), ('-que', 6.17, 1.42, 4.3), ('-d', 1.14, 3.36, 2.9)]
- Latin vs Italian: abs [('-s', 17.69, 1.5), ('-m', 16.43, 0.79), ('-a', 8.08, 20.18)]; ratio [('v-', 4.03, 0, 80.6), ('-he', 0, 3.45, 69.1), ('che-', 0, 3.45, 69.1)]
- French vs Italian: abs [('-o', 0.19, 17.52), ('-s', 16.08, 1.5), ('-a', 6.05, 20.18)]; ratio [('-o', 0.19, 17.52, 94.3), ('-to', 0, 4.43, 88.6), ('-di', 0, 4.04, 80.8)]

## E. Vocabulary sharing recomputed (independent code, new random B sample) -- jaccard / typesX_in_Y / tokX_in_Y / top100 / JSD bits
- Voynich A vs B(random nA): 0.1468 / 0.237 / 0.6685 / 0.95 / 0.4937; top-100 words of X missing in Y: ['cthor', 'ckhey', 'dchy', 'kchor', 'ctho']
- Voynich A half vs A half: 0.2067 / 0.3291 / 0.7071 / 1.0 / None; top-100 words of X missing in Y: []
- Danish vs Norwegian: 0.1163 / 0.176 / 0.5063 / 0.67 / 0.5198; top-100 words of X missing in Y: ['saa', 'paa', 'æ', 'klip', 'din', 'gaar', 'naar', 'ka', 'te', 'klap', 'lystig', 'jens']
- Danish vs Swedish: 0.0381 / 0.0669 / 0.3592 / 0.48 / 0.7342; top-100 words of X missing in Y: ['saa', 'der', 'æ', 'ved', 'jeg', 'fra', 'sang', 'da', 'hvor', 'klip', 'gaar', 'mens']
- Danish vs Danish: 0.1368 / 0.2118 / 0.5688 / 0.79 / 0.4589; top-100 words of X missing in Y: ['æ', 'klip', 'a', 'din', 'ka', 'te', 'klap', 'lystig', 'ej', 'dit', 'far', 'mi']
- English vs English: 0.1721 / 0.3455 / 0.7524 / 0.91 / 0.3436; top-100 words of X missing in Y: ['miss', 'bennet', 'bingley', 'mrs', 'darcy', 'heading', 'austen', 'illustration', 'jane']
- German vs German: 0.1608 / 0.2874 / 0.7081 / 0.87 / 0.3749; top-100 words of X missing in Y: ['wenk', 'hull', 'herr', 'spiel', 'selber', 'karten', 'balling', 'carozza', 'karstens', 'staatsanwalt', 'mark', 'basch']
- German vs Dutch: 0.0178 / 0.035 / 0.1968 / 0.19 / 0.8846; top-100 words of X missing in Y: ['und', 'sich', 'zu', 'das', 'sie', 'mit', 'es', 'hatte', 'nicht', 'ein', 'eine', 'ihm']
- Vergil vs Augustine: 0.0838 / 0.1382 / 0.339 / 0.71 / 0.6553; top-100 words of X missing in Y: ['quae', 'iam', 'haec', 'circum', 'arma', 'aeneas', 'moenia', 'danaum', 'urbem', 'sanguine', 'troiae', 'troia']
- Latin vs Italian: 0.0351 / 0.0588 / 0.3232 / 0.43 / 0.8129; top-100 words of X missing in Y: ['mihi', 'quam', 'quo', 'quæ', 'quia', 'domine', 'meus', 'autem', 'mea', 'aut', 'nisi', 'vel']
- French vs Italian: 0.0147 / 0.0308 / 0.3044 / 0.28 / 0.8377; top-100 words of X missing in Y: ['à', 'les', 'en', 'pas', 'du', 'dans', 'une', 'qu', 'pour', 'je', 'on', 'vous']
Top-100 overlap at 3315 tokens/side (a6's B-herbal vs A-herbal = 0.72, A-herbal vs A-pharma = 0.77): {'Voynich A vs B(random nA)': 0.77, 'Voynich A half vs A half': 0.99, 'Danish vs Norwegian': 0.59, 'Danish vs Swedish': 0.42, 'Danish vs Danish': 0.61, 'English vs English': 0.79, 'German vs German': 0.81, 'German vs Dutch': 0.11, 'Vergil vs Augustine': 0.53, 'Latin vs Italian': 0.31, 'French vs Italian': 0.26}

## F. Section-specific vocabulary
chi2/n bound: a6 says '#sections-1' (5); correct bound is (1-p_min)/p_min = 48.0 for the whole-MS section sizes (equal only when sections are equal-sized). Does not affect any reported number.
Whole MS recomputed: n_words 257, mean chi2/n 0.6537, median 0.4871, frac>0.5 0.4864 (a6: 257, 0.654, 0.487, 0.486)
F_within_B sizes {'H': 3315, 'T': 2080, 'B': 6191, 'S': 10851}: Voynich mean 0.3367 (n_words 184, frac>0.5 0.2011); shuffled 0.0771; Italian spread 0.4123 / offset placement 0.3673; Latin spread 0.3004
  top words by chi2 (word, n, chi2/n, peak): [('qol', 132, 1.218, 'B'), ('ol', 408, 0.371, 'B'), ('qokain', 273, 0.534, 'B'), ('shedy', 411, 0.342, 'B'), ('qokedy', 264, 0.511, 'B'), ('qokal', 164, 0.57, 'B'), ('qokeedy', 302, 0.276, 'B'), ('ar', 255, 0.248, 'T'), ('sol', 43, 1.451, 'B'), ('chdy', 117, 0.53, 'H')]
F_within_hand2 sizes {'H': 2254, 'B': 6191, 'T': 1787, 'C': 431}: Voynich mean 0.2912 (n_words 105, frac>0.5 0.1619); shuffled 0.0854; Italian spread 0.1948 / offset placement 0.2375; Latin spread 0.1878
  top words by chi2 (word, n, chi2/n, peak): [('qokain', 171, 0.522, 'B'), ('ar', 107, 0.794, 'H'), ('aiin', 146, 0.535, 'C'), ('qokeedy', 161, 0.423, 'B'), ('qol', 105, 0.602, 'B'), ('ol', 285, 0.17, 'B'), ('qokedy', 195, 0.204, 'B'), ('ykaiin', 25, 1.527, 'C'), ('shedy', 289, 0.125, 'B'), ('qokal', 119, 0.301, 'B')]
F_within_hand1 sizes {'H': 7514, 'P': 2293}: Voynich mean 0.2388 (n_words 77, frac>0.5 0.0779); shuffled 0.0277; Italian spread 0.1076 / offset placement 0.1885; Latin spread 0.0528
  top words by chi2 (word, n, chi2/n, peak): [('okeol', 37, 1.858, 'P'), ('qokeol', 31, 1.63, 'P'), ('okeey', 30, 1.585, 'P'), ('cheol', 62, 0.735, 'P'), ('cheody', 25, 1.319, 'P'), ('qokeey', 34, 0.822, 'P'), ('ol', 98, 0.258, 'P'), ('aiin', 71, 0.335, 'P'), ('cthy', 85, 0.247, 'H'), ('qokol', 45, 0.363, 'P')]

## G. Entropies recomputed (all loci, 4574 lines): H(lang)=0.9698, H(lang|hand)=0.0923, H(lang|section)=0.3984, H(lang|quire)=0.2291; mixed cells {'hand3_S': {'A': 80, 'B': 1039}} (a6: 0.9698 / 0.0923 / 0.3984; hand3_S 80/1039)
## Verdict (verifier)
Reproduction: a6_structure.py re-run unmodified (output redirected to scratchpad) gives a byte-identical a6.json; independent recomputation in v_a6.py matches every checked number (sub-word rates, after-bench distributions, entropies, whole-MS chi2/n, Jaccard/JSD). Formulas correct (log2 entropies, JSD = mean KL to mixture, chi2 vs size-proportional expectation, Ward via ni*nj/(ni+nj)*||ci-cj||^2). Corpora: START/END markers present and stripped in all 13 files used, all decode as UTF-8, strict English contamination (the/and/of) < 1 per 1000 words. Same rates in Takahashi IT2a (e.g. -edy 0.20/17.57, cho 16.5/2.8), so not a ZL-specific artefact.
Corrections: (1) '100% single-feature rule' is in-sample; leave-one-out = 99.5%; A max -edy 2.42% (f89r1) vs B min 3.23% (f55r); A is a spike (112/114 folios < 2%) but B is a continuum 3-42% (median 14.3%). (2) 'No natural-language pair shifts a word-final pattern 0.2% -> 17%': true for dialect pairs, false for language pairs: French vs Italian -o 0.19% -> 17.5%; Latin vs Italian -s 17.7 -> 1.5, -m 16.4 -> 0.8. The only same-rate pattern swap among related standards is the spelling-reform case Danish -aa 3.45% vs Norwegian -å 0.04%/3.45%. (3) Top-100 overlap: fresh random B sample gives 0.95 (not 0.98); English/English 0.91 includes Gutenberg markup words 'heading' and 'illustration', so ~0.93 corrected; remaining gap is proper names only; at 3315 tokens/side A/B 0.77 vs English/English 0.79, German/German 0.81. (4) chi2/n bound is (1-p_min)/p_min = 48 for the whole-MS sizes, not #sections-1 = 5 (no reported number affected). (5) 'lang and hand constant per folio' is by construction of the IVTFF page header. (6) 96 P tokens (0.28%) carry '@nnn;' codes or apostrophes (spurious types). (7) Single-placement Italian/Latin controls move by 0.05-0.08 with a different offset, so the 0..1 'position' values are unstable.
New: within hand 2 alone (one scribe, one language) section chi2/n = 0.291 vs shuffled 0.085 vs Italian 0.19-0.24; within hand 1 (H vs P) 0.239 vs shuffled 0.028 vs Italian 0.11-0.19. The 'section words' are qokain/qol/qokeedy/ol/qokedy/shedy/qokal (hand 2) and okeol/qokeol/okeey/cheol/cheody/qokeey (hand 1): the same sub-word families, not content-word-like vocabulary.
Checked: reproducibility, formulas, corpus hygiene, second transliteration, LOO, suffix-shift claim, top-100 claim, chi2 bound, within-scribe section effect. Not checked: k-means/Ward re-implementation with different seeds; GC2a v101 segmentation; Davis hand assignments themselves. User must verify: interpretive reading (dialect vs orthographic parameter) before citing. All output unvalidated until user review.
