"""Controls for slot_independence.py: which text-making mechanisms give Voynich's low start/end dependence?

Adds, at the same token count and with the same measure (first/last k glyph units, tokens of 4-8 units, length held
fixed, shuffle baseline subtracted, normalised):
  - autocopist s19, s7   Timm & Schinner self-citation generator (targets/voynich/a4_selfcitation.Autocopist)
  - rugg grille / sorted Rugg 2004 table-and-grille, Rugg & Taylor sorted table (a4 Rugg, RuggSorted)
  - naibbe (Pliny)       Greshko 2025, the shipped ciphertext encrypted/nathist_output_ciphertext.txt from
                         github.com/greshko/naibbe-cipher (path given as argv[1]; not committed here)
  - verbose Latin        each Latin letter -> a fixed 2-glyph group from a random table of Voynich-like pairs
  - verbose homophonic   each Latin letter -> one of 3 such groups, chosen at random each time
and repeats every row on word TYPES (each distinct word once) as well as tokens.

Run from the repository root:
  python -I research/voynich_siblings/slot_controls.py <path to nathist_output_ciphertext.txt>
"""
import os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', 'targets', 'voynich'))
import slot_independence as si
import a4_selfcitation as a4

N = si.N_TOK


def flat(pages):
    return [w for p in pages for ln in p['lines'] for w in ln['words']]


def verbose_latin(rng, n):
    pairs = ['qo', 'ok', 'ol', 'ch', 'sh', 'ed', 'dy', 'ai', 'in', 'ar', 'or', 'al', 'ee', 'ot', 'ke', 'te',
             'da', 'yk', 'od', 'ey', 'cth', 'lk', 'sa', 'ro', 'am', 'ir']
    table = dict(zip('abcdefghijklmnopqrstuvwxyz', rng.sample(pairs, 26)))
    lat = si.corpus('Latin')
    start = rng.randrange(0, len(lat) - n)
    return [''.join(table[c] for c in w) for w in lat[start:start + n]]


def verbose_latin_homophonic(rng, n, k=3):
    """each Latin letter -> one of k 2-glyph groups chosen at random at each use"""
    pool = [a + b for a in ['q', 'o', 'ch', 'sh', 'd', 'y', 'a', 'e', 'k', 't', 'l', 'r'] for b in ['o', 'ol', 'ed', 'dy', 'ai', 'in', 'ar', 'or', 'al', 'ee', 'y', 'e']]
    rng.shuffle(pool)
    table = {c: pool[i * k:(i + 1) * k] for i, c in enumerate('abcdefghijklmnopqrstuvwxyz')}
    lat = si.corpus('Latin')
    start = rng.randrange(0, len(lat) - n)
    return [''.join(rng.choice(table[c]) for c in w) for w in lat[start:start + n]]


def main():
    rng = random.Random(si.SEED)
    zl = a4.load_zl(); skel = a4.skeleton(zl)
    texts = []
    v = si.voynich(); rng.shuffle(v)
    texts.append(('Voynich all', v[:N]))
    for seed in (19, 7):
        texts.append((f'autocopist s{seed}', flat(a4.Autocopist(seed).generate(skel))[:N]))
    texts.append(('rugg grille', flat(a4.Rugg(19).generate(skel))[:N]))
    texts.append(('rugg sorted table', flat(a4.RuggSorted(19).generate(skel))[:N]))
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        nb = open(sys.argv[1], encoding='utf-8', errors='replace').read().split()
        nb = [w for w in nb if w.isalpha()]
        texts.append(('naibbe (Pliny, shipped)', nb[:N]))
    texts.append(('verbose Latin (2 glyphs/letter)', verbose_latin(rng, N)))
    texts.append(('verbose Latin, 3 homophones/letter', verbose_latin_homophonic(rng, N)))
    for name in si.CORP:
        c = si.corpus(name); s = rng.randrange(0, len(c) - N)
        texts.append((name, c[s:s + N]))
    print(f'{"text":34s} {"k":>2s} {"tokens":>7s} {"norm.":>7s} | {"types":>6s} {"norm.":>7s}')
    for k in (1, 2):
        for name, ws in texts:
            unit = (lambda w: list(w)) if name in si.CORP else si.eva_units
            tok = [unit(w) for w in ws]
            typ = [unit(w) for w in sorted(set(ws))]
            a, _, n1 = si.measure(tok, k, rng)
            b, _, n2 = si.measure(typ, k, rng)
            print(f'{name:34s} {k:2d} {n1:7d} {a:7.3f} | {n2:6d} {b:7.3f}')


if __name__ == '__main__':
    main()
