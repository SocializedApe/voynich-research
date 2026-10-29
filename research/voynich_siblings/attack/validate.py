"""One validation job for the blind attack: does a single solver run recover a synthetic ciphertext?

Kinds (--kind):
  naibbe     Greshko's tables, Latin plaintext (about 450 learned symbols at 20,000 tokens)
  --canon    merge symbols that differ only by a scribal variant before solving (validate.canon)
  expanded   the same, but every table entry also has three scribal variants (hybrid_model.edit applied to it), one of
             the four forms chosen at random at each use: a Voynich-sized inventory (about 1,500 symbols)
The solver is attack_v2 with one extra move (swap the values of two symbols, probability P_SWAP) and a randomised
start; iterations ITERS. Success = difflib similarity of the first 3,000 decrypted letters to the plaintext >= 0.80.
Prints one line: JOB kind seed similarity score time.

Run from the repository root: python research/voynich_siblings/attack/validate.py <naibbe_tables.csv> --kind naibbe --seed 1
"""
import collections, difflib, math, os, random, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..'))
import numpy as np
import attack_v0 as v0, attack_v1 as v1, attack_v2 as v2
from lang import lm
from b3_bakeoff import Naibbe

ITERS = 200000
P_SWAP = 0.25


def solve(vis, model, rng, iters=ITERS):
    """attack_v2.solve with swap moves and a single restart (restarts are separate jobs)."""
    types = sorted(set(vis)); tid = {t: i for i, t in enumerate(types)}
    seq = np.array([tid[s] for s in vis], dtype=np.int64)
    letters = [i for i, c in enumerate(model.alpha) if c != ' ']
    occ = [np.where(seq == i)[0] for i in range(len(types))]
    freq = np.array([len(o) for o in occ])
    isU = np.array([t[0] == 'U' for t in types])
    ref = v0.latin_unigram(model); n = len(seq); NONE = -1
    k1 = v0.freq_init(types, freq * np.array([0.7 + 0.6 * rng.random() for _ in types]), ref, letters, rng)
    k2 = np.full(len(types), NONE, dtype=np.int64)
    def stream():
        full = np.stack([k1[seq], k2[seq]], 1).ravel(); return full[full != NONE]
    x = stream(); cur = v0.objective(model, x, ref, len(x)); best = (cur, k1.copy(), k2.copy())
    T0 = 2.0 * n / 20000
    weights = freq / freq.sum()
    for it in range(iters):
        if rng.random() < P_SWAP:
            a, b = (int(i) for i in np.random.choice(len(types), 2, replace=False, p=weights))
            o = (k1[a], k2[a], k1[b], k2[b])
            k1[a], k1[b] = k1[b], k1[a]
            if isU[a] and isU[b]:
                k2[a], k2[b] = k2[b], k2[a]
            changed = [(a, o[0], o[1]), (b, o[2], o[3])]
        else:
            s = rng.randrange(len(types)) if rng.random() < 0.5 else int(np.random.choice(len(types), p=weights))
            changed = [(s, k1[s], k2[s])]
            k1[s] = rng.choice(letters)
            k2[s] = rng.choice(letters) if (isU[s] and rng.random() < v2.P_BIGRAM) else NONE
        x = stream(); sc = v0.objective(model, x, ref, len(x))
        T = T0 * (1 - it / iters) + 1e-3
        if sc > cur or rng.random() < math.exp((sc - cur) / T):
            cur = sc
            if sc > best[0]: best = (sc, k1.copy(), k2.copy())
        else:
            for s, a1, a2 in changed:
                k1[s], k2[s] = a1, a2
    _, k1, k2 = best
    def dec(s):
        i = tid[s]; return model.alpha[k1[i]] + (model.alpha[k2[i]] if k2[i] != NONE else '')
    return dec, best[0]


def synth_tokens(csv_path, n, kind, seed=19):
    syms, truth = v0.synth(csv_path, n, seed=seed)
    rng = random.Random(seed + 5)
    import hybrid_model as h1
    variants = {}
    toks, i = [], 0
    def form(g):
        if kind != 'expanded':
            return g
        if g not in variants:
            vs = {g}
            while len(vs) < 4:
                vs.add(h1.edit(rng.choice(sorted(vs)), rng))
            variants[g] = sorted(vs)
        return rng.choice(variants[g])
    while i < len(syms):
        if syms[i][0] == 'U': toks.append(form(syms[i][1])); i += 1
        else: toks.append(form(syms[i][1]) + form(syms[i + 1][1])); i += 2
    return toks, lm.norm(''.join(truth), 'latin', False)


def canon(g):
    """merge scribal variants: ee->e, sh->ch, t->k, a->o, a leading qo-/o- dropped, a final -y dropped"""
    c = g.replace('ee', 'e').replace('sh', 'ch').replace('t', 'k').replace('a', 'o')
    if c.startswith('qo') and len(c) > 3: c = c[2:]
    elif c.startswith('o') and len(c) > 2: c = c[1:]
    if c.endswith('y') and len(c) > 2: c = c[:-1]
    return c


def main():
    a = sys.argv[1:]
    kind = a[a.index('--kind') + 1]; seed = int(a[a.index('--seed') + 1])
    rng = random.Random(seed); np.random.seed(seed)
    model = lm.load('la', order=5, spaces=False)
    toks, truth = synth_tokens(a[0], 15000, kind)
    rd = v1.segment(collections.Counter(toks))
    vis = []
    for t in toks:
        r = rd[t]; vis += [('U', r[0])] if len(r) == 1 else [('P', r[0]), ('S', r[1])]
    if '--canon' in a:
        vis = [(role, canon(g)) for role, g in vis]
    t0 = time.time()
    dec, score = solve(vis, model, rng)
    out = ''.join(dec(s) for s in vis)
    sim = difflib.SequenceMatcher(None, out[:3000], truth[:3000], autojunk=False).ratio()
    print(f'JOB kind={kind} canon={"--canon" in a} seed={seed} symbols={len(set(vis))} similarity={sim:.3f} score={score:.0f} time={time.time() - t0:.0f}s')
    print('DEC', out[:200])


if __name__ == '__main__':
    main()
