# The line as the unit of production (10 Nov 2026)

Two tests on the ZL paragraph text (fixed parse, 207 pages, 34,834 tokens) with Latin, English, the Naibbe cipher
of Pliny, the autocopist (two seeds) and the gibberish volunteers poured into the same page/line skeleton. Scripts
`boundaries.py` and `copy_geometry.py`; tables in `boundaries.md`, `copy_geometry.md`; loader `common.py`.

## 1. The word-to-word coupling restarts at every line (`boundaries.py`)

Edge coupling X = normalised excess mutual information between the last glyph unit of a word and the first glyph
unit of the next word (as cipher_models.md), by kind of adjacent pair:

| text | inside a line | lag 2 inside a line | across a line break | across a break, skipping the line-initial word | across a paragraph break |
|---|---|---|---|---|---|
| Voynich | 0.060 | 0.003 | 0.0004 | 0.006 | 0.018 (n 533) |
| Voynich A / B | 0.041 / 0.079 | 0.002 / 0.003 | 0.001 / 0.001 | 0.003 / 0.005 | |
| Latin poured | 0.019 | 0.001 | 0.022 | 0.001 | 0.010 |
| English poured | 0.018 | 0.006 | 0.018 | 0.003 | 0.005 |
| Naibbe | 0.001 | 0.000 | 0.002 | 0.001 | |
| autocopist | 0.003 / 0.002 | 0.002 | 0.001 | 0.005 / 0.001 | |
| gibberish volunteers | 0.016 | 0.015 | 0.016 | 0.015 | |

Reading. In running text the coupling (Latin: the phonotactics and grammar of word endings and beginnings) carries
across a line break exactly as inside a line, because the lines are arbitrary cuts of a stream. In Voynich the
coupling, three times Latin's inside the line, is zero across the break, and skipping the line-initial word
recovers only a tenth of it: the process that ties a word's opening to the previous word's ending starts afresh at
each line. It is also strictly adjacent (lag 2 at 0.003), so it is not hand or page heterogeneity, which would show
at every lag as it does for the gibberish volunteers (whose coupling is the same at every lag and across breaks:
the pooled MI of 38 different writers' letter habits, not adjacency). Consequence for the cipher side: a chained
cipher of running text (the round-8 model's book-wide chaining rule) would carry its chain across line breaks
unless the clerk restarted it at every line; a plaintext itemised line by line (a list) would also give the
reset. Consequence for the generator side: the line is the unit inside which the word-making process has memory.

Update, same day (`reinforce/volunteers.py`, `reinforce/gibberish_fit.md`): the volunteers' transcriptions keep their
written lines and pages, and read as written their coupling is zero inside the line as well as across it (0.003 /
0.001 with a null shuffled within each page; the 0.016 above is writer heterogeneity). Five of 35 writers chain their
words at z >= 3 against their own shuffles, against 62 of 128 Voynich pages of the same size. Their line-first word
has no vocabulary of its own (JSD 0.012 against 0.205) and their last word is longer, not shorter. Casual
improvisation does not produce the line structure.

## 2. The line has a shaped beginning and end

JSD (bits) between the first-unit distribution of words at a given index in the line and that of interior words;
sampling floor from within-line shuffles about 0.002:

| index | 1 | 2 | 3 | 4 | 5-8 | third from last | second from last | last |
|---|---|---|---|---|---|---|---|---|
| Voynich | 0.205 | 0.020 | 0.005 | 0.003 | 0.002-0.006 | 0.004 | 0.010 | 0.049 |
| autocopist | 0.028-0.035 | 0.001-0.003 | 0.001 | 0.001 | 0.001-0.002 | 0.001-0.002 | 0.001 | 0.001 |
| poured texts | 0.001-0.002 throughout | | | | | | | |

Mean word length: first word 5.44, interior about 5.0, last 4.65 (Currier B: 5.55 / 5.2 / 4.67). (Correction,
second session: the first-word offset has the size wrapping alone gives; see section 5 for what does and does not
survive.) The second word
and the penultimate word are affected too, beyond the known first and last. The autocopist reproduces a weak
first-word effect only.

## 3. One boundary rule for the book, with an A/B difference

PMI matrices of (last unit -> first unit) over the 12 commonest units each way, Pearson correlation between random
halves of each group (within) and between groups (between), 10 splits, 4,500-4,800 pairs a half:

| groups | within | between |
|---|---|---|
| Currier A, B | 0.92, 0.94 | 0.77 |
| hands 1, 2, 3 | 0.91, 0.97, 0.93 | 1 vs 2 0.76; 1 vs 3 0.69; 2 vs 3 0.93 |
| Latin, two halves | 0.80, 0.79 | 0.81 |
| Naibbe, two halves | 0.05, 0.08 | 0.18 (no rule) |

The rule is largely shared (0.77 of a 0.93 ceiling) and the two B hands share it fully; the A/B convention changes
part of it. This is the same shape as the repository's result 2 (one system, personal habits on top).

## 4. Near-copies are not copied from the line above (`copy_geometry.py`)

For every pair of lines k apart on a page, every pair of words at Levenshtein distance <= 1; share of pairs at the
same word index +-1 (align1). Null A shuffles words within each line (destroys positions and position vocabulary);
null B swaps words at the same index among the lines of the page (keeps position vocabulary, destroys which line a
word is in). Ratio observed / null (z):

| text | k = 1, all positions, vs A | vs B | k = 1, interior words only (index >= 2, not last), vs B | k = 2, vs B | k = 3, vs B |
|---|---|---|---|---|---|
| Voynich | 1.13 (+9.3) | 1.01 (+0.7) | 0.99 (-0.7) | 1.05 (+3.7) | 0.97 (-2.6) |
| autocopist s19 / s7 | 1.12 / 1.09 (+8, +7) | 1.01 / 1.02 | 1.04 / 1.04 (+3.4, +3.1); same index 1.22 / 1.13 (+7, +5) | 0.99 / 1.02 | 1.00 / 1.01 |
| Latin, English, Naibbe, gibberish | 0.95-1.03 | 0.95-1.03 | 1.00-1.02 | | |
| gibberish volunteers with their own lines and pages (`reinforce/gibberish_fit.md`) | | | 1.06 (+2.2); same index 1.13 (+2.4) | | |

Reading. Against null A the Voynich near-copies look vertically aligned (+13%) at every line distance alike, which
is position vocabulary: line-initial words resemble line-initial words, line-final words line-final words. Against
null B, which keeps that, the alignment vanishes, and among interior words there is none at k = 1. The autocopist,
which by construction copies from the same position in a previous line 28% of the time, shows the alignment
against null B exactly where Voynich does not. So the scribes did not take their near-copies from the word above;
the self-citation signal of a4 (near-copies within 10 tokens, +0.03 over the within-page shuffle) lives in the
same line: the nearest earlier near-copy is in the same line for 0.141 of tokens (within-page shuffle 0.119), in
the line above for 0.180 (0.172), two or more lines up less often than the shuffle (0.329 vs 0.358). The small k = 2
excess against null B (+5%, z 3.7) is unexplained and not pursued.

## 5. Wrapping: the first word is long but it is not an overflow word (`wrapping.py`, second session, 10 Nov 2026)

Section 2 read the longer first word and the shorter last word as a shaped line. Wrapping any stream of words into
lines of limited width selects by length (the word that did not fit opens the next line), and the controls of
`boundaries.py` were poured in by word count, so they could not show it. Here streams are wrapped greedily into the
Voynich paragraphs (width = the paragraph's longest line in EVA characters, less 0..J per line for a ragged margin),
and the same estimators are applied to the real lines. Lines of 6+ words; lengths in EVA characters.

| text | first - interior | last - interior | JSD first / last | early breaks | r (slack of a line, length of the next line's first word) [95%] | r (space before the last word, its length) |
|---|---|---|---|---|---|---|
| Voynich | +0.48 | -0.31 | 0.205 / 0.049 | 0.36 | -0.011 [-0.045, +0.020] | 0.27 |
| Currier A / B | +0.56 / +0.48 | -0.05 / -0.41 | 0.134 / 0.263; 0.053 / 0.049 | 0.44 / 0.31 | -0.010 / -0.009 | 0.26 / 0.29 |
| stars section (text only, no drawings in the way) | +0.40 | -0.32 | 0.351 / 0.045 | 0.24 | -0.041 [-0.113, +0.029] | 0.47 |
| volunteers, their own handwritten lines | +0.39 | +0.42 | 0.012 / 0.007 | 0.61 | +0.017 [-0.041, +0.068] | 0.02 |
| Voynich words shuffled within the page, wrapped, J 0 / 6 / 12 / 20 | +0.41 / +0.43 / +0.46 | +0.07 / +0.04 / +0.02 | 0.003-0.005 / 0.002 | 0 / 0.22 / 0.43 | +0.38 / +0.25 / +0.17 / +0.09 [+0.06, +0.12] | 0.65 / 0.52 / 0.37 |
| Latin wrapped, J 0 / 6 / 12 / 20 | +0.69 / +0.72 / +0.77 | +0.09 / +0.14 / +0.20 | 0.003 / 0.001 | 0 / 0.19 / 0.40 | +0.40 / +0.34 / +0.20 / +0.15 | 0.67 / 0.57 / 0.44 |
| English wrapped, J 0 / 6 / 12 | +0.92 / +0.96 / +0.88 | -0.04 / -0.07 / -0.10 | 0.008 / 0.003 | 0 / 0.23 / 0.43 | +0.54 / +0.40 / +0.28 | 0.68 / 0.57 / 0.44 |

'Early break' = the next line's first word would have fitted in the space left. Mean first-word length after a line
with 0-1 / 2-3 / 4-6 / 7-10 / 11+ characters of slack: Voynich 5.29 / 5.23 / 5.24 / 5.25 / 5.15; shuffled Voynich
wrapped at J 6: 5.17 / 5.26 / 5.56 / 6.09 / 7.75.

Reading.
- The size of the first-word offset is what wrapping gives by itself (+0.41 to +0.46 of +0.48), so the offset alone
  was no evidence of a shaped line, and section 2's sentence on it is corrected here. By the rule set before the
  run the offsets are not withdrawn as a pair, because the last word fails: wrapping gives +0.02 to +0.07, Voynich
  -0.31, nearly all of it in Currier B (-0.41; A -0.05).
- Yet the Voynich first word is not the word that did not fit. Under wrapping the first word's length follows the
  slack on the line above (r 0.17-0.38 at ragged margins that give Voynich's share of early breaks, still 0.09 at a
  margin ragged by 20 characters); in Voynich the correlation is -0.01 (interval -0.05 to +0.02; stars section
  -0.04), and the first word after a line that stopped 11+ characters short is no longer than after a full line.
  So the lines were not made by wrapping a stream of ready words: the first word is long for its own reasons
  (section 6), whatever was left on the line above. A text copied from an exemplar with other line breaks, or
  enciphered word by word and wrapped, would show the overflow correlation unless the last word was always squeezed in.
- The last word is fitted to the space (r 0.27-0.47, as under wrapping), and is shorter than wrapping makes it.
- The vocabulary effects of section 2 stand: wrapping gives JSD 0.003-0.005 / 0.002 against 0.205 / 0.049.
- The volunteers show no overflow correlation either (+0.02), with very ragged lines (mean slack 19 characters
  against 6), and both edge words longer.

Limits: width is counted in EVA characters (a bench or a gallows is wider than an i), and the width of a paragraph
is taken as its longest line, which drawings in the text area violate; the stars section, which has none, gives the
same answer. 'Voynich in its own order' re-wrapped gets some of the real breaks back and is not a null.

## 6. What the edge words are made of (`edges.py`)

Word = opener | middle | ending (`reinforce/slots4.split3`); interior = words at index 3 and later, not the last two.

**First word.** It almost always has an opener (none: A 0.16, B 0.11; interior 0.42, 0.38), and its middle is longer
(A 1.96 against 1.64 characters, B 1.86 against 1.47). In 37% of lines it is 'prefixed-like': without its first
glyph it is a word at least five times commoner inside lines (interior words 14%, words shuffled within the line
16-19%). The glyphs in front are d (38% of d- first words against 12% of interior d- words), y (40% / 12%), s (63% /
43%), o (15% / 4%), sh (26% / 10%), l (71% / 44%); gallows-initial first words are prefixed-like at the interior
rate (t 0.60 / 0.59, k 0.50 / 0.50). Taking the front glyph off the prefixed-like words leaves +0.28 of the +0.48
(outside paragraph-first lines +0.14 of +0.34). The second word lacks an opener more often than interior words
(0.52-0.55 against 0.38-0.42).

**Last word.** Its length follows the space left before it: with 3 characters or fewer it is 2.4 characters long and
has no middle 83-87% of the time, with 4-5 it is 3.8-3.9 long, with 9+ it is 5.2-5.3, longer than an interior word
(A 4.66, B 5.07). The middle goes first, then the opener; the ending stays (none: 2-5%). But it is not an ordinary
short word picked to fit: at every length from 1 to 8 characters the last words differ from interior words of the
same length (JSD 0.14-0.27 against a floor of 0.02-0.08, and 0.13-0.26 with the words in -m left out). The same
holds for first words (0.17-0.31 against 0.04-0.08).

**Endings at the line end.** -am is 41 times commoner in the last word than inside the line in B (16% of last
words), -om 53 times, -m 25 times; in A -am 9 times (8%), -om 5 times. The endings that mark each language avoid
the line end: B's -eey x0.2, -eedy x0.4, -ey x0.4, -edy x0.5; A's -ol x0.2, -or x0.3. B's shorter last word is this
substitution (ending length 1.96 against 2.39 inside the line; A 1.94 against 1.95).

**The A/B convention by position** (JSD between A and B, bits; in brackets interior words subsampled to the same
counts, mean of 20 draws):

| slot | first | second | interior | penultimate | last |
|---|---|---|---|---|---|
| opener | 0.057 (0.071) | 0.073 (0.077) | 0.069 | 0.098 (0.073) | 0.106 (0.072) |
| middle | 0.107 (0.082) | 0.093 (0.082) | 0.077 | 0.094 (0.083) | 0.116 (0.082) |
| ending | 0.139 (0.150) | 0.152 (0.145) | 0.147 | 0.159 (0.147) | 0.087 (0.149) |

The ending difference between the languages, the largest of the three, drops by 40% in the last word (0.087
against 0.147-0.150 at the same counts), while opener and middle differ more at the line end than inside. So the
line end has its own set of endings that both languages use, and the convention that separates A from B is partly
suspended there.

Reading. Each line has a made beginning (an ordinary word with d, y, s, o or sh in front in about a quarter of
lines beyond the base rate, an opener nearly always) and a made end (a word of its own vocabulary built to the
remaining space, with a line-end set of endings shared by A and B). With section 5 (no overflow word) and section 1
(the chain restarts), the line is composed as a unit in the layout we have, not cut from a stream.

## 7. Three follow-ups (11 Nov 2026): a list, the m words, the labels

**A list, or a clerk who squeezes the last word in? (`listcipher.py`)** Two ways a text with content could still
give section 5. (A) Every line is one item of a list: then a line is as long as its item. Voynich lines that are not
the last of their paragraph fill 0.89 of the paragraph's longest line (CV 0.16; 3% under half the width, 17% under
80%); real items measured the same way vary three times as much and half are under half-width (Latin Vulgate
verses CV 0.43, 48% under half; clauses CV 0.50, 54%). Voynich paragraphs do look like items (CV 0.61). So lines
are filled to a margin, not items. (B) A stream in which the word that does not fit is cut down to fit with
probability q instead of opening the next line (cut as section 6 found: middle first, then opener):

| q | first - int. | last - int. | early breaks (J 12) | r slack, next first | r space, last |
|---|---|---|---|---|---|
| Voynich | +0.48 | -0.31 | 0.36 | -0.011 [-0.045, +0.020] | 0.27 |
| 0 | +0.47 | +0.04 | 0.43 | +0.17 | 0.37 |
| 0.5 | +0.26 | -0.83 | 0.42 | +0.11 | 0.50 |
| 0.8 | +0.14 | -1.33 | 0.41 | +0.06 | 0.49 |
| 1 | +0.06 | -1.66 | 0.41 | +0.01 | 0.44 |

Only a clerk who always cuts removes the overflow correlation, and the cell q 1, J 12 meets the three conditions
written before the run (r inside Voynich's interval, early breaks within 0.10, last offset negative). The
conditions were too loose: at q 1 the last word is 1.66 glyphs shorter than interior words, five times Voynich's
0.31, and at any q that gives Voynich's last-word offset (below 0.5) the overflow correlation is back (0.11+). No q
gives both. Cutting a ciphertext word also destroys what it encodes.

**The line-final m words (`lineend.py`).** 80% of B's m words and 52% of A's are line-final. They are not padding:
the share of last words that are m words does not depend on the space left before the last word (B 0.15-0.22
across bins, A 0.11-0.14) or on the slack left after the line (B 0.18-0.21, A 0.10-0.12), and at the same space an m
word is as long and leaves as much slack as any other last word. They are not stuck on: the chain from the
penultimate word to an m last word is as strong as between interior words (X 0.081 against 0.059; other last words
0.054). They are not one ordinary ending swapped at the margin: the stems of line-final -am words (commonest:
none, d, ot, qok, ok) are nearest those of interior -aiin words but far from them (JSD 0.16, floor 0.03; -y 0.24,
-ol 0.27, -edy 0.43). After an m word the next line starts a little differently in B (first-unit JSD 0.026,
label-shuffle maximum 0.014; A 0.018, within its floor). So -m is a line-end form of the word-making process
itself, used at a fixed rate per line whatever the space.

**Labels and ring texts (`labels.py`).** Labels (741 words beside drawings, 603 of them alone at their locus) are
not written in lines.

| group | n | length | no opener | no middle | no ending | m-final | words found in paragraphs | prefixed-like | variance ratio | chain MI of the ending (bits) |
|---|---|---|---|---|---|---|---|---|---|---|
| paragraph interior | 18360 | 4.96 | 0.40 | 0.46 | 0.012 | 0.008 | 1.00 | 0.14 | 0.71 | 0.81 |
| line-first | 3339 | 5.44 | 0.12 | 0.36 | 0.010 | 0.004 | 1.00 | 0.37 | 0.71 | 0.84 |
| line-last | 3339 | 4.65 | 0.33 | 0.43 | 0.030 | 0.171 | 1.00 | 0.16 | 0.69 | 0.81 |
| labels | 741 | 5.19 | 0.21 | 0.27 | 0.067 | 0.055 | 0.60 | 0.08 | 0.97 | 0.67 |
| circular text | 2338 | 4.77 | 0.44 | 0.38 | 0.033 | 0.019 | 0.77 | 0.11 | 0.87 | 0.85 |
| radial text | 350 | 5.21 | 0.28 | 0.29 | 0.034 | 0.029 | 0.73 | 0.11 | 0.63 | 0.83 |

First-unit JSD of labels: against interior words 0.18, against line-first words 0.25, against line-last words 0.11
(floors 0.003-0.005); endings 0.12 / 0.16 / 0.06. Labels are made by the same recipe (slots, within-word chain 0.67
of 0.81 bits) but are a population of their own: 40% are not paragraph words, they nearly always have an opener and
a middle, they are not prefixed-like (0.08: the glyph in front is a line-start matter), and the length budget is
gone as a whole (variance ratio 0.97 against 0.70), though it holds within chain contexts (r -0.15, -0.15). They
are nearer line-last words than interior or line-first words, without being like any of them. Limit: labels sit in
the zodiac, astronomical and pharmaceutical pages, the reference groups are all paragraphs; section is confounded.

## Reproduce

All commands are run from `targets/voynich` (Python 3 with numpy; the scripts are seeded, so reruns give the same
numbers). Inputs that are git-ignored and have to be fetched first: `python fetch_corpora.py` (ZL transliteration and
comparison texts into `data/`), `python -m lang.corpora la-gutenberg` from the repository root (Latin), and Greshko's
Naibbe files into `data/external/naibbe/out/` (see `SOURCES.md`, `CREDITS.md`). Every script states its protocol in
its docstring and writes a `*_results.json` beside the `.md` table it prints.

| section | command | writes |
|---|---|---|
| 1, 2, 3 | `python lines/boundaries.py` | `lines/boundaries_results.json`, `boundaries.md` |
| 4 | `python lines/copy_geometry.py` | `lines/copy_geometry_results.json`, `copy_geometry.md` |
| 5 | `python lines/wrapping.py` | `lines/wrapping_results.json`, `wrapping.md` |
| 6 | `python lines/edges.py` | `lines/edges_results.json`, `edges.md` |
| 7 (list, squeezed last word) | `python lines/listcipher.py` (needs `data/corpora/bible_lat.txt`) | `lines/listcipher_results.json`, `listcipher.md` |
| 7 (m words) | `python lines/lineend.py` | `lines/lineend_results.json`, `lineend.md` |
| 7 (labels) | `python lines/labels.py` | `lines/labels_results.json`, `labels.md` |

Loader shared by all of them: `lines/common.py` (`pages()`, `controls()`, `units()`).

## What this adds

- The line is the unit inside which the word-making process has memory: the inter-word coupling (the strongest
  word-to-word regularity in the text, and the one the round-8 cipher was built to explain) is confined to the line
  and restarts at every line; the line has a shaped start (two words) and end (two words).
- The copying of nearby words is a same-line matter, not copying from the line above as the self-citation
  generator does it.
- The boundary rule is one rule with an A/B modification, like everything else in the system.

- (second session) The first word's extra length is no more than wrapping would give, but it is not an overflow
  word: its length is unrelated to the space left on the line above (r -0.01; wrapping 0.09-0.38). The last word is
  built to the space left, in a vocabulary of its own, with endings (-am, -om, -y) that A and B share; the A/B
  ending convention weakens by 40% there.

- (11 Nov) Lines are filled to a margin and are not list items; no rate of cutting the overflow word gives both
  Voynich's missing overflow signal and its last-word length; the line-final m words are a line-end form used at a
  fixed rate, not padding; labels follow the word recipe without the line effects and without the length budget.

Any mechanism offered for Voynichese now has to work line by line: a state carried from word to word within the
line and dropped at the line end, with a start and an end convention. Ciphers of running text do not do this
unless the plaintext is itemised one line at a time.
