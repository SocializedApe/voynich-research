"""Table of the context curves from train.py results: loss (bits/char) by context length and the gains, with the
5-gram baseline (ngram.py) for reference; several seeds of one text are averaged (mean, and range in brackets).

short gain = loss(ctx 0) - loss(ctx 8-15)         what the current word and its neighbour give (spelling, word grammar)
mid gain   = loss(ctx 8-15) - loss(ctx 32-63)     a few words back (local syntax, phrase, copying)
long gain  = loss(ctx 32-63) - loss(ctx 128-255)  two to five lines back (topic, repetition across lines)
A model whose mean test loss is above its text's 5-gram is flagged UNDERTRAINED: its curve says nothing.

Run from the repository root: python targets/voynich/tfm/summarize.py
"""
import collections, json, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ORDER = ['voynich', 'voynich_shufline', 'voynich_shufpage', 'latin', 'italian', 'naibbe', 'rugg', 'autocopist']


def main():
    runs = collections.defaultdict(list)
    for f in os.listdir(os.path.join(HERE, 'results')):
        if f.endswith('.json') and f not in ('probe.json', 'ngram.json'):
            r = json.load(open(os.path.join(HERE, 'results', f))); runs[r['name']].append(r)
    ng = json.load(open(os.path.join(HERE, 'results', 'ngram.json'))) if os.path.exists(os.path.join(HERE, 'results', 'ngram.json')) else {}
    print('| text | seeds | 5-gram | model mean | ctx0 | ctx 8-15 | ctx 32-63 | ctx 128-255 | short gain | mid gain | long gain | flag |')
    print('|---|---|---|---|---|---|---|---|---|---|---|---|')
    for n in ORDER:
        if n not in runs: continue
        C = np.array([r['curve'] for r in runs[n]])
        def col(f):
            v = np.array([f(c) for c in C]); return f'{v.mean():.3f}' + (f' [{v.min():.3f}-{v.max():.3f}]' if len(v) > 1 else '')
        mean = C.mean(1).mean(); g5 = ng.get(n, {}).get('5', float('nan'))
        flag = 'UNDERTRAINED' if mean > g5 else ''
        print(f'| {n} | {len(C)} | {g5:.3f} | {mean:.3f} | {col(lambda c: c[0])} | {col(lambda c: c[8:16].mean())} | '
              f'{col(lambda c: c[32:64].mean())} | {col(lambda c: c[128:].mean())} | {col(lambda c: c[0] - c[8:16].mean())} | '
              f'{col(lambda c: c[8:16].mean() - c[32:64].mean())} | {col(lambda c: c[32:64].mean() - c[128:].mean())} | {flag} |')


if __name__ == '__main__':
    main()
