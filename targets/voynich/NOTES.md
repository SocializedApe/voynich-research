# Voynich manuscript (Beinecke MS 408): one-session adjudication, 2026-09-15

Not a decipherment. The question set was: hoax or meaningless text, cipher, or language, and how far the
evidence can be pushed in one session. Method: five literature sweeps (one per hypothesis or evidence
class), six fresh computational tests on the public transliterations against natural-language corpora and
against implemented hoax generators, an adversarial re-run of every test by a separate agent, and this
write-up. Every number below is either **(S)** computed this session by a named script in this directory
(a1 to a6, re-run and where necessary corrected by v_a1 to v_a6; corrected figures are the ones quoted) or
**(L)** quoted from the literature as returned by the sweeps and recorded in `SOURCES.md`. Judgement is
marked with an asterisk. Two independent baseline scripts (`baseline.py`, `baseline2.py`) written before
the agents ran reproduce the a1/a2 headline numbers (h2 2.32 raw EVA without spaces, Zipf slope -1.04,
adjacent repeats 0.81%).

## 0a. 28 October 2026 session: glyphs, meaning tests, codebook (in progress)

Overview and hypothesis table: `HYPOTHESES_2026-10-28.md`. Details: `glyphs/README.md` (transcriber disagreement,
twin glyphs, allographs, word spaces, f66r column vs f57v ring), `meaning/README.md` (word-swap page-context test,
code vs copy, synthetic codebooks on the b3 battery), `research/voynich_siblings/attack/README.md` (symbol inventory,
role-merged solver validation: failed), `tfm/` (small neural models: first run discarded as undertrained). Headline:
a one-to-one code of ordinary Latin/Italian is disfavoured on the b3 sequence items; with a copying scribe, the code
ties the letter cipher plus scribe. Leaf locality matches a real topical text (Pliny: 1.78 vs Voynich 1.81 as a ratio
to random pages); what nothing reproduces is the change of glyph statistics between parts of the book (A/B, about ten
times a topical text's), i.e. a change of writing convention by scribe. Redrawn plants share no words with their herbal
page, herbal pages share no opening formula, zodiac labels show no positional names; misbinding explains none of it.
29 Oct: a calibrated verbose-cipher sweep (verbose/README.md; gates broken blind, all Voynich groups, Latin, Italian,
German, Catalan, abbreviated Latin, fixed and positional units) finds nothing, as do Zhang & Sheng (arXiv 2610.34499)
over 16 languages. Leading judgement (HYPOTHESES section 2): meaningless text made page by page by several makers from
one shared word template.

## 0. October 2026 update (11 Oct): b1-b4 folded in, c1-c3 added, site page rewritten

Prompted by RBA's post "Not deciphering the Voynich manuscript" (goflaw.substack.com, 22 Sept 2026) and
Ilya A.'s note on it (constructed languages, Markov generators as charts, Lindemann & Bowern's alphabet-size
figure). Sections 1-8 below are the September adjudication; where October changed a statement, this section
says so and the site page (docs/voynich.html) carries the corrected text.

**Reproduction.** The September corpora lived in a scratchpad on another machine. `fetch_corpora.py` now
re-downloads them (the 38 Gutenberg ids named in the old results; voynich.nu transliterations with browser
headers; ZL is still version 3b of 13/05/2025 and parses to the committed TSV line for line). The Italian
control (git-ignored `vatican5/corpus_it.txt`) had been rebuilt with its documents in another order; the
September sample begins at character 10,375,656 ("cumque predictus fcrdiuandu s rex ..."), so the script
freezes a copy from there into `data/corpora/corpus_it.txt` and every script's `_IT` points to it. With that,
b1, b2, b3 and b4 reproduce every committed value (b3/b4 differ only in float rounding and runtime). All
scripts had hard-coded paths to the other machine; a header now defines `_HERE/_CORP/_EXT/_IT` locally.

**Verification of b1-b4** (separate agents, `v_b1.py`-`v_b3.py`, reports in `results/v_b*.md`; `v_b4.py` run
for the first time, `results/v_b4.json`):
- b1 confirmed. Correction: the CV-syllable rows match Voynich h2 by token shape (a random C/V/CV generator
  gives 2.10-2.16), not by language; Aeneid syllable pair-violation 0.192 is a tail artefact (0.255 on
  lengths 1-5). Section 2's gap (syllabic writing, uncertain spaces) counts as tested: neither reproduces
  Voynichese for Latin or Italian. Glyph groups spelling syllables inside word tokens stays in (a).
- **Parse defect (all scripts).** `parse_ivtff.py` deletes the 740 `<->` marks between glyphs (drawing
  interruptions; they behave like word spaces), gluing 655 false compounds, and drops 394 `{..}` ligature
  groups with their glyphs. Fixed: h2 unchanged (merged 2.635 -> 2.646), pair violation 0.160 -> 0.145, merged
  length variance 2.48 -> 2.12, hapax 69.5 -> 67.7% (inside the single-book language range: drop "hapax above
  every language"). Not yet propagated; next step is a full re-run on a corrected parser.
- b2 confirmed numerically; three readings overturned. Picture-text MI excess 0.088 is only 1.3-1.5x a
  compilation of different works (the fair control), and it follows the gathering, not the drawing (quire O:
  z 0.4; hand+gathering fixed: 0.003 bit). Adjacency: a no-continuity model already gives 0.84 of the 0.81
  ratio; Voynich continuity is smaller than the books' across the volume, within their range inside hand+
  section, present within quires for every text, and breaks at each change of scribe. MZ height measures
  heterogeneity (a Latin window running into the editor's notes gives 0.31).
- b3 confirmed (20 items re-implemented, within 0.2%; Naibbe port faithful, shipped file = naibbe.py v1,
  52-card deck). Corrections: not pre-registered (battery and results in one commit); autocopist and Naibbe
  FAIL Zipf; autocopist glyph-entropy excess 0.4-0.6 bit, and it overshoots the MZ peak (0.47) rather than
  lacking it; Naibbe divcom short 16 not 17; tolerance tighter than sampling noise on 6 items (candidates
  still miss by 7-18 SE); JSD halves and MZ height reward the A+B mixture. Naibbe's missing long-range
  structure is the cipher's (plaintext 0.10 -> letter units 0.02 -> ciphertext 0.004). A Pliny-then-Dante
  Naibbe hybrid still drifts 0.003 against 0.063.
- b4 re-run identical; v_b4 agrees (h2 2.311, h3 2.068, folio bootstrap 2.27-2.33, A/B p 0.002 at 500 perms,
  cross-word glyph MI excess 0.169).

**d1 (parse fix re-run, 28 Oct 2026; `parse_ivtff.py --fixed`, `d1_parsefix.py`, results/d1_parsefix.md).** ZL 3b
re-downloaded with plain curl (SHA-256 bf5b6d4a..., the published version 3b). `--fixed` turns `<->` into a word
break and keeps `{..}` ligature glyphs; without the flag the parse is byte-identical to the committed TSV. On the
Voynich side (no comparison corpus needed, September functions from a2/a3): tokens 34,116 -> 34,834, types 7,236 ->
7,021; pair-order violation 0.160 -> 0.145; merged length variance 2.48 -> 2.12; hapax 69.7 -> 68.0%; h2 raw 2.270 ->
2.280, merged 2.592 -> 2.606; Zipf -1.040 -> -1.041; adjacent identical 0.907 -> 0.935%. Every predicted correction
above is reproduced. **New: the change is concentrated in Currier A**, whose pages (mostly herbal, lines broken by
the plants) carry most `<->` marks: A raw length variance 4.44 -> 3.19, merged 2.89 -> 2.06, dispersion
var/(mean-1) 0.99 -> 0.74 (B 0.66; languages 1.67-2.02); A pair violation 0.201 -> 0.170. So section 4.3's
"under-dispersion is a Currier-B property; Currier A matches single-text Latin verse" does not survive the fix: both
languages are under-dispersed. Full re-run done the same day (results/fixed_parse/README.md):
the September copy reproduces every committed Voynich number within 0.1% (the Italian control rebuilt exactly from the
eight archive.org Nuntiaturberichte volumes); on the fixed parse no conclusion flips. b3: Naibbe 17 -> 21-23 of 37,
autocopist 9 -> 12-15, Rugg 8/14 -> 12/17 (Naibbe still closest, by more); a6 A/B recovery 99.5% -> 100%; b2 long-range
peak 0.268 -> 0.273. The items no generator reproduces narrow to the copying signatures, the MZ peak height, the drift
between halves and single-glyph words.

**c1 (comparators, `c1_comparators.py`, results/c1.md).** h2 under both conventions, every text cut to 34,116
tokens. Lindemann & Bowern count the space: ZL with space 2.117 raw / 2.509 merged against their 2.114 /
2.475, so the two conventions agree and must not be mixed. Their Appendix B is in `data/lb2021_wikipedia_h2.tsv`
(311 rows; lowest Hawaiian 2.765). With the space: Voynich EVA 2.12-2.14, Currier 2.35, merged 2.51, v101 2.53;
Toki Pona 2.334 (15 letters); Hawaiian Bible 1868 spelling 2.589; Setswana 2.652, Maori 2.656, Tongan 2.705;
Lojban 2.977, Swahili 2.980, Volapuk 3.091, Esperanto 3.108; 11 European languages 3.164-3.489. Without the
space Hawaiian 1868 (2.850) is below merged ZL (2.870) and v101 (2.897). So the absolute h2 is reachable by a
small alphabet with rigid syllables; at equal alphabet size (within 20%) the gap is still 0.33-0.54 bit, and on
h2/h1 (no space) every Voynich transliteration (0.60-0.71) is below every natural language (>= 0.75; Toki Pona
0.751). The CV languages fail word length (3.1-3.8), vocabulary growth (TTR 0.04-0.09 vs 0.21), hapax and
predictability (7-9x). b3 battery: Markov chains trained on Voynich 17/22/25 of 37 (fits, not hypotheses;
order 3 fails only the above-word items), Swahili and Esperanto 13, Vulgate 12, low-h2 languages 8-9, Toki Pona
8, Lojban 9, Latin-trained chains 7-9, random glyphs 6. Positional lock does not exclude Polynesian (Hawaiian
0.655 vs 0.644): correct b3's "natural language excluded by positional lock" to European languages. Zipf at
10,053 tokens: Voynich -0.99, random glyphs -0.87, Latin-trained order-1 chain -0.92; pooled human gibberish
-0.63 with 85% hapax, so the page's old "Zipf and hapax are reproduced by human gibberish" was wrong for the
pooled sample (corrected on the page).

**c3 (real period ciphers, `c3_period.py`, data/period/ built by its `_extract.py` from this project's own
targets).** 17 datasets, 18,604 signs, 1400-1490 (Mantua R1854 1428-30, Siena Concistoro 2308, Sforza BnF it.
1583 1446, Buda 1490, ...). h2 without spaces against 300 random same-length windows. Every transcribed
ciphertext of >= 250 signs sits 0.85-2.2 bits above Voynichese and -0.3 to +0.9 bit from Latin of the same
length; homophonic letters sit 0.24-0.62 bit above their own plaintext. benedict1399 is re-enciphered from
Puig's printed text (excluded from the chart). Homophonic/nomenclator chancery ciphers of a European language:
excluded.

**Corrections to sections below.** 4.2: hapax "above every language" falls with the parse fix. 5 (Live b):
"no implementation has been run at manuscript length" is out of date: the autocopist matches 9/37. 5 (Live c):
tested for Latin/Italian, now disfavoured. 7 items 1 (battery), 3 (illustration MI) and 4 (re-tokenisation)
are done (b3, b2, b1). 8 "Not checked" higher-order entropies, bootstrap, MZ, topic models, adjacency: done
(b4, b2). The two figures in two forms: merged h2 2.870 (a1 merge2 list) vs 2.646 (a4 list), both no space;
adjacency 0.907% within lines vs 0.82% across line breaks.

**RBA's post, compared.** Same transliteration and same character result (h2 2.07 vs 2.12 with space; Latin
3.36). Its Markov-chain h2 match is circular (a chain trained on Voynich reproduces h2 by construction). Its
"Zipf exponent 1.854, first report" looks like the frequency-distribution exponent, not the rank slope
(-1.04 here, Landini 2001). Its GRU masking effect (0.0055 nats, Latin ~0, Timm generator 0.007) is the
self-citation signal; our a4 shows most of it survives a within-page shuffle (0.238 of 0.269) and the
order-dependent part is Danish-verse sized (+0.031 vs +0.024). Its controls lack a within-page shuffle,
verse and a formulaic genre; that test is listed as open on the page.

**Still open.** Full re-run on a corrected parser (Voynich side done in d1; corpus comparisons pending); hybrid generator built to pass the battery; manuscript-length
human gibberish; RBA's masking test with the missing controls; f/p rules and line effects as alphabet-neutral
battery items; blind key test for any claimed key.

## 1. Verdict and confidence

**Established, and not disputed by anyone serious (L).** The object is a genuine early-15th-century codex:
vellum radiocarbon-dated 1404-1438 on four folios, iron-gall ink and period pigments throughout text and
drawings, five scribal hands sharing one writing system, provenance continuous from Prague c.1600 through
Baresch (1639), Marci (1665) and Kircher to 1912. The modern-forgery idea is dead.

**Excluded with high confidence*, robust to the transliteration (S).** That the text is a plaintext, a
one-to-one substitution, a letter transposition, a vowel-less (abjad) rendering, or a single-glyph-null
padding of any of eleven European languages tested (Latin, Italian, German, English, French, Danish,
Dutch, Swedish, Norwegian, Icelandic, Finnish) in ordinary word segmentation. Conditional character entropy
h2 is 2.18 to 2.35 bits in raw EVA and 2.66 to 2.89 bits under three independent glyph segmentations,
against a natural-language floor of 3.32 bits; any transposition of Latin gives at least 3.44; vowel
deletion leaves Latin at 3.52. This confirms Bennett (1976), Zandbergen and Lindemann & Bowern (2021) (L),
with the added point that it survives glyph merging and the Currier and v101 alphabets.

**Disfavoured*.** An unenciphered low-entropy non-European language (nearest published h2 is 2.77,
Hawaiian; L). Every published decipherment from Bax 2014 to the 2025-2026 LLM-assisted readings (L: none
has a reproducible key or survives blind application). Rugg's table-and-grille as the actual mechanism, and
free-edit self-citation as implemented here (section 5).

**Live, and not separated by this session or by the field (S, L).** (a) A verbose or positional cipher or
constructed encoding in which one plaintext unit becomes a rigid two- or three-glyph group, possibly with a
nomenclator; (b) structured meaningless text produced by a slot-preserving copy-and-modify procedure.
Every statistic that separates Voynichese from language is reproduced by at least one member of each
class. Judgement*: roughly even, perhaps 45:50 for (a):(b), with the remaining few percent on an
unenciphered exotic language. The three research camps reached the same shape of disagreement in 2022
(L: Gaskell & Bowern 2022 and Bowern & Gaskell 2022 published as a pair, one showing human gibberish
matches the statistics, the other showing ciphers do too).

## 2. Strongest counterargument first

All character statistics assume the transliteration and that EVA spaces mark plaintext units. Latin
re-segmented after {e, s, m} moves 60% of the way to Voynichese slot rigidity, and Latin cut into
vowel-final syllables is more rigid than Voynichese at equal length (S: v_a3). The exclusion therefore
covers word-boundary-preserving encodings of eleven languages in modern orthography; rule-based
re-segmentation, or a language with rigid consonant-vowel syllables written syllabically, was not tested.
Second, the verbose control that matches raw EVA on h1, h2 and their ratio at once produces words 2.3 times
too long (11.5 against 5.07 symbols) with Latin word entropy, so a letter-level verbose cipher of whole
Latin words is refuted by the session's own word-level data (S: v_a1). Both narrow the verdict; neither
overturns it.

## 3. Data

(S) ZL3b-n (Zandbergen-Landini, EVA, voynich.nu, version of 13 May 2025), paragraph text only, 34,116
tokens after dropping words with an unread glyph or extended-EVA codes; Currier A about 10,750 tokens,
B about 22,900; 7,236 word types. Cross-checked on RF1b-er, IT2a (Takahashi), GC2a (v101) and CD2a
(Currier). Parsed with `parse_ivtff.py`; uncertain word spaces (IVTFF commas, 2,463 in paragraph text)
were treated as breaks, and v_a2 shows the joined variant changes nothing material. Language controls are
single Gutenberg books (verse and prose distinguished where it matters) and an OCR'd 16th-century Italian
corpus containing about 8% Latin tokens (S: v_a1, v_a3). Entropies are plug-in; Miller-Madow correction
changes h2 by at most 0.007 (S: v_a1).

## 4. Key statistics (S)

### 4.1 Character entropies, bits, no spaces (a1, v_a1, v_a5)

| Text | h1 | h2 | h1-h2 | h2/h1 | mean word length |
|---|---|---|---|---|---|
| ZL raw EVA, Currier A | 3.832 | 2.353 | 1.479 | 0.614 | 4.98 |
| ZL raw EVA, Currier B | 3.859 | 2.182 | 1.677 | 0.565 | 5.12 |
| ZL raw EVA, all | 3.865 | 2.311 | 1.554 | 0.598 | 5.07 |
| ZL merged (benches, i/e groups, aiin, qo) | 4.039 | 2.870 | 1.170 | 0.710 | 3.7-3.9 |
| GC v101 (68 symbols) | 4.144 | 2.893 | 1.25 | 0.698 | 3.7-4.0 |
| Currier CD2a (35 symbols) | 3.857 | 2.660 | 1.197 | 0.690 | |
| Latin, Aeneid | 4.025 | 3.510 | 0.515 | 0.872 | 5.77 |
| German (diacritics folded 3.335) | 4.160 | 3.391 | 0.769 | 0.815 | 4.88 |
| Range of 11 languages (floor 3.32 folded) | 3.94-4.52 | 3.32-3.88 | 0.49-0.77 | 0.82-0.88 | 4.2-6.6 |
| Latin, vowels removed | 3.659 | 3.515 | 0.144 | 0.961 | 3.11 |
| Verbose cipher of Latin, every letter 2-3 symbols, 24 symbols | 3.901 | 2.325 | 1.576 | 0.596 | 11.52 |
| Verbose cipher, 8 letters kept single | 4.102 | 2.916 | 1.186 | 0.711 | 7.64 |

The redundancy is inside words: within-word h2 is 1.92 to 2.13 raw against 2.94 to 3.41 for languages.
Positional mutual information between glyph and position in word is 0.69 to 0.73 bits across ZL, Currier
and v101 against 0.17 to 0.27 for languages; 21 to 31% of glyphs are locked to one word position against
0 to 8% of letters (S: a5, v_a5). Greedy pair merging of the glyph stream closes the h1-h2 gap only after
about 40 merges, so an encoding of two- to three-glyph units drawn from 50 to 60 unit types is compatible
with the character statistics, a plain letter cipher is not (S: a5). The verifier's caveat stands: greedy
merging tests one heuristic, not the whole verbose class (S: v_a5). Word-level information budget:
425,468 bits, 12.47 bits per token, 0.82 times a Latin prose text of equal length under the same model
(S: a5, v_a5).

### 4.2 Zipf, hapax, vocabulary growth, 34,116 tokens (a2, v_a2)

| Corpus | Zipf slope, ranks 1-1000 | hapax % of types | Heaps beta | top-word share |
|---|---|---|---|---|
| Voynich all | -1.040 | 69.7 | 0.710 | 2.25% |
| Voynich A / B | -0.994 / -1.068 | 72.2 / 68.6 | 0.743 / 0.679 | 4.27% / 2.13% |
| Latin (Aeneid) | -0.820 | 67.0 | 0.749 | 4.9% |
| German | -1.045 | 65.1 | 0.779 | 3.46% |
| English | -1.056 | 55.1 | 0.675 | 4.68% |

All language-like, as the literature says (L: Landini 2001, Reddy & Knight 2011). Word-type entropy is
9.8 to 10.3 bits against 10.3 to 10.8 for Latin prose and 9.4 to 9.8 for Italian, French and German
(S: v_a1). The low top-word share is an A+B mixture effect (S: v_a2). Against single-book samples the
hapax rate is above every language, not inside the range (S: v_a5).

### 4.3 Word length, merged EVA (a2, v_a2)

| Corpus | mean | variance | variance / mean of (length-1) |
|---|---|---|---|
| Voynich all (raw EVA 5.07 / 3.73 / 0.92) | 4.11 | 2.48 | 0.80 |
| Voynich A (fixed parse, d1: 3.78 / 2.06 / 0.74) | 3.93 | 2.89 | 0.99 |
| Voynich B | 4.20 | 2.27 | 0.71 |
| Aeneid alone / Confessions alone | | 4.97 / | 1.04 / 1.74 |
| Italian / German / English / Danish | 4.53 / 4.99 / 4.23 / 4.67 | 6.52 / 7.04 / 5.41 / 7.40 | 1.85 / 1.77 / 1.67 / 2.02 |

Correction from the verifier: the famous under-dispersion ("binomial word lengths") is a Currier-B
property; Currier A matches single-text Latin verse. The binomial-fit contrast in a2 was a search-cap
artefact.

### 4.4 Word grammar rigidity and repetition (a3, v_a3, a2)

| Statistic | Voynich | Latin | Italian | German | English |
|---|---|---|---|---|---|
| Pair-order violations against the best glyph order, length-matched (shuffle null 0.49) | 0.160 (v101 0.140) | 0.363 | 0.318 | 0.278 | 0.308 |
| Adjacent identical tokens, % and observed:shuffled | 0.907 / 2.5 | 0.047 / 0.1 | 0.047 / 0.1 | 0.157 / 0.3 | 0.137 / 0.2 |
| Line-initial first-glyph effect, Cramer's V, paragraph-first lines excluded | 0.277 | pseudo-lined prose 0.02-0.03; hexameter 0.148 | | | |

Voynichese is 1.7 to 2.3 times more rigid than any tested language. The glyph order derived from the
data with no assumptions, q, then p f sh, then ch, then o t k, then e ee, then d s a, then l r y, then
g n iin m, is the Stolfi and Zandbergen layout recovered blind (S: a3). The line-final effect reported by
a2 collapses to V 0.07 to 0.16 once the final m and g allographs are removed; the line-initial effect
survives and exceeds hexameter verse (S: v_a2).

### 4.5 Self-citation distances (a4, v_a4)

Nearest earlier token at edit distance at most 1 on the same page, every corpus poured into the identical
page and line skeleton:

| Corpus | median distance | within 10 tokens | within-page shuffle | global shuffle | long tokens (5+) within 10 |
|---|---|---|---|---|---|
| Voynich ZL | 14 | 0.269 | 0.238 | 0.167 | 0.225 |
| Latin (Aeneid) | 41 | 0.035 | 0.034 | 0.030 | 0.006 |
| English (Italian, German similar) | 17 | 0.176 | 0.177 | 0.164 | 0.019 |
| Danish (verse) | 15 | 0.196 | 0.172 | 0.138 | 0.035 |
| Autocopist (Timm-Schinner re-implementation) | 13 | 0.329 | 0.275 | 0.079 | 0.257 |
| Rugg grille | 36 | 0.067 | 0.249 | 0.066 | 0.033 |
| Rugg sorted table | 34 | 0.329 | 0.162 | 0.112 | 0.341 |
| Order-3 character Markov model trained on Voynichese | 19 | 0.194 | 0.194 | 0.194 | 0.119 |

Sequential excess (real minus within-page shuffle): Voynich +0.031, Danish verse +0.024, autocopist
+0.054, prose about zero. Page-vocabulary excess (real minus global shuffle): Voynich +0.102, languages at
most +0.058, autocopist +0.250. For long tokens the language baselines collapse to 0.035 or less while
Voynichese stays at 0.225, but a memoryless character model reaches 0.119: about half of that density is
word-internal structure, not copying (S: v_a4). Brute-force Levenshtein reproduced every Voynich locality
figure exactly.

### 4.6 Generator comparison (a4, v_a4, a3)

| Text | types | h2 raw | h2 merged | Zipf slope | hapax % | adjacent repeat | pair-violation |
|---|---|---|---|---|---|---|---|
| Voynich ZL | 7,236 | 2.311 | 2.646 | -1.040 | 69.7 | 0.0082 | 0.160 |
| Autocopist, two seeds | 11,660 / 11,330 | 2.709 / 2.723 | 3.274 / 3.005 | -0.825 / -0.859 | 72.2 / 71.1 | 0.0013 / 0.0018 | free-edit 0.41-0.46 |
| Rugg grille / sorted table | 3,747 / 1,757 | 2.798 / 2.629 | 3.176 / 2.912 | -0.429 / -0.622 | 5.7 / 13.9 | 0.0003 / 0.0893 | fitted table 0.122 |

No generator matches on all columns. The autocopist yields only 37% real Voynich word types by token,
2% qo-initial words against 15%, and h2 0.4 to 0.6 bits too high; it is this session's re-implementation
of the published algorithm with documented deviations, not Timm's reference program. Grilles fail Zipf
and hapax. The one table that reproduces the slot rigidity had its columns read off Voynichese, which shows
sufficiency only (S: v_a3).

### 4.7 Currier A and B (a6, v_a6)

| Statistic | A | B |
|---|---|---|
| Tokens ending -edy / containing ed | 0.20% / 0.29% | 17.34% / 20.84% |
| Containing cho / starting qo- / ending -ol | 16.1 / 10.0 / 14.5% | 2.7 / 17.7 / 7.1% |
| Glyph after ch: e / o | 24.5 / 46.1% | 60.1 / 10.1% |
| daiin per thousand tokens | 42.5 | 13.0 |

Unsupervised folio clustering recovers Currier's labels at 95.4 to 99.5% on 197 folios; a single -edy
threshold separates them at 99.5% leave-one-out, A a spike (112 of 114 folios below 2%), B a continuum
from 3 to 42%; the same in IT2a. The language is nearly a function of the scribe: H(language | hand) =
0.09 bits, 98.2% of lines predicted from hand alone, the only mixed cell being hand 3 in the stars section.
Vocabulary sharing A against B, size-matched, gives Jaccard 0.147 and top-100 overlap 0.95, against 0.207
and 1.00 for two halves of A, 0.172 and 0.91 for two English novels, 0.116 and 0.67 for Danish against
Norwegian. A word-final pattern moving from 0.2% to 17% has no parallel between books in one language but
does between languages (French against Italian, final -o 0.19% to 17.5%) (S: v_a6). Section-specific
vocabulary exists (mean chi-square per token 0.654 against 0.121 shuffled and 0.40 for Italian) and
persists within one scribe and one language, but the section words are members of the same sub-word
families, qokain, qol, qokeedy, okeol, rather than anything that looks like content vocabulary (S: v_a6).
Parisel's 2026 preprint reaches the same single-switch description independently (L).

## 5. Hypothesis status

**Excluded.** (1) Plaintext or monoalphabetic substitution of the eleven tested languages: h2 gap at
least 1.0 bit raw, at least 0.4 bit merged (S: a1, v_a1; L: Bennett 1976, Zandbergen, Lindemann & Bowern
2021). (2) Substitution plus vowel removal or conventional abbreviation (S: a1, a5; L). (3) Letter-level
transposition of a real plaintext, including grille rearrangement (S: v_a5; L). (4) Vigenere-type
polyalphabetics (L: Stolfi 2000, D'Imperio 1978). (5) Single-glyph nulls as the source of the redundancy
(S: a5). (6) Named decipherments: Cheshire 2019 (L: refuted by its reviewers), Hauer & Kondrak 2016 as a
decipherment (L: the authors' own caveat), Bax 2014, Gibbs 2017, Ardic, Gladyseva 2023, Schechter 2025 and
the LLM-assisted readings (L: no reproducible key, none survives blind application). (7) Modern forgery
(L: radiocarbon, ink, provenance).

**Disfavoured*.** An unenciphered exotic language (L: nearest h2 2.77; the slot grammar has no parallel).
Rugg's grille as the mechanism: Cardan grilles date from about 1550 against 1404-1438 vellum, the special
roles of f and p cannot arise from the table (L: Zandbergen 2021), and the session's grilles fail Zipf and
hapax (S: a4). Free-edit self-citation: it over-produces locality and vocabulary and under-produces
character redundancy, while the manuscript's sequential copying excess is only the size of Danish verse
(S: a4, v_a4). Dee and Kelly glossolalia (L: Daruka 2020; conflicts with the vellum date).

**Live.** (a) A verbose or slot-template cipher of short units, a nomenclator, or a constructed language
with meaning: compatible with 4.1, 4.4 and 4.7 and with a hand-executable 15th-century design that
reproduces several headline statistics (L: Greshko 2025, the Naibbe cipher; Bowern & Gaskell 2022), but it
must also meet the word-length constraint (verbose controls give 7.6 to 11.5 symbols; S: v_a1), the
near-zero token-to-token predictability (L: Rozanova & Temerev 2026, preprint) and the line-initial effect
(S: v_a2). (b) Slot-preserving copy-and-modify generation (L: Timm & Schinner 2020, 2023; Timm 2026):
compatible with everything measured, but the slot grammar is an input to that model, not a product
(S: a3), and no implementation has been run at manuscript length against page, section and scribe
structure (L: consensus of all three sweeps). (c) A real language under a non-word segmentation:
untested (S: v_a3).

## 6. What the physical evidence adds (L)

Radiocarbon 1404-1438 from four folios (Hodgins, University of Arizona, 2009). Iron-gall ink and period
pigments (McCrone 2009, Yale 2014). Five hands, three of them writing 188 of the 227 pages (Davis 2020),
and this session finds Currier language almost determined by hand (S: a6). The codex is misbound relative
to its quire marks. Month names in a Romance dialect and a German-hand marginal note on f116v put it in
German- and French/Occitan-speaking hands within decades. Multispectral images of ten folios, taken in 2014
and released in 2024, recovered an erased alphabet trial on f1r and Tepenecz's ex libris, not new
Voynichese. Consequence for the question: any meaningless-text account must be a 1420s production on fresh
calfskin by several collaborating scribes who kept one slot grammar and one A/B switch consistent across
200-plus pages, which is a cost that no statistic addresses; any cipher account must explain why the scribe
rather than the subject matter sets the "language". Ink layering, pigment order and quire order were not
examined here.

## 7. What would settle the rest

1. A pre-registered generator bake-off at manuscript length: self-citation, table-and-grille, Naibbe-
   enciphered Latin and human gibberish under one battery that includes the Montemurro-Zanette long-range
   keyword peak, topic by illustration by scribe co-clustering, page-adjacency similarity, A/B separability,
   the f and p rules and the token-predictability measure. Scripts a1 to a6 are a partial battery that runs
   on any candidate text in the TSV format.
2. Manuscript-length human gibberish written over weeks with illustrations and sections (L: the open test
   named by Gaskell & Bowern 2022).
3. Illustration-to-text mutual information with hand, quire and adjacency partialled out.
4. Re-tokenisation on certain spaces only, and the same statistics on a syllabic segmentation of Latin and
   Italian, to close the gap left in section 2.
5. For any claimed key: blind application by a third party to five A and five B folios with a
   shuffled-glyph control.

## 8. Checked, not checked, user must verify

**Checked.** Every headline number in a1 to a6 was reproduced by an independent re-implementation
(v_a1 to v_a6), including the Levenshtein code, the entropy formulas, estimator bias, corpus contents and
Gutenberg boilerplate. Robustness across ZL, RF1b, IT2a, GC2a and CD2a. Corrections applied: single-book
samples; Latin word entropy from prose not verse; a folded natural-language floor of 3.32; rigidity ratio
1.7 to 2.3; under-dispersion as a Currier-B property; the line-final effect as the m/g allograph; the A/B
rule at 99.5% leave-one-out. My own two baseline scripts agree with a1 and a2.

**Not checked.** Paywalled Cryptologia full texts (Rugg 2004, Schinner 2007, Timm & Schinner 2020 and
2023, Daruka 2020, Greshko 2025) were characterised from abstracts and secondary summaries. Timm's
reference generator was not run. Higher-order entropies, per-hand entropies, significance tests on A
against B, bootstrap intervals. No higher-level literature statistic (the Montemurro-Zanette peak, topic
models, adjacent-page similarity) was recomputed. Davis's hand assignments were taken as given from the
IVTFF headers. Physical evidence beyond radiocarbon, ink, hands and the 1639 letter.

**User must verify before quoting.** The corpus choices (single Gutenberg books; an OCR Italian corpus
with about 8% Latin; verse against prose Latin), the glyph merge lists, the design of the 24-symbol
verbose controls, the treatment of uncertain spaces as breaks, and the labels excluded, disfavoured and
live. All output is unvalidated until review.

## Files

`fetch_corpora.py` (downloads every comparison corpus and transliteration into git-ignored folders and
freezes the Italian sample; run it first), `parse_ivtff.py` (IVTFF to TSV; see the parse defect in section 0),
`data/ZL3b-n.words.tsv` (the parsed main transliteration), `baseline.py`, `baseline2.py`, `a1_charstats.py` to
`a6_structure.py`, `v_a1.py` to `v_a6.py`, `b1_segmentation.py` to `b4_robustness.py`, `v_b1.py` to `v_b4.py`,
`c1_comparators.py`, `c3_period.py` (data in `data/period/`, built by `data/period/_extract.py`),
`c2_charts.py` (writes the inline SVG charts into docs/voynich.html), `data/lb2021_wikipedia_h2.tsv`
(Lindemann & Bowern 2021 Appendix B), `results/` (JSON and Markdown per analysis and per verification, plus
generator samples), `NOTES_draft.md` (the synthesis agent's draft this file was edited from), `SOURCES.md`
(the five literature sweeps with strengths and sources).
