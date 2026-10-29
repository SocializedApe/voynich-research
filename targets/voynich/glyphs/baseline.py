"""Baseline for variants.py: how close do two different letters' contexts get in real languages, and in a cipher
with homophones?

Same measure as variants.py (mean JSD of left and right unit contexts, '#' = word edge, units with >= 300
occurrences) on about 34,000 words of Latin, Renaissance Italian and early modern German (lang corpora, scheme
'early'), and on the Latin text with e and i each split at random into two homophones (e1/e2, i1/i2).

Run from the repository root: python targets/voynich/glyphs/baseline.py
"""
import collections, itertools, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', '..'))
from lang import lm, corpora
from variants import jsd

NW = 34000


def words(src):
    t = lm.norm(corpora.text([src])[:2000000], 'early', True)
    ws = t.split()
    return ws[len(ws) // 4: len(ws) // 4 + NW]


def report(name, seqs):
    L, R, freq = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter), collections.Counter()
    for u in seqs:
        u = ['#'] + u + ['#']
        for i in range(1, len(u) - 1):
            g = u[i]; freq[g] += 1; L[g][u[i - 1]] += 1; R[g][u[i + 1]] += 1
    common = [g for g, n in freq.items() if n >= 300]
    d = {(a, b): (jsd(L[a], L[b]) + jsd(R[a], R[b])) / 2 for a, b in itertools.combinations(sorted(common), 2)}
    v = sorted(d.values())
    print(f'{name:22} {len(common):3} units; median {v[len(v) // 2]:.3f}; closest: ' +
          ', '.join(f'{a}/{b} {x:.3f}' for (a, b), x in sorted(d.items(), key=lambda x: x[1])[:6]))


def main():
    rng = random.Random(1)
    for name, src in [('Latin', 'la-gutenberg'), ('Italian 1500-1600', 'it-renaissance'), ('German 1470-1610', 'de-dta-1470-1610')]:
        ws = words(src); report(name, [list(w) for w in ws])
        if name == 'Latin':
            hom = [[c + str(rng.randint(1, 2)) if c in 'ei' else c for c in w] for w in ws]
            report('Latin, e/i homophones', hom)


if __name__ == '__main__':
    main()
