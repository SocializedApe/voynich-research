# Full re-run on the fixed parse (28 Oct 2026)

Every analysis script (baseline, baseline2, a1-a6, b1-b4, c1, c3) run twice in scratch copies of `targets/voynich`
with all comparison corpora re-fetched by `fetch_corpora.py`:

- **September copy**: the committed TSVs. Reproduces every Voynich number in `results/*.json` within 0.1%
  (`d2_compare_runs.py results <copy>/results`). The only differences elsewhere are runtimes and the English and
  Icelandic Gutenberg texts, which Gutenberg has updated since September. The Italian control was rebuilt exactly:
  the eight Nuntiaturberichte volumes from archive.org, `targets/vatican5/build_it_lm.py`, and `freeze_italian`
  found the September anchor at offset 0.
- **Fixed copy** (these files): `ZL3b-n` and the other transliterations parsed with `parse_ivtff.py --fixed`
  (`<->` as a word break, `{..}` ligature glyphs kept). b3 needed one change: the fixed text (34,834 tokens) is
  longer than the shipped Naibbe ciphertext (34,764), so the shipped lines are now cycled to length (the change is
  in `b3_bakeoff.py`; no effect when the text is long enough).

`diff_fixed_vs_september.txt` lists every number that moves by more than 2%. Summary of what changes in the
conclusions (none flips):

| Item | September parse | Fixed parse |
|---|---|---|
| tokens / types (ZL, P text) | 34,116 / 7,236 | 34,834 / 7,021 |
| hapax share of types | 0.697 | 0.680 |
| Currier A tokens / types | 10,715 / 3,339 | 11,217 / 3,213 |
| b3 matches (of 37): Naibbe Pliny / lines / Divina Commedia | 17 / 17 / 17 | **22 / 23 / 21** |
| b3 matches: autocopist s19 / s7 | 9 / 9 | 12 / 15 |
| b3 matches: Rugg grille / sorted | 8 / 14 | 12 / 17 |
| b3 matches: Voynich A against the whole text | 27 | 31 |
| b3 items failed by every non-Voynich corpus | len sd, len=1, adj exact, adj LD<=1, sc <=10, sc prev2, MZ peak R, tok pred, ... | len=1, adj exact, adj LD<=1, sc <=10, MZ peak R, JSD halves |
| a6 unsupervised A/B recovery, merged bigrams (Ward) / words (k-means) | 99.5% / 98.0% | **100%** / 99.0% |
| b2 long-range peak (bits/token, scale) | 0.268 at 400 | 0.273 at 400 |
| b2 adjacent folio pairs more similar than random | 80% | 79% |

Reading: the fixed parse makes Voynichese look more like the Naibbe cipher on word length, Zipf and vocabulary items
(the glued false compounds had inflated length spread and types) and sharpens the Currier A/B split. The items no
generator or cipher reproduces are now the copying signatures (adjacent identical and edit-distance-1 pairs,
near-copies within 10 tokens), the long-range peak height and the drift between manuscript halves.
