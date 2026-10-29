"""Hybrid model: the round-8 cipher of Latin (cipher_models.py) written out by a copying scribe.

The held-out test (cipher_models.md) showed every cipher variant missing Voynich's copying signatures (near-copies
close by, page continuity, drift) while the self-citation generator misses the cipher-like items. Hybrid: generate
the cipher text, then a scribe who, with probability Q per token, writes instead a near-copy of a word he wrote in
the last W tokens on the same page (edited with probability E by one small change: e/ee, k/t, ch/sh, o/a, an o- or
qo- opening added or dropped), and who opens a line with a gallows-led variant (p/f/k/t + rest) with probability G.

Protocol, fixed before any run (28 Oct 2026):
  TUNING items: the seven profile items of cipher_models.TARGET (h2, start/end, edge, hapax, one page, D256,
                adjacent identical) and three b3 items: e_w10 (near-copy within 10 tokens), g_gal_init
                (line-initial gallows), b_len_sd (word length sd).
  HELD-OUT items: every other b3 item (37 - 7 overlapping/declared = 30: b3 items a_h2_raw, c_hapax_types,
                d_adj_exact, j_one_page, e_w10, g_gal_init, b_len_sd are excluded from the held-out count).
  Grid search on the tuning items only (seed 19); the best three settings then go, with seeds 19 and 7, through
  the full b3 battery, and only the held-out count is reported as the test.

Run from the repository root:
  python research/voynich_siblings/hybrid_model.py <naibbe_tables.csv> --grid
  python research/voynich_siblings/hybrid_model.py <naibbe_tables.csv> --holdout "<q>,<w>,<e>,<g>,<merge>" [...]
"""
import collections, itertools, math, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import cipher_models as cm, a4_selfcitation as a4
import b3_bakeoff as b3

BASE = dict(chain=True, drift=True, k_page=2, p_chain=0.7, sandhi=0.1, nulls=0.15, null_set=3, split=True, page_nulls=True)
TUNED_B3 = {'a_h2_raw', 'c_hapax_types', 'd_adj_exact', 'j_one_page', 'e_w10', 'g_gal_init', 'b_len_sd'}
EXTRA_TARGET = dict(e_w10=0.276, g_gal_init=0.223, b_len_sd=1.788)   # Voynich values, fixed parse (b3)


def edit(w, rng):
    out = _edit(w, rng)
    return out if out else w


def _edit(w, rng):
    r = rng.random()
    if r < 0.2 and 'e' in w:
        return w.replace('ee', 'e', 1) if 'ee' in w else w.replace('e', 'ee', 1)
    if r < 0.35 and ('k' in w or 't' in w):
        return w.translate(str.maketrans('kt', 'tk'))
    if r < 0.5 and ('ch' in w or 'sh' in w):
        return w.replace('ch', 'sh', 1) if 'ch' in w else w.replace('sh', 'ch', 1)
    if r < 0.65 and ('o' in w or 'a' in w):
        return w.replace('o', 'a', 1) if 'o' in w else w.replace('a', 'o', 1)
    if r < 0.8:
        return w[2:] if w.startswith('qo') and len(w) > 3 else ('qo' + w if w[:1] in 'kt' else 'o' + w)
    return w[1:] if w.startswith('o') and len(w) > 2 else w + 'y' if not w.endswith('y') else w[:-1]


def hybridize(pages, rng, q, w, e, g):
    out = []
    for p in pages:
        hist = []
        lines = []
        for ln in p['lines']:
            ws = []
            for i, tok in enumerate(ln['words']):
                if hist and rng.random() < q:
                    tok = rng.choice(hist[-w:])
                    if rng.random() < e:
                        tok = edit(tok, rng)
                if i == 0 and rng.random() < g:
                    core = tok[2:] if tok.startswith('qo') else tok
                    tok = rng.choice('pftk') + (core[1:] if core[:1] in 'pftkoy' else core)
                ws.append(tok); hist.append(tok)
            lines.append({'words': ws, 'para_start': ln['para_start']})
        out.append({'folio': p.get('folio', ''), 'lines': lines})
    return out


def tune_profile(pages, rng):
    p = cm.profile(pages, rng)
    sc = a4.selfcit_stats(pages)['nearest_earlier_LD<=1']
    words = [x for pg in pages for ln in pg['lines'] for x in ln['words']]
    L = [len(x) for x in words]; m = sum(L) / len(L)
    gi = ni = 0
    for pg in pages:
        for ln in pg['lines']:
            if len(ln['words']) >= 3:
                ni += 1; gi += ln['words'][0][0] in 'ktpf'
    p.update(e_w10=sc['frac_all_within_10'], g_gal_init=gi / ni, b_len_sd=math.sqrt(sum((x - m) ** 2 for x in L) / len(L)))
    return p


def distance(p):
    t = dict(cm.TARGET, **EXTRA_TARGET)
    return sum(abs(p[k] - v) / abs(v) for k, v in t.items()) / len(t)


def build(csv_path, seed, q, w, e, g, merge, skel, lat):
    rng = random.Random(seed * 1000 + 7)
    base = cm.generate(cm.Variant(csv_path, seed, merge=merge, **BASE), lat, skel)
    return hybridize(base, rng, q, w, e, g)


def main():
    csv_path = sys.argv[1]
    zl = a4.load_zl(); skel = a4.skeleton(zl)
    lat = os.path.join(HERE, '..', '..', 'lang', 'corpora', 'la-gutenberg.txt')
    rng = random.Random(83)
    keys = list(cm.TARGET) + list(EXTRA_TARGET)
    if '--grid' in sys.argv:
        print('setting                         dist  ' + ' '.join(f'{k:>9s}' for k in keys))
        vp = tune_profile(zl, rng)
        print('Voynich                               ' + ' '.join(f'{vp[k]:9.3f}' for k in keys))
        res = []
        for q, w, e, g, mg in itertools.product((0.15, 0.3, 0.45), (8, 30), (0.5, 0.9), (0.0, 0.2), (0.0, 0.05)):
            p = tune_profile(build(csv_path, 19, q, w, e, g, mg, skel, lat), rng)
            d = distance(p); res.append((d, (q, w, e, g, mg)))
            print(f'q {q:.2f} w {w:2d} e {e:.1f} g {g:.1f} m {mg:.2f}   {d:5.3f}  ' + ' '.join(f'{p[k]:9.3f}' for k in keys), flush=True)
        res.sort()
        print('BEST3:', ' | '.join(','.join(str(x) for x in s) + f' ({d:.3f})' for d, s in res[:3]))
    if '--holdout' in sys.argv:
        settings = [tuple(float(x) for x in s.split(',')) for s in sys.argv[sys.argv.index('--holdout') + 1:]]
        corpora = {'voynich_ZL': zl, 'autocopist_s19': a4.Autocopist(19).generate(skel), 'autocopist_s7': a4.Autocopist(7).generate(skel),
                   'naibbe_latin': cm.generate(cm.Variant(csv_path, 19), lat, skel),
                   'round8_s19': cm.generate(cm.Variant(csv_path, 19, merge=0.1, **BASE), lat, skel)}
        for i, (q, w, e, g, mg) in enumerate(settings):
            for seed in (19, 7):
                corpora[f'hyb{i}_s{seed}'] = build(csv_path, seed, q, int(w), e, g, mg, skel, lat)
        extra = {}
        results = {n: b3.battery(p, n, extra) for n, p in corpora.items()}
        tol, marks = b3.score(results)
        allk = [k for k, _ in b3.ITEMS]; held = [k for k in allk if k not in TUNED_B3]
        print(f'held-out items: {len(held)}')
        for n in corpora:
            print(f'{n:16s} all {sum(marks[n].values()):2d}/37   held-out {sum(marks[n][k] for k in held):2d}/{len(held)}   held-out misses: ' +
                  ', '.join(k for k in held if not marks[n][k]))
        for i, s in enumerate(settings):
            print(f'hyb{i} = q {s[0]} w {int(s[1])} e {s[2]} g {s[3]} merge {s[4]}')


if __name__ == '__main__':
    main()
