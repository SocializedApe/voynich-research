# A list, or a clerk who squeezes the last word in? (11 Nov 2026)

Script `listcipher.py` (protocol in its docstring).

## A. Are lines items? Fill of a line against the length of real items

| text | n | mean fill | CV | under half | under 80% |
|---|---|---|---|---|---|
| Voynich lines (not paragraph-final), characters / longest line | 3317 | 0.89 | 0.16 | 0.030 | 0.173 |
| Voynich lines (not paragraph-final), words / most words | 3317 | 0.83 | 0.20 | 0.039 | 0.349 |
| Voynich paragraphs as items (words) | 740 | 0.45 | 0.61 | 0.705 | 0.905 |
| Latin Vulgate verses (characters) | 35921 | 0.55 | 0.43 | 0.484 | 0.850 |
| Latin Vulgate clauses (characters) | 125783 | 0.52 | 0.50 | 0.537 | 0.871 |
| Latin Vulgate clauses (words) | 125783 | 0.53 | 0.47 | 0.512 | 0.886 |

## B. Stream wrapped with the overflow word cut to fit with probability q

| text | first - int. | last - int. | early breaks | mean slack | r slack, next first | r space, last | JSD last | words cut | match |
|---|---|---|---|---|---|---|---|---|---|
| Voynich | 0.481 | -0.308 | 0.362 | 5.911 | -0.011 | 0.274 | 0.049 | - | - |
| q 0.0, J 0 | 0.521 | 0.072 | 0.000 | 2.144 | 0.362 | 0.647 | 0.002 | 0.000 | False |
| q 0.0, J 6 | 0.459 | 0.044 | 0.224 | 3.482 | 0.238 | 0.501 | 0.002 | 0.000 | False |
| q 0.0, J 12 | 0.470 | 0.044 | 0.431 | 5.358 | 0.166 | 0.370 | 0.001 | 0.000 | False |
| q 0.5, J 0 | 0.279 | -0.775 | 0.005 | 1.484 | 0.279 | 0.806 | 0.048 | 0.029 | False |
| q 0.5, J 6 | 0.278 | -0.792 | 0.206 | 3.125 | 0.180 | 0.667 | 0.046 | 0.032 | False |
| q 0.5, J 12 | 0.263 | -0.830 | 0.424 | 5.060 | 0.113 | 0.501 | 0.047 | 0.034 | False |
| q 0.8, J 0 | 0.112 | -1.299 | 0.008 | 0.940 | 0.157 | 0.849 | 0.095 | 0.046 | False |
| q 0.8, J 6 | 0.174 | -1.234 | 0.178 | 2.759 | 0.087 | 0.676 | 0.085 | 0.048 | False |
| q 0.8, J 12 | 0.140 | -1.327 | 0.412 | 4.794 | 0.063 | 0.486 | 0.089 | 0.053 | False |
| q 1.0, J 0 | 0.053 | -1.609 | 0.011 | 0.563 | -0.027 | 0.906 | 0.127 | 0.056 | False |
| q 1.0, J 6 | 0.100 | -1.589 | 0.151 | 2.506 | 0.020 | 0.645 | 0.131 | 0.061 | False |
| q 1.0, J 12 | 0.058 | -1.657 | 0.405 | 4.579 | 0.009 | 0.435 | 0.128 | 0.065 | True |

Runtime 8 s.
