"""How much do the glyphs themselves decide where Voynich word spaces fall?

Every gap between two adjacent units in a line is a break (space) or not. Predict the break from the unit before and
the unit after the gap (majority rule per (before, after) pair, fitted on half the lines, scored on the other half),
and report accuracy, the information the pair carries about the break (share of the break's entropy), and the same
for Latin, Renaissance Italian and German text cut into lines of 40 letters. Also: where do transcribers disagree
about spaces (ZL against RF1b), by the unit before the gap.

If Voynich breaks are nearly fixed by the neighbouring glyphs while Latin's are not, the spaces add little to the
glyph stream: word division is then a by-product of glyph classes (finals and initials), not an independent signal.

Run from the repository root: python targets/voynich/glyphs/spaces.py
"""
import collections, csv, difflib, math, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', '..'))
from variants import UNIT, DATA
from choice import H


def gaps(lines):
    """lines = lists of words (each a list of units) -> (before, after, is_break) for every inner gap"""
    out = []
    for ws in lines:
        seq = []
        for wi, w in enumerate(ws):
            for ui, u in enumerate(w):
                seq.append((u, ui == 0 and wi > 0))
        for i in range(1, len(seq)):
            out.append((seq[i - 1][0], seq[i][0], seq[i][1]))
    return out


def score(name, lines):
    g = gaps(lines); half = len(g) // 2; train, test = g[:half], g[half:]
    tab = collections.defaultdict(collections.Counter)
    for a, b, br in train: tab[(a, b)][br] += 1
    prior = collections.Counter(br for *_, br in train).most_common(1)[0][0]
    acc = sum((tab[(a, b)].most_common(1)[0][0] if tab[(a, b)] else prior) == br for a, b, br in test) / len(test)
    base = max(collections.Counter(br for *_, br in test).values()) / len(test)
    def info(f):
        j = collections.Counter((f(x), x[2]) for x in g); c = collections.Counter(f(x) for x in g)
        b = collections.Counter(x[2] for x in g); return (H(b) + H(c) - H(j)) / H(b)
    print(f'{name:28} gaps {len(g):7}, breaks {sum(x[2] for x in g) / len(g):5.1%}; held-out accuracy {acc:.1%} '
          f'(always-majority {base:.1%}); info in before {info(lambda x: x[0]):.0%}, after {info(lambda x: x[1]):.0%}, '
          f'both {info(lambda x: x[:2]):.0%}')


def main():
    vl = []
    for r in csv.DictReader(open(os.path.join(DATA, 'ZL3b-n.fixed.words.tsv'), encoding='utf-8'), delimiter='\t'):
        if r['locus_type'] == 'P':
            ws = [UNIT.findall(w) for w in r['line_words'].split() if re.fullmatch(r'[a-z]+', w)]
            if ws: vl.append(ws)
    from lang import lm, corpora
    score('Voynich ZL', vl)
    for name, src in (('Latin', 'la-gutenberg'), ('Italian 1500-1600', 'it-renaissance'), ('German 1470-1610', 'de-dta-1470-1610')):
        ws = lm.norm(corpora.text([src])[:2000000], 'early', True).split()
        ws = ws[len(ws) // 4: len(ws) // 4 + 34000]
        lines, cur, n = [], [], 0
        for w in ws:
            cur.append(list(w)); n += len(w)
            if n >= 40: lines.append(cur); cur, n = [], 0
        score(name, lines)
    # transcriber disagreement on spaces, by unit before the gap (ZL vs RF), letters only
    from disagree import load
    A, B = load('ZL'), load('RF')
    tot, dis = collections.Counter(), collections.Counter()
    for k in set(A) & set(B):
        a, b = A[k], B[k]
        if a.replace(' ', '') != b.replace(' ', ''): continue      # same glyphs, compare spaces only
        pa = {i for i, c in enumerate(a.replace(' ', '|')) if c == '|'}
        def breaks(s):
            out, j = set(), 0
            for c in s:
                if c == ' ': out.add(j)
                else: j += 1
            return out
        ba, bb = breaks(a), breaks(b); s = a.replace(' ', '')
        for j in range(1, len(s)):
            tot[s[j - 1]] += 1
            if (j in ba) != (j in bb): dis[s[j - 1]] += 1
    print('\nZL vs RF, lines with identical glyphs: space disagreement rate by glyph before the gap')
    print('  ' + '; '.join(f'{c}: {dis[c] / tot[c]:.1%} (n={tot[c]})' for c, _ in tot.most_common(14)))


if __name__ == '__main__':
    main()
