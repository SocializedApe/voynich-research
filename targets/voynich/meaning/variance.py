"""Is the change of glyph statistics in Voynich tied to the scribe, to the topic (section), or to the single page?

Glyph-pair profile of a set of pages: counts of adjacent glyph units inside words, with '#' at word edges (units:
cth ckh cph cfh ch sh, other letters single). Distance between two sets = JSD (bits, add-0.5 smoothing on the union).
Cells = (hand, section) from ZL ($H Davis hand, $I illustration type), pages with paragraph text.

1. Between cells: mean JSD over cell pairs that share the section but not the hand ('scribe effect'), share the hand
   but not the section ('topic effect'), share neither. Noise floor: split-half JSD inside a cell (random halves,
   20 draws), compared at a matched size by subsampling every compared cell to the same number of tokens.
2. Within cells, per page: mean JSD of each page against the rest of its cell, against the same after shuffling the
   cell's words among its pages (page sizes kept, 30 shuffles): ratio > 1 means pages differ more than sampling
   explains (something changes page by page).
Controls on the same skeleton and the same cell labels: Pliny leaf-wise plain Latin (pliny.py 'sectioned'; topic
changes, no scribes) and the round-8 cipher + scribe of it (per-page variant choices).

Run from the repository root: python targets/voynich/meaning/variance.py <naibbe_tables.csv>
"""
import collections, csv, itertools, math, os, random, re, statistics, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, os.path.join(HERE, '..', 'glyphs'))
import pliny, drift
import a4_selfcitation as a4
import b3_bakeoff as b3
from variants import UNIT

SIZE = 400     # tokens per compared cell (subsampled)


def bigrams(words):
    c = collections.Counter()
    for w in words:
        u = ['#'] + UNIT.findall(w) + ['#']
        c.update(zip(u, u[1:]))
    return c


def jsd(p, q):
    keys = set(p) | set(q); sp = sum(p.values()) + 0.5 * len(keys); sq = sum(q.values()) + 0.5 * len(keys); d = 0.0
    for k in keys:
        a = (p.get(k, 0) + 0.5) / sp; b = (q.get(k, 0) + 0.5) / sq; m = (a + b) / 2
        d += 0.5 * a * math.log2(a / m) + 0.5 * b * math.log2(b / m)
    return d


def analyse(name, pages, cells, rng):
    words = [b3.words_of([p]) for p in pages]
    byc = collections.defaultdict(list)
    for i, c in enumerate(cells): byc[c].append(i)
    big = {c: idx for c, idx in byc.items() if sum(len(words[i]) for i in idx) >= 2 * SIZE and len(idx) >= 4}
    sample = lambda idx: rng.sample([w for i in idx for w in words[i]], SIZE)
    kinds = collections.defaultdict(list)
    for a, b in itertools.combinations(sorted(big), 2):
        k = 'same section, other hand' if a[1] == b[1] else 'same hand, other section' if a[0] == b[0] else 'different both'
        kinds[k].append(statistics.mean(jsd(bigrams(sample(big[a])), bigrams(sample(big[b]))) for _ in range(5)))
    floor = []
    for c, idx in big.items():
        for _ in range(4):
            ws = [w for i in idx for w in words[i]]; rng.shuffle(ws)
            floor.append(jsd(bigrams(ws[:SIZE]), bigrams(ws[SIZE:2 * SIZE])))
    out = {k: (statistics.mean(v), len(v)) for k, v in kinds.items()}
    out['noise floor (split half)'] = (statistics.mean(floor), len(floor))
    # per page heterogeneity
    ratios = []
    for c, idx in big.items():
        def het(ws_by_page):
            tot = bigrams([w for ws in ws_by_page for w in ws]); vals = []
            for ws in ws_by_page:
                b = bigrams(ws); rest = tot.copy(); rest.subtract(b)
                vals.append(jsd(b, +rest))
            return statistics.mean(vals)
        obs = het([words[i] for i in idx])
        null = []
        for _ in range(30):
            pool = [w for i in idx for w in words[i]]; rng.shuffle(pool); it = iter(pool)
            null.append(het([[next(it) for _ in words[i]] for i in idx]))
        ratios.append((c, len(idx), obs / statistics.mean(null), (obs - statistics.mean(null)) / statistics.pstdev(null)))
    print(f'\n== {name}: {len(big)} cells (hand, section) with >= {2 * SIZE} tokens: {sorted(big)}')
    for k, (v, n) in sorted(out.items(), key=lambda x: x[0]): print(f'  {k:28} JSD {v:.4f} (n {n})')
    print('  per-page heterogeneity, observed / words-shuffled-within-cell: ' + ', '.join(f'{c[0]}{c[1]} {r:.2f} (z {z:.0f})' for c, n, r, z in ratios))
    return out, ratios


def main():
    csv_path = sys.argv[1]
    zl = b3.load_zl_lang(); skel = a4.skeleton(zl); langs = [p['lang'] for p in zl]
    meta = {}
    for r in csv.DictReader(open(os.path.join(HERE, '..', 'data', 'ZL3b-n.words.tsv'), encoding='utf-8'), delimiter='\t'):
        meta.setdefault(r['folio'], (r['hand'], r['illus']))
    cells = [meta.get(p['folio'], ('?', '?')) for p in zl]
    groups, sections = pliny.leaves_of(zl)
    sec_words = pliny.sectioned_words(zl, skel, groups, sections)
    plain = pliny.pour_pages(sec_words, skel)
    queues = {s: pliny.queue(b) for s, b in pliny.SRC.items()}; texts = []
    for leaf, idx in groups.items():
        need = sum(n for i in idx for n, _, _ in skel[i]) * 2; q = queues.get(sections[idx[0]], queues['T']); txt = []
        while sum(len(t.split()) for t in txt) < need: txt.append(next(q))
        texts.append((idx, txt))
    ciph = drift.scribe(pliny.cipher_pages(csv_path, texts, skel), langs, random.Random(19007), 0.0, 0.0)
    rng = random.Random(9)
    for name, p in (('Voynich', zl), ('Pliny plain, leaf-wise', plain), ('Pliny round-8 cipher + scribe', ciph)):
        analyse(name, p, cells, rng)


if __name__ == '__main__':
    main()
