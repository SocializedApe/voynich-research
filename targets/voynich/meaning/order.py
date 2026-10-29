"""Does the (mis)binding order matter for the order-dependent b3 items? (Layfield & Davis 2026: the codex is bound
out of order; its bifolia were meant as singulions.)

For each corpus, the order-dependent items are computed in the current page order and under random page orders
(pages kept whole, shuffled within their section = ZL illustration type, 30 orders): j_jacc_excess (adjacent pages'
vocabulary overlap above random pairs), k_jsd_halves (glyph-bigram JSD between the first and second half), and
h_peak_R (Montemurro-Zanette long-range peak). If Voynich's current-order value lies inside its shuffled range, the
binding order carries no information for that item and misbinding cannot have distorted it.
Order-free replacement for adjacency: leaf_excess = vocabulary overlap of the two sides of one leaf (f<n>r with
f<n>v, always physical neighbours whatever the binding) minus random page pairs. In the synthetic corpora (poured into
the ZL skeleton) the same page positions are paired.
Corpora: Voynich; autocopist s19; cipher + scribe and code_it + scribe (hybrid_model setting q 0.15, w 8, e 0.9,
g 0.2), and both with carry 0.6 and habit 0.6 (drift.py), seed 19.

Run from the repository root: python targets/voynich/meaning/order.py <naibbe_tables.csv>
"""
import collections, csv, json, os, random, re, statistics, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'research', 'voynich_siblings'))
import codebook as cbk, drift
import a4_selfcitation as a4
import b3_bakeoff as b3
import hybrid_model as hm
import cipher_models as cm

NSHUF = 30


def jac(a, b): return len(a & b) / len(a | b) if (a | b) else 0.0


def items(pages, leaf_pairs, mz=True):
    pt = [set(b3.words_of([p])) for p in pages]
    rng = random.Random(1); rnd = sum(jac(*(pt[i] for i in rng.sample(range(len(pt)), 2))) for _ in range(300)) / 300
    adj = sum(jac(pt[i], pt[i + 1]) for i in range(len(pt) - 1)) / (len(pt) - 1)
    leaf = sum(jac(pt[i], pt[j]) for i, j in leaf_pairs) / len(leaf_pairs)
    ms = b3.page_strings(pages, merged=True); h = len(ms) // 2
    out = {'j_jacc_excess': adj - rnd, 'leaf_excess': leaf - rnd, 'k_jsd_halves': b3.jsd(b3.bigram_dist(ms[:h]), b3.bigram_dist(ms[h:]))}
    if mz: out['h_peak_R'] = b3.mz_curve(b3.words_of(pages), random.Random(3))[2]
    return out


def main():
    csv_path = sys.argv[1]
    zl = b3.load_zl_lang(); skel = a4.skeleton(zl); N = len(b3.words_of(zl)); langs = [p['lang'] for p in zl]
    sec = {}
    for r in csv.DictReader(open(os.path.join(HERE, '..', 'data', 'ZL3b-n.words.tsv'), encoding='utf-8'), delimiter='\t'):
        sec.setdefault(r['folio'], r['illus'])
    folios = [p['folio'] for p in zl]; sections = [sec.get(f, '?') for f in folios]
    leaf = collections.defaultdict(dict)
    for i, f in enumerate(folios):
        m = re.match(r'f(\d+)([rv])', f)
        if m: leaf[m.group(1)].setdefault(m.group(2), i)
    pairs = [(d['r'], d['v']) for d in leaf.values() if 'r' in d and 'v' in d]
    print(f'{len(zl)} pages, {len(pairs)} leaves with text on both sides', flush=True)
    lat = os.path.join(ROOT, 'lang', 'corpora', 'la-gutenberg.txt')
    vfreq = collections.Counter(b3.words_of(zl)); vtypes = sorted(vfreq, key=lambda w: -vfreq[w])
    code = a4.pour(cbk.encode(a4.lang_words('it', N), vtypes)[0], skel)
    ciph = cm.generate(cm.Variant(csv_path, 19, merge=0.0, **hm.BASE), lat, skel)
    C = collections.OrderedDict()
    C['voynich'] = zl
    C['autocopist_s19'] = a4.Autocopist(19).generate(skel)
    C['cipher+scribe'] = drift.scribe(ciph, langs, random.Random(19007), 0.0, 0.0)
    C['code_it+scribe'] = drift.scribe(code, langs, random.Random(19007), 0.0, 0.0)
    C['cipher+scribe+carry+habit'] = drift.scribe(ciph, langs, random.Random(19007), 0.6, 0.6)
    C['code_it+scribe+carry+habit'] = drift.scribe(code, langs, random.Random(19007), 0.6, 0.6)
    res = {}
    for n, p in C.items():
        cur = items(p, pairs)
        rng = random.Random(11); sh = collections.defaultdict(list)
        for k in range(NSHUF):
            order = list(range(len(p)))
            groups = collections.defaultdict(list)
            for i, s in enumerate(sections): groups[s].append(i)
            new = order[:]
            for s, idx in groups.items():
                perm = idx[:]; rng.shuffle(perm)
                for a, b in zip(idx, perm): new[a] = b
            q = [p[i] for i in new]
            inv = {b: a for a, b in enumerate(new)}
            for key, v in items(q, [(inv[i], inv[j]) for i, j in pairs], mz=(k < 5)).items(): sh[key].append(v)
        res[n] = {'current': cur, 'shuffled': {k: (min(v), statistics.mean(v), max(v)) for k, v in sh.items()}}
        print(f'{n:28} ' + ' | '.join(f'{k} {cur[k]:.4f} (shuffled {res[n]["shuffled"][k][1]:.4f}, {res[n]["shuffled"][k][0]:.4f}-{res[n]["shuffled"][k][2]:.4f})' for k in cur), flush=True)
    json.dump(res, open(os.path.join(HERE, 'order_results.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
