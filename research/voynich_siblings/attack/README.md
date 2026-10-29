# Blind attack on a Naibbe-type table cipher, and a first run on Voynich (28 Oct 2026)

## The attack

- `attack_v0.py`: homophonic annealer (symbol -> letter), objective = order-5 no-space Latin model minus a
  letter-frequency (KL) term, frequency-matched start. With the token split given (oracle), a synthetic Naibbe
  ciphertext of Latin (Greshko's tables, 15,000 tokens, 380 symbols) is recovered at **99.3%** per letter
  (Caesar, *De bello Gallico* I.1). Without the KL term the solver collapses to "iiii..." (Roman numerals in the
  Gutenberg Latin corpus).
- `attack_v1.py`: unsupervised segmentation of tokens into one part or head + tail: EM over all readings with a
  sparse prior, then a post-pass that splits rare whole readings into well-attested head + tail. Split accuracy 48.6%
  (Viterbi from all-whole, stuck) -> 86.6% (EM) -> **93.2%** (EM + post-pass); 445 symbols against 380 true.
- `attack_v2.py`: whole-token symbols may decrypt to one or two letters. With v1's segmentation, a run with seed 7
  recovers readable Latin blind ("commentarius primus gallia est omnis diuis.. partes ..earum unam incolunt belgae
  aliam aquitani tertiam qui ipsorum lin..a celt. nostra galli appellantur").

## First run on Voynich (`run_voynich.py`, decision rule committed before the run)

Six runs, 20,000 tokens each; per-character score of the decryption under the language model.

| Run | symbols | per char |
|---|---|---|
| synthetic Naibbe (Latin), real order | 447 | -2.608 |
| synthetic, shuffled within lines | 447 | -2.693 |
| Voynich, Latin, real order | 1,546 | -2.700 |
| Voynich, Latin, shuffled | 1,546 | -2.717 |
| Voynich, Italian (cinquecento), real order | 1,546 | -2.750 |
| Voynich, Italian, shuffled | 1,546 | -2.776 |

Gaps (real minus shuffled): synthetic 0.085; Voynich Latin 0.017 (0.19 of synthetic); Voynich Italian 0.026 (0.30).
By the rule: Latin **no signal**, Italian **weak / undecided**.

**But the positive control was not solved in this run.** With seed 211 the synthetic ciphertext stayed at -2.61 per
character (its first 250 letters are pseudo-Latin, not Caesar), while the seed-7 run of attack_v2 solved it. The
solver succeeds only on some seeds, so the yardstick (gap_synth = 0.085) is the gap of an unsolved cipher and the
verdicts above are weak. Sample outputs (first letters):

- synthetic, unsolved: `oritariarasiarianantueuarersuitastuitensialiueranitasedbenenesaniseruentem...`
- Voynich, Latin: `qdeinosperminetecatiiinonetinaririmexiiutelirarececeatellaiitecoitireticeptires...`
- Voynich, Italian: `xsetroomaleletaradiielacitirasisidiciittolasemirareilaghiiiuiraenisimimiluimaod...`

Also: Voynich segments into 1,546 symbols against 445 for the synthetic cipher at the same length, so either its
inventory of glyph groups is much larger than Naibbe's or the head/tail model fits it poorly.

## Status and next step*

Inconclusive. What is established: a Naibbe-type cipher of Latin can be broken blind by this pipeline when the
annealer converges. What is needed before a Voynich verdict means anything: a solver that converges reliably
(target: >= 8 of 10 seeds solve the synthetic cipher), with stronger moves (swaps, tempering, more restarts) and the
same pipeline run on synthetic ciphers with Voynich-sized inventories (about 1,500 symbols); then the six runs again.

## Proper run: solver validation first (`validate.py`, 2 jobs at a time on 2 cores)

Single runs, 200,000 iterations, swap moves, randomised starts, 15,000 synthetic tokens; success = similarity of the
first 3,000 decrypted letters to the plaintext >= 0.80.

| Cipher | symbols | runs solved | scores |
|---|---|---|---|
| Naibbe, Greshko's tables | 445 | **2 / 4** (0.93, 0.93) | solved -61.5k; failed -84k to -86k |
| Naibbe with three scribal variants per table entry ("expanded") | 1,218 | **0 / 4** (0.07-0.13) | -85k to -88k |
| expanded, variants merged before solving (`--canon`) | 555 | **0 / 2** (0.08) | -88k to -90k |

The objective separates solved from failed runs cleanly, so best-of-4 on the standard cipher succeeds about 94% of the
time. But the solver does not crack a cipher with a Voynich-sized inventory even when the answer is known, and
merging scribal variants (ee/e, sh/ch, t/k, a/o, qo-/o-, -y) does not rescue it: on the standard cipher the merge
fuses true symbols (445 -> 249), on the expanded one it leaves 555 symbols and still fails.

Symbol inventories under the same segmentation, 20,000 tokens:

| Text | symbols | after merging scribal variants |
|---|---|---|
| Naibbe synthetic | 445 | 249 |
| expanded synthetic | 1,218 | 555 |
| **Voynich** | **1,546** | **1,054** |

## Conclusion of the bounded attempt*

No Voynich verdict is drawn: by the plan fixed in advance, a Voynich run is only meaningful once the solver cracks a
synthetic cipher of Voynich's size, and it does not. What the attempt does establish:

1. A Naibbe-type table cipher of Latin (about 450 symbols) is breakable blind with this pipeline (best-of-4).
2. Under the same head + tail segmentation, Voynichese has 3.5 times the symbols of a Naibbe ciphertext of equal
   length, and still over 1,000 after merging the classic scribal alternations: about 20 occurrences per symbol in
   20,000 tokens. Either its encoding units are not head/tail groups of a small table cipher (a mismatch with the
   Naibbe family as a whole), or its key is far larger than any table cipher of that family; in both cases a blind
   homophonic attack of this kind is under-determined on the available text.
3. The earlier six-run comparison (Voynich Latin gap 0.017, Italian 0.026) stays uninterpretable.

## Where the 1,546 symbols come from (`inventory.py`, 28 Oct 2026)

Same 20,000 tokens and synthetic Naibbe text as above.

1. **Mostly unsplit rare words.** Of Voynich's 1,546 symbols, 731 are whole-word readings (Naibbe: 132), 570 of them
   seen once, long words such as `chckhyoltchedy`, `oksheyqolkeey` that hold more than two pieces. Heads 419 and tails
   396 (Naibbe 185 and 130).
2. **Coverage by a Naibbe-sized inventory** (the K pieces used most, share of tokens spelled by at most n of them):

   | K = 450 | <= 1 | <= 2 | <= 3 | <= 4 |
   |---|---|---|---|---|
   | Naibbe | 52.9% | 100.0% | 100.0% | 100.0% |
   | Voynich | 59.4% | 95.1% | 99.1% | 99.8% |

   Voynich is spelled by 450 pieces nearly as well as Naibbe once about 4% of words may take a third piece.
3. **Pieces float between positions.** Parsed with those 450 pieces (fewest pieces, then most frequent), the
   role-tagged stream still has 1,304 symbols (Naibbe 535): 95.4% of Voynich piece uses belong to strings that also
   occur in another position (whole / head / middle / tail; Naibbe 46.0%), e.g. `ol` S 411, U 351, P 243; `y` S 567,
   P 209, U 165. With roles merged: **625 symbols** (448 pieces + 177 unparsed rare words), Naibbe 393.
4. A free multi-piece segmenter (Viterbi-EM unigram, `--part2`) failed its calibration on Naibbe (900-2,800 units
   against ~390 true, most words left whole); its numbers are not used.

Revised reading of the earlier conclusion (point 2): the inventory is not 3.5 times Naibbe's. The excess comes from
the head + tail model, which cannot cut words of three or more pieces and gives each position its own symbol, while
Voynich pieces move freely between positions. Under a role-free parse of 1-3 pieces Voynich needs about 625 symbols,
1.6 times the synthetic cipher: near the size the solver cracks, not beyond it. This weakens the "too big for any
table cipher" reading. Whether role-free pieces fit a Naibbe-type cipher is open: in Naibbe the same string in head
and tail position can stand for different letters, so merging roles is a modelling choice, not neutral.

Next step (not run): validate the solver on a role-merged parse of the synthetic cipher first, as the earlier plan
requires, then the Voynich runs (real order vs shuffled) on the 625-symbol stream.

## Role-merged run (`run_merged.py`, rule fixed in its docstring before any solver run)

Parse: 450 pieces, 1-3 per word, one symbol per piece wherever it stands. Validation, 20,000 tokens, 200,000
iterations, success = similarity >= 0.80:

| Synthetic | symbols | solved | similarities |
|---|---|---|---|
| Naibbe (Greshko's tables) | 393 | **0 / 4** | 0.08, 0.17, 0.34, 0.11 |
| forms3 (yardstick, within 10% of Voynich's 625) | 587 | **0 / 3** (fourth seed stopped: cannot reach 2 / 4) | 0.10, 0.06, 0.14 |
| expanded | ~1,100 | not run (stopped) | |

**Validation failed; by the rule no Voynich run is made or interpreted.** The same solver solves the standard cipher
in 2 of 4 seeds under the role-tagged head + tail parse, so the role merge itself breaks it: in Naibbe the same
string as head and as tail can stand for different letters, and one value per string cannot express that. The
625-symbol count of `inventory.py` point 3 is therefore not a solvable stream for this family; what remains true is
that the excess over Naibbe comes from three-piece words and position-floating pieces, not from a huge table.
