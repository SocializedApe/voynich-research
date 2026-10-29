"""v_a4.py -- adversarial re-check of a4_selfcitation.py (Timm & Schinner self-citation test).

Pure Python 3.12.  Imports the a4 module (its main() is guarded) and re-uses its functions where the
point is to check the numbers, but recomputes the critical quantities independently:
  1. data counts and the inventory of dropped tokens
  2. ld1() vs. a full DP Levenshtein on random and adversarial pairs
  3. independent recomputation of the Voynich nearest-earlier statistics (DP Levenshtein, brute force)
     and of h1/h2 (log2), Zipf slope
  4. corpus artefacts: encoding of the Gutenberg files (a4 reads them as UTF-8 with errors='replace';
     files that are actually Latin-1/cp1252 lose every accented letter, splitting words), verse vs prose,
     and re-runs the language statistics with correct decoding and with prose-only Danish
  5. glyph-merged EVA versions of the LD-based statistics (a4 did the LD statistics on raw EVA only)
  6. a letter-trigram Markov control: words generated from a 3rd-order letter model trained on the
     Voynich tokens (and likewise on each language) -- tests whether the LD1 network / on-page LD1
     density follows from the low conditional letter entropy alone, without any copying
  7. autocopist fidelity: share of generated tokens that are real ZL word types
Writes results/v_a4.json and results/v_a4.md.
"""
import os as _os  # local paths (the September 2026 scripts hard-coded another machine)
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_CORP = _os.path.join(_HERE, 'data', 'corpora')  # corp_<lang>_<gutenberg id>.txt, see fetch_corpora.py
_EXT = _os.path.join(_HERE, 'data', 'external')  # third-party data (Naibbe, Gaskell & Bowern)
_IT = _os.path.join(_CORP, 'corpus_it.txt')  # vatican5 OCR corpus from the September sample's first words (fetch_corpora.py)
import sys, os, re, json, math, random, collections, statistics, time
BASE = _HERE
sys.path.insert(0, BASE)
import a4_selfcitation as A

OUT = os.path.join(BASE, 'results'); os.makedirs(OUT, exist_ok=True)
T0 = time.time()
RES = collections.OrderedDict()
def log(*a):
    print(*a, flush=True)

# ----------------------------------------------------------------------------- 1. data counts
zl = A.load_zl(); skel = A.skeleton(zl)
zl_words = [w for p in zl for ln in p['lines'] for w in ln['words']]
N = len(zl_words)
raw_P = 0; dropped = collections.Counter(); dropped_examples = collections.defaultdict(list)
with open(A.ZL, encoding='utf-8') as f:
    next(f)
    for l in f:
        c = l.rstrip('\n').split('\t')
        if c[2] != 'P': continue
        for w in c[9].split():
            raw_P += 1
            if not A.AZ.match(w):
                kind = 'has ?' if '?' in w else ('has @' if '@' in w else 'other non a-z')
                dropped[kind] += 1
                if len(dropped_examples[kind]) < 8: dropped_examples[kind].append(w)
RES['data'] = {'pages': len(zl), 'lines': sum(len(p) for p in skel), 'tokens_kept': N, 'tokens_raw_P': raw_P,
               'dropped': dict(dropped), 'dropped_examples': dict(dropped_examples)}
log('data', RES['data'])

# ----------------------------------------------------------------------------- 2. Levenshtein check
def lev(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]
rng = random.Random(123)
types = list(collections.Counter(zl_words))
bad = []; n_checked = 0
for _ in range(60000):
    a = rng.choice(types); b = rng.choice(types)
    if abs(len(a) - len(b)) <= 1:
        n_checked += 1
        d = lev(a, b); e = A.ld1(a, b)
        if (d <= 1) != (e <= 1) or (d == 0) != (e == 0): bad.append((a, b, d, e))
# adversarial pairs
for a, b in [('abc', 'ab'), ('abc', 'bc'), ('abc', 'ac'), ('abd', 'ac'), ('ab', 'ba'), ('aab', 'ab'), ('aba', 'aa'),
             ('daiin', 'dain'), ('chol', 'cthol'), ('qokeey', 'okeey'), ('a', ''), ('ab', 'cb'), ('abcd', 'abdc'), ('x', 'y')]:
    n_checked += 1
    d = lev(a, b); e = A.ld1(a, b)
    if (d <= 1) != (e <= 1) or (d == 0) != (e == 0): bad.append((a, b, d, e))
RES['levenshtein_check'] = {'pairs_checked': n_checked, 'disagreements': bad[:20]}
log('lev check', RES['levenshtein_check'])

# ----------------------------------------------------------------------------- 3. independent recomputation on Voynich
def nearest_earlier_bruteforce(pages, minlen=1):
    n_tok = 0; hits = []  # (dist, linediff)
    for p in pages:
        toks = [(li, w) for li, ln in enumerate(p['lines']) for w in ln['words']]
        for i, (li, w) in enumerate(toks):
            if len(w) < minlen: continue
            n_tok += 1
            for j in range(i - 1, -1, -1):
                u = toks[j][1]
                if abs(len(u) - len(w)) <= 1 and lev(u, w) <= 1:
                    hits.append((i - j, li - toks[j][0])); break
    d = [h[0] for h in hits]
    return {'n': n_tok, 'coverage': len(hits) / n_tok, 'median': statistics.median(d) if d else None,
            'within10': sum(1 for x in d if x <= 10) / n_tok, 'within30': sum(1 for x in d if x <= 30) / n_tok,
            'prev2lines': sum(1 for h in hits if h[1] <= 2) / n_tok, 'same_line': sum(1 for h in hits if h[1] == 0) / n_tok}
t = time.time()
bf = nearest_earlier_bruteforce(zl); bf5 = nearest_earlier_bruteforce(zl, 5)
log('bruteforce voynich', bf, bf5, f'{time.time()-t:.0f}s')
a4v = A.selfcit_stats(zl)
RES['voynich_recheck'] = {'bruteforce_all': bf, 'bruteforce_len>=5': bf5,
                         'a4_function_all': a4v['nearest_earlier_LD<=1'], 'a4_function_len>=5': a4v['long_tokens_LD<=1']}

def ent(words, sep=''):
    s = sep.join(words); n = len(s)
    c1 = collections.Counter(s); h1 = -sum(v / n * math.log2(v / n) for v in c1.values())
    c2 = collections.Counter(zip(s, s[1:]))
    # exact conditional entropy H(X2|X1) = sum_x p(x) H(X2|X1=x)
    byfirst = collections.defaultdict(collections.Counter)
    for (x, y), v in c2.items(): byfirst[x][y] += v
    tot = sum(c2.values()); h2 = 0.0
    for x, cy in byfirst.items():
        nx = sum(cy.values())
        h2 += nx / tot * -sum(v / nx * math.log2(v / nx) for v in cy.values())
    return round(h1, 4), round(h2, 4)
h1, h2 = ent(zl_words); h1s, h2s = ent(zl_words, ' ')
def zipf(words, maxrank=1000):
    f = sorted(collections.Counter(words).values(), reverse=True)[:maxrank]
    xs = [math.log10(r) for r in range(1, len(f) + 1)]; ys = [math.log10(v) for v in f]
    mx = sum(xs) / len(xs); my = sum(ys) / len(ys)
    return round(sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs), 4), f[-1], f[99]
RES['voynich_recheck'].update({'h1_h2_nospace_exact_conditional': (h1, h2), 'h1_h2_withspace': (h1s, h2s),
                               'zipf_slope_f1000_f100': zipf(zl_words), 'a4_general': {k: v for k, v in A.general_stats(zl_words).items() if k != 'top10'}})
log('entropy/zipf', RES['voynich_recheck']['h1_h2_nospace_exact_conditional'], RES['voynich_recheck']['zipf_slope_f1000_f100'])

# ----------------------------------------------------------------------------- 4. corpus artefacts
def read_text(path):
    b = open(path, 'rb').read()
    try:
        return b.decode('utf-8'), 'utf-8'
    except UnicodeDecodeError:
        return b.decode('cp1252', errors='replace'), 'cp1252'
LET = re.compile(r'[^a-zà-öø-ÿœæßþð]+')   # excludes the ÷ sign that a4's à-ÿ range includes
def gut_words(path):
    t, enc = read_text(path)
    i = t.find('*** START OF')
    if i >= 0: t = t[t.find('\n', i) + 1:]
    k = t.find('*** END OF')
    if k >= 0: t = t[:k]
    return [w for w in LET.split(t.lower()) if w], enc
corp_info = {}
def lang_words_fixed(files, need):
    words = []; encs = []
    for fn in files:
        w, enc = gut_words(os.path.join(A.CORP, fn)); words.extend(w); encs.append((fn, enc, len(w)))
        if len(words) >= need: break
    return words[:need], encs
allfiles = sorted(fn for fn in os.listdir(A.CORP) if fn.startswith('corp_') and fn.endswith('.txt'))
enc_report = {}
for fn in allfiles:
    t, enc = read_text(os.path.join(A.CORP, fn))
    m = re.search(r'\*\*\* START OF[^\n]*', t)
    enc_report[fn] = {'encoding': enc, 'title': m.group(0)[:80] if m else None}
RES['corpus_files'] = enc_report

# a4's own loader (utf-8 errors=replace) vs fixed loader: how many words differ?
langsets = collections.OrderedDict()
for lang in ['la', 'it', 'de', 'en', 'da']:
    a4w = A.lang_words(lang, N)
    if lang == 'it':
        fixed = a4w; encs = [('corpus_it.txt', 'utf-8', None)]
    else:
        files = [fn for fn in allfiles if fn.startswith(f'corp_{lang}_')]
        fixed, encs = lang_words_fixed(files, N)
    diff = sum(1 for a, b in zip(a4w, fixed) if a != b)
    nonascii_fixed = sum(1 for w in fixed if not w.isascii())
    onechar = sum(1 for w in fixed if len(w) == 1) / N
    langsets[lang] = {'a4': a4w, 'fixed': fixed}
    corp_info[lang] = {'files_used': encs, 'a4_vs_fixed_positions_differ': diff, 'a4_types': len(set(a4w)), 'fixed_types': len(set(fixed)),
                       'fixed_words_with_nonascii_letter': nonascii_fixed, 'frac_1char_tokens_fixed': round(onechar, 4),
                       'a4_first_words': ' '.join(a4w[:25]), 'fixed_first_words': ' '.join(fixed[:25])}
    log(lang, {k: v for k, v in corp_info[lang].items() if 'first' not in k})
# Danish prose only: skip the poetry volume (24747) -> which files are prose is decided from the titles printed in enc_report
da_files = [fn for fn in allfiles if fn.startswith('corp_da_')]
RES['corpus_info'] = corp_info

def key_stats(pages, words):
    s = A.selfcit_stats(pages); g = A.general_stats(words); tn = A.type_network(words)
    sh = A.selfcit_stats(A.shuffle_within_page(pages)); sg = A.selfcit_stats(A.shuffle_global(pages))
    a = s['nearest_earlier_LD<=1']
    return {'cover': round(a['coverage'], 3), 'median': a['median_distance_given_hit'], 'within10': round(a['frac_all_within_10'], 3),
            'within30': round(a['frac_all_within_30'], 3), 'prev2': round(a['frac_all_within_prev2lines'], 3),
            'within10_wpshuf': round(sh['nearest_earlier_LD<=1']['frac_all_within_10'], 3),
            'within10_gshuf': round(sg['nearest_earlier_LD<=1']['frac_all_within_10'], 3),
            'long5_within10': round(s['long_tokens_LD<=1']['frac_all_within_10'], 3), 'long5_cover': round(s['long_tokens_LD<=1']['coverage'], 3),
            'page_anyLD1': round(s['frac_tokens_with_any_page_neighbour_LD<=1'], 3), 'page_exact': round(s['frac_tokens_with_exact_repeat_on_page'], 3),
            'page_LD1other': round(s['frac_tokens_with_LD1_other_type_on_page'], 3),
            'net_types_nb': round(tn['frac_types_with_LD1_neighbour'], 3), 'net_giant': round(tn['giant_component_frac_types'], 3),
            'types': g['types'], 'h1': g['h1_letters'], 'h2': g['h2_letters'], 'zipf': g['zipf_slope_r1_1000'],
            'hapax_types': g['hapax_frac_types'], 'hapax_tokens': g['hapax_frac_tokens'], 'wlen_mean': g['wordlen_mean'], 'wlen_var': g['wordlen_var'],
            'adj_rep': g['adjacent_repeat_rate'], 'top5': ' '.join(w for w, c in g['top10'][:5])}
CMP = collections.OrderedDict()
CMP['voynich_raw'] = key_stats(zl, zl_words)
for lang in ['la', 'it', 'de', 'en', 'da']:
    CMP[f'{lang}_a4decode'] = key_stats(A.pour(langsets[lang]['a4'], skel), langsets[lang]['a4'])
    if lang in ('de', 'da'):
        CMP[f'{lang}_fixeddecode'] = key_stats(A.pour(langsets[lang]['fixed'], skel), langsets[lang]['fixed'])
    log(lang, 'done')
# Danish prose only (exclude poetry volume 24747; the ordering puts it first)
da_prose_files = [fn for fn in da_files if '24747' not in fn]
da_prose, encs = lang_words_fixed(da_prose_files, N)
corp_info['da_prose'] = {'files_used': encs, 'first_words': ' '.join(da_prose[:25])}
CMP['da_prose_fixed'] = key_stats(A.pour(da_prose, skel), da_prose)
# Latin prose (skip Aeneid 227 if another Latin file is prose)
la_files = [fn for fn in allfiles if fn.startswith('corp_la_') and '227' not in fn]
la_alt, encs = lang_words_fixed(la_files, N)
corp_info['la_alt'] = {'files_used': encs, 'first_words': ' '.join(la_alt[:25])}
CMP['la_alt_fixed'] = key_stats(A.pour(la_alt, skel), la_alt)
# English without the Saintsbury preface: start the English corpus at 'Chapter I' of Pride and Prejudice
en_all, _ = lang_words_fixed([fn for fn in allfiles if fn.startswith('corp_en_')], 10 ** 7)
txt = ' '.join(en_all)
k = txt.find('it is a truth universally acknowledged')
en_body = txt[k:].split()[:N] if k >= 0 else en_all[:N]
corp_info['en_body'] = {'preface_words_skipped': len(txt[:k].split()) if k >= 0 else None}
CMP['en_body_fixed'] = key_stats(A.pour(en_body, skel), en_body)
log('corpus variants done', f'{time.time()-T0:.0f}s')

# ----------------------------------------------------------------------------- 5. glyph-merged LD statistics for Voynich
MERGE_A = [('cfh', 'F'), ('cph', 'P'), ('ckh', 'K'), ('cth', 'T'), ('ch', 'C'), ('sh', 'S'), ('iiin', 'M'), ('iin', 'N'), ('in', 'n'), ('ee', 'E')]  # keeps i-count distinct
MERGE_B = A.MERGE   # a4's merge: in/iin/iiin all -> N (equates dain/daiin/daiiin)
def merge_with(w, table):
    out = []; i = 0
    while i < len(w):
        for s, r in table:
            if w.startswith(s, i): out.append(r); i += len(s); break
        else: out.append(w[i]); i += 1
    return ''.join(out)
def merged_pages(pages, table):
    return [{'folio': p['folio'], 'lines': [{'words': [merge_with(w, table) for w in ln['words']], 'para_start': ln['para_start']} for ln in p['lines']]} for p in pages]
for nm, tb in [('voynich_mergeA_icount_kept', MERGE_A), ('voynich_mergeB_a4', MERGE_B)]:
    mp = merged_pages(zl, tb); mw = [w for p in mp for ln in p['lines'] for w in ln['words']]
    CMP[nm] = key_stats(mp, mw)
    CMP[nm]['n_types_after_merge'] = len(set(mw))
log('merged done')

# ----------------------------------------------------------------------------- 6. Markov letter-trigram control
def markov_words(words, n, seed=5, order=2):
    rng = random.Random(seed)
    trans = collections.defaultdict(collections.Counter)
    for w in words:
        s = '^' * order + w + '$'
        for i in range(order, len(s)):
            trans[s[i - order:i]][s[i]] += 1
    tables = {k: (list(c.keys()), list(c.values())) for k, c in trans.items()}
    out = []
    while len(out) < n:
        ctx = '^' * order; w = ''
        while True:
            ks, vs = tables[ctx]
            ch = rng.choices(ks, vs)[0]
            if ch == '$': break
            w += ch; ctx = (ctx + ch)[-order:]
            if len(w) > 20: break
        if w: out.append(w)
    return out
for nm, src in [('markov3_voynich', zl_words), ('markov3_da_prose', da_prose), ('markov3_de_fixed', langsets['de']['fixed']),
                ('markov3_it', langsets['it']['a4']), ('markov3_en', en_body)]:
    mw = markov_words(src, N); CMP[nm] = key_stats(A.pour(mw, skel), mw)
    # how many generated types are real types of the source?
    st = set(src); CMP[nm]['frac_tokens_that_are_real_source_types'] = round(sum(1 for w in mw if w in st) / N, 3)
    log(nm, 'done', f'{time.time()-T0:.0f}s')
# also order-3 (4-gram) for Voynich
mw = markov_words(zl_words, N, order=3); CMP['markov4_voynich'] = key_stats(A.pour(mw, skel), mw)
st = set(zl_words); CMP['markov4_voynich']['frac_tokens_that_are_real_source_types'] = round(sum(1 for w in mw if w in st) / N, 3)
RES['comparison'] = CMP

# ----------------------------------------------------------------------------- 7. autocopist fidelity
ac = A.Autocopist(19).generate(skel); acw = [w for p in ac for ln in p['lines'] for w in ln['words']]
zl_cnt = collections.Counter(zl_words); zl_types = set(zl_cnt); zl_freq2 = {w for w, c in zl_cnt.items() if c >= 2}
ac_cnt = collections.Counter(acw)
def ttype_share(words):
    n = len(words)
    return {'i_type': round(sum(1 for w in words if 'i' in w) / n, 3), 'dy_or_y_final': round(sum(1 for w in words if w.endswith('y')) / n, 3),
            'gallows_initial': round(sum(1 for w in words if w[0] in 'ktpf') / n, 3), 'qo_initial': round(sum(1 for w in words if w.startswith('qo')) / n, 3),
            'ch_sh_initial': round(sum(1 for w in words if w.startswith(('ch', 'sh'))) / n, 3), 'contains_e': round(sum(1 for w in words if 'e' in w) / n, 3),
            'contains_ee': round(sum(1 for w in words if 'ee' in w) / n, 3)}
RES['autocopist_fidelity'] = {
    'frac_tokens_in_ZL_types': round(sum(1 for w in acw if w in zl_types) / N, 3),
    'frac_tokens_in_ZL_types_freq>=2': round(sum(1 for w in acw if w in zl_freq2) / N, 3),
    'frac_types_in_ZL_types': round(sum(1 for w in ac_cnt if w in zl_types) / len(ac_cnt), 3),
    'top20_autocopist_s19': ac_cnt.most_common(20), 'voynich_profile': ttype_share(zl_words), 'autocopist_profile': ttype_share(acw),
    'note': 'for reference: fraction of ZL P tokens whose type also occurs in ZL is 1 by definition; a Voynichese generator should reach a high share of real types'}
log('autocopist', RES['autocopist_fidelity'])

RES['_meta'] = {'runtime_s': round(time.time() - T0, 1)}
json.dump(RES, open(os.path.join(OUT, 'v_a4.json'), 'w'), indent=1, default=str)

# ----------------------------------------------------------------------------- markdown
cols = ['cover', 'median', 'within10', 'within10_wpshuf', 'within10_gshuf', 'prev2', 'long5_within10', 'long5_cover', 'page_exact', 'page_LD1other',
        'net_types_nb', 'net_giant', 'types', 'h1', 'h2', 'zipf', 'hapax_types', 'hapax_tokens', 'wlen_mean', 'wlen_var', 'adj_rep']
L = ['# v_a4: re-check of a4', '', f'ZL P text: {N} tokens, {len(zl)} pages, {RES["data"]["lines"]} lines; raw P tokens {raw_P}; dropped {dict(dropped)}', '',
     f'Levenshtein check: {n_checked} pairs, disagreements: {len(bad)}', '',
     f'Voynich brute-force nearest-earlier (DP Levenshtein): {bf}', f'len>=5: {bf5}', '',
     f'h1/h2 no space (exact conditional): {h1}/{h2}; with space {h1s}/{h2s}; zipf (slope, f at rank 1000, f at rank 100): {zipf(zl_words)}', '',
     '## corpus files', '']
for fn, d in enc_report.items(): L.append(f'- {fn}: {d["encoding"]}, {d["title"]}')
L += ['', '## corpus loaders', '']
for k, d in corp_info.items(): L.append(f'- {k}: ' + json.dumps({a: b for a, b in d.items()}, default=str)[:600])
L += ['', '## comparison table', '', '| corpus | ' + ' | '.join(cols) + ' |', '|' + '---|' * (len(cols) + 1)]
for nm, d in CMP.items(): L.append(f'| {nm} | ' + ' | '.join(str(d.get(c, '')) for c in cols) + ' |')
L += ['', 'top5: ' + '; '.join(f'{nm}: {d["top5"]}' for nm, d in CMP.items()), '',
      'Markov controls: frac tokens that are real source types: ' + ', '.join(f'{nm}={d["frac_tokens_that_are_real_source_types"]}' for nm, d in CMP.items() if 'markov' in nm), '',
      '## autocopist fidelity', '', json.dumps(RES['autocopist_fidelity'], default=str, indent=1)]
open(os.path.join(OUT, 'v_a4.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
log('written', f'{time.time()-T0:.0f}s')
