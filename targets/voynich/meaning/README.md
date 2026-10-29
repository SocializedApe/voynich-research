# Does a word belong on its page? Word-swap test (28 Oct 2026)

`swap.py`: for a word w on page i and a decoy v (same log2 frequency band, length +-1, not on page i), which fits
page i better, judged only by page co-occurrence counted on pages more than d away (mean smoothed PMI with the page's
other word types)? Accuracy over about 4,800-5,100 items per text (up to 25 per page); 0.5 = no page context. All texts
poured into the ZL paragraph skeleton (same pages and lines). `--far`: context words within edit distance 2 of either
candidate are ignored, removing the cue of sitting among one's own spelling variants.

| Text | d>0 | d>2 | d>10 | d>30 | --far d>0 | --far d>30 |
|---|---|---|---|---|---|---|
| Latin (la-gutenberg) | 0.731 | 0.729 | 0.733 | 0.699 | 0.732 | 0.708 |
| autocopist (Timm & Schinner, seed 19) | 0.653 | 0.652 | 0.654 | 0.638 | 0.602 | 0.595 |
| Rugg sorted grille | 0.631 | 0.597 | 0.593 | 0.585 | 0.615 | 0.573 |
| **Voynich ZL** | **0.611** | **0.612** | **0.611** | **0.611** | **0.596** | **0.596** |
| Italian (it-renaissance) | 0.556 | 0.552 | 0.557 | 0.561 | 0.551 | 0.555 |
| Naibbe cipher of Latin | 0.517 | 0.514 | 0.512 | 0.519 | 0.534 | 0.521 |
| Voynich, words shuffled over the whole text | 0.508 | 0.508 | 0.513 | 0.513 | 0.516 | 0.514 |

## Reading

- The prediction that a copy-and-modify generator's page context fades with distance failed: the autocopist copies
  from its whole history, and keeps 0.60 even with spelling variants removed. The test does not separate meaning
  from copying; Voynich (0.60) sits with the autocopist, between Italian and Latin.
- Voynich words carry page-specific vocabulary that holds across the book (flat at 0.60-0.61 from d>0 to d>30).
  Naibbe sits at chance (0.52). **Correction (later the same day, `hybrid_code.py`):** this does not show that Voynich
  words are more than letter units. The round-8 letter-unit cipher of `research/voynich_siblings/cipher_models.py`,
  whose variant choices are set per page and drift (k_page, page_nulls, drift), reaches 0.587 at d>30 with no topic in
  the mechanism: page-level cipher settings produce page-specific vocabulary. Only a cipher without page-level
  choices (Naibbe) is excluded by this test.
- Italian's low score is not explained here (the corpus mixes many short texts; not investigated).

# Code or copying generator? (`code_vs_copy.py`)

Spread = pages containing a word / pages expected under random placement (1 = even, lower = clumped), median over
rank bands; near = share of hapaxes within edit distance 1 of a word with frequency >= 5.

| Text | spread 1-10 | 11-50 | 51-200 | 201-1000 | hapax share of types | near | hapax / common mean length |
|---|---|---|---|---|---|---|---|
| Voynich, Currier B pages | 0.88 | 0.84 | 0.87 | 1.02 | 68% | 46% | 6.7 / 5.1 |
| Voynich, all | 0.74 | 0.74 | 0.84 | 1.01 | 70% | 43% | 7.1 / 5.1 |
| Latin | 0.82 | 0.70 | 0.77 | 0.93 | 54% | 13% | 7.4 / 5.7 |
| Italian | 0.99 | 0.94 | 0.91 | 1.00 | 60% | 12% | 8.2 / 5.7 |
| autocopist (seed 19) | 0.64 | 0.58 | 0.68 | 0.73 | 72% | 26% | 7.6 / 4.9 |
| Rugg sorted | 0.76 | 0.71 | 0.63 | 0.62 | 14% | 93% | 5.4 / 4.9 |
| Naibbe | 1.02 | 1.00 | 1.01 | 1.02 | 41% | 68% | 6.2 / 5.5 |
| Voynich shuffled | 0.99 | 1.00 | 1.00 | 1.02 | 70% | 43% | 7.1 / 5.1 |

- Spread: the copy-and-modify generator clumps words at every rank (0.58-0.73); Voynich B (0.84-1.02) lies in the
  Latin-Italian range. Against the autocopist as implemented here (one generator, one seed); not a test of every
  copying process.
- Near: Voynich hapaxes sit in a dense word space (43-46%, languages 12-13%), but not by copying (autocopist 26%);
  the template systems score high (Naibbe 68%, Rugg 93%). Fits template-built words.
- Hapaxes are about 2 units longer than common words in every text: no sign of spelled-out rare words, and no
  discrimination.
- Together with the swap test: template-built words with language-like page distribution. Fits a code whose code
  words follow a template better than either a letter-unit cipher (Naibbe) or this copying generator.

# Synthetic codebook texts against the b3 battery (`codebook.py`, `codebook_results.json`)

Design fixed in the script header before the run: one code word per plaintext word (the b3 Latin and Italian
controls), poured into the ZL skeleton. `codebook_vocab`: Voynich's own word types assigned rank to rank by frequency
(Latin has 11,383 types, so 4,147 extra codes from the template; Italian 6,762, none needed). `codebook_template`:
codes built from Rugg's prefix/middle/suffix lists, shortest to the most frequent words. b3.battery and b3.score
(tolerance from the two autocopist seeds); the circularity control is Voynich's own words shuffled over the text.

| Corpus | b3 items matched (of 37) |
|---|---|
| Voynich ZL (reference) | 37 |
| Voynich, Currier B pages | 34 |
| **codebook_vocab_it** | **28** |
| **Voynich words shuffled (same vocabulary, no order)** | **24** |
| Italian, Rugg sorted | 14 |
| codebook_vocab_la | 13 |
| codebook_template_it | 12 |
| Latin, autocopist s19, autocopist s7 | 9 |
| codebook_template_la | 5 |

(b3's earlier best, Naibbe, matched 17 under the same rule.)

- 24 of codebook_vocab_it's 28 matches are also matched by shuffled Voynich words: they come from the vocabulary,
  not from the code. The Italian word order adds 4: e_cover, e_w10_shuf, e_ratio (self-citation) and h_peak_log2s.
- It fails the sequence items, all in one direction. Voynich against the Italian code: exact adjacent repeats 0.82%
  vs 0.08%; neighbour within edit distance 1 4.1% vs 2.4%; near-copy within 10 words 26.9% vs 22.9%, within the
  previous two lines 40.5% vs 36.3%; MZ peak height 0.287 vs 0.096; next-word top-1 predictability 0.025 vs 0.093;
  first-half/second-half bigram JSD 0.063 vs 0.009; page-adjacency Jaccard excess 0.037 vs 0.025; line-initial
  gallows 22% vs 7%.
- The template codebooks fail the word-internal items (codes too short and too regular) and the Latin vocab code
  fails the vocabulary items (11,383 plaintext types against 7,236).
- Today's tests on the codebooks: page context (swap, d>30) vocab_la 0.590 (Voynich 0.586 in this run), vocab_it
  0.545; spread by rank 0.95-1.02 (language-like, inherited from the plaintext); word-space information 62-76% for
  the vocab codes (inherited from Voynich words), 31-41% for the template codes.

Reading: a one-to-one code of an ordinary Latin or Italian text is disfavoured. Voynich word order is not plaintext
syntax under substituted words: it repeats and near-repeats far more, is far less predictable word to word, clusters
more strongly at long range and drifts between halves. What the code still leaves open is a code plus a process
that varies and repeats nearby words (a copying scribe, `research/voynich_siblings/hybrid_model.md`, or homophone
code words chosen by proximity); that is the next test.

# Zodiac labels: positional names? (`zodiac.py`)

Twelve zodiac pages ($I=Z), 342 label words (17-39 per page). For each of the 66 page pairs the label sequences are
aligned at the best cyclic shift, similarity = 1 - normalised Levenshtein distance over glyph units; null = labels
shuffled within each page, 1,000 times. Observed 0.3202 against 0.3190 +- 0.0019 (z 0.63, p 0.26): the k-th label of
one sign does not resemble the k-th label of another under any alignment, so no calendar-style day or degree names.
278 distinct label words; 37 recur on two or more zodiac pages (oky, ar, otaly, otal, okeey on four), not at matching
positions. The varying counts per page (17-39) also argue against a fixed 30-day scheme.

# Code plus copying scribe against cipher plus copying scribe (`hybrid_code.py`, `hybrid_code_results.json`)

Protocol in the script header, fixed before the run: scribe of `hybrid_model.py` at its tuned setting (q 0.15, w 8,
e 0.9, g 0.2), unchanged, over (a) the round-8 letter cipher of Latin and (b) the Voynich-vocabulary codes of Italian
and Latin; seeds 19 and 7, and q 0.30 as a check. Held-out = the 30 b3 items not used in hybrid_model's tuning.

| Corpus | b3 all | held-out | page context d>30 | held-out misses |
|---|---|---|---|---|
| Voynich | 37 | 30 | 0.607 | |
| code_it + scribe s19 / s7 | 31 / 30 | 25 / 24 | 0.539 / 0.529 | e_ratio, h_peak_R, i_tok_acc, j_jacc_excess, k_jsd_halves (+ h_peak_log2s s7) |
| cipher + scribe s19 / s7 | 28 / 28 | 24 / 24 | 0.552 / 0.584 | b_len1, e_ratio, f_irrev, j_jacc_excess, k_jsd_halves (+ e_w10_shuf s19, h_peak_R s7) |
| code_it alone | 27 | 23 | 0.536 | d_adj_ld1, e_ratio, h_peak_log2s, h_peak_R, i_tok_acc, j_jacc_excess, k_jsd_halves |
| round-8 cipher alone | 22 | 20 | 0.587 | b_len1, d_adj_ld1, e_cover, e_prev2, e_w10_shuf, e_ratio, f_irrev, h_peak_R, j_jacc_excess, k_jsd_halves |
| code_la (+ scribe) | 14-16 | 11-13 | 0.585-0.596 | vocabulary and entropy items (11,383 Latin types) |
| q 0.30: cipher / code_it | 24 / 27 | 21 / 21 | 0.542 / 0.534 | the stronger scribe is worse for both |
| autocopist s19 / s7 | 12 / 15 | 11 / 14 | 0.654 / 0.664 | |

Verdict by the rule fixed in advance: not met. code_it + scribe ties cipher + scribe on held-out items (24-25 vs 24),
and its count is inflated by the borrowed Voynich vocabulary; page context does not separate them (cipher + scribe
does not fall toward chance; code_it + scribe is lower, 0.53-0.54, because the Italian plaintext has weak page
context). The code hypothesis does not become the leading model. Both families fail the same three items, page
adjacency (j_jacc_excess), A/B drift (k_jsd_halves) and the self-citation ratio (e_ratio): what neither supplies is
slow change across the book and stronger similarity between neighbouring pages.

# Drift and carry-over: can a scribe close the three items every model fails? (`drift.py`, `drift_results.json`)

Protocol in the script header: scribe of `hybrid_model.py` (q 0.15, w 8, e 0.9, g 0.2) plus carry c (a copy draws
from the last 30 words of the previous page with probability c) and habit h (on Currier-B pages, a word is rewritten
with probability h: k/t opening gets qo-, one e becomes ee). Grid c, h in (0, 0.3, 0.6), tuned on j_jacc_excess,
k_jsd_halves and e_ratio only; best two settings per base, seeds 19 and 7, through the full battery; test = the other
34 items.

| Tuning items at the best setting (c 0.6, h 0.6) | Voynich | code_it + scribe | cipher + scribe |
|---|---|---|---|
| j_jacc_excess (page adjacency) | 0.037 | 0.027 | 0.017 |
| k_jsd_halves (A/B drift) | 0.062 | 0.018 | 0.009 |
| e_ratio (self-citation) | 1.14 | 1.19 (matched) | 1.26 |

| Corpus | tuning (3) | held-out (34) | all (37) | held-out misses |
|---|---|---|---|---|
| code_it, c 0.6, h 0.6 or 0.3, seeds 19 and 7 | 1 | 29 | 30 | d_adj_exact, d_adj_ld1, h_peak_log2s, h_peak_R, i_tok_acc |
| cipher, c 0.6, h 0.6 / 0.3, seeds 19 and 7 | 0 | 23-24 | 23-24 | b_len1, c_hapax_types, d_adj_ld1, e_cover, e_w10, e_prev2, e_w10_shuf, f_irrev, g_len_last, j_one_page |
| autocopist s19 / s7 | 1 | 11 / 14 | 12 / 15 | |

- Neither mechanism closes the target items: the drift stays 3.5 times too small (0.018 vs 0.062). A spelling habit
  on B pages does not make the A/B switch, which changes the vocabulary itself. The best settings lie on the grid's
  edge (c 0.6, h 0.6); the grid was not extended, since that would turn the test into a fit.
- code_it + scribe + carry + habit reaches 30/37 (29/34 held-out), the highest count of any model in the repo, still
  inflated by the borrowed Voynich vocabulary (shuffled Voynich words alone match 24). Its remaining misses are all
  sequence items: too few immediate repeats, too little long-range clustering, too much word-to-word predictability.
- Carry-over breaks the cipher's self-copying items (e_cover, e_w10, e_prev2 now missed).

# Does the misbinding matter? (`order.py`, `order_results.json`)

Layfield & Davis (Digital Medievalist 19, 2026, doi 10.4000/16k0a) argue the codex is bound out of order (bifolia
meant as singulions). Their reconstructed orders cover two sections only and were chosen to maximise facing-page text
similarity (LSA), so they cannot be used to test adjacency. Instead: each order-dependent item in the current order and
under 30 random orders with pages shuffled within their section (ZL illustration type), plus an order-free adjacency
item, leaf_excess (the two sides of one leaf, always physical neighbours; vocabulary Jaccard minus random pairs).

| Corpus | j_jacc_excess current / shuffled | leaf_excess | k_jsd_halves current / shuffled | h_peak_R current / shuffled |
|---|---|---|---|---|
| Voynich | 0.039 / 0.022 (0.019-0.025) | 0.055 | 0.062 / 0.049 (0.042-0.057) | 0.310 / 0.262 |
| autocopist s19 | 0.003 / 0.002 | 0.005 | 0.024 / 0.020 | 0.514 / 0.522 |
| cipher + scribe | 0.005 / 0.006 | 0.008 | 0.004 / 0.004 | 0.359 / 0.355 |
| code_it + scribe | 0.018 / 0.010 | 0.022 | 0.009 / 0.007 | 0.099 / 0.077 |
| cipher + scribe + carry 0.6 + habit 0.6 | 0.016 / 0.007 | 0.016 | 0.009 / 0.007 | 0.347 / 0.328 |
| code_it + scribe + carry 0.6 + habit 0.6 | 0.027 / 0.012 | 0.030 | 0.018 / 0.013 | 0.118 / 0.077 |

- The current order is not random: adjacent pages share more vocabulary than within-section reorderings (0.039 vs
  0.022). The binding kept many true neighbours.
- Misbinding does not explain the models' failures. The order-free leaf item is the hardest target: the two sides of
  a leaf share far more vocabulary (0.055) than any model (best 0.030). Most of the drift survives any
  within-section reordering (0.049 of 0.062): it lies between sections and scribes, not in the page order; models reach
  at most 0.013. The long-range peak is mostly order-free (0.26 shuffled); codes stay too low (0.08), ciphers slightly
  high (0.33-0.36), the autocopist far too high (0.52).
- Restated without page order, the open target is: every leaf and every section has its own vocabulary, more strongly
  than any tested mechanism produces.

# Duplicate drawings: shared words between a herbal page and the pharmaceutical page that redraws its plant? (`duplicates.py`)

Pairs from René Zandbergen's quire pages (voynich.nu q15 and q19, fetched 28 Oct 2026; `data/voynich_nu/pairs.json`):
fragment N on a pharmaceutical page "appears to be the same plant as" (9 pairs) or "shows some similarity with" (22)
the plant on a herbal folio. The matches are visual, made without the text. For each pair: Jaccard of the two pages'
word types against the pharmaceutical page's Jaccard with other herbal pages of the same Currier language (same hand
where 8 or more exist); score = percentile; null = the herbal page replaced by a control, 10,000 times. All 31
pharmaceutical pages are Currier A; the matched herbal pages are 24 A, 7 B.

| Pairs | n | mean percentile (0.5 = chance) | p (one-sided, >=) |
|---|---|---|---|
| same plant, page vocabulary | 9 | 0.317 | 0.97 |
| all, page vocabulary | 31 | 0.410 | 0.96 |
| same plant, labels of the pharmaceutical page found in the herbal page | 9 | 0.517 | 0.42 |
| all, labels | 27 | 0.503 | 0.47 |
| positive control: the other side of the matched herbal page's own leaf | 30 | 0.650 | 0.0015 |

- The test detects shared vocabulary where it exists (same leaf, 0.65), but pages that redraw the same plant share none:
  same-plant pairs sit below chance (0.32; the lower tail is borderline, about 0.03-0.04 one-sided, not interpreted).
  Labels do not recur on the matched herbal page, as Oocephalus noted informally on voynich.ninja (2016).
- In a meaningful herbal with a remedy section, the plant's name or its properties would be expected to recur beside
  its second drawing. Either the pharmaceutical text is not about the drawn fragments, or a plant's word is not written
  the same way on different pages (as with cipher variant choices set per page), or there is no such word.

# Herbal openings: a recurring entry formula? (`formula.py`)

Herbal pages (ZL type H) with at least four lines, per hand. Mean word-type Jaccard between first lines of different
pages, against second lines and randomly drawn interior lines (200 draws, 95% range). With `--merge-gallows`
(p -> t, f -> k, since f/p are paragraph-first-line forms of k/t) to remove the spelling confound.

| Hand | pages | first lines | second lines | interior (95% range) | first words recurring as another page's first word |
|---|---|---|---|---|---|
| 1, raw | 95 | 0.0130 | 0.0208 | 0.0185 (0.0138-0.0242) | 7% |
| 1, gallows merged | 95 | 0.0143 | 0.0211 | 0.0187 (0.0140-0.0243) | 14% |
| 2, raw | 20 | 0.0096 | 0.0255 | 0.0228 (0.0140-0.0327) | 0% |
| 2, gallows merged | 20 | 0.0108 | 0.0255 | 0.0232 (0.0147-0.0331) | 0% |

No opening formula: first lines share the fewest words across pages (at or below the interior range, also without
their first word), second lines the most. A herbal entry opens with the plant's name, so a distinctive first line is
expected; what is missing is any shared formula after it ('calida est et sicca in ... gradu', 'nascitur in ...',
'valet contra ...'). Against a model herbal of the Circa instans type with fixed phrases, unless those phrases are
written differently from page to page.

# Leaf-wise topical plaintext: Pliny (`pliny.py`, `pliny_results.json`)

Protocol in the script header. Pliny, Naturalis Historia (Latin Wikisource): herbal pages <- books XX-XXIII, pharma
<- XXIV-XXV, recipes/text <- XXVI-XXVII, astronomical/cosmological/zodiac <- II, balneological <- XXXI. 'sectioned':
every leaf starts a new chapter of its section; 'stream': the same books as one continuous text. 100 leaves.

| Corpus | leaf_excess | j_jacc_excess | k_jsd_halves | k_jsd, within-section shuffled | h_peak_R | page context d>30 | b3 (37) |
|---|---|---|---|---|---|---|---|
| Voynich | 0.055 | 0.039 | 0.0624 | 0.0496 | 0.310 | 0.611 | 37 |
| autocopist s19 / s7 | 0.005 / 0.007 | 0.003 / 0.005 | 0.024 / 0.019 | 0.020 / 0.017 | 0.51 / 0.45 | 0.649 / 0.655 | 12 / 15 |
| plain Latin, sectioned | 0.028 | 0.023 | 0.0048 | 0.0039 | 0.192 | 0.615 | 9 |
| plain Latin, stream | 0.034 | 0.031 | 0.0114 | 0.0066 | 0.248 | 0.679 | 12 |
| code + scribe, sectioned | 0.023 | 0.018 | 0.0151 | 0.0073 | 0.168 | 0.611 | 19 |
| code + scribe, stream | 0.027 | 0.023 | 0.0225 | 0.0151 | 0.212 | 0.650 | 15 |
| cipher + scribe, sectioned | 0.007 | 0.005 | 0.0038 | 0.0044 | 0.372 | 0.562 | 28 |
| cipher + scribe, stream | 0.006 | 0.005 | 0.0041 | 0.0040 | 0.356 | 0.562 | 29 |

Same-leaf overlap as a ratio to random page pairs (word-type Jaccard), since an inflected language has a sparse word
space and a small absolute excess: Voynich 1.81 (same leaf 0.124, random 0.069; adjacent 1.59); Pliny stream 1.78
(adjacent 1.71); Pliny sectioned 1.62 (1.51); Italian b3 control 1.29 (1.26).

- Aligning topics to leaves does not raise leaf locality (sectioned 1.62 vs stream 1.78; Pliny's neighbouring
  chapters treat related plants anyway).
- **Correction to the order test above:** in relative terms Voynich's leaf locality (1.81) is what a real topical text
  gives (Pliny 1.78). The absolute leaf_excess gap (0.055 vs 0.028-0.034) comes from Latin's sparse vocabulary. A
  word-level code preserves which words co-occur, so it keeps this property; the letter cipher destroys it (0.006).
- What topic does not produce is the drift: within-section shuffled k_jsd 0.050 for Voynich against 0.004-0.007 for
  plain Pliny. Topic changes words, not letter statistics. Voynich's glyph-pair statistics change between parts of the
  book about ten times more: the A/B difference is a change of writing convention between scribes, not of subject.
- The long-range peak stays above a real text's (0.31 vs 0.19-0.25).
- cipher + scribe of Pliny matches 28-29/37 b3 items without borrowed vocabulary, as the hybrid model did.

# Scribe, topic or page? Where the glyph statistics change (`variance.py`)

Glyph-pair profiles (units inside words, '#' at edges), JSD with add-0.5 smoothing. Cells = (Davis hand, ZL section)
with at least 800 tokens, subsampled to 400 tokens per comparison; noise floor = split halves of a cell. Per-page
heterogeneity = mean JSD of each page against the rest of its cell, over the same with the cell's words shuffled among
its pages (30 shuffles). Controls on the same skeleton and cell labels.

| JSD between cells | Voynich | Pliny plain, leaf-wise | Pliny round-8 cipher + scribe |
|---|---|---|---|
| noise floor (split half) | 0.024 | 0.029 | 0.026 |
| same section, other hand (herbal 1 vs herbal 2; n 1) | 0.115 | 0.028 | 0.031 |
| same hand, other section (n 4) | 0.066 | 0.036 | 0.034 |
| different both (n 10) | 0.100 | 0.034 | 0.031 |

Per-page heterogeneity (observed / shuffled): Voynich 1H 1.28, 2H 1.38, 1P 1.49, 2B 1.69, 3S 2.56, 2T 3.47; Pliny plain
1.07-1.43; cipher with per-page variant choices 1.23-3.07.

- The scribe dominates: the same subject (herbal) by hands 1 and 2 differs about five times the noise floor. A
  topical Latin text, with or without the cipher, stays at the noise floor whatever the labels.
- Within one hand the section matters too (about three times the floor), which topic does not do in a real language;
  it may be the time of writing (sections in separate sessions) rather than the subject, which this test cannot part.
- Pages differ individually beyond sampling, more than topical Latin and about as much as a cipher whose variant
  choices are set per page.
- Fits each scribe having his own conventions, sections written apart, and every page made somewhat anew: either a
  cipher re-set per page in two scribal traditions, or text improvised page by page. It does not fit one meaningful
  text in one fixed writing system.

# How many writing styles? (`scribes.py`)

Pages with at least 60 words (186), features = counts of the 300 commonest glyph pairs (units, '#' at word edges).
Mixture of k multinomials (one style per page), EM with restarts; 5-fold cross-validation over pages.

| k | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Voynich, held-out log-lik per pair | -4.2163 | -4.1652 | -4.1467 | -4.1400 | -4.1348 | -4.1326 | -4.1329 | -4.1339 |
| Pliny plain, same skeleton | -5.0753 | -5.0698 | -5.0685 | -5.0687 | -5.0684 | -5.0694 | -5.0695 | -5.0691 |

Voynich gains 0.083 from 1 to 6 styles and flattens at 5-7; the control gains 0.007 and its clusters match nothing
(ARI with the hand labels 0.15). Voynich k = 5 against Davis's hands, Currier language and sections: ARI 0.50, 0.49,
0.37 (k = 6: 0.52, 0.43, 0.36). The five k = 5 styles: hand 1 herbal A (70 pages); hand 1 pharmaceutical plus some
herbal A (31 + 4 others); hand 2 herbal B with hands 3 and 5 (23 + 11 + 6); hand 2 biological with hand 3 (21 + 6);
hand 3 stars/recipes (11).

- About five or six styles, but not Davis's five hands: hands 1 and 2 each write two styles, by section (herbal vs
  pharmaceutical; herbal B vs biological); hands 4 and 5 (2 and 7 pages) do not form styles of their own.
- The text supports about five ways of writing, which are scribe-by-section combinations. Consistent with
  `variance.py` (scribe first, section within scribe).

# Control: a real multi-scribe manuscript (`auchinleck.py`)

The Auchinleck manuscript (NLS Adv. MS 19.2.1, c. 1331-40): Middle English verse by six scribes whose spellings are
dialectally distinct (LALME: Middlesex, London, Essex, Gloucestershire/Worcestershire border), the strongest ordinary
case of scribe-dependent spelling. NLS diplomatic edition (auchinleck.nls.uk, ed. Alison Wiggins 2003; 42 text pages
fetched 28 Oct 2026, `data/auchinleck_raw`); scribes from the NLS catalogue (1, 2, 3, 5; scribe 4's list of names and
scribe 6 left out). Letters as written (thorn, yogh, '&'), editorial matter removed, 170-word pseudo-pages; same
measure as variance.py on letter pairs. 321,300 words; 35 cells (scribe, text).

| Difference, as a multiple of the text's own split-half noise floor | Voynich | Auchinleck | Pliny (one author) |
|---|---|---|---|
| other scribe | 4.8 (same section, n 1); 4.2 (other section too) | 1.95 (floor 0.041) | about 1 |
| same scribe, other text / section | 2.75 | 1.47 | about 1.2 |
| pages within one scribe and text (observed / shuffled) | 1.28-3.47 | 1.15-1.35 (median 1.20) | 1.07-1.43 |

- Voynich's scribe and section differences are about twice those between dialectally distinct scribes of real Middle
  English, and its pages vary more within a cell than any page set of the control.
- Ordinary scribal spelling, even dialect spelling, does not account for the size of the Voynich A/B switch. Larger
  causes are needed: different writing systems or keys by scribe and section, or text made up page by page.

# Is Currier B Currier A under another key? (`keymap.py`, `keymap_results.json`)

One-to-one mapping of the 20 commonest units of text Y onto those of X (the rest pooled), found by hill climbing
(30 restarts plus identity, 4,000 swaps each), minimising the JSD of unit-pair distributions; 12,000 words a side.
Gap closed = (identity - best) / (identity - split-half floor).

| Comparison | identity | best mapping | floor | gap closed | units remapped |
|---|---|---|---|---|---|
| Voynich herbal A vs herbal B | 0.1004 | 0.0998 | 0.0051 | 1% | 3 (cth<->ckh, f pooled) |
| Voynich herbal A, half vs half | 0.0151 | 0.0144 | 0.0079 | 11% | 1 |
| Pliny vs Pliny under a random letter key (positive control) | 0.6002 | 0.0038 | 0.0028 | 100% | 19 (the key) |
| Latin vs Italian (related languages, no key) | 0.1170 | 0.1121 | 0.0026 | 4% | 3 |
| Auchinleck scribe 1 vs scribe 3 (dialects) | 0.0305 | 0.0305 | 0.0040 | 0% | 0 |

Currier B is not Currier A with a changed glyph-for-glyph key: the search recovers a substitution key completely
(100%) and finds none between A and B (1%). A and B stand as far apart as two related languages, or further.
Limit: only single-unit substitution is tested; a change of multi-glyph tables (verbose cipher) is not.

# Control: improvised gibberish by different people (`gibberish.py`)

Gaskell & Bowern (2022, CEUR 3313 paper 4): 38 volunteer gibberish texts (github.com/danielgaskell/voynich,
`data/gibberish_transcriptions.zip`, fetched 28 Oct 2026; 10,095 words, 79-482 per volunteer); each volunteer is one
'scribe' (30 with at least 200 words). Same measure for all at 100 words a side, 200 draws: unit-pair JSD between two
scribes over the JSD between two halves of one scribe.

| Scribes | between | within | ratio |
|---|---|---|---|
| Auchinleck (real scribes, real text), scribes 1, 2, 3, 5 | 0.1089 | 0.0918 | 1.19 |
| Voynich, Davis hands 1-3 | 0.1071 | 0.0528 | 2.03 |
| Gibberish, one volunteer = one scribe | 0.2680 | 0.0861 | 3.11 |

Voynich's scribes differ much more than real scribes copying real text and clearly less than people who each invent
gibberish from nothing. Read: one shared system (glyphs, word template), written by each scribe his own way; a taught
invented script used freely, or one cipher with per-scribe variants. Limits: the volunteers are modern, write the
Latin alphabet, and produced 200-500 words each; there is no section or page structure to compare.

## Correction: matched documents and bootstrap intervals (`scribe_ratio.py`)

gibberish.py drew a volunteer's within-scribe halves from one short text but a Voynich scribe's from his whole output
(several sections and pages), inflating Voynich's within spread. Redone with every text cut into 200-word documents in
reading order: within = the two 100-word halves of one document; between = 100 words of one document against 100 of
another; bootstrap over documents and scribes (1,000 resamples).

| Documents | scribes | docs | within | between scribes / within [95%] | same scribe, other doc / within [95%] |
|---|---|---|---|---|---|
| Auchinleck | 4 | 1,620 | 0.0905 | 1.42 [1.33-1.55] | 1.32 [1.17-1.33] |
| Voynich, hands 1-5 | 5 | 169 | 0.0501 | 2.97 [2.29-3.46] | 2.00 [1.87-2.13] |
| Gibberish volunteers | 30 | 30 | 0.0885 | 3.16 [2.63-3.81] | (one text each) |

The earlier 2.03 was biased low. With matched documents Voynich's scribes differ as much as independent gibberish
writers (intervals overlap), and clearly more than real scribes copying real text; two documents by the same Voynich
scribe differ more than two documents by different Auchinleck scribes. The reading of the section above is withdrawn:
Voynich's scribe differences are in the range of independent invention, though its scribes share one script and word
template, which the volunteers do not.

# Control: a period 'received' language, Enochian (`enochian.py`)

Dee's text of the Calls (1584; as printed in Casaubon 1659, from the comparison in sacred-texts.com/pag/pr_calls.txt,
fetched 28 Oct 2026): 18 calls, 2,513 words, 1,507 types. 1,000-word samples:

| Text | h1 | h2 | h1-h2 | TTR | hapax/types | mean length | adjacent repeats | Zipf (top 50) |
|---|---|---|---|---|---|---|---|---|
| Enochian (Dee 1584) | 4.18 | 3.49 | 0.69 | 0.71 | 0.82 | 5.52 | 0.000 | -0.74 |
| Voynich herbal A | 3.87 | 2.22 | 1.66 | 0.52 | 0.76 | 4.63 | 0.021 | -0.69 |
| Voynich herbal B | 3.86 | 2.17 | 1.70 | 0.53 | 0.72 | 4.87 | 0.007 | -0.62 |
| Gibberish volunteers (pooled) | 4.36 | 3.77 | 0.60 | 0.83 | 0.89 | 4.76 | 0.001 | -0.50 |
| Latin (Pliny) | 3.95 | 3.32 | 0.63 | 0.68 | 0.82 | 5.96 | 0.001 | -0.62 |
| Italian | 3.94 | 3.14 | 0.80 | 0.50 | 0.73 | 4.64 | 0.001 | -0.67 |

A 16th-century invented 'angelic' language behaves like ordinary language and like modern gibberish (h1-h2 0.6-0.8,
no adjacent repeats), not like Voynich (h1-h2 1.7, repeats 0.7-2.1%). Free invention of words, in any period, does not
give Voynich's glyph structure; that needs a rigid word template.

# Gibberish or meaningful, per scribe? A word-level classifier (`gib_classifier.py`) - fails its sanity check

Logistic regression on word-level features of 200-word documents, trained on Gaskell & Bowern's meaningful corpus (670
documents, 71 texts) against their gibberish (32 documents, 30 volunteers), cross-validated by source: AUC 0.822,
accuracy 0.80. Scored: every Voynich hand 0.97-0.98 P(gibberish) (100% of documents); Enochian 0.53; Auchinleck
scribes 0.44-0.58; Pliny 0.70 (85% of documents called gibberish). The sanity checks fail: real Latin and Middle
English, with many inflected one-off forms, look gibberish-like to a classifier trained on modern texts. Voynich's
score comes mostly from the one-edit neighbour density (weight +0.98), the templated word space that Naibbe-type
ciphers share. Not interpreted as evidence of meaninglessness. The one usable reading is relative: all five hands
score alike.

# Can word-to-word prediction show meaning under a cipher? A power check (`wordpredict.py`, `wordpredict_results.json`)

Each text poured into the ZL skeleton (Voynich's word count); split by page (mod 5: test, validation, training).
Models in bits per word on the test pages: U = unigram + cache of the previous 200 words; B = absolute-discounted
bigram on the previous word (Bw) or on its last two letters (Bs), with the same cache. Order gain U - B; signal = gain
minus the gain with words shuffled within each line (3 seeds). Each plaintext is also enciphered after scrambling its
word order, because the round-8 chaining rule produces a sub-word signal of its own; survival = (signal of the cipher
- signal of the cipher of scrambled text) / (signal of the plaintext - signal of scrambled plaintext).

| Cipher (Latin / Italian) | survival, previous word | survival, last two letters |
|---|---|---|
| one-to-one word code | 1.00 / 1.00 | 0.78 / 0.91 |
| homophonic word code (1-4 code words per word) | 0.44 / 0.46 | 0.04 / 0.05 |
| Naibbe | 0.03 / 0.01 | 0.05 / 0.02 |
| round-8 | 0.02 / 0.00 | -0.04 / 0.00 |

Plaintext signals: Latin 0.469 / 0.359, Italian 0.856 / 0.699 bits/word. Voynich: +0.105 / +0.181, inside the range
that Naibbe and round-8 give from their own machinery (0.12-0.21 word, 0.05-0.46 sub-word) on scrambled plaintext.
Word-sequence statistics detect meaning under word codes, not under Naibbe-type letter ciphers at this length; the
transformer context curves (`tfm/`) share the limit. Voynich's signal is below the homophonic codes, mild evidence
against a simple word code (homophony level not swept).

# Can a cipher make scribes as different as gibberish volunteers? (`cipher_scribes.py`, `cipher_scribes_results.json`)

Five scribes, each enciphering a different stretch of Latin into 15 pages of 120 words (9 documents of 200 words);
scribe_ratio.py's measure unchanged. 'Own tables': each scribe's glyph strings permuted among the codes of each kind,
the same system learned with a different table.

| System | between scribes / within | same scribe, other document / within |
|---|---|---|
| Naibbe, shared tables | 1.02 [0.96-1.07] | 1.02 |
| round-8, shared tables | 1.52 [1.37-1.66] | 1.31 |
| Naibbe, own tables | 1.40 [1.29-1.53] | 1.00 |
| round-8, own tables | 1.63 [1.52-1.75] | 1.30 |
| round-8, scribes 1-2 Latin, 3-5 Italian | 1.53 [1.39-1.68] | 1.31 |
| Voynich (scribe_ratio.py) | 2.97 [2.29-3.46] | 2.00 |
| gibberish volunteers | 3.16 [2.63-3.81] | n/a |

The ciphers' random choices raise the within-document floor and flatten the ratio. No shared or re-learned version of
this family reaches Voynich's scribe differences; only a different system per scribe group (not tested) could.

# Per-scribe systems: a cipher per scribe, shared rules vs habits, a template improviser (`scribe_systems.py`, `scribe_systems_results.json`)

Protocol in the script's docstring, fixed before the run. Every generated text fills the ZL skeleton page by page,
each page by its own Davis hand; hands 1-3 measured (94% of the text). Ciphers: round-8 (hybrid_model.BASE), each hand
enciphering its own stretch of Latin, with Greshko's tables (shared), one table set per Currier group, or one per hand
(tables built from that group's or hand's own Voynich words). No copying scribe on the ciphers. Improviser: a
glyph-unit trigram word model trained on all Voynich words (template borrowed), every transition weight multiplied
by exp(sigma z) per hand and per page, then hybridize at the repo's scribe setting; grid sigma_s 0.3/0.6/1.0, sigma_p
0.2/0.4, chosen on the two scribe ratios only. Rules = share of Y's tokens whose unit trigrams all occur in 2,000
training words of X, over X's own held-out share; habits = cross-entropy of Y under X's unit-bigram model minus X's
own (bits/unit); mean over ordered pairs, 20 draws.

| Text | between scribes / within [CI] | same scribe, other doc / within [CI] | rules | habits | b3 (37) | held-out (30) |
|---|---|---|---|---|---|---|
| Voynich, hands 1-3 | 2.96 [2.18-3.59] | 2.00 [1.87-2.15] | 0.884 | +0.307 | | |
| cipher, shared tables | 1.61 [1.48-1.82] | 1.44 [1.31-1.54] | 0.940 | +0.058 | 23 | 20 |
| cipher, tables per Currier group | 1.87 [1.57-2.08] | 1.45 [1.34-1.56] | 0.642 | +0.353 | 18 | 16 |
| cipher, tables per hand | 2.11 [1.85-2.31] | 1.44 [1.37-1.50] | 0.471 | +0.544 | 17 | 14 |
| improviser sigma_s 1.0, sigma_p 0.4 (chosen) | 2.88 [2.65-3.16] | 1.37 [1.26-1.46] | 0.845 | +0.433 | 25 | 22 |
| Auchinleck scribes 1, 2, 3, 5 | | | 0.847 | +0.188 | | |
| Latin vs Italian | | | 0.563 | +0.766 | | |

Voynich by pair: hands 1-2 rules 0.831, habits +0.467; 1-3 0.864, +0.428; 2-3 0.978, +0.084. Improviser grid (between,
same): 0.3/0.2 1.26, 1.17; 0.3/0.4 1.35, 1.25; 0.6/0.2 1.80, 1.17; 0.6/0.4 1.61, 1.31; 1.0/0.2 2.22, 1.20; 1.0/0.4
2.88, 1.37 (grid edge). Improviser held-out misses: a_h3_raw, b_len9, d_adj_ld1, e_ratio, h_peak_log2s, h_peak_R,
i_char_bits, k_jsd_halves.

- A cipher system per scribe or per Currier group fails: neither ratio reaches Voynich's interval, and separate
  tables break the shared word rules (0.47-0.64, like Latin vs Italian 0.56), while Voynich's scribes share them as
  well as scribes of one language (0.88 vs Auchinleck 0.85). The b3 count also falls (14-16 held-out).
- Voynich's scribes share one word grammar and differ by habit. Currier A (hand 1) against B (hands 2, 3) is a habit
  difference inside one system (rules 0.83-0.86, habits +0.43-0.47); hands 2 and 3 are nearly one writer (0.98, +0.08).
  This qualifies #21: A and B are not one glyph key apart, but they are not two systems either.
- One shared cipher used alike by all scribes gives too small a habit gap (+0.06).
- The improviser matches the between-scribe ratio and the rules/habits pattern but not same-scribe drift (1.37, at
  the grid edge) and matches 22 held-out items against 24-25 for cipher or code plus a copying scribe: not ahead by
  the pre-set rule. Its template is borrowed from Voynich, so its glyph-level matches are partly built in.

## Within one scribe (`keymap_scribe.py`, 3,000 words a side)

| Comparison | identity | best mapping | floor | gap closed |
|---|---|---|---|---|
| hand 1: herbal A vs pharmaceutical | 0.0612 | 0.0601 | 0.0086 | 2% |
| hand 2: herbal B vs biological | 0.0716 | 0.0716 | 0.0087 | 0% |
| hand 1 herbal vs hand 2 herbal | 0.1033 | 0.1024 | 0.0096 | 1% |
| control: hand 1 herbal, half vs half | 0.0159 | 0.0151 | 0.0098 | 13% |
| control: Pliny vs Pliny under a random key | 0.5795 | 0.0130 | 0.0092 | 99% |

Neither the two styles of one scribe nor the styles of two scribes are related by a glyph-for-glyph key. The same
glyphs are used in different proportions and combinations: what changes between scribes and sections is which words
and word shapes are written, not what a glyph stands for.

# Currier A/B against scribe, the unlabelled folios, drift inside A and inside B (`ab_internal.py`, `ab_internal_results.json`)

Protocol in the script header. variance.py compared herbal hand 1 with herbal hand 2, which is also A against B: its
"scribe effect" was scribe and language together. Here cells are (hand, language, section) and one factor is varied at
a time; folio bootstrap (400 draws, 250 tokens a side); floor = folio-level split half (0.049, stricter than
variance.py's word-level 0.024, so the multiples are smaller).

## 1. Which matters more: scribe or A/B?

Hands by language (paragraph tokens): hand 1 A 9,964 / B 0; hand 2 0 / 10,635; hand 3 751 / 10,892; hand 5 0 / 837;
hand 4 unlabelled (500). Only hand 3 writes both, A on two folios (f58r, f58v, ZL section S, bound in quire H among
hand 1's herbal A).

| Differs in | pairs | JSD as a multiple of the floor |
|---|---|---|
| hand only (B herbal: 2 vs 3 vs 5) | 3 | 1.1-2.1 (2BH vs 3BH 1.1, interval 0.037-0.075 includes the floor) |
| section only | 5 | 1.2-1.8 |
| hand + section | 10 | 1.1-2.7 (B-only pairs 1.1-2.1) |
| **language only (hand 3, stars: A vs B)** | 1 | **2.3 [0.089-0.148]** |
| hand + language | 3 | 2.5-3.1 |
| all three | 13 | 2.1-3.6 |

f58 test: f58r+f58v against the rest of 3BS 0.115; any two 3BS folios against the rest (231 pairs) median 0.046, max
0.068. Hand 3's A pages are not page-to-page noise.

- The Currier language outweighs the scribe. Within B, hands 2, 3 and 5 on the same subject differ about as much as
  one hand between sections, and hands 2 and 3 are not separable at this size.
- Hand 3's A is not hand 1's A: 1AH vs 3AS 2.7x, as far as A from B. Markers: -edy 0.8% (A), but cho 7.7%, -ol 6.4%,
  daiin 12 per thousand, where hand 1 has 19 / 14 / 47 and hand 3's B 3.5 / 5.6 / 11. f58 is hand 3's own writing
  with the -edy family switched off.

## 2. The unlabelled folios (hand 4, f67-f70; f68 is one of the four radiocarbon samples)

Rule: nearer of the A and B glyph-pair pools. Calibration on labelled folios cut to the same size: 84% correct at 30
tokens, 96% at 60, 98% at 100. All nine hand-4 folios fall nearer A (margins 0.02-0.06); pooled (500 tokens) JSD A
0.051, B 0.091. Markers: -edy 0.8%, cho 7.6%, -ol 8.2%, daiin 22. f65v (hand 3, 39 tokens) is a tie.

- Hand 4's text is A by its endings, and like hand 3's A it sits between hand 1 and B on cho and daiin.
- The radiocarbon samples therefore cover A three times (f8, f47 hand 1; f68 hand 4) and B once (f26, hand 2): same
  calfskin date, 1404-1438, on both sides. Radiocarbon cannot order them.
- Read with section 1: the A with the -edy family absent is shared by hands 1, 3 and 4; the heavy cho/daiin profile is
  hand 1's alone.

## 3. Drift inside A and inside B

Folios with at least 80 tokens; cells with at least 8. order = Spearman rho between distance in the current binding
and folio JSD (Mantel, binding positions permuted within the cell); quire = mean JSD between quires minus within a
quire (quire labels permuted). Language rows = mean over cells, stratified permutations (2,000).

| | A: rho (p) | A: quire excess (p) | B: rho (p) | B: quire excess (p) |
|---|---|---|---|---|
| **Voynich** | +0.218 (0.0005) | **+0.0124 (0.0005)** | +0.047 (0.17) | **+0.0273 (0.0005)**, 2BH only |
| words shuffled within cell | -0.025 (0.67) | -0.0003 (0.62) | +0.080 (0.09) | +0.0007 (0.36) |
| Pliny plain, leaf-wise, same cells | +0.167 (0.002) | +0.0021 (0.05) | +0.209 (0.0005) | +0.0034 (0.07) |

Per cell (Voynich): 1AH rho +0.10, quire +0.008 (36 folios, 9 quires); 1AP +0.34, +0.016 (15, 2); 2BH +0.22, +0.027
(18, 4); 2BB -0.11 and 3BS +0.03 (one quire each, no quire test).

- Drift inside one language is measurable and present in both. Its form is a quire effect: each quire has its own
  glyph-pair profile, inside one hand, one language and one section, 6x (A) to 8x (B) what topic changes give in Latin.
- The order trend (pages far apart differ more) does not distinguish Voynich: topical Pliny gives the same rank
  correlations. Within the two single-quire B cells (biological, stars) there is no trend along the binding.
- Fits text made in batches (quire by quire, sessions) with conventions drifting between batches. The A/B switch is the
  largest such step, not a different kind of thing in magnitude: A vs B 2.3-3.1x the floor, quire-to-quire inside a
  cell well below that.

Limits: f58 and hand 4 rest on 751 and 500 tokens; Davis's hand assignments are taken as given (expert judgment, not
replicated); the quire test exists only where a cell spans several quires (1AH, 1AP, 2BH).

# The duel inside one shared system: cipher with habits vs template improviser (`duel.py`, `duel_results.json`)

Protocol in the docstring, fixed before the run. Both sides: ZL skeleton by hand, same copying scribe. Cipher:
round-8, Greshko's tables shared, each free table draw weighted by exp(s z) per hand and exp(p z) per page and
plaintext unit (grid s 0.5/1/2, p 0.3/0.6/1). Improviser: scribe_systems.Improviser, s 1/1.5, p 0.4/0.7/1. Best of
each side chosen on the two scribe ratios (hands 1-3) only; then rules/habits and b3.

| Text | between / within | same scribe / within | inside CI | rules | habits | b3 (37) | held-out (30) |
|---|---|---|---|---|---|---|---|
| Voynich | 2.96 [2.18-3.59] | 2.00 [1.87-2.15] | yes | 0.890 | +0.317 | | |
| cipher + scribe, no habits | 1.62 | 1.52 | no | 0.958 | +0.039 | 26 | 21 |
| cipher + scribe, habits s 0.5 p 0.3 (chosen) | 1.65 | 1.54 | no | 0.955 | +0.053 | 25 | 21 |
| improviser s 1.0 p 1.0 (chosen) | 2.61 [2.38-2.82] | 2.16 [1.86-2.44] | no (same by 0.01) | 0.853 | +0.181 | 15 | 14 |

Cipher grid: every setting 1.60-1.65 / 1.49-1.54. Improviser grid (between, same): 1.0/0.4 2.86, 1.36; 1.0/0.7 2.64,
1.69; 1.0/1.0 2.61, 2.16; 1.5/0.4 4.02, 1.35; 1.5/0.7 4.45, 1.75; 1.5/1.0 3.98, 2.29. Improviser held-out misses add
the vocabulary and entropy items (a_h3_raw, a_h2_mrg, c_ttr, c_hapax_tokens, c_heaps, b_len9, g_len_last) to those
both sides miss (b_len1, e_ratio, h_peak_R, i_tok_acc, i_char_bits, j_jacc_excess, k_jsd_halves).

- Habits on round-8's free choices are invisible: the chaining rule and the page table subsets set the glyph
  statistics, so this cipher cannot carry a scribe's or a Currier group's convention.
- The improviser reaches the scribe ratios only with page drift that wrecks the vocabulary statistics.
- The pre-set rule names the cipher (21 vs 14 held-out), but it fails the scribe test and the improviser misses it
  by 0.01; the result is a trade-off, not a winner. b3 counts here are comparable only within this run (the scoring
  set differs from hybrid_code.py's).

# Repeated phrases (`phrase_repeats.py`, `phrase_repeats_results.json`)

Distinct word n-grams occurring at least twice, first 30,000 tokens of each text; and per 250-word document. Finnish
corpora left out (mostly Project Gutenberg licence text, which repeats verbatim).

| Text | 2-grams | 3-grams | 4-grams | 5-grams |
|---|---|---|---|---|
| **Voynich (ZL)** | 2,040 | **134** | **1** | **0** |
| Latin (Vulgate) / Italian / English / German | 2,856-3,628 | 926-1,585 | 221-559 | 66-292 |
| Icelandic (heavily inflected) | 2,727 | 952 | 344 | 178 |
| Naibbe cipher of Latin | 2,247 | 113 | 1 | 0 |
| autocopist | 615 | 12 | 0 | 0 |
| Rugg grille | 6,573 | 6,197 | 5,997 | 5,956 |

Per 250-word document (2-, 3-, 4-grams): Voynich 2.90 / 0.09 / 0.00; gibberish volunteers 6.86 / 1.86 / 0.48; Italian
5.54 / 0.81 / 0.16; Latin 9.95 / 3.19 / 1.33; Icelandic 10.00 / 3.34 / 1.56; Naibbe 0.70 / 0.01 / 0.00.

- Voynich has one repeated 4-word phrase in the book (ol shedy qokedy qokeedy, twice, on nearby pages). Every language
  has hundreds, an inflected one included; people improvising gibberish repeat phrases more than Voynich does.
- The Naibbe cipher of Latin reproduces the count almost exactly (113 / 1 / 0): when the same plaintext is spelled with
  random choices each time, phrase repeats vanish. Voynich's 3-grams are 6x a word shuffle (22) and its 2-grams per
  document 4x Naibbe's, which fits local near-copying on top. Naibbe stays disfavoured on other grounds (#7, b3).
- Consequence for crib attacks: with no repeated phrases, there is nothing to anchor a crib, and a mechanism that
  removes repeats is one where a known plaintext would not give a fixed ciphertext.

# Robustness of #25, #27, #28, #33 (`robustness.py`, `robustness_results.json`)

Homophony sweep (#25), previous-word signal in bits/word, every type with at least 5 tokens given K code words:

| K | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| Latin code | 0.469 | 0.281 | 0.149 | 0.081 | 0.038 |
| Italian code | 0.856 | 0.588 | 0.362 | 0.187 | 0.120 |

Voynich +0.105 lies between K 4 and 8 (Latin) and near K 16 (Italian). The earlier reading (Voynich below a homophonic
code, mild evidence against a word code) holds only for codes with up to 2-4 code words per frequent word.

Generator seeds 0-2, scribe ratios on hands 1-3 (Voynich 2.96 [2.18-3.59], 2.00 [1.87-2.15]): cipher with tables per
hand 2.11 / 1.43, 2.18 / 1.46, 2.13 / 1.45; cipher with habits s 2.0 p 1.0 1.56 / 1.47, 1.67 / 1.51, 1.69 / 1.54. The
per-hand cipher's between-scribe ratio reaches the edge of Voynich's interval in one seed; its same-scribe ratio
fails in all three. Habits stay without effect.

Rules / habits, 5 repeats of 20 draws: Voynich 0.892 [0.884-0.898] / +0.307 [+0.295-+0.320]; Auchinleck 0.849
[0.847-0.852] / +0.184 [+0.182-+0.191]; per-hand cipher 0.451 [0.446-0.454] / +0.558 [+0.554-+0.565]. Voynich's scribes
share rules slightly more than Auchinleck's and differ in habits clearly more; the separation from separate tables is
far outside the spread.

# Which slot carries the A/B difference? prefix + gallows + middle + ending (`slots_ab.py`, `slots_ab_results.json`)

Parse fixed in advance (script docstring): ending = longest of a fixed list (aiin, ain, iin, edy, eedy, dy, y, ol, or,
...); prefix = qo, q, o, y, d, s, l, r; gallows = cth, ckh, cph, cfh, k, t, p, f right after the prefix, else none;
middle = the rest. Filled: prefix 53%, gallows 40%, middle 57%, ending 99%. Measure: I(slot; label) on tokens,
classes balanced, minus a null that permutes labels between folios (200 permutations).

| Slot | A vs B excess (bits) | z | hand 2 vs 3 (B) excess | quire, hand-2 B pages, excess |
|---|---|---|---|---|
| prefix | 0.043 | 50 | 0.009 | 0.047 |
| gallows | 0.025 | 53 | 0.003 | 0.019 |
| middle | 0.064 | 33 | 0.025 | 0.094 |
| ending | 0.130 | 72 | 0.021 | 0.084 |
| whole word | 0.252 | 63 | 0.059 | 0.208 |

Largest A/B shifts (share in A, in B): ending -edy 0.001 / 0.122, -eedy 0.001 / 0.051, -or 0.101 / 0.038, -ol 0.142 /
0.071, -ain 0.021 / 0.059; prefix l- 0.005 / 0.051, qo- 0.093 / 0.169, d- 0.135 / 0.061; gallows cth 0.039 / 0.004,
ckh 0.018 / 0.004, k 0.16 / 0.236.

- Every slot differs between A and B (z 33-72), so the core is not fixed; but the ending carries about half the
  difference and the gallows the least. The slot excesses add up to about the whole-word excess (0.262 vs 0.252): the
  A/B difference is roughly a slot-by-slot change, not a change of whole words.
- -edy and -eedy are almost absent from A (at most 3 tokens on any of the commonest B -edy stems: chedy 1 in A vs 492
  in B, shedy 2 vs 421, qokeedy 0 vs 307). On the same stems A writes -ol, -y, -or, -ey, -o, -eol (pooled over the 30
  commonest stems: ol 891, y 703, or 544, ey 482): no one-to-one replacement, so not a simple spelling rewrite of one
  ending into another. A near-categorical rule (an ending A does not use), on top of reweighting.
- Hand 2 vs 3 inside B differs about four times less (word 0.059), spread over middle, ending and prefix.
- Quire drift inside hand 2's B is spread over all slots (middle 0.094, ending 0.084, prefix 0.047), not led by the
  ending as A/B is.

# A convention layer: one system rewritten toward A or B, with quire drift (`convention.py`, `convention_results.json`)

Protocol in the docstring, fixed before the run. Each word type is rewritten slot by slot (slots_ab.parse) toward
Voynich's own A or B slot distributions (each slot redrawn with probability lam, fixed per type and group), plus a
weaker rewrite per quire (lam_q). Bases: cipher + copying scribe (duel.py) and the improviser s 0.6, p 0.2. Grid lam
0.3/0.6/1.0, lam_q 0/0.15/0.3; chosen on the scribe ratios only. The layer's targets come from Voynich, so A/B matches
are partly built in.

| Text | between / within | same scribe / within | rules | habits | k_jsd_halves | b3 (37) | held-out (30) |
|---|---|---|---|---|---|---|---|
| Voynich | 2.96 [2.18-3.59] | 2.00 [1.87-2.15] | 0.891 | +0.307 | 0.0624 | | |
| cipher + scribe | 1.62 | 1.52 | 0.956 | +0.049 | 0.0069 | 26 | 21 |
| cipher + scribe + layer (1.0, 0.3) | 2.28 | 1.46 | 0.835 | +0.278 | 0.0372 | 25 | 23 |
| improviser | 1.81 | 1.16 | 0.930 | +0.171 | 0.0237 | 23 | 20 |
| improviser + layer (1.0, 0.3) | 2.13 | 1.32 | 0.812 | +0.311 | 0.0394 | 26 | 24 |

Held-out misses with the layer: cipher b_len1, d_adj_ld1, h_peak_log2s, h_peak_R, i_tok_acc, j_jacc_excess,
k_jsd_halves; improviser the same less i_tok_acc. Both chosen points are at the grid edge (lam 1.0, lam_q 0.3).

- Not a success by the pre-set rule for either base: the same-scribe ratio stays low (1.46, 1.32 vs 2.00) and
  k_jsd_halves, though five times higher than without the layer, stays below Voynich (0.037-0.039 vs 0.062).
- The layer helps every measure it touches: the habit gap reaches Voynich's (+0.28/+0.31 vs +0.31), the between-scribe
  ratio enters Voynich's interval for the cipher (2.28), held-out b3 rises (21 to 23, 20 to 24). The rules fall a
  little below Voynich (0.81-0.84 vs 0.89).
- What is still missing is variation at the scale of documents and quires: the same-scribe ratio and the size of
  the A/B drift. The two bases end level (24 vs 23 held-out, under the 2-item margin of duel.py): the layer does not
  separate cipher from improvisation.

# A stem + ending code (`stemcode.py`, `stemcode_results.json`)

Protocol in the docstring, fixed before the run (one pre-run fix recorded there: cores composed slot by slot from
Voynich's conditionals, because whole Voynich triples left too few distinct cores). Each plaintext word = stem +
grammatical ending (fixed ending lists for Latin and Italian); the stem becomes one of K homophone cores (prefix +
gallows + middle), the ending a Voynich ending by a shared rank table. A pages from Latin, B from Italian; control LL
with both Latin.

| Text | slot indep. | 3- / 4-word repeats | word signal | A/B excess prefix / gallows / middle / ending / word | between / same scribe | rules / habits | held-out b3 |
|---|---|---|---|---|---|---|---|
| Voynich | 0.107 | 144 / 1 | +0.105 | 0.043 / 0.024 / 0.064 / 0.130 / 0.253 | 3.01 / 2.01 | 0.891 / +0.307 | |
| code K4 | 0.051 | 56 / 7 | +0.278 | 0.008 / 0.005 / 0.194 / 0.225 / 0.576 | 1.21 / 1.05 | 0.821 / +0.104 | 7 |
| code K4 + scribe | 0.044 | 20 / 3 | +0.170 | 0.007 / 0.005 / 0.177 / 0.193 / 0.478 | 1.36 / 1.20 | 0.846 / +0.088 | 6 |
| code K8 | 0.042 | 9 / 0 | +0.099 | 0.005 / 0.001 / 0.161 / 0.215 / 0.506 | 1.16 / 1.03 | 0.849 / +0.096 | 6 |
| code K8 + scribe | 0.037 | 2 / 0 | +0.063 | 0.004 / 0.001 / 0.151 / 0.182 / 0.420 | 1.31 / 1.18 | 0.874 / +0.083 | 6 |
| code K8 + scribe, Latin for A and B | 0.017 | 2 / 0 | +0.023 | 0.002 / 0.000 / 0.037 / 0.018 / 0.117 | 1.27 / 1.23 | 0.929 / +0.026 | 6 |

- No variant fits by the pre-set rule; all fail b3 badly (6-7 of 30 held-out: word length, glyph entropies, Zipf,
  vocabulary growth, repetition, long-range items). The composed cores do not make Voynich-shaped words.
- Measurement note: slot independence computed here with glyphs/variants.UNIT gives Voynich 0.107, not the 0.040 of
  slot_independence.md (other unit set). The pre-set threshold (<= 0.08) was taken from that file; on the matched
  measure the codes (0.04-0.05) are more slot-independent than Voynich, not equal to it.
- What the run does show: two plaintext languages under one shared stem + ending code give an A/B split led by the
  ending, and the Latin-only control removes it (ending 0.18-0.23 against 0.018). That is the mechanism #35 asks for.
  But it overshoots (whole word 0.42-0.58 vs 0.25), puts the rest in the middle slot, and leaves prefix and gallows
  unchanged (Voynich shifts both).
- The homophony that brings the word-order signal to Voynich's (K 8: 0.099 vs 0.105) leaves too few repeated phrases
  (2-9 vs 144; K 4 without scribe 56) and flattens the scribe ratios (1.2-1.4 / 1.0-1.2), as for the ciphers in #26:
  random homophone choice raises the within-document floor.
