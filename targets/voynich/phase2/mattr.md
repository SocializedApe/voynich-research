# MATTR of Voynich against 50 languages (12 Nov 2026)

Script `mattr.py` (definition in its docstring). Reproduce: `python phase2/corpora2.py`, `python phase2/mattr.py` from `targets/voynich`.

| text | MATTR 50 | MATTR 200 | MATTR 500 | MATTR 2000 |
|---|---|---|---|---|
| Voynich (all) | 0.860 | 0.709 | 0.595 | 0.431 |
| Voynich A | 0.867 | 0.723 | 0.613 | 0.447 |
| Voynich B | 0.863 | 0.705 | 0.584 | 0.411 |
| Naibbe cipher of Pliny | 0.913 | 0.760 | 0.636 | 0.469 |
| Rugg table text | 0.895 | 0.757 | 0.552 | 0.331 |
| autocopist | 0.885 | 0.775 | 0.713 | 0.620 |
| Latin | 0.844 | 0.689 | 0.584 | 0.435 |
| Italian | 0.791 | 0.580 | 0.451 | 0.299 |
| German | 0.773 | 0.567 | 0.437 | 0.281 |
| English | 0.682 | 0.465 | 0.345 | 0.212 |
| Hebrew | 0.820 | 0.663 | 0.566 | 0.434 |
| Turkish | 0.880 | 0.741 | 0.643 | 0.501 |
| Finnish | 0.808 | 0.649 | 0.549 | 0.416 |
| Vietnamese-tok | 0.792 | 0.547 | 0.397 | 0.228 |
| Chinese-tok | 0.760 | 0.579 | 0.476 | 0.351 |

| window | languages: min / median / max | Voynich (all): rank from the lowest of 51 | five nearest languages |
|---|---|---|---|
| 50 | 0.516 / 0.773 / 0.880 | 45 | Quichua-NT 0.862, Syriac-NT 0.866, Xhosa 0.868, Shona 0.848, Amharic 0.873 |
| 200 | 0.284 / 0.579 / 0.749 | 45 | Basque-NT 0.703, Shona 0.703, Arabic 0.698, Quichua-NT 0.721, Coptic-NT 0.692 |
| 500 | 0.187 / 0.451 / 0.661 | 41 | Arabic 0.601, Coptic-NT 0.604, Shona 0.606, Latin 0.584, Basque-NT 0.609 |
| 2000 | 0.092 / 0.311 / 0.533 | 39 | Hebrew 0.434, Latin 0.435, Swahili-NT 0.424, Lithuanian 0.416, Finnish 0.416 |
