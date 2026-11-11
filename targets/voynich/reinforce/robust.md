# Battery ceiling and held-out generation (11 Nov 2026)

Script `robust.py` (protocol in its docstring). Reproduce: `python reinforce/robust.py run oddeven quires halves`, then `python reinforce/robust.py report`.

| split | reference half (tokens) | other half of Voynich: matched/37 | held-out/30 | lang8 in-sample /37 | lang8 held-out /37 | cat8p in-sample /37 | cat8p held-out /37 | items the other half misses |
|---|---|---|---|---|---|---|---|---|
| oddeven, 0 | 17570 | 35 | 28 | 26-27 | 27-28 | 17-30 | 19-27 | h_peak_log2s, j_jacc_excess |
| oddeven, 1 | 17264 | 36 | 29 | 34-36 | 34-35 | 29-34 | 24-34 | j_jacc_excess |
| quires, 0 | 15950 | 33 | 27 | 34-36 | 28-30 | 28-34 | 24-29 | b_len1, d_adj_exact, h_peak_R, k_jsd_halves |
| quires, 1 | 18884 | 30 | 25 | 31-33 | 31-33 | 20-32 | 23-31 | b_len1, d_adj_exact, e_w10, e_w10_shuf, f_irrev, h_peak_log2s, h_peak_R |
| halves, 0 | 9341 | 28 | 21 | 30-31 | 23-26 | 25-33 | 23-29 | b_len1, d_adj_ld1, e_cover, e_prev2, h_peak_R, i_tok_acc, j_jacc_excess, k_jsd_halves, k_jsd_oddeven |
| halves, 1 | 25493 | 22 | 16 | 27-28 | 21-24 | 23-31 | 21-30 | b_len1, c_ttr, c_hapax_tokens, d_adj_ld1, e_cover, e_prev2, f_irrev, g_gal_init, g_gal_mid, h_peak_log2s, h_peak_R, i_tok_acc, j_jacc_excess, k_jsd_halves, k_jsd_oddeven |

