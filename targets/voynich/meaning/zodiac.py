"""Zodiac labels: does the k-th label of one sign resemble the k-th label of another (day or degree names)?

Data: ZL3b, the twelve zodiac pages ($I=Z: f70v2 f70v1 f71r f71v f72r1 f72r2 f72r3 f72v3 f72v2 f72v1 f73r f73v),
label loci (type L). Labels are ordered as transcribed (rings outer to inner, each ring in reading order), readings
in [a:b] take the first, words with unread glyphs dropped. Similarity of two labels = 1 - normalised Levenshtein
distance over glyph units (cth ckh cph cfh ch sh single). For a pair of pages, sequence B is cyclically shifted
against A, the mean similarity of aligned labels is taken over the shorter length, and the best shift is kept;
statistic = mean over the 66 page pairs. Null: each page's labels shuffled (words kept, order destroyed), 1,000 times.
A positional naming scheme (the same day names on every sign, as in calendars) gives a statistic above the null.
Also reported: label words that recur on two or more zodiac pages.

Run from the repository root: python targets/voynich/meaning/zodiac.py
"""
import collections, itertools, os, random, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'glyphs'))
from variants import UNIT

ZL = os.path.join(HERE, '..', 'data', 'ZL3b-n.txt')
PAGES = ['f70v2', 'f70v1', 'f71r', 'f71v', 'f72r1', 'f72r2', 'f72r3', 'f72v3', 'f72v2', 'f72v1', 'f73r', 'f73v']


def labels():
    out = collections.OrderedDict((p, []) for p in PAGES)
    for line in open(ZL, encoding='utf-8'):
        m = re.match(r'<(f\w+)\.\d+,.(L)\w*>\s+(.*)', line)
        if not m or m.group(1) not in out: continue
        s = re.sub(r'<![^>]*>|<%>|<\$>|<->', '', m.group(3)); s = re.sub(r'\[([^:\]]*):[^\]]*\]', r'\1', s)
        s = s.replace('{', '').replace('}', '')
        for w in re.split(r'[.,]', s):
            if re.fullmatch(r'[a-z]+', w): out[m.group(1)].append(UNIT.findall(w))
    return out


def lev(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[-1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def stat(seqs, S):
    tot = 0.0
    for a, b in itertools.combinations(range(len(seqs)), 2):
        A, B = seqs[a], seqs[b]
        if len(A) > len(B): A, B = B, A; a, b = b, a
        n, m = len(A), len(B)
        best = max(sum(S[a][i][b][(i + s) % m] for i in range(n)) / n for s in range(m))
        tot += best
    return tot / (len(seqs) * (len(seqs) - 1) / 2)


def main():
    L = labels()
    seqs = [L[p] for p in PAGES]
    print('labels per page:', {p: len(v) for p, v in L.items()})
    # similarity lookup: S[a][i][b][j]
    S = [[[[1 - lev(x, y) / max(len(x), len(y)) for y in seqs[b]] for b in range(len(seqs))] for x in seqs[a]] for a in range(len(seqs))]
    obs = stat(seqs, S)
    rng = random.Random(3); null = []
    idx = [list(range(len(s))) for s in seqs]
    for _ in range(1000):
        perm = [rng.sample(ix, len(ix)) for ix in idx]
        P = [[[[S[a][perm[a][i]][b][perm[b][j]] for j in range(len(seqs[b]))] for b in range(len(seqs))] for i in range(len(seqs[a]))] for a in range(len(seqs))]
        null.append(stat(seqs, P))
    mu = sum(null) / len(null); sd = (sum((x - mu) ** 2 for x in null) / len(null)) ** 0.5
    p = (1 + sum(x >= obs for x in null)) / (1 + len(null))
    print(f'aligned similarity (best cyclic shift, mean over 66 pairs): observed {obs:.4f}; shuffled {mu:.4f} +- {sd:.4f}; z {(obs - mu) / sd:.2f}; p {p:.3f}')
    where = collections.defaultdict(set)
    for pg, ws in L.items():
        for w in ws: where[''.join(w)].add(pg)
    rec = {w: sorted(s) for w, s in where.items() if len(s) >= 2}
    print(f'{len(where)} distinct label words; {len(rec)} occur on two or more zodiac pages: ' + ', '.join(f'{w} {len(s)}' for w, s in sorted(rec.items(), key=lambda x: -len(x[1]))))


if __name__ == '__main__':
    main()
