"""Length coupling between the slots of a word: is there a length budget, and what conditioning does a chained
generator need to make words of the right shape? (10 Nov 2026, second session)

Every fitted generator so far makes words too dispersed in length (slots5: sd 2.6-2.9 glyphs against 1.8; 9-14% of
words of nine or more glyphs against 2.4%). Two possible causes: (a) the slots are coupled in length beyond what the
last-unit chain carries (a long opener is followed by a short middle: a budget), or (b) the chain is enough and the
excess comes from the invented middles of the template and from the reinforcement.

Part 1 (measure). Word = opener | middle | ending (slots4.split3), lengths in glyph units (common.units). Pearson
correlations between slot lengths; variance of the word length against the sum of the slot variances (ratio < 1 =
compensation); the same within chain-context cells (middle length against opener length among words whose opener
ends in the same unit; ending length against opener + middle length among words with the same last unit before the
ending), as a tokens-weighted mean of within-cell correlations. Voynich whole, Currier A, Currier B. Controls
that are written in the same glyphs and so take the same parse: the Naibbe cipher of Pliny and the autocopist.

Part 2 (resampling nulls; no fitting, no location, no template). The opener of every token is kept; the middle and
then the ending are redrawn from the empirical book-wide distribution given a conditioning key, sequentially (the
ending's key is computed from the redrawn middle). Five resamples each. Keys:
  N0 independent      middle | nothing;                 ending | nothing                       (slots4's assumption)
  N1 chain            middle | last unit of opener;     ending | last unit of opener + middle  (slots5's assumption)
  N2 chain + length   middle | last unit, opener length (0, 1, 2, 3+); ending | last unit, length so far (0-1, 2, 3, 4, 5+)
  N3 whole opener     middle | whole opener;            ending | last unit of opener + middle
  N4 whole stem       middle | whole opener;            ending | whole middle and whether the opener is empty
  N5 order 2          middle | last two units of opener; ending | last two units of opener + middle
A key never seen with the redrawn stem backs off to the N1 key. Reported per null: mean and sd of word length in
glyph units and in EVA characters, share of words of 9+ characters, share of tokens that are Voynich word types,
types per token, and the correlations of part 1. The conditioning that reproduces Voynich's sd and its share of real
words says what a chained generator has to know; if N1 already does, the generators' excess is not a missing length
coupling.

Run from targets/voynich: python reinforce/lengths.py  -> reinforce/lengths_results.json, lengths.md
"""
import collections, json, math, os, random, statistics, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..')
sys.path.insert(0, HERE); sys.path.insert(0, VOY); sys.path.insert(0, os.path.join(VOY, 'lines')); sys.path.insert(0, os.path.join(VOY, 'meaning'))
sys.path.insert(0, os.path.join(VOY, '..', '..', 'research', 'voynich_siblings'))
import common, slots4
from slots import EMPTY


def S(x):
    return '' if x == EMPTY else x


def U(x):
    return common.units(x) if x else []


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n; my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs); syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(sxx * syy)


def within(cells):
    """tokens-weighted mean of within-cell Pearson correlations; cells: key -> (xs, ys)"""
    num = 0.0; den = 0
    for xs, ys in cells.values():
        if len(xs) >= 30:
            r = pearson(xs, ys)
            if r is not None:
                num += r * len(xs); den += len(xs)
    return num / den if den else None


def measure(triples, voc=None):
    """triples: list of (opener, middle, ending) strings ('' for empty)"""
    lo = [len(U(o)) for o, m, e in triples]; lm = [len(U(m)) for o, m, e in triples]; le = [len(U(e)) for o, m, e in triples]
    L = [a + b + c for a, b, c in zip(lo, lm, le)]
    words = [(o + m + e) or 'o' for o, m, e in triples]; chars = [len(w) for w in words]
    c1 = collections.defaultdict(lambda: ([], [])); c2 = collections.defaultdict(lambda: ([], []))
    for (o, m, e), a, b, c in zip(triples, lo, lm, le):
        k = U(o)[-1] if o else '^'; c1[k][0].append(a); c1[k][1].append(b)
        k = U(o + m)[-1] if o + m else '^'; c2[k][0].append(a + b); c2[k][1].append(c)
    out = dict(n=len(triples), mean_units=statistics.mean(L), sd_units=statistics.pstdev(L), mean_chars=statistics.mean(chars),
               sd_chars=statistics.pstdev(chars), share_9plus_chars=sum(1 for x in chars if x >= 9) / len(chars),
               share_le2_chars=sum(1 for x in chars if x <= 2) / len(chars),
               r_opener_middle=pearson(lo, lm), r_stem_ending=pearson([a + b for a, b in zip(lo, lm)], le), r_opener_ending=pearson(lo, le),
               var_ratio=statistics.pvariance(L) / (statistics.pvariance(lo) + statistics.pvariance(lm) + statistics.pvariance(le)),
               r_opener_middle_within_ctx=within(c1), r_stem_ending_within_ctx=within(c2),
               types_per_token=len(set(words)) / len(words))
    if voc is not None:
        out['voynich_types_share'] = sum(1 for w in words if w in voc) / len(words)
    return out


def lu(s):
    return U(s)[-1] if s else '^'


def lu2(s):
    u = U(s)
    return '|'.join(u[-2:]) if u else '^'


KEYS = collections.OrderedDict([
    ('N0 independent', (lambda o: 0, lambda o, m: 0)),
    ('N1 chain', (lambda o: lu(o), lambda o, m: lu(o + m))),
    ('N2 chain + length', (lambda o: (lu(o), min(len(U(o)), 3)), lambda o, m: (lu(o + m), min(max(len(U(o + m)), 1), 5)))),
    ('N3 whole opener', (lambda o: o, lambda o, m: lu(o + m))),
    ('N4 whole stem', (lambda o: o, lambda o, m: (m, o == ''))),
    ('N5 order 2', (lambda o: lu2(o), lambda o, m: lu2(o + m)))])


def resample(triples, km, ke, rng):
    Tm = collections.defaultdict(list); Te = collections.defaultdict(list); Bm = collections.defaultdict(list); Be = collections.defaultdict(list)
    for o, m, e in triples:
        Tm[km(o)].append(m); Te[ke(o, m)].append(e); Bm[lu(o)].append(m); Be[lu(o + m)].append(e)
    out = []; backoff = 0
    for o, _, _ in triples:
        m = rng.choice(Tm[km(o)])
        k = ke(o, m)
        if k in Te:
            e = rng.choice(Te[k])
        else:
            e = rng.choice(Be[lu(o + m)]); backoff += 1
        out.append((o, m, e))
    return out, backoff / len(triples)


def main():
    t0 = time.time(); ref = common.pages()
    def trip(pgs):
        return [tuple(S(x) for x in slots4.split3(w)) for p in pgs for ln in p['lines'] for w in ln['words']]
    allt = trip(ref); voc = {(o + m + e) or 'o' for o, m, e in allt}
    res = collections.OrderedDict()
    res['measure'] = collections.OrderedDict([('Voynich', measure(allt, voc)), ('Currier A', measure(trip([p for p in ref if p['lang'] == 'A']), voc)),
                                              ('Currier B', measure(trip([p for p in ref if p['lang'] == 'B']), voc))])
    for name, pgs in common.controls(ref, which=('naibbe', 'autocopist_s19', 'autocopist_s7')).items():
        res['measure'][name + ' (same parse)'] = measure(trip(pgs), voc)
    res['nulls'] = collections.OrderedDict()
    for name, (km, ke) in KEYS.items():
        runs = []
        for seed in range(5):
            t, bo = resample(allt, km, ke, random.Random(seed)); r = measure(t, voc); r['backoff'] = bo; runs.append(r)
        res['nulls'][name] = {k: statistics.mean(r[k] for r in runs) for k in runs[0] if runs[0][k] is not None}
        res['nulls'][name]['sd_units_range'] = [min(r['sd_units'] for r in runs), max(r['sd_units'] for r in runs)]
        print(name, f"sd units {res['nulls'][name]['sd_units']:.2f} chars {res['nulls'][name]['sd_chars']:.2f} 9+ {res['nulls'][name]['share_9plus_chars']:.3f} "
              f"voy {res['nulls'][name]['voynich_types_share']:.2f}", flush=True)
    json.dump(res, open(os.path.join(HERE, 'lengths_results.json'), 'w'), indent=1)
    cols = [('mean_units', 'mean (units)'), ('sd_units', 'sd (units)'), ('mean_chars', 'mean (chars)'), ('sd_chars', 'sd (chars)'), ('share_9plus_chars', '9+ chars'),
            ('share_le2_chars', '<= 2 chars'), ('voynich_types_share', 'Voynich types'), ('types_per_token', 'types/token'), ('r_opener_middle', 'r opener, middle'),
            ('r_stem_ending', 'r stem, ending'), ('var_ratio', 'var ratio'), ('r_opener_middle_within_ctx', 'r o,m within ctx'), ('r_stem_ending_within_ctx', 'r stem,e within ctx')]
    L = ['# Length coupling between slots, and what a chain has to know (10 Nov 2026)', '', 'Script `lengths.py` (protocol in its docstring). Lengths in glyph units unless marked.', '']
    L.append('| text | ' + ' | '.join(c for _, c in cols) + ' |'); L.append('|---|' + '---|' * len(cols))
    f = lambda v: '-' if v is None else f'{v:.3f}'
    for name, r in list(res['measure'].items()) + list(res['nulls'].items()):
        L.append(f'| {name} | ' + ' | '.join(f(r.get(k)) for k, _ in cols) + ' |')
    L.append(''); L.append('Back-off share (ending key unseen with the redrawn stem): ' + ', '.join(f"{n} {r['backoff']:.3f}" for n, r in res['nulls'].items()))
    L.append(''); L.append(f'Runtime {time.time() - t0:.0f} s.')
    open(os.path.join(HERE, 'lengths.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    main()
