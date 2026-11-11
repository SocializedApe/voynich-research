"""Slot generator v7: borrowed transition tables x a tilt drawn once per language, hand, section and quire x
copying of nearby words. (11 Nov 2026)

slots6.py (prod6t, prod6e) got the word from the book-wide transition tables but lost the scribe and A/B convention:
a location habit that has to grow by reinforcement on top of fixed tables does not grow. product.py showed the habit
is close to context-free. So here the convention is a parameter, not an outcome of re-use:
  P(v | context, location) proportional to T(v | context) x exp(b x [t_lang(v) + t_hand(v) + t_section(v) + t_quire(v)])
with T the tables of prod6e (length-class contexts, line-end tables), b the location exponent chosen on dev pages in
product.py, and each t a vector of independent normal draws, one per node of the hierarchy lang > hand > section >
quire, made once per generated text. The standard deviation of each level is estimated from Voynich by moments, not
tuned: for every node and every value with expected count e = n_node x P_parent(v) >= 5, x = log((n + 0.5) / (e +
0.5)); sigma^2 = weighted mean of x^2 less the sampling variance 1 / e (floored at 0). The same tilt applies in every
context (that is the context-free habit). Which values a language prefers is random per seed: only the strength of
the convention is taken from Voynich.
Copying (the locality items every v6 variant missed): with probability q a word takes the opener and middle of a
word drawn uniformly from the previous 10 words of the page and draws only its ending from the model. q is the one
free number; q 0, 0.1, 0.2 are run, and the item it mostly moves (e_w10) is among the tuned battery items.
New middles from the template at the Good-Turing rate, as prod6t.

Variants tilt7_q0, tilt7_q10, tilt7_q20 and notilt7_q10 (control: copying without the tilt), five seeds. Scoring as
slots6.py. Run from targets/voynich: python reinforce/slots7.py generate <variant> ... | report
"""
import collections, json, math, os, random, statistics, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..')
sys.path.insert(0, HERE); sys.path.insert(0, VOY); sys.path.insert(0, os.path.join(VOY, 'lines')); sys.path.insert(0, os.path.join(VOY, 'meaning'))
sys.path.insert(0, os.path.join(VOY, '..', '..', 'research', 'voynich_siblings'))
import hpy, common, b3_bakeoff as b3
import slots4, slots6
from slots import EMPTY, coupling

TILT = ['lang', 'hand', 'section', 'quire']
SEEDS = (19, 7, 3, 11, 23)
SLOTS = slots6.SLOTS
VARIANTS = collections.OrderedDict([('tilt7_q0', (True, 0.0)), ('tilt7_q10', (True, 0.1)), ('tilt7_q20', (True, 0.2)), ('notilt7_q10', (False, 0.1))])
S = slots6.S


def sigmas(data):
    """moment estimate of the log-tilt sd per level, from (keys, value) rows of one slot"""
    cnt = collections.defaultdict(collections.Counter)
    for k, v in data:
        for i in range(len(TILT) + 1):
            cnt[tuple(k[l] for l in TILT[:i])][v] += 1
    out = []
    for i in range(1, len(TILT) + 1):
        num = 0.0; den = 0.0
        for path, c in cnt.items():
            if len(path) != i:
                continue
            par = cnt[path[:-1]]; npar = sum(par.values()); n = sum(c.values())
            for v, pv in par.items():
                e = n * pv / npar
                if e >= 5:
                    x = math.log((c.get(v, 0) + 0.5) / (e + 0.5)); num += e * (x * x - 1.0 / e); den += e
        out.append(math.sqrt(max(num / den, 0.0)) if den else 0.0)
    return out


class Slot:
    def __init__(self, counts, data, sig, b, nprng):
        self.vals = sorted(counts); self.idx = {v: i for i, v in enumerate(self.vals)}
        tot = sum(counts.values()); self.base = np.array([counts[v] / tot for v in self.vals])
        self.table = slots6.Table(data, self.idx, self.base); self.sig, self.b, self.np = sig, b, nprng
        self.t = {}; self.logt = {}

    def tilt(self, keys):
        path = tuple(keys[l] for l in TILT)
        if path not in self.t:
            tot = np.zeros(len(self.vals))
            for i in range(1, len(TILT) + 1):
                pre = path[:i]
                if pre not in self.logt:
                    self.logt[pre] = self.np.normal(size=len(self.vals)) * self.sig[i - 1]
                tot = tot + self.logt[pre]
            self.t[path] = np.exp(self.b * tot)
        return self.t[path]

    def draw(self, keys, rng):
        p = self.table.vec(keys['context']) * self.tilt(keys); c = np.cumsum(p)
        return self.vals[min(int(np.searchsorted(c, rng.random() * c[-1], side='right')), len(self.vals) - 1)]


def generate(variant, ref, weights, seed):
    use_tilt, q = VARIANTS[variant]
    rng = random.Random(seed); nprng = np.random.RandomState(seed)
    words = [w for p in ref for ln in p['lines'] for w in ln['words']]
    counts = {s: collections.Counter(slots4.split3(w)[i] for w in words) for i, s in enumerate(SLOTS)}
    gt = sum(1 for v, c in counts['middle'].items() if c == 1) / len(words)
    tpl = hpy.Template(sorted(v for v in counts['middle'] if v != EMPTY), random.Random(seed + 100))
    data = slots6.data_for(ref, edge=True)
    sig = {s: (sigmas(data[s]) if use_tilt else [0.0] * len(TILT)) for s in SLOTS}
    sl = {s: Slot(counts[s], data[s], sig[s], weights[s][1], nprng) for s in SLOTS}
    out = []; copies = 0
    for p in ref:
        lines = []; recent = []
        for li, ln in enumerate(p['lines']):
            prev = None; ws = []; k = slots6.loc_of(p, li)
            for wi in range(len(ln['words'])):
                fl = '$' if wi == len(ln['words']) - 1 else ''
                if recent and rng.random() < q:
                    o, m = rng.choice(recent[-10:]); copies += 1
                else:
                    k['context'] = slots6.ctx_opener(prev); o = S(sl['opener'].draw(k, rng))
                    if rng.random() < gt:
                        m = S(tpl.sample() or EMPTY)
                    else:
                        k['context'] = slots6.ctx_middle(o) + fl; m = S(sl['middle'].draw(k, rng))
                k['context'] = slots6.ctx_ending(o, m) + fl; e = S(sl['ending'].draw(k, rng))
                w = o + m + e; ws.append(w if w else 'o'); prev = (m + e) or EMPTY; recent.append((o, m))
            lines.append({'words': ws, 'para_start': ln['para_start']})
        g = {key: p[key] for key in ('folio', 'hand', 'lang', 'quire', 'illus')}; g['lines'] = lines; out.append(g)
    return out, dict(sigma=sig, copy_share=copies / len(words), good_turing_new_middle=gt)


def main():
    mode = sys.argv[1]; t0 = time.time(); ref = common.pages()
    words = [w for p in ref for ln in p['lines'] for w in ln['words']]; voc = set(words); weights = slots6.load_weights()
    if mode == 'generate':
        for variant in sys.argv[2:]:
            results = collections.OrderedDict(); meta = {}; extra = {}
            for seed in SEEDS:
                name = f'{variant}_s{seed}'; pgs, info = generate(variant, ref, weights, seed)
                results[name] = b3.battery(pgs, name, extra)
                toks = [w for p in pgs for ln in p['lines'] for w in ln['words']]
                info.update(scribe=hpy.scribe_ratios(pgs, random.Random(17)), drift=hpy.drift(pgs), coupling=coupling(pgs), lengths=slots6.length_stats(pgs),
                            voynich_types_share=sum(1 for w in toks if w in voc) / len(toks), types_per_token=len(set(toks)) / len(toks))
                meta[name] = info
                print(name, 'scored', f'{time.time() - t0:.0f}s', flush=True)
                json.dump(dict(results=results, meta=meta), open(os.path.join(HERE, f'slots7_gen_{variant}.json'), 'w'), indent=1)
        return
    R = hpy.reference(ref, os.path.join(HERE, 'reference_battery.json'))
    results = collections.OrderedDict(R); meta = {}
    for f in ['slots6_gen_prod6e.json'] + [f'slots7_gen_{v}.json' for v in VARIANTS]:
        f = os.path.join(HERE, f)
        if os.path.exists(f):
            o = json.load(open(f)); results.update(o['results']); meta.update(o['meta'])
    meta['voynich_ZL'] = dict(scribe=hpy.scribe_ratios(ref, random.Random(17)), drift=hpy.drift(ref), coupling=coupling(ref), lengths=slots6.length_stats(ref),
                              voynich_types_share=1.0, types_per_token=len(voc) / len(words))
    tol, marks = b3.score(results)
    json.dump(dict(marks=marks, tol=tol, meta=meta, weights=weights), open(os.path.join(HERE, 'slots7_gen_results.json'), 'w'), indent=1)
    L = ['# Slot generator v7: borrowed tables x drawn tilts x copying (11 Nov 2026)', '', 'Script `slots7.py` (variants in its docstring).', '']
    sg = next((m['sigma'] for k, m in meta.items() if k.startswith('tilt7') and 'sigma' in m), None)
    if sg:
        L.append('Log-tilt sd by level (' + ', '.join(TILT) + '), from Voynich by moments: ' + '; '.join(f"{s} " + ', '.join(f'{x:.2f}' for x in sg[s]) for s in SLOTS) + '.'); L.append('')
    L.append('| text | matched/37 | held-out/30 | between scribes / within | same scribe other doc / within | JSD A vs B | JSD quire halves in cell | edge X within | edge X across line | Voynich types share | types/token | length sd (chars) |')
    L.append('|---|---|---|---|---|---|---|---|---|---|---|---|')
    for name in results:
        m = marks[name]; tot = sum(m.values()); held = sum(v for k, v in m.items() if k not in hpy.TUNED); md = meta.get(name)
        if md and 'scribe' in md:
            s = md['scribe']; dr = md['drift']; c = md['coupling']
            L.append(f"| {name} | {tot} | {held} | {s['between_ratio']:.2f} [{s['ci'][0]:.2f}-{s['ci'][1]:.2f}] | {s['same_ratio']:.2f} [{s['same_ci'][0]:.2f}-{s['same_ci'][1]:.2f}] | "
                     f"{dr['A_vs_B']:.3f} | {dr['quire_halves_within_cell']:.3f} ({dr['cells']}) | {c['within']:.4f} | {c['line_break']:.4f} | {md['voynich_types_share']:.2f} | {md['types_per_token']:.3f} | {md['lengths']['sd_chars']:.2f} |")
        else:
            L.append(f'| {name} | {tot} | {held} | | | | | | | | | |')
    L.append(''); L.append('Missed items per generated text (value vs Voynich):'); L.append('')
    for name in results:
        if name in R or name.startswith('prod6e'):
            continue
        miss = [f"{k} {b3.fmt(results[name][k])} vs {b3.fmt(results['voynich_ZL'][k])}" for k, _ in b3.ITEMS if not marks[name][k]]
        L.append(f'- {name}: ' + '; '.join(miss))
    L.append(''); L.append(f'Runtime {time.time() - t0:.0f} s.')
    open(os.path.join(HERE, 'slots7_gen.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    main()
