# v_a2: adversarial re-check of a2_wordstats.py

Script: targets/voynich/v_a2.py (22 s). Numbers: results/v_a2.json. a2 files not modified.

## What reproduces exactly (checked by independent re-implementation)
- Token/line counts: ALL 34,116 / 4,130 lines; A 10,715; B 22,862. Dropped: 98 words with '?', 96 with non a-z (73 '@nnn;' rare-glyph codes, 24 apostrophes, digits).
- Zipf slopes (own OLS, log10, ranks 1-1000 / 1-5000): ALL -1.0403 / -1.0554, A -0.9937 / -0.7929, B -1.0681 / -0.9245. Hapax 69.72% types / 14.79% tokens. top-1 daiin 2.248%.
- Word length: RAW 5.070/3.734/disp 0.917, MERGED 4.111/2.484/0.798; A and B identical to a2.
- Chi-square / Cramer's V (own pooling): first-symbol 6383.2 df 36 V 0.306; last 4090.8 df 32 V 0.245; A 0.2618/0.2276; B 0.3484/0.2617. p-values: a2.gammq(47.8, 44) = 0.32110, exact Poisson-sum 0.32110; gammq(28.1,38)=0.87985 vs exact 0.87985.
- Levenshtein: a2.lev1 agrees with a full DP on all 29,986 (ALL), 9,158 (A), 20,384 (B) adjacent pairs, 0 mismatches. Identical 0.907% / shuffled 0.361%; ED1 3.538% / 1.734% reproduced with the same seed.
- Normalisation is like-for-like: both sides lower-case letter runs, spaces = breaks; language samples are exactly the Voynich token counts; pseudo-lines use the real Voynich line-length sequence.
- Language-sample noise floor: E[chi2]=df gives V = sqrt(df/2N) = 0.025, which is what the five languages show; the control is a correct null.

## Corrections / caveats

1. Word-length under-dispersion is a Currier-B property, not a Voynichese property, and the language range is a mixture artefact.
   - Aeneid alone (17,059 tokens): mean 5.77, var 4.97, var/mean(L-1) = 1.043. Confessiones alone: 7.45 / 1.742. The a2 "Latin" 6.27 / 1.387 is the 50/50 verse+prose mixture.
   - Voynich A: RAW 1.116 (over-dispersed), MERGED 0.986, comma-joined MERGED 1.027. Indistinguishable from the Aeneid.
   - Voynich B: MERGED 0.710, RAW 0.824, comma-joined 0.719 -- genuinely narrower than any single text here. ALL 0.80/0.92 is dominated by B.
   - "RAW ALL hits the n=40 cap" is a cap artefact: with cap 300 the RAW ALL ML optimum is finite, n=52, p=0.078 (moment estimate 49.2). A MERGED: n=277 (no useful optimum, consistent with dispersion 0.99 ~ 1). Corrected statement: "variance 33-50% of any language's" should read "B variance 2.3-2.5 (MERGED) vs 5.0 (Aeneid) to 7.4; A is not under-dispersed".

2. START-word lengthening is mostly the paragraph-initial word. START 4.40 = PARA_FIRST (n=740, 5.27) + LINE_FIRST (n=3,362, 4.211). LINE_FIRST - MID = 0.15 (A 4.105-3.837 = 0.27; B 4.280-4.163 = 0.12), vs language noise within 0.1. The a2 sentence "the START-word lengthening ... cannot be explained that way" is not supported; the residual is marginal.

3. Last-symbol line-position effect is essentially the final m/g allographs. Excluding paragraph-first lines: V 0.246 (unchanged). Additionally dropping words ending in m or g: V 0.102 (ALL), 0.161 (A), 0.071 (B). Recoding m->iin (N) and g->d instead: V 0.144 / 0.195 / 0.110. These residuals are at or below the hexameter control (0.177). "Stronger than verse, unlike any prose" therefore reduces to "there is a line-final allograph", which is what a2 itself concedes (terminal allograph) but then still scores as N/C.

4. First-symbol effect does survive paragraph removal: V 0.277 (A 0.245, B 0.320). Line-first shares without paragraph lines: y 17.5%, s 12.1%, d 18.5% vs mid-line 3.4/2.2/7.3%; ch 4.1% vs 20.2%. This is the robust part of the positional block. Whether y-/s-/d- line-initial forms are allographs of ch-/sh- words is not testable with a2's controls.

5. Comma handling is undocumented. parse_ivtff.py converts every IVTFF ',' (uncertain space; 2,463 in P text) into a word break; a2's method note does not mention it. With commas JOINED: tokens 31,658; RAW mean 5.461 var 4.066 disp 0.911; MERGED 4.428 / 2.798 / 0.816; identical adjacent 0.883% (shuffled 0.269%), ED1 3.128% (shuffled 1.33%); Zipf r1-1000 -1.005; hapax types 72.9%; first V 0.316, last V 0.246. Conclusions unchanged; means shift +0.3-0.4, variances +9-13%.

6. Latin corpus artefact: the Gutenberg Confessiones carries 996 "[Sidenote: ...]" apparatus entries (3,768 words: scripture references and chapter summaries); "sidenote" (168) is the 10th most frequent token of the Latin sample. Minor effect on Zipf/hapax/word length but should be stripped. The 663 'æ' ligature tokens are genuine (0xE6), not decoding damage.

7. Italian corpus: top word 'et' is 16th-century orthography, not Latin admixture (0 of 68 500-word windows Latin-dominated); 1.6% roman-numeral-like OCR tokens, 4.8% one-letter words. Numbers unaffected within rounding (Italian-only windows: var 6.52, slope -1.029).

8. Top-1 share "below every language": A alone is 4.27% (inside 3.5-4.9); only B (2.13%) and the A+B mixture (2.25%) are below. A two-dialect mixture lowers top-1 share by construction.

9. Robust anomalies that survive all checks: adjacent identical pairs 0.88-0.93% (comma-joined, ZL, IT2a) vs <=0.16% in five languages, obs/shuffled 2.5 vs <=0.3; ED1 pairs 3.1-3.5% vs <=1.4%; line-initial first-symbol V 0.28 without paragraph lines vs null 0.025 and hexameter 0.148; paragraph-initial gallows 83%; Currier B word-length dispersion 0.71-0.82.

## Strongest objection to the interpretation
The two blocks that carry the "cipher-/procedure-like" verdict (word-length dispersion, line-position dependence) compare the manuscript with re-lined printed prose, which by construction has neither scribal position-dependent letterforms (line-end flourishes/abbreviations, paragraph initials) nor single-text homogeneity. Against a single Latin verse text the dispersion contrast disappears for Currier A (1.04 vs 0.99-1.12), and the last-symbol effect collapses to V 0.07-0.16 once the two final allographs are removed. The tests separate "manuscript with scribal conventions" from "typed prose", not language from non-language. What remains unlike all controls is the adjacent (near-)repetition, the line-initial first-symbol effect, and Currier B's narrow word-length distribution.

Checked: code paths for loading, merging, Zipf, word length, chi-square/V/p, Levenshtein, shuffling, pseudo-lines; all headline numbers; comma variant; corpus content of la/it; single-book Latin dispersion.
Not checked: the Aeneid real-verse control's positional numbers (accepted from a2), the IT2a rerun, Heaps beta values (formula read, not recomputed), German/English/Danish corpus content beyond the audit counts.
User must verify: whether ',' (uncertain space) should be a break or a join for the intended analysis; whether m/g and line-initial y/s/d should be treated as allographs before any language/cipher comparison.
