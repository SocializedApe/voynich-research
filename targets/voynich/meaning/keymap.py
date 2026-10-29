"""Is Currier B the same system as Currier A under a different key? Search for a glyph-to-glyph mapping.

If text Y is text X's system with a substitution key changed, some one-to-one mapping of Y's units onto X's makes
their unit-pair statistics match up to sampling noise. Units: EVA glyph units (cth ckh cph cfh ch sh as one, others
single; for the controls, letters); the K = 20 commonest units of each text are mapped one to one, the rest pooled
as 'other'; word edges '#'. Distance = JSD of unit-pair distributions (word-internal pairs and edges), add-0.5.
Search: hill climbing over swaps of the mapping, 30 random restarts plus the identity start, 4,000 swaps each.
Reported: identity distance, best-mapping distance, the split-half noise floor of X, and the share of the gap to the
floor that the best mapping closes. Same size for every comparison (12,000 words each side, subsampled).

Comparisons:
  Voynich herbal A pages vs herbal B pages (same subject, other scribe)       <- the test
  Voynich herbal A first half vs second half                                <- identity should be best
  Pliny (Latin) vs the same Pliny with letters substituted by a random key  <- positive control: mapping closes all
  Latin (Pliny) vs Italian (b3 control)                                     <- related languages, no key
  Auchinleck scribe 1 vs scribe 3                                           <- dialect spelling, no key

Run from the repository root: python targets/voynich/meaning/keymap.py
"""
import collections, csv, json, math, os, random, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'glyphs')); sys.path.insert(0, os.path.join(HERE, '..'))
from variants import UNIT
import auchinleck, pliny
import a4_selfcitation as a4

K, NW = 20, 12000


def units_voy(w): return UNIT.findall(w)
def units_let(w): return list(w)


def pairs(words, split):
    c = collections.Counter()
    for w in words:
        u = ['#'] + split(w) + ['#']; c.update(zip(u, u[1:]))
    return c


def top_units(words, split):
    c = collections.Counter(u for w in words for u in split(w))
    return [u for u, _ in c.most_common(K)]


def remap(pc, mp):
    out = collections.Counter()
    for (a, b), v in pc.items():
        out[(mp.get(a, 'other' if a != '#' else '#'), mp.get(b, 'other' if b != '#' else '#'))] += v
    return out


def jsd(p, q):
    keys = set(p) | set(q); sp = sum(p.values()) + 0.5 * len(keys); sq = sum(q.values()) + 0.5 * len(keys); d = 0.0
    for k in keys:
        a = (p.get(k, 0) + 0.5) / sp; b = (q.get(k, 0) + 0.5) / sq; m = (a + b) / 2
        d += 0.5 * a * math.log2(a / m) + 0.5 * b * math.log2(b / m)
    return d


def compare(name, X, Y, split, rng, swaps=4000, restarts=30):
    X = rng.sample(X, min(NW, len(X))); Y = rng.sample(Y, min(NW, len(Y)))
    px = remap(pairs(X, split), {u: u for u in top_units(X, split)} | {'#': '#'})
    ux, uy = top_units(X, split), top_units(Y, split)
    py = pairs(Y, split)
    ident = {u: (u if u in ux else 'other') for u in uy} | {'#': '#'}
    d_id = jsd(px, remap(py, ident))
    best = (d_id, ident)
    for r in range(restarts + 1):
        tgt = ux[:] if r == 0 else rng.sample(ux, len(ux))
        mp = {u: (u if r == 0 and u in ux else tgt[i]) for i, u in enumerate(uy)}
        if r == 0: mp = {u: (u if u in ux else 'other') for u in uy}
        mp['#'] = '#'; cur = jsd(px, remap(py, mp))
        for _ in range(swaps):
            a, b = rng.sample(uy, 2)
            mp[a], mp[b] = mp[b], mp[a]
            d = jsd(px, remap(py, mp))
            if d < cur: cur = d
            else: mp[a], mp[b] = mp[b], mp[a]
        if cur < best[0]: best = (cur, dict(mp))
    h = len(X) // 2; Xs = X[:]; rng.shuffle(Xs)
    floor = jsd(remap(pairs(Xs[:h], split), {u: u for u in ux} | {'#': '#'}), remap(pairs(Xs[h:], split), {u: u for u in ux} | {'#': '#'}))
    closed = (d_id - best[0]) / (d_id - floor) if d_id > floor else float('nan')
    moved = {k: v for k, v in best[1].items() if k != '#' and k != v}
    print(f'{name:44} identity {d_id:.4f} | best mapping {best[0]:.4f} | floor {floor:.4f} | gap closed {closed:.0%} | '
          f'units remapped {len(moved)}: ' + ' '.join(f'{k}->{v}' for k, v in sorted(moved.items())[:14]), flush=True)
    return {'identity': d_id, 'best': best[0], 'floor': floor, 'closed': closed, 'mapping': best[1]}


def main():
    rng = random.Random(21)
    rows = [r for r in csv.DictReader(open(os.path.join(HERE, '..', 'data', 'ZL3b-n.fixed.words.tsv'), encoding='utf-8'), delimiter='\t')
            if r['locus_type'] == 'P' and r['illus'] == 'H']
    W = lambda lang: [w for r in rows if r['lang'] == lang for w in r['line_words'].split() if re.fullmatch(r'[a-z]+', w)]
    HA, HB = W('A'), W('B')
    out = {}
    out['voynich herbal A vs herbal B'] = compare('Voynich herbal A vs herbal B (the test)', HA, HB, units_voy, rng)
    out['voynich herbal A halves'] = compare('Voynich herbal A, half vs half', HA[:len(HA) // 2], HA[len(HA) // 2:], units_voy, rng)
    lat = [w for b in pliny.STREAM for c in pliny.chapters(b) for w in pliny.latin_words(c)]
    alpha = sorted(set(''.join(lat))); key = dict(zip(alpha, random.Random(3).sample(alpha, len(alpha))))
    sub = [''.join(key[c] for c in w) for w in lat[len(lat) // 2:]]
    out['pliny vs substituted pliny'] = compare('Pliny vs Pliny under a random letter key (+)', lat[:len(lat) // 2], sub, units_let, rng)
    ita = a4.lang_words('it', NW + 1000)
    out['latin vs italian'] = compare('Latin (Pliny) vs Italian (related, no key)', lat, ita, units_let, rng)
    items = json.load(open(os.path.join(auchinleck.RAW, 'items.json')))
    S = collections.defaultdict(list)
    for it in items:
        if it['scribe'] in (1, 3): S[it['scribe']] += auchinleck.text_of(os.path.join(auchinleck.RAW, os.path.basename(it['page'])))
    out['auchinleck 1 vs 3'] = compare('Auchinleck scribe 1 vs scribe 3 (dialects)', S[1], S[3], units_let, rng)
    json.dump(out, open(os.path.join(HERE, 'keymap_results.json'), 'w'), indent=1, default=str)


if __name__ == '__main__':
    main()
