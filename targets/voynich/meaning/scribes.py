"""How many writing styles do the pages support, and do they follow Davis's hands, Currier A/B or the sections?

Each page = counts of glyph-pair features (units inside words, '#' at word edges; the 300 commonest pairs, the rest
pooled). Model: mixture of k multinomials (one style per page), EM with 10 restarts, add-1 smoothing. For k = 1..8,
5-fold cross-validation over pages: fit on 4/5, score the held-out pages by their log-likelihood under the mixture
(per token); the k with the best held-out score is the number of styles the data supports. The full-data fit at the
best k (and at k = 5) is compared with Davis's hands, Currier language and ZL section: adjusted Rand index and the
contingency table. Control: Pliny leaf-wise plain Latin on the same skeleton (pliny.py), where no scribes exist.

Run from the repository root: python targets/voynich/meaning/scribes.py
"""
import collections, csv, math, os, random, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'glyphs'))
import pliny
import a4_selfcitation as a4
import b3_bakeoff as b3
from variants import UNIT

F = 300


def features(pages_words, vocab=None):
    cs = []
    for ws in pages_words:
        c = collections.Counter()
        for w in ws:
            u = ['#'] + (UNIT.findall(w) if vocab is None or True else []) + ['#']
            c.update(zip(u, u[1:]))
        cs.append(c)
    tot = collections.Counter(); [tot.update(c) for c in cs]
    keys = [k for k, _ in tot.most_common(F)]; idx = {k: i for i, k in enumerate(keys)}
    X = np.zeros((len(cs), F + 1))
    for r, c in enumerate(cs):
        for k, v in c.items(): X[r, idx.get(k, F)] += v
    return X


def em(X, k, rng, iters=200, restarts=10):
    best = None
    for _ in range(restarts):
        R = rng.dirichlet(np.ones(k), size=len(X))
        for _ in range(iters):
            pi = R.mean(0) + 1e-9; th = (R.T @ X) + 1.0; th /= th.sum(1, keepdims=True)
            L = X @ np.log(th).T + np.log(pi)
            m = L.max(1, keepdims=True); R = np.exp(L - m); R /= R.sum(1, keepdims=True)
        ll = float((m[:, 0] + np.log(np.exp(L - m).sum(1))).sum())
        if best is None or ll > best[0]: best = (ll, pi, th, R)
    return best


def heldout(X, k, rng, folds=5):
    order = rng.permutation(len(X)); tot = 0.0
    for f in range(folds):
        te = order[f::folds]; tr = np.setdiff1d(order, te)
        _, pi, th, _ = em(X[tr], k, rng, restarts=5)
        L = X[te] @ np.log(th).T + np.log(pi); m = L.max(1, keepdims=True)
        tot += float((m[:, 0] + np.log(np.exp(L - m).sum(1))).sum())
    return tot / X.sum()


def ari(a, b):
    from collections import Counter
    n = len(a); cab = Counter(zip(a, b)); ca = Counter(a); cb = Counter(b)
    c2 = lambda x: x * (x - 1) / 2
    s = sum(c2(v) for v in cab.values()); sa = sum(c2(v) for v in ca.values()); sb = sum(c2(v) for v in cb.values())
    e = sa * sb / c2(n); mx = (sa + sb) / 2
    return (s - e) / (mx - e) if mx != e else 0.0


def report(name, X, labels, rng):
    scores = {k: heldout(X, k, rng) for k in range(1, 9)}
    bestk = max(scores, key=scores.get)
    print(f'\n== {name}: {len(X)} pages; held-out log-likelihood per glyph pair by k: ' +
          ' '.join(f'{k}:{v:.4f}' for k, v in scores.items()) + f' | best k = {bestk}', flush=True)
    for k in sorted({bestk, 5}):
        _, _, _, R = em(X, k, rng); z = R.argmax(1)
        print(f'  k={k}: ARI with hand {ari(z, labels["hand"]):.2f}, Currier {ari(z, labels["lang"]):.2f}, section {ari(z, labels["section"]):.2f}')
        for lab in ('hand', 'section'):
            tab = collections.Counter(zip(z, labels[lab]))
            cols = sorted(set(labels[lab]))
            print(f'    cluster x {lab}: ' + ' | '.join(f'c{c}: ' + ' '.join(f'{v}{tab[(c, v)]}' for v in cols if tab[(c, v)]) for c in range(k)))


def main():
    rng = np.random.default_rng(4)
    zl = b3.load_zl_lang(); skel = a4.skeleton(zl)
    meta = {}
    for r in csv.DictReader(open(os.path.join(HERE, '..', 'data', 'ZL3b-n.words.tsv'), encoding='utf-8'), delimiter='\t'):
        meta.setdefault(r['folio'], (r['hand'], r['lang'], r['illus']))
    keep = [i for i, p in enumerate(zl) if sum(len(ln['words']) for ln in p['lines']) >= 60]
    labels = {'hand': [meta[zl[i]['folio']][0] for i in keep], 'lang': [meta[zl[i]['folio']][1] for i in keep],
              'section': [meta[zl[i]['folio']][2] for i in keep]}
    print('pages with >= 60 words:', len(keep), '| hands', collections.Counter(labels['hand']), '| sections', collections.Counter(labels['section']))
    report('Voynich', features([b3.words_of([zl[i]]) for i in keep]), labels, rng)
    groups, sections = pliny.leaves_of(zl)
    plain = pliny.sectioned_words(zl, skel, groups, sections)
    report('Pliny plain, leaf-wise (control, no scribes)', features([plain[i] for i in keep]), labels, rng)


if __name__ == '__main__':
    main()
