"""Are the stroke-level glyph pairs (a/o, r/s, k/t, f/p, ch/sh, ...) different letters or variants of one?

Units: EVA with the benches and pedestalled gallows as single units (cth ckh cph cfh ch sh), every other letter
single; '#' marks a word edge. For every unit with at least 300 occurrences in ZL paragraph text: the distribution of
the unit before it and the unit after it. Distance between two units = mean Jensen-Shannon divergence of their left
and right context distributions (bits, 0 = interchangeable contexts, 1 = disjoint). The candidate pairs are set
against all pairs of frequent units.
Also: share of each gallows in paragraph-first lines, and by Currier language, to test whether f/p are k/t written
in a special place or by a special scribe.

Run from the repository root: python targets/voynich/glyphs/variants.py
"""
import collections, csv, itertools, math, os, re
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
UNIT = re.compile(r'cth|ckh|cph|cfh|ch|sh|[a-z]')
PAIRS = [('a', 'o'), ('r', 's'), ('k', 't'), ('f', 'p'), ('f', 'k'), ('p', 't'), ('ch', 'sh'), ('cth', 'ckh'),
         ('e', 'i'), ('o', 'y'), ('a', 'y'), ('d', 'l'), ('n', 'r'), ('l', 'r')]


def rows():
    for r in csv.DictReader(open(os.path.join(DATA, 'ZL3b-n.fixed.words.tsv'), encoding='utf-8'), delimiter='\t'):
        if r['locus_type'] == 'P':
            ws = [w for w in r['line_words'].split() if re.fullmatch(r'[a-z]+', w)]
            yield r, ws


def jsd(p, q):
    keys = set(p) | set(q); sp, sq = sum(p.values()), sum(q.values()); d = 0.0
    for k in keys:
        a, b = p.get(k, 0) / sp, q.get(k, 0) / sq; m = (a + b) / 2
        if a: d += 0.5 * a * math.log2(a / m)
        if b: d += 0.5 * b * math.log2(b / m)
    return d


def main():
    L, R, freq = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter), collections.Counter()
    gal = collections.defaultdict(collections.Counter)
    first_line = None
    for r, ws in rows():
        pf = r['para_start'] == '1'
        for w in ws:
            u = ['#'] + UNIT.findall(w) + ['#']
            for i in range(1, len(u) - 1):
                g = u[i]; freq[g] += 1; L[g][u[i - 1]] += 1; R[g][u[i + 1]] += 1
                base = {'cth': 't', 'ckh': 'k', 'cph': 'p', 'cfh': 'f'}.get(g, g)
                if base in 'kftp':
                    gal[base]['para_first_line' if pf else 'other_line'] += 1; gal[base]['lang_' + r['lang']] += 1
    common = [g for g, n in freq.items() if n >= 300]
    dist = {}
    for a, b in itertools.combinations(sorted(common), 2):
        dist[(a, b)] = (jsd(L[a], L[b]) + jsd(R[a], R[b])) / 2
    allv = sorted(dist.values())
    def pct(v): return sum(x < v for x in allv) / len(allv)
    print(f'{len(common)} units with >= 300 occurrences, {len(allv)} pairs; context distance median {allv[len(allv) // 2]:.3f}, '
          f'10th pct {allv[len(allv) // 10]:.3f}, min {allv[0]:.3f}')
    print('pair        n_a     n_b    distance  percentile among all pairs (low = more interchangeable)')
    for a, b in PAIRS:
        k = tuple(sorted((a, b)))
        if k in dist:
            print(f'{a:>4}/{b:<4} {freq[a]:7} {freq[b]:7}   {dist[k]:.3f}     {pct(dist[k]):6.1%}')
        else:
            print(f'{a:>4}/{b:<4} {freq[a]:7} {freq[b]:7}   (rare: below 300)')
    print('closest 12 pairs overall:', ', '.join(f'{a}/{b} {v:.3f}' for (a, b), v in sorted(dist.items(), key=lambda x: x[1])[:12]))
    print('\ngallows (plain + pedestalled) by place and Currier language:')
    for g in 'kftp':
        c = gal[g]; n = c['para_first_line'] + c['other_line']
        print(f'  {g}: {n:6}  in paragraph-first lines {c["para_first_line"] / n:6.1%}   language A {c["lang_A"] / n:6.1%}')
    print('  (share of all text lines that are paragraph-first: see first row of each paragraph)')
    nf = sum(1 for r, ws in rows() if r['para_start'] == '1'); nt = sum(1 for _ in rows())
    print(f'  paragraph-first lines: {nf} of {nt} = {nf / nt:.1%}')


if __name__ == '__main__':
    main()
