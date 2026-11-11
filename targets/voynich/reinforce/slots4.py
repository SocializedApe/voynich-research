"""Slot-level reinforcing improviser, fourth version: opener in context | middle | ending, with a self-consistency
check. (10 Nov 2026)

slots3.py reproduced the line-bound chain but, with the near-degenerate levels pruned, lost the scribe differences:
the tail (3,762 values, 70% hapax) had been fitted with discounts at 1 at the language, hand and section levels, so
its A/B convention (-edy against -ol, -y) had nowhere to live once those levels were dropped, and in slots2 it had
lived in exactly those degenerate levels, whose rich-get-richer rule in generation can lock onto early tables.
Here the tail is split into middle (1,823 values) and ending (30 values, where the A/B convention is strongest,
slots_ab.py), each with its own location hierarchy (book > lang > hand > section > quire > page > line); the opener
keeps the slots3 context hierarchy. Levels with fitted d >= 0.99 are dropped from the generation.
Self-consistency: for every slot and level, the share of draws passed up in generation (tables / customers at the
end) is compared with the fitted share; a generation that re-uses much more than the fit at some level has locked
onto early tables there and is not a faithful sample of the fitted model.

Scoring as slots2.py, five seeds. Run from targets/voynich: python reinforce/slots4.py fit | generate | all
"""
import collections, json, math, os, random, statistics, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..')
sys.path.insert(0, HERE); sys.path.insert(0, VOY); sys.path.insert(0, os.path.join(VOY, 'lines')); sys.path.insert(0, os.path.join(VOY, 'meaning'))
sys.path.insert(0, os.path.join(VOY, '..', '..', 'research', 'voynich_siblings'))
import hpy, common, a4_selfcitation as a4, b3_bakeoff as b3
import slots2, slots3
from slots import EMPTY, Mixture, coupling
from slots_ab import parse

LOC = slots2.LEVELS           # book > lang > hand > section > quire > page > line
OPL = slots3.OPENER_LEVELS    # book > context > lang > hand > section > quire > page > line
SWEEPS = int(os.environ.get('HPY_SWEEPS', '60'))
SEEDS = (19, 7, 3, 11, 23)
SLOTS = ('opener', 'middle', 'ending')


def split3(w):
    d = parse(w); gal = d['gallows'] if d['gallows'] != '-' else ''
    return tuple(x or EMPTY for x in (d['prefix'] + gal, d['middle'], d['ending']))


def loc_data(pgs, slot_index):
    data = []
    for p in pgs:
        base = ('book', 'L' + p['lang'], 'h' + p['hand'], 's' + p['illus'], 'q' + p['quire'], p['folio'])
        for li, ln in enumerate(p['lines']):
            path = base + (f'l{li}',)
            for w in ln['words']:
                data.append((path, split3(w)[slot_index]))
    return data


def realised(pr):
    """share passed up per level of a Pruned sampler after generation"""
    out = {}
    for i, l in enumerate(pr.levels):
        t = sum(n.t for n in pr.m.nodes.values() if n.level == i); c = sum(n.c for n in pr.m.nodes.values() if n.level == i)
        out[l] = t / c if c else None
    return out


def generate(ref, fits, g0s, seed):
    rng = random.Random(seed)
    op = slots3.Pruned(OPL, fits['opener'], g0s['opener'])
    mid = slots3.Pruned(LOC, fits['middle'], g0s['middle']); end = slots3.Pruned(LOC, fits['ending'], g0s['ending'])
    out = []
    for p in ref:
        loc = ('L' + p['lang'], 'h' + p['hand'], 's' + p['illus'], 'q' + p['quire'], p['folio'])
        lines = []
        for li, ln in enumerate(p['lines']):
            prev = None; ws = []
            for _ in ln['words']:
                o = op.draw(('book', 'c' + slots3.ctx_of(prev)) + loc + (f'l{li}',), rng)
                m = mid.draw(('book',) + loc + (f'l{li}',), rng); e = end.draw(('book',) + loc + (f'l{li}',), rng)
                tail = ('' if m == EMPTY else m) + ('' if e == EMPTY else e)
                w = ('' if o == EMPTY else o) + tail
                ws.append(w if w else 'o'); prev = tail or EMPTY
            lines.append({'words': ws, 'para_start': ln['para_start']})
        q = {k: p[k] for k in ('folio', 'hand', 'lang', 'quire', 'illus')}; q['lines'] = lines; out.append(q)
    return out, dict(opener=realised(op), middle=realised(mid), ending=realised(end)), dict(opener=op.levels, middle=mid.levels, ending=end.levels)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'all'
    t0 = time.time(); ref = common.pages()
    words = [w for p in ref for ln in p['lines'] for w in ln['words']]
    counts = {s: collections.Counter(split3(w)[i] for w in words) for i, s in enumerate(SLOTS)}
    fit_path = os.path.join(HERE, 'slots4_fit.json')
    if mode in ('fit', 'all'):
        fits = dict(opener=json.load(open(os.path.join(HERE, 'slots3_fit.json')))['opener'])
        ome = os.path.join(HERE, 'slots2_ome_fit.json')   # same data, hierarchy, base and seed as the middle/ending fits here
        if os.path.exists(ome):
            fits.update({s: v for s, v in json.load(open(ome)).items() if s in ('middle', 'ending')})
        for i, s in enumerate(SLOTS):
            if s == 'opener' or s in fits:
                continue
            tot = sum(counts[s].values()); g0 = {v: c / tot for v, c in counts[s].items()}
            print(f'fitting {s} ({len(counts[s])} values)', flush=True)
            fits[s] = slots2.fit(loc_data(ref, i), g0, random.Random(7), SWEEPS)
            print(f'  done {time.time() - t0:.0f}s; d ' + ' '.join(f'{x:.2f}' for x in fits[s]['d']) + ' theta ' + ' '.join(f'{x:.1f}' for x in fits[s]['theta'])
                  + ' passed up ' + ' '.join(f"{fits[s]['share_new_at_level'][l]:.2f}" for l in LOC), flush=True)
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
            gen[f'ome4_s{seed}'], real, kept = generate(ref, fits, g0s, seed)
            meta[f'ome4_s{seed}'] = dict(realised=real)
        results = collections.OrderedDict(R)
        for name, pgs in gen.items():
            results[name] = b3.battery(pgs, name, extra)
            ntok = sum(len(ln['words']) for p in pgs for ln in p['lines'])
            meta[name].update(scribe=hpy.scribe_ratios(pgs, random.Random(17)), drift=hpy.drift(pgs), coupling=coupling(pgs),
                              voynich_types_share=sum(1 for p in pgs for ln in p['lines'] for w in ln['words'] if w in voc) / ntok)
            print(name, 'scored', f'{time.time() - t0:.0f}s', flush=True)
        meta['voynich_ZL'] = dict(scribe=hpy.scribe_ratios(ref, random.Random(17)), drift=hpy.drift(ref), coupling=coupling(ref), voynich_types_share=1.0)
        tol, marks = b3.score(results)
        json.dump(dict(results=results, marks=marks, tol=tol, meta=meta, fits=fits, kept=kept), open(os.path.join(HERE, 'slots4_gen_results.json'), 'w'), indent=1)
        L = ['# Slot-level reinforcing improviser v4: opener in context | middle | ending (10 Nov 2026)', '', 'Script `slots4.py`. Fitted (d; theta; share passed up):']
        for s in SLOTS:
            lv = OPL if s == 'opener' else LOC
            L.append(f"- {s}: d " + ', '.join(f'{x:.2f}' for x in fits[s]['d']) + '; theta ' + ', '.join(f'{x:.1f}' for x in fits[s]['theta'])
                     + '; passed up ' + ', '.join(f"{l} {fits[s]['share_new_at_level'][l]:.2f}" for l in lv) + f'; kept in generation {kept[s]}')
        L.append(''); L.append('Self-consistency: share passed up in generation (seed 19) against the fit, per kept level:')
        for s in SLOTS:
            r = meta['ome4_s19']['realised'][s]
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
        open(os.path.join(HERE, 'slots4_gen.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L[:22]))


if __name__ == '__main__':
    main()
