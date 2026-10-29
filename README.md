# Voynich research

Statistical tests of what the Voynich manuscript (Beinecke MS 408) could be: ciphers, codes, languages and generators,
each against controls and calibrated solvers. Not a decipherment.

**Start here: [`targets/voynich/README.md`](targets/voynich/README.md)** (the main results and the author's notes).
The full chain of tests is in `targets/voynich/HYPOTHESES_2026-10-28.md`.

## Layout

- `targets/voynich/`: the Voynich work (scripts, results, logs, per-programme READMEs, ZL transliteration in `data/`)
- `research/voynich_siblings/`: cipher models and the copying-scribe model the scripts import
- `lang/`: the n-gram language-model code some scripts import

Paths follow the original repository, so scripts are run from this folder, e.g.
`python targets/voynich/meaning/homclass.py <naibbe_tables.csv>`.

## Not included

- Language corpora (`lang/corpora/*.txt`, e.g. `la-gutenberg.txt`, `it-gutenberg.txt`): public-domain Project
  Gutenberg / Wikisource texts, re-downloadable; see `lang/README.md` and `targets/voynich/fetch_corpora.py`.
- Greshko's Naibbe tables: `references/naibbe_tables.csv` from github.com/greshko/naibbe-cipher.
- Bulky regenerable data (language-model tables, transformer checkpoints): archived separately.

Python 3 with numpy, scipy, scikit-learn, rapidfuzz (and torch for `tfm/`).
