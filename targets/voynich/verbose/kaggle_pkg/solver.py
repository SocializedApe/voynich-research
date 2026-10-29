"""Homophonic annealer (unit -> one letter) with incremental scoring; self-contained (numpy only).

Same objective as research/voynich_siblings/attack/attack_v0.py: log-probability of the decrypted letter stream under
an order-k character model minus LAMBDA * n * KL(decrypted letter distribution || the language's), frequency-matched
start, simulated annealing. Differences: the LM part is updated only on the order-k windows that contain a changed
symbol (identical value, far less work), and a share P_SWAP of proposals swap the letters of two symbols (as in
validate.py). check() compares the incremental objective with a full recomputation.
"""
import math
import numpy as np

LAMBDA = 1.0   # as attack_v0.py: weight of the letter-frequency (KL) term
P_SWAP = 0.25


class LM:
    """minimal reader of lang/lm.py DenseLM tables (.npy log-prob table, .json meta, alphabet)"""
    def __init__(self, table, order, alpha):
        self.lp, self.order, self.alpha = table, order, alpha
        self.A = len(alpha); self.index = {c: i for i, c in enumerate(alpha)}

    def encode(self, s): return np.fromiter((self.index[c] for c in s if c in self.index), dtype=np.int64)

    def ctx(self, x, starts):
        k = self.order; c = np.zeros(len(starts), dtype=np.int64)
        for j in range(k): c = c * self.A + x[starts + j]
        return c

    def score_idx(self, x):
        n = len(x) - self.order + 1
        return float(self.lp[self.ctx(x, np.arange(n))].sum()) if n > 0 else 0.0

    def per_char(self, s):
        x = self.encode(s); return self.score_idx(x) / max(1, len(x) - self.order + 1)


def kl(counts, ref):
    q = counts / counts.sum()
    return float(np.sum(np.where(q > 1e-12, q * np.log(np.maximum(q, 1e-300) / ref), 0.0)))


class Problem:
    def __init__(self, syms, model, ref):
        self.model, self.ref = model, ref
        self.types = sorted(set(syms)); tid = {t: i for i, t in enumerate(self.types)}
        self.seq = np.array([tid[s] for s in syms], dtype=np.int64); self.n = len(self.seq)
        self.T = len(self.types); k = model.order
        self.occ = [np.where(self.seq == i)[0] for i in range(self.T)]
        self.freq = np.array([len(o) for o in self.occ])
        nw = self.n - k + 1
        # windows touching each symbol: starts in [p-k+1, p], clipped to [0, nw-1]
        self.win = []
        for o in self.occ:
            w = (o[:, None] - np.arange(k)[None, :]).ravel(); w = w[(w >= 0) & (w < nw)]
            self.win.append(np.unique(w))
        self.letters = [i for i, c in enumerate(model.alpha) if c != ' ']

    def full(self, key):
        x = key[self.seq]; c = np.bincount(x, minlength=self.model.A).astype(float) + 1e-9
        return self.model.score_idx(x) - LAMBDA * self.n * kl(c, self.ref), x, c


def freq_init(P, rng):
    order = np.argsort(-P.freq); need = {l: P.ref[l] * P.freq.sum() for l in P.letters}
    key = np.zeros(P.T, dtype=np.int64)
    for s in order:
        l = max(P.letters, key=lambda L: need[L] + rng.random() * 1e-6); key[s] = l; need[l] -= P.freq[s]
    return key


def anneal(P, rng, iters=60000, restarts=4, log=None):
    m = P.model; best_all = (-1e18, None)
    weights = (P.freq / P.freq.sum()).tolist()
    for r in range(restarts):
        key = freq_init(P, rng)
        _, x, cnt = P.full(key); lmv = m.score_idx(x)
        cur = lmv - LAMBDA * P.n * kl(cnt, P.ref); best = (cur, key.copy())
        T0 = 2.0 * P.n / 20000
        for it in range(iters):
            if rng.random() < P_SWAP:
                a, b = rng.choices(range(P.T), weights=weights, k=2)
                if a == b or key[a] == key[b]: continue
                changed = [(a, key[b]), (b, key[a])]
            else:
                s = rng.randrange(P.T) if rng.random() < 0.5 else rng.choices(range(P.T), weights=weights)[0]
                new = rng.choice(P.letters)
                if new == key[s]: continue
                changed = [(s, new)]
            w = np.unique(np.concatenate([P.win[s] for s, _ in changed]))
            old_lm = float(m.lp[m.ctx(x, w)].sum())
            old = [(s, key[s]) for s, _ in changed]
            for s, l in changed:
                cnt[key[s]] -= P.freq[s]; cnt[l] += P.freq[s]; key[s] = l; x[P.occ[s]] = l
            new_lm = float(m.lp[m.ctx(x, w)].sum())
            sc = lmv - old_lm + new_lm - LAMBDA * P.n * kl(cnt, P.ref)
            Tt = T0 * (1 - it / iters) + 1e-3
            if sc > cur or rng.random() < math.exp((sc - cur) / Tt):
                cur = sc; lmv = lmv - old_lm + new_lm
                if sc > best[0]: best = (sc, key.copy())
            else:
                for s, l in old:
                    cnt[key[s]] -= P.freq[s]; cnt[l] += P.freq[s]; key[s] = l; x[P.occ[s]] = l
        if log: log(f'  restart {r}: best {best[0]:.0f}')
        if best[0] > best_all[0]: best_all = best
    return best_all


def solve(syms, model, ref, rng, iters=60000, restarts=4):
    P = Problem(syms, model, ref)
    score, key = anneal(P, rng, iters, restarts)
    dec = ''.join(model.alpha[key[i]] for i in P.seq)
    return {'objective': score, 'per_char': model.per_char(dec), 'decryption': dec,
            'key': {t: model.alpha[key[i]] for i, t in enumerate(P.types)}, 'units': P.T}


def check(syms, model, ref, rng, moves=300):
    """the incremental objective must equal the full recomputation after random accepted moves"""
    P = Problem(syms, model, ref); key = freq_init(P, rng)
    full0, x, cnt = P.full(key); lmv = model.score_idx(x); worst = 0.0
    for _ in range(moves):
        s = rng.randrange(P.T); l = rng.choice(P.letters)
        w = P.win[s]; old_lm = float(model.lp[model.ctx(x, w)].sum())
        cnt[key[s]] -= P.freq[s]; cnt[l] += P.freq[s]; key[s] = l; x[P.occ[s]] = l
        lmv += float(model.lp[model.ctx(x, w)].sum()) - old_lm
        inc = lmv - LAMBDA * P.n * kl(cnt, ref); ful, _, _ = P.full(key)
        worst = max(worst, abs(inc - ful) / max(1.0, abs(ful)))
    return worst
