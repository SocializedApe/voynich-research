"""Do Voynich's previous-word endings fall into a few discrete groups, as a chained cipher's tables would make them?

If a word's encoding table is chosen by how the previous word ended (chaining), endings that select the same table
are interchangeable: the words after them open with the same distribution. Endings then form a few groups (one per
table) whose members are statistically indistinguishable, while groups differ. A smooth mechanism gives no such
blocks.

Method. Interior word pairs (a, b) inside a line (first and last word of each line excluded). Context = last glyph
unit of a; response = first glyph unit of b (and, as a check, the first two units). Contexts with >= MIN_N
occurrences. For every pair of contexts (i, j): D = Jensen-Shannon divergence of their response distributions, and a
permutation null (pool the responses of i and j, re-split at random into sizes n_i, n_j, 200 times); the pair is
INDISTINGUISHABLE if D <= the null's 95th percentile. Indistinguishable pairs are edges of a graph; its connected
components are candidate tables. Block score = share of all context pairs that are indistinguishable AND lie inside
one component whose every member pair is indistinguishable (a clique), i.e. how much of the structure is clean blocks.

Texts: Voynich (fixed parse); positive control = round-8 chained cipher without null words (six tables chosen by the
previous word's last character, chain probability 0.7); negative controls = Latin (letters as units) and the
autocopist (s19).

Decision, fixed before the run (28 Oct 2026, this commit):
  SURVIVES (chaining has a discrete-table signature in Voynich) if Voynich has at least two components of >= 2
  contexts that are cliques, together covering >= 50% of its contexts, and its block score is >= 50% of the positive
  control's.
  FAILS if Voynich has no clique component of >= 2 contexts beyond what Latin shows, or its block score is < 25% of the
  positive control's. Otherwise undecided.

Run from the repository root: python research/voynich_siblings/context_tables.py <naibbe_tables.csv>
"""
import collections, itertools, math, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import cipher_models as cm, hybrid_model as h1, slot_independence as si, a4_selfcitation as a4

MIN_N = 300
PERM = 200


def jsd(c1, c2):
    n1, n2 = sum(c1.values()), sum(c2.values())
    keys = set(c1) | set(c2); d = 0.0
    for k in keys:
        p, q = c1.get(k, 0) / n1, c2.get(k, 0) / n2; m = (p + q) / 2
        if p: d += 0.5 * p * math.log2(p / m)
        if q: d += 0.5 * q * math.log2(q / m)
    return d


def collect(pages, unit, k=1):
    ctx = collections.defaultdict(list)
    for p in pages:
        for ln in p['lines']:
            ws = ln['words'][1:-1]
            for a, b in zip(ws, ws[1:]):
                ub = unit(b)
                if len(ub) >= k:
                    ctx[unit(a)[-1]].append(tuple(ub[:k]))
    return {c: r for c, r in ctx.items() if len(r) >= MIN_N}


def analyse(ctx, rng):
    names = sorted(ctx, key=lambda c: -len(ctx[c]))
    cnt = {c: collections.Counter(ctx[c]) for c in names}
    indist = {}
    for i, j in itertools.combinations(names, 2):
        d = jsd(cnt[i], cnt[j])
        pool = ctx[i] + ctx[j]; ni = len(ctx[i]); null = []
        for _ in range(PERM):
            rng.shuffle(pool)
            null.append(jsd(collections.Counter(pool[:ni]), collections.Counter(pool[ni:])))
        null.sort()
        indist[(i, j)] = d <= null[int(0.95 * PERM)]
    # components
    parent = {c: c for c in names}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for (i, j), ok in indist.items():
        if ok: parent[find(i)] = find(j)
    comps = collections.defaultdict(list)
    for c in names: comps[find(c)].append(c)
    comps = sorted(comps.values(), key=len, reverse=True)
    cliques = [g for g in comps if len(g) >= 2 and all(indist[tuple(sorted(p, key=names.index))] for p in itertools.combinations(g, 2))]
    npairs = len(indist)
    in_clique = sum(len(g) * (len(g) - 1) // 2 for g in cliques)
    return dict(n_ctx=len(names), n_indist=sum(indist.values()), npairs=npairs, comps=comps, cliques=cliques,
                block=in_clique / npairs if npairs else 0.0, covered=sum(len(g) for g in cliques) / len(names), cnt=cnt)


def main():
    rng = random.Random(131)
    zl = a4.load_zl(); skel = a4.skeleton(zl)
    lat = os.path.join(HERE, '..', '..', 'lang', 'corpora', 'la-gutenberg.txt')
    chained = cm.generate(cm.Variant(sys.argv[1], 19, merge=0.1, **dict(h1.BASE, nulls=0.0)), lat, skel)
    latin = a4.pour(si.corpus('Latin')[:40000], skel)
    texts = [('Voynich (fixed parse)', zl, si.eva_units), ('chained cipher (positive control)', chained, si.eva_units),
             ('Latin (letters)', latin, list), ('autocopist s19', a4.Autocopist(19).generate(skel), si.eva_units)]
    out = {}
    for k in (1, 2):
        print(f'\n=== response = first {k} unit(s)')
        print(f'{"text":34s} {"contexts":>8s} {"indist. pairs":>14s} {"components":>10s} {"clique comps>=2":>15s} {"covered":>8s} {"block":>6s}')
        for name, pages, unit in texts:
            r = analyse(collect(pages, unit, k), rng)
            out[(name, k)] = r
            print(f'{name:34s} {r["n_ctx"]:8d} {r["n_indist"]:6d}/{r["npairs"]:<7d} {len(r["comps"]):10d} {len(r["cliques"]):15d} {r["covered"]:8.2f} {r["block"]:6.3f}', flush=True)
    for name in ('Voynich (fixed parse)', 'chained cipher (positive control)'):
        r = out[(name, 1)]
        print(f'\n{name}: clique groups of previous endings (k = 1), with the commonest openings after them')
        for g in r['cliques']:
            pooled = sum((r['cnt'][c] for c in g), collections.Counter())
            tot = sum(pooled.values())
            print('  {' + ' '.join(g) + '}  ->  ' + ', '.join(f'{"".join(o)} {v / tot:.2f}' for o, v in pooled.most_common(6)))
        singles = [g[0] for g in r['comps'] if len(g) == 1]
        print('  singletons:', ' '.join(singles))


if __name__ == '__main__':
    main()
