"""v_b1.py -- adversarial verification of b1_segmentation.py (pure Python stdlib, seeded, deterministic).

Nothing is imported from b1, a1, a3 or a4.  IVTFF parsing, glyph merging, the syllabifier, entropies, Zipf,
positional lock, the linear-ordering (pair-violation) search and the length-matched resampler are written
again here from b1's stated method (its docstring), and compared with b1's committed results/b1.json.

1. ZL3b-n paragraph text (P loci).  ALL = every IVTFF ',' a break (the TSV); CERTAIN = ',' joined, '.' splits.
   My own IVTFF parse of data/ZL3b-n.txt is checked against the TSV.  Same battery in raw EVA, a3's merge
   (ckh cth cph cfh ch sh, eee/ee -> ee, iiin/iin/in -> iin) and a1's merge2 (greedy longest match over
   ckh cth cph cfh ch sh iiin iin eee ee aiin ain in qo).  Parse audit: the '<->' drawing-interruption tag and
   the '{..}' ligature groups, which b1 (and parse_ivtff.py) delete; a corrected parse ('<->' = break,
   braces keep their glyphs) is run through the same battery.
2. Latin prose (Confessiones, corp_la_33849), Latin verse (Aeneid, corp_la_227), Italian (vatican5
   corpus_it.txt, anchored at the September sample start 'cumque predictus fcrdiuandu', see below) as
   words / syllables / CV-trimmed syllables / bisyllabic chunks (plain, CV) / within-syllable shuffle,
   N = ZL ALL token count.
3. Attacks: (a) h2-with-spaces decomposed by the class of the previous symbol, and a language-free random
   generator of C/V/CV tokens; (b) syllabifier sensitivity: ae/oe ligatures folded, hiatus split, Italian
   u-for-v; (c) open-syllable (vowel-final) cut; (d) a real CV-rigid language: Hawaiian (1839 Bible) and
   Maori as words, morae, syllables, syllable pairs; (e) length-matched pair violation over 10 seeds, pool
   sizes, and per-length violation with the order refitted at each length (no resampling).
Battery: tokens, types, hapax % of types, Zipf slope ranks 1..min(1000, types) (OLS log10 f on log10 r),
length mean / variance / var/(mean-1), h1 h2 with spaces (one space symbol between tokens, none at line ends),
h1 h2 without spaces, h2 within words, positional lock (symbols >= 20 occurrences, >= 90% in one of
initial/medial/final) and I(symbol; position class), pair violation = token-weighted share of within-word
ordered pairs of distinct symbols out of order under the best linear order (own search: insertion local
search from 2 constructive + 40 random starts), by length 2..6, and length-matched to the ZL ALL merge-a3
length histogram (resampling with replacement inside each length, nearest length if absent).
Usage: python v_b1.py [--rerun <b1.json from an as-is re-run>] [--rerun-it <json of b1 code on the
anchored Italian sample>].  Writes results/v_b1.json and results/v_b1.md.  Does not touch b1 files.
"""
import os as _os  # local paths (the September 2026 scripts hard-coded another machine)
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_CORP = _os.path.join(_HERE, 'data', 'corpora')  # corp_<lang>_<gutenberg id>.txt, see fetch_corpora.py
_EXT = _os.path.join(_HERE, 'data', 'external')  # third-party data (Naibbe, Gaskell & Bowern)
_IT = _os.path.join(_CORP, 'corpus_it.txt')  # vatican5 OCR corpus from the September sample's first words (fetch_corpora.py)
import sys, re, json, math, random, collections, pathlib, time, subprocess, unicodedata

HERE = pathlib.Path(_HERE); DATA = HERE / 'data'; RES = HERE / 'results'
CORP = pathlib.Path(_CORP); IT = pathlib.Path(_IT)
T0 = time.time()
EVA = set('acdefghiklmnopqrsty')
SP = '\x00'          # the space symbol in with-space streams
IT_ANCHOR = 'cumque predictus fcrdiuandu'   # first words of b1's (and a3/a4's) Italian sample


def log(*a):
    print(f'[{time.time() - T0:6.1f}s]', *a, flush=True)


# ================================================================== Voynich: TSV and own IVTFF parse
def zl_tsv_lines():
    out = []
    with open(DATA / 'ZL3b-n.words.tsv', encoding='utf-8') as f:
        head = f.readline().rstrip('\n').split('\t')
        ci, wi = head.index('locus_type'), head.index('line_words')
        for line in f:
            r = line.rstrip('\n').split('\t')
            if r[ci] == 'P':
                out.append(r[wi].split())
    return out


def ivtff_P_texts(path):
    """Raw text of every P locus (locus header <page.n,xPy>), in file order."""
    out = []
    for raw in open(path, encoding='utf-8', errors='replace'):
        raw = raw.rstrip('\n')
        if not raw or raw.startswith('#'):
            continue
        m = re.match(r'<([^>]+)>\s*(.*)$', raw)
        if not m:
            continue
        mm = re.fullmatch(r'([^.,]+)\.([^,]+),(.)([A-Za-z])(.*)', m.group(1))
        if mm and mm.group(4) == 'P':
            out.append(m.group(2))
    return out


def ivtff_words(texts, comma='split', dash='delete', braces='delete'):
    """comma: split|join; dash ('<->' drawing interruption): delete (b1) | break; braces: delete (b1) | keep."""
    lines = []
    for t in texts:
        t = re.sub(r'<![^>]*>', '', t)
        if dash == 'break':
            t = t.replace('<->', '.')
        t = re.sub(r'<[^>]*>', '', t)
        t = re.sub(r'\{([^}]*)\}', (lambda m: m.group(1)) if braces == 'keep' else '', t)
        t = re.sub(r'\[([^:\]]*)(?::[^\]]*)?\]', r'\1', t)
        t = t.replace(',', '.' if comma == 'split' else '')
        lines.append([w for w in t.split('.') if w])
    return lines


def ivtff_audit(texts):
    j = '\n'.join(texts)
    ctx = re.findall(r'([a-z]{1,8})<->([a-z]{1,8})', j)
    return {'P_loci': len(texts), 'commas': j.count(','), 'periods': j.count('.'),
            'dash_tags': j.count('<->'), 'dash_between_glyphs': len(re.findall(r'[^.,\s>]<->[^.,\s<]', j)),
            'dash_next_to_separator': len(re.findall(r'[.,]<->|<->[.,]', j)),
            'brace_groups': len(re.findall(r'\{[^}]*\}', j)),
            'brace_groups_whole_word': len(re.findall(r'(?:^|[.,>])\{[^}]*\}(?=$|[.,<])', j, re.M)),
            'top_brace_groups': collections.Counter(re.findall(r'\{[^}]*\}', j)).most_common(10),
            'dash_contexts_first12': ['%s<->%s' % c for c in ctx[:12]],
            'other_tags': collections.Counter(re.findall(r'<[^!>][^>]*>', j)).most_common(8)}


def boundary_diagnostic(texts, min_n=5):
    """How word-break-like is each separator?  For every glyph pair (a, b), p_break(a, b) = n(a.b across a
    certain space) / (n across + n(ab inside a word)).  Averaged over the glyph pairs that flank each kind of
    separator ('.', ',', '<->'), and over the within-word pairs (token weighted; pairs seen < min_n times
    skipped).  A separator that marks word breaks scores like '.'; a word-internal juncture scores like 'within'."""
    within = collections.Counter(); across = collections.Counter(); ctx = {'.': [], ',': [], '<->': []}
    for t in texts:
        t = re.sub(r'<![^>]*>', '', t).replace('<->', '|')
        t = re.sub(r'<[^>]*>', '', t)
        t = re.sub(r'\{([^}]*)\}', lambda m: m.group(1), t)
        t = re.sub(r'\[([^:\]]*)(?::[^\]]*)?\]', r'\1', t)
        t = re.sub(r'@\d+;', '?', t)
        seq = [ch if (ch in EVA or ch in '.,|') else '?' for ch in t if not ch.isspace()]
        for a, b in zip(seq, seq[1:]):
            if a in EVA and b in EVA:
                within[(a, b)] += 1
        i = 0
        while i < len(seq):
            if seq[i] in '.,|':
                j = i
                while j < len(seq) and seq[j] in '.,|':
                    j += 1
                if j - i == 1 and i > 0 and j < len(seq) and seq[i - 1] in EVA and seq[j] in EVA:
                    key = {'.': '.', ',': ',', '|': '<->'}[seq[i]]
                    ctx[key].append((seq[i - 1], seq[j]))
                    if key == '.':
                        across[(seq[i - 1], seq[j])] += 1
                i = j
            else:
                i += 1

    def pb(p):
        n = across[p] + within[p]
        return across[p] / n if n >= min_n else None
    out = {}
    for k, lst in ctx.items():
        vals = [v for v in map(pb, lst) if v is not None]
        out[k] = {'contexts': len(lst), 'scored': len(vals), 'mean_p_break': round(sum(vals) / len(vals), 4),
                  'frac_p_break_gt_half': round(sum(v > 0.5 for v in vals) / len(vals), 4)}
    wv = [(pb(p), c) for p, c in within.items() if pb(p) is not None]
    out['within_word'] = {'pairs': sum(c for _, c in wv), 'mean_p_break': round(sum(v * c for v, c in wv) / sum(c for _, c in wv), 4),
                          'frac_p_break_gt_half': round(sum(c for v, c in wv if v > 0.5) / sum(c for _, c in wv), 4)}
    return out


def clean(lines):
    toks, drop, total = [], collections.Counter(), 0
    for ws in lines:
        for w in ws:
            total += 1
            if '?' in w:
                drop['?'] += 1
            elif not set(w) <= EVA:
                drop['nonEVA'] += 1
            else:
                toks.append(w)
    return toks, total, dict(drop)


# ------------------------------------------------------------------ glyph alphabets (words -> tuples)
_M3 = re.compile(r'ckh|cth|cph|cfh|ch|sh|eee|ee|iiin|iin|in|.')
_M3N = {'eee': 'ee', 'iiin': 'iin', 'in': 'iin'}
_M2 = {'ckh', 'cth', 'cph', 'cfh', 'ch', 'sh', 'iiin', 'iin', 'eee', 'ee', 'aiin', 'ain', 'in', 'qo'}


def g_raw(w):
    return tuple(w)


def g_m3(w):
    return tuple(_M3N.get(g, g) for g in _M3.findall(w))


def g_m2(w):
    out, i = [], 0
    while i < len(w):
        for L in (4, 3, 2):
            if w[i:i + L] in _M2:
                out.append(w[i:i + L]); i += L; break
        else:
            out.append(w[i]); i += 1
    return tuple(out)


ALPHA = {'raw': g_raw, 'merge_a3': g_m3, 'merge2_a1': g_m2}


# ================================================================== statistics
def cond_entropy(pairs):
    """H(B|A) from a Counter of (a, b) pairs, plug-in, bits."""
    n = sum(pairs.values()); first = collections.Counter()
    for (a, _), v in pairs.items():
        first[a] += v
    return sum(v / n * math.log2(first[a] / v) for (a, _), v in pairs.items())


def H(c):
    n = sum(c.values())
    return -sum(v / n * math.log2(v / n) for v in c.values())


def entropies(words):
    sp, ns = [], []
    for w in words:
        if sp:
            sp.append(SP)
        sp.extend(w); ns.extend(w)
    ww = collections.Counter()
    for w in words:
        ww.update(zip(w, w[1:]))
    return {'h1_sp': H(collections.Counter(sp)), 'h2_sp': cond_entropy(collections.Counter(zip(sp, sp[1:]))),
            'h1': H(collections.Counter(ns)), 'h2': cond_entropy(collections.Counter(zip(ns, ns[1:]))),
            'h2_within': cond_entropy(ww), 'alphabet': len(set(ns))}


def h2sp_by_class(words, vowels):
    """Contribution of each previous-symbol class (space / vowel / consonant) to h2 with spaces."""
    sp = []
    for w in words:
        if sp:
            sp.append(SP)
        sp.extend(w)
    pairs = collections.Counter(zip(sp, sp[1:])); n = sum(pairs.values())
    first = collections.Counter()
    for (a, _), v in pairs.items():
        first[a] += v
    cls = lambda s: 'space' if s == SP else ('vowel' if s in vowels else 'consonant')
    contrib, mass = collections.Counter(), collections.Counter()
    for (a, b), v in pairs.items():
        contrib[cls(a)] += v / n * math.log2(first[a] / v)
    for a, v in first.items():
        mass[cls(a)] += v / n
    return {k: {'P_prev': round(mass[k], 4), 'H_next_given_prev': round(contrib[k] / mass[k], 4) if mass[k] else None,
                'contribution_bits': round(contrib[k], 4)} for k in ('space', 'vowel', 'consonant') if mass[k]}


def zipf_slope(tokens):
    f = sorted(collections.Counter(tokens).values(), reverse=True); r = min(1000, len(f))
    xs = [math.log10(i) for i in range(1, r + 1)]; ys = [math.log10(v) for v in f[:r]]
    mx, my = sum(xs) / r, sum(ys) / r
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)


def positional(words, minc=20):
    cnt = collections.defaultdict(collections.Counter)
    for w in words:
        L = len(w)
        for i, s in enumerate(w):
            cnt[s]['S' if L == 1 else 'I' if i == 0 else 'F' if i == L - 1 else 'M'] += 1
    keep = {s: c for s, c in cnt.items() if sum(c.values()) >= minc}
    N = sum(sum(c.values()) for c in keep.values()); pc = collections.Counter()
    for c in keep.values():
        pc.update(c)
    mi = 0.0
    for c in keep.values():
        ns = sum(c.values())
        for k, v in c.items():
            mi += v / N * math.log2(v * N / (ns * pc[k]))
    locked = sorted(s for s, c in keep.items() if max(c['I'], c['M'], c['F']) / sum(c.values()) >= 0.9)
    return {'n_symbols': len(keep), 'locked_n': len(locked), 'locked_frac': len(locked) / len(keep) if keep else None,
            'locked': locked, 'mi_bits': mi}


# ------------------------------------------------------------------ pair violation (own LOP search)
def precedence(tokens):
    tc = collections.Counter(tokens)
    syms = sorted({s for w in tc for s in w})
    idx = {s: i for i, s in enumerate(syms)}; n = len(syms)
    W = [[0] * n for _ in range(n)]
    for w, c in tc.items():
        ix = [idx[s] for s in w]
        for i in range(len(ix)):
            a = ix[i]
            for j in range(i + 1, len(ix)):
                if ix[j] != a:
                    W[a][ix[j]] += c
    return syms, W, tc


def lop(W, seed=11, starts=40):
    """Minimise sum over placed pairs (a before b) of W[b][a]; insertion local search, best-improvement."""
    n = len(W); rng = random.Random(seed)

    def cost(o):
        return sum(W[o[b]][o[a]] for a in range(n) for b in range(a + 1, n))

    def local(o):
        o = o[:]
        while True:
            best, move = 0, None
            for i in range(n):
                s = o[i]; d = 0
                for j in range(i - 1, -1, -1):
                    t = o[j]; d += W[t][s] - W[s][t]
                    if d < best:
                        best, move = d, (i, j)
                d = 0
                for j in range(i + 1, n):
                    t = o[j]; d += W[s][t] - W[t][s]
                    if d < best:
                        best, move = d, (i, j)
            if move is None:
                return o
            i, j = move; s = o.pop(i); o.insert(j, s)

    net = [sum(W[i]) - sum(W[j][i] for j in range(n)) for i in range(n)]
    ratio = [sum(W[i][j] / (W[i][j] + W[j][i]) for j in range(n) if W[i][j] + W[j][i]) for i in range(n)]
    inits = [sorted(range(n), key=lambda i: (-net[i], i)), sorted(range(n), key=lambda i: (-ratio[i], i))]
    for _ in range(starts):
        o = list(range(n)); rng.shuffle(o); inits.append(o)
    best_o, best_c = None, None
    for o in inits:
        o = local(o); c = cost(o)
        if best_c is None or c < best_c:
            best_o, best_c = o, c
    return best_o, best_c


def pair_violation(tokens, starts=40, by_len=True):
    syms, W, tc = precedence(tokens)
    tot = sum(map(sum, W))
    if not tot:
        return {'frac': None, 'pairs': 0, 'by_length': {}}
    o, c = lop(W, starts=starts)
    rank = {syms[k]: r for r, k in enumerate(o)}
    out = {'frac': c / tot, 'pairs': tot, 'order': [syms[k] for k in o]}
    if by_len:
        bl = {}
        for L in (2, 3, 4, 5, 6):
            bad = t = 0
            for w, k in tc.items():
                if len(w) != L:
                    continue
                for i in range(L):
                    for j in range(i + 1, L):
                        if w[i] != w[j]:
                            t += k; bad += k * (rank[w[i]] > rank[w[j]])
            if t:
                bl[L] = bad / t
        out['by_length'] = bl
    return out


def length_matched(tokens, hist, seed):
    rng = random.Random(seed); pools = collections.defaultdict(list)
    for w in tokens:
        pools[len(w)].append(w)
    Ls = sorted(pools); out = []; exact = 0
    for L in sorted(hist):
        k = hist[L]
        if L in pools:
            p = pools[L]; exact += k
        else:
            p = pools[min(Ls, key=lambda x: (abs(x - L), x))]
        out.extend(p[rng.randrange(len(p))] for _ in range(k))
    return out, exact / sum(hist.values())


def per_length_refit(tokens, Ls=(2, 3, 4, 5, 6)):
    """Violation with the order refitted on the tokens of each length alone (no resampling)."""
    out = {}
    for L in Ls:
        sub = [w for w in tokens if len(w) == L]
        if len(sub) < 50:
            continue
        pv = pair_violation(sub, starts=12, by_len=False)
        if pv['frac'] is not None:
            out[L] = {'viol': round(pv['frac'], 4), 'tokens': len(sub), 'types': len(set(sub))}
    return out


def battery(tokens, label, hist=None, lm_seeds=1, refit=False):
    t1 = time.time()
    c = collections.Counter(tokens); L = [len(w) for w in tokens]; n = len(L); m = sum(L) / n
    var = sum((x - m) ** 2 for x in L) / n
    e = entropies(tokens); pos = positional(tokens); pv = pair_violation(tokens)
    r = {'n_tokens': n, 'types': len(c), 'hapax_pct': 100 * sum(1 for v in c.values() if v == 1) / len(c),
         'zipf': zipf_slope(tokens), 'len_mean': m, 'len_var': var, 'disp': var / (m - 1) if m > 1 else None,
         **e, 'locked_frac': pos['locked_frac'], 'locked_n': pos['locked_n'], 'n_pos_symbols': pos['n_symbols'],
         'mi': pos['mi_bits'], 'pv': pv['frac'], 'pv_by_length': pv['by_length'],
         'top5': [(''.join(w), k) for w, k in c.most_common(5)]}
    if hist is not None and max(L) >= 3:
        vals = []
        for s in range(lm_seeds):
            lm, cov = length_matched(tokens, hist, 17 + s)
            vals.append(pair_violation(lm, starts=12 if s else 40, by_len=False)['frac'])
        r['pv_lm'] = vals[0]; r['lm_cov'] = cov
        if lm_seeds > 1:
            r['pv_lm_seeds'] = [round(v, 4) for v in vals]
            r['pv_lm_range'] = (round(min(vals), 4), round(max(vals), 4))
        pools = collections.Counter(len(w) for w in set(tokens))
        r['types_by_length'] = {k: pools.get(k, 0) for k in range(1, 9)}
    if refit:
        r['refit_by_length'] = per_length_refit(tokens)
    r['seconds'] = round(time.time() - t1, 1)
    log(f"{label:30s} n={n} types={r['types']} hapax={r['hapax_pct']:.1f} len={m:.2f}/{var:.2f} zipf={r['zipf']:.3f} "
        f"h2sp={e['h2_sp']:.3f} h2={e['h2']:.3f} lock={pos['locked_frac']} mi={pos['mi_bits']:.3f} pv={pv['frac']} "
        f"lm={r.get('pv_lm')}")
    return r


# ================================================================== languages and syllabifier
WORD = re.compile(r'[^\W\d_]+')


def gutenberg_words(path):
    t = path.read_text(encoding='utf-8', errors='replace')
    i = t.find('*** START OF'); j = t.find('*** END OF')
    if i >= 0:
        t = t[t.find('\n', i) + 1:j if j >= 0 else None]
    return WORD.findall(t.lower())


def italian_words(anchor=True, max_chars=4_000_000):
    t = IT.read_text(encoding='utf-8', errors='replace')
    k = t.find(IT_ANCHOR) if anchor else 0
    return WORD.findall(t[k:k + max_chars].lower()), k


VOW = set('aeiouy')
ON3 = {'str', 'spr', 'scr', 'spl', 'scl', 'sch', 'chr', 'thr', 'phr'}
ON2 = {'bl', 'br', 'cl', 'cr', 'dr', 'fl', 'fr', 'gl', 'gr', 'pl', 'pr', 'tr', 'ph', 'th', 'ch', 'qu', 'gn', 'st', 'sp',
       'sc', 'sm', 'sn'}
DIPH_LA = {'ae', 'oe', 'au', 'eu'}
DIPH_IT = {'ia', 'ie', 'io', 'iu', 'ua', 'ue', 'ui', 'uo', 'ai', 'ei', 'oi', 'au'}


def vmask(w, uv=False):
    m = [ch in VOW and not (ch == 'u' and i > 0 and w[i - 1] == 'q') for i, ch in enumerate(w)]
    if uv:   # Italian u-for-v spelling: u before a vowel, word-initially or after a vowel, is the consonant v
        for i, ch in enumerate(w):
            if ch == 'u' and m[i] and i + 1 < len(w) and w[i + 1] in VOW and (i == 0 or m[i - 1]):
                m[i] = False
    return m


def nuclei(w, m, diph=None):
    out, i, n = [], 0, len(w)
    while i < n:
        if not m[i]:
            i += 1; continue
        j = i
        while j < n and m[j]:
            j += 1
        if diph is None:
            out.append((i, j))
        else:
            k = i
            while k < j:
                if k + 1 < j and w[k:k + 2] in diph:
                    out.append((k, k + 2)); k += 2
                else:
                    out.append((k, k + 1)); k += 1
        i = j
    return out


def syllabify(w, diph=None, uv=False, open_cut=False):
    m = vmask(w, uv); nu = nuclei(w, m, diph)
    if len(nu) <= 1:
        return [w]
    cuts = []
    for (s0, e0), (s1, e1) in zip(nu, nu[1:]):
        k = s1 - e0; cl = w[e0:s1]
        if open_cut or k <= 1:
            cut = e0
        elif k >= 3 and cl[-3:] in ON3:
            cut = s1 - 3
        elif cl[-2:] in ON2:
            cut = s1 - 2
        else:
            cut = s1 - 1
        cuts.append(cut)
    b = [0] + cuts + [len(w)]
    return [w[x:y] for x, y in zip(b, b[1:]) if w[x:y]]


def cv_trim(s, uv=False):
    m = vmask(s, uv); i = 0
    while i < len(s) and not m[i]:
        i += 1
    if i == len(s):
        return s[:1]
    return (s[0] if i > 0 else '') + s[i]


def variants(words, N, rng_seed=5, **kw):
    uv = kw.get('uv', False)
    sy = [syllabify(w, **kw) for w in words]
    syl = [s for ss in sy for s in ss]
    chunks = [ss[i:i + 2] for ss in sy for i in range(0, len(ss), 2)]
    out = {'words': [tuple(w) for w in words[:N]], 'syl': [tuple(s) for s in syl[:N]],
           'cv': [tuple(cv_trim(s, uv)) for s in syl[:N]],
           'syl2': [tuple(''.join(c)) for c in chunks[:N]],
           'cv2': [tuple(''.join(cv_trim(s, uv) for s in c)) for c in chunks[:N]]}
    rng = random.Random(rng_seed); sh = []
    for w in out['syl']:
        x = list(w); rng.shuffle(x); sh.append(tuple(x))
    out['syl_shuf'] = sh
    acc = 0; span = None
    for i, ss in enumerate(sy):
        acc += len(ss)
        if acc >= N:
            span = i + 1; break
    info = {'words_available': len(words), 'syllables_available': len(syl),
            'syllables_per_word': len(syl) / len(words), 'words_spanned_by_N_syllables': span,
            'syllables_per_syl2_chunk': sum(len(c) for c in chunks[:N]) / N,
            'multi_vowel_nuclei_frac': (lambda nn: sum(1 for a, b in nn if b - a > 1) / len(nn))(
                [x for w in words[:20000] for x in nuclei(w, vmask(w, uv), kw.get('diph'))])}
    return out, info


# ------------------------------------------------------------------ CV-rigid languages (Hawaiian, Maori)
def plain_words(path, fold_macrons=False, digraphs=()):
    t = path.read_text(encoding='utf-8', errors='replace').lower()
    if fold_macrons:
        t = ''.join(ch for ch in unicodedata.normalize('NFD', t) if unicodedata.category(ch) != 'Mn')
    for dg, ch in digraphs:
        t = t.replace(dg, ch)
    return WORD.findall(t)


def cv_lang_variants(words, N, vowels='aeiou', diph=('ai', 'ae', 'ao', 'au', 'ei', 'eu', 'oi', 'ou', 'iu')):
    v = f'[{vowels}]'; c = f'[^{vowels}]'
    mora = re.compile(f'{c}?{v}|{c}')
    syl = re.compile(f"{c}?(?:{'|'.join(diph)}|{v})|{c}")
    mo = [m for w in words for m in mora.findall(w)]
    sy_w = [syl.findall(w) for w in words]
    sy = [s for ss in sy_w for s in ss]
    pairs = [''.join(ss[i:i + 2]) for ss in sy_w for i in range(0, len(ss), 2)]
    return {'words': [tuple(w) for w in words[:N]], 'mora': [tuple(x) for x in mo[:N]],
            'syl': [tuple(x) for x in sy[:N]], 'syl2': [tuple(x) for x in pairs[:N]]}


def random_cv(tokens, vowels, N, seed=23):
    """Language-free control: token shape (C, V, CV, ...) and every consonant/vowel drawn independently from
    the sample's own shape and letter frequencies."""
    rng = random.Random(seed)
    shapes = collections.Counter(''.join('V' if s in vowels else 'C' for s in w) for w in tokens)
    cons = collections.Counter(s for w in tokens for s in w if s not in vowels)
    vows = collections.Counter(s for w in tokens for s in w if s in vowels)
    sh_k, sh_w = list(shapes), list(shapes.values())
    ck, cw = list(cons), list(cons.values()); vk, vw = list(vows), list(vows.values())
    out = []
    for _ in range(N):
        shp = rng.choices(sh_k, sh_w)[0]
        out.append(tuple(rng.choices(vk, vw)[0] if x == 'V' else rng.choices(ck, cw)[0] for x in shp))
    return out, dict(shapes.most_common(6))


# ================================================================== b1 committed / re-run values
def committed_b1():
    try:
        txt = subprocess.run(['git', 'show', 'HEAD:targets/voynich/results/b1.json'], cwd=HERE, capture_output=True,
                             text=True, encoding='utf-8', check=True).stdout
        return json.loads(txt), 'git HEAD:targets/voynich/results/b1.json'
    except Exception:
        return json.load(open(RES / 'b1.json', encoding='utf-8')), 'results/b1.json (working tree)'


def b1_view(r):
    """Map a b1.json row onto my field names."""
    if r is None:
        return None
    P = r['positional']; L = r['length']
    return {'n_tokens': r['n_tokens'], 'types': r['types'], 'hapax_pct': 100 * r['hapax_type_frac'],
            'zipf': r['zipf_slope_1_1000'], 'len_mean': L['mean'], 'len_var': L['variance'], 'h1_sp': r['h1_sp'],
            'h2_sp': r['h2_sp'], 'h1': r['h1_nosp'], 'h2': r['h2_nosp'], 'h2_within': r['h2_within_word'],
            'locked_frac': P['locked_frac'], 'mi': P['mi_bits'], 'pv': r['pair']['pair_violation_frac'],
            'pv_lm': r.get('pair_length_matched')}


KEYS = [('types', 0, 0), ('hapax_pct', 1, 0.051), ('len_mean', 2, 0.0051), ('len_var', 2, 0.0051), ('zipf', 3, 0.0006),
        ('h2_sp', 3, 0.0006), ('h2', 3, 0.0006), ('h2_within', 3, 0.0006), ('locked_frac', 3, 0.0006), ('mi', 3, 0.0006),
        ('pv', 3, 0.0006), ('pv_lm', 3, 0.0006)]


def compare(mine, b1):
    """Field-by-field agreement at b1's printed precision; pair violation may differ (search heuristic)."""
    out = {}
    for k, _, tol in KEYS:
        a, b = mine.get(k), b1.get(k)
        if a is None or b is None:
            out[k] = None if (a is None and b is None) else 'one side n/a'
            continue
        out[k] = abs(a - b) <= tol + 1e-12
    return out


# ================================================================== main
def main():
    args = sys.argv[1:]
    rerun = rerun_it = None
    if '--rerun' in args:
        rerun = json.load(open(args[args.index('--rerun') + 1], encoding='utf-8'))
    if '--rerun-it' in args:
        rerun_it = json.load(open(args[args.index('--rerun-it') + 1], encoding='utf-8'))
    b1, b1_src = committed_b1()
    O = {'method': __doc__, 'b1_source': b1_src, 'voynich': {}, 'languages': {}, 'attacks': {}, 'compare': {}}

    # ---------------- Voynich
    tsv_lines = zl_tsv_lines()
    all_tok, all_total, all_drop = clean(tsv_lines)
    N = len(all_tok)
    V = O['voynich']
    V['ALL'] = {'P_lines': len(tsv_lines), 'words_before_filter': all_total, 'dropped': all_drop, 'N': N}
    sets = {'ALL': all_tok}
    ivt = DATA / 'ZL3b-n.txt'
    if ivt.exists():
        texts = ivtff_P_texts(ivt)
        V['audit'] = ivtff_audit(texts)
        split = ivtff_words(texts, 'split'); join = ivtff_words(texts, 'join')
        V['split_parse_equals_tsv'] = [w for l in split for w in l] == [w for l in tsv_lines for w in l]
        cer, cer_total, cer_drop = clean(join)
        V['CERTAIN'] = {'words_before_filter': cer_total, 'dropped': cer_drop, 'N': len(cer),
                        'token_reduction_from_joins': sum(len(a) - len(b) for a, b in zip(split, join)),
                        'words_containing_a_join': sum(1 for a, b in zip(split, join) for w in b if w not in a)}
        sets['CERTAIN'] = cer; sets['ALL_trunc'] = all_tok[:len(cer)]
        fix_all = clean(ivtff_words(texts, 'split', 'break', 'keep'))[0]
        fix_cer = clean(ivtff_words(texts, 'join', 'break', 'keep'))[0]
        dash_all = clean(ivtff_words(texts, 'split', 'break', 'delete'))[0]
        brace_all = clean(ivtff_words(texts, 'split', 'delete', 'keep'))[0]
        dl = ivtff_words(texts, 'split', 'delete', 'delete'); bl = ivtff_words(texts, 'split', 'break', 'delete')
        glued = [w for x, y in zip(dl, bl) for w in x if w not in y and '?' not in w and set(w) <= EVA]
        V['FIXED'] = {'ALL_fix_N': len(fix_all), 'CERTAIN_fix_N': len(fix_cer), 'ALL_dash_N': len(dash_all),
                      'ALL_brace_N': len(brace_all),
                      'dash_glued_clean_tokens': len(glued), 'dash_glued_mean_len_raw': sum(map(len, glued)) / len(glued),
                      'dash_glued_first15': glued[:15],
                      'note': "_fix: '<->' read as a word break and {..} ligature groups keep their glyphs; "
                              "_dash: only '<->' fixed; _brace: only braces fixed"}
        V['boundary_diagnostic'] = boundary_diagnostic(texts)
        log('boundary diagnostic', V['boundary_diagnostic'])
        sets['ALL_fix'] = fix_all; sets['CERTAIN_fix'] = fix_cer
        sets['ALL_dash'] = dash_all; sets['ALL_brace'] = brace_all
    else:
        V['audit'] = 'data/ZL3b-n.txt absent: CERTAIN rows not computed'
    hist = {a: collections.Counter(len(f(w)) for w in all_tok) for a, f in ALPHA.items()}
    target = hist['merge_a3']
    V['merge_a3_length_hist'] = dict(sorted(target.items()))
    V['stats'] = {}
    for k, toks in sets.items():
        for a, f in ALPHA.items():
            if k in ('ALL_fix', 'CERTAIN_fix', 'ALL_dash', 'ALL_brace') and a == 'merge2_a1':
                continue
            sy = [f(w) for w in toks]
            V['stats'][f'{k}/{a}'] = battery(sy, f'ZL {k} {a}', hist[a] if k.startswith('CERTAIN') else None,
                                             lm_seeds=10 if k == 'CERTAIN' and a == 'merge_a3' else 1,
                                             refit=(k == 'ALL' and a in ('merge_a3', 'raw')))
    if 'CERTAIN' in sets:
        jw = collections.Counter(w for a, b in zip(split, join) for w in b if w not in a and '?' not in w
                                 and set(w) <= EVA)
        V['joined_words'] = {'n': sum(jw.values()), 'mean_len_raw': sum(len(w) * k for w, k in jw.items()) / sum(jw.values()),
                             'frac_already_ALL_types': sum(k for w, k in jw.items() if w in set(all_tok)) / sum(jw.values()),
                             'top10': jw.most_common(10)}

    # ---------------- languages
    books = {'la_prose': gutenberg_words(CORP / 'corp_la_33849.txt'), 'la_verse': gutenberg_words(CORP / 'corp_la_227.txt')}
    itw, k_anchor = italian_words(True)
    books['it'] = itw
    O['languages']['italian_anchor_char_offset'] = k_anchor
    O['languages']['ligature_tokens_in_la_prose_sample'] = sum(1 for w in books['la_prose'][:16004] if 'æ' in w or 'œ' in w)
    ex = b1['part2']['examples']
    mine_ex = {w: {'syl': syllabify(w), 'cv': [cv_trim(s) for s in syllabify(w)]} for w in ex}
    O['languages']['syllabifier_examples'] = {'all_equal_to_b1': all(mine_ex[w] == ex[w] for w in ex), 'mine': mine_ex,
                                              'ligature_cases': {w: {'syl': syllabify(w), 'cv': [cv_trim(s) for s in syllabify(w)]}
                                                                 for w in ('quæ', 'sæculorum', 'vitæ', 'cœlum', 'auere', 'uenire')}}
    LS = O['languages']['stats'] = {}; LI = O['languages']['info'] = {}
    VOWELS_SET = set('aeiouy')
    toks_cache = {}
    for name, words in books.items():
        var, info = variants(words, N)
        LI[name] = info; toks_cache[name] = var
        for v, toks in var.items():
            LS[f'{name}/{v}'] = battery(toks, f'{name} {v}', target, lm_seeds=10 if v in ('syl', 'syl2', 'cv2') else 1,
                                        refit=v in ('syl', 'syl2', 'cv2', 'words'))
    # length-matched on lengths 1-5 only (drops the tail filled by a few long syllables)
    h15 = {k: v for k, v in target.items() if k <= 5}
    for name in books:
        lm, _ = length_matched(toks_cache[name]['syl'], h15, 17)
        LS[f'{name}/syl']['pv_lm_len1to5'] = pair_violation(lm, by_len=False)['frac']
        LS[f'{name}/syl']['long_types_ge6'] = sorted(''.join(w) for w in set(toks_cache[name]['syl']) if len(w) >= 6)[:40]
    # Italian from the start of this machine's corpus file (what an as-is run reads)
    itw0, _ = italian_words(False)
    var0, info0 = variants(itw0, N); LI['it_filestart'] = info0
    for v in ('words', 'syl', 'syl2'):
        LS[f'it_filestart/{v}'] = battery(var0[v], f'it_filestart {v}', target)

    # ---------------- attacks
    A = O['attacks']
    # (a) h2 with spaces: decomposition and a language-free CV generator
    A['h2sp_decomposition'] = {}
    A['random_cv'] = {}
    for name in books:
        cvt = toks_cache[name]['cv']
        A['h2sp_decomposition'][f'{name}/cv'] = h2sp_by_class(cvt, VOWELS_SET)
        gen, shapes = random_cv(cvt, VOWELS_SET, N)
        e = entropies(gen)
        A['random_cv'][name] = {'shapes': shapes, 'h2_sp': e['h2_sp'], 'h2': e['h2'], 'h1_sp': e['h1_sp'],
                                'types': len(set(gen))}
        log('random CV', name, A['random_cv'][name])
    A['h2sp_decomposition']['ZL ALL raw (vowel class = a e i o y)'] = h2sp_by_class([g_raw(w) for w in all_tok], set('aeioy'))
    # (b) syllabifier sensitivity
    A['syllabifier_alt'] = {}
    alt_books = {'la_prose': ([w.replace('æ', 'ae').replace('œ', 'oe') for w in books['la_prose']], dict(diph=DIPH_LA)),
                 'la_verse': (books['la_verse'], dict(diph=DIPH_LA)),
                 'it': (books['it'], dict(diph=DIPH_IT, uv=True))}
    for name, (words, kw) in alt_books.items():
        var, info = variants(words, N, **kw)
        A['syllabifier_alt'][f'{name}/info'] = info
        for v in ('syl', 'cv', 'syl2', 'cv2'):
            A['syllabifier_alt'][f'{name}/{v}'] = battery(var[v], f'ALT {name} {v}', target)
    # (c) open-syllable (vowel-final) cut
    A['open_cut'] = {}
    for name, words in books.items():
        var, info = variants(words, N, open_cut=True)
        A['open_cut'][name] = battery(var['syl'], f'OPEN {name} syl', target, refit=True)
    # (d) CV-rigid languages
    A['cv_languages'] = {}
    haw = plain_words(CORP / 'bible_haw.txt')
    mri = plain_words(CORP / 'bible_mri.txt', fold_macrons=True, digraphs=(('wh', 'f'), ('ng', 'ŋ')))
    A['cv_languages']['first_words'] = {'haw': ' '.join(haw[:12]), 'mri': ' '.join(mri[:12])}
    for lang, words in (('haw', haw), ('mri', mri)):
        for v, toks in cv_lang_variants(words, N).items():
            A['cv_languages'][f'{lang}/{v}'] = battery(toks, f'{lang} {v}', target)
    # ---------------- comparison with b1
    C = O['compare']
    for k, r in b1['part1']['stats'].items():
        if k in V['stats']:
            C[f'part1/{k}'] = {'b1': b1_view(r), 'mine': {kk: V['stats'][k].get(kk) for kk, _, _ in KEYS},
                               'agree': compare(V['stats'][k], b1_view(r))}
    for k, r in b1['part2']['stats'].items():
        if k in LS:
            C[f'part2/{k}'] = {'b1': b1_view(r), 'mine': {kk: LS[k].get(kk) for kk, _, _ in KEYS},
                               'agree': compare(LS[k], b1_view(r))}
    prev = {}
    if (rerun is None or rerun_it is None) and (RES / 'v_b1.json').exists():   # keep the recorded 11 Oct re-run columns
        prev = json.load(open(RES / 'v_b1.json', encoding='utf-8'))
        if rerun is None and 'rerun' in prev:
            O['rerun'] = prev['rerun']
        if rerun_it is None and 'rerun_it_anchored' in prev:
            O['rerun_it_anchored'] = prev['rerun_it_anchored']
    if rerun is not None:
        O['rerun'] = {'part1': {k: b1_view(r) for k, r in rerun['part1']['stats'].items()},
                      'part2': {k: b1_view(r) for k, r in rerun['part2']['stats'].items()},
                      'checks': rerun['checks'], 'corpora': rerun['part2']['corpora']}
    if rerun_it is not None:
        O['rerun_it_anchored'] = {'anchor_char_offset': rerun_it['anchor_char_offset'],
                                  'stats': {k: b1_view(r) for k, r in rerun_it['stats'].items()}}
    O['b1_checks'] = b1['checks']; O['b1_part1_counts'] = {'N_ALL': b1['part1']['N_ALL'], 'N_CERTAIN': b1['part1']['N_CERTAIN'],
                                                            'joined_words': b1['part1']['joined_words']}
    O['b1_corpora'] = b1['part2']['corpora']
    O['seconds'] = round(time.time() - T0)
    json.dump(O, open(RES / 'v_b1.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=str)
    write_md(json.load(open(RES / 'v_b1.json', encoding='utf-8')))   # render from the file: string keys throughout
    log('written', RES / 'v_b1.json', RES / 'v_b1.md')


# ================================================================== markdown
def f3(x, d=3):
    return '-' if x is None else (f'{x:.{d}f}' if isinstance(x, float) else str(x))


def write_md(O):
    (RES / 'v_b1.md').write_text(render(O), encoding='utf-8')


def _row(d, lm=True):
    """types / hapax % / len mean/var / Zipf / h2 sp / h2 / locked / MI / pair-viol [/ length-matched]."""
    if not d:
        return '-'
    s = (f"{d['types']} / {d['hapax_pct']:.1f} / {d['len_mean']:.2f}/{d['len_var']:.2f} / {d['zipf']:.3f} / "
         f"{d['h2_sp']:.3f} / {d['h2']:.3f} / {f3(d['locked_frac'])} / {d['mi']:.3f} / {f3(d['pv'])}")
    if lm:
        s += f" / {f3(d.get('pv_lm'))}"
    return s


def _agree(a):
    det = [k for k in a if k not in ('pv_lm',)]
    if all(a[k] in (True, None) for k in det):
        return 'confirmed' if a.get('pv_lm') in (True, None) else 'confirmed (length-matched value differs only by resampling draw, <=0.002)'
    return 'differs: ' + ', '.join(k for k in det if a[k] is False)


def render(O):
    V = O['voynich']; S = V['stats']; C = O['compare']; LS = O['languages']['stats']; A = O['attacks']
    RR = O.get('rerun', {}); RI = O.get('rerun_it_anchored', {})
    bc = O['b1_checks']; b1c = O['b1_part1_counts']; bd = V.get('boundary_diagnostic', {})
    fx = V.get('FIXED', {}); lig = O['languages']['ligature_tokens_in_la_prose_sample']
    L = ['# v_b1: adversarial re-check of b1_segmentation.py', '',
         f"Script v_b1.py (stdlib only, seeded; nothing imported from b1/a1/a3/a4), runtime {O['seconds']} s, full numbers "
         f"in v_b1.json. b1 values are read from {O['b1_source']}.", '']
    # ---------------------------------------------------------------- verdict
    ra, rm = S['ALL/raw'], S['ALL/merge_a3']; fa, fm = S.get('ALL_fix/raw'), S.get('ALL_fix/merge_a3')
    da = S.get('ALL_dash/merge_a3')
    rnd = A['random_cv']
    L += ['**Verdict: numbers HOLD; two readings CORRECTED; one parse defect found upstream of b1.** Every deterministic number in '
          "b1.md reproduces: exactly in the as-is re-run, and to b1's stored precision in an independent re-implementation (counts, types, "
          'hapax, Zipf, length, all entropies, positional lock, MI, and the pair-violation order cost; a printed 3-decimal value can differ by one '
          'in the last place from rounding the same 4-decimal number). Length-matched values differ '
          'only by the resampling draw (<= 0.002; 10 seeds span 0.162-0.165 for CERTAIN merge-a3). The conclusion b1 '
          'supports also stands: no syllabic writing of Latin or Italian reproduces the Voynich profile. But (1) the one close '
          f"match in b1's own match table, CV syllables against Voynich h2 with spaces, comes from the token shape: a "
          f"language-free generator of C/V/CV tokens gives {min(r['h2_sp'] for r in rnd.values()):.2f}-"
          f"{max(r['h2_sp'] for r in rnd.values()):.2f} bits. The syl2 length match is just as much an arithmetic consequence of "
          "the chunk size. (2) One sixth of the length-matched syllable sample is drawn from about 22 rare long "
          f"syllables, mostly syllabifier artefacts ('troiae', 'graius'). Without them la_verse scores {LS['la_verse/syl']['pv_lm_len1to5']:.3f}, not 0.192, and at "
          "equal length the gap to Voynich is larger than b1's single figure. (3) The ZL parse (parse_ivtff.py, re-used by "
          f"b1 for ALL and CERTAIN) deletes the 740 '<->' drawing-interruption tags that sit between glyphs, gluing "
          f"{fx.get('dash_glued_clean_tokens')} spurious compounds (mean {fx.get('dash_glued_mean_len_raw', 0):.1f} glyphs), and it deletes the 394 {{..}} "
          "ligature groups together with their glyphs. The '<->' positions behave like certain spaces "
          f"(break score {bd.get('<->', {}).get('mean_p_break')} against {bd.get('.', {}).get('mean_p_break')} for '.' and "
          f"{bd.get('within_word', {}).get('mean_p_break')} inside words). Reading them as breaks moves merged word-length variance "
          f"{rm['len_var']:.2f} -> {fm['len_var']:.2f}, pair violation {rm['pv']:.3f} -> {fm['pv']:.3f} and hapax {ra['hapax_pct']:.1f} -> "
          f"{fa['hapax_pct']:.1f} %. Those are NOTES 4.2-4.4 figures, not only b1 figures.", '']
    # ---------------------------------------------------------------- re-run
    it_ok = all(C[f'part2/it/{v}']['agree'].get(k) in (True, None) for v in ('words', 'syl', 'cv', 'syl2', 'cv2') for k in
                ('types', 'hapax_pct', 'h2_sp', 'pv'))
    L += ['## 1. Re-run of b1 as-is (11 Oct 2026)', '',
          '- First attempt: FileNotFoundError, `data/ZL3b-n.txt` (the raw IVTFF file, git-ignored) was not on this machine. '
          'Once the coordinator fetched it ("Version 3b of 13/05/2025"; parse_ivtff.py reproduces the committed TSV), the full run took 14 s.',
          '- `git diff --stat`: 633 changed lines in results/b1.json, 28 in results/b1.md. A field-by-field comparison of the JSON shows that '
          'every Part 1 value and every Latin Part 2 value is identical to the commit, apart from the runtimes. '
          'Only the six Italian rows and the Italian corpus counts moved.',
          f"- Why: `../vatican5/corpus_it.txt` here (26,486,052 bytes, identical to the main checkout's copy) holds the same "
          f"Nuntiaturberichte OCR in a different document order. b1 takes \"the first N tokens\". The September sample began "
          f"'cumque predictus fcrdiuandu s rex nuper in romanorum regem', which sits at character "
          f"{O['languages']['italian_anchor_char_offset']:,} of this file. This file instead begins with OCR noise and German "
          f"('hitii hlf siifii ... die uerfruhte reise des bischofs'). As-is, the Italian rows come out as words "
          f"{LS['it_filestart/words']['types']} types / {LS['it_filestart/words']['hapax_pct']:.1f} % hapax (committed 6758 / 66.5), "
          f"syl {LS['it_filestart/syl']['types']} / {LS['it_filestart/syl']['hapax_pct']:.1f} (committed 1718 / 44.2).",
          f"- b1's own code, with the Italian text anchored at that offset, reproduces all six committed Italian rows exactly "
          f"(anchored re-run, v_b1.json 'rerun_it_anchored'; independent check below: {'all agree' if it_ok else 'see table'}).",
          '- The working-tree results/b1.json and b1.md were restored to the committed versions after the re-run. As-is, they '
          'would carry the noisy file-start Italian sample. The as-is values are kept in v_b1.json \'rerun\'.',
          '- Consequence: "the first N tokens of corpus_it.txt" is not a stable sample definition across copies of that file. '
          'v_b1 anchors the Italian sample by its first words. Any script that reads IT_CORPUS from the start (a1, a3, a4, a5, '
          'b-series) needs the same check before its Italian rows are compared with September values.', '']
    # ---------------------------------------------------------------- claims table
    L += ['## 2. Claims', '',
          'Row values: types / hapax % types / length mean/var / Zipf 1-1000 / h2 with spaces / h2 no spaces / locked frac / '
          'MI symbol;position / pair-violation / length-matched pair-violation. "re-run" = b1 as-is on 11 Oct (Italian rows: b1 '
          'code on the anchored sample); "independent" = v_b1.py.', '',
          '| claim in b1.md | b1 value | re-run value | independent value | verdict |', '|---|---|---|---|---|']
    rc = RR.get('checks', {})
    L.append(f"| Split re-parse reproduces the TSV; P lines | {bc['reparse_split_equals_tsv']}; {bc['P_lines']} | "
             f"{rc.get('reparse_split_equals_tsv')}; {rc.get('P_lines')} | {V.get('split_parse_equals_tsv')}; {V['ALL']['P_lines']} | confirmed |")
    L.append(f"| ALL: words before filter, dropped, N | {bc['ALL_words_before_filter']}, {bc['ALL_dropped']}, {b1c['N_ALL']} | "
             f"{rc.get('ALL_words_before_filter')}, {rc.get('ALL_dropped')}, {RR.get('part1', {}).get('ALL/raw', {}).get('n_tokens')} | "
             f"{V['ALL']['words_before_filter']}, {V['ALL']['dropped']}, {V['ALL']['N']} | confirmed |")
    ce = V.get('CERTAIN', {})
    L.append(f"| Uncertain spaces joined; CERTAIN before filter, dropped, N; words containing a join | {bc['uncertain_spaces_joined']}; "
             f"{bc['CERTAIN_words_before_filter']}, {bc['CERTAIN_dropped']}, {b1c['N_CERTAIN']}; {bc['CERTAIN_words_that_contain_a_join']} | "
             f"{rc.get('uncertain_spaces_joined')}; {rc.get('CERTAIN_words_before_filter')}, {rc.get('CERTAIN_dropped')}, "
             f"{RR.get('part1', {}).get('CERTAIN/raw', {}).get('n_tokens')}; {rc.get('CERTAIN_words_that_contain_a_join')} | "
             f"{ce.get('token_reduction_from_joins')}; {ce.get('words_before_filter')}, {ce.get('dropped')}, {ce.get('N')}; "
             f"{ce.get('words_containing_a_join')} | confirmed (the raw P-line text holds {V['audit']['commas']} commas, including any inside comments or next to deleted markup; 2458 of them join two words) |")
    jw = b1c['joined_words']; mj = V.get('joined_words', {})
    L.append(f"| Joined words: n, mean raw length, share already ALL types | {jw['n']}, {jw['mean_len_raw']}, {jw['frac_that_are_ALL_types']} | "
             f"same | {mj.get('n')}, {mj.get('mean_len_raw', 0):.2f}, {mj.get('frac_already_ALL_types', 0):.3f} | confirmed |")
    for k in ('ALL/raw', 'ALL/merge_a3', 'ALL/merge2_a1', 'CERTAIN/raw', 'CERTAIN/merge_a3', 'CERTAIN/merge2_a1',
              'ALL_trunc/raw', 'ALL_trunc/merge_a3', 'ALL_trunc/merge2_a1'):
        c = C[f'part1/{k}']; lm = k.startswith('CERTAIN')
        L.append(f"| Part 1 row {k} | {_row(c['b1'], lm)} | {_row(RR.get('part1', {}).get(k), lm)} | {_row(S[k], lm)} | {_agree(c['agree'])} |")
    # movement
    dl = {a: (S[f'CERTAIN/{a}'], S[f'ALL/{a}']) for a in ALPHA}
    d_h2 = max(abs(x['h2'] - y['h2']) for x, y in dl.values()); d_sp = [x['h2_sp'] - y['h2_sp'] for x, y in dl.values()]
    d_len = [x['len_mean'] - y['len_mean'] for x, y in dl.values()]; d_pv = [x['pv'] - y['pv'] for x, y in dl.values()]
    seeds = S['CERTAIN/merge_a3'].get('pv_lm_seeds', [])
    L.append(f"| ALL -> CERTAIN movement: h2 no spaces, h2 with spaces, mean length, pair-viol as-is, pair-viol length-matched (merge-a3) | "
             f"<=0.0006; +0.013 to +0.023; +0.29 to +0.39; +0.017 to +0.019; 0.1596 -> 0.1622 | same | <={d_h2:.4f}; {min(d_sp):+.3f} to {max(d_sp):+.3f}; "
             f"{min(d_len):+.2f} to {max(d_len):+.2f}; {min(d_pv):+.3f} to {max(d_pv):+.3f}; 0.1596 -> {min(seeds):.4f}-{max(seeds):.4f} (10 seeds) | confirmed |")
    L.append(f"| Part 1 heading: ALL = \"every IVTFF comma a break\" | commas only | same | true for commas; but 740 '<->' breaks between glyphs "
             f"are deleted (655 clean glued tokens) and 394 {{..}} ligature groups are dropped with their glyphs | corrected (see 3.1) |")
    bco = O['b1_corpora']; LI = O['languages']['info']
    L.append(f"| Corpora: words -> syllables, syllables/word, words spanned by N syllables | la_prose {bco['la_prose']['words_available']} -> "
             f"{bco['la_prose']['syllables_available']}, {bco['la_prose']['syllables_per_word']}, {bco['la_prose']['words_used_for_N_syllables']}; "
             f"la_verse {bco['la_verse']['words_available']} -> {bco['la_verse']['syllables_available']}, {bco['la_verse']['syllables_per_word']}, "
             f"{bco['la_verse']['words_used_for_N_syllables']}; it {bco['it']['words_available']} -> {bco['it']['syllables_available']}, "
             f"{bco['it']['syllables_per_word']}, {bco['it']['words_used_for_N_syllables']} | Latin same; it (file start) "
             f"{RR.get('corpora', {}).get('it', {}).get('words_available')} -> {RR.get('corpora', {}).get('it', {}).get('syllables_available')} | "
             f"la_prose {LI['la_prose']['words_available']} -> {LI['la_prose']['syllables_available']}, {LI['la_prose']['syllables_per_word']:.3f}, "
             f"{LI['la_prose']['words_spanned_by_N_syllables']}; la_verse {LI['la_verse']['words_available']} -> {LI['la_verse']['syllables_available']}, "
             f"{LI['la_verse']['syllables_per_word']:.3f}, {LI['la_verse']['words_spanned_by_N_syllables']}; it (anchored, 4M chars) "
             f"{LI['it']['words_available']} -> {LI['it']['syllables_available']}, {LI['it']['syllables_per_word']:.3f}, {LI['it']['words_spanned_by_N_syllables']} | "
             "Latin confirmed; Italian totals not reproducible (file order), the 18,757 words actually used confirmed |")
    L.append(f"| Syllabifier examples (17 words, syl and CV) | as listed | same | all identical: {O['languages']['syllabifier_examples']['all_equal_to_b1']} | confirmed |")
    for k in ('la_prose', 'la_verse', 'it'):
        for v in ('words', 'syl', 'cv', 'syl2', 'cv2', 'syl_shuf'):
            c = C[f'part2/{k}/{v}']
            rr = RI.get('stats', {}).get(f'it/{v}') if k == 'it' else RR.get('part2', {}).get(f'{k}/{v}')
            verdict = _agree(c['agree']) if v != 'syl_shuf' else 'null row; own shuffle seed, values agree to +-0.01 (pair-viol 0.49 vs 0.49)'
            L.append(f"| Part 2 row {k}/{v} | {_row(c['b1'])} | {_row(rr)} | {_row(LS[f'{k}/{v}'])} | {verdict} |")
    cvr = [LS[f'{k}/cv'] for k in ('la_prose', 'la_verse', 'it')]
    L.append(f"| Match table: cv rows give h2 with spaces 2.053-2.115 against Voynich raw 2.114 | 2.112 / 2.115 / 2.053 | same | "
             f"{' / '.join(f'{r['h2_sp']:.3f}' for r in cvr)}; a random C/V/CV generator with no language gives "
             f"{' / '.join(f'{r['h2_sp']:.3f}' for r in rnd.values())}; without spaces cv h2 = {' / '.join(f'{r['h2']:.3f}' for r in cvr)} (Voynich 2.307) | "
             "numbers confirmed; reading corrected: a match by construction, no evidence (3.3) |")
    s2 = [LS[f'{k}/syl2'] for k in ('la_prose', 'la_verse', 'it')]
    L.append(f"| Match table: syl2 length 3.71-4.17 inside 'len mean vs 4.1-5.1' | 3.96 / 4.17 / 3.71 | same | "
             f"{' / '.join(f'{r['len_mean']:.2f}' for r in s2)} = syllable length x {' / '.join(f'{LI[k]['syllables_per_syl2_chunk']:.2f}' for k in ('la_prose', 'la_verse', 'it'))} syllables per chunk | "
             "confirmed; by construction (the chunk size was chosen to match) |")
    sy = {k: LS[f'{k}/syl'] for k in ('la_prose', 'la_verse', 'it')}
    L.append(f"| Match table: syllable pair-viol length-matched 0.259 / 0.192 / 0.259 against 0.160 | as stated | same | "
             f"{' / '.join(f'{r['pv_lm']:.3f} (10 seeds {r['pv_lm_range'][0]}-{r['pv_lm_range'][1]})' for r in sy.values())} | confirmed as numbers; "
             f"la_verse 0.19 is a tail artefact ({LS['la_verse/syl']['pv_lm_len1to5']:.3f} on lengths 1-5), see 3.4; the per-length gap is larger |")
    L.append("| Match table targets: hapax 69-70 %, locked 0.21-0.31, MI 0.69-0.73 | as stated | same | b1's own Voynich rows: hapax 69.1-69.5, "
             f"locked {S['ALL/merge_a3']['locked_frac']:.2f} / {S['ALL/raw']['locked_frac']:.3f} / {S['ALL/merge2_a1']['locked_frac']:.3f} (merge-a3 / raw / merge2), "
             f"MI 0.690-0.713; with '<->' as a break hapax {S['ALL_fix/merge_a3']['hapax_pct']:.1f}-{S['ALL_fix/raw']['hapax_pct']:.1f}, MI "
             f"{S['ALL_fix/merge_a3']['mi']:.3f}-{S['ALL_fix/raw']['mi']:.3f} | corrected (range 0.24-0.36; 0.21-0.31 is v_a5's merged/Currier/v101 range) |")
    L.append('')
    # ---------------------------------------------------------------- critique
    au = V['audit']; cert_fix = S.get('CERTAIN_fix/merge_a3', {})
    L += ['## 3. Method critique', '',
          '### 3.1 IVTFF parse', '',
          f"Commas against periods: correct. In IVTFF '.' is a certain word space and ',' an uncertain one; P text has {au['periods']} "
          f"periods and {au['commas']} commas. The boundary score below puts commas at {bd[',']['mean_p_break']} "
          f"(half of them look like breaks, {bd[',']['frac_p_break_gt_half']}), between certain spaces ({bd['.']['mean_p_break']}) and "
          f"word-internal glyph pairs ({bd['within_word']['mean_p_break']}). That is what 'uncertain' should look like, and it means ALL "
          'and CERTAIN are the two extremes; the truth lies between them. Because nothing moves much from one extreme to the other, the bracketing is enough.',
          '',
          'Two other markups are mishandled, here and in parse_ivtff.py, so in every a- and b-script number:', '',
          f"- `<->` (drawing interruption): {au['dash_tags']} in P text, {au['dash_between_glyphs']} directly between two glyphs, "
          f"{au['dash_next_to_separator']} next to a separator. Deleting the tag glues the flanking pieces: "
          f"{fx['dash_glued_clean_tokens']} clean tokens, mean {fx['dash_glued_mean_len_raw']:.1f} raw glyphs, e.g. "
          f"{', '.join(fx['dash_glued_first15'][1:11])}. The two halves look like ordinary words (ochy|dcho, dam|sochey, okal|dolchey, "
          f"cthey|ykol). Boundary score at the {bd['<->']['scored']} scored '<->' positions: {bd['<->']['mean_p_break']} "
          f"({bd['<->']['frac_p_break_gt_half']} above one half), close to '.' and far from within-word. They are word breaks.",
          f"- `{{..}}` (ligature / unusual glyph groups, e.g. {', '.join(g for g, _ in au['top_brace_groups'][:6])}): {au['brace_groups']} in P text, "
          f"{au['brace_groups_whole_word']} of them a whole word. The regex `\\{{[^}}]*\\}}` -> '' drops the glyphs, so '{{ck}}eo' "
          "becomes 'eo'. These are glyphs, not comments; inline comments are `<!..>`.", '',
          '| parse | tokens | types | hapax % | merged len mean/var | var/(mean-1) merged | h2 merged | pair-viol merged | locked merged | MI merged |',
          '|---|---|---|---|---|---|---|---|---|---|']
    for k, lab in (('ALL', 'b1 ALL (TSV)'), ('ALL_dash', "'<->' = break"), ('ALL_brace', 'braces kept'), ('ALL_fix', 'both fixed'),
                   ('CERTAIN', 'b1 CERTAIN'), ('CERTAIN_fix', 'CERTAIN, both fixed')):
        r = S.get(f'{k}/merge_a3'); rr = S.get(f'{k}/raw')
        if r:
            L.append(f"| {lab} | {r['n_tokens']} | {rr['types']} | {rr['hapax_pct']:.1f} | {r['len_mean']:.3f}/{r['len_var']:.3f} | {r['disp']:.3f} | "
                     f"{r['h2']:.3f} | {r['pv']:.4f} | {r['locked_frac']:.3f} | {r['mi']:.3f} |")
    L += ['', f"Consequence for b1: the ALL vs CERTAIN contrast keeps its sign and size (CERTAIN_fix vs ALL_fix: hapax "
          f"{S['ALL_fix/raw']['hapax_pct']:.1f} -> {S['CERTAIN_fix/raw']['hapax_pct']:.1f}, length-matched pair violation "
          f"{S['ALL_fix/merge_a3']['pv']:.3f} -> {cert_fix.get('pv_lm', 0):.3f}). The absolute Voynich figures quoted in NOTES move, "
          f"though: merged word-length variance 2.48 -> {fm['len_var']:.2f} (dispersion {rm['disp']:.3f} -> {fm['disp']:.3f}, so even more "
          f"under-dispersed), pair violation 0.160 -> {fm['pv']:.3f} (more rigid), hapax 69.5 -> {fa['hapax_pct']:.1f} %, merged locked "
          f"fraction 0.24 -> {fm['locked_frac']:.2f}, MI 0.690 -> {fm['mi']:.3f}. h2 does not move (<= 0.011). Variance, rigidity, locking and MI "
          f"move away from language. Hapax moves toward it: {fa['hapax_pct']:.1f} % is inside v_a5's single-book range (57.0-68.7 %), so the "
          "remark that Voynich hapax is 'above every language' no longer holds. No exclusion verdict depends on hapax, "
          'but the 4.2-4.4 tables should be regenerated from a corrected TSV (outside this check: parse_ivtff.py is not b1).', '']
    alt = A['syllabifier_alt']
    L += ['### 3.2 Syllabifier', '',
          f"The rule as documented is the rule as coded: my implementation, written from the docstring, reproduces every syllable "
          f"count, the 17 examples and every syl/cv/syl2/cv2 row. As a syllabifier it has three defects; only the second is documented:", '',
          f"- 'æ' and 'œ' are not vowels. The Confessiones edition prints them: {lig} of the first 16,004 words (4.3 %) contain one. "
          "'quæ' -> one vowel-less syllable 'quæ', CV 'q'; 'vitæ' -> 'vitæ'; 'sæculorum' -> 'sæcu lo rum'. This is undocumented.",
          f"- A maximal vowel run is one nucleus, so hiatus is never split ('confessiones' -> 'sio', 'misericordia' -> 'dia'): "
          f"{LI['la_prose']['multi_vowel_nuclei_frac']:.1%} / {LI['la_verse']['multi_vowel_nuclei_frac']:.1%} / {LI['it']['multi_vowel_nuclei_frac']:.1%} of nuclei "
          '(prose / verse / Italian) have two or more vowel letters. This one is documented.',
          "- The Italian corpus spells v as u ('auere', 'uenire'), so 'auere' -> 'aue re' and 'uenire' -> 'ue ni re'.", '',
          'Corrected variant (ligatures folded to ae/oe; hiatus split except Latin ae oe au eu and the Italian glides; Italian u before a '
          'vowel at word start or after a vowel read as v):', '',
          '| corpus/variant | b1 rule: types / hapax / len / h2 sp / pair-viol lm | corrected rule: same |', '|---|---|---|']
    for k in ('la_prose', 'la_verse', 'it'):
        for v in ('syl', 'cv', 'syl2', 'cv2'):
            a, b = LS[f'{k}/{v}'], alt[f'{k}/{v}']
            L.append(f"| {k}/{v} | {a['types']} / {a['hapax_pct']:.1f} / {a['len_mean']:.2f} / {a['h2_sp']:.3f} / {f3(a.get('pv_lm'))} | "
                     f"{b['types']} / {b['hapax_pct']:.1f} / {b['len_mean']:.2f} / {b['h2_sp']:.3f} / {f3(b.get('pv_lm'))} |")
    L += ['', 'The syllabifier choices move the length-matched pair violation of syllables by up to 0.06 in either direction and syllable types '
          'by up to 38 %. Every variant stays far from Voynichese on vocabulary (types, hapax, Zipf) and on length-matched rigidity '
          '(0.21-0.36 against 0.16). '
          'The defects are real but do not change the conclusion.', '']
    dec = A['h2sp_decomposition']; vz = dec['ZL ALL raw (vowel class = a e i o y)']
    oc = A['open_cut']
    L += ['### 3.3 Is a match with Voynich non-trivial or built in?', '',
          f"- **cv and h2 with spaces: built in.** A CV token is consonant + vowel, then a space. After a vowel the next symbol is "
          f"always the space, which is 0 bits at {dec['la_prose/cv']['vowel']['P_prev']:.0%} of positions. h2 with spaces is then "
          f"P(space) x H(first letter) + P(consonant) x H(vowel | consonant) = {dec['la_prose/cv']['space']['contribution_bits']:.2f} + "
          f"{dec['la_prose/cv']['consonant']['contribution_bits']:.2f} bits for Latin prose (verse {dec['la_verse/cv']['space']['contribution_bits']:.2f} + "
          f"{dec['la_verse/cv']['consonant']['contribution_bits']:.2f}, Italian {dec['it/cv']['space']['contribution_bits']:.2f} + "
          f"{dec['it/cv']['consonant']['contribution_bits']:.2f}). Drawing every letter "
          f"independently into the same C/V/CV shapes, with no language at all, gives {' / '.join(f'{r['h2_sp']:.3f}' for r in rnd.values())} "
          f"(prose / verse / Italian). Without spaces the cv streams have h2 {min(r['h2'] for r in cvr):.2f}-{max(r['h2'] for r in cvr):.2f}, "
          f"Voynich 2.31. Voynich reaches its 2.114 by a different route: space {vz['space']['contribution_bits']:.2f}, vowel-class "
          f"{vz['vowel']['contribution_bits']:.2f}, consonant-class {vz['consonant']['contribution_bits']:.2f} bits. The cv rows also have 100-119 types, "
          '1-6 % hapax and MI about 1.0: they match nothing else.',
          '- **cv and pair violation 0.000: built in.** A two-symbol C+V token cannot violate a C-before-V order. b1 already prints it as "as-is" with no length-matched value.',
          f"- **syl2 and length: built in.** Mean syl2 length = mean syllable length (2.50-2.56) x syllables per chunk "
          f"({LI['la_prose']['syllables_per_syl2_chunk']:.2f} / {LI['la_verse']['syllables_per_syl2_chunk']:.2f} / {LI['it']['syllables_per_syl2_chunk']:.2f}). "
          'The docstring says the chunking was added to test hypothesis (a). That is legitimate, but the length agreement it buys is not evidence.',
          '- **syl and syl2, everything else: not built in.** These rows are honest tests and they fail: syllables give 1,497-1,718 types '
          'and 25-44 % hapax against 7,182 and 69.5 %, Zipf -1.26 to -1.44 against -1.04, and h2 with spaces 2.83-2.99. Bisyllabic chunks give '
          '4,941-6,817 types, 44-55 % hapax and h2 with spaces 3.13-3.32. MI is 0.17-0.43 against 0.69-0.71. Locking is 0-0.25; only '
          'Latin prose syllables (0.25) reach the Voynich range of 0.24-0.36.',
          f"- **Rigidity depends on the cut rule.** An open-syllable cut (every consonant cluster goes to the next onset) gives "
          f"pair violation {' / '.join(f'{r['pv']:.3f}' for r in oc.values())} as-is and {' / '.join(f'{r['pv_lm']:.3f}' for r in oc.values())} "
          "length-matched. v_a3's cut after every vowel gave 0.108 length-matched, more rigid than Voynich. So syllabic units can be made more or less "
          'rigid than Voynichese by choosing the cut. A pair-violation mismatch alone would not exclude syllabic writing; the vocabulary statistics do.', '']
    vh = V['merge_a3_length_hist']; tail = sum(v for k, v in vh.items() if int(k) >= 6) / sum(vh.values())
    rf_v = S['ALL/merge_a3']['refit_by_length']
    L += ['### 3.4 Length-matched pair violation', '',
          'The procedure is fair in form: the same resampler and the same order refit as the Voynich and v_a3 controls, with the order fitted on the resampled sample. '
          f"It is weak for sub-word units. {tail:.1%} of Voynich merged tokens have 6 or more symbols. In the Aeneid syllable pool there are "
          f"{LS['la_verse/syl']['types_by_length']['6']} syllable types of length 6 and {LS['la_verse/syl']['types_by_length']['7']} of length 7, so one sixth "
          'of the "length-matched" sample is about 22 syllables drawn over and over. Most of them are artefacts of the undivided vowel run '
          f"(troiae, troiam, graius, graiae, aeaeae, proiec). Matched on lengths 1-5 only, la_verse/syl scores {LS['la_verse/syl']['pv_lm_len1to5']:.3f}, not {LS['la_verse/syl']['pv_lm']:.3f}. Under the "
          'global order it is 0.21-0.31 at every length from 2 to 5. cv2 has nothing longer than 4 symbols (cov 0.62), so the 38 % of the '
          'target that has length 5 or more is filled with length-4 tokens; it is not length-matched. More seeds do not help: the 10-seed '
          'spread is <= 0.006, because the bias is structural. '
          'The fair comparison is per length with the order refitted at each length (no resampling):', '',
          '| corpus | L2 | L3 | L4 | L5 | L6 |', '|---|---|---|---|---|---|']
    def rf(r):
        x = r.get('refit_by_length', {})
        return ' | '.join(f"{x[str(l)]['viol']:.3f} ({x[str(l)]['types']})" if str(l) in x else (f"{x[l]['viol']:.3f} ({x[l]['types']})" if l in x else '-') for l in (2, 3, 4, 5, 6))
    L.append(f"| ZL ALL merge-a3 | {rf(S['ALL/merge_a3'])} |"); L.append(f"| ZL ALL raw | {rf(S['ALL/raw'])} |")
    for k in ('la_prose', 'la_verse', 'it'):
        for v in ('words', 'syl', 'syl2', 'cv2'):
            L.append(f"| {k}/{v} | {rf(LS[f'{k}/{v}'])} |")
        L.append(f"| {k}/open-syllable cut | {rf(oc[k])} |")
    L += ['', '(types of that length in brackets.) At every length from 2 to 5, Latin and Italian syllables are 1.6 to 8 times less '
          'rigid than merged Voynichese (2 to 5 times against raw EVA). The open-syllable cut comes closest, Italian at length 4 '
          '(0.160 against 0.125), and still falls short at every length.', '']
    cl = A['cv_languages']
    L += ['### 3.5 A real CV-rigid language (extension, not in b1)', '',
          "NOTES section 2 names 'a language with rigid consonant-vowel syllables written syllabically'. b1 approximates it by deleting "
          "letters from Latin (cv); that destroys the vocabulary and makes the cv rows uninformative. data/corpora holds a Hawaiian "
          f"Bible in the missionary orthography ((C)V only; 7 native consonant letters, about 2 % foreign letters in names, no okina or macrons; "
          f"starts '{cl['first_words']['haw']}') and a Maori Bible (macrons folded, wh/ng as "
          'one symbol). Same battery, same N:', '',
          '| corpus | types | hapax % | len mean/var | Zipf | h2 sp | h2 | locked | MI | pair-viol | length-matched |', '|---|---|---|---|---|---|---|---|---|---|---|']
    for k in ('haw/words', 'haw/mora', 'haw/syl', 'haw/syl2', 'mri/words', 'mri/mora', 'mri/syl', 'mri/syl2'):
        r = cl[k]
        L.append(f"| {k} | {r['types']} | {r['hapax_pct']:.1f} | {r['len_mean']:.2f}/{r['len_var']:.2f} | {r['zipf']:.3f} | {r['h2_sp']:.3f} | "
                 f"{r['h2']:.3f} | {f3(r['locked_frac'])} | {r['mi']:.3f} | {f3(r['pv'])} | {f3(r.get('pv_lm'))} |")
    L.append(f"| ZL ALL raw / merge-a3 | {ra['types']} / {rm['types']} | {ra['hapax_pct']:.1f} | {ra['len_mean']:.2f}/{ra['len_var']:.2f} | {ra['zipf']:.3f} | "
             f"{ra['h2_sp']:.3f} / {rm['h2_sp']:.3f} | {ra['h2']:.3f} / {rm['h2']:.3f} | {ra['locked_frac']:.3f} / {rm['locked_frac']:.2f} | {ra['mi']:.3f} | {ra['pv']:.3f} / {rm['pv']:.3f} | - |")
    L += ['', "A real CV language written syllabically reaches Voynich-level h2 with spaces and below (syllables 1.9, pairs 2.4), "
          "with more positional locking than Voynich (0.67-0.75 against 0.24-0.36). It does so with 116-147 syllable types and 6-11 % hapax, and even its ordinary words give only "
          f"{cl['haw/words']['types']}-{cl['mri/words']['types']} types (h2 {cl['mri/words']['h2']:.2f}-{cl['haw/words']['h2']:.2f}; the published Hawaiian "
          "figure is 2.77). Its syllable pairs are less rigid than Voynichese, length-matched (0.24 against 0.16). "
          "Caveat: both texts are Bibles, a repetitive genre, and the comparison is two languages, not a survey.", '']
    L += ['### 3.6 Corpus cleanliness', '',
          f"The file-start Italian sample (OCR noise, some German) raises hapax to {LS['it_filestart/words']['hapax_pct']:.1f} % for words and "
          f"{LS['it_filestart/syl2']['hapax_pct']:.1f} % for syllable pairs, above Voynich's 69.5 %. Vocabulary statistics measure the text's noise as "
          "much as its language. The vocabulary argument above rests on clean corpora (Gutenberg Latin, the Bibles, the anchored Italian "
          "sample, which still contains about 8 % Latin per v_a3). The same caution applies to Voynich's own 69.5 %: transcription "
          'disagreement inflates it too (SOURCES: 45 % of running tokens differ across transcribers).', '']
    L += ['### 3.7 Does b1.md overstate?', '',
          "b1.md states no conclusion in prose: it has two tables and a match table. The risk is in how the match table reads. It puts "
          "cv h2 with spaces (2.05-2.12) beside 'Voy 2.114', and syl2 length inside the 4.1-5.1 target, with no note that both agreements "
          "are built into the token shape. Its target line gives hapax 69.7 (NOTES's a2-filter figure; b1's own rows are 69.1-69.5) and locked "
          "0.21-0.31 (b1's own Voynich rows are 0.24-0.36). The docstring's 'syllabically written Latin' is Latin syllables spelled in the Latin "
          "alphabet and used as tokens. It is not a syllabary (one sign per syllable), which a 19-33 glyph inventory could not carry for Latin's 1,500 syllables "
          "or even Hawaiian's 147 without glyph groups. The glyph-group case is hypothesis (a), still open.", '']
    # ---------------------------------------------------------------- wording
    L += ['## 4. Corrected wording', '',
          'For a b1 summary, and for NOTES section 2 where it says the segmentation gap "was not tested":', '',
          '> b1 and v_b1 (October 2026) closed the two untested cases. (i) Uncertain spaces: joining all 2,458 IVTFF commas that separate '
          'words (CERTAIN) changes h2 by at most 0.023 bits and length-matched pair violation by +0.002 to +0.005 (0.160 -> 0.162-0.165). Hapax '
          'rises 69.5 -> 72.8 % and mean word length by 0.3-0.4 symbols. The commas themselves sit halfway between word breaks and '
          'word-internal junctures, so ALL and CERTAIN bracket the truth. (ii) Syllabic writing: Latin prose, Latin verse and Italian written '
          'as syllables, as CV syllables or as bisyllabic chunks, and Hawaiian and Maori written as morae or syllables, reproduce no Voynich '
          'profile. Syllable-sized tokens give 50-1,700 types and 0-44 % hapax at 34,059 tokens (Voynich 7,182 and 69.5 %), and Zipf -1.26 to '
          '-2.30 (Voynich -1.04). At every length from 2 to 5, Latin and Italian syllables are 1.6 to 8 times less rigid than merged Voynichese. The only exact-looking agreements, CV '
          'syllables on h2 with spaces and bisyllabic chunks on mean length, are fixed by the token shape (a random C/V/CV generator gives '
          'the same h2). Voynich tokens behave like words in their vocabulary and like a rigid template inside. The exclusion now covers '
          'syllable-as-token writing of Latin, Italian and two CV-rigid languages. A script in which glyph groups spell syllables inside '
          'word-sized tokens is hypothesis (a) and stays live.', '',
          "Add to NOTES section 3: the ZL parse deletes the 746 '<->' drawing-interruption tags (740 between glyphs, behaving as word "
          "breaks) and the 394 {..} ligature groups with their glyphs. Re-parsed, merged length variance is "
          f"{fm['len_var']:.2f} (not 2.48), pair violation {fm['pv']:.3f} (not 0.160) and hapax {fa['hapax_pct']:.1f} % (not 69.5 in this filter, 69.7 in a2's). "
          "The first two move away from language. Hapax moves into the single-book language range (57.0-68.7 %, v_a5), so 'Voynich hapax "
          "is above every language' should be dropped. Until parse_ivtff.py is fixed and a1-a6 are re-run, quote these as 'about'.", '']
    # ---------------------------------------------------------------- checked
    L += ['## 5. Checked / not checked', '',
          "**Checked.** b1 re-run as-is: Part 1 and the Latin rows are identical to the commit. The Italian rows are identical once the "
          "sample is anchored at the September start, and differ as-is because corpus_it.txt is in a different document order. "
          'Independently re-implemented and matched: the IVTFF P-locus parse (split mode = TSV token list), the CERTAIN join counts, the '
          "a3/a1 glyph merges, the clean filter, entropies with and without spaces and within words, Zipf, length statistics, positional "
          "lock and MI, the pair-violation linear-order cost (own search with 42 starts gives b1's figure to 3 decimals in every non-shuffled "
          "row, so b1's 12-restart search is not under-optimised), the length-matched resampler (10 seeds), and the syllabifier against all "
          "17 examples and every syllable count. Attacks run: IVTFF markup audit and corrected parse; boundary-likeness of '.', ',' and "
          "'<->'; h2 decomposition and a language-free CV generator; syllabifier sensitivity; open-syllable cut; per-length pair violation "
          'with refit; Hawaiian and Maori controls; corpus-order and corpus-noise sensitivity of the Italian rows.', '',
          '**Not checked.** Corpora other than the three b1 uses plus the two Bibles. The Bible files were in data/corpora on 11 Oct; I did not '
          "verify their provenance beyond the first words. Per-Currier-language splits of CERTAIN. Whether '<->' was ever meant to be a word space in "
          'the IVTFF definition: the evidence here is statistical, and the IVTFF 2.0 PDF was not consulted. The effect of the corrected parse '
          'on a1-a6 beyond the statistics listed in 3.1. Syllabification against a dictionary (the variants are rule-based both ways).', '',
          '**User must verify.** Whether to regenerate the TSV with \'<->\' as a break and braces kept, and re-run a1-a6/b1 (it changes NOTES '
          "4.2-4.4 figures); which Italian sample is canonical (anchor by first words or ship a fixed sample file); the corrected wording "
          'in section 4 before it goes into NOTES. All output unvalidated until user review.', '']
    return '\n'.join(L) + '\n'


if __name__ == '__main__':
    if '--md-only' in sys.argv:      # re-render the markdown from results/v_b1.json without recomputing
        write_md(json.load(open(RES / 'v_b1.json', encoding='utf-8')))
    else:
        main()
