"""Labels against paragraph text: the word recipe without the line machinery? (11 Nov 2026)

Everything so far used paragraph text (locus type P). Labels (L: short words beside drawings, 771 words in 693 loci)
are not written in lines, and the ring texts (C circular, R radial) are lines without a left and right margin.
If the line effects (first-word glyph in front, last-word vocabulary, -m) are made by the line, labels should look
like interior words; if the word recipe (slots, length budget, within-word chain) is general, labels should have it.

Groups: paragraph interior words (index >= 3, not the last two, lines of 6+ words), line-first, line-last, labels,
circular, radial; labels also split into single-word loci and multi-word loci. Per group:
  n, mean length, share with no opener / middle / ending (slots4.split3), share of m-final words;
  share of tokens that are paragraph word types, and prefixed-like (edges.py: without the first glyph the word is 5+
  times commoner among interior words);
  length budget (lengths.measure: r opener/middle and stem/ending within chain contexts, variance ratio);
  within-word chain: excess MI of the ending given the last unit before it, over a shuffle (bits);
  JSD of the first glyph unit, of the opener and of the ending against interior words, against line-first words and
  against line-last words (each with a floor: the reference group subsampled to the same count, 20 draws).
Reading rule: a group is 'like' the reference whose JSD less floor is smallest on first unit and ending.

Run from targets/voynich: python lines/labels.py -> lines/labels_results.json, labels.md
"""
import collections, csv, json, math, os, random, statistics, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..')
sys.path.insert(0, HERE); sys.path.insert(0, VOY); sys.path.insert(0, os.path.join(VOY, 'reinforce')); sys.path.insert(0, os.path.join(VOY, 'meaning'))
sys.path.insert(0, os.path.join(VOY, '..', '..', 'research', 'voynich_siblings'))
import common, boundaries, lengths
import slots4
from slots import EMPTY

U = common.units


def load():
    G = collections.defaultdict(list)
    for r in csv.DictReader(open(common.TSV, encoding='utf-8'), delimiter='\t'):
        ws = [w for w in r['line_words'].split() if common.AZ.match(w)]
        if not ws:
            continue
        t = r['locus_type']
        if t == 'P':
            G['paragraph, all'] += ws
            if len(ws) >= 6:
                G['line-first'].append(ws[0]); G['line-last'].append(ws[-1]); G['interior'] += ws[2:-2]
        elif t == 'L':
            G['labels'] += ws; G['labels, single-word loci' if len(ws) == 1 else 'labels, multi-word loci'] += ws
        elif t == 'C':
            G['circular'] += ws
        elif t == 'R':
            G['radial'] += ws
    return G


def trip(ws):
    return [tuple('' if x == EMPTY else x for x in slots4.split3(w)) for w in ws]


def chain_mi(ws, rng):
    pairs = []
    for o, m, e in trip(ws):
        s = o + m; pairs.append((U(s)[-1] if s else '^', e))
    if len(pairs) < 100:
        return None
    obs = boundaries.mi(pairs); xs = [a for a, _ in pairs]; ys = [b for _, b in pairs]; base = []
    for _ in range(20):
        rng.shuffle(ys); base.append(boundaries.mi(list(zip(xs, ys))))
    return obs - statistics.mean(base)


def jsd_floor(x, ref, rng):
    if len(x) < 60 or len(ref) < 2 * len(x):
        return None
    cr = collections.Counter(ref)
    fl = [boundaries.common_jsd(collections.Counter(rng.sample(ref, len(x))), cr) for _ in range(20)]
    return dict(jsd=boundaries.common_jsd(collections.Counter(x), cr), floor=statistics.mean(fl))


def main():
    t0 = time.time(); G = load(); rng = random.Random(6)
    inter = collections.Counter(G['interior']); ptypes = set(G['paragraph, all'])
    feats = dict(first=lambda w: U(w)[0], opener=lambda w: slots4.split3(w)[0], ending=lambda w: slots4.split3(w)[2])
    res = collections.OrderedDict()
    for name in ('interior', 'line-first', 'line-last', 'labels', 'labels, single-word loci', 'labels, multi-word loci', 'circular', 'radial'):
        ws = G[name]; T = trip(ws)
        if len(ws) < 60:
            continue
        loo = 1 if name == 'interior' else 0
        pre = sum(1 for w in ws if len(U(w)) >= 2 and inter[''.join(U(w)[1:])] >= 5 * max(inter[w] - loo, 1)) / len(ws)
        m = lengths.measure(T)
        r = dict(n=len(ws), mean_len=statistics.mean(map(len, ws)), no_opener=sum(1 for o, _, _ in T if not o) / len(T), no_middle=sum(1 for _, x, _ in T if not x) / len(T),
                 no_ending=sum(1 for _, _, e in T if not e) / len(T), m_final=sum(1 for w in ws if w.endswith('m')) / len(ws),
                 paragraph_type=sum(1 for w in ws if w in ptypes) / len(ws), prefixed_like=pre, types_per_token=len(set(ws)) / len(ws),
                 r_opener_middle_within_ctx=m['r_opener_middle_within_ctx'], r_stem_ending_within_ctx=m['r_stem_ending_within_ctx'], var_ratio=m['var_ratio'],
                 chain_mi_ending=chain_mi(ws, rng), jsd={})
        for refname in ('interior', 'line-first', 'line-last'):
            if refname == name:
                continue
            for fn, f in feats.items():
                r['jsd'][f'{fn} vs {refname}'] = jsd_floor([f(w) for w in ws], [f(w) for w in G[refname]], rng)
        res[name] = r
    json.dump(res, open(os.path.join(HERE, 'labels_results.json'), 'w'), indent=1)
    cols = [('n', 'n'), ('mean_len', 'length'), ('no_opener', 'no opener'), ('no_middle', 'no middle'), ('no_ending', 'no ending'), ('m_final', 'm-final'),
            ('paragraph_type', 'paragraph types'), ('prefixed_like', 'prefixed-like'), ('types_per_token', 'types/token'), ('r_opener_middle_within_ctx', 'r o,m in ctx'),
            ('r_stem_ending_within_ctx', 'r stem,e in ctx'), ('var_ratio', 'var ratio'), ('chain_mi_ending', 'chain MI (bits)')]
    f = lambda k, v: '-' if v is None else (str(v) if k == 'n' else f'{v:.2f}' if k == 'mean_len' else f'{v:.3f}')
    L = ['# Labels and ring texts against paragraph words (11 Nov 2026)', '', 'Script `labels.py` (protocol in its docstring).', '',
         '| group | ' + ' | '.join(c for _, c in cols) + ' |', '|---|' + '---|' * len(cols)]
    for name, r in res.items():
        L.append(f'| {name} | ' + ' | '.join(f(k, r[k]) for k, _ in cols) + ' |')
    L += ['', 'JSD less floor (bits; JSD and floor in brackets):', '', '| group | feature | vs interior | vs line-first | vs line-last |', '|---|---|---|---|---|']
    g = lambda d: '-' if d is None else f"{d['jsd'] - d['floor']:+.3f} ({d['jsd']:.3f}, {d['floor']:.3f})"
    for name, r in res.items():
        for fn in feats:
            L.append(f'| {name} | {fn} | ' + ' | '.join(g(r['jsd'].get(f'{fn} vs {ref}')) for ref in ('interior', 'line-first', 'line-last')) + ' |')
    L.append(''); L.append(f'Runtime {time.time() - t0:.0f} s.')
    open(os.path.join(HERE, 'labels.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    main()
