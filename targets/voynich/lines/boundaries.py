"""Line boundaries: does the text flow across them, and is the word-boundary rule one for the whole book? (10 Nov 2026)

Four questions, all on glyph units (ch sh cth ckh cph cfh one unit, other EVA letters single; '#' = word edge):

1. Edge coupling across line breaks. cipher_models.md found that the last unit of a word predicts the first unit of
   the next (edge coupling 0.054, Naibbe 0.002), one rule for the whole book. Here the same dependence is measured
   for three kinds of adjacent pair: within a line (interior pairs), across a line break (last word of line n ->
   first word of line n + 1), and across a line break skipping the line-initial word (last word of line n -> second
   word of line n + 1), plus across a paragraph break. X = [MI(last unit; first unit) - shuffle baseline] / H(first
   unit); baseline = mean over 10 shuffles of the second member among pairs of the same kind. Running text written
   out continuously carries the dependence over the break; a line-by-line generator or a cipher whose state resets
   at the line drops it.
2. Lag structure within lines: the same for pairs (w_t, w_t+k), k = 1, 2, 3, interior words only. An interleaving of
   two streams (every other word from another source) gives lag 2 > lag 1.
3. Position in line: Jensen-Shannon divergence (bits) between the first-unit distribution of words at index i
   (i = 1..8 from the left, and -1..-3 from the right) and the pooled interior distribution; the same for word
   length (mean). Nulls: words shuffled within the line (20 shuffles) give the sampling floor for each cell.
4. One boundary rule? The edge-coupling matrix (PMI of last unit -> first unit over the 12 commonest units each way)
   is computed for Currier A and B, and for hands 1, 2, 3, on random halves of each group. Similarity = Pearson
   correlation of PMI entries with >= 20 expected pairs. Between-group similarity against within-group split-half
   similarity (10 random splits): a book-wide rule gives between ~ within; a convention that differs by group gives
   between < within.

Controls poured into the ZL skeleton: Latin and English (running prose), the Naibbe cipher, the autocopist (two
seeds), the gibberish volunteers; and Voynich with its lines shuffled within each page (breaks the line order but
not the lines). Run from targets/voynich: python lines/boundaries.py -> lines/boundaries_results.json, boundaries.md
"""
import collections, itertools, json, math, os, random, statistics, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import common

U = common.units


def H(c):
    n = sum(c.values()); return -sum(v / n * math.log2(v / n) for v in c.values() if v)


def mi(pairs):
    return H(collections.Counter(a for a, _ in pairs)) + H(collections.Counter(b for _, b in pairs)) - H(collections.Counter(pairs))


def coupling(pairs, rng, reps=10):
    """normalised excess MI of (last unit of a, first unit of b) over shuffled b"""
    if len(pairs) < 50:
        return None
    ab = [(U(a)[-1], U(b)[0]) for a, b in pairs]
    obs = mi(ab); bs = [x for x, _ in ab]; ys = [y for _, y in ab]
    base = []
    for _ in range(reps):
        rng.shuffle(ys); base.append(mi(list(zip(bs, ys))))
    return dict(n=len(ab), X=(obs - statistics.mean(base)) / H(collections.Counter(ys)))


def pair_kinds(pgs):
    K = collections.defaultdict(list)
    for p in pgs:
        L = p['lines']
        for n, ln in enumerate(L):
            ws = ln['words']
            for i in range(1, len(ws) - 2):          # interior pairs: neither member line-first or line-last
                K['within'].append((ws[i], ws[i + 1]))
            for i in range(1, len(ws) - 3):
                K['within_lag2'].append((ws[i], ws[i + 2]))
            for i in range(1, len(ws) - 4):
                K['within_lag3'].append((ws[i], ws[i + 3]))
            if n + 1 < len(L):
                nx = L[n + 1]['words']
                kind = 'para_break' if L[n + 1]['para_start'] else 'line_break'
                K[kind].append((ws[-1], nx[0]))
                if len(nx) >= 2:
                    K[kind + '_skip1'].append((ws[-1], nx[1]))
            # line-first -> second word, for reference
            if len(ws) >= 3:
                K['first_to_second'].append((ws[0], ws[1]))
    return K


def position_profile(pgs, rng, reps=20):
    def cells(pp):
        first = collections.defaultdict(collections.Counter); length = collections.defaultdict(list)
        pool = collections.Counter(); plen = []
        for p in pp:
            for ln in p['lines']:
                ws = ln['words']
                if len(ws) < 6:
                    continue
                for i, w in enumerate(ws):
                    key = i + 1 if i < 8 else None
                    if key is not None:
                        first[key][U(w)[0]] += 1; length[key].append(len(w))
                    j = i - len(ws)
                    if j >= -3:
                        first[j][U(w)[0]] += 1; length[j].append(len(w))
                    if 2 <= i <= len(ws) - 3:
                        pool[U(w)[0]] += 1; plen.append(len(w))
        return first, length, pool, plen
    first, length, pool, plen = cells(pgs)
    keys = [1, 2, 3, 4, 5, 6, 7, 8, -3, -2, -1]
    obs = {k: dict(jsd=common_jsd(first[k], pool), len=statistics.mean(length[k])) for k in keys if sum(first[k].values()) >= 100}
    null = collections.defaultdict(lambda: collections.defaultdict(list))
    for s in range(reps):
        f2, l2, p2, pl2 = cells(common.shuffle_within_line(pgs, seed=100 * s + 3))
        for k in obs:
            null[k]['jsd'].append(common_jsd(f2[k], p2)); null[k]['len'].append(statistics.mean(l2[k]))
    out = {}
    for k in obs:
        out[str(k)] = dict(n=sum(first[k].values()), jsd=obs[k]['jsd'], jsd_null=statistics.mean(null[k]['jsd']),
                           len=obs[k]['len'], len_null=statistics.mean(null[k]['len']), len_pool=statistics.mean(plen))
    return out


def common_jsd(p, q):
    keys = set(p) | set(q); sp = sum(p.values()) + 0.5 * len(keys); sq = sum(q.values()) + 0.5 * len(keys); d = 0.0
    for k in keys:
        a = (p.get(k, 0) + 0.5) / sp; b = (q.get(k, 0) + 0.5) / sq; m = (a + b) / 2
        d += 0.5 * a * math.log2(a / m) + 0.5 * b * math.log2(b / m)
    return d


def pmi_matrix(pairs, rows, cols):
    c = collections.Counter((U(a)[-1], U(b)[0]) for a, b in pairs)
    n = sum(c.values()); ra = collections.Counter(); cb = collections.Counter()
    for (x, y), v in c.items():
        ra[x] += v; cb[y] += v
    M = {}
    for x in rows:
        for y in cols:
            e = ra[x] * cb[y] / n if n else 0
            if e >= 20:
                M[(x, y)] = math.log2((c[(x, y)] + 0.5) / (e + 0.5))
    return M


def corr(M1, M2):
    ks = [k for k in M1 if k in M2]
    if len(ks) < 10:
        return None
    a = [M1[k] for k in ks]; b = [M2[k] for k in ks]
    ma, mb = statistics.mean(a), statistics.mean(b)
    sa = math.sqrt(sum((x - ma) ** 2 for x in a)); sb = math.sqrt(sum((x - mb) ** 2 for x in b))
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb) if sa and sb else None


def rule_similarity(pgs, groups, rng, splits=10):
    """groups: dict name -> list of pages. Within-line adjacent pairs (all positions)."""
    allpairs = {g: [(ws[i], ws[i + 1]) for p in pp for ln in p['lines'] for ws in [ln['words']] for i in range(len(ws) - 1)] for g, pp in groups.items()}
    lastc = collections.Counter(U(a)[-1] for ps in allpairs.values() for a, _ in ps)
    firstc = collections.Counter(U(b)[0] for ps in allpairs.values() for _, b in ps)
    rows = [u for u, _ in lastc.most_common(12)]; cols = [u for u, _ in firstc.most_common(12)]
    n = min(len(ps) for ps in allpairs.values())
    out = {'n_pairs_per_half': n // 2}
    within = {}
    for g, ps in allpairs.items():
        vals = []
        for s in range(splits):
            x = ps[:]; rng.shuffle(x); x = x[:n]
            r = corr(pmi_matrix(x[:n // 2], rows, cols), pmi_matrix(x[n // 2:], rows, cols))
            if r is not None:
                vals.append(r)
        within[g] = statistics.mean(vals) if vals else None
    out['within'] = within
    between = {}
    for g1, g2 in itertools.combinations(allpairs, 2):
        vals = []
        for s in range(splits):
            x = allpairs[g1][:]; y = allpairs[g2][:]; rng.shuffle(x); rng.shuffle(y)
            r = corr(pmi_matrix(x[:n // 2], rows, cols), pmi_matrix(y[:n // 2], rows, cols))
            if r is not None:
                vals.append(r)
        between[f'{g1} vs {g2}'] = statistics.mean(vals) if vals else None
    out['between'] = between
    return out


def analyse(name, pgs, rng):
    R = {}
    K = pair_kinds(pgs)
    R['coupling'] = {k: coupling(v, rng) for k, v in K.items()}
    R['position'] = position_profile(pgs, rng)
    return R


def main():
    t0 = time.time(); rng = random.Random(23)
    voy = common.pages()
    texts = collections.OrderedDict(voynich=voy)
    texts['voynich_A'] = [p for p in voy if p['lang'] == 'A']
    texts['voynich_B'] = [p for p in voy if p['lang'] == 'B']
    texts['voynich_lines_shuffled'] = common.shuffle_lines_within_page(voy)
    texts.update(common.controls(voy))
    results = collections.OrderedDict()
    for name, pgs in texts.items():
        results[name] = analyse(name, pgs, rng); print(name, 'done', f'{time.time() - t0:.0f}s', flush=True)
    groups = {'A': texts['voynich_A'], 'B': texts['voynich_B']}
    results['rule_similarity_AB'] = rule_similarity(voy, groups, rng)
    groups = {f'hand{h}': [p for p in voy if p['hand'] == h] for h in ('1', '2', '3')}
    results['rule_similarity_hands'] = rule_similarity(voy, groups, rng)
    # control: the Naibbe cipher split into two arbitrary halves of pages should give between ~ within
    if 'naibbe' in texts:
        nb = texts['naibbe']; h = len(nb) // 2
        results['rule_similarity_naibbe_halves'] = rule_similarity(nb, {'first': nb[:h], 'second': nb[h:]}, rng)
    if 'latin' in texts:
        la = texts['latin']; h = len(la) // 2
        results['rule_similarity_latin_halves'] = rule_similarity(la, {'first': la[:h], 'second': la[h:]}, rng)
    json.dump(results, open(os.path.join(HERE, 'boundaries_results.json'), 'w'), indent=1)

    L = ['# Line boundaries, lag structure, position in line, one boundary rule? (10 Nov 2026)', '',
         'Script `boundaries.py` (docstring has the definitions).', '', '## 1-2. Edge coupling X by pair kind (n pairs)', '']
    kinds = ['within', 'within_lag2', 'within_lag3', 'line_break', 'line_break_skip1', 'para_break', 'para_break_skip1', 'first_to_second']
    L.append('| text | ' + ' | '.join(kinds) + ' |'); L.append('|---|' + '---|' * len(kinds))
    for name, R in results.items():
        if 'coupling' not in R:
            continue
        cells = []
        for k in kinds:
            c = R['coupling'].get(k)
            cells.append('-' if not c else f"{c['X']:.4f} ({c['n']})")
        L.append(f'| {name} | ' + ' | '.join(cells) + ' |')
    L.append(''); L.append('## 3. Position in line: JSD of first-unit distribution vs interior pool (null floor), mean length (pool)'); L.append('')
    pos_keys = ['1', '2', '3', '4', '5', '6', '7', '8', '-3', '-2', '-1']
    L.append('| text | ' + ' | '.join(pos_keys) + ' |'); L.append('|---|' + '---|' * len(pos_keys))
    for name, R in results.items():
        if 'position' not in R:
            continue
        cells = []
        for k in pos_keys:
            c = R['position'].get(k)
            cells.append('-' if not c else f"{c['jsd']:.3f} ({c['jsd_null']:.3f}); {c['len']:.2f}")
        L.append(f'| {name} | ' + ' | '.join(cells) + ' |')
    L.append(''); L.append('## 4. Is the boundary rule one for the whole book? PMI-matrix correlation, within-group split halves vs between groups'); L.append('')
    for key in ('rule_similarity_AB', 'rule_similarity_hands', 'rule_similarity_naibbe_halves', 'rule_similarity_latin_halves'):
        if key in results:
            r = results[key]
            L.append(f"- {key} (pairs per half {r['n_pairs_per_half']}): within " + ', '.join(f'{g} {v:.2f}' for g, v in r['within'].items() if v is not None)
                     + '; between ' + ', '.join(f'{g} {v:.2f}' for g, v in r['between'].items() if v is not None))
    L.append(''); L.append(f'Runtime {time.time() - t0:.0f} s.')
    open(os.path.join(HERE, 'boundaries.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
