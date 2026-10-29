"""Test H1 of homophone_plan.md: a whole-word homophonic code whose homophones are chosen by habit.

Protocol (homophone_plan.md, fixed 29 Oct 2026; the points the plan left open were fixed here before any run):
  Plaintext: Pliny (pliny.STREAM books) for A pages and the Italian control (a4.IT) for B pages ('LI'); control 'LL':
    A and B pages both Pliny (A from token 0, B from token 50,000). Each (language, word) with >= 5 tokens gets K
    homophones, rarer words one. K = 8 for the grid and the pass rule (the K at which Latin's previous-word signal
    first reaches Voynich's, #25); K 4 and 16 reported at the chosen point as sensitivity only.
  Code-word vocabulary, both run:
    vocab     Voynich word types by rank: code slots taken in order of plaintext word frequency (pooled over both
              languages), each slot the next Voynich type by frequency; past Voynich's types, distinct improviser-template
              words (borrowed vocabulary, flagged as in #12)
    template  distinct improviser-template words (scribe_systems.Improviser, no habits), assigned at random
  Choice (per ZL page by its Davis hand and quire): per hand a preference Dirichlet(alpha_s) over each word's
    homophones; per (hand, quire) Dirichlet(alpha_q x the hand's preference), alpha_q inf = the hand's preference;
    within a page the last homophone of that word reused with probability rho, else a draw from the quire's preference.
    Then the copying scribe from duel.py (hybrid_model.hybridize, scribe_systems.SCRIBE), unchanged.
  Grid: alpha_s 0.1 / 0.5 / 2, alpha_q 5 / 20 / inf, rho 0 / 0.5 / 0.8, for each vocabulary x plaintext set-up
    (generator seed 0). Chosen on the scribe ratios only (hands 1-3, sum of squared log ratios to Voynich's, as duel.py).
  At each chosen point, generator seeds 0, 1, 2: scribe ratios, rules / habits (scribe_systems.rules_habits),
    k_jsd_halves (b3), distinct 3- and 4-word phrases occurring >= 2 times (first 30,000 tokens), previous-word signal
    (robustness.signal), b3 (37 items, both autocopists in the scoring set; 30 held out of the hybrid_model tuning).
  Pass rule (judged on LI at K 8, on the mean over the three seeds): both scribe ratios inside Voynich's intervals,
    3-word repeats 72-216, word signal 0.07-0.15, held-out b3 >= 26/30. Any missed: not a fit, reported as a trade-off.

Run from the repository root: python targets/voynich/meaning/habitcode.py
"""
import collections, contextlib, csv, io, itertools, json, math, os, random, statistics, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'research', 'voynich_siblings'))
import scribe_ratio as sr
import scribe_systems as ss
import robustness
import pliny
import a4_selfcitation as a4
import b3_bakeoff as b3
import hybrid_model as hm
from homclass import code_words, scribe
from variants import UNIT

GRID = list(itertools.product((0.1, 0.5, 2.0), (5.0, 20.0, math.inf), (0.0, 0.5, 0.8)))


class Codebook:
    def __init__(self, plains, K, vocab, allw, seed):
        rng = random.Random(seed)
        freq = collections.Counter((lang, w) for lang, ws in plains.items() for w in ws)
        self.ks = {k: (K if n >= 5 else 1) for k, n in freq.items()}
        need = sum(self.ks.values())
        if vocab == 'vocab':
            pool = [w for w, _ in collections.Counter(allw).most_common()]
            if need > len(pool):
                have = set(pool); extra = [w for w in code_words(allw, 2 * (need - len(pool)) + 1000, seed) if w not in have]
                pool += extra[:need - len(pool)]
        else:
            pool = code_words(allw, need, seed); rng.shuffle(pool)
        self.codes, i = {}, 0
        for k, _ in freq.most_common():
            self.codes[k] = pool[i:i + self.ks[k]]; i += self.ks[k]


def encode(zl, hand_of, quire_of, streams, book, a_s, a_q, rho, seed):
    rng = random.Random(seed); nrng = np.random.default_rng(seed); hpref, qpref = {}, {}
    def pref(k, h, q):
        if (k, h, q) not in qpref:
            hp = hpref.setdefault((k, h), nrng.dirichlet([a_s] * book.ks[k]))
            qp = hp if math.isinf(a_q) else nrng.dirichlet(np.maximum(a_q * hp, 1e-3))
            qpref[(k, h, q)] = qp / qp.sum()
        return qpref[(k, h, q)]
    pos = {g: 0 for g in streams}; pages = []
    for p in zl:
        g = 'B' if p['lang'] == 'B' else 'A'; lang, ws = streams[g]
        h, q = hand_of[p['folio']], quire_of[p['folio']]; last = {}; lines = []
        for ln in p['lines']:
            out = []
            for _ in ln['words']:
                k = (lang, ws[pos[g] % len(ws)]); pos[g] += 1; n = book.ks[k]
                if n == 1:
                    j = 0
                elif k in last and rng.random() < rho:
                    j = last[k]
                else:
                    j = int(nrng.choice(n, p=pref(k, h, q)))
                last[k] = j; out.append(book.codes[k][j])
            lines.append({'words': out, 'para_start': ln['para_start']})
        pages.append({'folio': p['folio'], 'lang': p['lang'], 'lines': lines})
    return scribe(pages)


def main():
    rng = random.Random(17)
    zl = b3.load_zl_lang(); hand_of = ss.page_hands(); allw = b3.words_of(zl); N = len(allw)
    quire_of = {}
    for r in csv.DictReader(open(ss.TSV, encoding='utf-8'), delimiter='\t'):
        quire_of.setdefault(r['folio'], r['quire'])
    la = [w for b in pliny.STREAM for c in pliny.chapters(b) for w in pliny.latin_words(c)]; it = a4.gutenberg_words(a4.IT)
    nA = sum(len(ln['words']) for p in zl if p['lang'] != 'B' for ln in p['lines']); nB = N - nA
    SET = {'LI': {'A': ('la', la[:nA]), 'B': ('it', it[:nB])}, 'LL': {'A': ('la', la[:nA]), 'B': ('la', la[50000:50000 + nB])}}
    ratio = lambda n, p: sr.analyse(n, sr.docs_of(ss.by_hand(p, hand_of)), UNIT.findall, rng)
    v = ratio('voynich', zl)
    def dist(r):
        return math.log(r['between_ratio'] / v['between_ratio']) ** 2 + math.log(r['same_ratio'] / v['same_ratio']) ** 2
    books = {}
    def book(setup, vocab, K, seed=0):
        key = (setup, vocab, K, seed)
        if key not in books:
            st = SET[setup]; plains = collections.defaultdict(list)
            for lang, ws in st.values():
                plains[lang] += ws
            books[key] = Codebook(plains, K, vocab, allw, 11 + seed)
        return books[key]

    G = {}; chosen = {}
    for setup in ('LI', 'LL'):
        for vocab in ('vocab', 'template'):
            print(f'\ngrid {setup} {vocab} K 8', flush=True)
            for a_s, a_q, rho in GRID:
                n = f'{setup}_{vocab}_{a_s}_{a_q}_{rho}'
                with contextlib.redirect_stdout(io.StringIO()):
                    r = ratio(n, encode(zl, hand_of, quire_of, SET[setup], book(setup, vocab, 8), a_s, a_q, rho, 0))
                G[n] = {'between': r['between_ratio'], 'same': r['same_ratio'], 'dist': dist(r)}
                print(f"{n:34s} between {r['between_ratio']:.2f}  same {r['same_ratio']:.2f}  dist {G[n]['dist']:.3f}", flush=True)
            best = min((x for x in GRID), key=lambda x: G[f'{setup}_{vocab}_{x[0]}_{x[1]}_{x[2]}']['dist'])
            chosen[(setup, vocab)] = best; print('chosen:', best, flush=True)

    T = collections.OrderedDict()
    for (setup, vocab), (a_s, a_q, rho) in chosen.items():
        for seed in (0, 1, 2):
            T[f'{setup}_{vocab}_K8_s{seed}'] = encode(zl, hand_of, quire_of, SET[setup], book(setup, vocab, 8, seed), a_s, a_q, rho, seed)
        if setup == 'LI':
            for K in (4, 16):
                T[f'{setup}_{vocab}_K{K}_s0'] = encode(zl, hand_of, quire_of, SET[setup], book(setup, vocab, K), a_s, a_q, rho, 0)
    R = collections.OrderedDict()
    print('\nmeasures', flush=True)
    for n, p in itertools.chain([('voynich', zl)], T.items()):
        ws = b3.words_of(p)[:30000]; r = {}
        r['ratio'] = v if n == 'voynich' else ratio(n, p)
        r['rules'], r['habits'] = ss.rules_habits(ss.by_hand(p, hand_of), UNIT.findall, random.Random(5))
        r['rep3'] = sum(c >= 2 for c in collections.Counter(tuple(ws[i:i + 3]) for i in range(len(ws) - 2)).values())
        r['rep4'] = sum(c >= 2 for c in collections.Counter(tuple(ws[i:i + 4]) for i in range(len(ws) - 3)).values())
        r['signal'] = robustness.signal(p)
        R[n] = r
        print(f"{n:24s} between {r['ratio']['between_ratio']:.2f} same {r['ratio']['same_ratio']:.2f}  rules {r['rules']:.3f} "
              f"habits {r['habits']:+.3f}  rep3 {r['rep3']} rep4 {r['rep4']}  signal {r['signal']:+.3f}", flush=True)
    skel = a4.skeleton(zl)
    B = collections.OrderedDict(); B['voynich_ZL'] = zl
    B['autocopist_s19'] = a4.Autocopist(19).generate(skel); B['autocopist_s7'] = a4.Autocopist(7).generate(skel)
    B.update(T)
    full = collections.OrderedDict()
    for n, p in B.items():
        with contextlib.redirect_stdout(io.StringIO()):
            full[n] = b3.battery(p, n, {})
    tol, marks = b3.score(full)
    held = [k for k, _ in b3.ITEMS if k not in hm.TUNED_B3]
    R['voynich']['k_jsd'] = full['voynich_ZL']['k_jsd_halves']
    for n in T:
        R[n]['k_jsd'] = full[n]['k_jsd_halves']; R[n]['b3'] = sum(marks[n].values()); R[n]['held'] = sum(marks[n][k] for k in held)

    print('\n| text | between / same scribe | rules / habits | k_jsd_halves | 3- / 4-word repeats | word signal | b3 | held-out |')
    print('|---|---|---|---|---|---|---|---|')
    for n, r in R.items():
        print(f"| {n} | {r['ratio']['between_ratio']:.2f} / {r['ratio']['same_ratio']:.2f} | {r['rules']:.3f} / {r['habits']:+.3f} | "
              f"{r['k_jsd']:.3f} | {r['rep3']} / {r['rep4']} | {r['signal']:+.3f} | {r.get('b3', '')} | {r.get('held', '')} |")
    print(f"\nVoynich intervals: between {v['ci']}, same {v['same_ci']}")
    verdict = {}
    for (setup, vocab), pt in chosen.items():
        rs = [R[f'{setup}_{vocab}_K8_s{s}'] for s in (0, 1, 2)]
        m = lambda f: statistics.mean(f(r) for r in rs)
        c = {'between': v['ci'][0] <= m(lambda r: r['ratio']['between_ratio']) <= v['ci'][1],
             'same': v['same_ci'][0] <= m(lambda r: r['ratio']['same_ratio']) <= v['same_ci'][1],
             'rep3': 72 <= m(lambda r: r['rep3']) <= 216, 'signal': 0.07 <= m(lambda r: r['signal']) <= 0.15,
             'b3_held': m(lambda r: r['held']) >= 26}
        verdict[f'{setup}_{vocab}'] = {'point': pt, 'checks': c, 'fit': all(c.values())}
        print(f"{setup} {vocab} at alpha_s/alpha_q/rho {pt}: " + ('FIT' if all(c.values()) else 'no: ' + ', '.join(k for k, ok in c.items() if not ok))
              + ('' if setup == 'LI' else '  (control, not judged)'))
    print('held-out misses:', {n: [k for k in held if not marks[n][k]] for n in T if n.endswith('K8_s0')})
    json.dump({'grid': G, 'chosen': {f'{a}_{b}': c for (a, b), c in chosen.items()}, 'R': R, 'verdict': verdict,
               'b3': full, 'marks': marks, 'held': held}, open(os.path.join(HERE, 'habitcode_results.json'), 'w'), indent=1, default=str)


if __name__ == '__main__':
    main()
