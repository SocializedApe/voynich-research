"""Two robustness checks on the battery scores of the generators. (11 Nov 2026)

1. Ceiling: how many of the 37 battery items does Voynich match against itself? The book is split in two and one
   half is scored against the other with the b3 rule (tolerance = max(10% of the reference half, spread of two
   autocopist seeds on the reference half's skeleton)). If a half of Voynich matches the other half on about as many
   items as a generator matches Voynich, the generators are at the ceiling of the rule.
2. Held out: slots8's best variants borrow their tables (and, for lang8, the convention) from the text they are
   scored against. Here everything borrowed or estimated comes from one half and the text is generated on the
   skeleton of the other half and scored against that other half ('held-out'), beside the same variant built from
   and scored against the same half ('in-sample').
Splits: odd/even pages (interleaved), alternate quires, first/second half of the pages (the last confounds A/B).
Both directions of each split. Variants lang8 and cat8p of slots8.py, five seeds. Held-out counts use the 30 items
outside hybrid_model.TUNED_B3.

Run from targets/voynich: python reinforce/robust.py run <oddeven|quires|halves> ... ; python reinforce/robust.py report
-> reinforce/robust_<split>.json, robust.md
"""
import collections, json, os, random, statistics, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..')
sys.path.insert(0, HERE); sys.path.insert(0, VOY); sys.path.insert(0, os.path.join(VOY, 'lines')); sys.path.insert(0, os.path.join(VOY, 'meaning'))
sys.path.insert(0, os.path.join(VOY, '..', '..', 'research', 'voynich_siblings'))
import hpy, common, a4_selfcitation as a4, b3_bakeoff as b3
import slots8

SPLITS = ('oddeven', 'quires', 'halves'); VARS = ('lang8', 'cat8p'); SEEDS = slots8.SEEDS


def split(ref, how):
    if how == 'oddeven':
        return ref[0::2], ref[1::2]
    if how == 'halves':
        return ref[:len(ref) // 2], ref[len(ref) // 2:]
    order = list(collections.OrderedDict((p['quire'], 1) for p in ref)); par = {q: i % 2 for i, q in enumerate(order)}
    return [p for p in ref if par[p['quire']] == 0], [p for p in ref if par[p['quire']] == 1]


def ntok(pp):
    return sum(len(ln['words']) for p in pp for ln in p['lines'])


def main():
    t0 = time.time(); ref = common.pages()
    if sys.argv[1] == 'run':
        for how in sys.argv[2:]:
            out = collections.OrderedDict()
            for d, (X, Y) in enumerate((split(ref, how), split(ref, how)[::-1])):
                extra = {}; R = collections.OrderedDict(); skel = a4.skeleton(X)
                R['voynich_ZL'] = b3.battery(X, 'real', extra)
                for s in (19, 7):
                    R[f'autocopist_s{s}'] = b3.battery(common.with_meta(a4.Autocopist(s).generate(skel), X), 'ac', extra)
                R['other_half'] = b3.battery(Y, 'other', extra)
                for v in VARS:
                    for seed in SEEDS:
                        R[f'{v}_in_s{seed}'] = b3.battery(slots8.generate(v, X, seed)[0], 'g', extra)
                        R[f'{v}_out_s{seed}'] = b3.battery(slots8.generate(v, Y, seed, skel=X)[0], 'g', extra)
                        print(how, d, v, seed, f'{time.time() - t0:.0f}s', flush=True)
                tol, marks = b3.score(R)
                out[f'direction{d}'] = dict(tokens_reference=ntok(X), tokens_other=ntok(Y), results=R, marks=marks, tol=tol)
                json.dump(out, open(os.path.join(HERE, f'robust_{how}.json'), 'w'), indent=1)
        return
    L = ['# Battery ceiling and held-out generation (11 Nov 2026)', '', 'Script `robust.py` (protocol in its docstring). Reproduce: `python reinforce/robust.py run oddeven quires halves`, then `python reinforce/robust.py report`.', '',
         '| split | reference half (tokens) | other half of Voynich: matched/37 | held-out/30 | lang8 in-sample /37 | lang8 held-out /37 | cat8p in-sample /37 | cat8p held-out /37 | items the other half misses |', '|---|---|---|---|---|---|---|---|---|']
    res = {}
    for how in SPLITS:
        f = os.path.join(HERE, f'robust_{how}.json')
        if not os.path.exists(f):
            continue
        o = json.load(open(f))
        for d, r in o.items():
            m = r['marks']; tot = lambda n: sum(m[n].values()); held = lambda n: sum(v for k, v in m[n].items() if k not in hpy.TUNED)
            def rg(prefix, f_=tot):
                xs = [f_(n) for n in m if n.startswith(prefix)]
                return f'{min(xs)}-{max(xs)}' if xs else '-'
            miss = ', '.join(k for k, v in m['other_half'].items() if not v)
            L.append(f"| {how}, {d[-1]} | {r['tokens_reference']} | {tot('other_half')} | {held('other_half')} | {rg('lang8_in')} | {rg('lang8_out')} | {rg('cat8p_in')} | {rg('cat8p_out')} | {miss} |")
            res[f'{how}_{d}'] = dict(other=tot('other_half'), other_held=held('other_half'), **{f'{v}_{io}': [tot(n) for n in m if n.startswith(f'{v}_{io}')] for v in VARS for io in ('in', 'out')})
    json.dump(res, open(os.path.join(HERE, 'robust_results.json'), 'w'), indent=1)
    L.append(''); open(os.path.join(HERE, 'robust.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    main()
