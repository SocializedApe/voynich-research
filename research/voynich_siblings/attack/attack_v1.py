"""Attack v1 on a synthetic Naibbe ciphertext, no oracle: the solver sees whole tokens only.

Step 1, segmentation (unsupervised, Viterbi-EM over word types, Morfessor-like): every token type is read either as one
part (a one-letter unit) or as head + tail (a two-letter unit), split at any inner position. Part probabilities are
re-estimated from the current segmentation (token-weighted), each type takes its most probable reading (two-part
readings pay a fixed penalty PEN), repeated until stable. Heads, tails and wholes are separate inventories (roles).
Step 2, the v0 annealer (attack_v0.solve) on the resulting symbol sequence.

Measured: segmentation accuracy against the truth (share of tokens split correctly), symbol count, and per-letter
accuracy of the decryption after aligning lengths (letters compared position by position only where the segmentation
is right; overall readability shown).

Run from the repository root: python research/voynich_siblings/attack/attack_v1.py <naibbe_tables.csv> [n_tokens]
"""
import collections, math, os, random, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import attack_v0 as v0
from lang import lm

PEN = 2.0      # log-penalty for reading a type as two parts


def segment(token_counts, iters=40, alpha=0.01, post=True, post_min=5, post_rare=20):
    """EM over all readings of each type (whole, or head+tail at any inner split), token-weighted, with a sparse
    (Dirichlet alpha < 1, MAP) re-estimate so that small part inventories win; final Viterbi reading per type."""
    types = list(token_counts)
    cands = {t: [(t,)] + [(t[:k], t[k:]) for k in range(1, len(t))] for t in types}
    # start: expected counts spread evenly over all readings
    cU, cH, cT = collections.Counter(), collections.Counter(), collections.Counter()
    piB = 0.5
    for t, n in token_counts.items():
        w = n / len(cands[t])
        for r in cands[t]:
            if len(r) == 1: cU[r[0]] += w
            else: cH[r[0]] += w; cT[r[1]] += w
    for it in range(iters):
        def probs(c):
            tot = sum(max(v - (1 - alpha), 0) for v in c.values()) + 1e-9
            return {k: max(v - (1 - alpha), 0) / tot for k, v in c.items()}
        pU, pH, pT = probs(cU), probs(cH), probs(cT)
        nU, nH, nT = collections.Counter(), collections.Counter(), collections.Counter(); nB = 0.0; ntot = 0.0
        for t, n in token_counts.items():
            sc = []
            for r in cands[t]:
                v = (1 - piB) * pU.get(r[0], 0) if len(r) == 1 else piB * pH.get(r[0], 0) * pT.get(r[1], 0)
                sc.append(v)
            z = sum(sc)
            if z <= 0:
                continue
            for r, v in zip(cands[t], sc):
                w = n * v / z
                if w < 1e-9: continue
                if len(r) == 1: nU[r[0]] += w
                else: nH[r[0]] += w; nT[r[1]] += w; nB += w
            ntot += n
        cU, cH, cT = nU, nH, nT; piB = nB / max(ntot, 1)
    pU, pH, pT = probs(cU), probs(cH), probs(cT)
    reading = {}
    for t in types:
        best = max(cands[t], key=lambda r: (1 - piB) * pU.get(r[0], 0) if len(r) == 1 else piB * pH.get(r[0], 0) * pT.get(r[1], 0))
        reading[t] = best
    if post:
        # post-pass: a rare whole reading that splits into a well-attested head and tail is read as head + tail
        heads = {h for h, v in cH.items() if v >= post_min}; tails = {x for x, v in cT.items() if v >= post_min}
        for t in types:
            if len(reading[t]) == 1 and token_counts[t] < post_rare:
                opts = [(t[:k], t[k:]) for k in range(1, len(t)) if t[:k] in heads and t[k:] in tails]
                if opts:
                    reading[t] = max(opts, key=lambda r: cH[r[0]] * cT[r[1]])
    return reading


def main():
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 15000
    rng = random.Random(7)
    model = lm.load('la', order=5, spaces=False)
    syms, truth = v0.synth(sys.argv[1], n)
    # rebuild the visible tokens and the true readings
    toks, true_read, i = [], [], 0
    while i < len(syms):
        if syms[i][0] == 'U':
            toks.append(syms[i][1]); true_read.append((syms[i][1],)); i += 1
        else:
            toks.append(syms[i][1] + syms[i + 1][1]); true_read.append((syms[i][1], syms[i + 1][1])); i += 2
    counts = collections.Counter(toks)
    reading = segment(counts)
    seg_ok = sum(reading[t] == r for t, r in zip(toks, true_read)) / len(toks)
    vis = []
    for t in toks:
        r = reading[t]
        vis += [('U', r[0])] if len(r) == 1 else [('P', r[0]), ('S', r[1])]
    print(f'tokens {len(toks)}, types {len(counts)}; segmentation correct for {seg_ok:.3f} of tokens; symbols {len(set(vis))} types (truth {len(set(syms))})')
    t0 = time.time()
    types, key = v0.solve(vis, model, rng)
    dec = ''.join(model.alpha[key[types.index(s)]] for s in vis)
    tru = lm.norm(''.join(truth), 'latin', False)
    ok = sum(a == b for a, b in zip(dec, tru)) / len(tru)
    print(f'time {time.time() - t0:.0f}s; position-wise letter agreement {ok:.3f} (meaningful only if lengths line up)')
    print('truth:     ', tru[:300])
    print('decryption:', dec[:300])


if __name__ == '__main__':
    main()
