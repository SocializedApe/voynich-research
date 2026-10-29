# Glyph-level study: transcription, twin glyphs, allographs (28 Oct 2026)

Question: are Voynich glyphs badly transcribed or badly split, and do any glyph pairs behave like one letter
written two ways (scribal variants, positional allographs, cipher homophones)? Paragraph text of ZL3b unless noted.

## 1. Transcriber disagreement (`disagree.py`)

ZL3b, IT2a (Takahashi) and RF1b-er, line by line (3,900-4,000 common lines per pair; 41-48% of lines identical).
Glyph identity: 0.7-1.1% of glyphs disagree. The disagreements are one-stroke pairs: a/o (3.6-6.3% of a), r/s
(2.6-3.3%), k/t (1.8-3.0%), f/p (6-10%), e/h, c/e, and stroke counts (i vs ii, e vs ee). Word spaces disagree more
than glyphs: 1,300-1,500 space disagreements per pair. Example checked on the scan (f76r.5, Beinecke IIIF):
ZL `or or or`, IT `orar or`, RF `or ar or`; the image shows `or ar or` (the middle a has its tail stroke).

## 2. Twin glyphs (`variants.py`, `baseline.py`)

Context distance = mean JSD of the left and right neighbour distributions (0 = interchangeable).

| Pair | Voynich | Note |
|---|---|---|
| ch/sh | 0.028 | |
| f/p | 0.028 | f/p sit 78-81% in paragraph-first lines (18% of lines) |
| k/t | 0.029 | |
| cth/ckh | 0.062 | |
| a/o | 0.448 | |
| r/s | 0.267 | |

Baselines, closest pair of different letters: Latin a/o 0.065, Italian a/e 0.044, German b/g 0.110; Latin with
random homophones e1/e2 0.001. The twins are closer than any two letters of Latin or German and far from free
homophones.

## 3. What decides the choice (`choice.py`)

- k/t and ch/sh: hand explains 0-1% of the choice's entropy, line position about 1%, neighbours 2-3%; the context
  distance stays 0.025-0.042 inside each of hands 1, 2, 3, 5. Not scribal habit, not position: two distinct signs
  of one class.
- cth/ckh: partly scribal (cth 64% in hand 1, 36-37% in hands 2-3).
- a/o: neighbours predict the choice 88.5% (base 63.5%): o before k, t, d, p and at word end (95-100%), a before i
  (96%); both before l and r. Transcribers disagree on a/o 2-4 times more before l/r/m (1.7-4.0%) than before k/t/p
  (0.1-1.3%), but agree 96% or more even there: the al/ol, ar/or contrast is mostly legible.
- r/s: neighbours predict 88.4% (base 74.4%): r after a, o, i (87-98%), s after e, ch, sh, l (83-96%) and
  word-initially (71%). EVA r has the shape of the medieval r rotunda; the medieval rule (r rotunda after o, straight
  r word-initially and after c-shaped letters, straight r after minims) matches three of four contexts, not the
  minim one.

## 4. Positions in the word

q 99.4% initial (98% followed by o); n 98.8% final, m 96%, y 87%, g 84%, r 77%; i 99.8% and e 99% medial; sh 72%
and cth 53% initial.

## 5. Word spaces are fixed by the glyphs (`spaces.py`)

Every gap between adjacent units is a break or not; information the neighbouring units carry about it (share of the
break's entropy), and held-out accuracy of a majority rule per (before, after) pair:

| Text | before | after | both | accuracy (base) |
|---|---|---|---|---|
| **Voynich ZL** | **66%** | **31%** | **74%** | 94.7% (80.4%) |
| **Naibbe cipher of Latin** (a token = one cipher unit) | **65%** | **32%** | **81%** | 96.2% (81.3%) |
| verbose cipher keeping the plaintext word spaces | 31% | 28% | 34% | 94.9% (94.9%) |
| Latin / Italian 1500-1600 / German 1470-1610 | 15-21% | 8-17% | 34-46% | 87-89% (79-84%) |

Generator controls (a4_selfcitation generators poured into the ZL skeleton; same measure, "both"):
Voynich words shuffled across the whole text 76%; Rugg grille 70%, Rugg sorted 78%; autocopist (Timm & Schinner)
seeds 19 and 7 53% and 47%. Gaskell & Bowern gibberish not on this machine, not run.

Reading: the measure reflects word-internal structure only (shuffling words keeps it at 76%). It separates text whose
spaces are plaintext word spaces (languages, a cipher that keeps them: 34-46%) from text built of fixed-template
units (Naibbe, Rugg, Voynich: 70-81%), but not a cipher from a table generator. The self-citation generator falls
below Voynich (47-53%): its free edits loosen the start/end glyph classes. Transcribers (ZL vs RF, same glyphs)
disagree on spaces mostly after l (4.0%) and r (3.4%), the units that are final or internal; elsewhere 0-1.7%.

## 6. f66r single-glyph column against the f57v ring

Column read on the Beinecke scan (IIIF 1006192), 34 signs, one per text line, agreeing with ZL f66r.16-49:
`y o s sh y d o f @169 x air d sh y f f y o d s f c @172 x t o @195 l r t o x p d`. Ring (ZL f57v.3, second ring,
x4): `o l d r v x k m f/p @169 t r @170 @171 y c/I @172`. @169 and @172 occur nowhere else in the book; ZL already
annotates f66r.37-38 "cf f57v seq.". Ink of the column paler than the text, same letter forms.

Test: ring distance between consecutive column signs that occur in the ring (22 pairs), against 100,000 shuffles of
the column: steps of +1 2 (P 0.24), +-1 3 (P 0.29), +1 or +2 4 (P 0.18). The column is not a walk through the ring.
What links them is two pairs: both ring-only signs come with their ring predecessor (f @169, c @172), both followed
by x (in the ring: t and o). Rough chance of both predecessors 1 in 200, found after ZL's pointer, so post hoc.
Reading: the column borrows two compound signs from the ring; no evidence that the ring is a key to the text
(the ring also lacks e a i ch sh q n s, the commonest glyphs).

## 7. Failed method (not used)

`finals.py` (is a word-final glyph the end form of an internal glyph, by left context): on Latin it does not pair
final s with internal s (best b 0.191, itself 0.356); left contexts at word end differ from mid-word in any
language. Its Voynich output is not interpreted.

## Reading

Transcription error is small for glyph identity and larger for word division, and word division is itself mostly
fixed by the glyphs (section 5): a Voynich word is a template unit, not a plaintext word with a real space (this
does not separate a cipher from a table generator). Of the stroke pairs, k/t and ch/sh
are separate signs (not handwriting noise, not scribe-dependent), a/o and r/s are largely positional with residual
contrast, cth/ckh is partly a scribal habit, f/p is a paragraph-first-line form. For a simple-cipher model this
gives candidate merges (a/o outside l/r contexts, r/s, f/p with k/t in first lines) but none of them turns the
glyph stream into a one-glyph-per-letter cipher; the units question (inventory.py, NOTES 4.1) stands.
