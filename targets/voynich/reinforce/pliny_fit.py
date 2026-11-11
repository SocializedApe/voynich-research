"""Reuse profile of a real topical text laid out leaf by leaf: Pliny (meaning/pliny.py 'sectioned' and 'stream')
under the whole-word hierarchical Pitman-Yor fit of hpy.py, for comparison with Voynich and the poured controls.

Run from targets/voynich: python reinforce/pliny_fit.py -> reinforce/pliny_fit.json, pliny_fit.md
"""
import json, os, random, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..')
sys.path.insert(0, HERE); sys.path.insert(0, VOY); sys.path.insert(0, os.path.join(VOY, 'lines')); sys.path.insert(0, os.path.join(VOY, 'meaning'))
import hpy, common, a4_selfcitation as a4
import pliny


def main():
    t0 = time.time()
    ref = common.pages(); skel = a4.skeleton(ref)
    groups, sections = pliny.leaves_of(ref)
    sec_pages = common.with_meta(pliny.pour_pages(pliny.sectioned_words(ref, skel, groups, sections), skel), ref)
    N = sum(len(ln['words']) for p in ref for ln in p['lines'])
    stream = []
    for b in pliny.STREAM:
        for c in pliny.chapters(b):
            stream += pliny.latin_words(c)
            if len(stream) >= N:
                break
        if len(stream) >= N:
            break
    str_pages = common.with_meta(a4.pour(stream[:N], skel), ref)
    res = {}
    for name, pgs in (('pliny_sectioned', sec_pages), ('pliny_stream', str_pages)):
        print('fitting', name, flush=True)
        res[name] = hpy.fit(pgs, random.Random(7), sweeps=hpy.SWEEPS, log=True)
        print(f'  done {time.time() - t0:.0f}s', flush=True)
    json.dump(res, open(os.path.join(HERE, 'pliny_fit.json'), 'w'), indent=1)
    L = ['# Whole-word HPY reuse profile of Pliny laid out leaf by leaf, and as a stream (10 Nov 2026)', '',
         '| text | tokens | types | ' + ' | '.join(f'd {l}' for l in hpy.LEVELS) + ' | ' + ' | '.join(f'theta {l}' for l in hpy.LEVELS) + ' | ' + ' | '.join(f'passed up {l}' for l in hpy.LEVELS) + ' |',
         '|' + '---|' * (3 + 3 * len(hpy.LEVELS))]
    for name, r in res.items():
        L.append(f"| {name} | {r['tokens']} | {r['types']} | " + ' | '.join(f'{x:.2f}' for x in r['d']) + ' | ' + ' | '.join(f'{x:.1f}' for x in r['theta']) + ' | '
                 + ' | '.join(f"{r['share_new_at_level'][l]:.3f}" for l in hpy.LEVELS) + ' |')
    open(os.path.join(HERE, 'pliny_fit.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    main()
