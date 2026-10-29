"""CCCC 96 f. 240 (Bischoff 1954 no. 137): 'p3p3lap3edff.p4.g.gggharazy p3ar.' (Bischoff) /
'ipolapedff. o.g.gg gharazy p ar' (M. R. James 1912). p with n strokes = a vowel (Bischoff 137: 'p mit ein- bis
fünfmal durchstrichener Unterlänge', vowels; Kemly 'p1 p5 p3 = ave'), the other letters perhaps in a second system.
Search: every assignment of the five vowels to p1..p5 (120) x a consonant transform (identity, shift +-1..3 over the
consonants only or the whole alphabet, Atbash, reciprocal swaps), scored with lang/ English and Latin models.
Run from the repository root."""
import itertools, os, string, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
from lang import lm

A = string.ascii_lowercase
CONS = [c for c in A if c not in 'aeiou']
BISCHOFF = ['p3', 'p3', 'l', 'a', 'p3', 'e', 'd', 'f', 'f', ' ', 'p4', ' ', 'g', ' ', 'g', 'g', 'g', 'h', 'a', 'r', 'a', 'z', 'y', ' ', 'p3', 'a', 'r']


def transforms():
    yield 'identity', {}
    for k in (1, 2, 3, -1, -2, -3):
        yield f'alphabet shift {k:+d}', {c: A[(A.index(c) + k) % 26] for c in A}
        yield f'consonant shift {k:+d}', {c: CONS[(CONS.index(c) + k) % len(CONS)] for c in CONS}
    yield 'atbash', {c: A[25 - A.index(c)] for c in A}
    sw = {}
    for i in range(0, 26, 2):
        sw[A[i]], sw[A[i + 1]] = A[i + 1], A[i]
    yield 'swap ab cd', sw


def main():
    models = [(lm.load('en-modern'), 'early', 'en'), (lm.load('la'), 'latin', 'la')]
    res = []
    for vowels in itertools.permutations('aeiou'):
        for name, t in transforms():
            out = ''.join(vowels[int(x[1]) - 1] if x.startswith('p') else (x if x == ' ' else t.get(x, x)) for x in BISCHOFF)
            for m, sch, ln in models:
                res.append((m.per_char(lm.norm(out, sch)), ln, ''.join(vowels), name, out))
    res.sort(reverse=True)
    seen = set()
    for r in res:
        if r[4] in seen:
            continue
        seen.add(r[4])
        print(f'{r[0]:6.2f} {r[1]} p1-5={r[2]} {r[3]:20s} {r[4]}')
        if len(seen) >= 25:
            break


if __name__ == '__main__':
    main()
