"""Slot-level reinforcing improviser, fifth version: a chain of slots, each in the context of the previous one.
(10 Nov 2026)

slots4.py reproduced the scribe ratios, the A/B drift and the line-bound coupling faithfully (realised re-use =
fitted re-use at every level) but, with middle and ending drawn independently of the opener and of each other,
made words too long and too novel (mean length 6.3 against 5.0; half the tokens not Voynich words). Here every
slot is drawn in the context of the last glyph unit of what precedes it:
    opener  | last unit of the previous word in the line ('^' at a line start)
    middle  | last unit of the opener ('^' if no opener)
    ending  | last unit of opener + middle ('^' if both empty)
each with the hierarchy book > context > lang > hand > section > quire > page > line (slots3.py). The word is thus a
chunk-level Markov chain whose transition tables are re-used hierarchically by location: the template (which
chunks follow which) and the conventions (which chunks a hand, a language, a quire prefers) are both learned by the
same fit. Base distributions as before (empirical slot frequencies; 20% template for new middles). Levels with
d >= 0.99 are dropped from the generation; self-consistency reported as in slots4.

Scoring as slots4.py, five seeds. Run from targets/voynich: python reinforce/slots5.py fit | generate | all
"""
import collections, json, math, os, random, statistics, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..')
sys.path.insert(0, HERE); sys.path.insert(0, VOY); sys.path.insert(0, os.path.join(VOY, 'lines')); sys.path.insert(0, os.path.join(VOY, 'meaning'))
sys.path.insert(0, os.path.join(VOY, '..', '..', 'research', 'voynich_siblings'))
import hpy, common, a4_selfcitation as a4, b3_bakeoff as b3
import slots3, slots4
from slots import EMPTY, Mixture, coupling

LEVELS = slots3.OPENER_LEVELS
SWEEPS = int(os.environ.get('HPY_SWEEPS', '60'))
SEEDS = (19, 7, 3, 11, 23)
SLOTS = ('opener', 'middle', 'ending')


def last_unit(s):
    return '^' if not s or s == EMPTY else common.units(s)[-1]


def contexts(w, prev_tail):
    o, m, e = slots4.split3(w)
    os_ = '' if o == EMPTY else o; ms = '' if m == EMPTY else m
    return {'opener': (slots3.ctx_of(prev_tail), o), 'middle': (last_unit(os_), m), 'ending': (last_unit(os_ + ms), e)}


def data_for(pgs):
    data = {s: [] for s in SLOTS}
    for p in pgs:
        loc = ('L' + p['lang'], 'h' + p['hand'], 's' + p['illus'], 'q' + p['quire'], p['folio'])
        for li, ln in enumerate(p['lines']):
            prev = None
            for w in ln['words']:
                cx = contexts(w, prev)
                for s in SLOTS:
                    c, v = cx[s]; data[s].append((('book', 'c' + c) + loc + (f'l{li}',), v))
                o, m, e = slots4.split3(w); tail = ('' if m == EMPTY else m) + ('' if e == EMPTY else e); prev = tail or EMPTY
    return data


def fit(data, g0, rng, sweeps):
    m = hpy.HPY([0.5] * len(LEVELS), [1.0] * len(LEVELS), g0)
    for path, w in data:
        m.add(m.node(path), w, rng)
    order = list(range(len(data))); hist = []
    for s in range(sweeps):
        rng.shuffle(order)
        for i in order:
            path, w = data[i]; n = m.nodes[path]; m.remove(n, w, rng); m.add(n, w, rng)
        if s >= 10:
            m.resample_hyper(rng)
        hist.append((list(m.d), list(m.theta)))
    half = hist[len(hist) // 2:]
    d = [statistics.mean(h[0][i] for h in half) for i in range(len(LEVELS))]
    th = [statistics.mean(h[1][i] for h in half) for i in range(len(LEVELS))]
    tables = {l: sum(n.t for n in m.nodes.values() if n.level == i) for i, l in enumerate(LEVELS)}
    custs = {l: sum(n.c for n in m.nodes.values() if n.level == i) for i, l in enumerate(LEVELS)}
    return dict(d=d, theta=th, share_new_at_level={l: tables[l] / custs[l] for l in LEVELS})


def generate(ref, fits, g0s, seed):
    rng = random.Random(seed)
    S = {s: slots3.Pruned(LEVELS, fits[s], g0s[s]) for s in SLOTS}
    out = []
    for p in ref:
        loc = ('L' + p['lang'], 'h' + p['hand'], 's' + p['illus'], 'q' + p['quire'], p['folio'])
        lines = []
        for li, ln in enumerate(p['lines']):
            prev = None; ws = []
            for _ in ln['words']:
                tail_path = loc + (f'l{li}',)
                o = S['opener'].draw(('book', 'c' + slots3.ctx_of(prev)) + tail_path, rng); os_ = '' if o == EMPTY else o
                m = S['middle'].draw(('book', 'c' + last_unit(os_)) + tail_path, rng); ms = '' if m == EMPTY else m
                e = S['ending'].draw(('book', 'c' + last_unit(os_ + ms)) + tail_path, rng); es = '' if e == EMPTY else e
                w = os_ + ms + es; ws.append(w if w else 'o'); prev = (ms + es) or EMPTY
            lines.append({'words': ws, 'para_start': ln['para_start']})
        q = {k: p[k] for k in ('folio', 'hand', 'lang', 'quire', 'illus')}; q['lines'] = lines; out.append(q)
    return out, {s: slots4.realised(S[s]) for s in SLOTS}, {s: S[s].levels for s in SLOTS}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'all'
    t0 = time.time(); ref = common.pages()
    words = [w for p in ref for ln in p['lines'] for w in ln['words']]
    counts = {s: collections.Counter(slots4.split3(w)[i] for w in words) for i, s in enumerate(SLOTS)}
    fit_path = os.path.join(HERE, 'slots5_fit.json')
    if mode in ('fit', 'all'):
        data = data_for(ref); fits = {}
        for s in SLOTS:
            tot = sum(counts[s].values()); g0 = {v: c / tot for v, c in counts[s].items()}
            print(f'fitting {s} in context ({len(counts[s])} values, {len({p[1] for p, _ in data[s]})} contexts)', flush=True)
            fits[s] = fit(data[s], g0, random.Random(7), SWEEPS)
            print(f'  done {time.time() - t0:.0f}s; d ' + ' '.join(f'{x:.2f}' for x in fits[s]['d']) + ' theta ' + ' '.join(f'{x:.1f}' for x in fits[s]['theta'])
                  + ' passed up ' + ' '.join(f"{fits[s]['share_new_at_level'][l]:.2f}" for l in LEVELS), flush=True)
        json.dump(fits, open(fit_path, 'w'), indent=1)
    if mode in ('generate', 'all'):
        fits = json.load(open(fit_path))
        R = hpy.reference(ref, os.path.join(HERE, 'reference_battery.json'))
        voc = set(words); gen = collections.OrderedDict(); extra = {}; meta = {}; kept = None
        for seed in SEEDS:
            tpl = hpy.Template(sorted(v for v in counts['middle'] if v != EMPTY), random.Random(seed + 100))
            g0s = dict(opener=Mixture(counts['opener'], None, 0.0, random.Random(seed + 50)),
                       middle=Mixture(counts['middle'], tpl, 0.2, random.Random(seed + 51)),
                       ending=Mixture(counts['ending'], None, 0.0, random.Random(seed + 52)))
            gen[f'chain5_s{seed}'], real, kept = generate(ref, fits, g0s, seed)
            meta[f'chain5_s{seed}'] = dict(realised=real)
        results = collections.OrderedDict(R)
        for name, pgs in gen.items():
            results[name] = b3.battery(pgs, name, extra)
            ntok = sum(len(ln['words']) for p in pgs for ln in p['lines'])
            meta[name].update(scribe=hpy.scribe_ratios(pgs, random.Random(17)), drift=hpy.drift(pgs), coupling=coupling(pgs),
                              voynich_types_share=sum(1 for p in pgs for ln in p['lines'] for w in ln['words'] if w in voc) / ntok)
            print(name, 'scored', f'{time.time() - t0:.0f}s', flush=True)
        meta['voynich_ZL'] = dict(scribe=hpy.scribe_ratios(ref, random.Random(17)), drift=hpy.drift(ref), coupling=coupling(ref), voynich_types_share=1.0)
        tol, marks = b3.score(results)
        json.dump(dict(results=results, marks=marks, tol=tol, meta=meta, fits=fits, kept=kept), open(os.path.join(HERE, 'slots5_gen_results.json'), 'w'), indent=1)
        L = ['# Slot-level reinforcing improviser v5: chained slots, each in the context of the previous (10 Nov 2026)', '', 'Script `slots5.py`. Fitted (d; theta; share passed up), levels ' + ' > '.join(LEVELS) + ':']
        for s in SLOTS:
            L.append(f"- {s}: d " + ', '.join(f'{x:.2f}' for x in fits[s]['d']) + '; theta ' + ', '.join(f'{x:.1f}' for x in fits[s]['theta'])
                     + '; passed up ' + ', '.join(f"{l} {fits[s]['share_new_at_level'][l]:.2f}" for l in LEVELS) + f'; kept {kept[s]}')
        L.append(''); L.append('Self-consistency: share passed up in generation (seed 19) against the fit, per kept level:')
        for s in SLOTS:
            r = meta['chain5_s19']['realised'][s]
            L.append(f"- {s}: " + ', '.join(f"{l} {r[l]:.2f} (fit {fits[s]['share_new_at_level'][l]:.2f})" for l in kept[s] if r[l] is not None))
        L.append(''); L.append('Match rule as b3; held-out = the 30 items outside hybrid_model.TUNED_B3. Scribe ratios as scribe_ratio.py.'); L.append('')
        L.append('| text | matched/37 | held-out/30 | between scribes / within | same scribe other doc / within | JSD A vs B | JSD quire halves in cell | edge X within | edge X across line | Voynich types share |')
        L.append('|---|---|---|---|---|---|---|---|---|---|')
        for name in results:
            m = marks[name]; tot = sum(m.values()); held = sum(v for k, v in m.items() if k not in hpy.TUNED); md = meta.get(name)
            if md and 'scribe' in md:
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
        open(os.path.join(HERE, 'slots5_gen.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L[:22]))


if __name__ == '__main__':
    main()
