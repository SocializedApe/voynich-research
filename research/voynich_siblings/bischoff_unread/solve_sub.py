"""Try the medieval key families and a general monoalphabetic hill-climb on a short letter cipher printed by
Bischoff 1954, scored with lang/ character models (Latin, English, early German).

Usage: python research/voynich_siblings/bischoff_unread/solve_sub.py "<ciphertext>" [restarts]
(run from the repository root; needs the lang/ models, built on first use)
"""
import math, os, random, string, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
from lang import lm

A = string.ascii_lowercase
MODELS = [('la', 'latin'), ('de-1500s', 'early'), ('en-modern', 'early')]


def score(m, scheme, text):
    t = lm.norm(text, scheme)
    return m.per_char(t) if t.strip() else -99


def families(ct):
    """Fixed key families of Bischoff's sections 11-16 (shift, reverse, reciprocal swaps)."""
    out = []
    for k in range(1, 26):
        out.append((f'shift {k}', ''.join(A[(A.index(c) + k) % 26] if c in A else c for c in ct)))
    out.append(('atbash', ''.join(A[25 - A.index(c)] if c in A else c for c in ct)))
    for k in range(26):  # reversed alphabet with offset (Bischoff 15: z for a, y for b ...)
        out.append((f'reverse+{k}', ''.join(A[(25 - A.index(c) + k) % 26] if c in A else c for c in ct)))
    sw = {}
    for i in range(0, 26, 2):  # reciprocal adjacent pairs a<->b, c<->d ... (Bischoff 12a)
        sw[A[i]], sw[A[i + 1]] = A[i + 1], A[i]
    out.append(('swap pairs ab cd ...', ''.join(sw.get(c, c) for c in ct)))
    sw = {}
    for i in range(1, 25, 2):
        sw[A[i]], sw[A[i + 1]] = A[i + 1], A[i]
    out.append(('swap pairs bc de ...', ''.join(sw.get(c, c) for c in ct)))
    half = {A[i]: A[i + 13] for i in range(13)}; half.update({v: k for k, v in half.items()})
    out.append(('halves a<->n', ''.join(half.get(c, c) for c in ct)))
    return out


def climb(m, scheme, ct, rng, iters=20000):
    """One-to-one key: a permutation of the alphabet, improved by swapping two plaintext values."""
    letters = sorted(set(c for c in ct if c in A))
    perm = list(A); rng.shuffle(perm)
    key = dict(zip(A, perm))
    def dec(k): return ''.join(k.get(c, c) for c in ct)
    cur = score(m, scheme, dec(key)); best = (cur, dict(key))
    T = 0.6
    for it in range(iters):
        a = rng.choice(letters); b = rng.choice(A)
        if a == b:
            continue
        key[a], key[b] = key[b], key[a]
        s = score(m, scheme, dec(key))
        if s > cur or rng.random() < math.exp((s - cur) / T):
            cur = s
            if s > best[0]:
                best = (s, dict(key))
        else:
            key[a], key[b] = key[b], key[a]
        T = max(0.02, T * 0.9997)
    return best[0], dec(best[1])


def main():
    ct = sys.argv[1].lower()
    restarts = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    models = [(lm.load(n), s, n) for n, s in MODELS]
    print('ciphertext:', ct)
    print('\n== key families (best 3 per model)')
    for m, s, n in models:
        res = sorted(((score(m, s, p), name, p) for name, p in families(ct)), reverse=True)[:3]
        for sc, name, p in res:
            print(f'  {n:10s} {sc:6.2f}  {name:22s} {p}')
    print('\n== general substitution hill-climb (best 3 distinct per model; short texts have many fits)')
    rng = random.Random(7)
    for m, s, n in models:
        seen = {}
        for _ in range(restarts):
            sc, p = climb(m, s, ct, rng)
            seen[p] = max(sc, seen.get(p, -99))
        for p, sc in sorted(seen.items(), key=lambda x: -x[1])[:3]:
            print(f'  {n:10s} {sc:6.2f}  {p}')


if __name__ == '__main__':
    main()
