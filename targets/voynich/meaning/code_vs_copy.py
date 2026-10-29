"""Code (nomenclator) or copying generator? Two word-level predictions that differ.

1. Spread by frequency rank. A code of a real text keeps the plaintext's function words: the commonest words spread
   evenly over pages whatever the topic, rarer words clump. Spread = pages containing the word / pages expected if its
   tokens were placed at random (sum over pages of 1 - (1 - n_p/N)^f); 1 = even, lower = clumped. Reported as the
   median spread of the words in each rank band.
2. Origin of one-off words. A nomenclator spells rare words out (letter cipher), so hapaxes need not resemble common
   words; a copy-and-modify generator makes them by editing common words. Share of hapaxes within edit distance 1 of
   a word with frequency >= 5, and mean length of hapaxes against words of frequency >= 5.

Texts as in swap.py (ZL skeleton); Voynich also restricted to Currier B pages, so the A/B vocabulary switch does not
make common words look clumped.
Run from the repository root: python targets/voynich/meaning/code_vs_copy.py
"""
import collections, os, statistics, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import swap
import a4_selfcitation as a4

BANDS = ((1, 10), (11, 50), (51, 200), (201, 1000))


def ed1(a, b):
    if a == b or abs(len(a) - len(b)) > 1: return False
    if len(a) == len(b): return sum(x != y for x, y in zip(a, b)) == 1
    if len(a) > len(b): a, b = b, a
    return any(b[:i] + b[i + 1:] == a for i in range(len(b)))


def analyse(name, pages):
    tok = [[w for ln in p['lines'] for w in ln['words']] for p in pages if p['lines']]
    N = sum(map(len, tok)); freq = collections.Counter(w for t in tok for w in t)
    per = [collections.Counter(t) for t in tok]; sizes = [len(t) for t in tok]
    ranked = [w for w, _ in freq.most_common()]
    spread = {}
    for lo, hi in BANDS:
        vals = []
        for w in ranked[lo - 1:hi]:
            f = freq[w]; exp = sum(1 - (1 - n / N) ** f for n in sizes)
            vals.append(sum(1 for c in per if c[w]) / exp)
        spread[(lo, hi)] = statistics.median(vals)
    common = [w for w, c in freq.items() if c >= 5]
    byl = collections.defaultdict(list)
    for w in common: byl[len(w)].append(w)
    hap = [w for w, c in freq.items() if c == 1]
    near = sum(1 for h in hap if any(ed1(h, w) for L in (len(h) - 1, len(h), len(h) + 1) for w in byl.get(L, ())))
    print(f'{name:22} spread by rank ' + ' '.join(f'{lo}-{hi}: {spread[(lo, hi)]:.2f}' for lo, hi in BANDS) +
          f' | hapaxes {len(hap)} ({len(hap) / len(freq):.0%} of types), within ED1 of a common word {near / len(hap):.0%};'
          f' mean length hapax {statistics.mean(map(len, hap)):.1f} vs common {statistics.mean(map(len, common)):.1f}', flush=True)


def main():
    T = swap.texts()
    zl = a4.load_zl()
    import csv
    lang = {}
    for r in csv.DictReader(open(os.path.join(HERE, '..', 'data', 'ZL3b-n.words.tsv'), encoding='utf-8'), delimiter='\t'):
        lang.setdefault(r['folio'], r['lang'])
    T['voynich_B_only'] = [p for p in zl if lang.get(p['folio']) == 'B']
    for name in ('voynich', 'voynich_B_only', 'latin', 'italian', 'naibbe', 'autocopist', 'rugg_sorted', 'voynich_shuffled_all'):
        if name in T: analyse(name, T[name])


if __name__ == '__main__':
    main()
