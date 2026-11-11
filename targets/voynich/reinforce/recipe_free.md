# Without the word recipe (11 Nov 2026)

Script `recipe_free.py` (protocol in its docstring). Reproduce: `python reinforce/recipe_free.py` from `targets/voynich`.

## A. Word length against unit chains

| text | mean units | sd | chain 1 sd | chain 2 sd | chain 3 sd | variance ratio vs chain 1 | 2 | 3 |
|---|---|---|---|---|---|---|---|---|
| voynich | 4.46 | 1.65 | 2.96 | 1.97 | 1.74 | 0.31 | 0.70 | 0.90 |
| naibbe | 4.79 | 1.52 | 3.19 | 1.93 | 1.63 | 0.23 | 0.62 | 0.87 |
| latin | 5.77 | 2.21 | 5.10 | 3.83 | 2.81 | 0.19 | 0.33 | 0.62 |

## B. Switched convention on recipe-free values (levels lang, hand, section, quire, page)

| value | sd | pi | s |
|---|---|---|---|
| first unit | 0.37, 0.18, 0.23, 0.14, 0.32 | 0.08, 0.02, 0.02, 0.02, 0.10 | 1.31, 1.40, 1.64, 1.04, 0.98 |
| last unit | 0.16, 0.14, 0.15, 0.13, 0.24 | 0.19, 0.02, 0.03, 0.02, 0.04 | 0.37, 1.04, 0.91, 0.87, 1.24 |
| whole word | 1.08, 0.33, 0.42, 0.09, 0.55 | 0.09, 0.05, 0.05, 0.00, 0.10 | 3.49, 1.50, 1.87, 3.75, 1.78 |

## C. Next-unit models, bits per unit on held-out pages

| context | units | book | tilt | lang | lang - tilt [95%] |
|---|---|---|---|---|---|
| order 1, pseudocount 1 | 190262 | 2.2462 | 2.2320 | 2.1972 | -0.0348 [-0.0428, -0.0279] |
| order 1, pseudocount 10 | 190262 | 2.2462 | 2.2320 | 2.1916 | -0.0404 [-0.0500, -0.0333] |
| order 1, pseudocount 100 | 190262 | 2.2462 | 2.2320 | 2.1876 | -0.0443 [-0.0518, -0.0366] |
| order 2, pseudocount 1 | 190262 | 2.0838 | 2.0726 | 2.0843 | +0.0117 [+0.0040, +0.0197] |
| order 2, pseudocount 10 | 190262 | 2.0838 | 2.0726 | 2.0566 | -0.0160 [-0.0224, -0.0101] |
| order 2, pseudocount 100 | 190262 | 2.0838 | 2.0726 | 2.0434 | -0.0292 [-0.0341, -0.0246] |

Runtime 142 s.
