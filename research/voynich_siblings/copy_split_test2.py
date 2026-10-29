"""Candidate 2: a chained cipher of repetitive, formulaic Latin. Does it reproduce Voynich's copy-split pattern?

copy_split_test.py found that in Voynich the near-copy words (edit distance <= 1 to one of the previous 8 words on
the page) obey the boundary rule MORE strongly than the other words (coupling ratio other/copy 0.76), unlike the
cipher+copying hybrid (3.5-5.6), the pure cipher on Latin prose (1.6) and the self-citation generator (both near 0).
Candidate 2: the near-copies come from repeated plaintext in the same context, which a chained cipher turns into
near-identical words that carry the boundary rule.

Plaintext: formulaic instructional Latin = Apicius, De re coquinaria books 1-5 + Cato, De agri cultura (The Latin
Library, path argv[2]); control: the Latin prose corpus used before (lang/corpora/la-gutenberg.txt).
Ciphers: chained (cipher_models round-8 base without null words, nulls = 0) and round-8 with page null words.
Seeds 19 and 7. Same measure and W as copy_split_test.py.

Decision rule, fixed before the run (28 Oct 2026, this commit): candidate 2 SURVIVES if the chained cipher of the
formulaic plaintext gives ratio other/copy < 1 with both seeds (near-copies more coupled, as in Voynich) and a
near-copy share of at least 15% of words; it FAILS if the ratio is >= 1 with both seeds. Mixed seeds = undecided.

Run from the repository root: python research/voynich_siblings/copy_split_test2.py <naibbe_tables.csv> <formulaic.txt>
"""
import os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import cipher_models as cm, hybrid_model as h1, copy_split_test as cs, a4_selfcitation as a4


def main():
    rng = random.Random(113)
    zl = a4.load_zl(); skel = a4.skeleton(zl)
    prose = os.path.join(HERE, '..', '..', 'lang', 'corpora', 'la-gutenberg.txt')
    form = sys.argv[2]
    chained = dict(h1.BASE, nulls=0.0)
    rows = [('Voynich (fixed parse)', zl)]
    for seed in (19, 7):
        for pname, path in (('formulaic', form), ('prose', prose)):
            rows.append((f'chained, {pname}, s{seed}', cm.generate(cm.Variant(sys.argv[1], seed, merge=0.1, **chained), path, skel)))
            rows.append((f'chained+nulls, {pname}, s{seed}', cm.generate(cm.Variant(sys.argv[1], seed, merge=0.1, **h1.BASE), path, skel)))
    print(f'{"text":34s} {"copy share":>10s} {"copy coupling":>13s} {"other coupling":>14s} {"ratio other/copy":>16s}')
    for name, pages in rows:
        cp, nc = cs.groups(pages)
        c1, c2 = cs.coupling(cp, rng), cs.coupling(nc, rng)
        print(f'{name:34s} {len(cp) / (len(cp) + len(nc)):10.3f} {c1:13.4f} {c2:14.4f} {c2 / c1 if c1 > 0 else float("inf"):16.2f}', flush=True)


if __name__ == '__main__':
    main()
