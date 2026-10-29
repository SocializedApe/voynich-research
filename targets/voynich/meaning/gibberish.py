"""Control: how different are two people writing improvised gibberish, against Voynich's scribes and real scribes?

Gibberish: Gaskell & Bowern (2022, CEUR 3313 paper 4), 38 volunteer texts (github.com/danielgaskell/voynich,
data/gibberish_transcriptions.zip, fetched 28 Oct 2026 into data/gaskell_bowern). Each volunteer = one 'scribe';
volunteers with at least 200 words are used. Voynich: Davis hands 1, 2, 3 (paragraph text, ZL fixed parse).
Auchinleck: scribes 1, 2, 3, 5 (auchinleck.py).
Measure, the same for all three at one size (100 words a side, subsampled): JSD of unit-pair distributions (Voynich
glyph units, letters elsewhere; '#' at word edges) between two different scribes, and between two disjoint halves of
one scribe (the within-scribe floor); ratio = mean between / mean within. 200 draws per kind.

Run from the repository root: python targets/voynich/meaning/gibberish.py
"""
import collections, csv, json, os, random, re, statistics, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'glyphs'))
from variants import UNIT
from variance import jsd
import auchinleck

SIZE, DRAWS = 100, 200


def pairs(words, split):
    c = collections.Counter()
    for w in words:
        u = ['#'] + split(w) + ['#']; c.update(zip(u, u[1:]))
    return c


def ratio(name, groups, split, rng):
    keys = [k for k, ws in groups.items() if len(ws) >= 2 * SIZE]
    between, within = [], []
    for _ in range(DRAWS):
        a, b = rng.sample(keys, 2)
        between.append(jsd(pairs(rng.sample(groups[a], SIZE), split), pairs(rng.sample(groups[b], SIZE), split)))
        c = rng.choice(keys); ws = rng.sample(groups[c], 2 * SIZE)
        within.append(jsd(pairs(ws[:SIZE], split), pairs(ws[SIZE:], split)))
    r = statistics.mean(between) / statistics.mean(within)
    print(f'{name:40} scribes {len(keys):2} | between {statistics.mean(between):.4f} | within {statistics.mean(within):.4f} | ratio {r:.2f}', flush=True)
    return r


def main():
    rng = random.Random(13)
    z = zipfile.ZipFile(os.path.join(HERE, 'data', 'gaskell_bowern', 'gibberish_transcriptions.zip'))
    gib = {n: re.findall(r'[a-z]+', z.read(n).decode('utf-8', 'replace').lower()) for n in z.namelist() if not n.endswith('/')}
    voy = collections.defaultdict(list)
    for r in csv.DictReader(open(os.path.join(HERE, '..', 'data', 'ZL3b-n.fixed.words.tsv'), encoding='utf-8'), delimiter='\t'):
        if r['locus_type'] == 'P' and r['hand'] in ('1', '2', '3'):
            voy[r['hand']] += [w for w in r['line_words'].split() if re.fullmatch(r'[a-z]+', w)]
    au = collections.defaultdict(list)
    for it in json.load(open(os.path.join(auchinleck.RAW, 'items.json'))):
        if it['scribe']: au[it['scribe']] += auchinleck.text_of(os.path.join(auchinleck.RAW, os.path.basename(it['page'])))
    out = {'voynich hands 1-3': ratio('Voynich, Davis hands 1-3', voy, UNIT.findall, rng),
           'auchinleck scribes': ratio('Auchinleck, scribes 1, 2, 3, 5', au, list, rng),
           'gibberish volunteers': ratio('Gibberish, one volunteer = one scribe', gib, list, rng)}
    json.dump(out, open(os.path.join(HERE, 'gibberish_results.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
