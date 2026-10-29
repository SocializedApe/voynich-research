# How much does a Voynich word's beginning predict its end? Results, 28 Oct 2026

Scripts: `slot_independence.py` (Voynich against three languages), `slot_controls.py` (generators and ciphers).
Data: ZL 3b paragraph text; Latin, German 1470-1610 and English from `lang/corpora`; generators from
`targets/voynich/a4_selfcitation.py`; the Naibbe ciphertext shipped with github.com/greshko/naibbe-cipher
(`encrypted/nathist_output_ciphertext.txt`, Pliny; not committed here).

## Why

Fontana's *Secretum* (BnF n.a.l. 635, c. 1430) describes letter wheels for composing words: the *Speculum* (f. 21r)
is five alphabet wheels turned independently to make a five-letter word; the "snake" (ff. 29v-31r) a row of
alphabet gear wheels (Ponzi, viridisgreen 2021; Battisti & Battisti 1984; Neal). That is a dated North-Italian
device of the Voynich decades that composes words slot by slot. It answers the anachronism objection made to
Rugg's grille (Cardan grilles c. 1550). A slot-by-slot word maker should leave a word's opening and ending nearly
independent once the length is fixed; a language, or a cipher that encrypts whole words letter by letter, should
not. Volvelle generators for Voynichese have been proposed (D. Jackson 2014; voynich.ninja threads 5600 and 5739,
2026), but not tied to Fontana's devices and not measured this way, as far as found.

## Measure

I(prefix; suffix | word length) for word tokens of 4-8 units, prefix and suffix = first and last k units (k = 1, 2),
minus the same with suffixes shuffled among words of equal length, divided by min(H(prefix|L), H(suffix|L)).
Units: glyph units for Voynichese and the generators (ch, sh, cth, ckh, cph, cfh, qo, ee, ii, aiin, ain, iin as one),
letters for the languages. Up to 30,000 tokens per text. Also on word types (each distinct word once).

## Results (normalised dependence)

| Text | k = 1, tokens | k = 2, tokens | k = 1, types |
|---|---|---|---|
| **Voynich, all** | **0.040** | **0.155** | 0.001 |
| Voynich, Currier A / B | 0.027 / 0.057 | 0.114 / 0.179 | |
| Voynich, raw EVA letters | 0.101 | 0.192 | |
| Autocopist (Timm & Schinner), seeds 19 / 7 | 0.038 / 0.063 | 0.120 / 0.145 | 0.020 / 0.025 |
| Rugg grille | 0.048 | 0.178 | 0.004 |
| Rugg sorted table | 0.252 | 0.365 | 0.064 |
| **Naibbe cipher** (Greshko 2025, Pliny) | **0.052** | 0.196 | 0.000 |
| **Verbose Latin**, fixed 2-glyph group per letter | **0.344** | 0.486 | 0.009 |
| Verbose Latin, 3 homophonic groups per letter | 0.123 | 0.327 | 0.015 |
| Latin | 0.13-0.18 | 0.27-0.38 | 0.013 |
| German 1470-1610 | 0.24-0.30 | 0.44-0.54 | 0.027 |
| English | 0.27-0.31 | 0.50-0.56 | 0.017 |

(Ranges for the languages: three runs with different random windows; sampling spread about +-0.03.)

## Reading*

1. Voynich word tokens have 3-7 times less start-end dependence than Latin, German or English.
2. The mechanisms that match it all build a "word" from a small or combinable unit: the self-citation generator, the
   simple grille, and the Naibbe cipher, in which each Voynich word encodes one or two plaintext letters.
3. A cipher that encrypts whole Latin words letter by letter keeps (with fixed groups, raises) the language's
   dependence: 0.34 fixed, 0.12 with three homophones per letter, against 0.04. With this measure, a verbose cipher in
   which one Voynich word is one plaintext word is disfavoured, in line with the repository's earlier word-length
   argument (verbose words come out 2.3 times too long; `targets/voynich/NOTES.md` section 2).
4. On word types the dependence is near zero for every text, so the token effect comes from which words are
   frequent: in the languages the common words tie particular openings to particular endings; in Voynichese the
   common words spread across opening and ending combinations (chedy, shedy, qokedy, okedy ...), as a combinatorial
   system or a slot cipher would make them.
5. This does not separate "meaningless combinatorial text" from "Naibbe-like cipher of short plaintext units":
   both match. It narrows the cipher side to schemes in which a Voynich word carries a small piece of plaintext.

## Naibbe across seeds (`slot_naibbe_seeds.py`)

Naibbe regenerated from the Latin corpus with the repository's port (`targets/voynich/b3_bakeoff.Naibbe`) and
Greshko's tables, seeds 19, 7, 3, 101, 2026: k = 1 0.050-0.053, k = 2 0.199-0.202 (Voynich 0.040 / 0.155). Stable,
and at k = 2 a little above Voynichese, where the autocopist (0.120-0.145) is a little below. Small, not decisive.

## On the fixed parse

With `targets/voynich/parse_ivtff.py --fixed` (word breaks at `<->`, ligature glyphs kept): all 0.040 / 0.156,
Currier A 0.031 / 0.120, B 0.057 / 0.181 (k = 1 / k = 2). Unchanged.

## Robustness (`slot_robustness.py`, 28 Oct 2026)

| Text | k = 1 | k = 2 |
|---|---|---|
| Voynich ZL3b, fixed parse | 0.038 | 0.155 |
| Voynich IT2a (Takahashi), fixed parse: all / A / B | 0.036 / 0.028 / 0.053 | 0.154 / 0.119 / 0.178 |
| Human gibberish (Gaskell & Bowern 2022, 38 volunteer files, 10,075 tokens) | **0.043** | 0.064 |
| Verbose Latin, length-matched (ciphertext 4-8 units), fixed groups, 5 tables | 0.23-0.41 | 0.44-0.49 |
| Verbose Latin, length-matched, 3 homophones per letter, 5 tables | 0.10-0.15 | 0.23-0.25 |

The result replicates on a second transliteration, and the exclusion of whole-word verbose ciphers survives length
matching and five random tables. **But human gibberish is as start/end-independent as Voynichese at k = 1.** People
inventing words also combine openings and endings freely. So the measure separates "a cipher of whole words" from
"words made of freely combined parts", and the second group includes a fragment cipher (Naibbe), copy-and-modify
generation, a grille, and plain human invention.

## Limits and checks still to do

- Length matching of the verbose controls: done (robustness section).
- Several tables per verbose control: done (five each).
- The glyph-unit list is one choice; raw EVA letters give Voynich 0.10 (still below every language).
- Prior work (checked 28 Oct 2026): near-independence of Voynich prefixes and suffixes is already reported, e.g.
  NMI(prefix, suffix) = 0.032 in a non-peer-reviewed analysis (github.com/Workwrite-Niidome/voynich-manuscript-analysis),
  Stolfi's note on "the remarkable evenness and independence" of the gallows and bench traits (word-structure tech
  report), and slot models (Stolfi's grammar; Zattera 2022, CEUR-WS 3313 paper 10, 12 slots). What this note adds is
  the comparison under one measure with verbose ciphers of whole words (which fail), Naibbe and the generators
  (which match), and the link to a dated slot device (Fontana's wheels). arXiv 2604.19762 (2026) studies
  cross-word boundary information, a different quantity.
