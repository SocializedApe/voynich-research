"""Can a scribe mechanism close the three b3 items every model fails (page adjacency, A/B drift, self-citation ratio)?

Protocol, fixed before any run (28 Oct 2026):
  Bases: the round-8 letter cipher of Latin (cipher_models, hybrid_model.BASE) and codebook_vocab_it (codebook.py),
  poured into the ZL skeleton; scribe = hybrid_model.hybridize at its tuned setting (q 0.15, w 8, e 0.9, g 0.2), then:
  carry c: each copy event draws its source, with probability c, from the last 30 words of the previous page instead
           of the current page (implemented as a modified hybridize);
  habit h: on Currier-B pages (ZL page language), each word is rewritten with probability h by the B habit: an opening
           k/t gets qo- (k... -> qok...), and one e becomes ee.
  Grid c in (0, 0.3, 0.6) x h in (0, 0.3, 0.6), seed 19, distance on the three TUNING items only: j_jacc_excess,
  k_jsd_halves, e_ratio (mean of |value - Voynich| / |Voynich|). The best two settings per base, seeds 19 and 7, then
  run the full b3 battery; the test is the count on the 34 other items (HELD-OUT), b3.score tolerance as before.

Run from the repository root: python targets/voynich/meaning/drift.py <naibbe_tables.csv>
"""
import collections, itertools, json, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'research', 'voynich_siblings'))
import codebook as cbk
import a4_selfcitation as a4
import b3_bakeoff as b3
import hybrid_model as hm
import cipher_models as cm

TUNE = ('j_jacc_excess', 'k_jsd_halves', 'e_ratio')
Q, W, E, G = 0.15, 8, 0.9, 0.2


def scribe(pages, langs, rng, c, h):
    out, prev_tail = [], []
    for p, lang in zip(pages, langs):
        hist, lines = [], []
        for ln in p['lines']:
            ws = []
            for i, tok in enumerate(ln['words']):
                if (hist or prev_tail) and rng.random() < Q:
                    pool = prev_tail if (prev_tail and (not hist or rng.random() < c)) else hist[-W:]
                    tok = rng.choice(pool)
                    if rng.random() < E: tok = hm.edit(tok, rng)
                if i == 0 and rng.random() < G:
                    core = tok[2:] if tok.startswith('qo') else tok
                    tok = rng.choice('pftk') + (core[1:] if core[:1] in 'pftkoy' else core)
                if lang == 'B' and rng.random() < h:
                    if tok[:1] in 'kt': tok = 'qo' + tok
                    if 'e' in tok and 'ee' not in tok: tok = tok.replace('e', 'ee', 1)
                ws.append(tok); hist.append(tok)
            lines.append({'words': ws, 'para_start': ln['para_start']})
        prev_tail = hist[-30:]
        out.append({'folio': p.get('folio', ''), 'lines': lines})
    return out


def tune_items(pages):
    pt = [set(b3.words_of([p])) for p in pages]
    jac = lambda a, b: len(a & b) / len(a | b) if (a | b) else 0.0
    adj = sum(jac(pt[i], pt[i + 1]) for i in range(len(pt) - 1)) / (len(pt) - 1)
    rng = random.Random(1); rnd = [jac(*(pt[i] for i in rng.sample(range(len(pt)), 2))) for _ in range(100)]
    ms = b3.page_strings(pages, merged=True); hh = len(ms) // 2
    sc = a4.selfcit_stats(pages)['nearest_earlier_LD<=1']['frac_all_within_10']
    ss = a4.selfcit_stats(a4.shuffle_within_page(pages))['nearest_earlier_LD<=1']['frac_all_within_10']
    return {'j_jacc_excess': adj - sum(rnd) / len(rnd), 'k_jsd_halves': b3.jsd(b3.bigram_dist(ms[:hh]), b3.bigram_dist(ms[hh:])),
            'e_ratio': sc / ss if ss else 0.0}


def main():
    csv_path = sys.argv[1]
    zl = b3.load_zl_lang(); skel = a4.skeleton(zl); N = len(b3.words_of(zl)); langs = [p['lang'] for p in zl]
    lat = os.path.join(ROOT, 'lang', 'corpora', 'la-gutenberg.txt')
    vfreq = collections.Counter(b3.words_of(zl)); vtypes = sorted(vfreq, key=lambda w: -vfreq[w])
    plain = a4.lang_words('it', N)
    bases = {'cipher': cm.generate(cm.Variant(csv_path, 19, merge=0.0, **hm.BASE), lat, skel),
             'code_it': a4.pour(cbk.encode(plain, vtypes)[0], skel)}
    target = tune_items(zl); print('Voynich tuning items:', {k: round(v, 4) for k, v in target.items()}, flush=True)
    best = {}
    for bname, base in bases.items():
        res = []
        for c, h in itertools.product((0.0, 0.3, 0.6), (0.0, 0.3, 0.6)):
            t = tune_items(scribe(base, langs, random.Random(19 * 1000 + 7), c, h))
            d = sum(abs(t[k] - target[k]) / abs(target[k]) for k in TUNE) / len(TUNE); res.append((d, c, h))
            print(f'{bname} c {c} h {h}: distance {d:.3f} | ' + ' '.join(f'{k} {t[k]:.4f}' for k in TUNE), flush=True)
        best[bname] = sorted(res)[:2]
    C = collections.OrderedDict([('voynich_ZL', zl), ('autocopist_s19', a4.Autocopist(19).generate(skel)),
                                 ('autocopist_s7', a4.Autocopist(7).generate(skel))])
    for bname, base in bases.items():
        for d, c, h in best[bname]:
            for seed in (19, 7):
                C[f'{bname}_c{c}_h{h}_s{seed}'] = scribe(base, langs, random.Random(seed * 1000 + 7), c, h)
    full = collections.OrderedDict((n, b3.battery(p, n, {})) for n, p in C.items())
    tol, marks = b3.score(full)
    held = [k for k, _ in b3.ITEMS if k not in TUNE]
    print('\n| corpus | tuning items matched (3) | held-out (34) | all (37) | held-out misses |\n|---|---|---|---|---|')
    for n in C:
        m = marks[n]
        print(f'| {n} | {sum(m[k] for k in TUNE)} | {sum(m[k] for k in held)} | {sum(m.values())} | ' + ', '.join(k for k in held if not m[k]) + ' |')
    json.dump({'best': best, 'full': full, 'tol': tol, 'marks': marks}, open(os.path.join(HERE, 'drift_results.json'), 'w'), indent=1, default=str)


if __name__ == '__main__':
    main()
