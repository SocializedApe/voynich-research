"""Is the scribe/language convention a context-free habit on top of a shared transition rule? Held-out likelihood of
a product model against every tree ordering. (10 Nov 2026, second session)

slots4.py (slots independent, each with a location hierarchy) carried the scribe conventions and lost the word;
slots5.py (slots chained, context level above the location levels) carried the word and half the convention. A tree
has to put the chain above the convention or the convention above the chain. The alternative named in the README is
a product: P(value | context, location) proportional to P(value) x [P(value | context) / P(value)] x
[P(value | location) / P(value)], i.e. context and location independent given the value (the convention is a
context-free habit on each ending; the transition rule is shared by the book).

Protocol (fixed before the run). Slots and contexts as slots5.py (opener | last unit of the previous word in the
line; middle | last unit of the opener; ending | last unit of opener + middle). Pages i % 5 == 2 are the test set,
i % 5 == 4 the dev set, the rest the training set. Every model is a hierarchical Pitman-Yor (hpy.HPY) fitted on the
training pages by Gibbs sampling with hyperparameter sampling (HPY_SWEEPS, default 60), G0 uniform over the training
values with 1/(V+1) for an unseen value. Test pages are predicted token by token in order, each token then added to
the model (so the page's own re-use counts), the page removed afterwards.
  flat          book
  ctx           book > context
  loc           book > lang > hand > section > quire > page > line
  tree_ctx_loc  book > context > lang > hand > section > quire > page > line        (slots5: chain above convention)
  tree_lang_ctx book > lang > context > hand > section > quire > page > line        (language above the chain)
  tree_loc_ctx  book > lang > hand > section > quire > page > context               (convention above the chain)
  product       flat x (ctx / flat) x (loc / flat), normalised over all values seen in the corpus + one unseen value
  product_w     flat x (ctx / flat)^a x (loc / flat)^b, (a, b) on a grid, chosen on the dev pages   (diagnostic)
  mixture       lam ctx + (1 - lam) loc, lam chosen on the dev pages    (control: is any combination enough?)
Rule: on a slot the product is the better account if the unweighted product has fewer held-out bits per token than
every tree and the 95% interval of its difference to the best tree (2,000 page bootstraps, paired) excludes zero.
Calibration: the same comparison on a slots5 sample (truth = tree_ctx_loc: a tree must win or tie) and on a slots4
sample (truth for middle and ending = loc with no context: loc must win or tie, the product must not beat it), and
on a slots6 sample when it exists (truth = product for the ending).

Added after lengths.py: a fourth argument 'len' gives the middle and the ending a context with a length class
(last unit + number of glyph units written so far in the word, binned), to see what the length budget is worth.

Run from targets/voynich: python reinforce/product.py heldout <voynich|v5|v4|v6> <opener|middle|ending> [len]
                          python reinforce/product.py report
"""
import collections, json, math, os, random, statistics, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..')
sys.path.insert(0, HERE); sys.path.insert(0, VOY); sys.path.insert(0, os.path.join(VOY, 'lines')); sys.path.insert(0, os.path.join(VOY, 'meaning'))
sys.path.insert(0, os.path.join(VOY, '..', '..', 'research', 'voynich_siblings'))
import hpy, common
import slots3, slots4, slots5
from slots import EMPTY, Mixture

SWEEPS = int(os.environ.get('HPY_SWEEPS', '60'))
SLOTS = ('opener', 'middle', 'ending')
MODELS = collections.OrderedDict([
    ('flat', ['book']), ('ctx', ['book', 'context']),
    ('loc', ['book', 'lang', 'hand', 'section', 'quire', 'page', 'line']),
    ('tree_ctx_loc', ['book', 'context', 'lang', 'hand', 'section', 'quire', 'page', 'line']),
    ('tree_lang_ctx', ['book', 'lang', 'context', 'hand', 'section', 'quire', 'page', 'line']),
    ('tree_loc_ctx', ['book', 'lang', 'hand', 'section', 'quire', 'page', 'context'])])
TREES = ('ctx', 'loc', 'tree_ctx_loc', 'tree_lang_ctx', 'tree_loc_ctx')
GRID = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5]
LAMS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
UNK = '\x00unk'


def len_ctx(slot, w):
    """context with a length class (lengths.py N2): middle | last unit of the opener + opener length (0, 1, 2, 3+);
    ending | last unit of opener + middle + its length (0-1, 2, 3, 4, 5+)"""
    o, m, e = (('' if x == EMPTY else x) for x in slots4.split3(w))
    if slot == 'middle':
        return slots5.last_unit(o) + ':' + str(min(len(common.units(o)) if o else 0, 3))
    return slots5.last_unit(o + m) + ':' + str(min(max(len(common.units(o + m)) if o + m else 0, 1), 5))


def tokens(pgs, slot, mode='unit'):
    """per page: list of (key dict, value) in reading order"""
    out = []
    for p in pgs:
        toks = []
        for li, ln in enumerate(p['lines']):
            prev = None
            for w in ln['words']:
                c, v = slots5.contexts(w, prev)[slot]
                if mode == 'len' and slot != 'opener':
                    c = len_ctx(slot, w)
                toks.append((dict(book='book', context='c' + c, lang='L' + p['lang'], hand='h' + p['hand'], section='s' + p['illus'],
                                  quire='q' + p['quire'], page=p['folio'], line=f'l{li}'), v))
                o, m, e = slots4.split3(w); prev = (('' if m == EMPTY else m) + ('' if e == EMPTY else e)) or EMPTY
        out.append(toks)
    return out


def path(keys, levels):
    return tuple(keys[l] for l in levels)


class G0:
    def __init__(self, types):
        self.p = 1.0 / len(types); self.pu = 1.0 / (len(types) + 1); self.types = set(types)

    def __getitem__(self, w):
        return self.p if w in self.types else self.pu


def fit(train, levels, rng, sweeps):
    data = [(path(k, levels), v) for toks in train for k, v in toks]
    m = hpy.HPY([0.5] * len(levels), [1.0] * len(levels), G0(sorted({v for _, v in data})))
    for pth, v in data:
        m.add(m.node(pth), v, rng)
    order = list(range(len(data)))
    for s in range(sweeps):
        rng.shuffle(order)
        for i in order:
            pth, v = data[i]; n = m.nodes[pth]; m.remove(n, v, rng); m.add(n, v, rng)
        if s >= 10:
            m.resample_hyper(rng)
    return m


def pvec(m, node, idx, base):
    """predictive probability of every value in idx at a node (vectorised hpy.HPY.prob)"""
    if node is None:
        return base
    pp = pvec(m, node.parent, idx, base)
    d, th = m.d[node.level], m.theta[node.level]
    v = (th + d * node.t) * pp
    for w, cw in node.cw.items():
        v[idx[w]] += cw - d * node.tw[w]
    return v / (th + node.c)


def evaluate(models, pages_toks, idx, rng):
    """sequential prediction of each page; returns per page: n and, per model / grid point, the summed log2 prob"""
    V = len(idx); res = []
    bases = {}
    for name, m in models.items():
        b = np.full(V, m.g0.pu); b[[i for w, i in idx.items() if w in m.g0.types]] = m.g0.p; bases[name] = b
    for toks in pages_toks:
        acc = collections.defaultdict(float); added = []
        for keys, v in toks:
            i = idx[v]
            vec = {}
            for name, m in models.items():
                node = m.node(path(keys, MODELS[name]))
                if name in ('flat', 'ctx', 'loc'):
                    vec[name] = pvec(m, node, idx, bases[name]); p = vec[name][i]
                else:
                    p = m.prob(node, v)
                acc[name] += math.log2(max(p, 1e-300))
            lf, lc, ll = (np.log2(vec[k]) for k in ('flat', 'ctx', 'loc'))
            rc = lc - lf; rl = ll - lf
            for a in GRID:
                for b in GRID:
                    s = lf + a * rc + b * rl; mx = s.max()
                    acc[f'pw_{a}_{b}'] += s[i] - (mx + math.log2(np.exp2(s - mx).sum()))
            for lam in LAMS:
                acc[f'mix_{lam}'] += math.log2(lam * vec['ctx'][i] + (1 - lam) * vec['loc'][i])
            for name, m in models.items():
                node = m.node(path(keys, MODELS[name])); m.add(node, v, rng); added.append((m, node, v))
        for m, node, v in added:
            m.remove(node, v, rng)
        res.append(dict(n=len(toks), **acc))
    return res


def bits(res, key):
    return -sum(r[key] for r in res) / sum(r['n'] for r in res)


def boot(res, a, b, rng, B=2000):
    """bits per token of model a minus model b, page bootstrap"""
    out = []
    for _ in range(B):
        s = [res[rng.randrange(len(res))] for _ in res]; n = sum(r['n'] for r in s)
        out.append(-(sum(r[a] for r in s) - sum(r[b] for r in s)) / n)
    out.sort()
    return [out[int(0.025 * B)], out[int(0.975 * B)]]


def load_text(name, ref):
    if name == 'voynich':
        return ref
    words = [w for p in ref for ln in p['lines'] for w in ln['words']]
    counts = {s: collections.Counter(slots4.split3(w)[i] for w in words) for i, s in enumerate(SLOTS)}
    seed = 19
    tpl = hpy.Template(sorted(v for v in counts['middle'] if v != EMPTY), random.Random(seed + 100))
    g0s = dict(opener=Mixture(counts['opener'], None, 0.0, random.Random(seed + 50)),
               middle=Mixture(counts['middle'], tpl, 0.2, random.Random(seed + 51)),
               ending=Mixture(counts['ending'], None, 0.0, random.Random(seed + 52)))
    if name == 'v5':
        return slots5.generate(ref, json.load(open(os.path.join(HERE, 'slots5_fit.json'))), g0s, seed)[0]
    if name == 'v4':
        return slots4.generate(ref, json.load(open(os.path.join(HERE, 'slots4_fit.json'))), g0s, seed)[0]
    if name == 'v6':
        import slots6
        return slots6.sample(ref, seed)
    raise SystemExit('unknown text ' + name)


def heldout(text, slot, mode='unit'):
    t0 = time.time(); ref = common.pages(); pgs = load_text(text, ref)
    T = tokens(pgs, slot, mode); sfx = '' if mode == 'unit' else '_' + mode
    train = [t for i, t in enumerate(T) if i % 5 not in (2, 4)]; dev = [t for i, t in enumerate(T) if i % 5 == 4]; test = [t for i, t in enumerate(T) if i % 5 == 2]
    types = sorted({v for toks in T for _, v in toks}); idx = {w: i for i, w in enumerate(types)}; idx[UNK] = len(types)
    models = {}
    for name, levels in MODELS.items():
        models[name] = fit(train, levels, random.Random(3), SWEEPS)
        print(f'{text} {slot} fitted {name} {time.time() - t0:.0f}s', flush=True)
    rng = random.Random(11)
    D = evaluate(models, dev, idx, rng); R = evaluate(models, test, idx, rng)
    best_ab = min(((a, b) for a in GRID for b in GRID), key=lambda ab: bits(D, f'pw_{ab[0]}_{ab[1]}'))
    best_lam = min(LAMS, key=lambda l: bits(D, f'mix_{l}'))
    out = dict(text=text, slot=slot, ctx_mode=mode, sweeps=SWEEPS, values=len(types), train_tokens=sum(map(len, train)), dev_tokens=sum(map(len, dev)),
               test_tokens=sum(map(len, test)), test_pages=len(test))
    out['bits'] = {name: bits(R, name) for name in MODELS}
    out['bits']['product'] = bits(R, 'pw_1.0_1.0')
    out['bits']['product_w'] = bits(R, f'pw_{best_ab[0]}_{best_ab[1]}'); out['weights'] = best_ab
    out['bits']['mixture'] = bits(R, f'mix_{best_lam}'); out['lam'] = best_lam
    out['dev_bits'] = {name: bits(D, name) for name in MODELS}; out['dev_bits']['product'] = bits(D, 'pw_1.0_1.0')
    out['grid_test'] = {f'{a}_{b}': bits(R, f'pw_{a}_{b}') for a in GRID for b in GRID}
    best_tree = min(TREES, key=lambda k: out['bits'][k]); out['best_tree'] = best_tree
    brng = random.Random(5)
    out['product_minus_best_tree'] = dict(diff=out['bits']['product'] - out['bits'][best_tree], ci=boot(R, 'pw_1.0_1.0', best_tree, brng))
    out['product_w_minus_best_tree'] = dict(diff=out['bits']['product_w'] - out['bits'][best_tree], ci=boot(R, f'pw_{best_ab[0]}_{best_ab[1]}', best_tree, brng))
    out['mixture_minus_best_tree'] = dict(diff=out['bits']['mixture'] - out['bits'][best_tree], ci=boot(R, f'mix_{best_lam}', best_tree, brng))
    out['product_minus_mixture'] = dict(diff=out['bits']['product'] - out['bits']['mixture'], ci=boot(R, 'pw_1.0_1.0', f'mix_{best_lam}', brng))
    out['hyper'] = {name: dict(d=m.d, theta=m.theta) for name, m in models.items()}
    out['runtime_s'] = time.time() - t0
    json.dump(out, open(os.path.join(HERE, f'product_heldout_{text}_{slot}{sfx}.json'), 'w'), indent=1)
    print(json.dumps({k: out[k] for k in ('bits', 'weights', 'lam', 'best_tree', 'product_minus_best_tree', 'product_w_minus_best_tree', 'mixture_minus_best_tree')}, indent=1))


def report():
    cols = list(MODELS) + ['product', 'product_w', 'mixture']
    L = ['# Product model against the tree orderings: held-out bits per token (10 Nov 2026)', '',
         'Script `product.py` (protocol in its docstring). Test set = every fifth page, predicted token by token; lower is better.',
         'product = flat x (ctx / flat) x (loc / flat); product_w has exponents chosen on the dev pages; mixture = lam ctx + (1 - lam) loc.', '']
    L.append('| text | slot | ' + ' | '.join(cols) + ' | weights (a ctx, b loc) | lam | best tree | product - best tree [95%] | product_w - best tree [95%] | mixture - best tree [95%] |')
    L.append('|---|---|' + '---|' * (len(cols) + 6))
    for text in ('voynich', 'v5', 'v4', 'v6'):
        for slot in SLOTS + ('middle_len', 'ending_len'):
            f = os.path.join(HERE, f'product_heldout_{text}_{slot}.json')
            if not os.path.exists(f):
                continue
            o = json.load(open(f)); slot = slot.replace('_len', ', context + length class'); d = lambda k: f"{o[k]['diff']:+.3f} [{o[k]['ci'][0]:+.3f}, {o[k]['ci'][1]:+.3f}]"
            L.append(f"| {text} | {slot} | " + ' | '.join(f"{o['bits'][c]:.3f}" for c in cols) + f" | {o['weights'][0]}, {o['weights'][1]} | {o['lam']} | {o['best_tree']} | "
                     + d('product_minus_best_tree') + ' | ' + d('product_w_minus_best_tree') + ' | ' + d('mixture_minus_best_tree') + ' |')
    open(os.path.join(HERE, 'product_heldout.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    if sys.argv[1] == 'heldout':
        heldout(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else 'unit')
    else:
        report()
