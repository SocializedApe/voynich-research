"""Candidate 1: a context-sensitive copier (pure generator, no plaintext).

Each word is a copy of a recent word (the last W words on the page, plus the last CARRY words of the previous page so
that habits run on through the book), edited with probability E (hybrid_model.edit); with probability F a fresh word
is made from slot parts (a4.Rugg prefix / midfix / suffix lists). The context rule: a candidate source word c gets
weight 1 + K if the word that preceded c ended in the same glyph unit as the word just written, else 1. With K = 0 it
is a plain copier (the control); with K > 0 boundary habits emerge and propagate without any table. Lines open with a
gallows-led variant with probability G = 0.2 (as the hybrid).

Protocol, fixed before any run (28 Oct 2026, this commit):
  Tuning: the hybrid's ten items (cipher_models.TARGET + e_w10, g_gal_init, b_len_sd); grid F in (0.05, 0.15),
          K in (0, 4, 16), W in (10, 30), E in (0.5, 0.9), CARRY in (0, 50); seed 19.
  Test 1, battery: best three settings, seeds 19 and 7, b3 battery, matches on the 30 held-out items (as hybrid
          round 1, whose best scored 23-26).
  Test 2, copy split: copy_split_test measure on the same six runs (Voynich: near-copy share 0.256, ratio 0.76).
  Decision: candidate 1 SURVIVES if, for at least two of the six runs, held-out >= 23 AND near-copy share >= 0.20
          AND ratio other/copy < 1. It FAILS if no run has ratio < 1 with share >= 0.20. Otherwise undecided.
          The K = 0 control is reported alongside (best setting with K forced to 0).

Run from the repository root:
  python research/voynich_siblings/candidate1.py --grid
  python research/voynich_siblings/candidate1.py --test "<F>,<K>,<W>,<E>,<CARRY>" [...]
"""
import itertools, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import cipher_models as cm, hybrid_model as h1, copy_split_test as cs, slot_independence as si, a4_selfcitation as a4
import b3_bakeoff as b3

G = 0.2
PRE = [p for p in a4.Rugg.PRE if p] + [''] * 3
MID = [m for m in a4.Rugg.MID if m] + [''] * 3
SUF = [s for s in a4.Rugg.SUF if s]


def last_unit(w):
    return si.eva_units(w)[-1]


def generate(skel, seed, F, K, W, E, CARRY):
    rng = random.Random(seed)
    def fresh():
        w = rng.choice(PRE) + rng.choice(MID) + rng.choice(SUF)
        return w or 'daiin'
    pages, carry = [], []          # carry: list of (word, predecessor-last-unit)
    for pl in skel:
        hist = carry[-CARRY:] if CARRY else []
        lines = []
        prev = None
        for (n, _, ps) in pl:
            ws = []
            for i in range(n):
                cand = hist[-(W + (CARRY if not ws and not lines else 0)):]
                if not cand or rng.random() < F:
                    w = fresh()
                else:
                    pu = last_unit(prev) if prev else None
                    weights = [1 + (K if (pu is not None and c[1] == pu) else 0) for c in cand]
                    w = rng.choices(cand, weights=weights)[0][0]
                    if rng.random() < E:
                        w = h1.edit(w, rng)
                if i == 0 and rng.random() < G:
                    core = w[2:] if w.startswith('qo') else w
                    w = rng.choice('pftk') + (core[1:] if core[:1] in 'pftkoy' else core) or 'tol'
                hist.append((w, last_unit(prev) if prev else None))
                ws.append(w); prev = w
            lines.append({'words': ws, 'para_start': ps})
        pages.append({'folio': '', 'lines': lines})
        carry = hist
    return pages


def main():
    zl = a4.load_zl(); skel = a4.skeleton(zl)
    rng = random.Random(127)
    keys = list(cm.TARGET) + list(h1.EXTRA_TARGET)
    if '--grid' in sys.argv:
        print('F    K  W  E   C    dist ' + ' '.join(f'{k[:9]:>9s}' for k in keys))
        res = []
        for F, K, W, E, C in itertools.product((0.05, 0.15), (0, 4, 16), (10, 30), (0.5, 0.9), (0, 50)):
            p = h1.tune_profile(generate(skel, 19, F, K, W, E, C), rng)
            d = h1.distance(p); res.append((d, f'{F},{K},{W},{E},{C}'))
            print(f'{F:.2f} {K:2d} {W:2d} {E:.1f} {C:2d}  {d:5.3f} ' + ' '.join(f'{p[k]:9.3f}' for k in keys), flush=True)
        res.sort()
        print('BEST3:', ' | '.join(f'{s} ({d:.3f})' for d, s in res[:3]))
        k0 = sorted(r for r in res if r[1].split(',')[1] == '0')[0]
        print('BEST K=0 CONTROL:', f'{k0[1]} ({k0[0]:.3f})')
    if '--test' in sys.argv:
        settings = sys.argv[sys.argv.index('--test') + 1:]
        corpora = {'voynich_ZL': zl, 'autocopist_s19': a4.Autocopist(19).generate(skel), 'autocopist_s7': a4.Autocopist(7).generate(skel)}
        for i, s in enumerate(settings):
            F, K, W, E, C = s.split(',')
            for seed in (19, 7):
                corpora[f'c1_{i}_s{seed}'] = generate(skel, seed, float(F), int(K), int(W), float(E), int(C))
        extra = {}
        results = {n: b3.battery(p, n, extra) for n, p in corpora.items()}
        tol, marks = b3.score(results)
        held = [k for k, _ in b3.ITEMS if k not in h1.TUNED_B3]
        print(f'held-out items: {len(held)}')
        print(f'{"run":16s} {"held-out":>8s} {"copy share":>10s} {"ratio":>6s} {"edge":>6s}  misses')
        for n, pages in corpora.items():
            cp, nc = cs.groups(pages)
            c1, c2 = cs.coupling(cp, rng), cs.coupling(nc, rng)
            p = cm.profile(pages, rng)
            print(f'{n:16s} {sum(marks[n][k] for k in held):8d} {len(cp) / (len(cp) + len(nc)):10.3f} {c2 / c1 if c1 > 0 else float("inf"):6.2f} {p["edge"]:6.3f}  ' +
                  ', '.join(k for k in held if not marks[n][k]), flush=True)
        for i, s in enumerate(settings):
            print(f'c1_{i} = F,K,W,E,CARRY {s}')


if __name__ == '__main__':
    main()
