# Code, fragment cipher or generator? Results, 28 Oct 2026

Scripts: `code_vs_generator.py` (Voynich, autocopist, Naibbe, Latin, Italian and slot-built codes of both),
`cross_boundary.py` (the edge coupling by separator type, from the raw ZL file).

## Question and why it matters for decryption

If Voynichese is a cipher of a real language, which kind? A letter-fragment cipher (Naibbe: each token hides one or
two plaintext letters) or a code (each token stands for a whole plaintext word, codewords built from slots, as in a
nomenclator). Or is it generated text with nothing to recover (self-citation)? The b3 bake-off already showed that
Naibbe lacks Voynich's page locality, long-range clustering and hapax-rich vocabulary (Naibbe MZ peak 0.003 against
0.287; types on one page 37-41% against 70%; near-copy excess 0.96-0.98 against 1.13).

## Results (`code_vs_generator.py`, fixed parse, all texts in the ZL line skeleton)

| Text | word-to-word dependence | end -> next start | start/end in word | adjacent identical % | long range (D256) | hapax % |
|---|---|---|---|---|---|---|
| Voynich | 0.017 | **0.055** | 0.039 | 0.94 | 0.29 | 68 |
| Autocopist s19 / s7 | 0.009 / 0.006 | 0.003 / 0.001 | 0.04 / 0.05 | 0.15 / 0.22 | 0.48 / 0.43 | 71 / 70 |
| Naibbe (Latin) | 0.012 | 0.002 | 0.053 | 0.23 | 0.004 | 39 |
| Latin | 0.029 | 0.013 | 0.076 | 0.11 | 0.41 | 69 |
| Code of Latin (one slot-built codeword per word) | 0.026 | 0.000 | **0.112** | 0.11 | 0.41 | 62 |
| Italian | 0.057 | 0.014 | 0.126 | 0.09 | 0.17 | 59 |
| Code of Italian | 0.057 | 0.001 | 0.126 | 0.09 | 0.17 | 59 |

(A near-copy column within the line was uninformative, about 1.0 for every text, and is left out; the page-level
self-citation ratio in b3 is the right measure.)

Edge coupling by separator (`cross_boundary.py`, raw ZL, interior pairs, within-line shuffle null):

| Pairs | end -> next start (normalised) |
|---|---|
| all | 0.055 |
| certain spaces (.) only | **0.046** |
| uncertain spaces (,) only | 0.155 |
| drawing gaps (<->) only | -0.009 (none) |
| Currier A / B, certain spaces | 0.027 / 0.059 |
| words two apart | 0.000 |

## Reading*

1. A one-to-one code keeps the plaintext's word structure (long range, word-to-word dependence) but also its
   start/end dependence at token level (0.11-0.13, three times Voynich), because frequent plaintext words become
   frequent fixed codewords. Only a homophonic code (several codewords for common words) could come down to
   Voynich's 0.04.
2. No candidate reproduces the edge coupling: the last glyph of a token predicts the first glyph of the next 3.5
   times more than in Latin and 15-50 times more than in the autocopist, Naibbe or codes. It survives on certain
   spaces alone (0.046), vanishes at two words' distance, and is absent across drawing gaps, which confirms that
   `<->` is a true break (the `--fixed` parse).
3. This replicates, independently and with a different estimator, Rozanova & Temerev 2026 (arXiv 2608.17096, "A
   Glyph Is Not a Letter, a Token Is Not a Word, a Space Is Not a Space"): edge glyphs share about 0.2 bits, more than
   any prose control; neither Naibbe nor the self-citation generator reproduces it; uncertain separators behave like
   word-internal junctures (internality 0.49) and are physically narrower on the page (AUC 0.905), while certain
   separators are nearly independent junctures (internality 0.03). So the coupling is not an artefact of spaces cut
   into a continuous stream: token edges follow rules of their own. What this note adds: the code controls, the
   drawing-gap check, and Latin and Italian under the same measure.
4. Consequence for decryption: every mechanism tested so far fails at least one part of the profile (edge coupling,
   open vocabulary, page locality, start/end independence). A decipherment model has to produce all four at once.
   The open challenge (also stated in github.com/elder-plinius/V3R1T4S, voynich-generator-heldout-fingerprints.md)
   is a hand-executable cipher or generator that does. Candidate mechanisms to try next: a homophonic slot-built
   code with section-wise drift; a fragment cipher whose table choice for the next token depends on the ending of
   the current one (chained tables, an autokey-like rule); scribal word-final / word-initial agreement rules.
