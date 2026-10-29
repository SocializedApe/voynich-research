# Small neural models on Voynich and controls (28 Oct 2026)

Status: in progress. Question: does Voynich use context like a language (loss keeps falling as the model sees more
of the preceding text), like a generator, or like a cipher that hides context? And what does a trained model's
internal state encode?

## Files

| File | What |
|---|---|
| `texts.py` | builds `data/<name>.txt`: 180,000 characters each, lines broken as in Voynich: voynich, voynich_shufline, voynich_shufpage, latin, italian, naibbe, rugg, autocopist |
| `train.py` | one GPT-style character model per text (window 256; 20 blocks, 4 and 14 validation, 9 and 19 test); loss by position in the window = loss against context length; GPU when available |
| `ngram.py` | 2-, 3-, 5-gram baselines on the same test blocks (`results/ngram.json`): the bar a model must clear |
| `summarize.py` | table of context curves, mean over seeds, models above their 5-gram flagged UNDERTRAINED |
| `probe.py` | linear probes (Currier language, hand, section, paragraph-first line; grouped by folio) on trained vs untrained states; attention look-back and previous-line share per head |
| `calib.py` | CPU calibration on Latin (LSTM vs transformer) |
| `colab_run.ipynb` | the GPU run: calibration, 8 texts x 3 seeds, summary, probes, download |

## CPU results so far

5-gram bits/char on the test blocks: voynich 1.526, voynich_shufline 1.606, voynich_shufpage 1.642, latin 2.031,
italian 1.814, naibbe 1.613, rugg 1.416, autocopist 2.277. Shuffling Voynich words within lines costs the 5-gram
0.08 bits/char, within pages 0.12: word order carries local information across word boundaries.

No usable neural result on the CPU (shared with other work). First runs (lr 1e-3, dropout 0.2) stayed at bigram
level on Latin (3.45 vs 5-gram 2.03) and were discarded. Calibration on Latin: an LSTM (384 units, no dropout)
memorises the training text (train 0.40, held-out 3.85); the transformer with lr 3e-3, dropout 0.1, batch 16 reaches
2.49 after 4,000 steps, loss now falling with context, still above the 5-gram. A copy-task check failed in 300 steps
for this model and for PyTorch's own reference transformer alike, so it shows slow learning, not a bug.

Probe smoke test (100-step model, one position in 30): an untrained model's states already separate Currier A/B
(0.84), hand (0.65-0.74) and section (0.54-0.69) from glyph statistics alone, so a probe means something only as the
gain of the trained model over the untrained one.

## GPU run

Upload `voynich_tfm.zip` (scripts, the 8 texts, ngram.json, ZL TSV) to Colab with `colab_run.ipynb`, T4 runtime.
Settings in the notebook: 8,000 steps, lr 3e-3, dropout 0.1, batch 64, d 128, 4 layers, seeds 0-2. The calibration
cell must beat the Latin 5-gram before the main loop is worth running.

## GPU run 1 (Kaggle, 2 x T4, 28 Oct 2026; `run_kaggle.py`, results and logs in `kaggle_run1/`)

Settings: 8,000 steps max, lr 3e-3, dropout 0.1, batch 64, d 128, 4 layers (0.83M parameters), seeds 0-2, 64 minutes.
Calibration: Latin 2.536 bits/char against its 5-gram 2.031, UNDERTRAINED by the rule. Diagnosis from the logs: the
models overfit, they are not undertrained. Latin train loss falls to 1.88 while validation rises from 2.49 to 2.62;
early stopping ends every run at about 1,000-1,400 steps. Only Rugg and the autocopist beat their 5-grams.

| text | 5-gram | model mean | ctx0 | ctx 8-15 | ctx 32-63 | ctx 128-255 | long gain (32-63 -> 128-255) |
|---|---|---|---|---|---|---|---|
| voynich | 1.526 | 1.610 | 2.071 | 1.664 | 1.620 | 1.592 | 0.028 [0.022-0.037] |
| voynich_shufline | 1.606 | 1.705 | 2.106 | 1.782 | 1.715 | 1.688 | 0.027 [0.021-0.030] |
| voynich_shufpage | 1.642 | 1.751 | 2.140 | 1.780 | 1.760 | 1.739 | 0.020 [0.015-0.024] |
| latin | 2.031 | 2.518 | 3.485 | 2.519 | 2.505 | 2.514 | -0.009 |
| italian | 1.814 | 2.294 | 3.330 | 2.249 | 2.281 | 2.289 | -0.008 |
| naibbe | 1.613 | 1.763 | 2.268 | 1.749 | 1.763 | 1.755 | 0.008 |
| rugg | 1.416 | 1.103 | 2.635 | 1.156 | 1.072 | 1.081 | -0.008 |
| autocopist | 2.277 | 2.168 | 2.920 | 2.416 | 2.234 | 2.098 | 0.136 |

Not interpreted as a context comparison: the language controls fail their 5-grams, so their flat curves show the
overfitting, not the languages. Probes on voynich_s0 (trained / untrained, best layer): Currier language 0.969 / 0.897,
hand 0.808 / 0.743, section 0.753 / 0.704, paragraph-first line 0.903 / 0.813 (majority 0.813): the trained model
tracks dialect, scribe, section and the first line of a paragraph beyond glyph statistics. Attention: heads attending
to the previous line (share 0.40-0.48) appear in Voynich, both shuffled Voynich texts, Naibbe and the autocopist, so
the measure reflects local glyph statistics, not copying. Next: a regularisation sweep on Latin (`voynich-tfm-calib`).
