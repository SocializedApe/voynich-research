"""d2_compare_runs.py -- compare the results/*.json of two runs of the Voynich scripts, number by number.

usage: python d2_compare_runs.py <results dir A> <results dir B> [--rel 0.01] [--filter voynich]
Every JSON is flattened to path -> number; a pair is reported when |a - b| > rel * max(|a|, |b|, 1e-9). With
--filter, only paths containing that text (case-insensitive) are listed. Prints, per file, the number of numeric
leaves, how many differ, and the differing paths with both values.
"""
import json, os, sys


def flat(x, p=''):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from flat(v, f'{p}/{k}')
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from flat(v, f'{p}[{i}]')
    elif isinstance(x, (int, float)) and not isinstance(x, bool):
        yield p, float(x)


def main():
    a, b = sys.argv[1], sys.argv[2]
    rel = float(sys.argv[sys.argv.index('--rel') + 1]) if '--rel' in sys.argv else 0.01
    filt = sys.argv[sys.argv.index('--filter') + 1].lower() if '--filter' in sys.argv else None
    for fn in sorted(f for f in os.listdir(a) if f.endswith('.json')):
        fb = os.path.join(b, fn)
        if not os.path.exists(fb):
            print(f'{fn}: missing in B'); continue
        da = dict(flat(json.load(open(os.path.join(a, fn), encoding='utf-8'))))
        db = dict(flat(json.load(open(fb, encoding='utf-8'))))
        common = [k for k in da if k in db]
        diff = [k for k in common if abs(da[k] - db[k]) > rel * max(abs(da[k]), abs(db[k]), 1e-9)]
        shown = [k for k in diff if not filt or filt in k.lower()]
        print(f'== {fn}: {len(common)} numbers, {len(diff)} differ (> {rel:.0%}), only-A {len(set(da) - set(db))}, only-B {len(set(db) - set(da))}')
        for k in shown[:60]:
            print(f'   {k}: {da[k]:.6g} -> {db[k]:.6g}')
        if len(shown) > 60:
            print(f'   ... {len(shown) - 60} more')


if __name__ == '__main__':
    main()
