"""Held-out test of the round-8 cipher model on the b3 battery (targets/voynich/b3_bakeoff.py: 37 scored items,
match rule fixed in advance: |value - Voynich| <= max(10% of Voynich, autocopist seed spread)).

The model was tuned on seven statistics (h2, start/end, edge coupling, hapax share, one-page share, D256, adjacent
identical). Four b3 items overlap with them (a_h2_raw, c_hapax_types, d_adj_exact, j_one_page); the other 33 are held
out. Corpora: Voynich (fixed parse), autocopist s19 and s7 (the rule's spread), Naibbe (Latin, seed 19, unmodified
rule), round-8 model seeds 19 and 7, all in the fixed-parse skeleton.

Run from the repository root: python research/voynich_siblings/model_holdout.py <naibbe_tables.csv>
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import cipher_models as cm, a4_selfcitation as a4
import b3_bakeoff as b3

TUNED = {'a_h2_raw', 'c_hapax_types', 'd_adj_exact', 'j_one_page'}
BEST = dict(chain=True, drift=True, k_page=2, p_chain=0.7, merge=0.1, sandhi=0.1, nulls=0.15, null_set=3, split=True, page_nulls=True)


def main():
    zl = a4.load_zl(); skel = a4.skeleton(zl)
    lat = os.path.join(HERE, '..', '..', 'lang', 'corpora', 'la-gutenberg.txt')
    corpora = {'voynich_ZL': zl,
               'autocopist_s19': a4.Autocopist(19).generate(skel), 'autocopist_s7': a4.Autocopist(7).generate(skel),
               'naibbe_latin': cm.generate(cm.Variant(sys.argv[1], 19), lat, skel),
               'model_s19': cm.generate(cm.Variant(sys.argv[1], 19, **BEST), lat, skel),
               'model_s7': cm.generate(cm.Variant(sys.argv[1], 7, **BEST), lat, skel)}
    extra = {}
    results = {n: b3.battery(p, n, extra) for n, p in corpora.items()}
    tol, marks = b3.score(results)
    keys = [k for k, _ in b3.ITEMS]
    held = [k for k in keys if k not in TUNED]
    print(f'{"corpus":16s} {"all 37":>7s} {"held-out " + str(len(held)):>12s}')
    for n in corpora:
        print(f'{n:16s} {sum(marks[n].values()):7d} {sum(marks[n][k] for k in held):12d}')
    print('\nitem-by-item (Voynich value, tolerance, then each corpus value; * = match)')
    for k in keys:
        row = f'{k:16s} V={results["voynich_ZL"][k]!s:>9.9} tol={tol[k]!s:>8.8}' if False else f'{k:16s} V={b3.fmt(results["voynich_ZL"][k]):>9s} tol={b3.fmt(tol[k]):>8s}'
        for n in list(corpora)[1:]:
            row += f' {n[:10]}={b3.fmt(results[n][k])}{"*" if marks[n][k] else " "}'
        print(row + ('   [tuned]' if k in TUNED else ''))


if __name__ == '__main__':
    main()
