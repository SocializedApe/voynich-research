# The main results on three transliterations (11 Nov 2026)

Script `translit.py` (protocol in its docstring). Reproduce: `python lines/translit.py` from `targets/voynich`.

| measure | ZL (Zandbergen-Landini) | IT (Takahashi) | RF (reference) |
|---|---|---|---|
| pages | 207 | 206 | 207 |
| tokens | 34834 | 33641 | 33866 |
| first word - interior (chars) | +0.48 | +0.29 | +0.40 |
| last word - interior | -0.31 | -0.53 | -0.36 |
| early breaks | 0.36 | 0.34 | 0.33 |
| r(slack, next first word) | -0.011 | +0.008 | +0.009 |
| 95% interval | [-0.042, +0.018] | [-0.032, +0.045] | [-0.022, +0.039] |
| edge coupling within line | 0.0597 | 0.0566 | 0.0583 |
| edge coupling across line break | 0.0010 | 0.0001 | 0.0015 |
| r opener, middle lengths within context | -0.225 | -0.207 | -0.212 |
| r stem, ending lengths within context | -0.182 | -0.184 | -0.169 |
| variance ratio of slot lengths | 0.702 | 0.682 | 0.710 |
| variance ratio vs order-2 unit chain | 0.70 | 0.69 | 0.72 |
| JSD A vs B (glyph bigrams) | 0.101 | 0.102 | 0.102 |
| share of endings switched by language | 0.05 | 0.05 | 0.05 |
| size of a switch (log) | 3.78 | 3.81 | 3.76 |
| per-language unit chain - tilt (bits/unit) | -0.0404 | -0.0399 | -0.0389 |
| 95% interval | [-0.0483, -0.0329] | [-0.0482, -0.0325] | [-0.0463, -0.0323] |

Runtime 134 s.
