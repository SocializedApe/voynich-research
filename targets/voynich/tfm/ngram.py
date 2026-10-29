"""Character n-gram baselines on the same test blocks as train.py (interpolated absolute discounting, d = 0.75).

The bar every neural model must clear: a model above its text's 5-gram has not learned the text well enough for its
context curve to mean anything. Writes results/ngram.json {text: {order: bits/char}}.
Run from the repository root: python targets/voynich/tfm/ngram.py
"""
import collections, json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import train as T
from summarize import ORDER


def score(train, test, V, order, step=3):
    cnt = [collections.Counter() for _ in range(order)]; ctx = [collections.Counter() for _ in range(order)]
    for p in train:
        p = p.tolist()
        for i in range(len(p)):
            for k in range(order):
                if i - k < 0: break
                c = tuple(p[i - k:i]); cnt[k][c + (p[i],)] += 1; ctx[k][c] += 1
    bits = []
    for p in test:
        p = p.tolist()
        for i in range(order, len(p), step):
            pr = 1.0 / V
            for k in range(order):
                c = tuple(p[i - k:i]); n = ctx[k].get(c, 0)
                if n: pr = (max(cnt[k].get(c + (p[i],), 0) - 0.75, 0) + 0.75 * min(n, V) * pr) / n
            bits.append(-math.log2(pr))
    return float(np.mean(bits))


def main():
    out = {}
    for n in ORDER:
        if not os.path.exists(os.path.join(HERE, 'data', n + '.txt')): continue
        vocab, tr, va, te = T.load(n)
        out[n] = {str(k): score(tr, te, len(vocab), k) for k in (2, 3, 5)}
        print(n, out[n], flush=True)
    os.makedirs(os.path.join(HERE, 'results'), exist_ok=True)
    json.dump(out, open(os.path.join(HERE, 'results', 'ngram.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
