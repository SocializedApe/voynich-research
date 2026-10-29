"""Slot-HMM: does a hidden state behind each Voynich word, emitting its four slots independently, carry a sequence?

Each token is parsed into four slots, prefix + gallows core + middle + ending (regex PARSE). Two latent models:
  mixture  z_t drawn independently each token; P(word) = sum_z pi_z P_z(prefix) P_z(core) P_z(middle) P_z(ending)
  HMM      the same emissions, z_t depends on z_{t-1} (lines are the sequences)
If Voynichese is a slot cipher of a letter stream (each word = one plaintext unit, slots filled from that unit's
homophone tables), the HMM's states should behave like letters: the HMM should beat the mixture on held-out lines
by about what a language's letter bigram adds over unigrams, and its states should be recoverable on a control.

Controls:
  slotcipher   Latin letters -> words whose four slots are drawn independently from letter-specific homophone sets
               (the model's own assumption; positive control: states should map onto letters)
  slotcipher_m same, but letters merged into 1-2 letter units first (Naibbe-like respacing)
  shuffled     Voynich tokens shuffled over the whole text (null: no sequence, gain should be about 0)

Held-out = every 5th line. Reported: held-out bits/token for K = 1 (independent slots), mixture K, HMM K; the gain
HMM - mixture; for controls with a known plaintext, the share of tokens whose Viterbi state's majority letter is
right (purity) and the normalised mutual information between states and letters.

Run from the repository root: python -I research/voynich_siblings/slot_hmm.py
"""
import collections, csv, math, os, random, re, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..')
TSV = os.path.join(ROOT, 'targets', 'voynich', 'data', 'ZL3b-n.fixed.words.tsv')
LATIN = os.path.join(ROOT, 'lang', 'corpora', 'la-gutenberg.txt')
KS = [12, 24]
ITERS = 40
SEED = 11
M_CAP = 40   # middle-slot values kept; rarer ones pooled

PARSE = re.compile(r'^(?P<P>qo|q|o|y|d|s(?!h)|l|r)?'
                   r'(?P<C>(?:ch|sh)?(?:ckh|cth|cph|cfh|k|t|p|f)?(?:ch|sh)?)'
                   r'(?P<M>[a-z]*?)'
                   r'(?P<E>aiin|aiir|aiim|ain|air|aim|iin|iir|in|ir|al|ar|am|ol|or|dy|ey|y|l|r|m|n|s|d|g|o|a)?$')


def slots(w):
    m = PARSE.match(w)
    return (m['P'] or '-', m['C'] or '-', m['M'] or '-', m['E'] or '-')


# ---------------------------------------------------------------------------------------------------------- data
def voynich_lines(lang=None):
    out = []
    for r in csv.DictReader(open(TSV, encoding='utf-8'), delimiter='\t'):
        if r['locus_type'] != 'P' or (lang and r['lang'] != lang):
            continue
        ws = [w for w in r['line_words'].split() if re.fullmatch(r'[a-z]+', w)]
        if len(ws) >= 2:
            out.append(ws)
    return out


def latin_letters(n, rng):
    t = open(LATIN, encoding='utf-8', errors='replace').read().lower().replace('j', 'i').replace('v', 'u')
    t = re.sub(r'[^a-z]+', '', t[len(t) // 10:])
    s = rng.randrange(0, len(t) - n - 1)
    return t[s:s + n]


def slot_cipher(skel, rng, merge=False):
    """Pour a Latin letter stream into the Voynich line skeleton; each unit -> four slots drawn from that unit's own
    small homophone sets (2-3 values per slot, taken from the Voynich slot inventories). Returns lines of slot tuples
    and the parallel plaintext units."""
    voy = [slots(w) for ln in voynich_lines() for w in ln]
    inv = [sorted({s[i] for s in voy}, key=lambda v: -sum(1 for s in voy if s[i] == v))[:12] for i in range(4)]
    n = sum(len(l) for l in skel)
    text = latin_letters(3 * n, rng)
    units, i = [], 0
    while len(units) < n:
        if merge and rng.random() < 0.5:
            units.append(text[i:i + 2]); i += 2
        else:
            units.append(text[i]); i += 1
    table = {}
    lines, plain, k = [], [], 0
    for ln in skel:
        row, prow = [], []
        for _ in ln:
            u = units[k]; k += 1
            if u not in table:
                table[u] = [rng.sample(inv[j], rng.choice([2, 3])) for j in range(4)]
            row.append(tuple(rng.choice(table[u][j]) for j in range(4))); prow.append(u)
        lines.append(row); plain.append(prow)
    return lines, plain


# ---------------------------------------------------------------------------------------------------------- model
class Coder:
    def __init__(self, lines):
        cnt = [collections.Counter(s[j] for ln in lines for s in ln) for j in range(4)]
        keep2 = {v for v, _ in cnt[2].most_common(M_CAP)}
        self.vocab = []
        for j in range(4):
            vs = sorted(cnt[j]) if j != 2 else sorted(keep2) + ['*']
            self.vocab.append({v: i for i, v in enumerate(vs)})

    def enc(self, lines):
        """-> (X, mask): X (N, L, 4) slot indices (-1 unseen), mask (N, L) True on real tokens."""
        L = max(len(l) for l in lines)
        X = np.zeros((len(lines), L, 4), dtype=np.int64); mask = np.zeros((len(lines), L), dtype=bool)
        for n, ln in enumerate(lines):
            for t, s in enumerate(ln):
                for j in range(4):
                    v = s[j] if j != 2 or s[j] in self.vocab[2] else '*'
                    X[n, t, j] = self.vocab[j].get(v, -1)
                mask[n, t] = True
        return X, mask


def emis_prob(B, data):
    """B: list of 4 arrays (K, V_j) -> (N, L, K); unseen values get a floor, padding 1."""
    X, mask = data
    p = np.ones(X.shape[:2] + (B[0].shape[0],))
    for j in range(4):
        col = X[..., j]
        bj = B[j].T[np.where(col >= 0, col, 0)]
        bj[col < 0] = 1e-4
        p *= bj
    p[~mask] = 1.0
    return p


def forward_backward(pi, A, e, mask):
    N, L, K = e.shape
    al = np.empty((N, L, K)); c = np.ones((N, L))
    a = pi * e[:, 0]; c[:, 0] = a.sum(1); al[:, 0] = a / c[:, :1]
    for t in range(1, L):
        a = (al[:, t - 1] @ A) * e[:, t]; s = a.sum(1); v = mask[:, t]
        c[:, t] = np.where(v, s, 1.0)
        al[:, t] = np.where(v[:, None], a / s[:, None], al[:, t - 1])
    be = np.ones((N, L, K))
    for t in range(L - 2, -1, -1):
        nb = ((e[:, t + 1] * be[:, t + 1]) @ A.T) / c[:, t + 1, None]
        be[:, t] = np.where(mask[:, t + 1, None], nb, 1.0)
    return al, be, c


def fit(data, sizes, K, hmm, rng, iters=ITERS):
    X, mask = data
    pi = np.full(K, 1.0 / K)
    A = np.full((K, K), 1.0 / K) * 0.5 + rng.dirichlet(np.ones(K), K) * 0.5
    B = [rng.dirichlet(np.ones(v), K) for v in sizes]
    if not hmm:
        A = np.tile(pi, (K, 1))
    for _ in range(iters):
        e = emis_prob(B, data)
        al, be, c = forward_backward(pi, A, e, mask)
        g = al * be; g[~mask] = 0
        if hmm:
            cpi = g[:, 0].sum(0) + 1e-3
            cA = np.full((K, K), 1e-3)
            for t in range(X.shape[1] - 1):
                w = (e[:, t + 1] * be[:, t + 1]) / c[:, t + 1, None] * mask[:, t + 1, None]
                cA += (al[:, t].T @ w) * A
            A = cA / cA.sum(1, keepdims=True)
        else:
            cpi = g.sum((0, 1)) + 1e-3
        pi = cpi / cpi.sum()
        if not hmm:
            A = np.tile(pi, (K, 1))
        gm = g[mask]
        B = []
        for j in range(4):
            cb = np.full((sizes[j], K), 1e-2)
            np.add.at(cb, X[..., j][mask], gm)
            B.append((cb / cb.sum(0)).T)
    return pi, A, B


def loglik(data, pi, A, B):
    _, mask = data
    _, _, c = forward_backward(pi, A, emis_prob(B, data), mask)
    return -np.log(c[mask]).sum() / mask.sum() / math.log(2)


def viterbi(data, pi, A, B):
    X, mask = data
    le = np.log(emis_prob(B, data)); lA = np.log(A)
    N, L, K = le.shape
    d = np.log(pi) + le[:, 0]; bp = np.zeros((N, L, K), dtype=np.int64); ident = np.arange(K)
    for t in range(1, L):
        m = d[:, :, None] + lA
        v = mask[:, t]
        bp[:, t] = np.where(v[:, None], m.argmax(1), ident)
        d = np.where(v[:, None], m.max(1) + le[:, t], d)
    path = np.zeros((N, L), dtype=np.int64); path[:, -1] = d.argmax(1)
    for t in range(L - 1, 0, -1):
        path[:, t - 1] = bp[np.arange(N), t, path[:, t]]
    return [list(path[n, :mask[n].sum()]) for n in range(N)]


def H(c):
    n = sum(c.values())
    return -sum(v / n * math.log2(v / n) for v in c.values() if v)


def state_stats(paths):
    uni = collections.Counter(z for p in paths for z in p)
    bi = collections.Counter((a, b) for p in paths for a, b in zip(p, p[1:]))
    first = collections.Counter(a for p in paths for a in p[:-1])
    return H(uni), H(bi) - H(first)   # H(z), H(z_t | z_{t-1})


def recovery(paths, plain):
    pairs = [(z, u) for p, q in zip(paths, plain) for z, u in zip(p, q)]
    byz = collections.defaultdict(collections.Counter)
    for z, u in pairs:
        byz[z][u] += 1
    purity = sum(c.most_common(1)[0][1] for c in byz.values()) / len(pairs)
    hz = H(collections.Counter(z for z, _ in pairs)); hu = H(collections.Counter(u for _, u in pairs))
    mi = hz + hu - H(collections.Counter(pairs))
    return purity, mi / min(hz, hu)


# ---------------------------------------------------------------------------------------------------------- run
def run(name, lines, plain=None, ks=KS, seed=SEED):
    rng = np.random.default_rng(seed)
    tr = [l for i, l in enumerate(lines) if i % 5]; te = [l for i, l in enumerate(lines) if not i % 5]
    cod = Coder(tr); Xtr, Xte = cod.enc(tr), cod.enc(te)
    sizes = [len(v) for v in cod.vocab]
    p1 = fit(Xtr, sizes, 1, False, rng, iters=2)
    rows = [(name, 1, loglik(Xte, *p1), None, None, None, None, None)]
    for K in ks:
        mix = fit(Xtr, sizes, K, False, rng)
        hmm = fit(Xtr, sizes, K, True, rng)
        lm, lh = loglik(Xte, *mix), loglik(Xte, *hmm)
        paths = viterbi(cod.enc(lines), *hmm)
        hz, hzz = state_stats(paths)
        rec = recovery(paths, plain) if plain else (None, None)
        rows.append((name, K, lm, lh, lm - lh, hz, hz - hzz, rec))
        print(f'{name:14s} K={K:2d}  mix {lm:6.3f}  hmm {lh:6.3f}  gain {lm - lh:+.3f}  '
              f'H(z) {hz:.2f}  I(z;z-1) {hz - hzz:.3f}' + (f'  purity {rec[0]:.2f} NMI {rec[1]:.2f}' if plain else ''),
              flush=True)
    return rows, (hmm, cod)


def main():
    rng = random.Random(SEED)
    vl = voynich_lines()
    V = [[slots(w) for w in ln] for ln in vl]
    n = sum(len(l) for l in V)
    parsed = sum(1 for ln in vl for w in ln if PARSE.match(w)['M'] in ('', None) or len(PARSE.match(w)['M']) <= 3)
    print(f'Voynich lines {len(V)}, tokens {n}; middle slot of 0-3 letters: {parsed / n:.1%}')
    for j, nm in enumerate('PCME'):
        c = collections.Counter(s[j] for l in V for s in l)
        print(f'  slot {nm}: {len(c)} values; top {c.most_common(8)}')
    flat = [s for l in V for s in l]; rng.shuffle(flat); it = iter(flat)
    shuf = [[next(it) for _ in l] for l in V]
    sc, scp = slot_cipher(V, rng)
    sm, smp = slot_cipher(V, rng, merge=True)
    lat = latin_letters(n, rng); it = iter(lat)
    latp = [[next(it) for _ in l] for l in V]
    lat_uni = H(collections.Counter(lat)); lat_bi = H(collections.Counter(zip(lat, lat[1:]))) - lat_uni
    print(f'Latin letters: H1 {lat_uni:.2f}, H(x|x-1) {lat_bi:.2f}, I(x;x-1) {lat_uni - lat_bi:.3f} bits')
    rows = []
    rows += run('slotcipher', sc, scp)[0]
    rows += run('slotcipher_m', sm, smp)[0]
    rows += run('shuffled', shuf)[0]
    rows += run('voynich', V)[0]
    rows += run('voynich_A', [[slots(w) for w in ln] for ln in voynich_lines('A')], ks=[24])[0]
    rows += run('voynich_B', [[slots(w) for w in ln] for ln in voynich_lines('B')], ks=[24])[0]


if __name__ == '__main__':
    main()
