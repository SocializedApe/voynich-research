"""Control for variance.py: how big are scribe and text effects in a real multi-scribe manuscript?

The Auchinleck manuscript (Edinburgh, NLS Adv. MS 19.2.1, c. 1331-40), Middle English verse copied by six scribes
whose spellings are dialectally distinct (LALME: Middlesex, London, Essex, Gloucestershire/Worcestershire).
Text: the NLS diplomatic edition (auchinleck.nls.uk, ed. Alison Wiggins, 2003), pages fetched 28 Oct 2026 into
data/auchinleck_raw. Scribe of each item from the NLS catalogue: scribe 1 items 1-9, 11-13, 22-3, 26-31, 33-43;
scribe 2 items 10, 20, 44; scribe 3 items 14-19; scribe 5 items 24-25 (scribe 4, a list of names, and scribe 6,
whose item is not confirmed here, are left out).
Cleaning: editorial note layers, line numbers, supplied text in [...] and parentheses removed; letters kept as written
(thorn, yogh, '&' as a word); lowercase. Pages = chunks of 170 words in reading order (the size of a Voynich page),
labelled by scribe and item.
Analysis = variance.py on letter pairs: cells (scribe, item) with >= 800 words, 400-word subsamples, JSD by kind
(same scribe other item, other scribe, noise floor), per-page heterogeneity within cells.

Run from the repository root: python targets/voynich/meaning/auchinleck.py
"""
import collections, html, itertools, json, os, random, re, statistics, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from variance import jsd

RAW = os.path.join(HERE, 'data', 'auchinleck_raw')
SIZE, CHUNK = 400, 170
LETTER = re.compile(r"[a-zþȝðæ&]+")


def text_of(path):
    t = open(path, encoding='utf-8', errors='replace').read()
    t = re.sub(r'<div id="myLayer\d+"[^>]*>.*?</div>', ' ', t, flags=re.S)          # editorial note layers
    t = re.sub(r'<font[^>]*>.*?</font>', ' ', t, flags=re.S)                         # line-number spacers, folio marks
    t = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', t, flags=re.S)
    k = t.find('<div class="divvy50"'); body = t[k:] if k >= 0 else t
    s = html.unescape(re.sub(r'<[^>]+>', '\n', body))
    s = re.sub(r'\[[^\]]*\]|\([^)]*\)', ' ', s)                                       # supplied and editorial text
    s = re.sub(r'\d+', ' ', s).replace('¶', ' ').lower()
    return LETTER.findall(s)


def bigrams(words):
    c = collections.Counter()
    for w in words:
        u = ['#'] + list(w) + ['#']; c.update(zip(u, u[1:]))
    return c


def main():
    items = json.load(open(os.path.join(RAW, 'items.json')))
    pages, cells = [], []
    for it in items:
        if not it['scribe']: continue
        ws = text_of(os.path.join(RAW, os.path.basename(it['page'])))
        for k in range(0, len(ws) - CHUNK + 1, CHUNK):
            pages.append(ws[k:k + CHUNK]); cells.append((it['scribe'], it['item']))
    print('words by scribe:', dict(collections.Counter(s for (s, _), p in zip(cells, pages) for _ in p)))
    print('sample:', ' '.join(pages[0][:25]))
    rng = random.Random(9)
    byc = collections.defaultdict(list)
    for i, c in enumerate(cells): byc[c].append(i)
    big = {c: idx for c, idx in byc.items() if len(idx) * CHUNK >= 2 * SIZE and len(idx) >= 4}
    sample = lambda idx: rng.sample([w for i in idx for w in pages[i]], SIZE)
    kinds = collections.defaultdict(list)
    for a, b in itertools.combinations(sorted(big), 2):
        k = 'same scribe, other text' if a[0] == b[0] else 'other scribe'
        kinds[k].append(statistics.mean(jsd(bigrams(sample(big[a])), bigrams(sample(big[b]))) for _ in range(3)))
    floor = []
    for c, idx in big.items():
        for _ in range(3):
            ws = [w for i in idx for w in pages[i]]; rng.shuffle(ws)
            floor.append(jsd(bigrams(ws[:SIZE]), bigrams(ws[SIZE:2 * SIZE])))
    fl = statistics.mean(floor)
    print(f'\n{len(big)} cells (scribe, item) with >= {2 * SIZE} words, by scribe: {collections.Counter(c[0] for c in big)}')
    print(f'  noise floor (split half)    JSD {fl:.4f} (n {len(floor)})')
    for k, v in sorted(kinds.items()):
        print(f'  {k:27} JSD {statistics.mean(v):.4f} (n {len(v)}) = {statistics.mean(v) / fl:.2f} x floor')
    by_pair = collections.defaultdict(list)
    for a, b in itertools.combinations(sorted(big), 2):
        if a[0] != b[0]: by_pair[tuple(sorted((a[0], b[0])))].append(None)
    ratios = []
    for c, idx in big.items():
        def het(wp):
            tot = bigrams([w for ws in wp for w in ws]); vals = []
            for ws in wp:
                b = bigrams(ws); rest = tot.copy(); rest.subtract(b); vals.append(jsd(b, +rest))
            return statistics.mean(vals)
        obs = het([pages[i] for i in idx]); null = []
        for _ in range(20):
            pool = [w for i in idx for w in pages[i]]; rng.shuffle(pool); itr = iter(pool)
            null.append(het([[next(itr) for _ in pages[i]] for i in idx]))
        ratios.append(obs / statistics.mean(null))
    print(f'  per-page heterogeneity (observed / shuffled within cell): median {statistics.median(ratios):.2f}, '
          f'range {min(ratios):.2f}-{max(ratios):.2f} over {len(ratios)} cells')


if __name__ == '__main__':
    main()
