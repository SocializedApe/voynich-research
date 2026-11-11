"""Gaskell-Bowern gibberish volunteers with their real line and page structure: the line tests and the fits
(10 Nov 2026)

Every earlier use of the volunteers' texts in this repository (b3 'gibberish', the November controls) poured their
words into the Voynich skeleton, which destroyed the volunteers' own lines and pages. Gaskell & Bowern (2022) had
42 volunteers hand-write 1-3 pages of meaningless text in pen, lowercase Latin letters, no punctuation, and
transcribed them preserving line breaks; 38 files are shipped. Here each file is read as written: one line per
written line (a word hyphenated across two lines is re-joined on the line where it starts), '____' separators as
page breaks, blank lines as paragraph breaks, the file as the writer, the file prefix (DA: 2 files, DC: 36) as the
batch. Apostrophes inside words (17 in all) are dropped, accents stripped, a-z kept. Glyph units as everywhere in
the November tests (common.units: ch and sh merged, otherwise letters).
Hierarchy for the fits: book > batch > writer > page > line (batch and writer stand where lang/hand and
section/quire stand for Voynich; a writer's whole output, 80-480 words, is about one Voynich page).

Parts (run from targets/voynich: python reinforce/volunteers.py <part>; 'all' = lines, writers, reuse, habit, slots gib, report):
  lines     word-to-word coupling within a line / across a line break / across a paragraph break and the position
            profile (lines/boundaries.py), plus the same coupling against a null that shuffles within each page
            (removes writer and page heterogeneity from the excess); near-copy geometry (lines/copy_geometry.py);
            per writer. Controls poured into the volunteers' skeleton: Latin, English, the autocopist, and the
            Voynich text itself in reading order (its own lines gone, so its coupling must cross the new breaks).
  writers   within-line coupling writer by writer against 200 shuffles of that writer's own pairs (and Voynich page by page).
  reuse     whole-word hierarchical Pitman-Yor fit (hpy.py, 100 sweeps) on the volunteers' hierarchy and on the
            same controls in the same skeleton.
  habit     the ending habit per writer and the ending's dependence on the preceding unit, both corpora:
            scribe_ratio.py on glyph bigrams, on endings alone and on openers alone, writers as scribes and
            Voynich hands 1-3 as scribes, 100-word docs (the 200-word docs of scribe_ratio.py do not fit a
            volunteer); normalised excess MI(last unit; preceding unit) over a shuffle of last units.
  slots gib | slots voy
            the location-only (slots4.py form) and the chained (slots5.py form) slot models refitted with a
            script-neutral split (first unit | rest | last unit) on the volunteers and on Voynich, so both corpora
            get the same model; share passed up per level, d, theta and the predictive log-likelihood per token.
  report    assembles gibberish_fit.md from the part files.
"""
import collections, json, math, os, random, re, statistics, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..')
sys.path.insert(0, HERE); sys.path.insert(0, VOY); sys.path.insert(0, os.path.join(VOY, 'lines')); sys.path.insert(0, os.path.join(VOY, 'meaning'))
sys.path.insert(0, os.path.join(VOY, '..', '..', 'research', 'voynich_siblings'))
import hpy, common, a4_selfcitation as a4, b3_bakeoff as b3
import boundaries, copy_geometry
import scribe_ratio as sr
import slots2, slots3
from slots import EMPTY

GIB = b3.GIB_DIR
GLEVELS = ['book', 'batch', 'writer', 'page', 'line']
GCTX = ['book', 'context', 'batch', 'writer', 'page', 'line']
VLOC = slots2.LEVELS                 # book > lang > hand > section > quire > page > line
VCTX = slots3.OPENER_LEVELS          # book > context > lang > hand > section > quire > page > line
SLOTS = ('opener', 'middle', 'ending')
SWEEPS_WORD = int(os.environ.get('HPY_SWEEPS', '100'))
SWEEPS_SLOT = int(os.environ.get('HPY_SLOT_SWEEPS', '60'))
U = common.units


def out_path(name):
    return os.path.join(HERE, name)


# ------------------------------------------------------------------------------------------------ loader
def gib_pages():
    out = []
    for fn in sorted(os.listdir(GIB)):
        if not fn.lower().endswith('.txt'):
            continue
        writer = re.sub(r'^gibberish - |\.txt$', '', fn, flags=re.I); batch = writer.split('_')[0]
        text = b3.strip_accents(open(os.path.join(GIB, fn), encoding='utf-8', errors='replace').read()).lower()
        text = text.replace('\r', '').replace("'", '')
        pages = []; lines = []; para = True; hyph = None
        for s in text.split('\n'):
            if re.match(r'^\s*_{3,}\s*$', s):
                if lines:
                    pages.append(lines); lines = []
                para = True; hyph = None; continue
            ws = re.findall(r'[a-z]+', s)
            if not ws:
                para = True; continue
            if hyph is not None:
                hyph['words'][-1] += ws[0]; ws = ws[1:]; hyph = None
                if not ws:
                    continue
            ln = {'words': ws, 'para_start': para}; para = False; lines.append(ln)
            hyph = ln if s.rstrip().endswith('-') else None
        if lines:
            pages.append(lines)
        for i, pl in enumerate(pages):
            out.append({'folio': f'{writer}_p{i + 1}', 'hand': writer, 'lang': batch, 'quire': writer, 'illus': batch, 'lines': pl})
    return out


def summary(pgs):
    toks = [w for p in pgs for ln in p['lines'] for w in ln['words']]
    return dict(writers=len({p['hand'] for p in pgs}), pages=len(pgs), lines=sum(len(p['lines']) for p in pgs), tokens=len(toks),
                types=len(set(toks)), words_per_line=statistics.mean(len(ln['words']) for p in pgs for ln in p['lines']),
                units_per_word=statistics.mean(len(U(w)) for w in toks), letters_per_word=statistics.mean(len(w) for w in toks))


def texts_for(gib):
    skel = a4.skeleton(gib); N = sum(len(ln['words']) for p in gib for ln in p['lines'])
    T = collections.OrderedDict(gibberish=gib)
    T['gibberish_DA'] = [p for p in gib if p['lang'] == 'DA']; T['gibberish_DC'] = [p for p in gib if p['lang'] == 'DC']
    T.update(common.controls(gib, which=('latin', 'english', 'autocopist_s19')))
    voy = common.pages(); vw = [w for p in voy for ln in p['lines'] for w in ln['words']]
    T['voynich_poured'] = common.with_meta(a4.pour(vw[:N], skel), gib)
    return T


# ------------------------------------------------------------------------------------------------ lines
def pair_kinds_grouped(pgs, key):
    K = collections.defaultdict(list)
    for p in pgs:
        g = key(p); L = p['lines']
        for n, ln in enumerate(L):
            ws = ln['words']
            for i in range(1, len(ws) - 2):
                K['within'].append((g, ws[i], ws[i + 1]))
            for i in range(1, len(ws) - 3):
                K['within_lag2'].append((g, ws[i], ws[i + 2]))
            if n + 1 < len(L):
                nx = L[n + 1]['words']
                K['para_break' if L[n + 1]['para_start'] else 'line_break'].append((g, ws[-1], nx[0]))
    return K


def coupling_grouped(triples, rng, reps=10):
    """normalised excess MI(last unit of a; first unit of b) over a null that shuffles the b-units within each group"""
    if len(triples) < 50:
        return None
    ab = [(g, U(a)[-1], U(b)[0]) for g, a, b in triples]
    obs = boundaries.mi([(x, y) for _, x, y in ab]); ys = [y for _, _, y in ab]
    byg = collections.defaultdict(list)
    for i, (g, _, _) in enumerate(ab):
        byg[g].append(i)
    base = []
    for _ in range(reps):
        y2 = ys[:]
        for idx in byg.values():
            vals = [ys[i] for i in idx]; rng.shuffle(vals)
            for i, v in zip(idx, vals):
                y2[i] = v
        base.append(boundaries.mi([(x, y2[i]) for i, (_, x, _) in enumerate(ab)]))
    return dict(n=len(ab), X=(obs - statistics.mean(base)) / boundaries.H(collections.Counter(ys)))


def coupling_z(pairs, rng, reps=200):
    """as boundaries.coupling, with the null's spread: X, z and the share of shuffles at or above the observed MI"""
    if len(pairs) < 50:
        return None
    ab = [(U(a)[-1], U(b)[0]) for a, b in pairs]
    obs = boundaries.mi(ab); bs = [x for x, _ in ab]; ys = [y for _, y in ab]; base = []
    for _ in range(reps):
        rng.shuffle(ys); base.append(boundaries.mi(list(zip(bs, ys))))
    mu = statistics.mean(base); sd = statistics.pstdev(base) or 1e-9; h = boundaries.H(collections.Counter(ys))
    return dict(n=len(ab), X=(obs - mu) / h, z=(obs - mu) / sd, p=sum(1 for b in base if b >= obs) / reps)


def part_writers(gib):
    """within-line coupling writer by writer with 200 shuffles each, and the same for Voynich page by page"""
    t0 = time.time(); rng = random.Random(29); R = collections.OrderedDict()
    for w in sorted({p['hand'] for p in gib}):
        pp = [p for p in gib if p['hand'] == w]; K = boundaries.pair_kinds(pp)
        R[w] = dict(tokens=sum(len(ln['words']) for p in pp for ln in p['lines']), within=coupling_z(K['within'], rng), line_break=coupling_z(K['line_break'], rng))
    voy = common.pages(); V = collections.OrderedDict()
    for p in voy:
        K = boundaries.pair_kinds([p])
        V[p['folio']] = dict(tokens=sum(len(ln['words']) for ln in p['lines']), hand=p['hand'], within=coupling_z(K['within'], rng))
    json.dump(dict(writers=R, voynich_pages=V), open(out_path('gibberish_writers.json'), 'w'), indent=1)
    zs = [r['within']['z'] for r in R.values() if r['within']]; vz = [r['within']['z'] for r in V.values() if r['within']]
    print(f'writers with >= 50 pairs {len(zs)}: z >= 3 in {sum(1 for z in zs if z >= 3)}, z >= 2 in {sum(1 for z in zs if z >= 2)}; '
          f'Voynich pages with >= 50 pairs {len(vz)}: z >= 3 in {sum(1 for z in vz if z >= 3)}, z >= 2 in {sum(1 for z in vz if z >= 2)}; {time.time() - t0:.0f}s')


def part_lines(gib):
    t0 = time.time(); rng = random.Random(23); T = texts_for(gib); R = collections.OrderedDict()
    for name, pgs in T.items():
        R[name] = boundaries.analyse(name, pgs, rng)
        K = pair_kinds_grouped(pgs, lambda p: p['folio'])
        R[name]['coupling_page_null'] = {k: coupling_grouped(K[k], rng) for k in ('within', 'within_lag2', 'line_break', 'para_break')}
        R[name]['geometry'] = copy_geometry.analyse(name, pgs)
        R[name]['summary'] = summary(pgs)
        print(name, 'done', f'{time.time() - t0:.0f}s', flush=True)
    voy = common.pages(); K = pair_kinds_grouped(voy, lambda p: p['folio'])
    R['voynich'] = dict(coupling={k: boundaries.coupling([(a, b) for _, a, b in K[k]], rng) for k in K},
                        coupling_page_null={k: coupling_grouped(K[k], rng) for k in K}, summary=summary(voy))
    per = collections.OrderedDict()
    for w in sorted({p['hand'] for p in gib}):
        pp = [p for p in gib if p['hand'] == w]; K = boundaries.pair_kinds(pp)
        per[w] = dict(tokens=sum(len(ln['words']) for p in pp for ln in p['lines']), lines=sum(len(p['lines']) for p in pp), pages=len(pp),
                      within=boundaries.coupling(K['within'], rng, reps=20), line_break=boundaries.coupling(K['line_break'], rng, reps=20))
    R['per_writer'] = per
    json.dump(R, open(out_path('gibberish_lines.json'), 'w'), indent=1)
    print('lines part done', f'{time.time() - t0:.0f}s')


# ------------------------------------------------------------------------------------------------ fits
def fit_data(data, levels, rng, sweeps, g0=None, fixed_sweeps=0, log=''):
    """hpy.fit over given (path, value) data and level names"""
    types = sorted({w for _, w in data})
    if g0 is None:
        g0 = {w: 1.0 / len(types) for w in types}
    m = hpy.HPY([0.5] * len(levels), [1.0] * len(levels), g0)
    for path, w in data:
        m.add(m.node(path), w, rng)
    order = list(range(len(data))); hist = []
    for s in range(sweeps):
        rng.shuffle(order)
        for i in order:
            path, w = data[i]; n = m.nodes[path]; m.remove(n, w, rng); m.add(n, w, rng)
        if s >= fixed_sweeps:
            m.resample_hyper(rng)
        hist.append((list(m.d), list(m.theta)))
        if log and (s % 10 == 9 or s == sweeps - 1):
            print(f'  {log} sweep {s + 1}: d ' + ' '.join(f'{x:.2f}' for x in m.d) + ' | theta ' + ' '.join(f'{x:.1f}' for x in m.theta), flush=True)
    half = hist[len(hist) // 2:]
    d = [statistics.mean(h[0][i] for h in half) for i in range(len(levels))]
    th = [statistics.mean(h[1][i] for h in half) for i in range(len(levels))]
    ll = m.loglik(data, rng)
    tables = {l: sum(n.t for n in m.nodes.values() if n.level == i) for i, l in enumerate(levels)}
    custs = {l: sum(n.c for n in m.nodes.values() if n.level == i) for i, l in enumerate(levels)}
    return dict(levels=levels, d=d, theta=th, loglik_per_token=ll, tokens=len(data), types=len(types),
                share_new_at_level={l: tables[l] / custs[l] for l in levels})


def gib_loc(p):
    return ('b' + p['lang'], 'w' + p['hand'], p['folio'])


def voy_loc(p):
    return ('L' + p['lang'], 'h' + p['hand'], 's' + p['illus'], 'q' + p['quire'], p['folio'])


def word_paths(pgs, loc_of):
    data = []
    for p in pgs:
        base = ('book',) + loc_of(p)
        for li, ln in enumerate(p['lines']):
            path = base + (f'l{li}',)
            for w in ln['words']:
                data.append((path, w))
    return data


def part_reuse(gib):
    t0 = time.time(); T = texts_for(gib); R = collections.OrderedDict()
    for name in ('gibberish', 'latin', 'english', 'autocopist_s19', 'voynich_poured'):
        if name not in T:
            continue
        R[name] = fit_data(word_paths(T[name], gib_loc), GLEVELS, random.Random(11), SWEEPS_WORD, log=name)
        print(name, 'fitted', f'{time.time() - t0:.0f}s', 'passed up', ' '.join(f"{l} {R[name]['share_new_at_level'][l]:.3f}" for l in GLEVELS), flush=True)
        json.dump(R, open(out_path('gibberish_reuse.json'), 'w'), indent=1)
    print('reuse part done', f'{time.time() - t0:.0f}s')


# ------------------------------------------------------------------------------------------------ habit
def excess_mi(pairs, rng, reps=20):
    if len(pairs) < 50:
        return None
    obs = boundaries.mi(pairs); ys = [y for _, y in pairs]; xs = [x for x, _ in pairs]; base = []
    for _ in range(reps):
        rng.shuffle(ys); base.append(boundaries.mi(list(zip(xs, ys))))
    return dict(n=len(pairs), X=(obs - statistics.mean(base)) / boundaries.H(collections.Counter(ys)))


def chain_measures(pgs, rng):
    words = [w for p in pgs for ln in p['lines'] for w in ln['words']]
    us = [U(w) for w in words]
    return dict(ending_given_preceding=excess_mi([(u[-2], u[-1]) for u in us if len(u) >= 2], rng),
                second_given_first=excess_mi([(u[0], u[1]) for u in us if len(u) >= 2], rng),
                ending_given_first=excess_mi([(u[0], u[-1]) for u in us if len(u) >= 3], rng),
                length_given_first=excess_mi([(u[0], str(min(len(u), 9))) for u in us], rng))


def part_habit(gib):
    t0 = time.time(); rng = random.Random(17); voy = common.pages(); R = collections.OrderedDict()
    groups = {'gibberish writers': {w: [x for p in gib if p['hand'] == w for ln in p['lines'] for x in ln['words']] for w in sorted({p['hand'] for p in gib})},
              'voynich hands 1-3': {h: [x for p in voy if p['hand'] == h for ln in p['lines'] for x in ln['words']] for h in ('1', '2', '3')}}
    splits = {'bigrams': U, 'ending': lambda w: [U(w)[-1]], 'opener': lambda w: [U(w)[0]], 'last2': lambda w: U(w)[-2:]}
    sr.DOC, sr.HALF = 100, 50
    import io, contextlib
    for gname, grp in groups.items():
        R[gname] = {}
        for sname, split in splits.items():
            with contextlib.redirect_stdout(io.StringIO()):
                R[gname][sname] = sr.analyse(f'{gname} {sname}', sr.docs_of(grp), split, random.Random(17))
            r = R[gname][sname]
            print(f"{gname:20} {sname:8} between/within {r['between_ratio']:.2f} [{r['ci'][0]:.2f}-{r['ci'][1]:.2f}] same/within {r['same_ratio']:.2f} docs {r['docs']}", flush=True)
    R['chain'] = {'gibberish': chain_measures(gib, rng), 'voynich': chain_measures(voy, rng)}
    for n, c in R['chain'].items():
        print(n, {k: round(v['X'], 4) if v else None for k, v in c.items()})
    json.dump(R, open(out_path('gibberish_habit.json'), 'w'), indent=1)
    print('habit part done', f'{time.time() - t0:.0f}s')


# ------------------------------------------------------------------------------------------------ slots
def split_neutral(w):
    u = U(w)
    if len(u) == 1:
        return (u[0], EMPTY, EMPTY)
    if len(u) == 2:
        return (u[0], EMPTY, u[1])
    return (u[0], ''.join(u[1:-1]), u[-1])


def last_unit(s):
    return '^' if not s or s == EMPTY else U(s)[-1]


def slot_data(pgs, loc_of, with_context):
    data = {s: [] for s in SLOTS}
    for p in pgs:
        loc = loc_of(p)
        for li, ln in enumerate(p['lines']):
            prev = None
            for w in ln['words']:
                o, m, e = split_neutral(w); os_ = '' if o == EMPTY else o; ms = '' if m == EMPTY else m
                cx = {'opener': (slots3.ctx_of(prev), o), 'middle': (last_unit(os_), m), 'ending': (last_unit(os_ + ms), e)}
                for s in SLOTS:
                    c, v = cx[s]
                    data[s].append(((('book', 'c' + c) if with_context else ('book',)) + loc + (f'l{li}',), v))
                tail = ms + ('' if e == EMPTY else e); prev = tail or EMPTY
    return data


def part_slots(corpus):
    t0 = time.time()
    if corpus == 'gib':
        pgs = gib_pages(); loc_of = gib_loc; levels = {'location': GLEVELS, 'chain': GCTX}
    else:
        pgs = common.pages(); loc_of = voy_loc; levels = {'location': VLOC, 'chain': VCTX}
    path = out_path(f'gibberish_slots_{corpus}.json')
    out = json.load(open(path)) if os.path.exists(path) else {}
    for model, with_ctx in (('location', False), ('chain', True)):
        data = slot_data(pgs, loc_of, with_ctx); out.setdefault(model, {})
        for s in SLOTS:
            if s in out[model]:
                continue
            counts = collections.Counter(v for _, v in data[s]); tot = sum(counts.values()); g0 = {v: c / tot for v, c in counts.items()}
            print(f'{corpus} {model} {s}: {len(counts)} values, {len({p for p, _ in data[s]})} line nodes', flush=True)
            r = fit_data(data[s], levels[model], random.Random(7), SWEEPS_SLOT, g0=g0, fixed_sweeps=10, log=f'{corpus} {model} {s}')
            out[model][s] = r
            print(f'  done {time.time() - t0:.0f}s ll {r["loglik_per_token"]:.3f} passed up ' + ' '.join(f"{l} {r['share_new_at_level'][l]:.2f}" for l in levels[model]), flush=True)
            json.dump(out, open(path, 'w'), indent=1)
    print('slots', corpus, 'done', f'{time.time() - t0:.0f}s')


# ------------------------------------------------------------------------------------------------ report
def f3(v, nd=3):
    return '' if v is None else f'{v:.{nd}f}'


def X(c):
    return '' if not c else f"{c['X']:.4f} ({c['n']})"


def report():
    L = ['# The gibberish volunteers with their own lines and pages: line tests and fits (10 Nov 2026)', '',
         'Script `volunteers.py` (docstring has the loader and the definitions). Every earlier use of the Gaskell-Bowern volunteers in this',
         'repository poured their words into the Voynich skeleton; here their own lines, pages and writers are kept.', '']
    if os.path.exists(out_path('gibberish_lines.json')):
        R = json.load(open(out_path('gibberish_lines.json')))
        s = R['gibberish']['summary']; v = R['voynich']['summary']
        L += ['## Corpus', '', '| | writers | pages | lines | tokens | types | words/line | units/word | letters/word |', '|---|---|---|---|---|---|---|---|---|']
        for name, q in (('gibberish', s), ('voynich ZL', v)):
            L.append(f"| {name} | {q['writers']} | {q['pages']} | {q['lines']} | {q['tokens']} | {q['types']} | {q['words_per_line']:.2f} | {q['units_per_word']:.2f} | {q['letters_per_word']:.2f} |")
        L += ['', '## Coupling of adjacent words: inside a line, across a line break, across a paragraph break', '',
              'X = normalised excess MI(last unit of the first word; first unit of the next) over shuffles (lines/boundaries.py); interior pairs',
              'for within; lag2 = one word skipped. "page null" = the shuffle is done within each page, which removes writer and page',
              'heterogeneity from the excess. Controls are poured into the volunteers\' skeleton (same lines, pages, writers).', '',
              '| text | within | within lag2 | line break | para break | first to second | within, page null | lag2, page null | line break, page null |',
              '|---|---|---|---|---|---|---|---|---|']
        for name, r in R.items():
            if name == 'per_writer':
                continue
            c = r['coupling']; g = r['coupling_page_null']
            L.append(f"| {name} | {X(c.get('within'))} | {X(c.get('within_lag2'))} | {X(c.get('line_break'))} | {X(c.get('para_break'))} | {X(c.get('first_to_second'))} | "
                     f"{X(g.get('within'))} | {X(g.get('within_lag2'))} | {X(g.get('line_break'))} |")
        per = R['per_writer']
        xs = sorted((w, r['within']['X']) for w, r in per.items() if r['within'])
        vals = [x for _, x in xs]
        L += ['', f'Per writer (within-line X, 20 shuffles, writers with >= 50 interior pairs: {len(vals)} of {len(per)}): median {statistics.median(vals):.4f}, '
              f'quartiles {sorted(vals)[len(vals) // 4]:.4f} / {sorted(vals)[3 * len(vals) // 4]:.4f}, min {min(vals):.4f}, max {max(vals):.4f}; '
              f'writers above 0.02: {sum(1 for x in vals if x > 0.02)}, above 0.04: {sum(1 for x in vals if x > 0.04)}.',
              'Across a line break per writer (where >= 50 breaks): ' + ', '.join(f"{w} {r['line_break']['X']:.3f}" for w, r in per.items() if r['line_break']) + '.', '']
        L += ['Writers ranked by within-line X: ' + ', '.join(f'{w} {x:.3f} ({per[w]["tokens"]}w)' for w, x in sorted(xs, key=lambda t: -t[1])) + '.', '']
        if os.path.exists(out_path('gibberish_writers.json')):
            W = json.load(open(out_path('gibberish_writers.json')))
            zs = [(w, r['within']) for w, r in W['writers'].items() if r['within']]
            vz = [(f, r['within'], r['tokens']) for f, r in W['voynich_pages'].items() if r['within']]
            L += ['Writer by writer against 200 shuffles of his own pairs (no heterogeneity in the null), writers with >= 50 interior pairs: '
                  + f'{len(zs)}; z >= 3 in {sum(1 for _, r in zs if r["z"] >= 3)}, z >= 2 in {sum(1 for _, r in zs if r["z"] >= 2)}, '
                  + f'median z {statistics.median(r["z"] for _, r in zs):.2f}. The same page by page for Voynich, pages with >= 50 interior pairs: {len(vz)}; '
                  + f'z >= 3 in {sum(1 for _, r, _ in vz if r["z"] >= 3)}, z >= 2 in {sum(1 for _, r, _ in vz if r["z"] >= 2)}, median z {statistics.median(r["z"] for _, r, _ in vz):.2f}; '
                  + f'median page size {statistics.median(t for _, _, t in vz):.0f} words.',
                  'Writers with z >= 2: ' + ', '.join(f'{w} X {r["X"]:.3f} z {r["z"]:.1f} ({W["writers"][w]["tokens"]}w)' for w, r in sorted(zs, key=lambda t: -t[1]['z']) if r['z'] >= 2) + '.', '']
        L += ['## Position profile: are line-first and line-last words different?', '',
              'JSD of the first-unit distribution at a position against the interior pool (lines of >= 6 words) and mean word length there; null =',
              'words shuffled within each line (20 reps). Positions 1, 2 from the start and -2, -1 from the end.', '',
              '| text | jsd 1 (null) | jsd 2 (null) | jsd -2 (null) | jsd -1 (null) | len 1 (null) | len -1 (null) | len pool |', '|---|---|---|---|---|---|---|---|']
        for name, r in R.items():
            if 'position' not in r:
                continue
            P = r['position']
            def cell(k, key, nd):
                return f"{P[k][key]:.{nd}f} ({P[k][key + '_null']:.{nd}f})" if k in P else ''
            L.append(f"| {name} | {cell('1', 'jsd', 3)} | {cell('2', 'jsd', 3)} | {cell('-2', 'jsd', 3)} | {cell('-1', 'jsd', 3)} | {cell('1', 'len', 2)} | {cell('-1', 'len', 2)} | {f3(P['1']['len_pool'], 2) if '1' in P else ''} |")
        try:
            B = json.load(open(os.path.join(VOY, 'lines', 'boundaries_results.json')))['voynich']['position']
            L.append(f"| voynich (lines/boundaries) | {B['1']['jsd']:.3f} ({B['1']['jsd_null']:.3f}) | {B['2']['jsd']:.3f} ({B['2']['jsd_null']:.3f}) | {B['-2']['jsd']:.3f} ({B['-2']['jsd_null']:.3f}) | "
                     f"{B['-1']['jsd']:.3f} ({B['-1']['jsd_null']:.3f}) | {B['1']['len']:.2f} ({B['1']['len_null']:.2f}) | {B['-1']['len']:.2f} ({B['-1']['len_null']:.2f}) | {B['1']['len_pool']:.2f} |")
        except Exception:
            pass
        L += ['', '## Near-copy geometry: is a near-copy in the line above, at the same position?', '',
              'lines/copy_geometry.py: token pairs at Levenshtein <= 1 between a line and the line above, interior positions; align1 = |position',
              'difference| <= 1, as a ratio to null A (words shuffled within each line) and null B (column shuffle); nearest = where the nearest',
              'earlier near-copy of a token on the page is (same line / one line above / two / three or more), observed and within-page shuffle.', '',
              '| text | events | align1 / null A | align1 / null B | same index / null B | nearest same, above1, above2, above3+ | shuffled |', '|---|---|---|---|---|---|---|']
        rows = [(n, r['geometry']) for n, r in R.items() if 'geometry' in r]
        try:
            rows.append(('voynich (lines/copy_geometry)', json.load(open(os.path.join(VOY, 'lines', 'copy_geometry_results.json')))['voynich']))
        except Exception:
            pass
        for name, G in rows:
            x = G['interior_k1_ld<=1']; na = G['nearest']
            def rat(c):
                return f"{c['ratio']:.3f} (z {c['z']:.1f})" if c else ''
            L.append(f"| {name} | {x['n']} | {rat(x['align1_A'])} | {rat(x['align1_B'])} | {rat(x['same_B'])} | "
                     + ', '.join(f"{na['obs'].get(k, 0):.3f}" for k in ('same', 'above1', 'above2', 'above3+')) + ' | '
                     + ', '.join(f"{na['within_page_shuffle'].get(k, 0):.3f}" for k in ('same', 'above1', 'above2', 'above3+')) + ' |')
        L.append('')
    if os.path.exists(out_path('gibberish_reuse.json')):
        R = json.load(open(out_path('gibberish_reuse.json')))
        L += ['## Whole-word re-use: hierarchical Pitman-Yor fit on book > batch > writer > page > line', '',
              f'hpy.py fit, {SWEEPS_WORD} sweeps, posterior means over the second half; passed up = share of draws at a level that opened a new table',
              '(were not a re-use at that level). Controls poured into the volunteers\' skeleton: each "writer" is then a run of 80-480 words of the',
              'control, each "page" a run of the size of that volunteer\'s page.', '',
              '| text | tokens | types | log2 p/token | ' + ' | '.join(f'd {l}' for l in GLEVELS) + ' | ' + ' | '.join(f'theta {l}' for l in GLEVELS) + ' | ' + ' | '.join(f'passed up {l}' for l in GLEVELS) + ' |',
              '|---|---|---|---|' + '---|' * (3 * len(GLEVELS))]
        for name, r in R.items():
            L.append(f"| {name} | {r['tokens']} | {r['types']} | {r['loglik_per_token']:.3f} | " + ' | '.join(f'{x:.2f}' for x in r['d']) + ' | ' + ' | '.join(f'{x:.1f}' for x in r['theta'])
                     + ' | ' + ' | '.join(f"{r['share_new_at_level'][l]:.3f}" for l in GLEVELS) + ' |')
        try:
            F = json.load(open(out_path('fit_results.json')))
            L += ['', 'For reference, the Voynich fit on its own hierarchy (fit.md), passed up per level: ' + ', '.join(f"{l} {F['voynich']['share_new_at_level'][l]:.3f}" for l in hpy.LEVELS)
                  + '; the same for the poured gibberish of that run: ' + ', '.join(f"{l} {F['gibberish']['share_new_at_level'][l]:.3f}" for l in hpy.LEVELS) + '.']
        except Exception:
            pass
        L.append('')
    if os.path.exists(out_path('gibberish_habit.json')):
        R = json.load(open(out_path('gibberish_habit.json')))
        L += ['## The ending habit per writer, and the chain inside the word', '',
              'scribe_ratio.py with 100-word docs (HALF 50): JSD between docs of different scribes / JSD between the two halves of a doc, and the',
              'same for docs of the same scribe; on glyph bigrams (the repository\'s scribe ratio), on last units alone, on last two units, on first',
              'units alone. Writers are the volunteers\' scribes; Voynich hands 1-3 are Davis\'s.', '',
              '| scribes | split | between scribes / within | same scribe other doc / within | docs |', '|---|---|---|---|---|']
        for gname in ('gibberish writers', 'voynich hands 1-3'):
            for sname, r in R[gname].items():
                L.append(f"| {gname} | {sname} | {r['between_ratio']:.2f} [{r['ci'][0]:.2f}-{r['ci'][1]:.2f}] | {r['same_ratio']:.2f} [{r['same_ci'][0]:.2f}-{r['same_ci'][1]:.2f}] | {r['docs']} |")
        L += ['', 'Chain inside the word: normalised excess MI over a shuffle (20 reps), words of >= 2 units (>= 3 for ending given first).', '',
              '| text | ending given preceding unit | second given first | ending given first | length given first |', '|---|---|---|---|---|']
        for name, c in R['chain'].items():
            L.append(f"| {name} | {X(c['ending_given_preceding'])} | {X(c['second_given_first'])} | {X(c['ending_given_first'])} | {X(c['length_given_first'])} |")
        L.append('')
    for corpus, title in (('gib', 'volunteers'), ('voy', 'Voynich')):
        p = out_path(f'gibberish_slots_{corpus}.json')
        if not os.path.exists(p):
            continue
        R = json.load(open(p))
        L += [f'## Slot models with the neutral split on the {title}', '',
              f'Split: first unit | the rest | last unit. Location model: slots4.py form (no context); chain model: slots5.py form (each slot in the',
              f'context of the unit before it, context directly under book). {SWEEPS_SLOT} sweeps, 10 at fixed hyperparameters. log2 p/token = held-in',
              'predictive log-likelihood of the fitted restaurant (same data for both models of a slot, so the difference is the value of the context).', '']
        for model, M in R.items():
            lv = next(iter(M.values()))['levels']
            L += [f'### {model} model, levels ' + ' > '.join(lv), '',
                  '| slot | values | log2 p/token | ' + ' | '.join(f'd {l}' for l in lv) + ' | ' + ' | '.join(f'theta {l}' for l in lv) + ' | ' + ' | '.join(f'up {l}' for l in lv) + ' |',
                  '|---|---|---|' + '---|' * (3 * len(lv))]
            for s, r in M.items():
                L.append(f"| {s} | {r['types']} | {r['loglik_per_token']:.3f} | " + ' | '.join(f'{x:.2f}' for x in r['d']) + ' | ' + ' | '.join(f'{x:.1f}' for x in r['theta'])
                         + ' | ' + ' | '.join(f"{r['share_new_at_level'][l]:.2f}" for l in lv) + ' |')
            L.append('')
        if 'location' in R and 'chain' in R:
            L.append('Gain of the chain model over the location model, bits per token: ' + ', '.join(
                f"{s} {R['chain'][s]['loglik_per_token'] - R['location'][s]['loglik_per_token']:+.3f}" for s in SLOTS if s in R['chain'] and s in R['location']) + '.')
            L.append('')
    open(out_path('gibberish_fit.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('\n'.join(L))


def main():
    part = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if part in ('summary',):
        gib = gib_pages(); print(json.dumps(summary(gib), indent=1))
        for p in gib[:3]:
            print(p['folio'], p['hand'], p['lang'], len(p['lines']), p['lines'][0])
        return
    if part in ('lines', 'all'):
        part_lines(gib_pages())
    if part in ('writers', 'all'):
        part_writers(gib_pages())
    if part in ('reuse', 'all'):
        part_reuse(gib_pages())
    if part in ('habit', 'all'):
        part_habit(gib_pages())
    if part == 'slots':
        part_slots(sys.argv[2])
    if part == 'all':
        part_slots('gib')
    if part in ('report', 'all'):
        report()


if __name__ == '__main__':
    main()
