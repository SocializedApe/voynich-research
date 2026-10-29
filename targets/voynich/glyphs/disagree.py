"""Where do independent EVA transcriptions disagree? ZL3b (Zandbergen-Landini), IT2a (Takahashi), RF1b-er.

Every line present in two transcriptions is aligned glyph by glyph (difflib on EVA letters, word space as its own
symbol). Reported: substitutions between glyphs (a<->o and so on) as a share of the glyph's occurrences, word-space
disagreements (one transcriber splits a word the other keeps whole), and insertions/deletions (one transcriber sees
a stroke or glyph the other does not, e.g. i vs ii, e vs ee). Paragraph text only (locus type P).

Run from the repository root: python targets/voynich/glyphs/disagree.py
"""
import collections, csv, difflib, os, re
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
FILES = {'ZL': 'ZL3b-n.words.tsv', 'IT': 'IT2a-n.words.tsv', 'RF': 'RF1b-er.words.tsv'}


def load(name):
    out = {}
    for r in csv.DictReader(open(os.path.join(DATA, FILES[name]), encoding='utf-8'), delimiter='\t'):
        if r['locus_type'] != 'P': continue
        ws = [w for w in r['line_words'].split() if re.fullmatch(r'[a-z]+', w)]
        if len(ws) == len(r['line_words'].split()): out[r['line_id']] = ' '.join(ws)
    return out


def compare(A, B, la, lb):
    sub, ins, freq = collections.Counter(), collections.Counter(), collections.Counter()
    n_lines = n_same = 0
    for k in sorted(set(A) & set(B)):
        a, b = A[k], B[k]; n_lines += 1; n_same += a == b
        freq.update(a)
        for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
            if op == 'replace' and i2 - i1 == j2 - j1:
                for x, y in zip(a[i1:i2], b[j1:j2]): sub[tuple(sorted((x, y)))] += 1
            elif op != 'equal':
                # unequal replace, insert, delete: record the strings each side has
                ins[(a[i1:i2] or '-', b[j1:j2] or '-')] += 1
    tot = sum(freq.values())
    print(f'\n== {la} vs {lb}: {n_lines} common lines, {n_same / n_lines:.1%} identical, {tot} glyphs ({la})')
    nsub = sum(sub.values()); nsp = sum(v for (x, y), v in sub.items() if ' ' in (x, y))
    sp_ins = sum(v for (x, y), v in ins.items() if ' ' in x + y and x.strip() == y.strip())
    print(f'glyph substitutions {nsub} ({nsub / tot:.2%} of glyphs); word-space only disagreements {sp_ins}')
    print('top substitutions (pair: count, % of the rarer glyph\'s occurrences):')
    for (x, y), v in sub.most_common(14):
        if ' ' in (x, y): continue
        print(f'  {x}<->{y}: {v:5}  {v / min(freq[x] or 1, freq[y] or 1):6.2%}')
    print('top insertions/deletions/unequal replacements:')
    for (x, y), v in ins.most_common(14):
        print(f'  {x!r} vs {y!r}: {v}')


def main():
    T = {k: load(k) for k in FILES}
    compare(T['ZL'], T['IT'], 'ZL', 'IT')
    compare(T['ZL'], T['RF'], 'ZL', 'RF')
    compare(T['IT'], T['RF'], 'IT', 'RF')


if __name__ == '__main__':
    main()
