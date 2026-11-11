# Phase 2: linguistic concepts as features, and classifiers trained on known kinds of text (11 Nov 2026)

Phase 1 tested one hypothesis at a time. Phase 2 turns the linguistic concepts that can be measured without knowing
what a symbol means into 68 numbers per 4,000-word chunk, computes them on texts whose nature is known (real
languages, ciphers of them, generators with no message), trains classifiers on those, checks whether the classifiers
carry over to kinds of text they were not trained on, and only then looks at Voynich. The protocol and the rule for a
verdict are in the docstring of `model.py` and were written before the Voynich rows were looked at.

**Result in one line: no verdict. The classifiers separate the kinds they were trained on almost perfectly and fail
every test of carrying over to a new kind, so what they say about Voynich (P = 1.00 'a language underneath') carries
no weight: they say the same of Rugg's table text and of the volunteers' gibberish. What phase 2 does give is a
feature-by-feature description of where Voynich sits among 67 natural-language sources.**

## The features (`features.py`)

| concept | what it asks | features |
|---|---|---|
| graphotactics | how predictable is a symbol from the ones before | `c_h1`, `c_h2`, `c_h3` and their ratios, `c_alpha_eff` |
| vowels and consonants | do symbols fall into two classes that alternate (Sukhotin's algorithm) | `p_vowel_share`, `p_cv_alt_excess` |
| positional rules | are word-initial and word-final symbols a restricted set | `p_h_init`, `p_h_final`, `p_jsd_init_med`, `p_jsd_final_med`, `p_jsd_init_final`, `p_double` |
| word shape | length, spread, skew; are frequent words shorter (law of abbreviation) | `w_len_*`, `w_type_len_*`, `w_brevity` |
| lexicon | vocabulary growth, Zipf, hapax, one-edit neighbours | `l_ttr`, `l_hapax_types`, `l_zipf_slope`, `l_zipf_curv`, `l_heaps`, `l_h_word`, `l_top1`, `l_top10`, `l_ld1_share`, `l_ld1_mean` |
| morphology | shared stems against shared endings, suffixing preference, successor variety | `m_suffix_pref`, `m_prefix_trie`, `m_suffix_trie`, `m_trie_asym`, `m_stem_family`, `m_tail_family`, `m_succ_var`, `m_pred_var` |
| subword tokens | byte-pair encoding learnt on the chunk: how the text breaks into reusable pieces | `t_pieces_per_word`, `t_pieces_per_symbol`, `t_top20_cover`, `t_piece_entropy`, `t_merge_at_start`, `t_merge_at_end`, `t_merge_len`, `t_whole_words` |
| syntax | does the previous word predict the next; is word order reversible; word classes | `s_bigram_mi_x`, `s_irrev_x`, `s_class_rank_x` |
| function and content words | are the commonest words spread evenly and the rarer ones bunched | `s_burst_top`, `s_burst_mid`, `s_burst_diff` |
| agreement and sandhi | do neighbours share endings; does a word's end depend on the next word's start | `s_agree_last_x`, `s_sandhi_x`, `s_first_first_x` |
| repetition | exact and near repeats of the neighbour, re-use within 10 words | `s_rep_adj`, `s_rep_adj_x`, `s_near_adj_x`, `s_w10_x` |
| rhythm | autocorrelation and long-range exponent of word lengths | `s_len_ac1_x`, `s_len_hurst` |
| discourse | vocabulary drift, clustering of words, new words late in the text | `d_half_jsd_x`, `d_cluster_x`, `d_new_late_x` |
| compression | bits per symbol; what word order adds | `z_bpc`, `z_wordid_x` |

`_x` = excess over the same statistic with the word order shuffled (3 shuffles), which removes the bias of a short
sample. One feature was dropped before any run (forward against backward predictability, identically zero as built).

## The data (`corpora2.py`, `build.py`, `features.csv`)

908 training chunks: 229 natural (50 languages of the Bible corpus, 4 chunks each; Gutenberg texts; 12 real
manuscripts in graphic transcription), 399 cipher (verbose, homophonic, abjad, digraphic, anagram, respace, nulls,
codebook; one chunk per language each), 280 generated (symbol chains of order 1-3, bag of words, table, self-citation).
Held out of all training: texts made to look like Voynich (autocopist, Rugg, Naibbe, volunteers, this repository's
lang8), and Voynich itself in three encodings, 8 chunks each.

## The checks, and why there is no verdict (`model.py`, `phase2.md`)

| check | result (logistic / forest / boosting) | rule | met |
|---|---|---|---|
| C1 leave a language or generator seed out: AUC | 1.000 / 1.000 / 0.999 | >= 0.95 | yes |
| C3 trained on Bible text, other genres called meaningful | 1.00 / 1.00 / 1.00 | >= 0.9 | yes |
| C2 leave a whole process out: share called right | 13 of 14 processes 0.56-1.00; **self-citation 0.00 under every model** | mean >= 0.8, none under 0.5 | no |
| C4 Voynich mimics on the right side (boosting) | **autocopist 0.72, Rugg 1.00, volunteers 1.00, lang8 0.95 called meaningful; the Naibbe cipher 0.06, called generated** | all five right | no (0 of 5) |
| C5 Voynich inside the training distribution | 1 of 8 chunks (distance 7.6, threshold 7.1, training median 3.5) | >= 6 of 8 | no |

P(meaningful) for Voynich: 0.29 (logistic), 0.89 (forest), 1.00 (boosting); 3-class boosting says cipher. Under the
rule this is not a result. The reason is visible in what the models use: the six most used features are all
word-order features (`s_sandhi_x`, `s_first_first_x`, `s_agree_last_x`, `d_half_jsd_x`, `s_bigram_mi_x`,
`s_burst_mid`). Every generator in the training set but one draws its words independently, so the models learnt
'word order has structure = a language underneath'. A copying generator has word-order structure and no message, and
is called meaningful every time it is held out; the Naibbe cipher scrambles word order with dice and is called
generated. **A classifier of this kind measures sequential structure, not meaning**, and Voynich has sequential
structure (phase 1: coupling within the line).

Three encodings of Voynich (ZL glyph units, ZL EVA characters, Takahashi) give the same numbers throughout.

## Description: where Voynich sits (not a verdict)

Scale: two chunks of the same language are 2.7 apart (median, standardised features), two different languages 6.7,
Voynich is 8.0 from its nearest natural source.

- Nearest natural sources: three Old French manuscripts in graphic transcription (8.0-8.5), Syriac (8.1), Quichua
  (8.5), Hebrew (8.6), Swahili (8.7). Latin is 23rd of 67, German 22nd, **Italian 34th**, Turkish 30th, Vietnamese
  20th, Chinese 64th. Nothing here singles out Italian, or any Romance language. That the nearest are abjads (Syriac,
  Hebrew) and abbreviated manuscripts fits low per-symbol information; it is a description, not an identification.
  Among all training chunks the nearest also include the table generator and a digraphic cipher of Quichua.
- Inside the middle 90% of natural languages on 45 of 68 features, including type/token ratio, hapax, Zipf slope and
  curvature, Heaps, the vowel/consonant split and its alternation, the law of abbreviation, burstiness of common
  against mid-frequency words, clustering and vocabulary drift, the subword-token profile, sandhi.
- Outside natural languages, strongest first:

| feature | Voynich | natural median | reading |
|---|---|---|---|
| `m_tail_family` | 1.85 | 1.09 | far more word types share an ending and differ at the start than in any language here |
| `p_jsd_final_med` | 0.74 | 0.19 | word-final symbols are a set apart from word-medial ones |
| `m_suffix_trie`, `m_prefix_trie` | 0.33, 0.42 | 0.54, 0.52 | word types share both starts and ends: few distinct paths through the word |
| `c_h2`, `c_h3` | 2.15, 1.87 | 3.15, 2.34 | the known low conditional entropy |
| `t_merge_len` | 3.37 | 2.62 | the reusable pieces a tokenizer learns are longer |
| `w_len_skew` | 0.16 | 0.87 | word lengths are symmetric; every language here has a long right tail |
| `s_len_ac1_x` | +0.10 | -0.09 | a long word is followed by a long word; in languages by a short one |
| `s_near_adj_x` | +0.015 | -0.004 | neighbours one edit apart, above chance |
| `z_wordid_x` | -0.30 | -1.50 | word order adds less compressible structure than in a language |

Full table in `phase2.md` and `model_results.json`.

## What this adds, and limits

- Trained classifiers do not answer 'is there a language underneath' here: they do not carry over to an unseen
  generator, they misplace all five Voynich-like texts whose nature is known, and Voynich is outside what they were
  trained on. This is a negative result about the method and it applies to any classifier trained on a similar set.
- The descriptive profile repeats phase 1 from a different side: lexicon-level statistics (Zipf, vocabulary growth,
  clustering) are language-like; word-internal structure (few paths through the word, endings and finals a set
  apart, symmetric lengths) and the rhythm of word lengths are not found in any of 67 natural sources.
- Limits. All 50 base languages are Bible translations (genre held constant by design; other genres are 29 chunks).
  Ciphers and generators are this repository's own simple versions. 4,000 tokens a chunk. The generated class lacks
  generators with sequential structure, which is what a second round would have to add (self-citation variants,
  chained slots, topic-driven tables) before the leave-process-out check can pass.

## Reproduce

From `targets/voynich` (Python 3 with numpy, scipy, pandas, scikit-learn):

| step | command | writes |
|---|---|---|
| corpora (git-ignored) | `python phase2/corpora2.py` (Bible corpus, 50 languages, first 40,000 words each); `python lines/fetch_mss.py` (manuscripts); `python fetch_corpora.py` and the `lang/` corpora as in the other READMEs | `data/external/bible/`, `data/external/cremma/` |
| features | `python phase2/build.py` (about 27 minutes) | `phase2/features.csv` (952 chunks x 68 features) |
| models, checks, report | `python phase2/model.py` (about 1 minute) | `phase2/model_results.json`, `phase2/phase2.md` |
| one text | `python phase2/features.py <text file>` | prints the 68 features of its first 4,000 words |
| nearest languages | the ranking above is the distance between the mean standardised feature vector of the 8 ZL-unit chunks and that of each natural source, from `features.csv` | |
