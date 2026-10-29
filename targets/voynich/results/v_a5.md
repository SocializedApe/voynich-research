# v_a5: adversarial re-check of a5 (script v_a5.py, runtime ~10 s; full numbers in v_a5.json)

Verdict: HOLDS WITH CORRECTIONS. All headline numbers of a5 reproduce exactly (h1/h2 raw and merged, BPE step 12,
null removals, CV information budget 425,468 bits). The low-h2 / high-positional-MI result is NOT an EVA artefact:
Currier CD2a (1 char per glyph, 35 symbols, 15,823 P tokens) h2 = 2.660 nospace [2.351 space], MI 0.706;
v101 GC2a (68 symbols, 36,211 tokens) h2 = 2.887 [2.524], MI 0.725. Language floor with diacritics folded to
ASCII (like-with-like alphabets): German 3.380, Italian 3.442, French 3.443, Danish 3.513, Latin 3.516, English 3.615.

Corrections
1. Transposition: the h1 argument ("Voynich h1 3.87 below all languages") is segmentation-dependent and wrong for
   merged EVA (3.966 > Italian 3.939) and v101 (4.143). Drop it. The h2 argument alone suffices: for Latin/Italian/German
   H(X_n|X_n-k) rises monotonically with k (Latin 3.535, 3.885, 3.997, 4.022 for k=1..4), so any transposition gives
   h2 >= 3.44, never 2.3-2.9.
2. Positional lock in raw EVA: of the 6 locked symbols, h and i (and c never-final, h never-initial) are halves of the
   EVA composites ch/sh and in/iin. Cite the merged (9 of 29), Currier (7 of 28) and v101 (12 of 58) counts instead,
   i.e. 21-31 % locked. Languages with folded alphabets: 0-2 of 24-26 locked (0-8 %), MI 0.166-0.272 (French drops from
   6 locked / 0.301 to 0 / 0.272). MI ratio Voynich/language = 2.5-4.3x.
3. Word inventory: language samples mix 2-5 books, which inflates types (French 6,291 mixed vs 5,173 single book;
   Latin 11,640 vs 9,357). Single-book hapax rates 57.0-68.7 %; Voynich 69.7 % is above every one, and 72.9 %
   (8,155 types on 31,658 tokens) if the 2,461 uncertain-space commas are joined instead of split (a5 split them).
   Types remain inside the single-book range (5,173-9,357).
4. Latin information-budget row is inflated by Aeneid verse + Confessiones mixing (unk 26.8 %): Confessiones alone
   (sidenotes removed) gives 15.27 bits/word (a5: 16.95), lzma 584,800 bits (a5: 631,072); capacity_vs_la becomes
   0.817 (bigram) / 0.809 (lzma) instead of 0.736 / 0.749.
5. Minor: [Sidenote:] apparatus = 276 tokens (0.8 %) of the Latin sample, effect on h2 -0.002; Danish alphabet contains a
   superscript-6 footnote marker; French 41 symbols are mostly rare accented letters; raw-EVA "remove h" (+0.159) is a
   ch->c merge, not a null test; h1-h2 gap ratio is 1.8-3.1x, not "2-3x".

Strongest objection: the verbose-cipher verdict is a test of greedy pair-merging, not of the cipher class. A5's own
extended run shows the Voynich h1-h2 gap converging on Italian's by 40 merges (1.01 vs 0.99) and it explicitly leaves
"2-3 units from ~50-60 unit types per word" open; a verbose or positional (slot-template) cipher, a nomenclator code, and
a generated meaningless text all produce the profile measured here, so the tests exclude only sequence-preserving
ciphers (1:1 substitution, transposition, plain abjad, single-glyph nulls), which the report's headline verdicts do state
but the "consistent with WORDS" wording in (5) over-reads.

Checked: sample construction, entropy formulas (base 2, plug-in, proper conditional marginal), BPE, nulls, CV model,
corpus contents (titles, boilerplate stripping, language mixing, OCR noise), EVA-independent transliterations,
diacritic folding, single-book samples, uncertain-space handling. Not checked: the syllabifier's output quality
(only used for order-of-magnitude syllable inventories), abjad numbers beyond reading the code (code is correct), the
truncated interpretation text of finding (6). User must verify: the phrasing corrections above before quoting a5.
