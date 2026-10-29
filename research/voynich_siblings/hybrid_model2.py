"""Hybrid model, round 2: slow drift and opening-preserving copying.

Round 1 (hybrid_model.md) missed adjacent-page vocabulary similarity and the drift between manuscript halves (the
model drew page tables and null words independently per page) and halved the edge coupling (copies overwrote
chained openings). Changes:
  slow drift      each new page keeps the previous page's suffix tables and null words, except that with
                  probability R_T one suffix table is swapped for another and with probability R_N one null word is
                  replaced: a random walk through the book instead of independent pages.
  copy mode       'any' (round 1) or 'same_open': the scribe copies only from recent words whose first glyph unit
                  equals that of the cipher word he is about to write (if there is none, he writes the cipher word).

Protocol, fixed before any run (28 Oct 2026, this commit):
  TUNING items: round 1's ten (seven profile items, e_w10, g_gal_init, b_len_sd) plus j_jacc_excess and
                k_jsd_halves (now targeted).
  HELD-OUT items: the other 28 b3 items.
  Grid on tuning items, seed 19: R_T in (0.1, 0.3), R_N in (0.1, 0.3), copy mode in (any, same_open), Q in
  (0.15, 0.25); W = 8, E = 0.9, G = 0.2, M = 0.05 fixed (round-1 best). Best three -> b3 battery with seeds 19 and 7.

Run from the repository root:
  python research/voynich_siblings/hybrid_model2.py <naibbe_tables.csv> --grid
  python research/voynich_siblings/hybrid_model2.py <naibbe_tables.csv> --holdout "<rt>,<rn>,<mode>,<q>" [...]
"""
import itertools, math, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import cipher_models as cm, hybrid_model as h1, a4_selfcitation as a4, slot_independence as si
import b3_bakeoff as b3

TUNED_B3 = h1.TUNED_B3 | {'j_jacc_excess', 'k_jsd_halves'}
EXTRA_TARGET = dict(h1.EXTRA_TARGET, j_jacc_excess=0.037, k_jsd_halves=0.062)   # Voynich, fixed parse (b3)
W, E, G, M = 8, 0.9, 0.2, 0.05


class SlowVariant(cm.Variant):
    def __init__(self, *a, r_t=0.1, r_n=0.1, **k):
        super().__init__(*a, **k)
        self.r_t, self.r_n, self.started = r_t, r_n, False

    def new_page(self):
        if not self.started:
            self.active = self.rng.sample(cm.TABLES, self.k_page)
            self.null_words = self.rng.sample(sorted(set(self.glyph.values())), self.null_set)
            self.started = True
            return
        if self.rng.random() < self.r_t:
            out = [t for t in cm.TABLES if t not in self.active]
            self.active = self.active[:]; self.active[self.rng.randrange(len(self.active))] = self.rng.choice(out)
        if self.rng.random() < self.r_n:
            self.null_words = self.null_words[:]
            self.null_words[self.rng.randrange(len(self.null_words))] = self.rng.choice(sorted(set(self.glyph.values())))


def hybridize(pages, rng, q, mode):
    out = []
    for p in pages:
        hist, lines = [], []
        for ln in p['lines']:
            ws = []
            for i, tok in enumerate(ln['words']):
                if hist and rng.random() < q:
                    pool = hist[-W:]
                    if mode == 'same_open':
                        o = si.eva_units(tok)[0]
                        pool = [x for x in pool if si.eva_units(x)[0] == o]
                    if pool:
                        tok = rng.choice(pool)
                        if rng.random() < E:
                            tok = h1.edit(tok, rng)
                if i == 0 and rng.random() < G:
                    core = tok[2:] if tok.startswith('qo') else tok
                    tok = rng.choice('pftk') + (core[1:] if core[:1] in 'pftkoy' else core)
                ws.append(tok); hist.append(tok)
            lines.append({'words': ws, 'para_start': ln['para_start']})
        out.append({'folio': p.get('folio', ''), 'lines': lines})
    return out


def build(csv_path, seed, rt, rn, mode, q, skel, lat):
    v = SlowVariant(csv_path, seed, merge=M, r_t=rt, r_n=rn, **h1.BASE)
    return hybridize(cm.generate(v, lat, skel), random.Random(seed * 1000 + 11), q, mode)


def tune_profile(pages, rng):
    p = h1.tune_profile(pages, rng)
    extra = {}
    R = b3.battery(pages, 'x', extra)
    p.update(j_jacc_excess=R['j_jacc_excess'], k_jsd_halves=R['k_jsd_halves'])
    return p


def distance(p):
    t = dict(cm.TARGET, **EXTRA_TARGET)
    return sum(abs(p[k] - v) / abs(v) for k, v in t.items()) / len(t)


def main():
    csv_path = sys.argv[1]
    zl = a4.load_zl(); skel = a4.skeleton(zl)
    lat = os.path.join(HERE, '..', '..', 'lang', 'corpora', 'la-gutenberg.txt')
    rng = random.Random(97)
    keys = list(cm.TARGET) + list(EXTRA_TARGET)
    if '--grid' in sys.argv:
        vp = tune_profile(zl, rng)
        print('setting                      dist ' + ' '.join(f'{k[:9]:>9s}' for k in keys))
        print('Voynich                            ' + ' '.join(f'{vp[k]:9.3f}' for k in keys))
        res = []
        for rt, rn, mode, q in itertools.product((0.1, 0.3), (0.1, 0.3), ('any', 'same_open'), (0.15, 0.25)):
            p = tune_profile(build(csv_path, 19, rt, rn, mode, q, skel, lat), rng)
            d = distance(p); res.append((d, f'{rt},{rn},{mode},{q}'))
            print(f'{rt:.1f} {rn:.1f} {mode:9s} q {q:.2f}  {d:5.3f} ' + ' '.join(f'{p[k]:9.3f}' for k in keys), flush=True)
        res.sort()
        print('BEST3:', ' | '.join(f'{s} ({d:.3f})' for d, s in res[:3]))
    if '--holdout' in sys.argv:
        settings = sys.argv[sys.argv.index('--holdout') + 1:]
        corpora = {'voynich_ZL': zl, 'autocopist_s19': a4.Autocopist(19).generate(skel), 'autocopist_s7': a4.Autocopist(7).generate(skel),
                   'naibbe_latin': cm.generate(cm.Variant(csv_path, 19), lat, skel),
                   'hybrid1_best': h1.build(csv_path, 19, 0.15, 8, 0.9, 0.2, 0.05, skel, lat)}
        for i, s in enumerate(settings):
            rt, rn, mode, q = s.split(',')
            for seed in (19, 7):
                corpora[f'h2_{i}_s{seed}'] = build(csv_path, seed, float(rt), float(rn), mode, float(q), skel, lat)
        extra = {}
        results = {n: b3.battery(p, n, extra) for n, p in corpora.items()}
        tol, marks = b3.score(results)
        held = [k for k, _ in b3.ITEMS if k not in TUNED_B3]
        print(f'held-out items: {len(held)}')
        for n in corpora:
            p = cm.profile(corpora[n], rng)
            print(f'{n:16s} all {sum(marks[n].values()):2d}/37  held-out {sum(marks[n][k] for k in held):2d}/{len(held)}  edge {p["edge"]:.3f}  misses: ' +
                  ', '.join(k for k in held if not marks[n][k]))
        for i, s in enumerate(settings):
            print(f'h2_{i} = {s}')


if __name__ == '__main__':
    main()
