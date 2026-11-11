"""Slot-level reinforcing improviser, third version: the opener depends on the previous word, within the line.
(10 Nov 2026)

lines/boundaries.py showed that the last glyph unit of a word predicts the opening of the next word three times
more strongly than in Latin, that this holds only inside a line (zero across a line break) and only between
adjacent words. slots2.py (opener | tail, both drawn from location hierarchies) reproduces the scribe ratios and
much of the drift but has no word-to-word dependence (edge X 0.003 against 0.060). Here the opener's hierarchy gets a
context level at the top: book > context > lang > hand > section > quire > page > line, where context = the last
glyph unit of the previous word's tail, or '^' for the first word of a line. So the chain, its reset at the line
start and the line-initial opener convention are all learned from the data by the same fit, not borrowed; the hand,
section, quire, page and line habits sit under each context. The tail keeps the slots2 hierarchy and fit.

Also: a level whose fitted discount is >= 0.99 is a pass-through (it re-uses nothing) and is dropped from the
generation; with d that close to 1 the rich-get-richer rule in generation can lock onto one early table (seed 3 of
slots2 did), which the fit never does because the data pin the seating.

Scoring as slots2.py, five seeds. Run from targets/voynich: python reinforce/slots3.py fit | generate | all
"""
import collections, json, math, os, random, statistics, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..')
sys.path.insert(0, HERE); sys.path.insert(0, VOY); sys.path.insert(0, os.path.join(VOY, 'lines')); sys.path.insert(0, os.path.join(VOY, 'meaning'))
sys.path.insert(0, os.path.join(VOY, '..', '..', 'research', 'voynich_siblings'))
import hpy, common, boundaries, a4_selfcitation as a4, b3_bakeoff as b3
import hybrid_model as hm
import slots2
from slots import EMPTY, Mixture, coupling

OPENER_LEVELS = ['book', 'context', 'lang', 'hand', 'section', 'quire', 'page', 'line']
TAIL_LEVELS = slots2.LEVELS
SWEEPS = int(os.environ.get('HPY_SWEEPS', '60'))
SEEDS = (19, 7, 3, 11, 23)


def ctx_of(prev_tail):
    if prev_tail is None:
        return '^'
    if prev_tail == EMPTY:
        return '~'
    return common.units(prev_tail)[-1]


def opener_data(pgs):
    data = []
    for p in pgs:
        loc = ('L' + p['lang'], 'h' + p['hand'], 's' + p['illus'], 'q' + p['quire'], p['folio'])
        for li, ln in enumerate(p['lines']):
            prev = None
            for w in ln['words']:
                op, tail = slots2.split(w, 'ot')
                data.append((('book', 'c' + ctx_of(prev)) + loc + (f'l{li}',), op)); prev = tail
    return data


def fit_opener(pgs, g0, rng, sweeps):
    data = opener_data(pgs)
    m = hpy.HPY([0.5] * len(OPENER_LEVELS), [1.0] * len(OPENER_LEVELS), g0)
    for path, w in data:
        m.add(m.node(path), w, rng)
    order = list(range(len(data))); hist = []
    for s in range(sweeps):
        rng.shuffle(order)
        for i in order:
            path, w = data[i]; n = m.nodes[path]; m.remove(n, w, rng); m.add(n, w, rng)
        if s >= 10:
            m.resample_hyper(rng)
        if s % 10 == 9 or s == sweeps - 1:
            print(f'  sweep {s + 1}: d ' + ' '.join(f'{x:.2f}' for x in m.d) + ' | theta ' + ' '.join(f'{x:.1f}' for x in m.theta), flush=True)
        hist.append((list(m.d), list(m.theta)))
    half = hist[len(hist) // 2:]
    d = [statistics.mean(h[0][i] for h in half) for i in range(len(OPENER_LEVELS))]
    th = [statistics.mean(h[1][i] for h in half) for i in range(len(OPENER_LEVELS))]
    tables = {l: sum(n.t for n in m.nodes.values() if n.level == i) for i, l in enumerate(OPENER_LEVELS)}
    custs = {l: sum(n.c for n in m.nodes.values() if n.level == i) for i, l in enumerate(OPENER_LEVELS)}
    return dict(d=d, theta=th, share_new_at_level={l: tables[l] / custs[l] for l in OPENER_LEVELS})


class Pruned:
    """a Sampler over the active levels only (fitted d < 0.99); path keys of dropped levels are removed"""
    def __init__(self, levels, fit, g0, threshold=0.99):
        self.keep = [i for i, l in enumerate(levels) if fit['d'][i] < threshold or i == 0]
        self.levels = [levels[i] for i in self.keep]
        self.m = hpy.Sampler([fit['d'][i] for i in self.keep], [fit['theta'][i] for i in self.keep], g0)

    def draw(self, full_path, rng):
        path = tuple(full_path[i] for i in self.keep)
        return self.m.draw(self.m.node(path), rng)


def generate(ref, fits, g0s, seed):
    rng = random.Random(seed)
    op = Pruned(OPENER_LEVELS, fits['opener'], g0s['opener']); tl = Pruned(TAIL_LEVELS, fits['tail'], g0s['tail'])
    out = []
    for p in ref:
        loc = ('L' + p['lang'], 'h' + p['hand'], 's' + p['illus'], 'q' + p['quire'], p['folio'])
        lines = []
        for li, ln in enumerate(p['lines']):
            prev = None; ws = []
            for _ in ln['words']:
                o = op.draw(('book', 'c' + ctx_of(prev)) + loc + (f'l{li}',), rng)
                t = tl.draw(('book',) + loc + (f'l{li}',), rng)
                w = ('' if o == EMPTY else o) + ('' if t == EMPTY else t)
                ws.append(w if w else 'o'); prev = t
            lines.append({'words': ws, 'para_start': ln['para_start']})
        q = {k: p[k] for k in ('folio', 'hand', 'lang', 'quire', 'illus')}; q['lines'] = lines; out.append(q)
    return out, dict(opener_levels=op.levels, tail_levels=tl.levels)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'all'
    t0 = time.time(); ref = common.pages()
    words = [w for p in ref for ln in p['lines'] for w in ln['words']]
    counts = {s: collections.Counter(slots2.split(w, 'ot')[i] for w in words) for i, s in enumerate(('opener', 'tail'))}
    fit_path = os.path.join(HERE, 'slots3_fit.json')
    if mode in ('fit', 'all'):
        tot = sum(counts['opener'].values()); g0 = {v: c / tot for v, c in counts['opener'].items()}
        print('fitting opener with context', flush=True)
        fo = fit_opener(ref, g0, random.Random(7), SWEEPS)
        print(f'  done {time.time() - t0:.0f}s; d ' + ' '.join(f'{x:.2f}' for x in fo['d']) + ' theta ' + ' '.join(f'{x:.1f}' for x in fo['theta'])
              + ' new/cust ' + ' '.join(f"{fo['share_new_at_level'][l]:.2f}" for l in OPENER_LEVELS), flush=True)
        fits = dict(opener=fo, tail=json.load(open(os.path.join(HERE, 'slots2_ot_fit.json')))['tail'])
        json.dump(fits, open(fit_path, 'w'), indent=1)
    if mode in ('generate', 'all'):
        fits = json.load(open(fit_path))
        R = hpy.reference(ref, os.path.join(HERE, 'reference_battery.json'))
        voc = set(words); gen = collections.OrderedDict(); extra = {}; meta = {}; pruned = None
        for seed in SEEDS:
            tpl = hpy.Template(sorted(v for v in counts['tail'] if v != EMPTY), random.Random(seed + 100))
            g0s = dict(opener=Mixture(counts['opener'], None, 0.0, random.Random(seed + 50)), tail=Mixture(counts['tail'], tpl, 0.2, random.Random(seed + 51)))
            gen[f'ot3_s{seed}'], pruned = generate(ref, fits, g0s, seed)
        results = collections.OrderedDict(R)
        for name, pgs in gen.items():
            results[name] = b3.battery(pgs, name, extra)
            ntok = sum(len(ln['words']) for p in pgs for ln in p['lines'])
            meta[name] = dict(scribe=hpy.scribe_ratios(pgs, random.Random(17)), drift=hpy.drift(pgs), coupling=coupling(pgs),
                              voynich_types_share=sum(1 for p in pgs for ln in p['lines'] for w in ln['words'] if w in voc) / ntok)
            print(name, 'scored', f'{time.time() - t0:.0f}s', flush=True)
        meta['voynich_ZL'] = dict(scribe=hpy.scribe_ratios(ref, random.Random(17)), drift=hpy.drift(ref), coupling=coupling(ref), voynich_types_share=1.0)
        tol, marks = b3.score(results)
        json.dump(dict(results=results, marks=marks, tol=tol, meta=meta, fits=fits, pruned=pruned), open(os.path.join(HERE, 'slots3_gen_results.json'), 'w'), indent=1)
        L = ['# Slot-level reinforcing improviser v3: opener in context of the previous word, line-bound (10 Nov 2026)', '',
             'Script `slots3.py`. Fitted opener (d; theta; share passed up), levels ' + ' > '.join(OPENER_LEVELS) + ':',
             "- opener: d " + ', '.join(f'{x:.2f}' for x in fits['opener']['d']) + '; theta ' + ', '.join(f'{x:.1f}' for x in fits['opener']['theta'])
             + '; passed up ' + ', '.join(f"{fits['opener']['share_new_at_level'][l]:.2f}" for l in OPENER_LEVELS),
             "- tail (slots2 fit): d " + ', '.join(f'{x:.2f}' for x in fits['tail']['d']) + '; theta ' + ', '.join(f'{x:.1f}' for x in fits['tail']['theta']),
             f"- levels kept in generation (d < 0.99): opener {pruned['opener_levels']}, tail {pruned['tail_levels']}", '',
             'Match rule as b3; held-out = the 30 items outside hybrid_model.TUNED_B3. Scribe ratios as scribe_ratio.py.', '',
             '| text | matched/37 | held-out/30 | between scribes / within | same scribe other doc / within | JSD A vs B | JSD quire halves in cell | edge X within | edge X across line | Voynich types share |',
             '|---|---|---|---|---|---|---|---|---|---|']
        for name in results:
            m = marks[name]; tot = sum(m.values()); held = sum(v for k, v in m.items() if k not in hpy.TUNED); md = meta.get(name)
            if md:
                s = md['scribe']; dr = md['drift']; c = md['coupling']
                L.append(f"| {name} | {tot} | {held} | {s['between_ratio']:.2f} [{s['ci'][0]:.2f}-{s['ci'][1]:.2f}] | {s['same_ratio']:.2f} [{s['same_ci'][0]:.2f}-{s['same_ci'][1]:.2f}] | "
                         f"{dr['A_vs_B']:.3f} | {dr['quire_halves_within_cell']:.3f} ({dr['cells']}) | {c['within']:.4f} | {c['line_break']:.4f} | {md['voynich_types_share']:.2f} |")
            else:
                L.append(f'| {name} | {tot} | {held} | | | | | | | |')
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
        open(os.path.join(HERE, 'slots3_gen.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L[:18]))


if __name__ == '__main__':
    main()
