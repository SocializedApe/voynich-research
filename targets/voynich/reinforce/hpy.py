"""Hierarchical Pitman-Yor model of Voynich word use: fit, compare, generate. (10 Nov 2026)

Idea. Every account that fits part of the Voynich profile has words being re-used from what was written just before
(self-citation), from what the scribe habitually writes (hand conventions) and from a shared stock (one template).
That is the structure of a hierarchical Pitman-Yor process (Teh 2006): a tree of 'restaurants'

    book -> hand -> hand x section -> hand x section x quire -> page -> line

in which each node re-uses the words already used at that node with a rich-get-richer rule (an existing table with
c customers is chosen with weight c - d, a new one with weight theta + d t, which sends the request to the parent),
and the root draws new words from a base distribution G0. Two parameters per level (discount d, concentration
theta) say how much re-use happens at that level. The same model is the standard Bayesian account of burstiness,
Zipf and Heaps laws in text, so fitting it to Voynich and to the controls gives a 'where does word re-use live'
profile that no earlier test here produced, and generating from the fitted parameters with the glyph-unit template
as G0 gives a new candidate generator: the reinforcing improviser.

Stage 1 (fit). Chinese-restaurant-franchise Gibbs sampling (remove and re-seat every token), with the per-level d
and theta resampled by Teh's auxiliary-variable scheme (priors d ~ Beta(1, 1), theta ~ Gamma(1, 0.1)). G0 for the
fit is uniform over the text's word types (the fit is about re-use, not about spelling). Fitted to Voynich (ZL
paragraph text, fixed parse, pages labelled by Davis hand, section and quire) and to the controls poured into the
same skeleton (Latin, English, Naibbe cipher of Pliny, autocopist, gibberish volunteers), each inheriting the
skeleton's labels.

Stage 2 (generate). Fresh restaurants with the fitted (d, theta) of Voynich, the real skeleton (hands, sections,
quires, pages, line lengths) and G0 = glyph-unit trigram word model trained on Voynich word types (the shared
template; the vocabulary is regenerated, so it is borrowed, as the earlier improviser's was). Variants: none
(pure HPY), +gallows (line-initial gallows at the repo's scribe rate g 0.2), +scribe (hybrid_model.hybridize at
the repo's setting q 0.15, w 8, e 0.9, g 0.2). Seeds 19 and 7.

Stage 3 (score). b3 battery (37 items, b3.score with the match rule fixed in b3), computed on the fixed-parse
Voynich and autocopists regenerated into the same skeleton; the held-out count uses hybrid_model.TUNED_B3 (30 items
held out of the earlier tuning; nothing here was tuned on the battery, the fit is by likelihood). Scribe ratios
(scribe_ratio.analyse: between scribes / within document, same scribe other document / within) for hands 1-3.
Drift: JSD of merged-glyph bigrams between Currier A and B pages, and between quire halves within one hand and
section (the k_jsd-within-section idea of ab_internal).

Run from targets/voynich:
  python reinforce/hpy.py fit        -> reinforce/fit_results.json, fit.md       (all texts)
  python reinforce/hpy.py generate   -> reinforce/gen_results.json, gen.md       (needs fit_results.json)
  python reinforce/hpy.py all
"""
import collections, json, math, os, random, statistics, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..'); ROOT = os.path.join(VOY, '..', '..')
sys.path.insert(0, VOY); sys.path.insert(0, os.path.join(VOY, 'lines')); sys.path.insert(0, os.path.join(VOY, 'meaning'))
sys.path.insert(0, os.path.join(ROOT, 'research', 'voynich_siblings'))
import common, a4_selfcitation as a4, b3_bakeoff as b3
import hybrid_model as hm
import scribe_ratio as sr

LEVELS = ['book', 'hand', 'section', 'quire', 'page', 'line']
SWEEPS = int(os.environ.get('HPY_SWEEPS', '100'))
TUNED = hm.TUNED_B3


# ------------------------------------------------------------------------------------------------ restaurants
class Node:
    """a restaurant: for every word, its tables kept as size classes {table size: number of tables}; cw / tw = that
    word's customers / tables; c / t = totals. Size classes make every seating step O(number of distinct sizes)
    instead of O(number of tables), which matters when a discount near 1 gives a frequent word thousands of tables."""
    __slots__ = ('level', 'parent', 'tables', 'cw', 'tw', 'c', 't', 'key')

    def __init__(self, level, parent, key):
        self.level, self.parent, self.key = level, parent, key
        self.tables = {}; self.cw = {}; self.tw = {}
        self.c = 0; self.t = 0


class HPY:
    def __init__(self, d, theta, g0):
        self.d, self.theta, self.g0 = list(d), list(theta), g0   # per level; g0: dict word -> prob (fit) or sampler (gen)
        self.nodes = {}

    def node(self, path):
        """path: tuple of keys from the root; creates nodes along the way"""
        parent = None
        for i in range(len(path)):
            key = path[:i + 1]
            n = self.nodes.get(key)
            if n is None:
                n = Node(i, parent, key); self.nodes[key] = n
            parent = n
        return parent

    def prob(self, node, w):
        if node is None:
            return self.g0[w]
        d, th = self.d[node.level], self.theta[node.level]
        cw = node.cw.get(w, 0); tw = node.tw.get(w, 0)
        pp = self.prob(node.parent, w)
        return ((cw - d * tw) + (th + d * node.t) * pp) / (th + node.c)

    def _seat_existing(self, node, w, d, rng):
        """join an existing table of w, chosen with weight (size - d); returns True if done"""
        sizes = node.tables.get(w)
        if not sizes:
            return False
        exist = node.cw[w] - d * node.tw[w]
        r = rng.random() * exist
        for size, count in sizes.items():
            r -= count * (size - d)
            if r < 0:
                sizes[size] = count - 1
                if sizes[size] == 0:
                    del sizes[size]
                sizes[size + 1] = sizes.get(size + 1, 0) + 1
                node.cw[w] += 1; node.c += 1
                return True
        return False

    def add(self, node, w, rng):
        d, th = self.d[node.level], self.theta[node.level]
        pp = self.prob(node.parent, w) if node.parent is not None else self.g0[w]
        cw = node.cw.get(w, 0); tw = node.tw.get(w, 0)
        exist = cw - d * tw; new_w = (th + d * node.t) * pp
        if rng.random() * (exist + new_w) < exist and self._seat_existing(node, w, d, rng):
            return
        sizes = node.tables.setdefault(w, {}); sizes[1] = sizes.get(1, 0) + 1
        node.cw[w] = cw + 1; node.tw[w] = tw + 1; node.c += 1; node.t += 1
        if node.parent is not None:
            self.add(node.parent, w, rng)

    def remove(self, node, w, rng):
        sizes = node.tables[w]
        r = rng.random() * node.cw[w]
        for size, count in sizes.items():
            r -= count * size
            if r < 0:
                sizes[size] = count - 1
                if sizes[size] == 0:
                    del sizes[size]
                node.cw[w] -= 1; node.c -= 1
                if size == 1:
                    node.tw[w] -= 1; node.t -= 1
                    if node.tw[w] == 0:
                        del node.tables[w]; del node.cw[w]; del node.tw[w]
                    if node.parent is not None:
                        self.remove(node.parent, w, rng)
                else:
                    sizes[size - 1] = sizes.get(size - 1, 0) + 1
                return
        raise RuntimeError('remove failed')

    # ---- hyperparameters (Teh 2006, appendix): auxiliary variables per restaurant, conjugate updates per level
    def resample_hyper(self, rng, a=1.0, b=1.0, alpha=1.0, beta=0.1):
        by_level = collections.defaultdict(list)
        for n in self.nodes.values():
            by_level[n.level].append(n)
        for lev, nodes in by_level.items():
            d, th = self.d[lev], self.theta[lev]
            sum_1my = 0; sum_y = 0; sum_1mz = 0; sum_logx = 0.0
            for n in nodes:
                if n.c >= 2:
                    sum_logx += math.log(rng.betavariate(th + 1, n.c - 1))
                for i in range(1, n.t):
                    y = 1 if rng.random() < th / (th + d * i) else 0
                    sum_y += y; sum_1my += 1 - y
                for sizes in n.tables.values():
                    for size, count in sizes.items():
                        for l in range(1, size):   # z ~ Bernoulli((l-1)/(l-d)) for each of the count tables
                            sum_1mz += count - rng.binomialvariate(count, (l - 1) / (l - d))
            self.d[lev] = min(max(rng.betavariate(a + sum_1my, b + sum_1mz), 1e-4), 0.9999)
            rate = beta - sum_logx
            self.theta[lev] = rng.gammavariate(alpha + sum_y, 1.0 / rate) if rate > 0 else th

    def loglik(self, data, rng):
        """held-in predictive log2-prob per token, sequentially re-adding each removed token (one pass)"""
        tot = 0.0
        for path, w in data:
            n = self.nodes[path]
            self.remove(n, w, rng); tot += math.log2(max(self.prob(n, w), 1e-300)); self.add(n, w, rng)
        return tot / len(data)


def paths_of(pgs):
    """list of (line path, word) in text order"""
    data = []
    for p in pgs:
        base = ('book', 'h' + p['hand'], 's' + p['illus'], 'q' + p['quire'], p['folio'])
        for li, ln in enumerate(p['lines']):
            path = base + (f'l{li}',)
            for w in ln['words']:
                data.append((path, w))
    return data


def fit(pgs, rng, sweeps=SWEEPS, log=None, init_d=0.5, init_theta=1.0, fixed_sweeps=0):
    """fixed_sweeps: Gibbs sweeps at the initial hyperparameters before hyperparameter sampling starts (the
    seating otherwise collapses to singleton tables at d -> 1 before multi-customer tables can form)"""
    data = paths_of(pgs)
    types = sorted({w for _, w in data}); g0 = {w: 1.0 / len(types) for w in types}
    m = HPY([init_d] * len(LEVELS), [init_theta] * len(LEVELS), g0)
    for path, w in data:
        m.add(m.node(path), w, rng)
    order = list(range(len(data)))
    hist = []
    for s in range(sweeps):
        rng.shuffle(order)
        for i in order:
            path, w = data[i]; n = m.nodes[path]
            m.remove(n, w, rng); m.add(n, w, rng)
        if s >= fixed_sweeps:
            m.resample_hyper(rng)
        if log and (s % 5 == 4 or s == sweeps - 1):
            print(f'  sweep {s + 1}: d ' + ' '.join(f'{x:.2f}' for x in m.d) + ' | theta ' + ' '.join(f'{x:.1f}' for x in m.theta)
                  + f' | root tables {m.nodes[("book",)].t}', flush=True)
        hist.append((list(m.d), list(m.theta)))
    # posterior means over the second half of the sweeps
    half = hist[len(hist) // 2:]
    d = [statistics.mean(h[0][i] for h in half) for i in range(len(LEVELS))]
    th = [statistics.mean(h[1][i] for h in half) for i in range(len(LEVELS))]
    d_sd = [statistics.pstdev(h[0][i] for h in half) for i in range(len(LEVELS))]
    th_sd = [statistics.pstdev(h[1][i] for h in half) for i in range(len(LEVELS))]
    ll = m.loglik(data, rng)
    tables = {LEVELS[l]: sum(n.t for n in m.nodes.values() if n.level == l) for l in range(len(LEVELS))}
    custs = {LEVELS[l]: sum(n.c for n in m.nodes.values() if n.level == l) for l in range(len(LEVELS))}
    return dict(d=d, theta=th, d_sd=d_sd, theta_sd=th_sd, loglik_per_token=ll, tokens=len(data), types=len(types), tables=tables, customers=custs,
                share_new_at_level={LEVELS[l]: tables[LEVELS[l]] / custs[LEVELS[l]] for l in range(len(LEVELS))})


# ------------------------------------------------------------------------------------------------ template G0
class Template:
    """glyph-unit trigram word model with '#' edges, trained on word types (each once) or tokens"""
    def __init__(self, words, rng):
        t = collections.defaultdict(collections.Counter)
        for w in words:
            u = ['#', '#'] + common.units(w) + ['#']
            for a, b, c in zip(u, u[1:], u[2:]):
                t[(a, b)][c] += 1
        self.opts = {k: (list(v), [float(x) for x in v.values()]) for k, v in t.items()}
        self.rng = rng

    def sample(self):
        ctx = ('#', '#'); out = []
        while len(out) < 14:
            opts, w = self.opts[ctx]
            nxt = self.rng.choices(opts, weights=w)[0]
            if nxt == '#':
                if out:
                    break
                continue
            out.append(nxt); ctx = (ctx[1], nxt)
        return ''.join(out)


class Sampler(HPY):
    """generation: the base distribution is a sampler, probabilities are not needed"""
    def draw(self, node, rng):
        d, th = self.d[node.level], self.theta[node.level]
        exist = node.c - d * node.t
        if rng.random() * (exist + th + d * node.t) < exist:
            r = rng.random() * exist
            for w, tw in node.tw.items():
                r -= node.cw[w] - d * tw
                if r < 0:
                    if self._seat_existing(node, w, d, rng):
                        return w
                    break
        w = self.draw(node.parent, rng) if node.parent is not None else self.g0.sample()
        sizes = node.tables.setdefault(w, {}); sizes[1] = sizes.get(1, 0) + 1
        node.cw[w] = node.cw.get(w, 0) + 1; node.tw[w] = node.tw.get(w, 0) + 1; node.c += 1; node.t += 1
        return w


def generate(ref, d, theta, template, seed):
    rng = random.Random(seed); m = Sampler(d, theta, template)
    out = []
    for p in ref:
        base = ('book', 'h' + p['hand'], 's' + p['illus'], 'q' + p['quire'], p['folio'])
        lines = []
        for li, ln in enumerate(p['lines']):
            n = m.node(base + (f'l{li}',))
            lines.append({'words': [m.draw(n, rng) for _ in ln['words']], 'para_start': ln['para_start']})
        q = {k: p[k] for k in ('folio', 'hand', 'lang', 'quire', 'illus')}; q['lines'] = lines; out.append(q)
    return out


def gallows_only(pgs, rng, g=0.2):
    return hm.hybridize(pgs, rng, 0.0, 8, 0.0, g)


# ------------------------------------------------------------------------------------------------ scoring
def battery(pgs, name, extra):
    return b3.battery(pgs, name, extra)


def scribe_ratios(pgs, rng):
    groups = collections.defaultdict(list)
    for p in pgs:
        if p['hand'] in ('1', '2', '3'):
            groups[p['hand']] += [w for ln in p['lines'] for w in ln['words']]
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        r = sr.analyse('x', sr.docs_of(groups), common.units, rng)
    return r


def drift(pgs):
    """JSD of merged-glyph bigram distributions: A vs B; and quire halves within (hand, section) cells, mean over
    cells with >= 2 quires and >= 600 tokens a side"""
    def strings(pp):
        return b3.page_strings(pp, merged=True)
    A = [p for p in pgs if p['lang'] == 'A']; B = [p for p in pgs if p['lang'] == 'B']
    ab = b3.jsd(b3.bigram_dist(strings(A)), b3.bigram_dist(strings(B))) if A and B else None
    cells = collections.defaultdict(lambda: collections.defaultdict(list))
    for p in pgs:
        cells[(p['hand'], p['illus'])][p['quire']].append(p)
    vals = []
    for cell, qs in cells.items():
        quires = sorted(qs)
        if len(quires) < 2:
            continue
        h = len(quires) // 2
        a = [p for q in quires[:h] for p in qs[q]]; b = [p for q in quires[h:] for p in qs[q]]
        na = sum(len(ln['words']) for p in a for ln in p['lines']); nb = sum(len(ln['words']) for p in b for ln in p['lines'])
        if na >= 600 and nb >= 600:
            vals.append(b3.jsd(b3.bigram_dist(strings(a)), b3.bigram_dist(strings(b))))
    return dict(A_vs_B=ab, quire_halves_within_cell=statistics.mean(vals) if vals else None, cells=len(vals))


def reference(ref, cache):
    if os.path.exists(cache):
        return json.load(open(cache))
    extra = {}; R = collections.OrderedDict()
    skel = a4.skeleton(ref)
    R['voynich_ZL'] = battery(ref, 'voynich_ZL', extra)
    R['autocopist_s19'] = battery(common.with_meta(a4.Autocopist(19).generate(skel), ref), 'autocopist_s19', extra)
    R['autocopist_s7'] = battery(common.with_meta(a4.Autocopist(7).generate(skel), ref), 'autocopist_s7', extra)
    json.dump(R, open(cache, 'w'), indent=1)
    return R


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'all'
    t0 = time.time(); rng = random.Random(19)
    ref = common.pages()
    if mode in ('fit', 'all'):
        texts = collections.OrderedDict(voynich=ref)
        texts.update(common.controls(ref, which=('latin', 'english', 'naibbe', 'autocopist_s19', 'gibberish')))
        res = collections.OrderedDict()
        for name, pgs in texts.items():
            print(f'fitting {name} ({sum(len(ln["words"]) for p in pgs for ln in p["lines"])} tokens)', flush=True)
            res[name] = fit(pgs, random.Random(7), log=True)
            print(f'  {name}: done {time.time() - t0:.0f}s, loglik/token {res[name]["loglik_per_token"]:.3f}', flush=True)
        json.dump(res, open(os.path.join(HERE, 'fit_results.json'), 'w'), indent=1)
        L = ['# Hierarchical Pitman-Yor fit: where does word re-use live? (10 Nov 2026)', '',
             f'Script `hpy.py fit` ({SWEEPS} Gibbs sweeps, posterior means over the second half). Levels: ' + ' > '.join(LEVELS) + '.',
             'd = discount, theta = concentration (small theta, large d = strong re-use at that level); new/cust = share of customers at that level that opened a new table (were passed up to the parent).', '']
        L.append('| text | tokens | types | log2 p/token | ' + ' | '.join(f'd {l}' for l in LEVELS) + ' | ' + ' | '.join(f'theta {l}' for l in LEVELS) + ' | ' + ' | '.join(f'new/cust {l}' for l in LEVELS) + ' |')
        L.append('|' + '---|' * (4 + 3 * len(LEVELS)))
        for name, r in res.items():
            L.append(f"| {name} | {r['tokens']} | {r['types']} | {r['loglik_per_token']:.3f} | " + ' | '.join(f'{x:.2f}+-{s:.2f}' for x, s in zip(r['d'], r['d_sd'])) + ' | '
                     + ' | '.join(f'{x:.1f}+-{s:.1f}' for x, s in zip(r['theta'], r['theta_sd'])) + ' | ' + ' | '.join(f"{r['share_new_at_level'][l]:.3f}" for l in LEVELS) + ' |')
        L.append(''); L.append(f'Runtime {time.time() - t0:.0f} s.')
        open(os.path.join(HERE, 'fit.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L))
    if mode in ('generate', 'all'):
        fr = json.load(open(os.path.join(HERE, 'fit_results.json')))['voynich']
        R = reference(ref, os.path.join(HERE, 'reference_battery.json'))
        extra = {}
        voc_types = sorted({w for p in ref for ln in p['lines'] for w in ln['words']})
        voc_tokens = [w for p in ref for ln in p['lines'] for w in ln['words']]
        gen = collections.OrderedDict(); meta = {}
        for base_name, base_words in (('types', voc_types), ('tokens', voc_tokens)):
            for seed in (19, 7):
                tpl = Template(base_words, random.Random(seed + 100))
                pure = generate(ref, fr['d'], fr['theta'], tpl, seed)
                gen[f'hpy_{base_name}_s{seed}'] = pure
                gen[f'hpy_{base_name}_gallows_s{seed}'] = gallows_only(pure, random.Random(seed + 200))
                gen[f'hpy_{base_name}_scribe_s{seed}'] = common.with_meta(hm.hybridize(pure, random.Random(seed + 300), 0.15, 8, 0.9, 0.2), ref)
                gen[f'hpy_{base_name}_gallows_s{seed}'] = common.with_meta(gen[f'hpy_{base_name}_gallows_s{seed}'], ref)
        results = collections.OrderedDict(R)
        for name, pgs in gen.items():
            results[name] = battery(pgs, name, extra)
            meta[name] = dict(scribe=scribe_ratios(pgs, random.Random(17)), drift=drift(pgs),
                              voynich_types_share=sum(1 for p in pgs for ln in p['lines'] for w in ln['words'] if w in set(voc_types)) / sum(len(ln['words']) for p in pgs for ln in p['lines']))
            print(name, 'scored', f'{time.time() - t0:.0f}s', flush=True)
        meta['voynich'] = dict(scribe=scribe_ratios(ref, random.Random(17)), drift=drift(ref))
        tol, marks = b3.score(results)
        out = dict(results=results, marks=marks, tol=tol, meta=meta, fitted=fr)
        json.dump(out, open(os.path.join(HERE, 'gen_results.json'), 'w'), indent=1)
        L = ['# Reinforcing improviser (fitted HPY + glyph template) against the b3 battery, scribe ratios and drift (10 Nov 2026)', '',
             'Script `hpy.py generate`. Fitted Voynich parameters: d ' + ', '.join(f'{x:.2f}' for x in fr['d']) + '; theta ' + ', '.join(f'{x:.1f}' for x in fr['theta']) + ' (' + ' > '.join(LEVELS) + ').',
             'Match rule as b3 (tolerance = max(10% of Voynich, autocopist seed spread)); held-out = the 30 items outside hybrid_model.TUNED_B3. Scribe ratios as scribe_ratio.py (Voynich 2.97 / 2.00 in the October run).', '']
        L.append('| text | matched/37 | held-out/30 | between scribes / within | same scribe other doc / within | JSD A vs B | JSD quire halves in cell | Voynich types share |')
        L.append('|---|---|---|---|---|---|---|---|')
        for name in results:
            m = marks[name]; tot = sum(m.values()); held = sum(v for k, v in m.items() if k not in TUNED)
            md = meta.get(name) or meta.get('voynich') if name == 'voynich_ZL' else meta.get(name)
            if md and 'scribe' in md:
                s = md['scribe']; dr = md['drift']
                L.append(f"| {name} | {tot} | {held} | {s['between_ratio']:.2f} [{s['ci'][0]:.2f}-{s['ci'][1]:.2f}] | {s['same_ratio']:.2f} [{s['same_ci'][0]:.2f}-{s['same_ci'][1]:.2f}] | "
                         f"{dr['A_vs_B']:.3f} | {dr['quire_halves_within_cell']:.3f} ({dr['cells']}) | {md.get('voynich_types_share', 1.0):.2f} |")
            else:
                L.append(f'| {name} | {tot} | {held} | | | | | |')
        L.append(''); L.append('## Items, all corpora'); L.append('')
        names = list(results)
        for title, keys in b3.GROUPS:
            ks = [k for k, _ in b3.ITEMS if k[0] in keys]
            L.append(f'### {title}'); L.append(''); L += b3.table(results, ks, names, marks, count=False); L.append('')
        L.append('Missed items per generated text (value vs Voynich):'); L.append('')
        for name in gen:
            miss = [f"{k} {b3.fmt(results[name][k])} vs {b3.fmt(results['voynich_ZL'][k])}" for k, _ in b3.ITEMS if not marks[name][k]]
            L.append(f'- {name}: ' + '; '.join(miss))
        L.append(''); L.append(f'Runtime {time.time() - t0:.0f} s.')
        open(os.path.join(HERE, 'gen.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L[:12]))


if __name__ == '__main__':
    main()
