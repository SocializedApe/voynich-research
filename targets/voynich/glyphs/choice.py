"""What decides between the near-twin glyphs (k/t, ch/sh, f/p, cth/ckh, a/o, r/s)? Scribe, place, or neighbours?

For every occurrence of either member of a pair: the choice (first or second member) and its conditions: hand (Davis's
five scribes, ZL $H), Currier language, line position (paragraph-first line, first word of a line, last word),
previous unit, next unit. Reported: share of the second member per condition, and how much each condition explains
(mutual information with the choice, bits; and as a share of the choice's entropy). Also the context distance of the
pair computed within one hand only, against the pooled distance (variants.py): if the pair is near the homophone
floor (about 0.001-0.01 at these sizes) inside every hand, the difference between the members is a scribal habit.

Run from the repository root: python targets/voynich/glyphs/choice.py
"""
import collections, csv, math, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from variants import UNIT, jsd, DATA

PAIRS = [('k', 't'), ('ch', 'sh'), ('f', 'p'), ('ckh', 'cth'), ('a', 'o'), ('r', 's'), ('l', 'r')]


def H(c):
    n = sum(c.values()); return -sum(v / n * math.log2(v / n) for v in c.values() if v)


def mi(rows, key):
    """I(choice; condition) from (choice, conditions) rows"""
    joint = collections.Counter((r[key], r['ch']) for r in rows)
    byc = collections.Counter(r[key] for r in rows)
    ch = collections.Counter(r['ch'] for r in rows)
    return H(ch) + H(byc) - H(joint), H(ch)


def main():
    occ = collections.defaultdict(list)
    ctx = collections.defaultdict(lambda: (collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)))
    for r in csv.DictReader(open(os.path.join(DATA, 'ZL3b-n.fixed.words.tsv'), encoding='utf-8'), delimiter='\t'):
        if r['locus_type'] != 'P': continue
        ws = [w for w in r['line_words'].split() if re.fullmatch(r'[a-z]+', w)]
        for wi, w in enumerate(ws):
            u = ['#'] + UNIT.findall(w) + ['#']
            for i in range(1, len(u) - 1):
                g = u[i]
                L, R = ctx[r['hand']]; L[g][u[i - 1]] += 1; R[g][u[i + 1]] += 1
                for a, b in PAIRS:
                    if g in (a, b):
                        occ[(a, b)].append({'ch': g == b, 'hand': r['hand'], 'lang': r['lang'],
                                            'pfl': r['para_start'] == '1', 'wpos': 'first' if wi == 0 else 'last' if wi == len(ws) - 1 else 'mid',
                                            'prev': u[i - 1], 'next': u[i + 1], 'folio': r['folio']})
    hands = sorted(h for h in ctx if h not in ('', '?', 'X', 'Y'))
    for a, b in PAIRS:
        rows = occ[(a, b)]
        print(f'\n== {a}/{b}: {len(rows)} occurrences, share of {b}: {sum(r["ch"] for r in rows) / len(rows):.1%}')
        line = []
        for h in hands:
            rr = [r for r in rows if r['hand'] == h]
            if len(rr) >= 30: line.append(f'hand {h} {sum(r["ch"] for r in rr) / len(rr):.0%} (n={len(rr)})')
        print('  by hand:', '; '.join(line))
        for key, lab in (('pfl', 'para-first line'), ('wpos', 'word in line')):
            parts = collections.defaultdict(list)
            for r in rows: parts[r[key]].append(r['ch'])
            print(f'  by {lab}:', '; '.join(f'{k} {sum(v) / len(v):.0%} (n={len(v)})' for k, v in sorted(parts.items(), key=str)))
        expl = []
        for key in ('hand', 'lang', 'folio', 'pfl', 'wpos', 'prev', 'next'):
            m, h0 = mi(rows, key); expl.append(f'{key} {m:.3f} ({m / h0:.0%})')
        print('  information about the choice (bits, share of its entropy):', ', '.join(expl))
        within = []
        for h in hands:
            L, R = ctx[h]
            if sum(L[a].values()) >= 150 and sum(L[b].values()) >= 150:
                within.append(f'hand {h} {(jsd(L[a], L[b]) + jsd(R[a], R[b])) / 2:.3f}')
        print('  context distance within one hand:', ', '.join(within) or '(too few)')


if __name__ == '__main__':
    main()
