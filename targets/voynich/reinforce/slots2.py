"""Slot-level reinforcing improviser, second version. (10 Nov 2026)

Changes from slots.py, each answering a miss of the first version (slots_gen.md):
  - the prefix and the gallows are one slot, the opener (prefix + gallows, 50 values): generated independently they
    gave words starting with a bare gallows 5 times too often (Voynich writes o-/qo- before a gallows);
  - two slot schemes are run: 'ot' = opener | tail (tail = middle + ending, 4,300 values), the split at which
    slot_independence.md measured the smallest start-end dependence in Voynich; 'ome' = opener | middle | ending;
  - a Currier-language level sits between the book and the hands (book > lang > hand > section > quire > page >
    line), because the main convention difference is A/B and hand 3 writes both: without it each hand's
    restaurant drifted on its own and the scribe differences overshot;
  - the fit uses the same base distribution as the generation: the slot's empirical token distribution (borrowed
    from Voynich, as before); for tail and middle the generation mixes in 20% of a glyph-unit trigram template
    over the slot's types so that new values can be invented.
Scoring as slots.py (b3 battery, held-out 30 items, scribe ratios, A/B and quire drift, edge coupling), seeds 19, 7, 3.

Run from targets/voynich: python reinforce/slots2.py fit | generate | all   [ot|ome]
"""
import collections, json, math, os, random, statistics, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..')
sys.path.insert(0, HERE); sys.path.insert(0, VOY); sys.path.insert(0, os.path.join(VOY, 'lines')); sys.path.insert(0, os.path.join(VOY, 'meaning'))
sys.path.insert(0, os.path.join(VOY, '..', '..', 'research', 'voynich_siblings'))
import hpy, common, boundaries, a4_selfcitation as a4, b3_bakeoff as b3
import hybrid_model as hm
from slots_ab import parse
from slots import EMPTY, Mixture, coupling

LEVELS = ['book', 'lang', 'hand', 'section', 'quire', 'page', 'line']
SCHEMES = {'ot': ('opener', 'tail'), 'ome': ('opener', 'middle', 'ending')}
SWEEPS = int(os.environ.get('HPY_SWEEPS', '60'))


def split(w, scheme):
    d = parse(w); gal = d['gallows'] if d['gallows'] != '-' else ''
    if scheme == 'ot':
        parts = (d['prefix'] + gal, d['middle'] + d['ending'])
    else:
        parts = (d['prefix'] + gal, d['middle'], d['ending'])
    return tuple(x or EMPTY for x in parts)


def paths_of(pgs, slot_index, scheme):
    data = []
    for p in pgs:
        base = ('book', 'L' + p['lang'], 'h' + p['hand'], 's' + p['illus'], 'q' + p['quire'], p['folio'])
        for li, ln in enumerate(p['lines']):
            path = base + (f'l{li}',)
            for w in ln['words']:
                data.append((path, split(w, scheme)[slot_index]))
    return data


def fit(data, g0, rng, sweeps, fixed_sweeps=10, log=True):
    m = hpy.HPY([0.5] * len(LEVELS), [1.0] * len(LEVELS), g0)
    for path, w in data:
        m.add(m.node(path), w, rng)
    order = list(range(len(data))); hist = []
    for s in range(sweeps):
        rng.shuffle(order)
        for i in order:
            path, w = data[i]; n = m.nodes[path]; m.remove(n, w, rng); m.add(n, w, rng)
        if s >= fixed_sweeps:
            m.resample_hyper(rng)
        if log and (s % 10 == 9 or s == sweeps - 1):
            print(f'  sweep {s + 1}: d ' + ' '.join(f'{x:.2f}' for x in m.d) + ' | theta ' + ' '.join(f'{x:.1f}' for x in m.theta), flush=True)
        hist.append((list(m.d), list(m.theta)))
    half = hist[len(hist) // 2:]
    d = [statistics.mean(h[0][i] for h in half) for i in range(len(LEVELS))]
    th = [statistics.mean(h[1][i] for h in half) for i in range(len(LEVELS))]
    tables = {LEVELS[l]: sum(n.t for n in m.nodes.values() if n.level == l) for l in range(len(LEVELS))}
    custs = {LEVELS[l]: sum(n.c for n in m.nodes.values() if n.level == l) for l in range(len(LEVELS))}
    return dict(d=d, theta=th, share_new_at_level={LEVELS[l]: tables[LEVELS[l]] / custs[LEVELS[l]] for l in range(len(LEVELS))})


def generate(ref, fits, g0s, scheme, seed):
    rng = random.Random(seed); slots = SCHEMES[scheme]
    models = {s: hpy.Sampler(fits[s]['d'], fits[s]['theta'], g0s[s]) for s in slots}
    out = []
    for p in ref:
        base = ('book', 'L' + p['lang'], 'h' + p['hand'], 's' + p['illus'], 'q' + p['quire'], p['folio'])
        lines = []
        for li, ln in enumerate(p['lines']):
            nodes = {s: models[s].node(base + (f'l{li}',)) for s in slots}
            ws = []
            for _ in ln['words']:
                w = ''.join('' if x == EMPTY else x for x in (models[s].draw(nodes[s], rng) for s in slots))
                ws.append(w if w else 'o')
            lines.append({'words': ws, 'para_start': ln['para_start']})
        q = {k: p[k] for k in ('folio', 'hand', 'lang', 'quire', 'illus')}; q['lines'] = lines; out.append(q)
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'all'
    schemes = [a for a in sys.argv[2:] if a in SCHEMES] or list(SCHEMES)
    t0 = time.time(); ref = common.pages()
    words = [w for p in ref for ln in p['lines'] for w in ln['words']]
    for scheme in schemes:
        slots = SCHEMES[scheme]
        fit_path = os.path.join(HERE, f'slots2_{scheme}_fit.json')
        counts = {s: collections.Counter(split(w, scheme)[i] for w in words) for i, s in enumerate(slots)}
        if mode in ('fit', 'all'):
            fits = {}
            for i, s in enumerate(slots):
                data = paths_of(ref, i, scheme); tot = sum(counts[s].values())
                g0 = {v: c / tot for v, c in counts[s].items()}
                print(f'[{scheme}] fitting slot {s} ({len(counts[s])} values)', flush=True)
                fits[s] = fit(data, g0, random.Random(7), SWEEPS)
                print(f'  done {time.time() - t0:.0f}s; d ' + ' '.join(f'{x:.2f}' for x in fits[s]['d']) + ' theta ' + ' '.join(f'{x:.1f}' for x in fits[s]['theta'])
                      + ' new/cust ' + ' '.join(f"{fits[s]['share_new_at_level'][l]:.2f}" for l in LEVELS), flush=True)
            json.dump(fits, open(fit_path, 'w'), indent=1)
        if mode in ('generate', 'all'):
            fits = json.load(open(fit_path))
            R = hpy.reference(ref, os.path.join(HERE, 'reference_battery.json'))
            voc = set(words); gen = collections.OrderedDict(); extra = {}; meta = {}
            for seed in (19, 7, 3):
                g0s = {}
                for s in slots:
                    tpl = hpy.Template(sorted(v for v in counts[s] if v != EMPTY), random.Random(seed + 100)) if s in ('tail', 'middle') else None
                    g0s[s] = Mixture(counts[s], tpl, 0.2, random.Random(seed + 50))
                plain = generate(ref, fits, g0s, scheme, seed)
                gen[f'{scheme}_s{seed}'] = plain
                gen[f'{scheme}_gallows_s{seed}'] = common.with_meta(hm.hybridize(plain, random.Random(seed + 200), 0.0, 8, 0.0, 0.2), ref)
            results = collections.OrderedDict(R)
            for name, pgs in gen.items():
                results[name] = b3.battery(pgs, name, extra)
                ntok = sum(len(ln['words']) for p in pgs for ln in p['lines'])
                meta[name] = dict(scribe=hpy.scribe_ratios(pgs, random.Random(17)), drift=hpy.drift(pgs), coupling=coupling(pgs),
                                  voynich_types_share=sum(1 for p in pgs for ln in p['lines'] for w in ln['words'] if w in voc) / ntok)
                print(name, 'scored', f'{time.time() - t0:.0f}s', flush=True)
            meta['voynich_ZL'] = dict(scribe=hpy.scribe_ratios(ref, random.Random(17)), drift=hpy.drift(ref), coupling=coupling(ref), voynich_types_share=1.0)
            tol, marks = b3.score(results)
            json.dump(dict(results=results, marks=marks, tol=tol, meta=meta, fits=fits), open(os.path.join(HERE, f'slots2_{scheme}_gen_results.json'), 'w'), indent=1)
            L = [f'# Slot-level reinforcing improviser v2, scheme {scheme} ({" | ".join(slots)}) (10 Nov 2026)', '',
                 'Script `slots2.py`. Fitted (d; theta; share passed up) per slot, levels ' + ' > '.join(LEVELS) + ':']
            for s in slots:
                L.append(f"- {s}: d " + ', '.join(f'{x:.2f}' for x in fits[s]['d']) + '; theta ' + ', '.join(f'{x:.1f}' for x in fits[s]['theta'])
                         + '; passed up ' + ', '.join(f"{fits[s]['share_new_at_level'][l]:.2f}" for l in LEVELS))
            L.append(''); L.append('Match rule as b3; held-out = the 30 items outside hybrid_model.TUNED_B3. Scribe ratios as scribe_ratio.py.'); L.append('')
            L.append('| text | matched/37 | held-out/30 | between scribes / within | same scribe other doc / within | JSD A vs B | JSD quire halves in cell | edge X within | edge X across line | Voynich types share |')
            L.append('|---|---|---|---|---|---|---|---|---|---|')
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
            open(os.path.join(HERE, f'slots2_{scheme}_gen.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L[:14]))


if __name__ == '__main__':
    main()
