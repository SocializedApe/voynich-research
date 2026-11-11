"""Sanity check of the HPY fit: is the d -> 1 (pass-through) solution really the best, or a trapped sampler?

Leave-one-out predictive log2-probability per token on Voynich under fixed hyperparameters (seating resampled by
Gibbs for a few sweeps under each setting), compared with the values the hyperparameter sampler found.
Run from targets/voynich: python reinforce/check_fit.py
"""
import json, os, random, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'lines'))
import hpy, common

SWEEPS = 15


def run(pgs, d, theta, levels=None, seed=3):
    rng = random.Random(seed)
    data = hpy.paths_of(pgs)
    if levels is not None:   # collapse: keep only the given level indices of the path
        data = [(tuple(p[i] for i in levels), w) for p, w in data]
    types = sorted({w for _, w in data}); g0 = {w: 1.0 / len(types) for w in types}
    m = hpy.HPY(d, theta, g0)
    for path, w in data:
        m.add(m.node(path), w, rng)
    order = list(range(len(data)))
    for s in range(SWEEPS):
        rng.shuffle(order)
        for i in order:
            path, w = data[i]; n = m.nodes[path]; m.remove(n, w, rng); m.add(n, w, rng)
    return m.loglik(data, rng)


def main():
    t0 = time.time()
    ref = common.pages()
    settings = [
        ('fitted (d~0.9-1.0, theta small)', [0.91, 0.96, 0.97, 0.97, 0.98, 0.99], [2.0, 5.0, 6.0, 12.5, 4.0, 1.9], None),
        ('d 0.8 all, same theta', [0.8] * 6, [2.0, 5.0, 6.0, 12.5, 4.0, 1.9], None),
        ('d 0.5 all, same theta', [0.5] * 6, [2.0, 5.0, 6.0, 12.5, 4.0, 1.9], None),
        ('d 0.5 all, theta 10 all', [0.5] * 6, [10.0] * 6, None),
        ('d 0.9 root, 0.5 others, theta 10', [0.9, 0.5, 0.5, 0.5, 0.5, 0.5], [10.0] * 6, None),
        ('d 0.9 root, 0.7 others, theta 20', [0.9, 0.7, 0.7, 0.7, 0.7, 0.7], [20.0] * 6, None),
        ('flat root only d 0.91 theta 2', [0.91], [2.0], [0]),
        ('flat root only d 0.8 theta 50', [0.8], [50.0], [0]),
        ('root+page d 0.9/0.5 theta 2/10', [0.9, 0.5], [2.0, 10.0], [0, 4]),
        ('root+page d 0.9/0.9 theta 2/5', [0.9, 0.9], [2.0, 5.0], [0, 4]),
    ]
    out = {}
    for name, d, th, lev in settings:
        ll = run(ref, d, th, lev)
        out[name] = ll
        print(f'{name:40s} LOO log2 p/token {ll:.3f}   ({time.time() - t0:.0f}s)', flush=True)
    json.dump(out, open(os.path.join(HERE, 'check_fit.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
