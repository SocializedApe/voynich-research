"""Slot generator v8: is the convention categorical, and does a page-to-page drift give the long-range clustering?
(11 Nov 2026, third session)

slots7.py drew the convention of each language, hand, section and quire as a normal log-tilt and got a quarter to a
half of the A/B difference and none of the clustering beyond the page (h_peak_R, j_jacc_excess, k_jsd_halves missed
by every seed). Two things were confounded there: the shape of the tilt (normal) and its strength (the tilt was
multiplied by the location exponent b = 0.75 of product.py although the sd was estimated for the full log-ratio).
Here b = 1 throughout and the shape is varied:
  P(v | context, location) proportional to T(v | context) x exp(sum over levels of t_level(v))
with T the borrowed tables of prod6e, copying of the opener and middle of one of the previous 10 words with
probability 0.1 (slots7), a new middle from the template at the Good-Turing rate.

Variants, five seeds each:
  norm8   t normal, sd per level by moments from Voynich (slots7.sigmas). Separates the effect of b from the shape.
  cat8    t = +s or -s (random sign) with probability pi, else 0, per value and node. pi and s per level and slot by
          moments from Voynich: with x = log((n + 0.5) / (e + 0.5)) for values with expected count e >= 5, m2 =
          weighted mean of x^2 - 1/e, m4 = weighted mean of x^4 - 6 m2 / e - 3 / e^2 (the sampling noise of x taken
          as normal with variance 1/e); s^2 = m4 / m2, pi = m2^2 / m4 (capped at 1). Which values are switched is
          random per seed.
  emp8    control, not a generator of the convention: t is Voynich's own x at every node (the borrowed convention).
          What a context-free convention can reach at all when it is the right one.
  cat8p   cat8 plus a page level that drifts: t_page = rho x t_previous page + sqrt(1 - rho^2) x sd_page x normal
          inside a quire, a fresh draw at a quire boundary. sd_page by moments as above; rho = weighted mean of
          x_page(v) x x_next page(v) over consecutive pages of a quire (weights sqrt(e e')), over sd_page^2, clipped
          to 0-0.95.
  emp8p   emp8 plus the same drawn page drift.
  lang8   control added after the first five were scored (emp8 reached three quarters of the A/B difference): emp8
          with the borrowed tables T(v | context) built separately for language A and B, in place of the language
          tilt. Tests whether the rest of the A/B difference sits in the chaining rule, not in slot frequencies.
Nothing is tuned on the battery; q = 0.1 is slots7's middle value. Scoring as slots6.py / slots7.py.

Run from targets/voynich: python reinforce/slots8.py generate <variant> ... | report
"""
import collections, json, math, os, random, statistics, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..')
sys.path.insert(0, HERE); sys.path.insert(0, VOY); sys.path.insert(0, os.path.join(VOY, 'lines')); sys.path.insert(0, os.path.join(VOY, 'meaning'))
sys.path.insert(0, os.path.join(VOY, '..', '..', 'research', 'voynich_siblings'))
import hpy, common, b3_bakeoff as b3
import slots4, slots6
from slots import EMPTY, coupling

LV = ['lang', 'hand', 'section', 'quire']
SEEDS = (19, 7, 3, 11, 23)
SLOTS = slots6.SLOTS
VARIANTS = collections.OrderedDict([('norm8', ('norm', False)), ('cat8', ('cat', False)), ('emp8', ('emp', False)), ('cat8p', ('cat', True)), ('emp8p', ('emp', True)), ('lang8', ('lang', False))])
Q = 0.1
S = slots6.S


def node_counts(data, levels):
    cnt = collections.defaultdict(collections.Counter)
    for k, v in data:
        for i in range(len(levels) + 1):
            cnt[tuple(k[l] for l in levels[:i])][v] += 1
    return cnt


def moments(data, levels):
    """per level: (sd, pi, s) of the log-tilt, by moments"""
    cnt = node_counts(data, levels); out = []
    for i in range(1, len(levels) + 1):
        rows = []
        for path, c in cnt.items():
            if len(path) != i:
                continue
            par = cnt[path[:-1]]; npar = sum(par.values()); n = sum(c.values())
            for v, pv in par.items():
                e = n * pv / npar
                if e >= 5:
                    rows.append((e, math.log((c.get(v, 0) + 0.5) / (e + 0.5))))
        den = sum(e for e, _ in rows)
        m2 = max(sum(e * (x * x - 1.0 / e) for e, x in rows) / den, 0.0) if den else 0.0
        m4 = max(sum(e * (x ** 4 - 6.0 * m2 / e - 3.0 / (e * e)) for e, x in rows) / den, 0.0) if den else 0.0
        if m2 > 0 and m4 > 0:
            pi = min(m2 * m2 / m4, 1.0); s = math.sqrt(m2 / pi)
        else:
            pi, s = 1.0, math.sqrt(m2)
        out.append(dict(sd=math.sqrt(m2), pi=pi, s=s))
    return out


def page_rho(data, pages, sd_page):
    """lag-1 correlation of the page log-tilt between consecutive pages of a quire"""
    lv = LV + ['page']; cnt = node_counts(data, lv)
    path = {p['folio']: tuple(slots6.loc_of(p, 0)[l] for l in lv) for p in pages}
    def xs(p):
        c = cnt[path[p['folio']]]; par = cnt[path[p['folio']][:-1]]; npar = sum(par.values()); n = sum(c.values()); o = {}
        for v, pv in par.items():
            e = n * pv / npar
            if e >= 5:
                o[v] = (e, math.log((c.get(v, 0) + 0.5) / (e + 0.5)))
        return o
    num = den = 0.0
    for a, b in zip(pages, pages[1:]):
        if path[a['folio']][:-1] != path[b['folio']][:-1]:
            continue
        xa, xb = xs(a), xs(b)
        for v in set(xa) & set(xb):
            w = math.sqrt(xa[v][0] * xb[v][0]); num += w * xa[v][1] * xb[v][1]; den += w
    return min(max(num / den / (sd_page ** 2), 0.0), 0.95) if den and sd_page > 0 else 0.0


class Slot:
    def __init__(self, counts, data, kind, mom, page, nprng):
        self.vals = sorted(counts); self.idx = {v: i for i, v in enumerate(self.vals)}
        tot = sum(counts.values()); self.base = np.array([counts[v] / tot for v in self.vals])
        self.table = self.table0 = slots6.Table(data, self.idx, self.base); self.kind, self.mom, self.page, self.np = kind, mom, page, nprng
        self.cnt = node_counts(data, LV) if kind in ('emp', 'lang') else None
        self.tabs = {l: slots6.Table([r for r in data if r[0]['lang'] == l], self.idx, self.base) for l in {k['lang'] for k, _ in data}} if kind == 'lang' else None
        self.logt = {}; self.t = {}; self.pt = None; self.pkey = None; self.cur = None

    def level(self, pre):
        if pre not in self.logt:
            n = len(self.vals); m = self.mom[len(pre) - 1]
            if self.kind == 'norm':
                t = self.np.normal(size=n) * m['sd']
            elif self.kind == 'cat':
                t = (self.np.random_sample(n) < m['pi']) * np.where(self.np.random_sample(n) < 0.5, -1.0, 1.0) * m['s']
            else:
                c = self.cnt[pre]; par = self.cnt[pre[:-1]]; npar = sum(par.values()); nn = sum(c.values()); t = np.zeros(n)
                for v, pv in par.items():
                    e = nn * pv / npar; t[self.idx[v]] = math.log((c.get(v, 0) + 0.5) / (e + 0.5))
            self.logt[pre] = t
        return self.logt[pre]

    def start_page(self, keys):
        path = tuple(keys[l] for l in LV)
        if path not in self.t:
            self.t[path] = sum(self.level(path[:i]) for i in range(2 if self.kind == 'lang' else 1, len(LV) + 1))
        if self.tabs:
            self.table = self.tabs.get(keys['lang'], self.table0)   # a language absent from the source: the book table
        tot = self.t[path]
        if self.page:
            sd, rho = self.page; z = self.np.normal(size=len(self.vals)) * sd
            self.pt = z if (self.pt is None or self.pkey != path) else rho * self.pt + math.sqrt(1 - rho * rho) * z
            self.pkey = path; tot = tot + self.pt
        self.cur = np.exp(tot - tot.max())

    def draw(self, context, rng):
        p = self.table.vec(context) * self.cur; c = np.cumsum(p)
        return self.vals[min(int(np.searchsorted(c, rng.random() * c[-1], side='right')), len(self.vals) - 1)]


def generate(variant, ref, seed, skel=None):
    """skel: pages to generate on (default ref); everything borrowed or estimated comes from ref (robust.py)"""
    kind, drift = VARIANTS[variant]
    rng = random.Random(seed); nprng = np.random.RandomState(seed)
    words = [w for p in ref for ln in p['lines'] for w in ln['words']]
    counts = {s: collections.Counter(slots4.split3(w)[i] for w in words) for i, s in enumerate(SLOTS)}
    gt = sum(1 for v, c in counts['middle'].items() if c == 1) / len(words)
    tpl = hpy.Template(sorted(v for v in counts['middle'] if v != EMPTY), random.Random(seed + 100))
    data = slots6.data_for(ref, edge=True)
    mom = {s: moments(data[s], LV + ['page']) for s in SLOTS}
    pg = {s: (mom[s][-1]['sd'], page_rho(data[s], ref, mom[s][-1]['sd'])) for s in SLOTS}
    sl = {s: Slot(counts[s], data[s], kind, mom[s][:len(LV)], pg[s] if drift else None, nprng) for s in SLOTS}
    out = []; copies = 0
    for p in (skel or ref):
        lines = []; recent = []; k = slots6.loc_of(p, 0)
        for s in SLOTS:
            sl[s].start_page(k)
        for li, ln in enumerate(p['lines']):
            prev = None; ws = []
            for wi in range(len(ln['words'])):
                fl = '$' if wi == len(ln['words']) - 1 else ''
                if recent and rng.random() < Q:
                    o, m = rng.choice(recent[-10:]); copies += 1
                else:
                    o = S(sl['opener'].draw(slots6.ctx_opener(prev), rng))
                    m = S(tpl.sample() or EMPTY) if rng.random() < gt else S(sl['middle'].draw(slots6.ctx_middle(o) + fl, rng))
                e = S(sl['ending'].draw(slots6.ctx_ending(o, m) + fl, rng))
                w = o + m + e; ws.append(w if w else 'o'); prev = (m + e) or EMPTY; recent.append((o, m))
            lines.append({'words': ws, 'para_start': ln['para_start']})
        g = {key: p[key] for key in ('folio', 'hand', 'lang', 'quire', 'illus')}; g['lines'] = lines; out.append(g)
    return out, dict(moments=mom, page=pg, copy_share=copies / max(sum(len(ln['words']) for p in out for ln in p['lines']), 1), good_turing_new_middle=gt)


def rng_(xs):
    return f'{min(xs):.3g}-{max(xs):.3g}'


def main():
    mode = sys.argv[1]; t0 = time.time(); ref = common.pages()
    words = [w for p in ref for ln in p['lines'] for w in ln['words']]; voc = set(words)
    if mode == 'generate':
        for variant in sys.argv[2:]:
            results = collections.OrderedDict(); meta = {}; extra = {}
            for seed in SEEDS:
                name = f'{variant}_s{seed}'; pgs, info = generate(variant, ref, seed)
                results[name] = b3.battery(pgs, name, extra)
                toks = [w for p in pgs for ln in p['lines'] for w in ln['words']]
                info.update(scribe=hpy.scribe_ratios(pgs, random.Random(17)), drift=hpy.drift(pgs), coupling=coupling(pgs), lengths=slots6.length_stats(pgs),
                            voynich_types_share=sum(1 for w in toks if w in voc) / len(toks), types_per_token=len(set(toks)) / len(toks))
                meta[name] = info
                print(name, 'scored', f'{time.time() - t0:.0f}s', flush=True)
                json.dump(dict(results=results, meta=meta), open(os.path.join(HERE, f'slots8_gen_{variant}.json'), 'w'), indent=1)
        return
    R = hpy.reference(ref, os.path.join(HERE, 'reference_battery.json'))
    results = collections.OrderedDict(R); meta = {}
    for f in ['slots6_gen_prod6e.json', 'slots7_gen_tilt7_q10.json'] + [f'slots8_gen_{v}.json' for v in VARIANTS]:
        f = os.path.join(HERE, f)
        if os.path.exists(f):
            o = json.load(open(f)); results.update(o['results']); meta.update(o['meta'])
    meta['voynich_ZL'] = dict(scribe=hpy.scribe_ratios(ref, random.Random(17)), drift=hpy.drift(ref), coupling=coupling(ref), lengths=slots6.length_stats(ref),
                              voynich_types_share=1.0, types_per_token=len(voc) / len(words))
    tol, marks = b3.score(results)
    json.dump(dict(marks=marks, tol=tol, meta=meta), open(os.path.join(HERE, 'slots8_gen_results.json'), 'w'), indent=1)
    L = ['# Slot generator v8: categorical convention, page drift (11 Nov 2026)', '', 'Script `slots8.py` (variants in its docstring).', '']
    mm = next((m for k, m in meta.items() if 'moments' in m), None)
    if mm:
        L += ['Moment estimates from Voynich (levels ' + ', '.join(LV + ['page']) + '):', '', '| slot | sd | pi (share of values switched) | s (size of a switch, log) | page lag-1 rho |', '|---|---|---|---|---|']
        for s in SLOTS:
            m = mm['moments'][s]
            L.append(f"| {s} | " + ', '.join(f"{x['sd']:.2f}" for x in m) + ' | ' + ', '.join(f"{x['pi']:.2f}" for x in m) + ' | ' + ', '.join(f"{x['s']:.2f}" for x in m) + f" | {mm['page'][s][1]:.2f} |")
        L.append('')
    groups = collections.OrderedDict()
    for name in results:
        if name in meta and 'scribe' in meta[name]:
            groups.setdefault(name if name == 'voynich_ZL' else name.rsplit('_s', 1)[0], []).append(name)
    items = ['h_peak_R', 'j_jacc_excess', 'k_jsd_halves', 'e_w10', 'd_adj_ld1']
    L += ['## Summary (range over five seeds)', '', '| variant | matched/37 | held-out/30 | between scribes / within | same scribe other doc / within | JSD A vs B | JSD quire halves | ' + ' | '.join(items) + ' | length sd |',
          '|---|---|---|---|---|---|---|' + '---|' * (len(items) + 1)]
    for g, names in groups.items():
        tot = [sum(marks[n].values()) for n in names]; held = [sum(v for k, v in marks[n].items() if k not in hpy.TUNED) for n in names]
        md = [meta[n] for n in names]
        L.append(f"| {g} | {rng_(tot)} | {rng_(held)} | {rng_([m['scribe']['between_ratio'] for m in md])} | {rng_([m['scribe']['same_ratio'] for m in md])} | {rng_([m['drift']['A_vs_B'] for m in md])} | "
                 f"{rng_([m['drift']['quire_halves_within_cell'] for m in md])} | " + ' | '.join(rng_([results[n][k] for n in names]) for k in items) + f" | {rng_([m['lengths']['sd_chars'] for m in md])} |")
    L += ['', '## Items missed, by number of seeds (of five) that miss them', '', '| variant | ' + 'missed by all five | missed by some |', '|---|---|---|']
    for g, names in groups.items():
        if g == 'voynich_ZL':
            continue
        c = collections.Counter(k for n in names for k, _ in b3.ITEMS if not marks[n][k])
        L.append(f"| {g} | " + ', '.join(k for k, x in c.items() if x == len(names)) + ' | ' + ', '.join(f'{k} ({x})' for k, x in c.items() if x < len(names)) + ' |')
    L += ['', '## Per seed', '', '| text | matched/37 | held-out/30 | JSD A vs B | edge X within | edge X across line | Voynich types share | types/token |', '|---|---|---|---|---|---|---|---|']
    for name in results:
        m = marks[name]; tot = sum(m.values()); held = sum(v for k, v in m.items() if k not in hpy.TUNED); md = meta.get(name)
        if md and 'scribe' in md:
            c = md['coupling']
            L.append(f"| {name} | {tot} | {held} | {md['drift']['A_vs_B']:.3f} | {c['within']:.4f} | {c['line_break']:.4f} | {md['voynich_types_share']:.2f} | {md['types_per_token']:.3f} |")
    L.append(''); L.append(f'Runtime {time.time() - t0:.0f} s.')
    open(os.path.join(HERE, 'slots8_gen.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    main()
