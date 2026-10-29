"""Attack v2: like v1 (learned segmentation), but a whole-token symbol may decrypt to one OR two letters.

v1's segmentation leaves 12% of two-letter tokens unsplit; each then loses a letter. Here every 'U' (whole) symbol's
value is either one letter or a letter pair, chosen by the annealer; 'P' and 'S' symbols stay one letter. The stream is
held as two slots per occurrence with a sentinel for an empty second slot, so a proposal costs one vectorised rebuild.

Run from the repository root: python research/voynich_siblings/attack/attack_v2.py <naibbe_tables.csv> [n_tokens]
"""
import collections, math, os, random, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import attack_v0 as v0, attack_v1 as v1
from lang import lm

P_BIGRAM = 0.35


def solve(vis, model, rng, iters=150000, restarts=3, log=print):
    types = sorted(set(vis)); tid = {t: i for i, t in enumerate(types)}
    seq = np.array([tid[s] for s in vis], dtype=np.int64)
    letters = [i for i, c in enumerate(model.alpha) if c != ' ']
    occ = [np.where(seq == i)[0] for i in range(len(types))]
    freq = np.array([len(o) for o in occ])
    isU = np.array([t[0] == 'U' for t in types])
    ref = v0.latin_unigram(model); n = len(seq)
    NONE = -1
    best_all = (-1e18, None)
    for r in range(restarts):
        k1 = v0.freq_init(types, freq, ref, letters, rng)
        k2 = np.full(len(types), NONE, dtype=np.int64)
        def stream():
            a = k1[seq]; b = k2[seq]
            full = np.stack([a, b], 1).ravel()
            return full[full != NONE]
        x = stream(); cur = v0.objective(model, x, ref, len(x)); best = (cur, k1.copy(), k2.copy())
        T0 = 2.0 * n / 20000
        for it in range(iters):
            s = rng.randrange(len(types)) if rng.random() < 0.5 else int(rng.choices(range(len(types)), weights=freq)[0])
            o1, o2 = k1[s], k2[s]
            k1[s] = rng.choice(letters)
            k2[s] = rng.choice(letters) if (isU[s] and rng.random() < P_BIGRAM) else NONE
            if k1[s] == o1 and k2[s] == o2:
                continue
            x = stream(); sc = v0.objective(model, x, ref, len(x))
            T = T0 * (1 - it / iters) + 1e-3
            if sc > cur or rng.random() < math.exp((sc - cur) / T):
                cur = sc
                if sc > best[0]: best = (sc, k1.copy(), k2.copy())
            else:
                k1[s], k2[s] = o1, o2
        log(f'  restart {r}: best score {best[0]:.0f}')
        if best[0] > best_all[0]: best_all = best
    _, k1, k2 = best_all
    def dec(s):
        i = tid[s]; return model.alpha[k1[i]] + (model.alpha[k2[i]] if k2[i] != NONE else '')
    return dec


def main():
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 15000
    rng = random.Random(7)
    model = lm.load('la', order=5, spaces=False)
    syms, truth = v0.synth(sys.argv[1], n)
    toks, i = [], 0
    while i < len(syms):
        if syms[i][0] == 'U': toks.append(syms[i][1]); i += 1
        else: toks.append(syms[i][1] + syms[i + 1][1]); i += 2
    rd = v1.segment(collections.Counter(toks))
    vis = []
    for t in toks:
        r = rd[t]; vis += [('U', r[0])] if len(r) == 1 else [('P', r[0]), ('S', r[1])]
    t0 = time.time()
    dec = solve(vis, model, rng)
    out = ''.join(dec(s) for s in vis)
    tru = lm.norm(''.join(truth), 'latin', False)
    print(f'time {time.time() - t0:.0f}s; decrypted length {len(out)} vs plaintext {len(tru)}')
    print('truth:     ', tru[:300])
    print('decryption:', out[:300])


if __name__ == '__main__':
    main()
