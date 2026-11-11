"""Slot-level hierarchical Pitman-Yor: the reinforcing improviser at the level of word parts. (10 Nov 2026)

Why. hpy.py fitted a hierarchical Pitman-Yor model to whole words and found discounts near 1 at every level below
the book: a whole-word model sees little to re-use on a page or in a line, because Voynich's locality is mostly in
near-copies (one-glyph variants: 0.64 of tokens have an LD<=1 twin on the page, exact repeats add 0.03 of tokens
over the hand/section/quire vocabulary). So the unit that is re-used is the word part, not the word. Here each word
is parsed into the four slots of meaning/slots_ab.py (prefix | gallows | middle | ending) and each slot gets its own
hierarchical PY over book > hand > section > quire > page > line. A word is the concatenation of one draw per slot
(slots independent given the location, the Fontana-wheel picture of slot_independence.md). Re-using a recent prefix
and middle with a fresh ending gives a near-copy; a hand's reinforced endings give the A/B convention; a line's
re-use gives adjacent repeats.

Fit: as hpy.fit per slot (Gibbs seating + hyperparameter sampling), G0 uniform over the slot's observed values.
Generate: fresh restaurants with the fitted (d, theta) of each slot on the real skeleton; G0 = the slot's empirical
token distribution (borrowed from Voynich, like the earlier improviser's template), for the middle mixed 4:1 with a
glyph-unit trigram template over middle types so that new middles can be invented. Variants: plain; +gallows
(hybrid_model line-initial gallows, g 0.2); +scribe (full hybridize q 0.15 w 8 e 0.9 g 0.2). Seeds 19 and 7.
Score: b3 battery (37 items, held-out 30 as hybrid_model.TUNED_B3), scribe ratios, drift (A vs B JSD, quire halves
within hand x section), within-line and across-line edge coupling (lines/boundaries.py).

Run from targets/voynich: python reinforce/slots.py fit | generate | all
"""
import collections, json, math, os, random, statistics, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..')
sys.path.insert(0, HERE); sys.path.insert(0, VOY); sys.path.insert(0, os.path.join(VOY, 'lines')); sys.path.insert(0, os.path.join(VOY, 'meaning'))
sys.path.insert(0, os.path.join(VOY, '..', '..', 'research', 'voynich_siblings'))
import hpy, common, boundaries, a4_selfcitation as a4, b3_bakeoff as b3
import hybrid_model as hm
from slots_ab import parse, SLOTS

EMPTY = '~'
SWEEPS = int(os.environ.get('HPY_SWEEPS', '60'))


def slot_pages(pgs, slot):
    out = []
    for p in pgs:
        q = {k: p[k] for k in ('folio', 'hand', 'lang', 'quire', 'illus')}
        q['lines'] = [{'words': [parse(w)[slot] or EMPTY for w in ln['words']], 'para_start': ln['para_start']} for ln in p['lines']]
        out.append(q)
    return out


class Mixture:
    def __init__(self, counts, template, w_template, rng):
        self.vals = list(counts); self.wts = [float(counts[v]) for v in self.vals]
        self.template, self.wt, self.rng = template, w_template, rng

    def sample(self):
        if self.template is not None and self.rng.random() < self.wt:
            s = self.template.sample()
            return s if s else EMPTY
        return self.rng.choices(self.vals, weights=self.wts)[0]


def generate(ref, fits, g0s, seed):
    rng = random.Random(seed)
    models = {s: hpy.Sampler(fits[s]['d'], fits[s]['theta'], g0s[s]) for s in SLOTS}
    out = []
    for p in ref:
        base = ('book', 'h' + p['hand'], 's' + p['illus'], 'q' + p['quire'], p['folio'])
        lines = []
        for li, ln in enumerate(p['lines']):
            nodes = {s: models[s].node(base + (f'l{li}',)) for s in SLOTS}
            ws = []
            for _ in ln['words']:
                parts = [models[s].draw(nodes[s], rng) for s in SLOTS]
                w = ''.join('' if x in (EMPTY, '-') else x for x in parts)
                ws.append(w if w else 'o')
            lines.append({'words': ws, 'para_start': ln['para_start']})
        q = {k: p[k] for k in ('folio', 'hand', 'lang', 'quire', 'illus')}; q['lines'] = lines; out.append(q)
    return out


def coupling(pgs):
    K = boundaries.pair_kinds(pgs); rng = random.Random(5)
    return {k: (boundaries.coupling(K[k], rng) or {}).get('X') for k in ('within', 'line_break')}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'all'
    t0 = time.time()
    ref = common.pages()
    fit_path = os.path.join(HERE, 'slots_fit.json')
    if mode in ('fit', 'all'):
        fits = {}
        for s in SLOTS:
            sp = slot_pages(ref, s)
            print(f'fitting slot {s} ({len({w for p in sp for ln in p["lines"] for w in ln["words"]})} values)', flush=True)
            fits[s] = hpy.fit(sp, random.Random(7), sweeps=SWEEPS, log=True, fixed_sweeps=10)
            print(f'  done {time.time() - t0:.0f}s; d ' + ' '.join(f'{x:.2f}' for x in fits[s]['d']) + ' theta ' + ' '.join(f'{x:.1f}' for x in fits[s]['theta']), flush=True)
        json.dump(fits, open(fit_path, 'w'), indent=1)
    if mode in ('generate', 'all'):
        fits = json.load(open(fit_path))
        R = hpy.reference(ref, os.path.join(HERE, 'reference_battery.json'))
        counts = {s: collections.Counter(parse(w)[s] or EMPTY for p in ref for ln in p['lines'] for w in ln['words']) for s in SLOTS}
        voc = {w for p in ref for ln in p['lines'] for w in ln['words']}
        gen = collections.OrderedDict(); extra = {}; meta = {}
        for seed in (19, 7):
            tpl = hpy.Template(sorted(v for v in counts['middle'] if v != EMPTY), random.Random(seed + 100))
            g0s = {s: Mixture(counts[s], tpl if s == 'middle' else None, 0.2, random.Random(seed + 50)) for s in SLOTS}
            plain = generate(ref, fits, g0s, seed)
            gen[f'slots_s{seed}'] = plain
            gen[f'slots_gallows_s{seed}'] = common.with_meta(hm.hybridize(plain, random.Random(seed + 200), 0.0, 8, 0.0, 0.2), ref)
            gen[f'slots_scribe_s{seed}'] = common.with_meta(hm.hybridize(plain, random.Random(seed + 300), 0.15, 8, 0.9, 0.2), ref)
        results = collections.OrderedDict(R)
        for name, pgs in gen.items():
            results[name] = b3.battery(pgs, name, extra)
            ntok = sum(len(ln['words']) for p in pgs for ln in p['lines'])
            meta[name] = dict(scribe=hpy.scribe_ratios(pgs, random.Random(17)), drift=hpy.drift(pgs), coupling=coupling(pgs),
                              voynich_types_share=sum(1 for p in pgs for ln in p['lines'] for w in ln['words'] if w in voc) / ntok)
            print(name, 'scored', f'{time.time() - t0:.0f}s', flush=True)
        meta['voynich_ZL'] = dict(scribe=hpy.scribe_ratios(ref, random.Random(17)), drift=hpy.drift(ref), coupling=coupling(ref), voynich_types_share=1.0)
        tol, marks = b3.score(results)
        json.dump(dict(results=results, marks=marks, tol=tol, meta=meta, fits=fits), open(os.path.join(HERE, 'slots_gen_results.json'), 'w'), indent=1)
        L = ['# Slot-level reinforcing improviser against the b3 battery, scribe ratios, drift and edge coupling (10 Nov 2026)', '',
             'Script `slots.py`. Fitted (d; theta) per slot, levels ' + ' > '.join(hpy.LEVELS) + ':']
        for s in SLOTS:
            L.append(f"- {s}: d " + ', '.join(f'{x:.2f}' for x in fits[s]['d']) + '; theta ' + ', '.join(f'{x:.1f}' for x in fits[s]['theta']))
        L.append('')
        L.append('Match rule as b3; held-out = the 30 items outside hybrid_model.TUNED_B3 (nothing here was tuned on the battery). Scribe ratios as scribe_ratio.py.')
        L.append('')
        L.append('| text | matched/37 | held-out/30 | between scribes / within | same scribe other doc / within | JSD A vs B | JSD quire halves in cell | edge X within | edge X across line | Voynich types share |')
        L.append('|---|---|---|---|---|---|---|---|---|---|')
        for name in results:
            m = marks[name]; tot = sum(m.values()); held = sum(v for k, v in m.items() if k not in hpy.TUNED)
            md = meta.get(name)
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
        open(os.path.join(HERE, 'slots_gen.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L[:16]))


if __name__ == '__main__':
    main()
