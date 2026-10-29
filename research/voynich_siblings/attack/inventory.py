"""Why does Voynich segment into ~1,500 symbols? Inventory diagnostics for the head/tail segmentation (attack_v1).

Part 1: the attack_v1 symbols broken down by role (U = whole word, P = head, S = tail), with how many are rare and how
many tokens they cover. Question: is the excess mostly unsplit rare whole words (a segmentation failure) or real
head/tail pieces?
Part 2: a looser segmentation, every word cut into 1..MAXP pieces from ONE shared inventory (unigram model, Viterbi EM
with a per-piece cost and a sparse prior, Morfessor-like). Question: does Voynich come down to a Naibbe-sized
inventory when the units may be smaller than head/tail?

Texts: Voynich paragraph tokens (first N, manuscript order) and a synthetic Naibbe ciphertext of Latin, same N.
Part 3: segmenter-free coverage, the K most used pieces and how many of them each word needs.
Run from the repository root: python research/voynich_siblings/attack/inventory.py <naibbe_tables.csv> [N] [--part2]
"""
import collections, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import attack_v1 as v1, run_voynich as rv


def first_n(lines, n):
    out = []
    for ws in lines:
        if len(out) >= n: break
        out += ws
    return out


def part1(name, toks):
    rd = v1.segment(collections.Counter(toks))
    occ = collections.Counter()
    for t in toks:
        r = rd[t]
        if len(r) == 1: occ[('U', r[0])] += 1
        else: occ[('P', r[0])] += 1; occ[('S', r[1])] += 1
    print(f'\n== {name}: {len(toks)} tokens, {len(set(toks))} word types, {len(occ)} symbols; '
          f'{sum(len(rd[t]) == 1 for t in toks) / len(toks):.1%} of tokens left whole')
    print('role  symbols  freq=1  freq<=4  freq>=20  tokens covered by freq<=4 symbols')
    for role in 'UPS':
        f = [v for (r, _), v in occ.items() if r == role]
        if not f: continue
        print(f'{role:>4}  {len(f):7}  {sum(v == 1 for v in f):6}  {sum(v <= 4 for v in f):7}  {sum(v >= 20 for v in f):8}'
              f'  {sum(v for v in f if v <= 4):6}')
    tot = len(occ); rare = sum(v <= 4 for v in occ.values())
    print(f' all  {tot:7}  {sum(v == 1 for v in occ.values()):6}  {rare:7}  {sum(v >= 20 for v in occ.values()):8}')
    same = {g for (r, g) in occ} ; print(f'distinct strings ignoring role: {len(same)}')
    top_u = sorted(((v, g) for (r, g), v in occ.items() if r == 'U' and v <= 2), key=lambda x: -len(x[1]))[:12]
    print('sample rare whole-word symbols:', ' '.join(g for _, g in top_u))
    return occ


def seg_multi(counts, maxp=3, cost=0.0, iters=30, disc=3.0):
    """Each type -> 1..maxp pieces from one inventory; Viterbi EM; a piece costs `cost` nats extra. Each re-estimate
    subtracts `disc` from every unit's count (sparse prior), so units used fewer than `disc` times die; single glyphs
    keep a floor so every word stays coverable."""
    p = collections.Counter(); glyphs = {c for t in counts for c in t}
    for t, n in counts.items():          # start: every substring, token-weighted
        for i in range(len(t)):
            for j in range(i + 1, len(t) + 1): p[t[i:j]] += n
    best = {}
    for _ in range(iters):
        tot = sum(p.values()); lp = {k: math.log(v / tot) for k, v in p.items() if v > 0}
        for c in glyphs: lp.setdefault(c, math.log(0.1 / tot))
        new = collections.Counter()
        for t, n in counts.items():
            L = len(t)
            # dp[k][i]: best score covering t[:i] with k pieces
            dp = [[-1e18] * (L + 1) for _ in range(maxp + 1)]; bp = [[0] * (L + 1) for _ in range(maxp + 1)]
            dp[0][0] = 0.0
            for k in range(1, maxp + 1):
                for i in range(1, L + 1):
                    for j in range(i):
                        s = lp.get(t[j:i])
                        if s is None or dp[k - 1][j] <= -1e17: continue
                        v = dp[k - 1][j] + s - cost
                        if v > dp[k][i]: dp[k][i], bp[k][i] = v, j
            k = max(range(1, maxp + 1), key=lambda k: dp[k][L])
            if dp[k][L] <= -1e17:          # not coverable by maxp surviving units: kept whole (reported as such)
                best[t] = [t]; new[t] += n; continue
            parts, i = [], L
            while k > 0:
                j = bp[k][i]; parts.append(t[j:i]); i, k = j, k - 1
            best[t] = parts[::-1]
            for q in best[t]: new[q] += n
        p = collections.Counter({k: v - disc for k, v in new.items() if v - disc > 0})
    return best


def part2(name, toks, maxp, disc, cost=0.0):
    best = seg_multi(collections.Counter(toks), maxp=maxp, cost=cost, disc=disc)
    occ = collections.Counter(q for t in toks for q in best[t])
    npieces = sum(occ.values())
    whole = sum(1 for t in toks if best[t] == [t] and len(t) > 3)
    print(f'{name:9} maxp={maxp} disc={disc:4}: {len(occ):5} units, {sum(v <= 4 for v in occ.values()):5} with freq<=4, '
          f'{npieces / len(toks):.2f} pieces/word, {npieces / len(occ):6.1f} occ/unit, {whole / len(toks):.1%} words >3 glyphs unsplit; '
          f'top: {" ".join(g for g, _ in occ.most_common(12))}')


def min_pieces(t, inv, cap=6):
    """fewest pieces from `inv` that spell t (cap+1 if none within cap)"""
    L = len(t); dp = [0] + [cap + 1] * L
    for i in range(1, L + 1):
        for j in range(i):
            if dp[j] < cap and t[j:i] in inv: dp[i] = min(dp[i], dp[j] + 1)
    return dp[L]


def part3(name, toks, occ):
    """Coverage: inventory = the K pieces used most in the attack_v1 segmentation (roles merged); share of tokens
    spelled by at most 1/2/3/4 pieces from it."""
    by = collections.Counter()
    for (r, g), v in occ.items(): by[g] += v
    ranked = [g for g, _ in by.most_common()]
    for K in (50, 100, 250, 450, 1000):
        inv = set(ranked[:K]); need = collections.Counter(min_pieces(t, inv) for t in toks)
        cum = [sum(v for k, v in need.items() if k <= m) / len(toks) for m in (1, 2, 3, 4)]
        print(f'{name:8} K={K:5}: <=1 {cum[0]:6.1%}  <=2 {cum[1]:6.1%}  <=3 {cum[2]:6.1%}  <=4 {cum[3]:6.1%}')


def main():
    csv_path = sys.argv[1]; nums = [a for a in sys.argv[2:] if a.isdigit()]; N = int(nums[0]) if nums else 20000
    texts = {'Naibbe': first_n(rv.lines_synth(csv_path, N), N), 'Voynich': first_n(rv.lines_voynich(), N)}
    occs = {name: part1(name, toks) for name, toks in texts.items()}
    print('\n== Part 3: coverage by the K most used pieces')
    for name, toks in texts.items(): part3(name, toks, occs[name])
    if '--part2' not in sys.argv: return
    print('\n== Part 2: one shared inventory, 1..maxp pieces per word')
    for maxp, disc in [(2, 2.0), (2, 5.0), (3, 2.0), (3, 5.0), (3, 10.0), (4, 5.0)]:
        for name, toks in texts.items(): part2(name, toks, maxp, disc)


if __name__ == '__main__':
    main()
