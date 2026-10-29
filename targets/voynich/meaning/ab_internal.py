"""Currier A/B against scribe, the unlabelled folios, and drift inside A and inside B.

Protocol, fixed before the run (28 Oct 2026). Measure throughout: glyph-pair profile (units of glyphs/variants.UNIT,
'#' at word edges), JSD with add-0.5 smoothing, as in variance.py. Cells = (Davis hand, Currier language, ZL
illustration type) from ZL3b-n.words.tsv, paragraph text only.

1. One factor at a time, with folio bootstrap. Cells with >= 500 tokens; each comparison draws 250 tokens per side
   after resampling the cell's folios with replacement (400 draws) -> mean and 95% interval. Floor = folio-level split
   half (folios of a cell split at random into two halves, 250 tokens each) over cells with >= 6 folios. Pairs grouped
   by which of hand / language / section differ.
   f58 test: hand 3's only A text is two folios (f58r, f58v). Null = every set of two hand-3 B folios from the stars
   section (3BS) against the rest of 3BS, same 250-token draws. 3AS vs 3BS counts as a real language switch inside one
   hand if it lies above the null's 99th percentile.
2. Unlabelled folios (lang '?'): JSD of the folio's profile to the A pool and the B pool (all labelled paragraph text,
   the folio itself excluded); call = nearer pool; margin = JSD(B) - JSD(A). Calibration: labelled folios truncated to
   the same token count (30, 60, 100), leave-one-out, accuracy of the same rule. Marker rates (-edy, cho, -ol, daiin)
   printed alongside.
3. Drift inside one language. Folios with >= 80 tokens; cells (hand, lang, section) with >= 8 such folios. Per cell:
   order    Spearman rho between |binding position difference| and pairwise folio JSD (Mantel); null = binding
            positions permuted within the cell (2,000 permutations). Positive rho = folios far apart in the book differ
            more = drift along the current order.
   quire    mean JSD of folio pairs in different quires minus pairs in the same quire; null = quire labels permuted
            within the cell. Positive = quires have their own profile (order-free within a quire, robust to the
            misbinding of bifolia inside a quire).
   Language-level statistics = mean over that language's cells, null permuted within each cell (stratified).
   Control: Pliny plain, leaf-wise sectioned (pliny.py), poured into the same skeleton and labelled with the same
   cells: what topic drift alone does to glyph pairs.

Run from the repository root: python targets/voynich/meaning/ab_internal.py
"""
import collections, csv, itertools, json, math, os, random, re, statistics, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'glyphs'))
from variants import UNIT
import variance
import pliny
import a4_selfcitation as a4
import b3_bakeoff as b3

TSV = os.path.join(HERE, '..', 'data', 'ZL3b-n.words.tsv')
SIZE = 250
jsd, bigrams = variance.jsd, variance.bigrams
MARK = (('-edy', lambda x: x.endswith('edy')), ('cho', lambda x: 'cho' in x), ('-ol', lambda x: x.endswith('ol')),
        ('daiin', lambda x: x == 'daiin'))


def load():
    folios = collections.OrderedDict()
    for r in csv.DictReader(open(TSV, encoding='utf-8'), delimiter='\t'):
        if r['locus_type'] != 'P':
            continue
        f = folios.setdefault(r['folio'], {'folio': r['folio'], 'hand': r['hand'], 'lang': r['lang'], 'sect': r['illus'],
                                           'quire': r['quire'], 'words': []})
        f['words'] += [w for w in r['line_words'].split() if re.fullmatch(r'[a-z]+', w)]
    for i, f in enumerate(folios.values()):
        f['pos'] = i
    return [f for f in folios.values() if f['words']]


def cell(f): return f['hand'] + f['lang'] + f['sect']


def markers(ws):
    n = len(ws)
    return {k: round((1000 if k == 'daiin' else 100) * sum(map(g, ws)) / n, 1) for k, g in MARK}


def draw(fols, rng):
    pool = [w for f in (rng.choice(fols) for _ in fols) for w in f['words']]
    while len(pool) < SIZE:
        pool += rng.choice(fols)['words']
    return rng.sample(pool, SIZE)


def part1(F, rng, N=400):
    by = collections.defaultdict(list)
    for f in F: by[cell(f)].append(f)
    cells = {c: fs for c, fs in by.items() if '?' not in c and sum(len(f['words']) for f in fs) >= 2 * SIZE}
    floor = []
    for c, fs in cells.items():
        if len(fs) < 6:
            continue
        for _ in range(40):
            s = fs[:]; rng.shuffle(s); h = len(s) // 2
            floor.append(jsd(bigrams(draw(s[:h], rng)), bigrams(draw(s[h:], rng))))
    fl = statistics.mean(floor)
    rows = []
    for a, b in itertools.combinations(sorted(cells), 2):
        v = sorted(jsd(bigrams(draw(cells[a], rng)), bigrams(draw(cells[b], rng))) for _ in range(N))
        diff = '+'.join(n for n, i in (('hand', 0), ('lang', 1), ('sect', 2)) if a[i] != b[i])
        rows.append({'a': a, 'b': b, 'differs': diff, 'mean': statistics.mean(v), 'lo': v[int(.025 * N)],
                     'hi': v[int(.975 * N) - 1], 'x_floor': statistics.mean(v) / fl})
    print(f'\n== 1. One factor at a time (folio bootstrap, {SIZE} tokens a side); folio-level floor {fl:.4f}')
    print('cells:', ', '.join(f'{c} ({len(fs)} fol, {sum(len(f["words"]) for f in fs)} tok)' for c, fs in sorted(cells.items())))
    for d in sorted({r['differs'] for r in rows}, key=lambda d: (d.count('+'), d)):
        rs = [r for r in rows if r['differs'] == d]
        print(f'  differs in {d}: mean {statistics.mean(r["x_floor"] for r in rs):.1f}x floor')
        for r in sorted(rs, key=lambda r: r['mean']):
            print(f'     {r["a"]} vs {r["b"]}  {r["mean"]:.4f} [{r["lo"]:.4f}-{r["hi"]:.4f}]  {r["x_floor"]:.1f}x')
    # f58 test
    a3 = cells['3AS']; b3s = cells['3BS']; obs = statistics.mean(jsd(bigrams(draw(a3, rng)), bigrams(draw(b3s, rng))) for _ in range(100))
    null = []
    for pair in itertools.combinations(range(len(b3s)), 2):
        two = [b3s[i] for i in pair]; rest = [f for i, f in enumerate(b3s) if i not in pair]
        null.append(statistics.mean(jsd(bigrams(draw(two, rng)), bigrams(draw(rest, rng))) for _ in range(20)))
    null.sort(); p99 = null[int(.99 * len(null)) - 1]
    print(f'  f58 test: 3AS (f58r, f58v) vs rest of 3BS {obs:.4f}; any two 3BS folios vs the rest: median '
          f'{null[len(null) // 2]:.4f}, 99th pct {p99:.4f}, max {null[-1]:.4f} ({len(null)} pairs); '
          f'share of null >= observed {sum(x >= obs for x in null) / len(null):.3f}')
    for k in ('1AH', '1AP', '3AS', '3BS', '2BH', '3BH', '5BH'):
        if k in cells: print(f'     markers {k}: {markers([w for f in cells[k] for w in f["words"]])}')
    return {'floor': fl, 'pairs': rows, 'f58': {'obs': obs, 'null_median': null[len(null) // 2], 'null_p99': p99,
                                                'null_max': null[-1], 'n_null': len(null)}}


def part2(F, rng):
    lab = [f for f in F if f['lang'] in 'AB' and f['lang']]
    unk = [f for f in F if f['lang'] not in ('A', 'B')]
    pool = {L: bigrams([w for f in lab if f['lang'] == L for w in f['words']]) for L in 'AB'}
    def call(f, ws):
        own = bigrams(f['words']) if f['lang'] in ('A', 'B') else None
        d = {}
        for L in 'AB':
            p = pool[L].copy()
            if own is not None and f['lang'] == L: p.subtract(own); p = +p
            d[L] = jsd(bigrams(ws), p)
        return d
    print('\n== 2. Unlabelled folios: nearer of the A and B pools')
    cal = {}
    for n in (30, 60, 100):
        ok = tot = 0
        for f in lab:
            if len(f['words']) < n: continue
            for _ in range(3):
                s = f['words'][:] if len(f['words']) == n else rng.sample(f['words'], n)
                d = call(f, s); ok += (min(d, key=d.get) == f['lang']); tot += 1
        cal[n] = ok / tot
        print(f'  calibration, labelled folios cut to {n} tokens: {100 * ok / tot:.1f}% correct ({tot} draws)')
    out = []
    for f in unk:
        d = call(f, f['words']); c = min(d, key=d.get)
        out.append({'folio': f['folio'], 'hand': f['hand'], 'sect': f['sect'], 'quire': f['quire'], 'tokens': len(f['words']),
                    'jsd_A': d['A'], 'jsd_B': d['B'], 'call': c, 'markers': markers(f['words'])})
        print(f'  {f["folio"]:7} hand {f["hand"]} sect {f["sect"]} quire {f["quire"]} {len(f["words"]):4} tok  JSD A {d["A"]:.3f} '
              f'B {d["B"]:.3f} -> {c}  {markers(f["words"])}')
    for h in sorted({r['hand'] for r in out}):
        rs = [r for r in out if r['hand'] == h]; ws = [w for f in unk if f['hand'] == h for w in f['words']]
        d = call({'lang': '?', 'words': ws}, ws)
        print(f'  pooled hand {h} unlabelled ({len(ws)} tok): JSD A {d["A"]:.3f} B {d["B"]:.3f} -> {min(d, key=d.get)}; '
              f'folio calls {collections.Counter(r["call"] for r in rs)}; markers {markers(ws)}')
    return {'calibration': cal, 'folios': out}


def spearman(x, y):
    def rank(v):
        o = sorted(range(len(v)), key=v.__getitem__); r = [0] * len(v); i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]: j += 1
            for k in range(i, j + 1): r[o[k]] = (i + j) / 2
            i = j + 1
        return r
    rx, ry = rank(x), rank(y); mx, my = statistics.mean(rx), statistics.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    return num / math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))


def part3(name, F, rng, P=2000):
    by = collections.defaultdict(list)
    for f in F:
        if len(f['words']) >= 80 and f['lang'] in ('A', 'B'): by[cell(f)].append(f)
    cells = {c: fs for c, fs in sorted(by.items()) if len(fs) >= 8}
    prep = {}
    for c, fs in cells.items():
        prof = [bigrams(f['words']) for f in fs]
        pairs = list(itertools.combinations(range(len(fs)), 2))
        prep[c] = (fs, pairs, [jsd(prof[i], prof[j]) for i, j in pairs])
    def stats(c, pos, qu):
        fs, pairs, d = prep[c]
        rho = spearman([abs(pos[i] - pos[j]) for i, j in pairs], d)
        same = [x for (i, j), x in zip(pairs, d) if qu[i] == qu[j]]; diff = [x for (i, j), x in zip(pairs, d) if qu[i] != qu[j]]
        q = statistics.mean(diff) - statistics.mean(same) if same and diff else float('nan')
        return rho, q
    obs = {c: stats(c, [f['pos'] for f in fs], [f['quire'] for f in fs]) for c, (fs, _, _) in prep.items()}
    nulls = {c: [] for c in prep}
    for _ in range(P):
        for c, (fs, _, _) in prep.items():
            pos = [f['pos'] for f in fs]; qu = [f['quire'] for f in fs]; rng.shuffle(pos); rng.shuffle(qu)
            nulls[c].append(stats(c, pos, qu))
    print(f'\n== 3. Drift inside one language: {name}')
    res = {}
    for c in prep:
        fs = prep[c][0]; o = obs[c]; nr = [x[0] for x in nulls[c]]; nq = [x[1] for x in nulls[c] if x[1] == x[1]]
        pr = (1 + sum(x >= o[0] for x in nr)) / (P + 1); pq = (1 + sum(x >= o[1] for x in nq)) / (len(nq) + 1) if nq else float('nan')
        res[c] = {'folios': len(fs), 'quires': len({f['quire'] for f in fs}), 'rho': o[0], 'p_order': pr,
                  'quire_excess': o[1], 'p_quire': pq}
        print(f'  {c}: {len(fs)} folios in {res[c]["quires"]} quires  order rho {o[0]:+.3f} (p {pr:.4f})  '
              f'quire excess {o[1]:+.4f} (p {pq:.4f})')
    for L in 'AB':
        cs = [c for c in prep if c[1] == L]
        if not cs: continue
        mo = statistics.mean(obs[c][0] for c in cs); mq = statistics.mean(obs[c][1] for c in cs if obs[c][1] == obs[c][1])
        nr = [statistics.mean(nulls[c][k][0] for c in cs) for k in range(P)]
        nq = [statistics.mean(nulls[c][k][1] for c in cs if nulls[c][k][1] == nulls[c][k][1]) for k in range(P)]
        pr = (1 + sum(x >= mo for x in nr)) / (P + 1); pq = (1 + sum(x >= mq for x in nq)) / (P + 1)
        res['lang_' + L] = {'cells': cs, 'rho': mo, 'p_order': pr, 'quire_excess': mq, 'p_quire': pq}
        print(f'  language {L} ({", ".join(cs)}): mean rho {mo:+.3f} (p {pr:.4f}); mean quire excess {mq:+.4f} (p {pq:.4f})')
    return res


def pliny_folios(F):
    zl = b3.load_zl_lang(); skel = a4.skeleton(zl)
    groups, sections = pliny.leaves_of(zl)
    plain = pliny.pour_pages(pliny.sectioned_words(zl, skel, groups, sections), skel)
    byf = {p['folio']: b3.words_of([q]) for p, q in zip(zl, plain)}
    return [dict(f, words=byf.get(f['folio'], [])) for f in F]


def main():
    F = load(); rng = random.Random(58)
    out = {'part1': part1(F, rng), 'part2': part2(F, rng)}
    out['part3'] = {'voynich': part3('Voynich', F, rng)}
    out['part3']['voynich_shuffled'] = part3('Voynich, words shuffled within each cell (sanity: no drift)',
                                             shuffled(F, rng), rng)
    out['part3']['pliny'] = part3('Pliny plain, leaf-wise sectioned, same skeleton and cells', pliny_folios(F), rng)
    json.dump(out, open(os.path.join(HERE, 'ab_internal_results.json'), 'w'), indent=1, default=str)


def shuffled(F, rng):
    by = collections.defaultdict(list)
    for f in F: by[cell(f)].append(f)
    out = []
    for c, fs in by.items():
        pool = [w for f in fs for w in f['words']]; rng.shuffle(pool); it = iter(pool)
        out += [dict(f, words=[next(it) for _ in f['words']]) for f in fs]
    return sorted(out, key=lambda f: f['pos'])


if __name__ == '__main__':
    main()
