"""The duel within one shared system: a cipher whose scribes have habits against the template improviser.

Protocol, fixed before any run (28 Oct 2026; follows #28, scribe_systems.py):
  Both texts fill the ZL skeleton page by page, each page by its own Davis hand, and both pass through the same copying
  scribe (hybrid_model.hybridize, q 0.15, w 8, e 0.9, g 0.2).
  cipher_habit_<s>_<p>  round-8 (hybrid_model.BASE, Greshko's tables shared by all), each hand enciphering its own
                        stretch of Latin. Habits act on the cipher's free choices: every free table draw (opening
                        table when the chaining rule does not fire, every suffix table) has its weight multiplied by
                        exp(s z) per hand and exp(p z) per page, z ~ N(0,1) drawn once per (hand or page, role,
                        plaintext unit, table). Grid s 0.5/1.0/2.0, p 0.3/0.6/1.0.
  improv_<s>_<p>        scribe_systems.Improviser (template borrowed from Voynich), grid s 1.0/1.5, p 0.4/0.7/1.0
                        (past the earlier grid edge).
  cipher_scribe         the reference: round-8 + the same copying scribe, no habits (s = p = 0).
  Choice: on each side, the grid point closest to Voynich's two scribe ratios (hands 1-3, sum of squared log ratios),
  on those ratios only. Then rules/habits (scribe_systems.rules_habits) and the b3 battery (both autocopists in the
  scoring set; 30 items held out of the hybrid_model tuning).
  Rule: the side with more held-out b3 items wins if it leads by 2 or more; otherwise undecided. A side whose two
  ratios are not both inside Voynich's intervals is reported as failing the scribe test whatever its b3 count.

Run from the repository root: python targets/voynich/meaning/duel.py <naibbe_tables.csv>
"""
import collections, contextlib, io, json, math, os, random, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'research', 'voynich_siblings'))
import scribe_ratio as sr
import scribe_systems as ss
import a4_selfcitation as a4
import b3_bakeoff as b3
import hybrid_model as hm
import cipher_models as cm
from variants import UNIT

C_GRID = [(s, p) for s in (0.5, 1.0, 2.0) for p in (0.3, 0.6, 1.0)]
I_GRID = [(s, p) for s in (1.0, 1.5) for p in (0.4, 0.7, 1.0)]


class HabitVariant(cm.Variant):
    def __init__(self, csv_path, seed, s, p):
        super().__init__(csv_path, seed, merge=0.0, **hm.BASE)
        self.s, self.p, self.hrng = s, p, random.Random(seed * 31 + 1)
        self.hf, self.pf, self.cur = {}, {}, None

    def new_page(self):
        super().new_page(); self.pf = {}

    def fac(self, store, key, sigma):
        if key not in store:
            store[key] = {t: math.exp(sigma * self.hrng.gauss(0, 1)) for t in cm.TABLES}
        return store[key]

    def pick(self, last, role='open'):
        pool = cm.TABLES if (self.split and role == 'open') else self.active
        if self.chain and role == 'open' and last is not None and self.rng.random() < self.p_chain:
            i = self.chain_map.get(last[-1])
            if i is not None:
                return pool[i % len(pool)]
        key = (role, self.cur); f1 = self.fac(self.hf, key, self.s); f2 = self.fac(self.pf, key, self.p)
        return self.rng.choices(pool, weights=[self.WEIGHTS[False][t] * f1[t] * f2[t] for t in pool])[0]

    def encrypt_units(self, units, last):
        out = []
        for u in units:
            self.cur = u; ws, last = super().encrypt_units([u], last); out += ws
        return out, last


def cipher_habit(zl, hand_of, csv_path, plain, s, p):
    out = {}
    for i, h in enumerate(sorted({hand_of[x['folio']] for x in zl})):
        pg = [x for x in zl if hand_of[x['folio']] == h]
        for a, q in zip(pg, cm.generate(HabitVariant(csv_path, 19 + i, s, p), plain[h], a4.skeleton(pg))):
            out[a['folio']] = {'folio': a['folio'], 'lang': a['lang'], 'lines': q['lines']}
    pages = [out[x['folio']] for x in zl]
    q, w, e, g = ss.SCRIBE
    res = hm.hybridize(pages, random.Random(7), q, w, e, g)
    for a, b in zip(res, pages):
        a['lang'] = b['lang']
    return res


def main():
    csv_path = sys.argv[1]; rng = random.Random(17)
    zl = b3.load_zl_lang(); hand_of = ss.page_hands()
    la = a4.gutenberg_words(os.path.join(ROOT, 'lang', 'corpora', 'la-gutenberg.txt')); tmp = tempfile.mkdtemp(); plain = {}
    for i, h in enumerate(sorted(set(hand_of.values()))):
        ws = la[i * 12000:(i + 1) * 12000]; plain[h] = os.path.join(tmp, f'{h if h != "?" else "x"}.txt')
        open(plain[h], 'w', encoding='utf-8').write('\n'.join(' '.join(ws[k:k + 12]) for k in range(0, len(ws), 12)))
    ratio = lambda n, p: sr.analyse(n, sr.docs_of(ss.by_hand(p, hand_of)), UNIT.findall, rng)
    T, R = collections.OrderedDict(), {}
    T['voynich'] = zl; R['voynich'] = {'ratio': ratio('voynich', zl)}
    v = R['voynich']['ratio']
    def dist(n):
        r = R[n]['ratio']; return math.log(r['between_ratio'] / v['between_ratio']) ** 2 + math.log(r['same_ratio'] / v['same_ratio']) ** 2
    T['cipher_scribe'] = cipher_habit(zl, hand_of, csv_path, plain, 0.0, 0.0); R['cipher_scribe'] = {'ratio': ratio('cipher_scribe', T['cipher_scribe'])}
    for s, p in C_GRID:
        n = f'cipher_habit_{s}_{p}'; T[n] = cipher_habit(zl, hand_of, csv_path, plain, s, p); R[n] = {'ratio': ratio(n, T[n])}
    allw = b3.words_of(zl)
    for s, p in I_GRID:
        n = f'improv_{s}_{p}'; T[n] = ss.Improviser(allw, s, p, 23).text(zl, hand_of); R[n] = {'ratio': ratio(n, T[n])}
    best_c = min((n for n in T if n.startswith('cipher_habit')), key=dist)
    best_i = min((n for n in T if n.startswith('improv_')), key=dist)
    print('chosen:', best_c, best_i, flush=True)
    show = ['voynich', 'cipher_scribe', best_c, best_i]
    for n in show:
        r = R[n]['ratio']
        R[n]['inside'] = v['ci'][0] <= r['between_ratio'] <= v['ci'][1] and v['same_ci'][0] <= r['same_ratio'] <= v['same_ci'][1]
        R[n]['rules'], R[n]['habits'] = ss.rules_habits(ss.by_hand(T[n], hand_of), UNIT.findall, rng)
        print(f"{n:24s} rules {R[n]['rules']:.3f} habits {R[n]['habits']:+.3f}", flush=True)
    skel = a4.skeleton(zl)
    B = collections.OrderedDict(); B['voynich_ZL'] = zl
    B['autocopist_s19'] = a4.Autocopist(19).generate(skel); B['autocopist_s7'] = a4.Autocopist(7).generate(skel)
    for n in show[1:]:
        B[n] = T[n]
    full = collections.OrderedDict()
    for n, p in B.items():
        with contextlib.redirect_stdout(io.StringIO()):
            full[n] = b3.battery(p, n, {})
    tol, marks = b3.score(full)
    held = [k for k, _ in b3.ITEMS if k not in hm.TUNED_B3]
    print('\n| text | between / within | same scribe / within | inside Voynich CI | rules | habits | b3 (37) | held-out (30) | held-out misses |')
    print('|---|---|---|---|---|---|---|---|---|')
    for n in show:
        r = R[n]['ratio']; m = marks.get('voynich_ZL' if n == 'voynich' else n)
        b3s = ' | | ' if n == 'voynich' else f"{sum(m.values())} | {sum(m[k] for k in held)} | " + ', '.join(k for k in held if not m[k])
        R[n]['b3_all'] = None if n == 'voynich' else sum(m.values()); R[n]['b3_held'] = None if n == 'voynich' else sum(m[k] for k in held)
        print(f"| {n} | {r['between_ratio']:.2f} [{r['ci'][0]:.2f}-{r['ci'][1]:.2f}] | {r['same_ratio']:.2f} [{r['same_ci'][0]:.2f}-{r['same_ci'][1]:.2f}] | "
              f"{'yes' if R[n]['inside'] else 'no'} | {R[n]['rules']:.3f} | {R[n]['habits']:+.3f} | {b3s} |")
    print('\ngrid (between, same):', {n: (round(R[n]['ratio']['between_ratio'], 2), round(R[n]['ratio']['same_ratio'], 2)) for n in T if n != 'voynich'})
    hc, hi = R[best_c]['b3_held'], R[best_i]['b3_held']
    verdict = 'cipher with habits' if hc - hi >= 2 else 'improviser' if hi - hc >= 2 else 'undecided'
    print(f'\nverdict by the pre-set rule: {verdict} (held-out {hc} vs {hi})')
    json.dump({'R': R, 'best': [best_c, best_i], 'verdict': verdict, 'b3': full, 'marks': marks, 'held': held},
              open(os.path.join(HERE, 'duel_results.json'), 'w'), indent=1, default=str)


if __name__ == '__main__':
    main()
