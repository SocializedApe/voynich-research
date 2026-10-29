# v_a3: adversarial re-check of a3

Reload: a3 N=34059, mine N=34059 (identical token list: True); P words before filtering 34310, dropped {'?': 98, "nonEVA:'": 23, 'nonEVA:x': 21, 'nonEVA:b': 15, 'nonEVA:j': 9, 'nonEVA:u': 7, 'nonEVA:157;@': 6, 'nonEVA:138;@': 4, 'nonEVA:145;@': 4, 'nonEVA:z': 4, 'nonEVA:026;@': 4, 'nonEVA:135;@': 3}

a3 order cost recomputed: 40319 / 252550 (a3 reports 40319 / 252550). Own LOP heuristic: 0.15965 vs a3 0.15965.

| corpus | tokens | types | mean len | pair-viol | adjacent-only viol | length-matched to Voynich | L3 glob/refit | L4 | L5 | L6 | L7 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| voy_merged | 34059 | 6897 | 4.11 | 0.1596 | 0.1684 | None | 0.0755/0.0588 | 0.1305/0.1252 | 0.1373/0.1351 | 0.1594/0.1484 | 0.2151/0.1927 |
| voy_raw | 34059 | 7182 | 5.07 | 0.1574 | 0.162 | None | 0.1061/0.0892 | 0.091/0.0901 | 0.1085/0.1083 | 0.1428/0.1364 | 0.1609/0.1457 |
| la | 34059 | 11368 | 5.76 | 0.3601 | 0.3977 | 0.3627 | 0.4593/0.1779 | 0.4174/0.2976 | 0.3521/0.3382 | 0.3592/0.3498 | 0.3627/0.3568 |
| it | 34059 | 6758 | 4.54 | 0.3506 | 0.3808 | 0.3175 | 0.2494/0.1126 | 0.3219/0.2516 | 0.3384/0.309 | 0.3292/0.2941 | 0.3555/0.3413 |
| de | 34059 | 5568 | 4.87 | 0.3179 | 0.3125 | 0.2781 | 0.1476/0.13 | 0.2546/0.2029 | 0.294/0.2742 | 0.2946/0.2807 | 0.3118/0.3024 |
| en | 34059 | 3973 | 4.39 | 0.3393 | 0.3558 | 0.3082 | 0.2211/0.1172 | 0.3226/0.2462 | 0.3057/0.2778 | 0.322/0.2963 | 0.3205/0.3108 |
| voy_merged_shuf | 34059 | 16560 | 4.11 | 0.4935 | 0.4946 | 0.4903 | 0.4976/0.4834 | 0.4956/0.4854 | 0.4924/0.4885 | 0.4884/0.485 | 0.4963/0.4774 |
| la_shuf | 34059 | 26707 | 5.76 | 0.4953 | 0.4964 | 0.489 | 0.5016/0.4721 | 0.4955/0.4834 | 0.498/0.487 | 0.4945/0.489 | 0.4956/0.4876 |
| gc_v101 | 34059 | 7935 | 3.86 | 0.1395 | 0.1593 | None | 0.076/0.0573 | 0.1328/0.1269 | 0.1387/0.1352 | 0.156/0.1437 | 0.1798/0.1596 |
| gc_v101_shuf | 34059 | 17208 | 3.86 | 0.4903 | 0.4934 | 0.481 | 0.4955/0.4797 | 0.4908/0.4799 | 0.4872/0.4835 | 0.4901/0.4804 | 0.4892/0.4753 |
| it_only | 34059 | 8359 | 4.58 | 0.358 | 0.4017 | 0.3139 | 0.2712/0.1412 | 0.3272/0.2816 | 0.332/0.304 | 0.3183/0.2917 | 0.3571/0.3494 |
| la_reseg_esm | 34059 | 9577 | 4.0 | 0.31 | 0.2977 | 0.2321 | 0.0885/0.0829 | 0.1947/0.1809 | 0.2399/0.2345 | 0.2648/0.2596 | 0.2992/0.2969 |
| la_reseg_vowels | 34059 | 1249 | 2.23 | 0.0526 | 0.0666 | 0.1075 | 0.0745/0.0654 | 0.0641/0.05 | - | - | - |
| la_reseg_st | 30898 | 14109 | 6.35 | 0.3628 | 0.3605 | 0.2284 | 0.1005/0.0757 | 0.1863/0.1671 | 0.2363/0.2219 | 0.2698/0.263 | 0.2888/0.2873 |
| rugg_la | 34059 | 15067 | 4.0 | 0.3312 | 0.376 | 0.3322 | 0.3312/0.2913 | 0.3326/0.3239 | 0.3296/0.3211 | 0.3303/0.3243 | 0.3285/0.3094 |
| rugg_en | 34059 | 5979 | 2.98 | 0.2384 | 0.2655 | 0.2387 | 0.222/0.2058 | 0.25/0.2432 | 0.2469/0.2325 | 0.2696/0.2227 | 0.2812/0.2137 |

## Corpus diagnostics

- la corp_la_227.txt: *** START OF THE PROJECT GUTENBERG EBOOK AENEIDOS *** | body tokens 63791 | exhausted within N: False | footer tokens leaked by stale index if exhausted: 123 | starts: publi vergili maronis aeneidos liber i arma virumque cano troiae qui primus
- la corp_la_33849.txt: *** START OF THE PROJECT GUTENBERG EBOOK CONFESSIONES *** | body tokens 135590 | exhausted within N: False | footer tokens leaked by stale index if exhausted: 177 | starts: s aurelii augustini confessiones post editionem parisiensem novissimam ad fidem codicum oxoniensium
- la corp_la_50280.txt: *** START OF THE PROJECT GUTENBERG EBOOK LATIN PHRASE-BOOK *** | body tokens 60100 | exhausted within N: False | footer tokens leaked by stale index if exhausted: 140 | starts: latin phrase book by c meissner translated from the sixth german edition
- de corp_de_35312.txt: *** START OF THE PROJECT GUTENBERG EBOOK AUS DEM LEBEN EINES TAUGENICHTS: NOVELLE *** | body tokens 31388 | exhausted within N: True | footer tokens leaked by stale index if exhausted: 162 | starts: produced by jana srna and the online distributed proofreading team at https
- de corp_de_50285.txt: *** START OF THE PROJECT GUTENBERG EBOOK DR. MABUSE, DER SPIELER *** | body tokens 73899 | exhausted within N: False | footer tokens leaked by stale index if exhausted: 167 | starts: dr mabuse der spieler ullstein bücher eine sammlung zeitgenössischer romane dr mabuse
- de corp_de_56156.txt: *** START OF THE PROJECT GUTENBERG EBOOK VENUS IM PELZ *** | body tokens 39387 | exhausted within N: False | footer tokens leaked by stale index if exhausted: 158 | starts: anmerkungen zur transkription der vorliegende text wurde anhand der erschienenen buchausgabe so
- de corp_de_66452.txt: *** START OF THE PROJECT GUTENBERG EBOOK DIE LIEBE: NOVELLE *** | body tokens 14970 | exhausted within N: False | footer tokens leaked by stale index if exhausted: 158 | starts: illustration d v die liebe novelle von hans kaltneker donau verlag ges
- en corp_en_1342.txt: *** START OF THE PROJECT GUTENBERG EBOOK PRIDE AND PREJUDICE *** | body tokens 128559 | exhausted within N: False | footer tokens leaked by stale index if exhausted: 156 | starts: illustration george allen publisher charing cross road london ruskin house illustration reading
- en corp_en_2554.txt: *** START OF THE PROJECT GUTENBERG EBOOK CRIME AND PUNISHMENT *** | body tokens 208782 | exhausted within N: False | footer tokens leaked by stale index if exhausted: 144 | starts: crime and punishment by fyodor dostoevsky translated by constance garnett translator s
- en corp_en_2701.txt: *** START OF THE PROJECT GUTENBERG EBOOK MOBY DICK; OR, THE WHALE *** | body tokens 219032 | exhausted within N: False | footer tokens leaked by stale index if exhausted: 142 | starts: moby dick or the whale by herman melville contents etymology extracts supplied
- it (corpus_it.txt first 34059 tokens): Latin marker tokens 2127, Italian marker tokens 5670, 1000-token windows Latin-dominated 0/35; starts: cumque predictus fcrdiuandu s rex nuper in romanorum regem electus et in aquisgrana coronatus fuerit fraternitasque tua eundem ferdinandum regem
- it_only (50-token windows with 0 Latin markers, >=2 Italian markers): {'n': 34059, 'windows_kept': 682, 'windows_seen': 16218, 'first_20': 'nostra il ucscouado di pola hauendo ueduta la fidel seruitu d aurelio mio maggio schreibt am februar aus uenedig nunz', 'latin_marker_tokens': 0, 'italian_marker_tokens': 6113}

## Slot-grammar coverage (a3 functions, budgets 20/40/30) as-is vs length-matched to Voynich

| corpus/sample | types | mean len | ngram cov tok | ngram cov typ | zone cov tok | zone cov typ |
|---|---|---|---|---|---|---|
| voy_merged/as_is | 6897 | 4.11 | 0.843 | 0.447 | 0.691 | 0.276 |
| gc_v101/as_is | 7935 | 3.86 | 0.776 | 0.382 | None | None |
| la/as_is | 11368 | 5.76 | 0.409 | 0.181 | 0.191 | 0.061 |
| la/length_matched | 4679 | 4.11 | 0.694 | 0.315 | 0.382 | 0.105 |
| it/as_is | 6758 | 4.54 | 0.63 | 0.213 | 0.503 | 0.097 |
| it/length_matched | 3566 | 4.11 | 0.705 | 0.344 | 0.514 | 0.169 |
| it_only/as_is | 8359 | 4.58 | 0.602 | 0.202 | 0.5 | 0.104 |
| it_only/length_matched | 4340 | 4.11 | 0.658 | 0.317 | 0.496 | 0.168 |
| de/as_is | 5568 | 4.87 | 0.591 | 0.125 | 0.426 | 0.059 |
| de/length_matched | 2828 | 4.11 | 0.722 | 0.266 | 0.487 | 0.098 |
| en/as_is | 3973 | 4.39 | 0.628 | 0.156 | 0.452 | 0.023 |
| en/length_matched | 2317 | 4.11 | 0.674 | 0.237 | 0.495 | 0.096 |
| la_reseg_esm/as_is | 9577 | 4.0 | 0.675 | 0.146 | 0.597 | 0.095 |
| la_reseg_esm/length_matched | 5343 | 4.11 | 0.666 | 0.29 | 0.466 | 0.144 |
| voy_merged_shuf/as_is | 16560 | 4.11 | 0.69 | 0.445 | 0.258 | 0.065 |

GC v101 (Claston) P tokens: {'n_tokens_P': 36385, 'n_types': 8351, 'alphabet': 70, 'mean_len': 3.87, 'top_chars': 'o9ac1e8hy4km2C7snKpHgA3jz5(dfiMu%*ZNJI+6'}

Re-segmented Latin mean lengths: {'la_reseg_esm': 4.0, 'la_reseg_vowels': 2.23, 'la_reseg_st': 6.35}

Rugg fits: {'rugg_la': {'columns': [20, 38, 413], 'la_ngram_cov_tok': 0.409, 'la_ngram_cov_typ': 0.181}, 'rugg_en': {'columns': [21, 36, 216], 'en_ngram_cov_tok': 0.628, 'en_ngram_cov_typ': 0.156}}

One-edit check: {'a3_function_all_types': 0.8424, 'brute_force_sample1500': 0.8407}

runtime 83 s