"""A convention layer: one shared system, rewritten slot by slot toward Currier A or B, with a weaker drift per quire.

Protocol, fixed before any run (28 Oct 2026; follows #33 and #35):
  Bases (ZL skeleton by hand, as in duel.py): cipher_scribe (round-8, Greshko's tables, copying scribe; the best b3
  model of the duel) and improviser s 0.6, p 0.2 (scribe_systems.Improviser, mild habits).
  Layer: every word type is parsed into prefix + gallows + middle + ending (slots_ab.parse). On A pages it is rewritten
  toward Voynich's A slot distributions, on B pages toward B's; other pages unchanged. Slots in order, each redrawn
  with probability lam: prefix ~ P_G(prefix); gallows ~ P_G(gallows | prefix); middle ~ P_G(middle | gallows);
  ending ~ P_G(ending | last letter before it). The draw is fixed per (word type, group), so repeats and copies stay
  repeats. Quire drift: a second rewrite with probability lam_q, fixed per (word type, group, quire), on top.
  Grid lam 0.3/0.6/1.0, lam_q 0/0.15/0.3, for each base.
  The layer's targets come from Voynich's own A and B pages: a match on A/B items is partly built in. The question is
  whether one model can carry the convention and keep the word statistics and the scribe structure together.
  Choice: per base, the grid point closest to Voynich's two scribe ratios (hands 1-3), on those ratios only.
  Success: both ratios inside Voynich's intervals, k_jsd_halves matched, and held-out b3 items not below the same base
  without the layer (scored in the same run).

Run from the repository root: python targets/voynich/meaning/convention.py <naibbe_tables.csv>
"""
import collections, contextlib, csv, io, json, math, os, random, sys, tempfile, zlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'research', 'voynich_siblings'))
import scribe_ratio as sr
import scribe_systems as ss
import duel
import slots_ab
import a4_selfcitation as a4
import b3_bakeoff as b3
import hybrid_model as hm
from variants import UNIT

GRID = [(l, q) for l in (0.3, 0.6, 1.0) for q in (0.0, 0.15, 0.3)]


class Layer:
    def __init__(self, zl):
        self.P = {}
        for g in ('A', 'B'):
            toks = [slots_ab.parse(w) for p in zl if p['lang'] == g for ln in p['lines'] for w in ln['words']]
            d = {'prefix': collections.Counter(), 'gallows': collections.defaultdict(collections.Counter),
                 'middle': collections.defaultdict(collections.Counter), 'ending': collections.defaultdict(collections.Counter)}
            for t in toks:
                d['prefix'][t['prefix']] += 1; d['gallows'][t['prefix']][t['gallows']] += 1
                d['middle'][t['gallows']][t['middle']] += 1
                stem = t['prefix'] + (t['gallows'] if t['gallows'] != '-' else '') + t['middle']
                d['ending'][stem[-1:]][t['ending']] += 1
            self.P[g] = d
        self.cache = {}

    @staticmethod
    def draw(counter, rng):
        vals = list(counter); return rng.choices(vals, weights=[counter[v] for v in vals])[0] if vals else None

    def rewrite(self, w, g, lam, key):
        k = (w, g, lam, key)
        if k not in self.cache:
            rng = random.Random(zlib.crc32(repr(k).encode())); t = slots_ab.parse(w); d = self.P[g]
            if rng.random() < lam:
                t['prefix'] = self.draw(d['prefix'], rng)
            if rng.random() < lam:
                t['gallows'] = self.draw(d['gallows'][t['prefix']], rng) or t['gallows']
            if rng.random() < lam:
                t['middle'] = self.draw(d['middle'][t['gallows']], rng) or ''
            stem = t['prefix'] + (t['gallows'] if t['gallows'] != '-' else '') + t['middle']
            if rng.random() < lam:
                e = self.draw(d['ending'][stem[-1:]], rng); t['ending'] = e if e is not None else t['ending']
            out = stem + t['ending']
            self.cache[k] = out or w
        return self.cache[k]

    def apply(self, pages, quire_of, lam, lam_q):
        out = []
        for p in pages:
            g = p['lang']
            lines = []
            for ln in p['lines']:
                ws = ln['words']
                if g in ('A', 'B'):
                    ws = [self.rewrite(w, g, lam, '') for w in ws]
                    if lam_q:
                        ws = [self.rewrite(w, g, lam_q, quire_of[p['folio']]) for w in ws]
                lines.append({'words': ws, 'para_start': ln['para_start']})
            out.append({'folio': p['folio'], 'lang': g, 'lines': lines})
        return out


def main():
    csv_path = sys.argv[1]; rng = random.Random(17)
    zl = b3.load_zl_lang(); hand_of = ss.page_hands()
    quire_of = {}
    for r in csv.DictReader(open(ss.TSV, encoding='utf-8'), delimiter='\t'):
        quire_of.setdefault(r['folio'], r['quire'])
    la = a4.gutenberg_words(os.path.join(ROOT, 'lang', 'corpora', 'la-gutenberg.txt')); tmp = tempfile.mkdtemp(); plain = {}
    for i, h in enumerate(sorted(set(hand_of.values()))):
        ws = la[i * 12000:(i + 1) * 12000]; plain[h] = os.path.join(tmp, f'{h if h != "?" else "x"}.txt')
        open(plain[h], 'w', encoding='utf-8').write('\n'.join(' '.join(ws[k:k + 12]) for k in range(0, len(ws), 12)))
    bases = {'cipher_scribe': duel.cipher_habit(zl, hand_of, csv_path, plain, 0.0, 0.0),
             'improv_0.6_0.2': ss.Improviser(b3.words_of(zl), 0.6, 0.2, 23).text(zl, hand_of)}
    layer = Layer(zl)
    ratio = lambda n, p: sr.analyse(n, sr.docs_of(ss.by_hand(p, hand_of)), UNIT.findall, rng)
    T, R = collections.OrderedDict(), {}
    T['voynich'] = zl; R['voynich'] = ratio('voynich', zl); v = R['voynich']
    for b, p in bases.items():
        T[b] = p; R[b] = ratio(b, p)
        for lam, lq in GRID:
            n = f'{b}+layer_{lam}_{lq}'; T[n] = layer.apply(p, quire_of, lam, lq); R[n] = ratio(n, T[n])
    def dist(n):
        r = R[n]; return math.log(r['between_ratio'] / v['between_ratio']) ** 2 + math.log(r['same_ratio'] / v['same_ratio']) ** 2
    chosen = [min((n for n in T if n.startswith(b + '+layer')), key=dist) for b in bases]
    print('chosen:', chosen, flush=True)
    show = list(bases) + chosen
    skel = a4.skeleton(zl)
    B = collections.OrderedDict(); B['voynich_ZL'] = zl
    B['autocopist_s19'] = a4.Autocopist(19).generate(skel); B['autocopist_s7'] = a4.Autocopist(7).generate(skel)
    for n in show:
        B[n] = T[n]
    full = collections.OrderedDict()
    for n, p in B.items():
        with contextlib.redirect_stdout(io.StringIO()):
            full[n] = b3.battery(p, n, {})
    tol, marks = b3.score(full)
    held = [k for k, _ in b3.ITEMS if k not in hm.TUNED_B3]
    rh = {n: ss.rules_habits(ss.by_hand(T[n], hand_of), UNIT.findall, random.Random(5)) for n in ['voynich'] + show}
    inside = lambda r: v['ci'][0] <= r['between_ratio'] <= v['ci'][1] and v['same_ci'][0] <= r['same_ratio'] <= v['same_ci'][1]
    print('\n| text | between / within | same scribe / within | inside CI | rules | habits | k_jsd_halves (Voynich) | b3 (37) | held-out (30) | held-out misses |')
    print('|---|---|---|---|---|---|---|---|---|---|')
    out = {}
    for n in ['voynich'] + show:
        r = R[n]; kj = full['voynich_ZL' if n == 'voynich' else n]['k_jsd_halves']
        if n == 'voynich':
            print(f"| voynich | {r['between_ratio']:.2f} [{r['ci'][0]:.2f}-{r['ci'][1]:.2f}] | {r['same_ratio']:.2f} [{r['same_ci'][0]:.2f}-{r['same_ci'][1]:.2f}] | yes | {rh[n][0]:.3f} | {rh[n][1]:+.3f} | {kj:.4f} | | | |")
            continue
        m = marks[n]; hs = sum(m[k] for k in held)
        out[n] = {'between': r['between_ratio'], 'same': r['same_ratio'], 'inside': inside(r), 'rules': rh[n][0], 'habits': rh[n][1],
                  'k_jsd_halves': kj, 'k_pass': m['k_jsd_halves'], 'b3': sum(m.values()), 'held': hs}
        print(f"| {n} | {r['between_ratio']:.2f} | {r['same_ratio']:.2f} | {'yes' if inside(r) else 'no'} | {rh[n][0]:.3f} | {rh[n][1]:+.3f} | "
              f"{kj:.4f} ({'pass' if m['k_jsd_halves'] else 'miss'}) | {sum(m.values())} | {hs} | " + ', '.join(k for k in held if not m[k]) + ' |')
    print('\ngrid (between, same):', {n: (round(R[n]['between_ratio'], 2), round(R[n]['same_ratio'], 2)) for n in T if '+layer' in n})
    for b, c in zip(bases, chosen):
        ok = out[c]['inside'] and out[c]['k_pass'] and out[c]['held'] >= out[b]['held']
        print(f'success by the pre-set rule, {b}: {"yes" if ok else "no"} (inside CI {out[c]["inside"]}, k_jsd_halves {out[c]["k_pass"]}, held-out {out[c]["held"]} vs base {out[b]["held"]})')
    json.dump({'ratios': R, 'out': out, 'chosen': chosen, 'b3': full, 'marks': marks, 'held': held},
              open(os.path.join(HERE, 'convention_results.json'), 'w'), indent=1, default=str)


if __name__ == '__main__':
    main()
