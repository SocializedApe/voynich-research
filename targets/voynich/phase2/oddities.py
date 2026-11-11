"""Which known process gives the word-internal profile that sets Voynich apart from natural languages? (12 Nov 2026)

Round 1 of phase 2 found eight features on which Voynich lies furthest outside 67 natural sources (the word-internal
ones and the rhythm of word lengths): m_tail_family, p_jsd_final_med, m_suffix_trie, m_prefix_trie, c_h2,
t_merge_len, w_len_skew, s_len_ac1_x. For every process in features.csv and features2.csv (ciphers, generators,
mimics, abbreviation, positional cipher, taxonomic constructed language, numerals; and each natural source), the
mean of each of the eight features over its chunks is compared with Voynich's window: the range of the 8 ZL-unit
chunks widened on each side by a quarter of the standard deviation of the natural-language chunks.
Rule, fixed before the run: a process 'reproduces the profile' if its mean is inside the window on at least 6 of
the 8 features; 4-5 is a partial match. The count per single chunk (best chunk) is listed too.

Run from targets/voynich: python phase2/oddities.py -> phase2/oddities_results.json, oddities.md
"""
import json, os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
ODD = ['m_tail_family', 'p_jsd_final_med', 'm_suffix_trie', 'm_prefix_trie', 'c_h2', 't_merge_len', 'w_len_skew', 's_len_ac1_x']


def main():
    df = pd.concat([pd.read_csv(os.path.join(HERE, f)) for f in ('features.csv', 'features2.csv')], ignore_index=True)
    v = df[(df.kind == 'voynich') & (df.process == 'ZL units')][ODD]; nat = df[df.kind == 'natural'][ODD]
    lo = v.min() - 0.25 * nat.std(); hi = v.max() + 0.25 * nat.std()
    df['inside'] = ((df[ODD] >= lo) & (df[ODD] <= hi)).sum(1)
    rows = []
    def row(name, g):
        m = g[ODD].mean(); ins = (m >= lo) & (m <= hi)
        rows.append(dict(text=name, chunks=len(g), matched=int(ins.sum()), best_chunk=int(g.inside.max()), which=[f for f in ODD if ins[f]], **{f: float(m[f]) for f in ODD}))
    for (k, p), g in df[df.kind != 'natural'].groupby(['kind', 'process']):
        row(f'{k}: {p}', g)
    for s, g in df[df.kind == 'natural'].groupby('source'):
        row(f'natural: {s}', g)
    rows.sort(key=lambda r: (-r['matched'], -r['best_chunk']))
    json.dump(dict(window={f: [float(lo[f]), float(hi[f])] for f in ODD}, rows=rows), open(os.path.join(HERE, 'oddities_results.json'), 'w'), indent=1)
    L = ['# Which process gives the Voynich word-internal profile? (12 Nov 2026)', '', 'Script `oddities.py` (rule in its docstring). Reproduce: `python phase2/build.py`, `python phase2/build2.py`, `python phase2/oddities.py` from `targets/voynich`.', '',
         'Window per feature (Voynich range widened by a quarter of the natural sd): ' + '; '.join(f'{f} {lo[f]:.2f} to {hi[f]:.2f}' for f in ODD) + '.', '',
         '| text | chunks | features inside (of 8), mean | best single chunk | ' + ' | '.join(ODD) + ' |', '|---|---|---|---|' + '---|' * len(ODD)]
    shown = [r for r in rows if not r['text'].startswith('natural')] + [r for r in rows if r['text'].startswith('natural')][:8]
    for r in sorted(shown, key=lambda r: (-r['matched'], -r['best_chunk'])):
        L.append(f"| {r['text']} | {r['chunks']} | {r['matched']} | {r['best_chunk']} | " + ' | '.join(('**' if f in r['which'] else '') + f'{r[f]:.2f}' + ('**' if f in r['which'] else '') for f in ODD) + ' |')
    nn = [r['matched'] for r in rows if r['text'].startswith('natural')]
    L += ['', f'Natural sources: {len(nn)}; features inside the window, mean {np.mean(nn):.1f}, maximum {max(nn)} (the eight best are listed above).']
    open(os.path.join(HERE, 'oddities.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    main()
