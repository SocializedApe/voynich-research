# Slot-HMM: is there a hidden letter stream behind the slots? Results, 28 Oct 2026

Scripts: `slot_hmm.py` (model, controls), `slot_hmm2.py` (line-position and edge controls, three seeds). Raw output:
`slot_hmm_run1.txt`, `slot_hmm_run2.txt`. Data: ZL3b fixed parse, paragraph lines (4,103 lines, 34,807 tokens).

## Model

Each token parsed by regex into prefix (9 values) + gallows core (51) + middle (1,412, top 40 kept) + ending (28).
A hidden state z per token emits the four slots independently. Mixture: z independent per token. HMM: z depends on
the previous token's z, lines as sequences. Held-out = every 5th line. Gain = held-out bits/token, mixture minus HMM:
what the order of the hidden states adds. If Voynichese were a slot cipher of a letter stream, the states would be
letters and the gain would be the letter bigram's.

## Results, K = 24

| Text | gain (bits/token) | I(z; z-1) | letter recovery (purity / NMI) |
|---|---|---|---|
| slot cipher of Latin, 1 letter per word (positive control) | 0.470 | 0.68 | 0.99 / 0.98 |
| same, 1-2 letter units (Naibbe-like respacing) | 0.045 | 0.24 | 0.49 / 0.75 |
| Voynich shuffled over the whole text | 0.000 | 0.05 | |
| Voynich (seeds 11-13, and run 1) | 0.146-0.191, mean 0.170 | 0.54-0.59 | |
| Voynich, tokens shuffled inside lines, first and last kept | 0.077-0.122, mean 0.102 | 0.42-0.52 | |
| Voynich, prefix blanked / same, interior shuffle | 0.120 / 0.078 | | |
| Voynich, ending only / same, interior shuffle | 0.096 / 0.067 | | |
| Currier A / B (run 1, one seed) | 0.068 / 0.164 | 0.68 / 0.52 | |
| Latin letters, for scale | | I(x; x-1) 0.54 | |

## Reading*

1. The headline match (Voynich states 0.54 bits on the previous state, Latin letters 0.54) is mostly not word order.
   About 60% of the HMM gain survives shuffling tokens inside lines with the first and last token kept: it is line
   position and page/section vocabulary, not sequence.
2. The order-specific part is 0.06 bits/token (0.04 with the prefix blanked, so edge coupling into openers is only part
   of it), about one eighth of a one-letter-per-word slot cipher (0.47) and the size of the Naibbe-like 1-2 letter
   control (0.045).
3. The positive control shows the model would have found a one-letter-per-word slot cipher (99% of tokens mapped to
   the right letter). Voynich is not that. A cipher of 1-2 letter units remains compatible, but on that control even the
   known-plaintext recovery is 49%, so a Viterbi decode of Voynich into 24 symbols plus a substitution solver would
   not be informative. Not run.
4. Small new item: an ending predicts the next word's ending after the interior-shuffle null (0.029 bits/token, ending
   slot alone), separate from the end -> next-opening edge coupling (`code_vs_generator.md`).

Limits: one hand-written slot parser (middle slot catches gallows after e, e.g. `sheckhy` -> sh + eckh + y); EM local
optima (gain spread 0.15-0.19 across seeds); K = 24 only for the controls; no Naibbe tables on this machine, so the
Naibbe-like control is a stand-in built with this model's own assumption.
