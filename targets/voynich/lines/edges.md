# What the first and the last word of a line are made of (10 Nov 2026)

Script `edges.py` (protocol in its docstring).

## 1 and 3. Affix tests against the interior vocabulary

| lines | position | n | is an interior word | prefixed-like | cut-like | suffixed-like | mean length | mean length, prefix removed |
|---|---|---|---|---|---|---|---|---|
| all lines | first | 3339 | 0.666 | 0.368 | 0.022 | 0.013 | 5.44 | 5.05 |
| all lines | second | 3339 | 0.870 | 0.136 | 0.033 | 0.023 | 4.95 | 4.75 |
| all lines | interior | 18360 | 0.864 | 0.140 | 0.026 | 0.027 | 4.96 | 4.77 |
| all lines | penult | 3339 | 0.847 | 0.152 | 0.025 | 0.029 | 4.93 | 4.73 |
| all lines | last | 3339 | 0.694 | 0.160 | 0.015 | 0.111 | 4.65 | 4.45 |
| paragraph-first lines | first | 673 | 0.366 | 0.432 | 0.016 | 0.006 | 6.40 | 5.95 |
| paragraph-first lines | second | 673 | 0.771 | 0.168 | 0.030 | 0.021 | 5.43 | 5.16 |
| paragraph-first lines | interior | 3866 | 0.772 | 0.152 | 0.025 | 0.031 | 5.32 | 5.13 |
| paragraph-first lines | penult | 673 | 0.722 | 0.168 | 0.022 | 0.031 | 5.32 | 5.10 |
| paragraph-first lines | last | 673 | 0.587 | 0.149 | 0.007 | 0.101 | 4.90 | 4.71 |
| other lines | first | 2666 | 0.742 | 0.352 | 0.023 | 0.015 | 5.20 | 4.82 |
| other lines | second | 2666 | 0.895 | 0.128 | 0.034 | 0.024 | 4.83 | 4.65 |
| other lines | interior | 14494 | 0.889 | 0.137 | 0.026 | 0.026 | 4.86 | 4.68 |
| other lines | penult | 2666 | 0.878 | 0.148 | 0.026 | 0.029 | 4.83 | 4.64 |
| other lines | last | 2666 | 0.721 | 0.163 | 0.017 | 0.114 | 4.59 | 4.39 |

Words shuffled within each line (control):

| lines | position | n | is an interior word | prefixed-like | cut-like | suffixed-like | mean length |
|---|---|---|---|---|---|---|---|
| all lines | first | 3339 | 0.821 | 0.187 | 0.029 | 0.036 | 5.04 |
| all lines | second | 3339 | 0.824 | 0.183 | 0.030 | 0.036 | 5.02 |
| all lines | interior | 18360 | 0.836 | 0.165 | 0.025 | 0.034 | 4.95 |
| all lines | penult | 3339 | 0.828 | 0.178 | 0.026 | 0.032 | 4.99 |
| all lines | last | 3339 | 0.834 | 0.164 | 0.026 | 0.030 | 4.99 |

Line-first words by first glyph: share prefixed-like, against interior words beginning with the same glyph:

| first glyph | n first | prefixed-like, first | n interior | prefixed-like, interior |
|---|---|---|---|---|
| d | 522 | 0.379 | 1310 | 0.115 |
| y | 462 | 0.396 | 698 | 0.119 |
| q | 436 | 0.032 | 3299 | 0.025 |
| o | 415 | 0.154 | 4048 | 0.044 |
| p | 358 | 0.525 | 110 | 0.755 |
| t | 339 | 0.596 | 337 | 0.588 |
| s | 329 | 0.632 | 422 | 0.427 |
| sh | 153 | 0.261 | 1716 | 0.104 |
| ch | 101 | 0.139 | 3218 | 0.099 |
| k | 90 | 0.500 | 670 | 0.499 |
| l | 59 | 0.712 | 800 | 0.444 |
| f | 32 | 0.406 | 47 | 0.745 |
| a | 13 | 0.308 | 929 | 0.055 |
| r | 9 | 0.556 | 259 | 0.575 |

## 2. Slots by position

| language | position | n | no opener | no middle | no ending | opener length | middle length | ending length | word length |
|---|---|---|---|---|---|---|---|---|---|
| A | first | 1088 | 0.155 | 0.304 | 0.022 | 1.25 | 1.96 | 2.01 | 5.22 |
| A | second | 1088 | 0.551 | 0.309 | 0.017 | 0.87 | 1.89 | 1.94 | 4.70 |
| A | interior | 4992 | 0.424 | 0.396 | 0.015 | 1.07 | 1.64 | 1.95 | 4.66 |
| A | penult | 1088 | 0.397 | 0.423 | 0.020 | 1.04 | 1.60 | 2.01 | 4.66 |
| A | last | 1088 | 0.347 | 0.437 | 0.051 | 0.99 | 1.69 | 1.94 | 4.62 |
| A | last, space <= 3 | 104 | 0.413 | 0.865 | 0.048 | 0.62 | 0.18 | 1.55 | 2.36 |
| A | last, space 4-5 | 175 | 0.297 | 0.560 | 0.057 | 0.95 | 0.93 | 2.04 | 3.91 |
| A | last, space 6-8 | 274 | 0.332 | 0.369 | 0.047 | 1.06 | 1.86 | 1.90 | 4.83 |
| A | last, space 9+ | 531 | 0.360 | 0.347 | 0.051 | 1.03 | 2.15 | 2.00 | 5.18 |
| B | first | 2206 | 0.108 | 0.393 | 0.005 | 1.22 | 1.86 | 2.46 | 5.55 |
| B | second | 2206 | 0.519 | 0.396 | 0.010 | 0.93 | 1.75 | 2.39 | 5.07 |
| B | interior | 13150 | 0.383 | 0.479 | 0.010 | 1.21 | 1.47 | 2.39 | 5.07 |
| B | penult | 2206 | 0.370 | 0.518 | 0.005 | 1.19 | 1.39 | 2.48 | 5.06 |
| B | last | 2206 | 0.319 | 0.425 | 0.020 | 1.08 | 1.62 | 1.96 | 4.67 |
| B | last, space <= 3 | 190 | 0.458 | 0.826 | 0.026 | 0.59 | 0.24 | 1.56 | 2.40 |
| B | last, space 4-5 | 359 | 0.309 | 0.504 | 0.031 | 1.05 | 0.98 | 1.75 | 3.78 |
| B | last, space 6-8 | 525 | 0.290 | 0.410 | 0.017 | 1.16 | 1.66 | 1.94 | 4.76 |
| B | last, space 9+ | 1025 | 0.313 | 0.343 | 0.017 | 1.13 | 2.04 | 2.10 | 5.27 |

- A | endings over-represented in the last word: am x9.3 (0.083 of last words), om x5.1 (0.033 of last words), an x4.5 (0.018 of last words), (none) x3.3 (0.051 of last words), d x2.6 (0.037 of last words), dy x1.8 (0.114 of last words), ain x1.8 (0.030 of last words), al x1.5 (0.061 of last words), ar x1.5 (0.062 of last words), aiin x1.4 (0.142 of last words)
- A | endings under-represented in the last word: ol x0.2 (0.035 of last words), o x0.3 (0.014 of last words), or x0.3 (0.028 of last words), s x0.8 (0.044 of last words), y x1.1 (0.193 of last words), aiin x1.4 (0.142 of last words)
- B | endings over-represented in the last word: om x53.0 (0.018 of last words), am x41.1 (0.161 of last words), m x24.8 (0.012 of last words), y x2.1 (0.194 of last words), (none) x1.9 (0.020 of last words), r x1.5 (0.010 of last words), dy x1.4 (0.094 of last words), d x1.3 (0.019 of last words), s x1.1 (0.025 of last words), al x1.0 (0.062 of last words)
- B | endings under-represented in the last word: eey x0.2 (0.015 of last words), eedy x0.4 (0.021 of last words), ey x0.4 (0.024 of last words), edy x0.5 (0.067 of last words), ar x0.5 (0.043 of last words), aiin x0.6 (0.054 of last words)

## 4. Currier A against B, by slot and position (JSD in bits; in brackets interior words subsampled to the same counts: mean, max of 20)

| slot | first | second | interior | penult | last |
|---|---|---|---|---|---|
| opener | 0.057 (0.071, 0.080) | 0.073 (0.077, 0.091) | 0.069 (0.069, 0.069) | 0.098 (0.073, 0.084) | 0.106 (0.072, 0.080) |
| middle | 0.107 (0.082, 0.092) | 0.093 (0.082, 0.089) | 0.077 (0.077, 0.077) | 0.094 (0.083, 0.100) | 0.116 (0.082, 0.094) |
| ending | 0.139 (0.150, 0.179) | 0.152 (0.145, 0.157) | 0.147 (0.147, 0.147) | 0.159 (0.147, 0.170) | 0.087 (0.149, 0.162) |

## 5. Edge words against interior words of the same length: JSD (floor), n

| language | length | interior n | share of interior / of last words | last | last, no -m words | first |
|---|---|---|---|---|---|---|
| A | 1 | 263 | 0.053 / 0.041 | 0.204 (0.023), 45 | 0.197 (0.023), 44 | - |
| A | 2 | 291 | 0.058 / 0.097 | 0.225 (0.021), 106 | 0.207 (0.025), 91 | - |
| A | 3 | 570 | 0.114 / 0.159 | 0.228 (0.033), 173 | 0.206 (0.042), 137 | 0.212 (0.047), 122 |
| A | 4 | 1158 | 0.232 / 0.185 | 0.270 (0.058), 201 | 0.256 (0.063), 173 | 0.231 (0.068), 161 |
| A | 5 | 1219 | 0.244 / 0.210 | 0.172 (0.062), 228 | 0.156 (0.065), 205 | 0.211 (0.051), 303 |
| A | 6 | 792 | 0.159 / 0.150 | 0.184 (0.061), 163 | 0.173 (0.066), 146 | 0.187 (0.058), 210 |
| A | 7 | 458 | 0.092 / 0.084 | 0.142 (0.057), 91 | 0.133 (0.058), 82 | 0.170 (0.057), 128 |
| A | 8 | 163 | 0.033 / 0.051 | 0.148 (0.053), 56 | 0.143 (0.053), 52 | 0.165 (0.051), 69 |
| B | 1 | 353 | 0.027 / 0.021 | 0.212 (0.021), 46 | 0.181 (0.025), 42 | 0.229 (0.015), 66 |
| B | 2 | 891 | 0.068 / 0.103 | 0.258 (0.016), 228 | 0.174 (0.020), 172 | 0.183 (0.073), 46 |
| B | 3 | 947 | 0.072 / 0.157 | 0.265 (0.025), 347 | 0.229 (0.030), 290 | 0.294 (0.040), 218 |
| B | 4 | 2201 | 0.167 / 0.193 | 0.273 (0.042), 425 | 0.220 (0.057), 323 | 0.313 (0.077), 211 |
| B | 5 | 3376 | 0.257 / 0.216 | 0.248 (0.062), 476 | 0.204 (0.074), 382 | 0.313 (0.058), 502 |
| B | 6 | 2852 | 0.217 / 0.161 | 0.237 (0.075), 356 | 0.210 (0.083), 299 | 0.275 (0.057), 536 |
| B | 7 | 1691 | 0.129 / 0.082 | 0.201 (0.084), 180 | 0.181 (0.094), 152 | 0.228 (0.057), 355 |
| B | 8 | 572 | 0.043 / 0.040 | 0.155 (0.061), 89 | 0.139 (0.058), 73 | 0.198 (0.058), 149 |

Runtime 16 s.
