"""Round-8 cipher model (cipher_models.py): profile over several seeds, and the opener/core test of sandhi_test.py,
against Voynich. Run from the repository root: python research/voynich_siblings/model_check.py <naibbe_tables.csv> <ZL3b-n.txt>"""
import os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import cipher_models as cm, sandhi_test as st, code_vs_generator as cg, cross_boundary as cb, a4_selfcitation as a4

BEST = dict(chain=True, drift=True, k_page=2, p_chain=0.7, merge=0.1, sandhi=0.1, nulls=0.15, null_set=3, split=True, page_nulls=True)
rng = random.Random(71)
zl = a4.load_zl(); skel = a4.skeleton(zl)
lat = os.path.join(HERE, '..', '..', 'lang', 'corpora', 'la-gutenberg.txt')
keys = list(cm.TARGET)
print('text           ' + ' '.join(f'{k:>8s}' for k in keys) + '     dist   opener   core')
vl = []
for lang, ws, ss in cb.parse(sys.argv[2]):
    run = [ws[0]]
    for w, s in zip(ws[1:], ss):
        if s == '.' and cb.good(w) and cb.good(run[-1]): run.append(w)
        else:
            if len(run) >= 3: vl.append(run)
            run = [w]
    if len(run) >= 3: vl.append(run)
p = cm.profile(zl, rng); o, c, _ = st.measure(vl, rng)
print('Voynich        ' + ' '.join(f'{p[k]:8.3f}' for k in keys) + f'   {0:6.3f}  {o:7.4f} {c:7.4f}')
for seed in (19, 7, 3, 101):
    pages = cm.generate(cm.Variant(sys.argv[1], seed, **BEST), lat, skel)
    p = cm.profile(pages, rng); o, c, _ = st.measure(cg.lines_of(pages), rng)
    print(f'model s{seed:<7d} ' + ' '.join(f'{p[k]:8.3f}' for k in keys) + f'   {cm.distance(p):6.3f}  {o:7.4f} {c:7.4f}', flush=True)
