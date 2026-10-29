"""Two-layer test on the real text: is the edge coupling carried by the non-copy words?

Hybrid hypothesis (hybrid_model.md): a cipher whose words obey a book-wide boundary rule (edge coupling), written by
a scribe who replaces some words by edited copies of recent ones. Copies do not obey the boundary rule. Prediction:
split every interior word b (with predecessor a in the same line) by whether b is a near-copy (edit distance <= 1,
identical included) of any of the previous W = 8 words on the page:
  hybrid:          coupling(a -> b) high for non-copies, low for copies
  pure cipher:     about equal in both groups (near-copies arise by chance)
  pure generator:  low in both groups
Coupling = I(last glyph unit of a; first glyph unit of b) minus the mean over 20 permutations of the predecessors
within the group, divided by H(first unit of b) in the group.

Run from the repository root: python research/voynich_siblings/copy_split_test.py <naibbe_tables.csv>
"""
import collections, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import cipher_models as cm, hybrid_model as h1, code_vs_generator as cg, slot_independence as si, a4_selfcitation as a4

W = 8


def groups(pages):
    cp, nc = [], []
    for p in pages:
        hist = []
        for ln in p['lines']:
            ws = ln['words']
            for i, b in enumerate(ws):
                if 0 < i < len(ws) - 1:
                    a = ws[i - 1]
                    pair = (si.eva_units(a)[-1], si.eva_units(b)[0])
                    (cp if any(a4.ld1(b, x) <= 1 for x in hist[-W:]) else nc).append(pair)
                hist.append(b)
    return cp, nc


def coupling(pairs, rng, reps=20):
    obs = cg.mi(pairs)
    pre = [a for a, _ in pairs]; post = [b for _, b in pairs]; base = 0
    for _ in range(reps):
        rng.shuffle(pre); base += cg.mi(list(zip(pre, post)))
    return (obs - base / reps) / cg.H(collections.Counter(post))


def main():
    rng = random.Random(101)
    zl = a4.load_zl(); skel = a4.skeleton(zl)
    lat = os.path.join(HERE, '..', '..', 'lang', 'corpora', 'la-gutenberg.txt')
    texts = [('Voynich (fixed parse)', zl),
             ('hybrid round 1 (cipher + copying)', h1.build(sys.argv[1], 19, 0.15, 8, 0.9, 0.2, 0.05, skel, lat)),
             ('hybrid round 1, seed 7', h1.build(sys.argv[1], 7, 0.15, 8, 0.9, 0.2, 0.05, skel, lat)),
             ('pure cipher (round 8)', cm.generate(cm.Variant(sys.argv[1], 19, merge=0.1, **h1.BASE), lat, skel)),
             ('pure generator (autocopist s19)', a4.Autocopist(19).generate(skel)),
             ('pure generator (autocopist s7)', a4.Autocopist(7).generate(skel))]
    print(f'{"text":36s} {"copies: n":>10s} {"coupling":>9s} {"non-copies: n":>14s} {"coupling":>9s} {"ratio non/copy":>14s}')
    for name, pages in texts:
        cp, nc = groups(pages)
        c1, c2 = coupling(cp, rng), coupling(nc, rng)
        print(f'{name:36s} {len(cp):10d} {c1:9.4f} {len(nc):14d} {c2:9.4f} {c2 / c1 if c1 > 0 else float("inf"):14.2f}', flush=True)


if __name__ == '__main__':
    main()
