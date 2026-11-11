# Every sweep tier read by key stability alone (12 Nov 2026)

Script `kaggle_pkg/restability.py` (criterion in its docstring; post hoc for tiers 3-5). Reproduce: `python verbose/kaggle_pkg/restability.py` from `targets/voynich`.

| tier | texts | cells | normalised stability: min / median / max | cells >= 0.5 | raw stability: min / median / max | cells >= 0.5 with KL <= 0.15 |
|---|---|---|---|---|---|---|
| tier1_cpu | synthetic ciphers | 4 | - | - | 0.73 / 1.00 / 1.00 | - |
| tier1_cpu | Voynich | 32 | - | - | 0.00 / 0.25 / 0.66 | - |
| gpucal | synthetic ciphers | 6 | - | - | 0.18 / 1.00 / 1.00 | - |
| gpufull | Voynich | 168 | - | - | 0.00 / 0.37 / 0.84 | - |
| tier3 | synthetic ciphers | 3 | -0.04 / 0.65 / 0.97 | 2 | 0.79 / 0.92 / 0.99 | 2 |
| tier3 | Voynich | 42 | -5.34 / -2.58 / -0.20 | 0 | 0.00 / 0.21 / 0.68 | 0 |
| tier4 | synthetic ciphers | 4 | -3.56 / 0.40 / 1.00 | 2 | 0.15 / 0.87 / 1.00 | 2 |
| tier4 | Voynich | 56 | -4.79 / -0.08 / 0.67 | 4 | 0.00 / 0.39 / 0.79 | 0 |
| tier5 | synthetic ciphers | 4 | -4.22 / 0.06 / 0.87 | 2 | 0.41 / 0.79 / 0.97 | 2 |
| tier5 | Voynich | 28 | -3.78 / -0.87 / 0.30 | 0 | 0.02 / 0.31 / 0.68 | 0 |
| tier6 | synthetic ciphers | 21 | -3.31 / 0.50 / 0.84 | 10 | 0.16 / 0.87 / 0.97 | 9 |

Voynich cells with normalised stability >= 0.5: 4.
- ('tier4', 'voy_h1_pharma', 'de', 'rawpos', 42): raw 0.67, normalised 0.59, letter KL 0.37
- ('tier4', 'voy_h2_bio', 'de', 'rawpos', 42): raw 0.79, normalised 0.64, letter KL 0.36
- ('tier4', 'voy_h2_bio', 'de', 'rawpos', 50): raw 0.77, normalised 0.67, letter KL 0.35
- ('tier4', 'voy_h3_stars', 'de', 'rawpos', 42): raw 0.63, normalised 0.53, letter KL 0.32

Tier 6 (noisy calibration ciphers) under stability >= 0.5 and KL <= 0.15, per noise level and K:

| text | K | normalised stability | KL | similarity to plaintext | passes |
|---|---|---|---|---|---|
| syn_gate7~g02 | 42 | -0.56 | 0.280 | 0.04 | no |
| syn_gate7~g02 | 50 | 0.75 | 0.078 | 0.83 | yes |
| syn_gate7~g02 | 60 | 0.79 | 0.039 | 0.88 | yes |
| syn_gate7~g05 | 42 | -0.94 | 0.190 | 0.45 | no |
| syn_gate7~g05 | 50 | 0.47 | 0.145 | 0.73 | no |
| syn_gate7~g05 | 60 | 0.78 | 0.095 | 0.77 | yes |
| syn_gate7~g05w05 | 42 | -3.31 | 0.253 | 0.13 | no |
| syn_gate7~g05w05 | 50 | 0.60 | 0.116 | 0.72 | yes |
| syn_gate7~g05w05 | 60 | 0.72 | 0.104 | 0.75 | yes |
| syn_gate7~g10 | 42 | -0.21 | 0.352 | 0.38 | no |
| syn_gate7~g10 | 50 | -0.15 | 0.274 | 0.59 | no |
| syn_gate7~g10 | 60 | 0.50 | 0.209 | 0.64 | no |
| syn_gate7~g20 | 42 | 0.69 | 1.467 | 0.05 | no |
| syn_gate7~g20 | 50 | 0.10 | 1.729 | 0.03 | no |
| syn_gate7~g20 | 60 | -0.82 | 1.700 | 0.04 | no |
| syn_gate7~w05 | 42 | 0.20 | 0.196 | 0.59 | no |
| syn_gate7~w05 | 50 | 0.74 | 0.028 | 0.91 | yes |
| syn_gate7~w05 | 60 | 0.79 | 0.020 | 0.94 | yes |
| syn_gate7~w15 | 42 | -3.12 | 0.272 | 0.55 | no |
| syn_gate7~w15 | 50 | 0.51 | 0.047 | 0.86 | yes |
| syn_gate7~w15 | 60 | 0.84 | 0.027 | 0.91 | yes |
