# Voynich MS 408: one-session adjudication (draft notes)

Status: DRAFT, unvalidated. Each number is either (S) computed this session by a named script in `targets/voynich/` (a1 to a6, adversarially re-run by v_a1 to v_a6; corrected figures used where the verifier changed them) or (L) quoted from the literature as returned by the research pass. Judgment and inference are marked (*).

## 1. Verdict and confidence

**Excluded (high confidence*, transcription-robust):** plaintext, 1:1 substitution, letter transposition, vowel-less (abjad) rendering, or single-glyph-null padding of any of eleven European languages (Latin, Italian, German, English, French, Danish, Dutch, Swedish, Norwegian, Icelandic, Finnish) in standard word segmentation. Conditional character entropy h2 is 2.18 to 2.35 bits (raw EVA) and 2.66 to 2.89 bits under three independent glyph segmentations, against a natural-language floor of 3.32 bits (S: a1, v_a1, v_a5). Any transposition of Latin gives h2 >= 3.44 (S: v_a5); vowel deletion leaves Latin at 3.52 (S: a1).

**Disfavoured*:** an unenciphered low-entropy non-European language (nearest published h2 2.77, Hawaiian; L: Lindemann & Bowern 2021); every published decipherment 2014 to 2026 (L: no reproducible key); Rugg's grille and free-edit self-citation as the actual mechanism (section 5).

**Live, not separated by this session:** (a) a verbose or positional cipher of short plaintext units (one unit -> a rigid 2 to 3 symbol group); (b) structured meaningless text from a table or slot-preserving copy-and-modify procedure. Every statistic that separates Voynichese from language is reproduced by at least one member of each class. Judgment*: roughly even between (a) and (b); the literature is in the same position (L: both consensus summaries).

## 2. Strongest counterargument first

All character statistics assume the transliteration and that EVA spaces mark plaintext units. Latin re-segmented after {e, s, m} moves 60% of the way to Voynichese slot rigidity, and Latin cut into vowel-final syllables is more rigid than Voynichese at equal length (S: v_a3). The exclusion therefore covers only word-boundary-preserving encodings of eleven languages in modern orthography; rule-based re-segmentation, or a CV-rigid language written syllabically, was not tested. Second, the verbose control that matches raw EVA on h1, h2 and h2/h1 at once yields words 2.3x too long (11.5 vs 5.07 symbols) with Latin word entropy, so a letter-level verbose cipher of whole Latin words is refuted by the session's own word-level data (S: v_a1). Both narrow the verdict; neither overturns it.

## 3. Session data versus quoted data

(S) ZL3b-n, paragraph text only, 34,116 to 34,212 tokens after dropping `?` and extended-glyph tokens; Currier A about 10,750, B about 22,900. Cross-checked on RF1b, IT2a, GC2a v101 and Currier CD2a. Language controls are single Gutenberg books and an OCR'd 16th-century Italian corpus with about 8% Latin tokens (S: v_a1, v_a3). Entropies are plug-in; Miller-Madow changes h2 by <= 0.007 (S: v_a1).

(L) As returned by the research passes; the paywalled Cryptologia papers (Rugg, Schinner, Timm & Schinner, Daruka, Greshko) were characterised from abstracts and secondary summaries.

## 4. Key statistics (S)

### 4.1 Character entropies, bits, no spaces (a1, v_a1, v_a5)

| Text | h1 | h2 | h1-h2 | h2/h1 | mean word length |
|---|---|---|---|---|---|
| ZL raw, Currier A | 3.832 | 2.353 | 1.479 | 0.614 | 4.98 |
| ZL raw, Currier B | 3.859 | 2.182 | 1.677 | 0.565 | 5.12 |
| ZL raw, all | 3.865 | 2.311 | 1.554 | 0.598 | 5.07 |
| ZL merge2 (benches, i/e groups, aiin, qo) | 4.039 | 2.870 | 1.170 | 0.710 | 3.7-3.9 |
| GC v101 (68 symbols) | 4.144 | 2.893 | 1.25 | 0.698 | 3.7-4.0 |
| Latin, Aeneid | 4.025 | 3.510 | 0.515 | 0.872 | 5.77 |
| German (folded 3.335) | 4.160 | 3.391 | 0.769 | 0.815 | 4.88 |
| Range, 11 languages (floor 3.32 folded) | 3.94-4.52 | 3.32-3.88 | 0.49-0.77 | 0.82-0.88 | 4.2-6.6 |
| Latin, vowels removed | 3.659 | 3.515 | 0.144 | 0.961 | 3.11 |
| Verbose24 cipher of Latin, all letters 2-3 symbols | 3.901 | 2.325 | 1.576 | 0.596 | 11.52 |
| Verbose24, 8 letters single | 4.102 | 2.916 | 1.186 | 0.711 | 7.64 |

Currier CD2a gives h2 2.660 (S: v_a5). Within-word h2 is 1.92 to 2.13 raw against 2.94 to 3.41 for languages: the redundancy is inside words (S: a1). Positional mutual information I(symbol; position) is 0.69 to 0.73 bits across ZL, Currier and v101 against 0.17 to 0.27 for languages; 21 to 31% of glyphs are locked to one word position against 0 to 8% of letters (S: a5, v_a5). Greedy pair merging closes the h1-h2 gap only after about 40 merges, so a code of 2 to 3 units from 50 to 60 unit types is compatible (S: a5). Word-level budget: 425,468 bits, 12.47 bits per token, 0.82x a Latin prose text of equal length (S: a5, v_a5).

### 4.2 Zipf, hapax, vocabulary growth (a2, v_a2), 34,116 tokens

| Corpus | Zipf slope r1-1000 | hapax % types | Heaps beta | top-1 share |
|---|---|---|---|---|
| Voynich all | -1.040 | 69.7 | 0.710 | 2.25% |
| Voynich A / B | -0.994 / -1.068 | 72.2 / 68.6 | 0.743 / 0.679 | 4.27% / 2.13% |
| Latin | -0.820 | 67.0 | 0.749 | 4.9% |
| German | -1.045 | 65.1 | 0.779 | 3.46% |
| English | -1.056 | 55.1 | 0.675 | 4.68% |

All language-like; word-type entropy 9.8 to 10.3 bits against 10.3 to 10.8 for Latin prose and 9.4 to 9.8 for Italian, French, German (S: v_a1). Robust to IT2a. The low top-1 share is an A+B mixture effect (S: v_a2).

### 4.3 Word length, merged EVA (a2, v_a2)

| Corpus | mean | variance | var/mean of (L-1) |
|---|---|---|---|
| Voynich all (raw EVA: 5.07 / 3.73 / 0.92) | 4.11 | 2.48 | 0.80 |
| Voynich A | 3.93 | 2.89 | 0.99 |
| Voynich B | 4.20 | 2.27 | 0.71 |
| Aeneid alone / Confessions alone | - | 4.97 / - | 1.04 / 1.74 |
| Italian / German / English / Danish | 4.53 / 4.99 / 4.23 / 4.67 | 6.52 / 7.04 / 5.41 / 7.40 | 1.85 / 1.77 / 1.67 / 2.02 |

Correction (v_a2): under-dispersion is a Currier-B property; A matches single-text Latin verse. The binomial-cap contrast in a2 was an artefact (raw ALL has a finite optimum at n=52).

### 4.4 Word grammar rigidity and repetition (a3, v_a3, a2)

| Statistic | Voynich | Latin | Italian | German | English |
|---|---|---|---|---|---|
| Pair-violation fraction vs best glyph order, length-matched (shuffle null 0.49) | 0.160 (v101 0.140) | 0.363 | 0.318 | 0.278 | 0.308 |
| Adjacent identical tokens, % / observed:shuffled | 0.907 / 2.5 | 0.047 / 0.1 | 0.047 / 0.1 | 0.157 / 0.3 | 0.137 / 0.2 |
| Line-initial first-symbol effect, Cramer's V, paragraph lines excluded | 0.277 | pseudo-lined prose 0.02-0.03; hexameter 0.148 | | | |

Voynichese is 1.7 to 2.3x more rigid than any tested language (a3's 2.0 to 2.3x corrected by v_a3). The data-derived glyph order q | p f sh | ch | o t k | e ee | d s a | l r y | g n iin m is the Stolfi/Zandbergen layout recovered without assumptions (S: a3). The line-final effect in a2 collapses to V 0.07 to 0.16 once m/g allographs are removed; the line-initial effect survives (S: v_a2).

### 4.5 Self-citation distances (a4, v_a4): nearest earlier token at edit distance <= 1 on the same page, all corpora poured into the identical page/line skeleton

| Corpus | median distance | within 10 tokens | within-page shuffle | global shuffle | long tokens (>=5) within 10 |
|---|---|---|---|---|---|
| Voynich ZL | 14 | 0.269 | 0.238 | 0.167 | 0.225 |
| Latin (Aeneid) | 41 | 0.035 | 0.034 | 0.030 | 0.006 |
| English (Italian, German similar) | 17 | 0.176 | 0.177 | 0.164 | 0.019 |
| Danish (verse) | 15 | 0.196 | 0.172 | 0.138 | 0.035 |
| Autocopist (Timm-Schinner re-implementation, seed 19) | 13 | 0.329 | 0.275 | 0.079 | 0.257 |
| Rugg grille | 36 | 0.067 | 0.249 | 0.066 | 0.033 |
| Rugg sorted table | 34 | 0.329 | 0.162 | 0.112 | 0.341 |
| Order-3 character Markov model trained on Voynich | 19 | 0.194 | 0.194 | 0.194 | 0.119 |

Sequential excess (real minus within-page shuffle): Voynich +0.031, Danish verse +0.024, autocopist +0.054, prose about zero. Page-vocabulary excess (real minus global shuffle): Voynich +0.102, languages <= +0.058, autocopist +0.250. For long tokens language baselines collapse to <= 0.035 while Voynichese stays at 0.225; a memoryless character model reaches 0.119, so about half of that density is word-internal structure, not copying. Brute-force Levenshtein reproduced every Voynich locality figure exactly (S: v_a4).

### 4.6 Generator comparison (a4, v_a4, a3)

| Text | types | h2 raw | h2 merged | Zipf slope | hapax % | adjacent repeat | pair-violation |
|---|---|---|---|---|---|---|---|
| Voynich ZL | 7,236 | 2.311 | 2.646 | -1.040 | 69.7 | 0.0082 | 0.160 |
| Autocopist s19 / s7 | 11,660 / 11,330 | 2.709 / 2.723 | 3.274 / 3.005 | -0.825 / -0.859 | 72.2 / 71.1 | 0.0013 / 0.0018 | a3 free-edit 0.41-0.46 |
| Rugg grille / sorted table | 3,747 / 1,757 | 2.798 / 2.629 | 3.176 / 2.912 | -0.429 / -0.622 | 5.7 / 13.9 | 0.0003 / 0.0893 | a3 fitted table 0.122 |

No generator matches on all columns. The autocopist yields only 37% real Voynich word types by token (9% by type), 2% qo-initial words against 15%, and h2 0.4 to 0.6 bits too high (S: v_a4, a4); it is a4's re-implementation of Timm's Java with documented deviations, not the reference binary. Grilles fail Zipf and hapax. The a3 table that reproduces slot rigidity had its columns read off Voynichese (sufficiency only; S: v_a3).

### 4.7 Currier A/B (a6, v_a6)

| Statistic | A | B |
|---|---|---|
| Tokens ending -edy / containing ed | 0.20% / 0.29% | 17.34% / 20.84% |
| Containing cho / starting qo- / ending -ol | 16.1 / 10.0 / 14.5% | 2.7 / 17.7 / 7.1% |
| Character after ch: e / o | 24.5 / 46.1% | 60.1 / 10.1% |
| daiin per mille | 42.5 | 13.0 |

Unsupervised folio clustering recovers Currier's labels at 95.4 to 99.5% on 197 folios; one -edy threshold separates them at 99.5% leave-one-out (A max 2.42%, B min 3.23%); A is a spike (112 of 114 folios below 2%), B a continuum 3 to 42%; same in IT2a (S: v_a6). Language is nearly a function of Davis's hand: H(lang | hand) = 0.09 bits, 98.2% predicted from hand alone; the only mixed cell is hand 3 in the stars section (80 A lines, 1,039 B). Vocabulary sharing A vs B, size-matched: Jaccard 0.147, top-100 overlap 0.95, against A-half vs A-half 0.207 / 1.00, two English novels 0.172 / 0.91, Danish vs Norwegian 0.116 / 0.67. A word-final pattern shifting 0.2% to 17% has no parallel among same-language book pairs but does among language pairs (French vs Italian -o 0.19% to 17.5%) (S: v_a6). Section-specific vocabulary exists (mean chi2/n 0.654 vs 0.121 shuffled, 0.40 Italian) and persists within one scribe and language (hand 2: 0.291 vs 0.085 shuffled vs 0.19 to 0.24 Italian), but the section words are members of the same sub-word families (qokain, qol, qokeedy, okeol), not content-word-like vocabulary (S: v_a6).

## 5. Hypothesis status

**Excluded.** (1) Plaintext or monoalphabetic substitution of the 11 tested languages: h2 gap >= 1.0 bit raw, >= 0.4 bit merged (S: a1, v_a1; L: Bennett 1976, Zandbergen, Lindemann & Bowern 2021). (2) Substitution plus vowel removal or conventional abbreviation (S: a1, a5; L: Lindemann & Bowern 2021). (3) Letter-level transposition including grille rearrangement of a real plaintext (S: v_a5; L: Parisel 2026, preprint). (4) Vigenere-type polyalphabetics (L: Stolfi 2000). (5) Single-glyph nulls as the source of the redundancy (S: a5). (6) Named decipherments: Cheshire 2019 (L: refuted); Hauer & Kondrak 2016 as a decipherment (L: authors' caveat); Gibbs, Ardic, Gladyseva, Schechter and LLM-assisted readings (L: no reproducible key).

**Disfavoured*.** Unenciphered exotic language (L: nearest h2 2.77). Rugg's grille as the mechanism: Cardan grilles date from c. 1550 against 1404 to 1438 vellum, the f/p problem is unsolved (L: Zandbergen 2021), and the session grilles fail Zipf and hapax (S: a4). Free-edit self-citation: over-produces locality and vocabulary, under-produces character redundancy, while the manuscript's sequential copy excess is only Danish-verse-sized (S: a4, v_a4). Dee/Kelly glossolalia (L: Daruka 2020; conflicts with vellum date).

**Live.** (a) Verbose or slot-template cipher of short units, nomenclator, or constructed language: compatible with 4.1, 4.4, 4.7 and with Naibbe feasibility (L: Greshko 2025; Bowern & Gaskell 2022), but must also meet the word-length constraint (verbose controls give 7.6 to 11.5 symbols; S: v_a1), near-zero token-to-token predictability (L: Rozanova & Temerev 2026, preprint) and the line-initial effect (S: v_a2). (b) Slot-preserving copy-and-modify generation (L: Timm & Schinner 2020): compatible with everything measured, but the slot grammar is an input to that model, not a product (S: a3), and it has not been run at manuscript length against page, section and scribe structure (L: consensus). (c) A real language under a non-word segmentation: untested (S: v_a3).

## 6. Physical evidence constraints (L)

Vellum radiocarbon-dated 1404 to 1438 (L: via Pelling 2016; Bowern & Lindemann 2021). Five hands sharing one writing system, scribes 1 to 3 writing 188 of 227 pages (L: Davis 2020); Currier language is nearly determined by hand (S: a6). Earliest documentary mention 1639, Baresch letter (L). Any hoax model must place the writing in the early 15th century or posit century-old vellum with period-consistent ink and codicology (L: Pelling 2016). A 200-plus page vellum codex by several collaborating scribes is a cost argument no statistic addresses (L). Ink, pigment and quire order were not examined.

## 7. What would settle the rest

1. Full-length generator bake-off (self-citation, grille, Naibbe-enciphered Latin, human gibberish) under one battery including the Montemurro-Zanette peak (~807 words), topic x illustration x scribe co-clustering, page-adjacency similarity, A/B separability and f/p rules (L: decisive tests). Scripts a1 to a6 are a partial battery runnable on any candidate.
2. Manuscript-length human gibberish written over weeks with illustrations and sections (L: Gaskell & Bowern 2022).
3. Illustration-text mutual information with hand, quire and adjacency partialled out.
4. Token-predictability discriminator on cipher, self-citation and gibberish outputs (L: Rozanova & Temerev 2026).
5. A key applied blind by a third party to 5 A and 5 B folios with a shuffled-glyph control (L: Fagin Davis criteria; Malta 2026 CFP).

## 8. Checked / not checked / user must verify

**Checked.** Every headline number in a1 to a6 reproduced by independent re-implementation (v_a1 to v_a6): Levenshtein, entropy formulas, estimator bias, corpus contents, boilerplate. Transliteration robustness across ZL, RF1b, IT2a, GC2a, CD2a. Corrections applied: single-book samples; Latin word entropy from prose; folded floor 3.32; rigidity ratio 1.7 to 2.3x; under-dispersion Currier-B only; line-final effect is the m/g allograph; a6 rule 99.5% leave-one-out; v101 inventory 68.

**Not checked.** Paywalled Cryptologia full texts. Timm's reference generator binary. Higher-order entropies, per-hand entropy, significance of A vs B differences, bootstrap intervals. No higher-level literature statistic (Montemurro-Zanette peak, topic models, ADJPAGESIM) was recomputed. Davis's hand assignments taken as given. The v_a4 verdict text was not among this writer's inputs; v_a4 numbers were read from `results/v_a4.md`. Physical evidence beyond radiocarbon, hands and the 1639 letter. The natural-language research pass and the tail of the cipher-pass source list were truncated in the inputs.

**User must verify.** Corpus choices (single Gutenberg books; OCR Italian with ~8% Latin; verse vs prose Latin), glyph merge lists, the 24-symbol verbose code designs, treating 2,461 uncertain-space commas as breaks, and the labels excluded / disfavoured / live before quoting. All output is unvalidated until user review.
