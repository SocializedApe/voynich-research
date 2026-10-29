"""Do Voynich herbal pages open with a formula, as entries in medieval herbals do ('X calida est et sicca ...')?

Herbal pages (ZL illustration type H), paragraph text. For each hand: mean word-type Jaccard between the first lines
of two different pages, against the same between the second lines, and between randomly chosen interior lines (one
per page, excluding the first two lines; 200 draws). A recurring opening formula makes first lines share more words
across pages than other lines do. Also reported without each line's first word (the paragraph-initial gallows word
has its own spelling habits), and the share of first words that recur as the first word of another page.

--merge-gallows: p -> t and f -> k (cph -> cth, cfh -> ckh) first, since f/p behave as paragraph-first-line forms of
k/t (glyphs/README.md s3) and would otherwise make first-line words rarer by spelling alone.
Run from the repository root: python targets/voynich/meaning/formula.py [--merge-gallows]
"""
import collections, csv, itertools, os, random, re, statistics, sys
HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, '..', 'data', 'ZL3b-n.fixed.words.tsv')


def jac(a, b): return len(a & b) / len(a | b) if (a | b) else 0.0


def mean_pair(lines):
    v = [jac(set(a), set(b)) for a, b in itertools.combinations(lines, 2)]
    return statistics.mean(v) if v else float('nan')


def main():
    pages = collections.OrderedDict()
    for r in csv.DictReader(open(TSV, encoding='utf-8'), delimiter='\t'):
        if r['locus_type'] != 'P' or r['illus'] != 'H': continue
        ws = [w for w in r['line_words'].split() if re.fullmatch(r'[a-z]+', w)]
        if '--merge-gallows' in sys.argv: ws = [w.replace('p', 't').replace('f', 'k') for w in ws]
        if ws: pages.setdefault((r['hand'], r['folio']), []).append(ws)
    rng = random.Random(3)
    for hand in sorted({h for h, _ in pages}):
        P = [ls for (h, _), ls in pages.items() if h == hand and len(ls) >= 4]
        if len(P) < 8: continue
        first = [ls[0] for ls in P]; second = [ls[1] for ls in P]
        interior = [statistics.mean(mean_pair([rng.choice(ls[2:]) for ls in P]) for _ in range(1)) for _ in range(200)]
        lo, hi = sorted(interior)[5], sorted(interior)[194]
        f1 = mean_pair(first); f2 = mean_pair(second)
        nf = mean_pair([l[1:] for l in first]); ns = mean_pair([l[1:] for l in second])
        fw = collections.Counter(l[0] for l in first)
        rec = sum(c for c in fw.values() if c > 1) / len(first)
        print(f'hand {hand}: {len(P)} herbal pages | first lines {f1:.4f}, second {f2:.4f}, interior {statistics.mean(interior):.4f} '
              f'(95% {lo:.4f}-{hi:.4f}) | without first word: first {nf:.4f}, second {ns:.4f} | first words recurring as another page\'s first word: {rec:.0%}')


if __name__ == '__main__':
    main()
