# v_a4: re-check of a4

ZL P text: 34116 tokens, 207 pages, 4130 lines; raw P tokens 34310; dropped {'has ?': 98, 'has @': 73, 'other non a-z': 23}

Levenshtein check: 25404 pairs, disagreements: 0

Voynich brute-force nearest-earlier (DP Levenshtein): {'n': 34116, 'coverage': 0.643100011724704, 'median': 14.0, 'within10': 0.2693457615195216, 'within30': 0.46248094735607925, 'prev2lines': 0.40541095087349044, 'same_line': 0.13747215382811584}
len>=5: {'n': 21746, 'coverage': 0.5660811183665961, 'median': 15.0, 'within10': 0.2245010576657776, 'within30': 0.38972684631656396, 'prev2lines': 0.34291363928998436, 'same_line': 0.10903154603145405}

h1/h2 no space (exact conditional): 3.865/2.311; with space 3.8738/2.117; zipf (slope, f at rank 1000, f at rank 100): (-1.0403, 4, 55)

## corpus files

- corp_da_24747.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK SAMLEDE VÆRKER, ANDET BIND ***
- corp_da_36942.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK KONGENS FALD ***
- corp_da_41072.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK LEONORA CHRISTINA ULFELDT'S "JAMMERS-MI
- corp_da_44967.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK LIVSERINDRINGER ***
- corp_da_66058.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK MED LUFTSKIB TIL MARS: FANTASTISK FREMT
- corp_de_35312.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK AUS DEM LEBEN EINES TAUGENICHTS: NOVELL
- corp_de_50285.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK DR. MABUSE, DER SPIELER ***
- corp_de_56156.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK VENUS IM PELZ ***
- corp_de_66452.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK DIE LIEBE: NOVELLE ***
- corp_en_1342.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK PRIDE AND PREJUDICE ***
- corp_en_2554.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK CRIME AND PUNISHMENT ***
- corp_en_2701.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK MOBY DICK; OR, THE WHALE ***
- corp_fi_75789.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK MARKIISITTAREN RIKOS ***
- corp_fi_78071.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK KAKSI MORSIANTA ***
- corp_fr_18143.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK ROMÉO ET JULIETTE ***
- corp_fr_19919.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK MAMAN LÉO ***
- corp_fr_62215.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK LE FANTÔME DE L'OPÉRA ***
- corp_fr_78027.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK LES ENCHANTEMENTS DE LA FORÊT ***
- corp_is_15178.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK ALASKA ***
- corp_is_16696.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK LEIÐARVÍSIR Í ÁSTAMÁLUM ***
- corp_is_16846.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK MJALLHVÍT: ÆFINTÝRI HANDA BÖRNUM ***
- corp_is_17025.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK SÆFARINN (FERÐIN KRING UM HNÖTTIN NEÐAN
- corp_is_19960.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK HÚSABÆTUR Á SVEITABÆJUM: UPPDRÆTTIR OG 
- corp_la_227.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK AENEIDOS ***
- corp_la_33849.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK CONFESSIONES ***
- corp_la_50280.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK LATIN PHRASE-BOOK ***
- corp_nl_76186.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK LORD LISTER NO. 0032: DE BLAUWE DOOD **
- corp_nl_76280.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK MATHIAS SANDORF [1] ***
- corp_nl_76761.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK LORD LISTER NO. 0033: DE ALARMKREET ***
- corp_nl_76765.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK LORD LISTER NO. 0333: DE LIEFDE VAN EEN
- corp_no_30027.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK SULT ***
- corp_no_43724.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK MARKENS GRØDE, FØRSTE DEL ***
- corp_no_59635.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK NORSK LITERATURHISTORIE FOR GYMNASIET, 
- corp_no_77368.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK SKUM ***
- corp_sv_48961.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK EN PIGA BLAND PIGOR ***
- corp_sv_59341.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK ÄDELT VILDT: EN FAMILJEHISTORIA ***
- corp_sv_62635.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK MOLOKS LEENDE: ROMAN ***
- corp_sv_62806.txt: utf-8, *** START OF THE PROJECT GUTENBERG EBOOK KÅTORNAS FOLK ***

## corpus loaders

- la: {"files_used": [["corp_la_227.txt", "utf-8", 63791]], "a4_vs_fixed_positions_differ": 0, "a4_types": 11383, "fixed_types": 11383, "fixed_words_with_nonascii_letter": 0, "frac_1char_tokens_fixed": 0.0038, "a4_first_words": "publi vergili maronis aeneidos liber i arma virumque cano troiae qui primus ab oris italiam fato profugus laviniaque venit litora multum ille et terris iactatus", "fixed_first_words": "publi vergili maronis aeneidos liber i arma virumque cano troiae qui primus ab oris italiam fato profugus laviniaque venit litora multum ille et terris iactatus"}
- it: {"files_used": [["corpus_it.txt", "utf-8", null]], "a4_vs_fixed_positions_differ": 0, "a4_types": 6762, "fixed_types": 6762, "fixed_words_with_nonascii_letter": 0, "frac_1char_tokens_fixed": 0.0491, "a4_first_words": "cumque predictus fcrdiuandu s rex nuper in romanorum regem electus et in aquisgrana coronatus fuerit fraternitasque tua eundem ferdinandum regem ad quecunquc loca ad que", "fixed_first_words": "cumque predictus fcrdiuandu s rex nuper in romanorum regem electus et in aquisgrana coronatus fuerit fraternitasque tua eundem ferdinandum regem ad quecunquc loca ad que"}
- de: {"files_used": [["corp_de_35312.txt", "utf-8", 31388], ["corp_de_50285.txt", "utf-8", 73899]], "a4_vs_fixed_positions_differ": 0, "a4_types": 5551, "fixed_types": 5551, "fixed_words_with_nonascii_letter": 3041, "frac_1char_tokens_fixed": 0.0007, "a4_first_words": "produced by jana srna and the online distributed proofreading team at https www pgdp net anmerkungen zur transkription schreibweise und interpunktion des originaltextes wurden \u00fcbernommen", "fixed_first_words": "produced by jana srna and the online distributed proofreading team at https www pgdp net anmerkungen zur transkription 
- en: {"files_used": [["corp_en_1342.txt", "utf-8", 128559]], "a4_vs_fixed_positions_differ": 0, "a4_types": 3976, "fixed_types": 3976, "fixed_words_with_nonascii_letter": 8, "frac_1char_tokens_fixed": 0.0406, "a4_first_words": "illustration george allen publisher charing cross road london ruskin house illustration reading jane s letters chap pride and prejudice by jane austen with a preface", "fixed_first_words": "illustration george allen publisher charing cross road london ruskin house illustration reading jane s letters chap pride and prejudice by jane austen with a preface"}
- da: {"files_used": [["corp_da_24747.txt", "utf-8", 53237]], "a4_vs_fixed_positions_differ": 0, "a4_types": 7851, "fixed_types": 7851, "fixed_words_with_nonascii_letter": 3948, "frac_1char_tokens_fixed": 0.0402, "a4_first_words": "produced by louise hope steen christensen and the online distributed proofreading team at http www pgdp net jeppe aakj\u00e6r samlede v\u00e6rker andet bind digte gyldendalske", "fixed_first_words": "produced by louise hope steen christensen and the online distributed proofreading team at http www pgdp net jeppe aakj\u00e6r samlede v\u00e6rker andet bind digte gyldendalsk
- da_prose: {"files_used": [["corp_da_36942.txt", "utf-8", 70025]], "first_words": "johannes v jensen kongens fald gyldendalske boghandel nordisk forlag kj\u00f8benhavn kristiania london berlin mdccccxxii copyright by johannes v jensen fjerde oplag trykt ialt i eksemplarer"}
- la_alt: {"files_used": [["corp_la_33849.txt", "utf-8", 135590]], "first_words": "s aurelii augustini confessiones post editionem parisiensem novissimam ad fidem codicum oxoniensium recognit\u00e6 et post editionem m dubois ex ipso augustino illustrat\u00e6 oxonii j h"}
- en_body: {"preface_words_skipped": 4939}

## comparison table

| corpus | cover | median | within10 | within10_wpshuf | within10_gshuf | prev2 | long5_within10 | long5_cover | page_exact | page_LD1other | net_types_nb | net_giant | types | h1 | h2 | zipf | hapax_types | hapax_tokens | wlen_mean | wlen_var | adj_rep |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| voynich_raw | 0.643 | 14.0 | 0.269 | 0.238 | 0.167 | 0.405 | 0.225 | 0.566 | 0.445 | 0.77 | 0.819 | 0.802 | 7236 | 3.865 | 2.3111 | -1.0403 | 0.6972 | 0.1479 | 5.0702 | 3.7336 | 0.00815 |
| la_a4decode | 0.196 | 41.0 | 0.035 | 0.034 | 0.03 | 0.066 | 0.006 | 0.082 | 0.183 | 0.206 | 0.615 | 0.308 | 11383 | 4.0249 | 3.5091 | -0.6978 | 0.5991 | 0.1999 | 5.7628 | 4.8816 | 0.00032 |
| it_a4decode | 0.477 | 17.0 | 0.168 | 0.173 | 0.165 | 0.278 | 0.017 | 0.175 | 0.433 | 0.487 | 0.633 | 0.329 | 6762 | 3.9414 | 3.4513 | -1.025 | 0.6652 | 0.1318 | 4.5409 | 6.5817 | 0.00076 |
| de_a4decode | 0.455 | 21.0 | 0.128 | 0.131 | 0.128 | 0.232 | 0.017 | 0.17 | 0.47 | 0.445 | 0.497 | 0.274 | 5551 | 4.162 | 3.3917 | -1.0397 | 0.5972 | 0.0972 | 4.8678 | 6.3305 | 0.00114 |
| de_fixeddecode | 0.455 | 21.0 | 0.128 | 0.131 | 0.128 | 0.232 | 0.017 | 0.17 | 0.47 | 0.445 | 0.497 | 0.274 | 5551 | 4.162 | 3.3917 | -1.0397 | 0.5972 | 0.0972 | 4.8678 | 6.3305 | 0.00114 |
| en_a4decode | 0.5 | 17.0 | 0.176 | 0.177 | 0.164 | 0.293 | 0.019 | 0.148 | 0.534 | 0.463 | 0.413 | 0.188 | 3976 | 4.1843 | 3.6015 | -1.0776 | 0.5008 | 0.0584 | 4.3893 | 5.9836 | 0.0005 |
| da_a4decode | 0.502 | 15.0 | 0.196 | 0.172 | 0.138 | 0.309 | 0.035 | 0.153 | 0.46 | 0.53 | 0.668 | 0.55 | 7851 | 4.238 | 3.6694 | -0.9327 | 0.6045 | 0.1391 | 4.1476 | 4.6542 | 0.00378 |
| da_fixeddecode | 0.502 | 15.0 | 0.196 | 0.172 | 0.138 | 0.309 | 0.035 | 0.153 | 0.46 | 0.53 | 0.668 | 0.55 | 7851 | 4.238 | 3.6694 | -0.9327 | 0.6045 | 0.1391 | 4.1476 | 4.6542 | 0.00378 |
| da_prose_fixed | 0.474 | 19 | 0.145 | 0.153 | 0.144 | 0.259 | 0.017 | 0.156 | 0.483 | 0.438 | 0.552 | 0.37 | 6273 | 4.1304 | 3.5255 | -1.0316 | 0.6284 | 0.1155 | 4.3866 | 5.1749 | 0.00185 |
| la_alt_fixed | 0.372 | 19 | 0.126 | 0.106 | 0.094 | 0.203 | 0.032 | 0.136 | 0.384 | 0.342 | 0.503 | 0.163 | 9486 | 4.0351 | 3.5005 | -0.9562 | 0.6744 | 0.1875 | 5.4236 | 7.9056 | 0.00038 |
| en_body_fixed | 0.501 | 17 | 0.172 | 0.175 | 0.168 | 0.291 | 0.016 | 0.147 | 0.535 | 0.466 | 0.413 | 0.187 | 3574 | 4.188 | 3.5947 | -1.0761 | 0.4675 | 0.049 | 4.3609 | 5.9017 | 0.00044 |
| voynich_mergeA_icount_kept | 0.692 | 12.0 | 0.325 | 0.29 | 0.215 | 0.467 | 0.196 | 0.508 | 0.446 | 0.813 | 0.843 | 0.835 | 7207 | 3.9492 | 2.683 | -1.0422 | 0.697 | 0.1472 | 4.1213 | 2.5013 | 0.0083 |
| voynich_mergeB_a4 | 0.698 | 11 | 0.336 | 0.302 | 0.227 | 0.478 | 0.201 | 0.515 | 0.456 | 0.817 | 0.842 | 0.835 | 7053 | 3.9115 | 2.6462 | -1.0515 | 0.6949 | 0.1437 | 4.1213 | 2.5013 | 0.00909 |
| markov3_voynich | 0.579 | 19.0 | 0.194 | 0.194 | 0.194 | 0.324 | 0.119 | 0.427 | 0.375 | 0.705 | 0.732 | 0.699 | 8134 | 3.8658 | 2.373 | -1.0757 | 0.7526 | 0.1794 | 5.0478 | 5.5024 | 0.00484 |
| markov3_da_prose | 0.449 | 20 | 0.143 | 0.143 | 0.142 | 0.243 | 0.007 | 0.078 | 0.293 | 0.544 | 0.625 | 0.585 | 12614 | 4.1331 | 3.5385 | -0.9815 | 0.8108 | 0.2998 | 4.3837 | 6.2408 | 0.0049 |
| markov3_de_fixed | 0.424 | 21.0 | 0.126 | 0.128 | 0.126 | 0.221 | 0.005 | 0.067 | 0.26 | 0.527 | 0.565 | 0.522 | 13454 | 4.1604 | 3.4012 | -1.0016 | 0.8264 | 0.3259 | 4.8575 | 7.7065 | 0.0029 |
| markov3_it | 0.465 | 14.0 | 0.195 | 0.197 | 0.197 | 0.304 | 0.004 | 0.04 | 0.305 | 0.546 | 0.526 | 0.487 | 13503 | 3.9392 | 3.4477 | -1.0446 | 0.852 | 0.3372 | 4.5225 | 9.8138 | 0.00495 |
| markov3_en | 0.466 | 17 | 0.167 | 0.165 | 0.164 | 0.272 | 0.003 | 0.042 | 0.315 | 0.557 | 0.545 | 0.491 | 12233 | 4.1887 | 3.6077 | -1.0322 | 0.8252 | 0.2959 | 4.3667 | 7.8681 | 0.00443 |
| markov4_voynich | 0.584 | 20.0 | 0.18 | 0.185 | 0.184 | 0.312 | 0.134 | 0.473 | 0.371 | 0.717 | 0.768 | 0.737 | 7424 | 3.8664 | 2.3625 | -1.0818 | 0.7155 | 0.1557 | 5.0702 | 4.4073 | 0.00407 |

top5: voynich_raw: daiin ol chedy aiin shedy; la_a4decode: et in nec per ad; it_a4decode: et di che a non; de_a4decode: und die ich der in; de_fixeddecode: und die ich der in; en_a4decode: the to and of a; da_a4decode: og i en den det; da_fixeddecode: og i en den det; da_prose_fixed: og han i var en; la_alt_fixed: et in non te sed; en_body_fixed: the to and of a; voynich_mergeA_icount_kept: daN ol Cedy aN Sedy; voynich_mergeB_a4: daN aN qokaN ol Cedy; markov3_voynich: ol chedy daiin chey chy; markov3_da_prose: og i de en han; markov3_de_fixed: und die ich den der; markov3_it: di et che a la; markov3_en: to of the a i; markov4_voynich: daiin chedy ol aiin chey

Markov controls: frac tokens that are real source types: markov3_voynich=0.813, markov3_da_prose=0.441, markov3_de_fixed=0.34, markov3_it=0.5, markov3_en=0.391, markov4_voynich=0.852

## autocopist fidelity

{
 "frac_tokens_in_ZL_types": 0.372,
 "frac_tokens_in_ZL_types_freq>=2": 0.299,
 "frac_types_in_ZL_types": 0.091,
 "top20_autocopist_s19": [
  [
   "daiin",
   280
  ],
  [
   "dain",
   242
  ],
  [
   "cho",
   232
  ],
  [
   "chy",
   216
  ],
  [
   "shy",
   210
  ],
  [
   "sho",
   196
  ],
  [
   "ky",
   143
  ],
  [
   "eeo",
   141
  ],
  [
   "eey",
   137
  ],
  [
   "chol",
   126
  ],
  [
   "ko",
   120
  ],
  [
   "shol",
   109
  ],
  [
   "ey",
   107
  ],
  [
   "to",
   105
  ],
  [
   "ka",
   103
  ],
  [
   "ty",
   99
  ],
  [
   "shar",
   95
  ],
  [
   "aiin",
   94
  ],
  [
   "kar",
   94
  ],
  [
   "ochy",
   93
  ]
 ],
 "voynich_profile": {
  "i_type": 0.191,
  "dy_or_y_final": 0.407,
  "gallows_initial": 0.082,
  "qo_initial": 0.151,
  "ch_sh_initial": 0.248,
  "contains_e": 0.379,
  "contains_ee": 0.125
 },
 "autocopist_profile": {
  "i_type": 0.2,
  "dy_or_y_final": 0.232,
  "gallows_initial": 0.268,
  "qo_initial": 0.02,
  "ch_sh_initial": 0.178,
  "contains_e": 0.263,
  "contains_ee": 0.16
 },
 "note": "for reference: fraction of ZL P tokens whose type also occurs in ZL is 1 by definition; a Voynichese generator should reach a high share of real types"
}
