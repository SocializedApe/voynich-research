"""Attack v0 on a synthetic Naibbe ciphertext, best case: the split of every token into its one or two parts is given.

Purpose: before any attempt on Voynich, check that a homophonic annealer with a Latin character model can recover the
plaintext of a Naibbe-type cipher when the key is unknown but the segmentation is known. If this fails, the approach
is dead; if it works, v1 removes the oracle segmentation.

Ciphertext: Greshko's tables (argv[1]), Latin plaintext (lang/corpora/la-gutenberg.txt), the Naibbe rule (deck draw,
respacing 17/36). Every token is recorded with its parts: ('U', glyph string) for a one-letter token, ('P', string) and
('S', string) for the two halves of a two-letter token. A cipher SYMBOL is a (role, string) pair; the key maps each
symbol to one plaintext letter (homophonic). The attacker sees symbols and their order only.

Solver: simulated annealing on the symbol -> letter map, objective = log-probability of the decrypted letter stream
under the order-5 no-space Latin model (lang 'la'), proposal = re-assign one symbol to a random letter, restarts.
Measured: share of symbol occurrences decrypted correctly, and the first 300 letters of the decryption.

Run from the repository root: python research/voynich_siblings/attack/attack_v0.py <naibbe_tables.csv> [n_tokens]
"""
import collections, math, os, random, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'targets', 'voynich'))
import numpy as np
from lang import lm
from b3_bakeoff import Naibbe


def synth(csv_path, n_tokens, seed=19):
    nb = Naibbe(csv_path, seed=seed)
    lat = os.path.join(ROOT, 'lang', 'corpora', 'la-gutenberg.txt')
    syms, truth = [], []
    deck = nb.deck(); di = [0]
    def draw():
        if di[0] >= len(deck):
            deck[:] = nb.deck(); di[0] = 0
        t = deck[di[0]]; di[0] += 1; return t
    started = False
    for raw in open(lat, encoding='utf-8', errors='replace'):
        c = nb.clean_line(raw)
        if not c:
            continue
        if not started:          # skip Gutenberg front matter
            started = 'arma' in c or len(syms) > 0 or True
        for u in nb.respace(c):
            if len(u) == 1:
                g = nb.glyph.get(f'unigram_{draw()}_{u}')
                if g: syms.append(('U', g)); truth.append(u)
            else:
                tp, ts = draw(), draw()
                gp = nb.glyph.get(f'prefix_{tp}_{u[0]}'); gs = nb.glyph.get(f'suffix_{ts}_{u[1]}')
                if gp and gs:
                    syms.append(('P', gp)); truth.append(u[0]); syms.append(('S', gs)); truth.append(u[1])
        if len(syms) >= 2 * n_tokens:
            break
    return syms, truth


LAMBDA = 1.0   # weight of the unigram (letter frequency) term, in nats per letter of KL divergence x stream length


def latin_unigram(model):
    t = lm.norm(open(os.path.join(ROOT, 'lang', 'corpora', 'la-gutenberg.txt'), encoding='utf-8', errors='replace').read()[200000:2200000], 'latin', False)
    c = np.bincount(model.encode(t), minlength=model.A).astype(float) + 1
    return c / c.sum()


def objective(model, x, ref, n):
    """LM log-probability minus LAMBDA * n * KL(decrypted letter distribution || Latin's)."""
    q = np.bincount(x, minlength=model.A).astype(float) + 1e-9; q /= q.sum()
    kl = float(np.sum(np.where(q > 1e-8, q * np.log(q / ref), 0.0)))
    return model.score_idx(x) - LAMBDA * n * kl


def freq_init(types, freq, ref, letters, rng):
    """assign symbols, most frequent first, to letters in proportion to Latin letter frequencies"""
    order = np.argsort(-freq); need = {l: ref[l] * freq.sum() for l in letters}
    key = np.zeros(len(types), dtype=np.int64)
    for s in order:
        l = max(letters, key=lambda L: need[L] + rng.random() * 1e-6)
        key[s] = l; need[l] -= freq[s]
    return key


def solve(syms, model, rng, iters=60000, restarts=4):
    types = sorted(set(syms)); tid = {t: i for i, t in enumerate(types)}
    seq = np.array([tid[s] for s in syms], dtype=np.int64)
    A = model.A
    letters = [i for i, c in enumerate(model.alpha) if c != ' ']
    occ = [np.where(seq == i)[0] for i in range(len(types))]
    freq = np.array([len(o) for o in occ])
    ref = latin_unigram(model); n = len(seq)
    best_all = (-1e18, None)
    for r in range(restarts):
        key = freq_init(types, freq, ref, letters, rng)
        x = key[seq]; cur = objective(model, x, ref, n); best = (cur, key.copy())
        T0 = 2.0 * len(seq) / 20000
        for it in range(iters):
            s = rng.randrange(len(types)) if rng.random() < 0.5 else int(rng.choices(range(len(types)), weights=freq)[0])
            old = key[s]; new = rng.choice(letters)
            if new == old:
                continue
            key[s] = new; x[occ[s]] = new
            sc = objective(model, x, ref, n)
            T = T0 * (1 - it / iters) + 1e-3
            if sc > cur or rng.random() < math.exp((sc - cur) / T):
                cur = sc
                if sc > best[0]:
                    best = (sc, key.copy())
            else:
                key[s] = old; x[occ[s]] = old
        print(f'  restart {r}: best score {best[0]:.0f}', flush=True)
        if best[0] > best_all[0]:
            best_all = best
    return types, best_all[1]


def main():
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 20000
    rng = random.Random(7)
    model = lm.load('la', order=5, spaces=False)
    syms, truth = synth(sys.argv[1], n)
    print(f'symbols: {len(syms)} occurrences, {len(set(syms))} types; plaintext letters {len(truth)}')
    t0 = time.time()
    types, key = solve(syms, model, rng)
    dec = ''.join(model.alpha[key[types.index(s)]] for s in syms)
    tru = ''.join(truth)
    acc = sum(a == b for a, b in zip(dec, lm.norm(tru, 'latin', False))) / len(tru)
    print(f'time {time.time() - t0:.0f}s; per-occurrence accuracy {acc:.3f}')
    print('truth:     ', lm.norm(tru, 'latin', False)[:300])
    print('decryption:', dec[:300])


if __name__ == '__main__':
    main()
