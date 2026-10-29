"""v_a2.py -- adversarial re-check of a2_wordstats.py (word-level / positional statistics).

Does NOT modify a2 files. Imports a2_wordstats as a module (main() is not run) to reuse its loader and
to compare against independent re-implementations. Outputs results/v_a2.json and results/v_a2.md.

Checks:
 1. token/line counts of the a2 loader; dropped-word accounting
 2. independent Zipf slope / hapax / top-1 on the same tokens
 3. independent word-length mean/variance/dispersion (RAW, MERGED); binomial ML with cap raised to 300
 4. independent chi-square + Cramer's V (own pooling), p-value cross-check by Poisson sum (exact for even df)
 5. full-DP Levenshtein vs a2.lev1 on every adjacent pair; identical-pair and ED1 rates and shuffled baselines
 6. START split into LINE_FIRST (non-paragraph) vs PARA_FIRST mean word length (a2 only reports the mixture)
 7. how much positional effect survives when the known allograph/ornament classes are removed:
    (a) paragraph-first lines excluded, (b) words ending in m/g excluded, (c) m->iin (N) and g->d recoded
 8. COMMA ARTEFACT: parse_ivtff.py turned every ',' (IVTFF uncertain space) into a word break. Re-parse ZL3b-n.txt
    with ',' JOINED (no break) and recompute word length, repetition, Zipf, positional V.
 9. corpus audit: Gutenberg samples (non-ASCII share, 1-letter words, roman numerals), 'Italian' corpus Latin admixture
"""
import re, json, math, random, collections, pathlib, sys, importlib.util

HERE = pathlib.Path(__file__).resolve().parent
RES = HERE / 'results'; RES.mkdir(exist_ok=True)
spec = importlib.util.spec_from_file_location('a2', HERE / 'a2_wordstats.py'); a2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(a2)
A2 = json.loads((RES / 'a2.json').read_text(encoding='utf-8'))
OUT = {}

# ------------------------------------------------------------------ 1. loader counts
lines = a2.load_voynich()
subsets = {'ALL': lines, 'A': [l for l in lines if l['lang'] == 'A'], 'B': [l for l in lines if l['lang'] == 'B']}
toks = {k: [w for l in v for w in l['words']] for k, v in subsets.items()}
OUT['counts'] = {k: {'lines': len(v), 'tokens': len(toks[k]), 'a2_tokens': A2['voynich'][k]['tokens']} for k, v in subsets.items()}
print('counts', OUT['counts'])

# ------------------------------------------------------------------ 2. independent zipf
def my_zipf(tokens, R):
    c = collections.Counter(tokens); f = sorted(c.values(), reverse=True)[:R]
    xs = [math.log10(i + 1) for i in range(len(f))]; ys = [math.log10(v) for v in f]
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    hap = sum(1 for v in c.values() if v == 1)
    return {'slope': round(b, 4), 'types': len(c), 'hapax_types_pct': round(100 * hap / len(c), 2), 'hapax_tokens_pct': round(100 * hap / len(tokens), 2),
            'top1_pct': round(100 * max(c.values()) / len(tokens), 3), 'top1': c.most_common(1)[0][0]}
OUT['zipf'] = {k: {'r1000': my_zipf(toks[k], 1000), 'r5000': my_zipf(toks[k], 5000)['slope'],
                   'a2': (A2['voynich'][k]['zipf']['zipf_slope_1_1000'], A2['voynich'][k]['zipf']['zipf_slope_1_5000'])} for k in toks}
print('zipf', OUT['zipf'])

# ------------------------------------------------------------------ 3. word length + binomial with high cap
def my_len(tokens):
    Ls = [len(t) for t in tokens]; N = len(Ls); m = sum(Ls) / N; var = sum((L - m) ** 2 for L in Ls) / N
    sd = var ** .5; sk = sum((L - m) ** 3 for L in Ls) / N / sd ** 3
    return {'mean': round(m, 3), 'var': round(var, 3), 'disp_Lminus1': round(var / (m - 1), 3), 'skew': round(sk, 3), 'max': max(Ls),
            'moment_n': round((m - 1) / (1 - var / (m - 1)), 1) if var / (m - 1) < 1 else None}
def binom_cap(tokens, cap):
    ks = [len(t) - 1 for t in tokens]; N = len(ks); m = sum(ks) / N; best = None
    for n in range(max(ks), cap + 1):
        p = m / n; ll = sum(a2.log_binom_pmf(k, n, p) for k in ks)
        if best is None or ll > best[2]: best = (n, round(p, 4), ll)
    return {'n': best[0], 'p': best[1], 'at_cap': best[0] == cap}
OUT['wordlength'] = {}
for k in toks:
    OUT['wordlength'][k] = {'raw': my_len(toks[k]), 'merged': my_len([a2.merge(w) for w in toks[k]]),
                            'a2_raw': (A2['voynich'][k]['wordlength_raw']['mean'], A2['voynich'][k]['wordlength_raw']['variance']),
                            'a2_merged': (A2['voynich'][k]['wordlength_merged']['mean'], A2['voynich'][k]['wordlength_merged']['variance'])}
OUT['wordlength']['ALL']['raw_binom_cap300'] = binom_cap(toks['ALL'], 300)
OUT['wordlength']['A']['merged_binom_cap300'] = binom_cap([a2.merge(w) for w in toks['A']], 300)
OUT['wordlength']['ALL']['merged_binom_cap300'] = binom_cap([a2.merge(w) for w in toks['ALL']], 300)
# without 1-letter words (languages have 1-letter function words; Voynich 1-letter tokens are often labels/fragments)
OUT['wordlength']['ALL']['merged_excl_L1'] = my_len([a2.merge(w) for w in toks['ALL'] if len(a2.merge(w)) > 1])
print('wordlength', json.dumps(OUT['wordlength'], indent=0))

# ------------------------------------------------------------------ 4. independent chi-square / V / p
def my_chi(table):
    rows = list(table); cols = sorted(set().union(*[set(c) for c in table.values()]))
    N = sum(sum(c.values()) for c in table.values()); rs = {r: sum(table[r].values()) for r in rows}; cs = {s: sum(table[r][s] for r in rows) for s in cols}
    keep = [s for s in cols if all(rs[r] * cs[s] / N >= 5 for r in rows)]
    pooled = {r: collections.Counter() for r in rows}
    for r in rows:
        for s, v in table[r].items(): pooled[r][s if s in keep else 'other'] += v
    cols = sorted(set().union(*[set(c) for c in pooled.values()])); cs = {s: sum(pooled[r][s] for r in rows) for s in cols}
    chi = sum((pooled[r][s] - rs[r] * cs[s] / N) ** 2 / (rs[r] * cs[s] / N) for r in rows for s in cols if cs[s] > 0)
    df = (len(rows) - 1) * (len(cols) - 1); V = (chi / (N * (min(len(rows), len(cols)) - 1))) ** .5
    return round(chi, 1), df, round(V, 4)
def poisson_sf(chi, df):  # exact chi-square survival for even df
    assert df % 2 == 0; lam = chi / 2; return sum(math.exp(-lam + k * math.log(lam) - math.lgamma(k + 1)) for k in range(df // 2))
OUT['pvalue_check'] = {'gammq(22,23.9)': a2.chi2_p(47.8, 44), 'poisson_exact': poisson_sf(47.8, 44), 'gammq(19,14.05)': a2.chi2_p(28.1, 38), 'poisson_exact2': poisson_sf(28.1, 38)}
print('p-check', OUT['pvalue_check'])

def tables(lines, sym, excl_para=False, drop_last=(), recode=None):
    first = {c: collections.Counter() for c in ('START', 'MID', 'END')}; last = {c: collections.Counter() for c in ('START', 'MID', 'END')}
    wl = collections.defaultdict(list)
    for ln in lines:
        if excl_para and ln['pstart']: continue
        ws = [sym(w) for w in ln['words']]
        if len(ws) < 2: continue
        for i, w in enumerate(ws):
            cls = 'START' if i == 0 else ('END' if i == len(ws) - 1 else 'MID')
            first[cls][w[0]] += 1
            lw = w[-1]
            if recode: lw = recode.get(lw, lw)
            if lw not in drop_last: last[cls][lw] += 1
            wl[cls].append(len(w)); wl['PARA_FIRST' if (i == 0 and ln['pstart']) else ('LINE_FIRST' if i == 0 else cls)].append(len(w))
    return first, last, wl
OUT['positional'] = {}
for k in subsets:
    f, l, wl = tables(subsets[k], a2.merge)
    OUT['positional'][k] = {'first_chi_df_V': my_chi(f), 'last_chi_df_V': my_chi(l),
                            'a2_first_V': A2['voynich'][k]['positional_merged']['first_symbol_by_position']['cramers_V'],
                            'a2_last_V': A2['voynich'][k]['positional_merged']['last_symbol_by_position']['cramers_V'],
                            'mean_len': {c: round(sum(v) / len(v), 3) for c, v in wl.items()}, 'n': {c: len(v) for c, v in wl.items()}}
    # 7. what survives removing known ornament / allograph classes
    f2, l2, _ = tables(subsets[k], a2.merge, excl_para=True)
    f3, l3, _ = tables(subsets[k], a2.merge, excl_para=True, drop_last=('m', 'g'))
    f4, l4, _ = tables(subsets[k], a2.merge, excl_para=True, recode={'m': 'N', 'g': 'd'})
    OUT['positional'][k]['excl_para_lines'] = {'first': my_chi(f2), 'last': my_chi(l2)}
    OUT['positional'][k]['excl_para_and_drop_m_g_final'] = {'last': my_chi(l3)}
    OUT['positional'][k]['excl_para_recode_m_to_iin_g_to_d'] = {'last': my_chi(l4)}
    # first-symbol test restricted to START vs MID only after removing the 'line-initial variant' letters y,s,d,p,t? no -- instead: share table
    tot = {c: sum(f2[c].values()) for c in f2}
    OUT['positional'][k]['first_shares_excl_para_pct'] = {c: {s: round(100 * f2[c][s] / tot[c], 1) for s in ('y', 's', 'd', 'o', 'q', 'C', 'S', 'a', 't', 'p', 'k')} for c in f2}
print('positional', json.dumps(OUT['positional'], indent=0))

# ------------------------------------------------------------------ 5. Levenshtein full DP check + repetition
def lev(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1): cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]
def rep(lines, sym, seed=1, nshuf=5):
    pairs = same = ed1 = ed1_dp = mism = 0
    for ln in lines:
        ws = [sym(w) for w in ln['words']]
        for a, b in zip(ws, ws[1:]):
            pairs += 1; same += a == b; x = a2.lev1(a, b); y = lev(a, b) == 1; ed1 += x; ed1_dp += y; mism += x != y
    tk = [sym(w) for ln in lines for w in ln['words']]; rng = random.Random(seed); ss = se = sp = 0
    for _ in range(nshuf):
        rng.shuffle(tk); k = 0
        for ln in lines:
            ws = tk[k:k + len(ln['words'])]; k += len(ln['words'])
            for a, b in zip(ws, ws[1:]): sp += 1; ss += a == b; se += lev(a, b) == 1
    return {'pairs': pairs, 'identical_pct': round(100 * same / pairs, 3), 'ed1_pct': round(100 * ed1 / pairs, 3), 'ed1_dp_pct': round(100 * ed1_dp / pairs, 3),
            'lev1_vs_dp_mismatches': mism, 'identical_shuf_pct': round(100 * ss / sp, 3), 'ed1_shuf_pct': round(100 * se / sp, 3)}
OUT['repetition'] = {k: {'raw': rep(subsets[k], lambda w: w), 'a2_raw': A2['voynich'][k]['repetition_raw']} for k in subsets}
# repetition excluding the ~20 most frequent tokens? no; instead: identical pairs that are 1-2 letter words
OUT['repetition']['ALL']['identical_pairs_by_word'] = a2.top_repeats(subsets['ALL'], 15)
print('repetition', json.dumps(OUT['repetition'], indent=0))

# ------------------------------------------------------------------ 8. comma artefact: re-parse raw IVTFF with ',' joined
def parse_raw(path, comma='break'):
    meta = {}; rows = []; ncomma = 0
    for raw in pathlib.Path(path).read_text(encoding='utf-8', errors='replace').splitlines():
        if raw.startswith('#') or not raw.strip(): continue
        m = re.match(r'<(f\d+[rv]\d?|[a-z]\w*)>\s*<!([^>]*)>', raw)
        if m and '.' not in m.group(1):
            meta[m.group(1)] = dict(re.findall(r'\$(\w)=(\w+)', m.group(2))); continue
        m = re.match(r'<(f\d+[rv]\d?|\w+)\.(\d+),([@+*=])([A-Za-z])(\w*)>\s*(.*)$', raw)
        if not m: continue
        folio, ln, tag, ltype, sub, text = m.groups()
        if ltype != 'P': continue
        pstart = '<%>' in text
        t = re.sub(r'<![^>]*>', '', text); t = re.sub(r'<[^>]*>', '', t); t = re.sub(r'\{[^}]*\}', '', t); t = re.sub(r'\[([^\]:]*):[^\]]*\]', r'\1', t)
        ncomma += t.count(',')
        t = t.replace(',', '.' if comma == 'break' else '')
        words = [w for w in t.split('.') if w and re.fullmatch(r'[a-z]+', w)]
        if words: rows.append({'words': words, 'pstart': pstart, 'lang': meta.get(folio, {}).get('L', '?')})
    return rows, ncomma
rows_b, nc = parse_raw(HERE / 'data' / 'ZL3b-n.txt', 'break'); rows_j, _ = parse_raw(HERE / 'data' / 'ZL3b-n.txt', 'join')
tb = [w for l in rows_b for w in l['words']]; tj = [w for l in rows_j for w in l['words']]
fb, lb, _ = tables(rows_b, a2.merge); fj, lj, _ = tables(rows_j, a2.merge)
OUT['comma'] = {'commas_in_P_text': nc, 'tokens_break': len(tb), 'tokens_join': len(tj), 'my_break_matches_a2_tokens': len(tb) == len(toks['ALL']),
                'break': {'len_raw': my_len(tb), 'len_merged': my_len([a2.merge(w) for w in tb]), 'zipf': my_zipf(tb, 1000), 'rep': rep(rows_b, lambda w: w, nshuf=2), 'first_V': my_chi(fb), 'last_V': my_chi(lb)},
                'join': {'len_raw': my_len(tj), 'len_merged': my_len([a2.merge(w) for w in tj]), 'zipf': my_zipf(tj, 1000), 'rep': rep(rows_j, lambda w: w, nshuf=2), 'first_V': my_chi(fj), 'last_V': my_chi(lj)}}
# comma-join per Currier language
for L in ('A', 'B'):
    r = [l for l in rows_j if l['lang'] == L]; t = [w for l in r for w in l['words']]
    OUT['comma'][f'join_{L}'] = {'tokens': len(t), 'len_merged': my_len([a2.merge(w) for w in t]), 'rep_identical_pct': rep(r, lambda w: w, nshuf=1)['identical_pct']}
print('comma', json.dumps(OUT['comma'], indent=0))

# ------------------------------------------------------------------ 9. corpus audit
def audit(words):
    n = len(words); c = collections.Counter(words)
    return {'tokens': n, 'non_ascii_pct': round(100 * sum(1 for w in words if not w.isascii()) / n, 2), 'one_letter_pct': round(100 * sum(1 for w in words if len(w) == 1) / n, 2),
            'roman_numeral_like_pct': round(100 * sum(1 for w in words if re.fullmatch(r'[ivxlcdm]{2,}', w) and w not in ('mi', 'di', 'vi', 'li', 'dic', 'vim', 'civil', 'dixi', 'vidi', 'mild')) / n, 3),
            'top10': c.most_common(10), 'len': my_len(words)}
OUT['corpus'] = {}
for lg in ('la', 'it', 'de', 'en', 'da'):
    ws = a2.language_sample(lg, 34116); OUT['corpus'][lg] = audit(ws)
    if lg == 'it':
        lat = {'et', 'in', 'non', 'est', 'ad', 'cum', 'ut', 'quod', 'de', 'sed', 'ac', 'atque', 'enim', 'autem', 'esse', 'qui', 'quae', 'per', 'ex', 'nec'}
        ita = {'che', 'di', 'e', 'la', 'il', 'non', 'per', 'si', 'con', 'le', 'se', 'del', 'della', 'lo', 'li', 'gli', 'una', 'uno', 'ma', 'sua'}
        # windowed: fraction of 500-word windows where Latin function words outnumber Italian ones
        win = 500; nl = ni = 0
        for i in range(0, len(ws) - win, win):
            w = ws[i:i + win]; a = sum(1 for x in w if x in lat); b = sum(1 for x in w if x in ita)
            nl += a > b; ni += b >= a
        OUT['corpus'][lg]['latin_dominated_500w_windows'] = nl; OUT['corpus'][lg]['italian_dominated_500w_windows'] = ni
        # Italian-only subsample: windows where Italian dominates
        it_only = []
        for i in range(0, len(ws) - win, win):
            w = ws[i:i + win]
            if sum(1 for x in w if x in ita) > sum(1 for x in w if x in lat): it_only.extend(w)
        OUT['corpus'][lg]['italian_only_windows'] = {'tokens': len(it_only), 'len': my_len(it_only), 'zipf': my_zipf(it_only, 1000)}
        # nonsense OCR tokens: types occurring once with length >= 12 or containing unusual clusters
    if lg == 'la':
        ae = a2.gutenberg_words(a2.T50 / 'corp_la_227.txt')[2000:2000 + 17059]; co = a2.gutenberg_words(a2.T50 / 'corp_la_33849.txt')[2000:2000 + 17059]
        OUT['corpus']['la_books'] = {'aeneid': audit(ae), 'confessiones': audit(co)}
print('corpus', json.dumps(OUT['corpus'], indent=0, ensure_ascii=False))

# ------------------------------------------------------------------ 10. word-length dispersion of languages after removing 1-letter words / and of Latin with abbreviation? (skip)
OUT['lang_len_excl_L1'] = {lg: my_len([w for w in a2.language_sample(lg, 34116) if len(w) > 1]) for lg in ('la', 'it', 'de', 'en', 'da')}
print(OUT['lang_len_excl_L1'])

(RES / 'v_a2.json').write_text(json.dumps(OUT, indent=1, ensure_ascii=False), encoding='utf-8')
print('written', RES / 'v_a2.json')
