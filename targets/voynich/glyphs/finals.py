"""Are Voynich word-final glyphs end-of-word forms of word-internal glyphs (like Greek final sigma)?

For each unit: the distribution of the unit before it, separately for word-final occurrences and for non-final
occurrences. If final X is the end form of internal Y, X-final follows the same units Y-internal does, so the left
context distance (JSD) of X-final against Y-internal is small, and the best match of a letter's final form is
itself in a real script. Sanity check on Latin and on Latin with s written as a distinct final form ('S' at word
end): the method must pair S-final with s-internal.

Run from the repository root: python targets/voynich/glyphs/finals.py
"""
import collections, csv, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', '..'))
from variants import UNIT, DATA, jsd

MIN = 200


def table(words):
    Lf, Ln = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
    for u in words:
        for i, g in enumerate(u):
            prev = u[i - 1] if i else '#'
            (Lf if i == len(u) - 1 else Ln)[g][prev] += 1
    return Lf, Ln


def report(name, words, show):
    Lf, Ln = table(words)
    fin = [g for g in Lf if sum(Lf[g].values()) >= MIN]
    internal = [g for g in Ln if sum(Ln[g].values()) >= MIN]
    print(f'\n== {name}: best internal match for each final form (left-context JSD; lower = same letter)')
    for g in sorted(fin, key=lambda g: -sum(Lf[g].values()))[:show]:
        ds = sorted((jsd(Lf[g], Ln[h]), h) for h in internal)
        self_d = next((d for d, h in ds if h == g), None)
        print(f'  final {g:4} (n={sum(Lf[g].values()):5}): ' + ', '.join(f'{h} {d:.3f}' for d, h in ds[:4]) +
              (f'   | itself internal {self_d:.3f}' if self_d is not None else '   | never internal'))


def main():
    vw = []
    for r in csv.DictReader(open(os.path.join(DATA, 'ZL3b-n.fixed.words.tsv'), encoding='utf-8'), delimiter='\t'):
        if r['locus_type'] == 'P':
            vw += [UNIT.findall(w) for w in r['line_words'].split() if re.fullmatch(r'[a-z]+', w)]
    from lang import lm, corpora
    lw = lm.norm(corpora.text(['la-gutenberg'])[:2000000], 'latin', True).split()
    lw = lw[len(lw) // 4: len(lw) // 4 + 34000]
    report('Latin', [list(w) for w in lw], 8)
    report('Latin, final s written S', [list(w[:-1]) + ['S' if w[-1] == 's' else w[-1]] for w in lw], 8)
    report('Voynich (ZL, paragraph text)', vw, 10)


if __name__ == '__main__':
    main()
