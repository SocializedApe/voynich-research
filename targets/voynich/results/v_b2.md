# v_b2: adversarial re-check of b2_longrange.py

Verifier script `v_b2.py` (pure Python, own code, nothing imported from b2 or a4; seeds 20261011 and k-means seeds 0-9; runtime 78 s). Numbers below are from `results/v_b2.json`, which also holds the claims table as `claims`. All output unvalidated until user review.

## Re-run of b2 as-is

- **First re-run** (the 38 re-downloaded Gutenberg files, and the Italian corpus at `../vatican5/corpus_it.txt`): every Voynich, Latin and English number was identical to the committed b2.json, k-means included. The fixed seed makes it deterministic; the seed sensitivity is between seeds, not between runs. Every Italian number moved. MZ went from 0.0560 (peak 800) to 0.0388 (peak 200), types at 34,116 tokens from 6,762 to 12,584, and the adjacency, MI and k-means Italian rows changed too. The cause was that `vatican5/corpus_it.txt` on this machine is a rebuild. `build_it_lm.py` concatenates `sorted(glob('nb_*.txt'))`, and this checkout has eleven extra `nb_bub_gb_*` volumes that sort first, whose OCR opens with "hitii hlf siifii r um fr roi iilii". The September sample ("cumque predictus fcrdiuandu ...", as in v_a4.md) starts at character 10,375,656 of the rebuilt file. Re-running b2 unmodified, with only the Italian tokens taken from that point, reproduced the committed b2.json in every number.
- **After the coordinator froze `data/corpora/corpus_it.txt`** (the file from that point on) and pointed `_IT` at it, a plain `python b2_longrange.py` reproduces the committed results exactly. The only diff is three corpus `source` paths and `runtime_seconds`. `results/b2.json` and `b2.md` in the working tree are that re-run.

## Claims table

"Re-run" means the plain re-run on the frozen Italian copy, which equals b2 in every row. On the rebuilt vatican5 file only the Italian entries differed (shown in the Italian row). The independent values come from the analytic MZ baseline, independent JSD/MI/k-means code and 10 k-means seeds.

| claim in b2.md | b2 value | re-run value | independent value | verdict |
|---|---|---|---|---|
| MZ: Voynich peak 400 tokens, 0.268 bits/token | 400 / 0.2677 | = b2 | 400 / 0.2668 (20-shuffle check 0.2665); finer grid peak 600 / 0.2701, 800 = 0.2620 | confirmed; the peak is a flat top from 400 to 800 (MZ 2013: 807) |
| MZ: Latin 0.107 (peak 200), English 0.110 (peak 200) | 0.1071; 0.1099 | = b2 | 0.1067 (200); English 0.1085 (400), 0.1069 (200) | confirmed (English is flat from 200 to 400) |
| MZ: Italian OCR 0.056 (peak 800) | 0.0560 | = b2 on the frozen copy; 0.0388 (peak 200) on the rebuilt vatican5 file | 0.0551 (800) | confirmed; see the re-run note |
| MZ: shuffled Voynichese 0.0013 | 0.0013 | = b2 | 0.0024 (a different shuffle) | confirmed (noise floor of about ±0.004) |
| MZ: Currier A 0.111 (200), "Latin-like"; B 0.195 (400) | 0.1106; 0.1953 | = b2 | 0.1104; 0.1950. Windows of the same length: Latin 0.054-0.130 (mean 0.089), English 0.051-0.102 (0.080) at A's length; Latin 0.077-0.172, English 0.091-0.106 at B's | confirmed. A is inside the Latin range and 1.2-1.4x the language means; B is above every window |
| MZ: top carriers shedy, qokain, qokeedy, qokedy, daiin, chedy "are the words MZ 2013 listed" | as stated | = b2 | same six, same order. MZ 2013 Table 1 (PMC3689824): shedy, qokeedy, daiin, qokaijn, chedy, qokedy | confirmed (five identical; qokain against qokaijn) |
| Adjacency, all pairs: ratio 0.81, 80% below the random median; Latin 0.88 / 73%, English 0.87 / 68%, Italian 0.93 / 58% | as stated | = b2 | 0.813 / 0.80; 0.884 / 0.73; 0.870 / 0.67; 0.928 / 0.58. The no-continuity baseline (defined in critique 4) is 0.838 for the Voynich and 0.954-0.965 for the pours | numbers confirmed; interpretation corrected: about 87% of the Voynich raw effect is page length plus stratum composition |
| Adjacency: shuffling within hand leaves 0.91 / 70%, so "hand runs explain roughly half" | 0.91 | = b2 | 0.913 (50 shuffles) | confirmed as stated (see critique 4 for what the rest is) |
| Adjacency, same hand + section: 0.83 / 78% (p 0.001), "the same size as a real book" (0.82, 0.81, 0.87) | as stated | = b2 | 0.833 / 0.78 against a baseline of 0.895 (residual 0.062); books 0.816 / 0.808 / 0.866 against 0.888 / 0.888 / 0.903 (residuals 0.071 / 0.080 / 0.037) | confirmed; the conclusion holds against the correct baseline, but the effect is 0.06, not 0.17 |
| Adjacency: "within a single quire no text shows an adjacency effect" (1.00, 0.97, 1.00) | as stated | = b2 | 1.000 / 0.968 / 0.990 / 1.028 against baselines 1.091 / 1.063 / 1.085 / 1.079 | **corrected**: every text shows within-quire continuity (residual 0.05-0.095; Voynich 0.091) |
| Adjacency across a hand change: Voynich 1.03 (n 30), English 0.94, Latin and Italian 0.99, "weak" | as stated | = b2 | 1.035 against a baseline of 1.038 (residual 0.003); books 0.991 / 0.951 / 0.994 against 1.064 / 1.068 / 1.055 (residuals 0.07 / 0.12 / 0.06) | **corrected**: all three books show continuity across the (arbitrary) hand cuts; the Voynich shows none |
| MI marginal 0.369, of which 0.201 is reproduced by the within-hand null | 0.3694 / 0.2011 | = b2 | 0.3694 / 0.2020 (z 13.9) | confirmed |
| MI given hand 0.171 against a null of 0.083: excess 0.088, z 14.5 | 0.1709 / 0.0828 / 0.0881 | = b2 | 0.1709 / 0.0831 / 0.0878, z 15.3 (500 permutations) | confirmed |
| "5 to 6 times the excess of a real book cut into contiguous sections (Latin 0.017, English 0.025, Italian 0.015, all z = 4 to 5)" | as stated | = b2 | 0.0169 (z 4.1), 0.0255 (z 7.6), 0.0146 (z 4.5): 3.4 to 6.0 times. Compilation of different works: 0.0671 (English), 0.0576 (German): 1.3 to 1.5 times | **corrected** (b2's own table has English at z 6.8; the ratio range is wrong; the positive control is weak) |
| Rotation null within hand 0.107; "about 72% of the within-hand excess is tied to where the drawings change" | 0.1073 / 72% | = b2 | 0.1077 / 72%. Compilation of different works: 72% and 81% | number confirmed; interpretation **corrected** (drawing change = gathering change; see critique 3) |
| Per hand: hand 1 0.126 (z 20.8), hand 2 0.146 (z 13.2), hand 3 0.000 | as stated | = b2 | 0.1259 (z 18.2), 0.1452 (z 12.2), 0.0004 (z 0.0) | confirmed (hand 3's zero is real, not a bug) |
| "Conditioning on quire leaves almost nothing for any text, because quires are section-pure" | Voynich hand x quire 0.0027, z 0.8 | = b2 | 0.0028, z 0.85 (p 0.22). Seven hand x quire strata mix sections. Contiguous pours 0.003-0.008 (z 1.4-3.2); Voynich labels on the pours 0.001-0.002; compilation 0.010 / 0.013 (z 3.5 / 3.3). Quire O alone (hand 1, 6 H against 6 P): Voynich z 0.36, compilation z 4.0 / 4.0 | **corrected**: quires are not all section-pure; where they mix, the Voynich section label carries nothing, while a text that changes with the drawing would be detected |
| "The drawings predict the frequent words within a scribe ... Positive evidence of section-conditioned production" | - | - | Hand 1's ten herbal pages in the pharma quires read like the pharma pages: log-likelihood ratio +0.17 bits/token, 8 of 10 pharma-like. Herbal pages in the herbal quires: -0.72 (4 of 85); pharma pages: +0.53 (16 of 16) | **corrected**: the signal follows the gathering, not the drawing |
| k-means, all pages: section ARI 0.13, hand 0.21, language 0.27; "language first, hand second, section last" | 0.134 / 0.206 / 0.267 | = b2 | medians over 10 seeds 0.187 (0.092-0.311) / 0.283 (0.195-0.421) / 0.275 (0.243-0.358); homogeneity 0.51 / 0.57 / 0.70 | confirmed within the seed range; the ordering holds by homogeneity, not by ARI (hand roughly equals language) |
| Within hand 2 ARI 0.61; hand 1 0.33; hand 3 -0.03 | as stated | = b2 | 0.531 (0.295-0.641); 0.274 (0.210-0.432); 0.000 (-0.029-0.407) | confirmed within the seed range. b2's "Currier A" run is the same 111 pages as its hand 1 run and gave 0.18 against 0.33 |
| Pours with contiguous sections ARI about 0, "so the Voynich section structure ... is far sharper than topic structure in real prose at this page size" | -0.04 / -0.00 / -0.06 | = b2 | -0.012 / -0.010 / -0.048. Compilation of different works: 0.142 (English), 0.171 (German); within hand 2: 0.42, 0.35 | numbers confirmed; comparison **corrected** |
| Overall: "every literature-level 'language-like' long-range statistic is present with hand and quire partialled out" | - | - | Section MI with hand and quire partialled out is 0.003 bits, z 0.8 (above) | **corrected** |

## Method critique

**1. Montemurro-Zanette estimator.** b2 computes the MZ 2010/2013 decomposition: ΔI(s) = Σ_w p(w) [⟨H_w(s)⟩_shuffled − H_w(s)], with the entropy taken over P = floor(N/s) equal blocks and p(w) = n/N.
- **Shuffle baseline.** MZ compute the shuffled term analytically (hypergeometric block occupancy); b2 averages 20 shuffles. An average over random permutations is an unbiased estimate of that expectation.
- **Tail.** b2 shuffles the whole text and then drops the tail (up to 2,116 tokens at s = 3,200 and 6,400), while the real text loses its own tail. The two quantities differ slightly.
- **Size of both effects.** Analytic and 20-shuffle values on the truncated text agree within 0.0005 at every scale. b2's shuffle-then-truncate variant differs by at most 0.0015 (Voynich, all eight scales; Latin and English at 200, 400, 3,200 and 6,400). Neither changes any conclusion.
- **Calibration against MZ 2013.** The thirteen books of the same Gutenberg Confessions (82,696 tokens, cut before the Annales, notes and index) give 0.175 bits/token, peaking at 400. MZ 2013 report about 0.2 for Latin (the Confessions). MZ 2013 found the Voynich only "slightly above English". At equal length b2 finds 2.4 to 2.5 times; the full Pride and Prejudice (122,855 tokens) gives only 0.129. The difference comes from the control text (MZ used Darwin) and its length. The measure grows with length: Latin windows go from 0.089 at 10.7k tokens to 0.107 at 34k and 0.175 at 83k.
- **Coverage.** Coverage does not explain the excess. The frequency ≥ 20 words cover 59% of Voynich tokens, 49% of Latin and 71% of English.
- **What the magnitude measures.** It measures heterogeneity, not language-likeness. A 34,116-token window of the same Latin file that crosses from book XIII into the Annales and notes gives 0.310 (peak 800), above the Voynich. The English compilation control gives 0.163 and the German 0.119.

**2. Section labels.** b2 reads the right variable. `illus` is IVTFF page variable `$I`, the illustration type, parsed per page header in `parse_ivtff.py`.
- **Label consistency.** No page changes label inside it (0 inconsistent P lines). Foldout panels are separate loci with their own headers (f67r1, f85r2, fRos, f86v3-6, f89r1/2 ...), which handles mixed foldouts sensibly.
- **"Folios" are pages.** b2's 207 "folios" are IVTFF pages, about 165 tokens each, so "two to three folios" should read "two to three pages".
- **Layout labels.** T (text only) is not a drawing type. The T/C split on the rosettes foldout (f85r1, f86v5, f86v6 against f85r2, f86v3, f86v4) and f76r (T in the biological quire) are layout labels. The drawing claims therefore rest on herbal against pharma (hand 1) and herbal against biological (hand 2).
- **Other labels.** Zodiac pages have no P text and drop out. f58r/v are labelled S although they sit in quire H. One S page (f115r) has hand '?'.

**3. Is the conditional-MI null conditional on hand?** Yes. For `given_hand` the labels are permuted within hand, the MI is computed within each hand and pooled with token weights, and the independent code reproduces the observed value to four decimals. It is not conditional on the gathering, though, and for the Voynich drawing type and gathering are almost fully confounded.
- **Hand 2.** Hand 2's herbal pages are all in herbal quires D-G and its biological pages all in quire M.
- **Hand 1.** Hand 1's pharma pages are in quires O and S, after a gap of about 30 leaves filled by other scribes.
- **What the rotation null can and cannot test.** The rotation null keeps the run structure but cannot move a boundary away from a production break. Its "72% tied to where the drawings change" is the same share the compilation control gives, where every boundary is a change of work.
- **The crossed test.** Hand 1 is the one place where drawing and gathering can be crossed: ten herbal pages drawn inside the pharma quires O and Q (f87r/v, f90r1, f90r2, f90v1, f90v2, f93r/v, f96r/v). The test uses an add-0.5 unigram log-likelihood ratio, leave-one-out for the model pages. Those ten pages sit 71% of the way from the herbal-quire herbal pages (-0.72) to the pharma pages (+0.53).
- **MI on the same splits.** Herbal drawings split by gathering give an excess of 0.050 (z 11.4, 85 against 10 pages). Drawings split inside the pharma quires give 0.029 (z 2.7). Even that second split still mixes quires, because Q holds only herbal pages and S only pharma pages.
- **Inside a single quire.** In quire O alone (six herbal, six pharma pages, 700 tokens) the drawing type carries nothing: excess 0.007, z 0.36. With the same pages, labels and sizes, a text that changes with the drawing (compilation control) gives z 4.0 in both languages, so the test had power for a change of that size.
- **The other mixed strata.** Each pits a single text-only page or a handful of pages against the rest: 1/A f1r (z 2.5, p 0.06), 2/M f76r (z 2.1, p 0.055), 2/N rosettes T against C (z -0.9), 4/I astronomical against cosmological (z 0.9).

**4. Adjacency baseline.** b2 compares adjacent pairs with all non-adjacent pairs in a stratum. That builds in two artefacts present in every text.
- **The artefacts.** Plug-in JSD depends nonlinearly on page length, and adjacent pages have similar lengths. Pooling strata also weights each stratum by n for adjacent pairs and by n² for random pairs.
- **Size of the artefacts.** With tokens shuffled globally (only page lengths left) the same-hand-and-section ratio is already 0.89-0.91 for every text, and the within-quire ratio 1.07-1.08. With tokens shuffled within hand x section (no page continuity at all, lengths and composition kept) the Voynich all-pairs ratio is 0.838.
- **Corrected comparison.** Against these baselines (3 replicates; spread mostly ≤ 0.01, at most 0.04) the Voynich residuals are 0.025 for all pages, 0.062 within hand + section, 0.091 within quire and 0.003 across hands. The pours give 0.04-0.09, 0.04-0.08, 0.05-0.10 and 0.06-0.12.
- **p-values.** b2's p_boot = 0.001 is against the unmatched pairs, so it measures mostly the artefact.

**5. Positive controls.** Contiguous cuts of one novel are a lower bound: topic drift inside one work, with arbitrary cut points. They are not a model of an illustrated compendium, where each section would be a different text even in one scribe's hand.
- **The compilation control.** v_b2 adds one: every Voynich section is filled from a different work, with the Voynich page lengths, hands, quires and labels kept. English: herbal from Pride and Prejudice, biological from Moby-Dick, the rest from Crime and Punishment. German: Taugenichts, Dr. Mabuse, Venus im Pelz, Die Liebe.
- **Result.** It gives a within-hand MI excess of 0.067 / 0.058, k-means ARI 0.14 / 0.17 and an MZ peak of 0.163 / 0.119.
- **Where the Voynich falls.** Its within-hand section signal (0.088) is 1.3-1.5 times this control, its section clustering about the same, and its MZ above it.
- **Limit of the control.** Works by different authors overstate what one author's herbal-and-recipe book would show. A single-author multi-topic compendium was not available.

**6. k-means.**
- **Seed sensitivity.** It is larger than b2 says ("a few hundredths"). Over 10 seeds of 10 restarts, section ARI on all pages ranges 0.09-0.31 and hand 3 ranges -0.03 to 0.41. b2's "hand 1" and "Currier A" runs cluster the identical 111 pages with k = 2 and get 0.33 and 0.18.
- **Comparing label sets.** ARI against labels with 3, 6 and 7 classes is not comparable. Homogeneity (the share of each label's entropy explained by the clusters) is the fairer ranking: language 0.70, hand 0.57, section 0.51.
- **Vocabulary.** The clustering vocabulary skips the 20 commonest words (ranks 21-520), so "sits in the commonest words" comes from the MI analysis, not from the clustering.

**7. Minor.**
- b2.md describes the Italian control as "first 34116 tokens" of `vatican5/corpus_it.txt`. That file is rebuilt from a glob and has changed; the frozen `data/corpora/corpus_it.txt` now pins it.
- My English loader gives 3,558 types at 34,116 tokens against b2's 3,556, which is negligible.

## Corrected wording for b2.md section 5

**1. Montemurro-Zanette.** Voynichese carries 0.267-0.268 bits/token of long-range word-placement information, with a flat maximum between 400 and 800 tokens (600 on a finer grid; MZ 2013: 807 words, about two to five pages). At equal length the controls give 0.107 (Latin), 0.109-0.110 (English) and 0.055 (Italian OCR); shuffled Voynichese gives 0.002. The estimator is MZ's and its scale is right: the full Confessions give 0.175, against MZ 2013's ≈ 0.2. The top carriers (shedy, qokain, qokeedy, qokedy, daiin, chedy) are five of MZ 2013's top six.

The magnitude measures heterogeneity, not language-likeness.*
- A window of the same Latin book that runs from the end of book XIII into the Annales and notes gives 0.310 at the Voynich length, above the Voynich.
- Different novels poured into the Voynich sections give 0.12-0.16.
- Currier A alone (0.110) lies inside the range of Latin windows of its length (0.054-0.130). B alone (0.195) is above every language window of its length.

Keep (ii) and the implication as written. It does not discriminate.*

**2. Adjacent pages.** Adjacent Voynich pages are more alike than random pairs (ratio 0.81; 80% below the random median). A model with no page-to-page continuity, with tokens shuffled within each hand x section stratum and page lengths kept, already gives 0.84: most of the raw effect is stratum composition plus page length. That artefact is present in every text.

Against that baseline:
- **Whole book.** The Voynich's page-to-page continuity is smaller (0.025) than in the Latin and English pours (0.070, 0.088; Italian 0.037).
- **Within one hand and one section.** The residual is 0.06 (0.833 against 0.895), inside the books' range (0.04-0.08).
- **Within a quire.** Every text, the Voynich included, shows continuity.
- **Across a change of scribe.** The Voynich shows none (1.035 against 1.038, n = 30), while the books, whose "hand" boundaries are arbitrary cuts, all do.

Implication.* Adjacent pages by one scribe in one section resemble each other about as much as adjacent pages of a real book, and the continuity breaks at every change of scribe. That is topic continuity or generator drift inside a scribe's run, and does not discriminate. "Each page is an independent draw from its section" is still rejected, by a margin of 0.06 in the ratio.

**3. Illustration-to-text MI.** Marginal MI(section; word) is 0.369 bits/token, of which 0.202 is reproduced by a null that keeps each label's hand. Conditional on hand the excess is 0.088 bits (z ≈ 15). That is 3.4 to 6 times the excess from contiguous cuts of one book (0.015-0.026), but only 1.3 to 1.5 times that of a compilation that fills each section from a different work (0.058-0.067), which is the relevant control for an illustrated compendium. As in the compilation, about three quarters of the excess is tied to the real section boundaries rather than to any contiguous partition. The excess is carried by hand 1 (0.126) and hand 2 (0.145); hand 3 shows none.

The signal follows the gathering, not the drawing.
- **Hand 1.** Its herbal pages bound inside the pharma quires (f87, f90, f93, f96) read like the pharma pages around them: 8 of 10 are closer to the pharma model, on average 71% of the way from herbal to pharma.
- **Quire O.** The same scribe drew six herbal and six pharma pages there, and the drawing type carries no detectable information (z 0.4). With the same pages and labels, a text that changes with the drawing gives z 4.0.
- **All mixed strata pooled.** The section label adds 0.003 bits (z 0.8), like arbitrary labels on a real book.
- **Hand 2.** Drawing and gathering coincide throughout, so they cannot be separated.

Implication.* Within a scribe, the frequent words (the same sub-word families as in a6) change between gatherings, and the illustrated sections are made of different gatherings. There is no evidence that a page's drawing conditions its text once the gathering is fixed. This is evidence of gathering-level (production-campaign) variation. Either a text compiled or copied gathering by gathering, or a generator re-parameterised per batch, would produce it. It is not evidence of section-conditioned production, and not of meaning.

**4. Clustering.** Over 10 seeds, k = 7 clusters agree with the section at ARI 0.19 (0.09-0.31), the hand at 0.28 and the Currier language at 0.28. Homogeneity orders them language (0.70) > hand (0.57) > section (0.51). Within hand 2 the sections are recovered at ARI 0.53 (0.30-0.64), within hand 1 at 0.27 (0.21-0.43), and within hand 3 at 0.00 (unstable, up to 0.41). Contiguous cuts of one book give ARI about 0. A compilation of different works gives 0.14-0.17, and 0.35-0.42 within hand 2.

Implication.* The page-level section structure is far sharper than drift inside one book and about as sharp as the change between different works. The lexical structure is language/scribe first, section second.

**Overall.*** None of the four statistics separates meaningful text from generated text. If the text is generated, they narrow the generator class to one whose output:
- drifts page to page within a scribe's run;
- breaks at changes of scribe;
- changes between gatherings.

They show no re-parameterisation at an illustration boundary inside a gathering (one case with power: quire O). With hand and quire partialled out, page adjacency survives (as in the books), and section information does not (0.003 bits, z 0.8).

## Checked / not checked

Checked:
- b2 re-run as-is: identical to the committed results with the frozen Italian copy; the Italian drift explained and reproduced.
- The MZ estimator against an analytic (hypergeometric) baseline, a 20-shuffle baseline and b2's shuffle-then-truncate variant.
- MZ magnitude against MZ 2013's Latin value (same work); top carriers against MZ 2013 Table 1 (PMC text).
- Length-matched language windows for A and B; coverage of the frequent words.
- The section variable (`$I`) and per-page label consistency.
- Adjacency, MI and k-means re-implemented; the MI null's conditioning.
- Seed range of k-means.
- Adjacency baselines (global and within-stratum token shuffles) for all four texts.
- The compilation positive control (English, German).
- The drawing-against-gathering crossed test on hand 1; per hand x quire MI strata.

Not checked:
- Other transliterations (Takahashi, GC). Davis's hand assignments and the quire/binding order (original page order unknown; possible misbinding).
- A single-author multi-topic compendium as the positive control (none in data/corpora).
- Sensitivity to the top-300, frequency ≥ 20 and ranks 21-520 cut-offs.
- Smoothing choices in the log-likelihood placement.
- MZ 2013's equations themselves (rendered as images on the journal and PMC pages).
- Per-word significance of the MZ carriers.

All interpretive sentences marked * are judgement. All output unvalidated until user review.
