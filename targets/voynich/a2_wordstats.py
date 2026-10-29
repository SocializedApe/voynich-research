"""a2_wordstats.py -- word-level and positional statistics of Voynichese (ZL3b-n, paragraph text)
versus 5 natural-language samples (Latin, Italian, German, English, Danish).

Pure Python 3.12, no third-party packages.
Outputs: results/a2.json, results/a2.md

METHOD CHOICES (all explicit):
- Voynich text: data/ZL3b-n.words.tsv, locus_type P only. Words containing '?' (unread glyph) or any
  character outside a-z (rare-glyph codes '@nnn;', apostrophes) are dropped; a dropped word still counts
  as a slot for line-position purposes only if it is kept in the line list -- we drop it entirely, so the
  neighbouring words become adjacent (affects <0.3% of words).
- Subsets: ALL (all P lines), A (Currier lang=A), B (lang=B).
- Two Voynich alphabets are used: RAW EVA characters, and MERGED glyphs where the multi-letter EVA
  composites cfh ckh cph cth (gallows-in-bench), iiin, iin, in, eee, ee, ch, sh are each replaced by one
  private symbol (longest match first, left to right). MERGED is the primary alphabet for word length
  and positional tests; RAW numbers are also reported.
- Language corpora: Gutenberg texts, header/footer stripped at '*** START OF' / '*** END OF', lower-cased,
  a word = maximal run of Unicode letters (str.isalpha), digits/punctuation = word breaks. From each book
  the first 2000 words are skipped (title page, translator notes) and an equal share of the sample is taken
  from each book, so that the sample spans several works like the manuscript spans several sections.
  Latin: Aeneid (#227) + Confessiones (#33849); #50280 (bilingual phrase-book) excluded.
  Italian: targets/vatican5/corpus_it.txt (16th-c. nunciature letters, OCR, already lower-cased, no punctuation),
  first 10000 words skipped, then one contiguous sample. It contains OCR errors and some Latin passages.
- Sample size for languages: the same number of tokens as the Voynich subset being compared (ALL, A, B).
- Zipf slope: ordinary least squares of log10(freq) on log10(rank), ranks 1..1000 and 1..5000
  (or up to the number of types if fewer).
- Hapax: fraction of TYPES occurring once, and fraction of TOKENS that are hapax types.
- Word length: L = number of symbols. Binomial ML fit of (L-1) ~ Binom(n,p): for each n >= max(L)-1 up to
  n=40, p_hat = mean(L-1)/n, pick the n maximising the log-likelihood. A chi-square distance and the
  sample skewness are given as goodness-of-fit descriptors.
- Type-token growth: distinct types after the first 5k/10k/20k/N tokens in text order; Heaps exponent =
  OLS slope of log V vs log N at every 1000 tokens.
- Positional test: word position class within a line: START (first word), END (last word), MID (others);
  1-word lines are excluded. Contingency tables (position x first symbol) and (position x last symbol),
  Pearson chi-square with df=(rows-1)(cols-1), p-value from the regularised upper incomplete gamma
  function, Cramer's V = sqrt(chi2/(N*(min(rows,cols)-1))) as the effect size. Symbols with an expected
  count < 5 in any cell are pooled into 'other'. Strongest deviations = largest |standardised residual|
  (obs-exp)/sqrt(exp). Paragraph-initial: first word of a para_start line vs first word of a non-para-start
  line vs all MID words; gallows enrichment = share of words whose first symbol is k,t,p,f (or the merged
  gallows-bench symbols).
- Language positional control: each language sample is cut into pseudo-lines whose word counts are the
  ACTUAL sequence of Voynich P-line word counts (and para_start flags) in manuscript order, so line-length
  and paragraph structure are identical; letters are the symbols. A second control uses the REAL verse
  lines of the Aeneid (Gutenberg line breaks = hexameter lines).
- Repetition: adjacent token pairs in text order (within lines for Voynich, i.e. pairs spanning a line break
  are not counted; for pseudo-lined languages the same rule is applied). Identical pairs; pairs at
  Levenshtein distance exactly 1; and the same two rates after a seeded random shuffle of the token
  sequence (expected value under random adjacency, 5 shuffles averaged).
"""
import os as _os  # local paths (the September 2026 scripts hard-coded another machine)
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_CORP = _os.path.join(_HERE, 'data', 'corpora')  # corp_<lang>_<gutenberg id>.txt, see fetch_corpora.py
_EXT = _os.path.join(_HERE, 'data', 'external')  # third-party data (Naibbe, Gaskell & Bowern)
_IT = _os.path.join(_CORP, 'corpus_it.txt')  # vatican5 OCR corpus from the September sample's first words (fetch_corpora.py)
import re, json, math, random, collections, pathlib, glob, sys

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / 'data'
RES = HERE / 'results'; RES.mkdir(exist_ok=True)
T50 = pathlib.Path(_CORP)
IT_FILE = pathlib.Path(_IT)

# ---------------------------------------------------------------- Voynich loading
MERGE = [('cfh', 'F'), ('ckh', 'K'), ('cph', 'P'), ('cth', 'T'), ('iiin', 'M'), ('iin', 'N'), ('eee', 'W'),
         ('ee', 'E'), ('ch', 'C'), ('sh', 'S'), ('in', 'J')]
MERGE_NAMES = {v: k for k, v in MERGE}
GALLOWS_RAW = set('ktpf'); GALLOWS_MERGED = set('ktpfKTPF')

def merge(word):
    out = []; i = 0
    while i < len(word):
        for src, dst in MERGE:
            if word.startswith(src, i):
                out.append(dst); i += len(src); break
        else:
            out.append(word[i]); i += 1
    return ''.join(out)

def load_voynich(path=DATA / 'ZL3b-n.words.tsv'):
    lines = []
    with open(path, encoding='utf-8') as f:
        next(f)
        for row in f:
            fld = row.rstrip('\n').split('\t')
            if fld[2] != 'P': continue
            words = [w for w in fld[9].split() if re.fullmatch(r'[a-z]+', w)]
            if not words: continue
            lines.append(dict(folio=fld[0], line=fld[1], lang=fld[3], hand=fld[4], illus=fld[5],
                              pstart=fld[7] == '1', words=words))
    return lines

# ---------------------------------------------------------------- corpora
def gutenberg_words(path):
    t = path.read_text(encoding='utf-8', errors='replace')
    i = t.find('*** START OF'); j = t.find('*** END OF')
    if i >= 0: t = t[t.find('\n', i) + 1:]
    if j >= 0: t = t[:t.find('*** END OF')]
    return re.findall(r'[^\W\d_]+', t.lower())

def language_sample(lang, n, skip=2000):
    if lang == 'it':
        words = re.findall(r'[^\W\d_]+', IT_FILE.read_text(encoding='utf-8', errors='replace').lower())
        return words[10000:10000 + n]
    files = sorted(T50.glob(f'corp_{lang}_*.txt'))
    if lang == 'la': files = [f for f in files if '50280' not in f.name]
    books = [gutenberg_words(f)[skip:] for f in files]
    share = n // len(books) + 1
    out = []
    for b in books: out.extend(b[:share])
    return out[:n]

def aeneid_verse_lines():
    t = (T50 / 'corp_la_227.txt').read_text(encoding='utf-8', errors='replace')
    i = t.find('*** START OF'); j = t.find('*** END OF')
    t = t[t.find('\n', i) + 1:j]
    lines = []
    for raw in t.splitlines():
        ws = re.findall(r'[^\W\d_]+', raw.lower())
        if len(ws) >= 2: lines.append(ws)
    return lines

# ---------------------------------------------------------------- statistics helpers
def ols_slope(xs, ys):
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys)); sxx = sum((x - mx) ** 2 for x in xs)
    return sxy / sxx

def zipf(tokens):
    c = collections.Counter(tokens); freqs = sorted(c.values(), reverse=True)
    out = {'tokens': len(tokens), 'types': len(c)}
    for R in (1000, 5000):
        r = min(R, len(freqs))
        xs = [math.log10(i + 1) for i in range(r)]; ys = [math.log10(freqs[i]) for i in range(r)]
        out[f'zipf_slope_1_{R}'] = round(ols_slope(xs, ys), 4); out[f'ranks_used_{R}'] = r
    hap = sum(1 for v in freqs if v == 1)
    out['hapax_types'] = hap; out['hapax_type_frac'] = round(hap / len(c), 4); out['hapax_token_frac'] = round(hap / len(tokens), 4)
    out['dis_legomena_type_frac'] = round(sum(1 for v in freqs if v == 2) / len(c), 4)
    out['top10'] = [(w, n) for w, n in c.most_common(10)]
    out['top1_share'] = round(freqs[0] / len(tokens), 4)
    return out

def log_binom_pmf(k, n, p):
    if p <= 0: return 0.0 if k == 0 else -1e9
    if p >= 1: return 0.0 if k == n else -1e9
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1) + k * math.log(p) + (n - k) * math.log(1 - p)

def binom_fit(lengths, shift=1):
    ks = [L - shift for L in lengths]; N = len(ks); m = sum(ks) / N; kmax = max(ks)
    best = None
    for n in range(max(kmax, 1), 41):
        p = m / n; ll = sum(log_binom_pmf(k, n, p) for k in ks)
        if best is None or ll > best[2]: best = (n, p, ll)
    n, p, ll = best
    hist = collections.Counter(ks); chi = 0.0
    for k in range(0, n + 1):
        e = N * math.exp(log_binom_pmf(k, n, p))
        if e >= 1: chi += (hist.get(k, 0) - e) ** 2 / e
    return {'n': n, 'p': round(p, 4), 'loglik': round(ll, 1), 'chi2_vs_fit': round(chi, 1), 'shift': shift,
            'n_at_cap': n == 40, 'note': 'n=40 is the search cap: likelihood still rising with n, i.e. no finite binomial optimum (over-dispersed, Poisson-or-wider)' if n == 40 else ''}

def wordlength(tokens):
    Ls = [len(t) for t in tokens]; N = len(Ls); m = sum(Ls) / N
    var = sum((L - m) ** 2 for L in Ls) / N; sd = math.sqrt(var)
    skew = sum((L - m) ** 3 for L in Ls) / N / sd ** 3
    hist = collections.Counter(Ls)
    return {'mean': round(m, 3), 'variance': round(var, 3), 'skewness': round(skew, 3), 'max': max(Ls),
            'dispersion_var_over_mean_Lminus1': round(var / (m - 1), 3),
            'histogram_pct': {str(L): round(100 * hist.get(L, 0) / N, 2) for L in range(1, 16)},
            'pct_over_15': round(100 * sum(v for k, v in hist.items() if k > 15) / N, 2),
            'binomial_fit_Lminus1': binom_fit(Ls, 1), 'binomial_fit_L': binom_fit(Ls, 0)}

def ttr_curve(tokens):
    seen = set(); pts = {}; checkpoints = (5000, 10000, 20000, 37000); xs = []; ys = []
    for i, t in enumerate(tokens, 1):
        seen.add(t)
        if i in checkpoints: pts[str(i)] = len(seen)
        if i % 1000 == 0: xs.append(math.log(i)); ys.append(math.log(len(seen)))
    pts['N=' + str(len(tokens))] = len(seen)
    return {'types_after': pts, 'heaps_beta': round(ols_slope(xs, ys), 4) if len(xs) > 2 else None}

# --- chi-square p-value (regularised upper incomplete gamma, Numerical Recipes gammq)
def gammq(a, x):
    if x <= 0: return 1.0
    if x < a + 1:
        ap = a; s = d = 1.0 / a
        for _ in range(10000):
            ap += 1; d *= x / ap; s += d
            if abs(d) < abs(s) * 1e-15: break
        return 1.0 - s * math.exp(-x + a * math.log(x) - math.lgamma(a))
    b = x + 1 - a; c = 1e300; d = 1 / b; h = d
    for i in range(1, 10000):
        an = -i * (i - a); b += 2; d = an * d + b
        if abs(d) < 1e-300: d = 1e-300
        c = b + an / c
        if abs(c) < 1e-300: c = 1e-300
        d = 1 / d; de = d * c; h *= de
        if abs(de - 1) < 1e-15: break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h

def chi2_p(chi2, df):
    try: return gammq(df / 2, chi2 / 2)
    except (OverflowError, ValueError): return 0.0

def contingency(table, min_exp=5.0):
    """table: dict[rowlabel] -> Counter(symbol). Pools rare symbols. Returns chi2, df, p, V, residuals, shares."""
    rows = list(table); N = sum(sum(c.values()) for c in table.values())
    colsum = collections.Counter()
    for c in table.values(): colsum.update(c)
    rowsum = {r: sum(table[r].values()) for r in rows}
    keep = [s for s in colsum if all(rowsum[r] * colsum[s] / N >= min_exp for r in rows)]
    pooled = {r: collections.Counter() for r in rows}
    for r in rows:
        for s, v in table[r].items(): pooled[r][s if s in keep else 'other'] += v
    cols = sorted(set().union(*[set(c) for c in pooled.values()]))
    colsum = collections.Counter()
    for c in pooled.values(): colsum.update(c)
    chi2 = 0.0; resid = []
    for r in rows:
        for s in cols:
            e = rowsum[r] * colsum[s] / N; o = pooled[r][s]
            if e > 0:
                chi2 += (o - e) ** 2 / e; resid.append((round((o - e) / math.sqrt(e), 1), r, s, o, round(e, 1)))
    df = (len(rows) - 1) * (len(cols) - 1)
    V = math.sqrt(chi2 / (N * (min(len(rows), len(cols)) - 1))) if N and min(len(rows), len(cols)) > 1 else 0
    resid.sort(key=lambda t: -abs(t[0]))
    shares = {r: {s: round(100 * table[r][s] / rowsum[r], 1) for s, _ in table[r].most_common(8)} for r in rows}
    return {'N': N, 'chi2': round(chi2, 1), 'df': df, 'p': float(f'{chi2_p(chi2, df):.3g}'), 'cramers_V': round(V, 4),
            'top_deviations': [f'{r}:{s} obs={o} exp={e} z={z:+}' for z, r, s, o, e in resid[:10]],
            'row_n': rowsum, 'top_symbol_shares_pct': shares}

def positional(lines, sym_word, gallows):
    """lines: list of dict(words, pstart). sym_word(w) -> symbol string for w."""
    first = {'START': collections.Counter(), 'MID': collections.Counter(), 'END': collections.Counter()}
    last = {'START': collections.Counter(), 'MID': collections.Counter(), 'END': collections.Counter()}
    para = {'PARA_FIRST': collections.Counter(), 'LINE_FIRST': collections.Counter(), 'MID': collections.Counter()}
    gal = collections.defaultdict(lambda: [0, 0])  # class -> [gallows-initial, total]
    wl = collections.defaultdict(lambda: [0, 0])  # class -> [sum length, count]
    for ln in lines:
        ws = [sym_word(w) for w in ln['words']]
        if len(ws) < 2: continue
        for i, w in enumerate(ws):
            cls = 'START' if i == 0 else ('END' if i == len(ws) - 1 else 'MID')
            first[cls][w[0]] += 1; last[cls][w[-1]] += 1
            if i == 0:
                pc = 'PARA_FIRST' if ln['pstart'] else 'LINE_FIRST'
            elif cls == 'MID': pc = 'MID'
            else: pc = None
            if pc: para[pc][w[0]] += 1
            g = w[0] in gallows
            wl[cls][0] += len(w); wl[cls][1] += 1
            if pc == 'PARA_FIRST': wl['PARA_FIRST'][0] += len(w); wl['PARA_FIRST'][1] += 1
            gal[cls][1] += 1; gal[cls][0] += g
            if pc: gal[pc][1] += 1; gal[pc][0] += g
            if ln['pstart']: gal['PARA_LINE_ALL'][1] += 1; gal['PARA_LINE_ALL'][0] += g
            else: gal['NONPARA_LINE_ALL'][1] += 1; gal['NONPARA_LINE_ALL'][0] += g
    return {'first_symbol_by_position': contingency(first), 'last_symbol_by_position': contingency(last),
            'first_symbol_para_vs_line_vs_mid': contingency(para),
            'gallows_initial_pct': {k: round(100 * v[0] / v[1], 2) for k, v in sorted(gal.items())},
            'mean_word_length_by_position': {k: round(v[0] / v[1], 3) for k, v in sorted(wl.items()) if v[1]}}

def lev1(a, b):
    """True iff Levenshtein distance == 1."""
    la, lb = len(a), len(b)
    if abs(la - lb) > 1 or a == b: return False
    if la == lb:
        return sum(x != y for x, y in zip(a, b)) == 1
    if la > lb: a, b = b, a; la, lb = lb, la
    i = 0
    while i < la and a[i] == b[i]: i += 1
    return a[i:] == b[i + 1:]

def repetition(lines, sym_word, seed=1):
    pairs = 0; same = 0; ed1 = 0
    for ln in lines:
        ws = [sym_word(w) for w in ln['words']]
        for a, b in zip(ws, ws[1:]):
            pairs += 1; same += a == b; ed1 += lev1(a, b)
    # shuffled baseline keeping line lengths
    toks = [sym_word(w) for ln in lines for w in ln['words']]; rng = random.Random(seed)
    ss = se = 0; sp = 0
    for _ in range(5):
        rng.shuffle(toks); k = 0
        for ln in lines:
            ws = toks[k:k + len(ln['words'])]; k += len(ln['words'])
            for a, b in zip(ws, ws[1:]):
                sp += 1; ss += a == b; se += lev1(a, b)
    return {'pairs': pairs, 'identical_pct': round(100 * same / pairs, 3), 'ed1_pct': round(100 * ed1 / pairs, 3),
            'identical_pct_shuffled': round(100 * ss / sp, 3), 'ed1_pct_shuffled': round(100 * se / sp, 3),
            'identical_ratio_obs_over_shuffled': round((same / pairs) / max(ss / sp, 1e-9), 1),
            'ed1_ratio_obs_over_shuffled': round((ed1 / pairs) / max(se / sp, 1e-9), 1)}

def top_repeats(lines, k=8):
    c = collections.Counter()
    for ln in lines:
        ws = ln['words']
        for a, b in zip(ws, ws[1:]):
            if a == b: c[a] += 1
    return c.most_common(k)

# ---------------------------------------------------------------- pseudo-lines for languages
def pseudo_lines(tokens, template_lines):
    out = []; k = 0
    for ln in template_lines:
        n = len(ln['words'])
        if k + n > len(tokens): break
        out.append({'words': tokens[k:k + n], 'pstart': ln['pstart']}); k += n
    return out

# ---------------------------------------------------------------- main
def analyse_voynich(lines, label):
    toks_raw = [w for ln in lines for w in ln['words']]
    toks_m = [merge(w) for w in toks_raw]
    r = {'label': label, 'lines': len(lines), 'tokens': len(toks_raw)}
    r['zipf'] = zipf(toks_raw)
    r['wordlength_raw'] = wordlength(toks_raw); r['wordlength_merged'] = wordlength(toks_m)
    r['ttr'] = ttr_curve(toks_raw)
    r['positional_merged'] = positional(lines, merge, GALLOWS_MERGED)
    r['positional_raw'] = positional(lines, lambda w: w, GALLOWS_RAW)
    r['repetition_raw'] = repetition(lines, lambda w: w); r['repetition_merged'] = repetition(lines, merge)
    r['top_repeated_words'] = top_repeats(lines)
    return r

def analyse_language(lang, n, template_lines, label):
    toks = language_sample(lang, n)
    lines = pseudo_lines(toks, template_lines)
    r = {'label': label, 'tokens': len(toks), 'lines': len(lines)}
    r['zipf'] = zipf(toks); r['wordlength'] = wordlength(toks); r['ttr'] = ttr_curve(toks)
    r['positional'] = positional(lines, lambda w: w, set())
    r['repetition'] = repetition(lines, lambda w: w); r['top_repeated_words'] = top_repeats(lines)
    return r

def main():
    lines = load_voynich()
    subsets = {'ALL': lines, 'A': [l for l in lines if l['lang'] == 'A'], 'B': [l for l in lines if l['lang'] == 'B']}
    results = {'voynich': {}, 'languages': {}, 'controls': {}}
    for k, ls in subsets.items():
        results['voynich'][k] = analyse_voynich(ls, f'Voynich ZL P {k}'); print(k, results['voynich'][k]['tokens'], file=sys.stderr)
    LANGS = {'la': 'Latin', 'it': 'Italian', 'de': 'German', 'en': 'English', 'da': 'Danish'}
    for k, ls in subsets.items():
        n = sum(len(l['words']) for l in ls)
        results['languages'][k] = {}
        for lg, name in LANGS.items():
            results['languages'][k][lg] = analyse_language(lg, n, ls, f'{name} sample N={n} (lined as Voynich {k})')
            print(k, lg, file=sys.stderr)
    # real verse lines control
    vl = [{'words': ws, 'pstart': False} for ws in aeneid_verse_lines()]
    results['controls']['aeneid_real_verse_lines'] = {'lines': len(vl), 'tokens': sum(len(l['words']) for l in vl),
                                                      'positional': positional(vl, lambda w: w, set()),
                                                      'repetition': repetition(vl, lambda w: w)}
    # second transliteration robustness (IT2a, EVA): zipf/hapax/length only
    try:
        it_lines = load_voynich(DATA / 'IT2a-n.words.tsv'); toks = [w for l in it_lines for w in l['words']]
        results['controls']['IT2a_transliteration'] = {'tokens': len(toks), 'zipf': zipf(toks), 'wordlength_raw': wordlength(toks),
                                                       'wordlength_merged': wordlength([merge(w) for w in toks]),
                                                       'repetition_raw': repetition(it_lines, lambda w: w)}
    except Exception as e:
        results['controls']['IT2a_transliteration'] = {'error': str(e)}
    results['voynich_line_length_hist'] = dict(sorted(collections.Counter(len(l['words']) for l in lines).items()))
    results['merge_map'] = MERGE
    (RES / 'a2.json').write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding='utf-8')
    write_md(results)

def write_md(R):
    L = []; V = R['voynich']; LG = R['languages']
    names = {'la': 'Latin', 'it': 'Italian', 'de': 'German', 'en': 'English', 'da': 'Danish'}
    def row(cells): L.append('| ' + ' | '.join(str(c) for c in cells) + ' |')
    L.append('# a2: word-level and positional statistics (ZL3b-n paragraph text vs 5 languages)\n')
    L.append('Voynich tokens: ALL=%d, A=%d, B=%d. Language samples are matched to each subset size. See a2_wordstats.py docstring for methods.\n' % (V['ALL']['tokens'], V['A']['tokens'], V['B']['tokens']))
    for sub in ('ALL', 'A', 'B'):
        L.append(f'\n## Subset {sub} (N={V[sub]["tokens"]} tokens)\n')
        L.append('### (1) Zipf / vocabulary\n'); row(['text', 'types', 'slope r1-1000', 'slope r1-5000 (ranks used)', 'hapax types %', 'hapax tokens %', 'top-1 share %', 'top 5 words']); row(['---'] * 8)
        def zrow(name, z): row([name, z['types'], z['zipf_slope_1_1000'], f"{z['zipf_slope_1_5000']} ({z['ranks_used_5000']})", round(100 * z['hapax_type_frac'], 1), round(100 * z['hapax_token_frac'], 1), round(100 * z['top1_share'], 2), ' '.join(f'{w}:{n}' for w, n in z['top10'][:5])])
        zrow('Voynich ' + sub, V[sub]['zipf'])
        for lg in names: zrow(names[lg], LG[sub][lg]['zipf'])
        L.append('\n### (2) Word length (symbols per word)\n'); row(['text', 'mean', 'var', 'var/mean of L-1', 'skew', 'binom fit L-1~B(n,p) (n=40 = cap)', 'chi2 vs fit', 'hist % L=1..12']); row(['---'] * 8)
        def wrow(name, w):
            b = w['binomial_fit_Lminus1']; row([name, w['mean'], w['variance'], w['dispersion_var_over_mean_Lminus1'], w['skewness'], f"n={b['n']} p={b['p']}", b['chi2_vs_fit'], ' '.join(str(w['histogram_pct'][str(i)]) for i in range(1, 13))])
        wrow('Voynich RAW EVA', V[sub]['wordlength_raw']); wrow('Voynich MERGED', V[sub]['wordlength_merged'])
        for lg in names: wrow(names[lg], LG[sub][lg]['wordlength'])
        L.append('\n### (3) Type-token growth\n'); row(['text', 'types@5k', '@10k', '@20k', '@37k', '@N', 'Heaps beta']); row(['---'] * 7)
        def trow(name, t):
            p = t['types_after']; row([name, p.get('5000', ''), p.get('10000', ''), p.get('20000', ''), p.get('37000', ''), [v for k, v in p.items() if k.startswith('N=')][0], t['heaps_beta']])
        trow('Voynich ' + sub, V[sub]['ttr'])
        for lg in names: trow(names[lg], LG[sub][lg]['ttr'])
        L.append('\n### (4) Positional effects (START/MID/END of line; 1-word lines excluded)\n')
        row(['text', 'first-symbol chi2 (df) p', 'V', 'last-symbol chi2 (df) p', 'V', 'para-first vs line-first vs mid chi2 (df) p', 'V']); row(['---'] * 7)
        def prow(name, P):
            a, b, c = P['first_symbol_by_position'], P['last_symbol_by_position'], P['first_symbol_para_vs_line_vs_mid']
            row([name, f"{a['chi2']} ({a['df']}) p={a['p']}", a['cramers_V'], f"{b['chi2']} ({b['df']}) p={b['p']}", b['cramers_V'], f"{c['chi2']} ({c['df']}) p={c['p']}", c['cramers_V']])
        prow('Voynich MERGED', V[sub]['positional_merged']); prow('Voynich RAW', V[sub]['positional_raw'])
        for lg in names: prow(names[lg] + ' (pseudo-lines)', LG[sub][lg]['positional'])
        if sub == 'ALL':
            prow('Aeneid REAL verse lines', R['controls']['aeneid_real_verse_lines']['positional'])
        P = V[sub]['positional_merged']
        L.append('\nStrongest deviations, Voynich MERGED first symbol by position (z = standardised residual; merged symbols: ' + ', '.join(f'{v}={k}' for k, v in R['merge_map']) + '):\n')
        for d in P['first_symbol_by_position']['top_deviations']: L.append('- ' + d)
        L.append('\nStrongest deviations, last symbol by position:\n')
        for d in P['last_symbol_by_position']['top_deviations']: L.append('- ' + d)
        L.append('\nStrongest deviations, paragraph-first vs line-first vs mid (first symbol):\n')
        for d in P['first_symbol_para_vs_line_vs_mid']['top_deviations']: L.append('- ' + d)
        L.append('\nGallows-initial share % (k t p f + merged bench-gallows):\n'); row(['class', 'Voynich MERGED', 'Voynich RAW']); row(['---'] * 3)
        for k in P['gallows_initial_pct']: row([k, P['gallows_initial_pct'][k], V[sub]['positional_raw']['gallows_initial_pct'].get(k, '')])
        L.append('\nMean word length (symbols) by line position:\n'); row(['text', 'START', 'MID', 'END', 'PARA_FIRST']); row(['---'] * 5)
        def lrow(name, P_):
            d = P_['mean_word_length_by_position']; row([name, d.get('START'), d.get('MID'), d.get('END'), d.get('PARA_FIRST')])
        lrow('Voynich MERGED', P); lrow('Voynich RAW', V[sub]['positional_raw'])
        for lg in names: lrow(names[lg] + ' (pseudo-lines)', LG[sub][lg]['positional'])
        if sub == 'ALL': lrow('Aeneid real verse', R['controls']['aeneid_real_verse_lines']['positional'])
        L.append('\nFirst-symbol shares % by position (top symbols):\n')
        for cls, sh in P['first_symbol_by_position']['top_symbol_shares_pct'].items(): L.append(f'- {cls} (n={P["first_symbol_by_position"]["row_n"][cls]}): ' + ', '.join(f'{s}={v}' for s, v in sh.items()))
        L.append('\nLast-symbol shares % by position (top symbols):\n')
        for cls, sh in P['last_symbol_by_position']['top_symbol_shares_pct'].items(): L.append(f'- {cls} (n={P["last_symbol_by_position"]["row_n"][cls]}): ' + ', '.join(f'{s}={v}' for s, v in sh.items()))
        if sub == 'ALL':
            L.append('\nControl: Latin/German pseudo-lines strongest deviations (first symbol):\n')
            for lg in ('la', 'de'):
                L.append(f'- {names[lg]}: ' + '; '.join(LG[sub][lg]['positional']['first_symbol_by_position']['top_deviations'][:4]))
            L.append('- Aeneid real verse lines: ' + '; '.join(R['controls']['aeneid_real_verse_lines']['positional']['first_symbol_by_position']['top_deviations'][:4]))
            L.append('- Aeneid real verse lines, LAST symbol: ' + '; '.join(R['controls']['aeneid_real_verse_lines']['positional']['last_symbol_by_position']['top_deviations'][:4]))
        L.append('\n### (5) Adjacent word repetition (pairs within lines)\n'); row(['text', 'pairs', 'identical %', 'identical % shuffled', 'ratio', 'edit-dist-1 %', 'ED1 % shuffled', 'ratio', 'top repeated']); row(['---'] * 9)
        def rrow(name, r, top=None): row([name, r['pairs'], r['identical_pct'], r['identical_pct_shuffled'], r['identical_ratio_obs_over_shuffled'], r['ed1_pct'], r['ed1_pct_shuffled'], r['ed1_ratio_obs_over_shuffled'], ' '.join(f'{w}:{n}' for w, n in (top or [])[:5])])
        rrow('Voynich RAW', V[sub]['repetition_raw'], V[sub]['top_repeated_words']); rrow('Voynich MERGED', V[sub]['repetition_merged'])
        for lg in names: rrow(names[lg], LG[sub][lg]['repetition'], LG[sub][lg]['top_repeated_words'])
        if sub == 'ALL': rrow('Aeneid real verse', R['controls']['aeneid_real_verse_lines']['repetition'])
    c = R['controls'].get('IT2a_transliteration', {})
    if 'zipf' in c:
        L.append('\n## Robustness: Takahashi IT2a transliteration (P locus, same cleaning)\n')
        z = c['zipf']; w = c['wordlength_raw']; wm = c['wordlength_merged']; r = c['repetition_raw']
        L.append(f"tokens={c['tokens']} types={z['types']} slope1-1000={z['zipf_slope_1_1000']} slope1-5000={z['zipf_slope_1_5000']} hapax types%={100*z['hapax_type_frac']:.1f}; length RAW mean={w['mean']} var={w['variance']} skew={w['skewness']}; MERGED mean={wm['mean']} var={wm['variance']} skew={wm['skewness']}; identical adjacent%={r['identical_pct']} ED1%={r['ed1_pct']}")
    L.append('\nVoynich P-line length histogram (words): ' + ', '.join(f'{k}:{v}' for k, v in R['voynich_line_length_hist'].items()))
    L.append(VERDICT)
    (RES / 'a2.md').write_text('\n'.join(L) + '\n', encoding='utf-8')

VERDICT = """
## Verdict table (ALL subset; L = language-like, C = cipher-like, N = neither / unlike both simple options)

| statistic | Voynich | 5-language range | class | reason |
| --- | --- | --- | --- | --- |
| Zipf slope r1-1000 / r1-5000 | -1.04 / -1.06 | -0.82..-1.06 / -0.87..-1.02 | L | inside the range |
| hapax types % / hapax tokens % | 69.7 / 14.8 | 55-67 / 8-23 | L (edge) | slightly above every language on types, inside on tokens |
| top-1 word share % | 2.25 | 3.5-4.9 | N | no dominant function word; flatter head than any language |
| types at 34k tokens / Heaps beta | 7236 / 0.71 | 5139-11640 / 0.68-0.78 | L | inside the range |
| word-length variance (MERGED / RAW) | 2.5 / 3.7 | 5.4-7.4 | N/C | half the variance of any language; var/mean(L-1) 0.80-0.92 vs 1.4-2.0 |
| binomial ML fit of L-1 | finite optimum n=19 p=0.16 (MERGED), n=15 p=0.21 (B) | no finite optimum (n at cap) for all 5 | N/C | languages over-dispersed, Voynich under-dispersed |
| skewness of word length | 0.57-0.76 | 0.50-1.46 | L | skew alone does not separate it; dispersion does |
| first-symbol x line-position Cramer V | 0.31 | 0.02-0.03 (pseudo-lines); 0.15 real hexameter lines | N/C | 10x the null, 2x genuine verse |
| last-symbol x line-position Cramer V | 0.25 | 0.02-0.03; 0.18 hexameter | N/C | line-final -m 15.4% vs 0.9% mid-line |
| paragraph-first gallows-initial % | 83 | n/a (letters) | N/C | vs 9% for other line-first words and 9% mid-line |
| mean word length START/MID/END/PARA_FIRST | 4.40/4.06/4.11/5.27 | flat within 0.1 | N/C | line-first and paragraph-first words are longer |
| identical adjacent pairs % (obs / shuffled) | 0.91 / 0.36 (ratio 2.5) | 0.05-0.17 / 0.35-0.82 (ratio 0.1-0.3) | C/N | 5-30x language rate; languages avoid repetition, Voynichese seeks it |
| edit-distance-1 adjacent pairs % (obs / shuffled) | 3.5 / 1.7 (ratio 2.0) | 0.4-1.4 / 0.4-1.5 (ratio 0.5-1.7) | C/N | near-copies cluster; vocabulary itself is denser than any language (shuffled baseline already higher) |

Reading: rank-frequency, vocabulary growth and hapax behaviour are language-like (but these are also reproduced
by known meaningless generators). Word-length dispersion, line/paragraph-position dependence and adjacent
(near-)repetition are unlike all five languages and unlike genuine verse lines, and a simple substitution cipher
of any of them would inherit the language values for all three. What remains compatible: a verbose or lossy
code/cipher whose output units are not plaintext words, a generation procedure (table/grille or copy-and-modify),
or a language written in an unusual segmentation/abbreviation system. These tests do not separate those three.
"""

if __name__ == '__main__':
    main()
