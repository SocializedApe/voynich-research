# Held-out bits per token of the hierarchical Pitman-Yor model, by hierarchy variant (10 Nov 2026)

Script `ablate.py` (60 sweeps; every fifth page held out and predicted token by token). Lower is better; the gain of a level = bits saved when it is present.

| text | full | -line | -page | -quire | -section | -hand | book+page+line | flat | gain line | gain page | gain quire | gain section | gain hand | hierarchy vs flat |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| voynich | 10.050 | 10.055 | 10.061 | 10.060 | 10.040 | 10.093 | 10.214 | 10.285 | +0.005 | +0.010 | +0.010 | -0.011 | +0.042 | +0.234 |
| latin | 12.180 | - | 12.183 | - | - | 12.167 | 12.173 | 12.161 | - | +0.003 | - | - | -0.013 | -0.019 |
| naibbe | 10.200 | - | 10.199 | - | - | 10.199 | 10.194 | 10.190 | - | -0.001 | - | - | -0.001 | -0.011 |
| english | 9.146 | - | 9.155 | - | - | 9.146 | 9.165 | 9.170 | - | +0.008 | - | - | -0.001 | +0.024 |
| gibberish | 11.692 | - | 12.182 | - | - | 11.689 | 11.703 | 12.263 | - | +0.491 | - | - | -0.003 | +0.571 |

Runtime 1482 s.
