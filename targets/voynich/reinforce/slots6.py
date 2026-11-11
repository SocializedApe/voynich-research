"""Slot-level generator, sixth version: a shared transition rule times a context-free location habit, with a
length budget. (10 Nov 2026, second session)

slots4.py (independent slots) kept the scribe conventions and lost the word; slots5.py (chained slots, the context
level above the location levels) kept the word and half the convention: under a context level every (context,
language) restaurant draws its own convention, and independent draws average out of the marginal statistics. Two
changes, both taken from tests run first:
  - lengths.py: slot lengths compensate inside chain-context cells (r -0.22 opener/middle, -0.18 stem/ending); a
    context with a length class reproduces the word-length spread. Here: middle | last unit of the opener + opener
    length (0, 1, 2, 3+); ending | last unit of opener + middle + its length (0-1, 2, 3, 4, 5+).
  - product.py: held-out likelihood of the product P(v) x [P(v | context) / P(v)]^a x [P(v | location) / P(v)]^b
    against the tree orderings; exponents (a, b) chosen there on dev pages are used here unchanged.
Template rate: slots1-5 drew 20% of the middle's base draws from the trigram template (a hand-set number). Here the
rate is the Good-Turing estimate of a new middle type per token (middle types seen once / tokens), divided for the
tree variants by the share of tokens that reach the base distribution under the fit.

Variants, five seeds each:
  len5    control: slots5 (every slot a tree book > context > lang > hand > section > quire > page > line) with the
          length-class contexts and the Good-Turing template rate. What the length budget alone buys.
  prod6   opener and ending drawn from the product of two reinforced models (book > context) and (book > lang > hand
          > section > quire > page > line); middle as len5. Everything generated from fitted re-use strengths.
  prod6g  prod6 with the two exponents rescaled to sum to one (a logarithmic pool). Added after the dry run: with
          exponents summing to more than one the reinforcement of a product of two reinforced models is super-linear
          (an urn with exponent > 1) and the generation collapses onto a few values.
  prod6t  the book-wide transition tables P(v | context) are borrowed from Voynich (as the slot frequencies and the
          template always were) and only the location habit is generated: every slot is table x habit^b; a new
          middle from the template at the Good-Turing rate per token (not reinforced).
  prod6e  prod6t with the line end in the borrowed tables: the last word of a line draws its middle and ending from
          the tables of last words (lines/edges.py: the last word has its own vocabulary and endings).
Levels with fitted d >= 0.99 are dropped (slots3). P(v) in the ratios is the slot's Voynich frequency (the base
distribution of every model here). Scoring as slots5.py (b3 battery, held-out 30, scribe ratios, drift, coupling).

Run from targets/voynich: python reinforce/slots6.py fit <opener|middle|ending> | generate <variant> ... | report
"""
import collections, json, math, os, random, statistics, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..')
sys.path.insert(0, HERE); sys.path.insert(0, VOY); sys.path.insert(0, os.path.join(VOY, 'lines')); sys.path.insert(0, os.path.join(VOY, 'meaning'))
sys.path.insert(0, os.path.join(VOY, '..', '..', 'research', 'voynich_siblings'))
import hpy, common, b3_bakeoff as b3
import slots3, slots4, slots5
from slots import EMPTY, Mixture, coupling

LOC = ['book', 'lang', 'hand', 'section', 'quire', 'page', 'line']
CTX = ['book', 'context']
TREE = ['book', 'context', 'lang', 'hand', 'section', 'quire', 'page', 'line']
LEVELS = dict(ctx=CTX, loc=LOC, tree=TREE)
SWEEPS = int(os.environ.get('HPY_SWEEPS', '60'))
SEEDS = (19, 7, 3, 11, 23)
SLOTS = ('opener', 'middle', 'ending')
VARIANTS = ('len5', 'prod6', 'prod6g', 'prod6t', 'prod6e')
lu = slots5.last_unit


def nu(s):
    return len(common.units(s)) if s else 0


def S(x):
    return '' if x == EMPTY else x


def ctx_opener(prev_tail):
    return 'c' + slots3.ctx_of(prev_tail)


def ctx_middle(o):
    return 'c' + lu(o) + ':' + str(min(nu(o), 3))


def ctx_ending(o, m):
    return 'c' + lu(o + m) + ':' + str(min(max(nu(o + m), 1), 5))


def loc_of(p, li):
    return dict(book='book', lang='L' + p['lang'], hand='h' + p['hand'], section='s' + p['illus'], quire='q' + p['quire'], page=p['folio'], line=f'l{li}')


def data_for(pgs, edge=False):
    """slot -> list of (key dict incl. context, value); edge: the last word of a line gets '$' on its middle and
    ending contexts"""
    data = {s: [] for s in SLOTS}
    for p in pgs:
        for li, ln in enumerate(p['lines']):
            prev = None
            for wi, w in enumerate(ln['words']):
                o, m, e = slots4.split3(w); os_, ms, es = S(o), S(m), S(e)
                fl = '$' if edge and wi == len(ln['words']) - 1 else ''
                for s, c, v in (('opener', ctx_opener(prev), o), ('middle', ctx_middle(os_) + fl, m), ('ending', ctx_ending(os_, ms) + fl, e)):
                    k = loc_of(p, li); k['context'] = c; data[s].append((k, v))
                prev = (ms + es) or EMPTY
    return data


def fit(data, levels, g0, rng, sweeps):
    rows = [(tuple(k[l] for l in levels), v) for k, v in data]
    m = hpy.HPY([0.5] * len(levels), [1.0] * len(levels), g0)
    for path, v in rows:
        m.add(m.node(path), v, rng)
    order = list(range(len(rows))); hist = []
    for s in range(sweeps):
        rng.shuffle(order)
        for i in order:
            path, v = rows[i]; n = m.nodes[path]; m.remove(n, v, rng); m.add(n, v, rng)
        if s >= 10:
            m.resample_hyper(rng)
        hist.append((list(m.d), list(m.theta)))
    half = hist[len(hist) // 2:]
    d = [statistics.mean(h[0][i] for h in half) for i in range(len(levels))]
    th = [statistics.mean(h[1][i] for h in half) for i in range(len(levels))]
    tables = {l: sum(n.t for n in m.nodes.values() if n.level == i) for i, l in enumerate(levels)}
    custs = {l: sum(n.c for n in m.nodes.values() if n.level == i) for i, l in enumerate(levels)}
    return dict(levels=levels, d=d, theta=th, share_new_at_level={l: tables[l] / custs[l] for l in levels})


# ------------------------------------------------------------------------------------------------ generation
class PrunedHPY:
    """hpy.HPY (probabilities available) over the levels with fitted d < 0.99"""
    def __init__(self, fit_, g0):
        lv = fit_['levels']
        self.keep = [i for i, l in enumerate(lv) if fit_['d'][i] < 0.99 or i == 0]
        self.levels = [lv[i] for i in self.keep]
        self.m = hpy.HPY([fit_['d'][i] for i in self.keep], [fit_['theta'][i] for i in self.keep], g0)

    def node(self, keys):
        return self.m.node(tuple(keys[l] for l in self.levels))

    def realised(self):
        out = {}
        for i, l in enumerate(self.levels):
            t = sum(n.t for n in self.m.nodes.values() if n.level == i); c = sum(n.c for n in self.m.nodes.values() if n.level == i)
            out[l] = t / c if c else None
        return out


def pvec(m, node, idx, base):
    if node is None:
        return base
    pp = pvec(m, node.parent, idx, base)
    d, th = m.d[node.level], m.theta[node.level]
    v = (th + d * node.t) * pp
    for w, cw in node.cw.items():
        v[idx[w]] += cw - d * node.tw[w]
    return v / (th + node.c)


class Table:
    """borrowed book-wide transition table P(v | context), add-one-pseudocount towards the slot frequencies; a
    context never seen in Voynich backs off to its last-unit part, then to the slot frequencies"""
    def __init__(self, data, idx, base):
        self.base = base; cnt = collections.defaultdict(lambda: np.zeros(len(idx))); cnt2 = collections.defaultdict(lambda: np.zeros(len(idx)))
        for k, v in data:
            cnt[k['context']][idx[v]] += 1; cnt2[k['context'].split(':')[0]][idx[v]] += 1
        self.t = {c: (x + base) / (x.sum() + 1) for c, x in cnt.items()}; self.t2 = {c: (x + base) / (x.sum() + 1) for c, x in cnt2.items()}

    def vec(self, c):
        return self.t[c] if c in self.t else self.t2.get(c.split(':')[0], self.base)


class ProductSlot:
    def __init__(self, counts, ctx_part, loc_fit, a, b):
        self.vals = sorted(counts); self.idx = {v: i for i, v in enumerate(self.vals)}
        tot = sum(counts.values()); self.base = np.array([counts[v] / tot for v in self.vals]); g0 = {v: counts[v] / tot for v in self.vals}
        self.loc = PrunedHPY(loc_fit, g0); self.a, self.b = a, b
        self.ctx = PrunedHPY(ctx_part, g0) if isinstance(ctx_part, dict) else None
        self.table = None if isinstance(ctx_part, dict) else ctx_part
        self.lb = np.log(self.base)

    def bind(self, data):
        self.table = Table(data, self.idx, self.base)

    def draw(self, keys, rng):
        ln = self.loc.node(keys); pl = pvec(self.loc.m, ln, self.idx, self.base)
        if self.ctx is not None:
            cn = self.ctx.node(keys); pc = pvec(self.ctx.m, cn, self.idx, self.base)
        else:
            pc = self.table.vec(keys['context'])
        s = self.lb + self.a * (np.log(pc) - self.lb) + self.b * (np.log(pl) - self.lb)
        p = np.exp(s - s.max()); c = np.cumsum(p)
        v = self.vals[min(int(np.searchsorted(c, rng.random() * c[-1], side='right')), len(self.vals) - 1)]
        self.loc.m.add(ln, v, rng)
        if self.ctx is not None:
            self.ctx.m.add(cn, v, rng)
        return v


class TreeSlot:
    def __init__(self, fit_, g0):
        self.pr = slots3.Pruned(fit_['levels'], fit_, g0); self.levels = fit_['levels']

    def draw(self, keys, rng):
        return self.pr.draw(tuple(keys[l] for l in self.levels), rng)


def reach(fit_):
    """share of tokens that reach the base distribution under the fit (product of the shares passed up, kept levels)"""
    r = 1.0
    for i, l in enumerate(fit_['levels']):
        if fit_['d'][i] < 0.99 or i == 0:
            r *= fit_['share_new_at_level'][l]
    return r


def build(variant, ref, fits, weights, seed):
    words = [w for p in ref for ln in p['lines'] for w in ln['words']]
    counts = {s: collections.Counter(slots4.split3(w)[i] for w in words) for i, s in enumerate(SLOTS)}
    gt = sum(1 for v, c in counts['middle'].items() if c == 1) / len(words)
    tpl = hpy.Template(sorted(v for v in counts['middle'] if v != EMPTY), random.Random(seed + 100))
    info = dict(good_turing_new_middle=gt)
    if variant in ('len5', 'prod6', 'prod6g'):
        wt = min(1.0, gt / reach(fits['middle']['tree'])); info['template_share_of_base_draws'] = wt
        mid = TreeSlot(fits['middle']['tree'], Mixture(counts['middle'], tpl, wt, random.Random(seed + 51)))
    if variant == 'len5':
        op = TreeSlot(fits['opener']['tree'], Mixture(counts['opener'], None, 0.0, random.Random(seed + 50)))
        en = TreeSlot(fits['ending']['tree'], Mixture(counts['ending'], None, 0.0, random.Random(seed + 52)))
    elif variant in ('prod6', 'prod6g'):
        nz = (lambda a, b: (a / (a + b), b / (a + b))) if variant == 'prod6g' else (lambda a, b: (a, b))
        op = ProductSlot(counts['opener'], fits['opener']['ctx'], fits['opener']['loc'], *nz(*weights['opener']))
        en = ProductSlot(counts['ending'], fits['ending']['ctx'], fits['ending']['loc'], *nz(*weights['ending']))
    else:
        data = data_for(ref, edge=variant == 'prod6e')
        op = ProductSlot(counts['opener'], None, fits['opener']['loc'], 1.0, weights['opener'][1]); op.bind(data['opener'])
        mid = ProductSlot(counts['middle'], None, fits['middle']['loc'], 1.0, weights['middle'][1]); mid.bind(data['middle'])
        en = ProductSlot(counts['ending'], None, fits['ending']['loc'], 1.0, weights['ending'][1]); en.bind(data['ending'])
        mid.novel = (tpl, gt)
    return op, mid, en, info


def generate(variant, ref, fits, weights, seed):
    rng = random.Random(seed); op, mid, en, info = build(variant, ref, fits, weights, seed)
    out = []; novel = 0
    for p in ref:
        lines = []
        for li, ln in enumerate(p['lines']):
            prev = None; ws = []; k = loc_of(p, li)
            for wi in range(len(ln['words'])):
                fl = '$' if variant == 'prod6e' and wi == len(ln['words']) - 1 else ''
                k['context'] = ctx_opener(prev); o = S(op.draw(k, rng))
                k['context'] = ctx_middle(o) + fl
                if getattr(mid, 'novel', None) and rng.random() < mid.novel[1]:
                    m = mid.novel[0].sample() or EMPTY
                    if m in mid.idx:
                        mid.loc.m.add(mid.loc.node(k), m, rng)
                    else:
                        novel += 1
                    m = S(m)
                else:
                    m = S(mid.draw(k, rng))
                k['context'] = ctx_ending(o, m) + fl; e = S(en.draw(k, rng))
                w = o + m + e; ws.append(w if w else 'o'); prev = (m + e) or EMPTY
            lines.append({'words': ws, 'para_start': ln['para_start']})
        q = {key: p[key] for key in ('folio', 'hand', 'lang', 'quire', 'illus')}; q['lines'] = lines; out.append(q)
    info['novel_middle_tokens'] = novel
    real = {}
    for s, x in (('opener', op), ('middle', mid), ('ending', en)):
        if isinstance(x, ProductSlot):
            real[s] = dict(loc=x.loc.realised(), ctx=x.ctx.realised() if x.ctx is not None else None)
        else:
            real[s] = dict(tree=slots4.realised(x.pr))
    info['realised'] = real
    return out, info


def load_fits():
    return {s: json.load(open(os.path.join(HERE, f'slots6_fit_{s}.json'))) for s in SLOTS}


def load_weights():
    w = {}
    for s in SLOTS:
        f = os.path.join(HERE, f"product_heldout_voynich_{s}{'' if s == 'opener' else '_len'}.json")
        w[s] = json.load(open(f))['weights']
    return w


def sample(ref, seed, variant='prod6t'):
    return generate(variant, ref, load_fits(), load_weights(), seed)[0]


def length_stats(pgs):
    ws = [w for p in pgs for ln in p['lines'] for w in ln['words']]; L = [len(w) for w in ws]
    return dict(mean_chars=statistics.mean(L), sd_chars=statistics.pstdev(L), share_9plus=sum(1 for x in L if x >= 9) / len(L))


def main():
    mode = sys.argv[1]; t0 = time.time(); ref = common.pages()
    words = [w for p in ref for ln in p['lines'] for w in ln['words']]
    if mode == 'fit':
        s = sys.argv[2]; i = SLOTS.index(s); data = data_for(ref)[s]
        counts = collections.Counter(slots4.split3(w)[i] for w in words); tot = sum(counts.values()); g0 = {v: c / tot for v, c in counts.items()}
        out = {}
        for name in (('loc', 'tree') if s == 'middle' else ('ctx', 'loc', 'tree')):
            out[name] = fit(data, LEVELS[name], g0, random.Random(7), SWEEPS)
            print(f"{s} {name} {time.time() - t0:.0f}s d " + ' '.join(f'{x:.2f}' for x in out[name]['d']) + ' passed up '
                  + ' '.join(f"{out[name]['share_new_at_level'][l]:.2f}" for l in LEVELS[name]), flush=True)
            json.dump(out, open(os.path.join(HERE, f'slots6_fit_{s}.json'), 'w'), indent=1)
        return
    fits = load_fits(); weights = load_weights(); voc = set(words)
    if mode == 'generate':
        for variant in sys.argv[2:]:
            results = collections.OrderedDict(); meta = {}; extra = {}
            for seed in SEEDS:
                name = f'{variant}_s{seed}'; pgs, info = generate(variant, ref, fits, weights, seed)
                results[name] = b3.battery(pgs, name, extra)
                ntok = sum(len(ln['words']) for p in pgs for ln in p['lines'])
                info.update(scribe=hpy.scribe_ratios(pgs, random.Random(17)), drift=hpy.drift(pgs), coupling=coupling(pgs), lengths=length_stats(pgs),
                            voynich_types_share=sum(1 for p in pgs for ln in p['lines'] for w in ln['words'] if w in voc) / ntok,
                            types_per_token=len({w for p in pgs for ln in p['lines'] for w in ln['words']}) / ntok)
                meta[name] = info
                print(name, 'scored', f'{time.time() - t0:.0f}s', flush=True)
                json.dump(dict(results=results, meta=meta), open(os.path.join(HERE, f'slots6_gen_{variant}.json'), 'w'), indent=1)
        return
    R = hpy.reference(ref, os.path.join(HERE, 'reference_battery.json'))
    results = collections.OrderedDict(R); meta = {}
    for variant in VARIANTS:
        f = os.path.join(HERE, f'slots6_gen_{variant}.json')
        if os.path.exists(f):
            o = json.load(open(f)); results.update(o['results']); meta.update(o['meta'])
    meta['voynich_ZL'] = dict(scribe=hpy.scribe_ratios(ref, random.Random(17)), drift=hpy.drift(ref), coupling=coupling(ref), lengths=length_stats(ref),
                              voynich_types_share=1.0, types_per_token=len(voc) / len(words))
    tol, marks = b3.score(results)
    json.dump(dict(marks=marks, tol=tol, meta=meta, weights=weights), open(os.path.join(HERE, 'slots6_gen_results.json'), 'w'), indent=1)
    L = ['# Slot generator v6: transition rule x context-free location habit, with a length budget (10 Nov 2026)', '', 'Script `slots6.py` (variants in its docstring).',
         'Exponents (a context, b location) from product.py dev pages: ' + ', '.join(f'{s} {weights[s][0]}, {weights[s][1]}' for s in SLOTS) + '.', '']
    for s in SLOTS:
        for name, f in fits[s].items():
            L.append(f"- {s} {name}: d " + ', '.join(f'{x:.2f}' for x in f['d']) + '; passed up ' + ', '.join(f"{l} {f['share_new_at_level'][l]:.2f}" for l in f['levels']))
    L.append(''); L.append('Match rule as b3; held-out = the 30 items outside hybrid_model.TUNED_B3.'); L.append('')
    L.append('| text | matched/37 | held-out/30 | between scribes / within | same scribe other doc / within | JSD A vs B | JSD quire halves in cell | edge X within | edge X across line | Voynich types share | types/token | length sd (chars) | 9+ chars |')
    L.append('|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    for name in results:
        m = marks[name]; tot = sum(m.values()); held = sum(v for k, v in m.items() if k not in hpy.TUNED); md = meta.get(name)
        if md and 'scribe' in md:
            s = md['scribe']; dr = md['drift']; c = md['coupling']; ls = md['lengths']
            L.append(f"| {name} | {tot} | {held} | {s['between_ratio']:.2f} [{s['ci'][0]:.2f}-{s['ci'][1]:.2f}] | {s['same_ratio']:.2f} [{s['same_ci'][0]:.2f}-{s['same_ci'][1]:.2f}] | "
                     f"{dr['A_vs_B']:.3f} | {dr['quire_halves_within_cell']:.3f} ({dr['cells']}) | {c['within']:.4f} | {c['line_break']:.4f} | {md['voynich_types_share']:.2f} | {md['types_per_token']:.3f} | {ls['sd_chars']:.2f} | {ls['share_9plus']:.3f} |")
        else:
            L.append(f'| {name} | {tot} | {held} | | | | | | | | | | |')
    L.append(''); L.append('Realised share passed up (seed 19) against the fit:')
    for variant in VARIANTS:
        md = meta.get(f'{variant}_s19')
        if not md:
            continue
        for s in SLOTS:
            for part, r in md['realised'][s].items():
                if r:
                    L.append(f"- {variant} {s} {part}: " + ', '.join(f"{l} {v:.2f} (fit {fits[s][part]['share_new_at_level'][l]:.2f})" for l, v in r.items() if v is not None))
    L.append(''); L.append('Missed items per generated text (value vs Voynich):'); L.append('')
    for name in results:
        if name in R:
            continue
        miss = [f"{k} {b3.fmt(results[name][k])} vs {b3.fmt(results['voynich_ZL'][k])}" for k, _ in b3.ITEMS if not marks[name][k]]
        L.append(f'- {name}: ' + '; '.join(miss))
    L.append(''); L.append(f'Runtime {time.time() - t0:.0f} s.')
    open(os.path.join(HERE, 'slots6_gen.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L[:60]))


if __name__ == '__main__':
    main()
