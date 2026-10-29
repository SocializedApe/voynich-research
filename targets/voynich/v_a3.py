"""v_a3.py -- adversarial re-check of a3 (word grammar / slot rigidity).
Pure Python 3.12. Does not modify a3 files. Writes results/v_a3.json and results/v_a3.md.

Checks:
 1. reload Voynich P tokens independently; token/type counts; cost of a3's published order recomputed
 2. own order search (different init, more restarts) -> is a3's 0.1596 a true minimum?
 3. pair-violation fraction BY WORD LENGTH (global order and per-length refit) and LENGTH-MATCHED resample
 4. adjacent-pair-only violation fraction
 5. independent transliteration: GC2a-n (Claston v101) P tokens, raw symbols
 6. corpus diagnostics: Gutenberg per-file token counts + stale-footer-index leak; Italian corpus language mix
 7. Italian-only re-sample (lines classified by function words) -> pair-violation
 8. Latin re-segmented at letter-defined boundaries (segmentation-artefact control)
 9. Rugg generator fitted to Latin (does the 3-column generator lower ANY corpus to ~0.12?)
10. one-edit fraction re-implemented (brute Levenshtein on a sample) vs a3 numbers
"""
import os as _os  # local paths (the September 2026 scripts hard-coded another machine)
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_CORP = _os.path.join(_HERE, 'data', 'corpora')  # corp_<lang>_<gutenberg id>.txt, see fetch_corpora.py
_EXT = _os.path.join(_HERE, 'data', 'external')  # third-party data (Naibbe, Gaskell & Bowern)
_IT = _os.path.join(_CORP, 'corpus_it.txt')  # vatican5 OCR corpus from the September sample's first words (fetch_corpora.py)
import re, json, random, collections, pathlib, sys, time
sys.path.insert(0, _HERE)
import a3_wordgrammar as A   # read-only reuse of loaders / grammar functions

BASE = A.BASE; RES = BASE / 'results'; RES.mkdir(exist_ok=True)
T0 = time.time()
out = {}

# ---------------------------------------------------------------- own primitives
def prec_counts(tokens):
    prec = collections.Counter(); typec = collections.Counter(tokens)
    for w, c in typec.items():
        for i in range(len(w)):
            for j in range(i+1, len(w)):
                if w[i] != w[j]: prec[(w[i], w[j])] += c
    return prec, typec

def cost_of(order, prec):
    rank = {s: i for i, s in enumerate(order)}
    return sum(c for (x, y), c in prec.items() if rank[x] > rank[y])

def my_best_order(prec, typec, restarts=40, seed=99):
    """Independent LOP heuristic: init by mean relative position, insertion local search, 40 restarts."""
    rnd = random.Random(seed)
    syms = sorted({s for w in typec for s in w})
    n = len(syms); idx = {s: i for i, s in enumerate(syms)}
    W = [[0]*n for _ in range(n)]
    for (x, y), c in prec.items(): W[idx[x]][idx[y]] = c
    acc = collections.defaultdict(lambda: [0.0, 0])
    for w, c in typec.items():
        L = len(w)
        for i, s in enumerate(w): acc[s][0] += c*(i/(L-1) if L > 1 else 0.5); acc[s][1] += c
    def cost(o): return sum(W[o[b]][o[a]] for a in range(n) for b in range(a+1, n))
    def ls(o):
        cur = cost(o); imp = True
        while imp:
            imp = False
            for i in range(n):
                s = o[i]; rest = o[:i]+o[i+1:]
                bestc, bestp = cur, i
                for p in range(n):
                    cand = rest[:p]+[s]+rest[p:]
                    c = cost(cand)
                    if c < bestc: bestc, bestp = c, p
                if bestp != i:
                    o = rest[:bestp]+[s]+rest[bestp:]; cur = bestc; imp = True
        return o, cur
    init = sorted(range(n), key=lambda i: acc[syms[i]][0]/max(1, acc[syms[i]][1]))
    bo, bc = ls(init)
    for r in range(restarts):
        o = bo[:]
        for _ in range(4):
            i, j = rnd.randrange(n), rnd.randrange(n); o[i], o[j] = o[j], o[i]
        o, c = ls(o)
        if c < bc: bo, bc = o, c
    return [syms[i] for i in bo], bc, sum(prec.values())

def pv(tokens, restarts=12):
    prec, typec = prec_counts(tokens)
    order, c, tot = A.best_order(prec, [s for s, _ in collections.Counter(''.join(tokens)).most_common()], restarts=restarts)
    return order, c/tot, typec, prec

def pv_by_length(tokens, order, lengths=(2, 3, 4, 5, 6, 7, 8)):
    """pair-violation fraction restricted to words of length L, (a) under the given global order, (b) refit on length-L words."""
    res = {}
    for L in lengths:
        sub = [w for w in tokens if len(w) == L]
        if len(sub) < 200: continue
        prec, typec = prec_counts(sub)
        tot = sum(prec.values())
        if tot == 0: continue
        g = cost_of(order, prec)/tot
        syms = [s for s, _ in collections.Counter(''.join(sub)).most_common()]
        o2, c2, _ = A.best_order(prec, syms, restarts=6)
        res[L] = {'n_tokens': len(sub), 'global_order': round(g, 4), 'refit': round(c2/tot, 4)}
    return res

def adjacent_violation(tokens, order):
    rank = {s: i for i, s in enumerate(order)}
    bad = tot = 0
    for w in tokens:
        for a, b in zip(w, w[1:]):
            if a != b:
                tot += 1; bad += rank[a] > rank[b]
    return bad/tot if tot else None

def length_matched(tokens, target_tokens, seed=17):
    """resample `tokens` (with replacement within each length) to the length histogram of target_tokens."""
    rnd = random.Random(seed)
    byL = collections.defaultdict(list)
    for w in tokens: byL[len(w)].append(w)
    need = collections.Counter(len(w) for w in target_tokens)
    outt = []
    for L, k in need.items():
        pool = byL.get(L)
        if not pool:
            # nearest available length
            Ls = sorted(byL); Lc = min(Ls, key=lambda x: abs(x-L)); pool = byL[Lc]
        outt.extend(rnd.choice(pool) for _ in range(k))
    return outt

# ---------------------------------------------------------------- 1. reload + a3 order cost
voy_m = A.load_voynich(merged=True); voy_r = A.load_voynich(merged=False)
N = len(voy_m)
# independent reload
tok2 = []
with open(BASE/'data'/'ZL3b-n.words.tsv', encoding='utf-8') as f:
    next(f)
    for l in f:
        fl = l.rstrip('\n').split('\t')
        if fl[2] == 'P':
            for w in fl[9].split():
                if '?' not in w and not (set(w) - set('acdefghiklmnopqrsty')): tok2.append(w)
d = json.load(open(RES/'a3.json', encoding='utf-8'))
a3v = d['corpora']['voy_merged']
prec_m, typec_m = prec_counts(voy_m)
cost_a3 = cost_of(a3v['order_raw'], prec_m)
out['reload'] = {'N_a3': d['N_tokens'], 'N_mine_raw': len(tok2), 'N_mine_merged': N, 'match': tok2 == voy_r,
                 'types_merged': len(typec_m), 'a3_types': a3v['n_types'],
                 'a3_pair_violation_weight': a3v['pair_violation_weight'], 'recomputed_cost_of_a3_order': cost_a3,
                 'pair_total_mine': sum(prec_m.values()), 'a3_total': a3v['pair_total_weight'],
                 'P_words_total_incl_dropped': None}
print('reload', out['reload'], flush=True)

# dropped-word audit
allP = []; dropped = collections.Counter()
with open(BASE/'data'/'ZL3b-n.words.tsv', encoding='utf-8') as f:
    next(f)
    for l in f:
        fl = l.rstrip('\n').split('\t')
        if fl[2] == 'P':
            for w in fl[9].split():
                allP.append(w)
                if '?' in w: dropped['?'] += 1
                elif set(w) - set('acdefghiklmnopqrsty'): dropped['nonEVA:' + ''.join(sorted(set(w) - set('acdefghiklmnopqrsty')))] += 1
out['reload']['P_words_total_incl_dropped'] = len(allP); out['reload']['dropped'] = dict(dropped.most_common(12))
# merged alphabet stragglers
sym = collections.Counter(''.join(voy_m)); out['reload']['merged_symbol_freq'] = {A.symname(k): v for k, v in sym.most_common()}
strag = [w for w in voy_m if 'c' in w or 'h' in w]
out['reload']['straggler_words_c_h'] = strag[:10]

# ---------------------------------------------------------------- 2. own order search
o_mine, c_mine, tot = my_best_order(prec_m, typec_m)
out['order_search'] = {'a3_frac': round(a3v['pair_violation_weight']/a3v['pair_total_weight'], 5), 'mine_frac': round(c_mine/tot, 5),
                       'mine_order': [A.symname(s) for s in o_mine], 'a3_order': a3v['order']}
print('order search', out['order_search'], flush=True)

# ---------------------------------------------------------------- corpora
la, la_files = A.load_gutenberg('la', N); de, de_files = A.load_gutenberg('de', N); en, en_files = A.load_gutenberg('en', N)
it = A.load_italian(N)
corp = {'voy_merged': voy_m, 'voy_raw': voy_r, 'la': la, 'it': it, 'de': de, 'en': en,
        'voy_merged_shuf': A.shuffle_within(voy_m), 'la_shuf': A.shuffle_within(la)}

# ---------------------------------------------------------------- 5. GC2a-n (v101) independent transliteration
gc = []; gc_chars = collections.Counter()
with open(BASE/'data'/'GC2a-n.words.tsv', encoding='utf-8') as f:
    next(f)
    for l in f:
        fl = l.rstrip('\n').split('\t')
        if fl[2] == 'P':
            for w in fl[9].split():
                if '?' in w or '@' in w or "'" in w: continue
                gc.append(w); gc_chars.update(w)
out['gc_v101'] = {'n_tokens_P': len(gc), 'n_types': len(set(gc)), 'alphabet': len(gc_chars),
                  'mean_len': round(sum(map(len, gc))/len(gc), 2), 'top_chars': ''.join(k for k, _ in gc_chars.most_common(40))}
corp['gc_v101'] = gc[:N] if len(gc) >= N else gc
corp['gc_v101_shuf'] = A.shuffle_within(corp['gc_v101'])

# ---------------------------------------------------------------- 6. corpus diagnostics
diag = {}
for lang in ['la', 'de', 'en']:
    files = sorted(A.CORP.glob(f'corp_{lang}_*.txt')); rows = []; cum = 0
    for p in files:
        t = p.read_text(encoding='utf-8', errors='replace')
        i = t.find('*** START OF'); j = t.find('*** END OF')
        k = t.find('\n', i)+1 if i >= 0 else 0
        body = t[k:j] if j >= 0 else t[k:]
        ntok = len(A.LETTER.findall(body.lower()))
        # a3 keeps t[k : k+j] -> leaks t[j : j+k] of footer when file exhausted
        leak = len(A.LETTER.findall(t[j:j+k].lower())) if j >= 0 else 0
        used_before = cum; cum += ntok
        rows.append({'file': p.name, 'title_line': re.sub(r'\s+', ' ', t[i:t.find('\n', i)]) if i >= 0 else '(no START marker)',
                     'body_tokens': ntok, 'footer_leak_tokens_if_exhausted': leak,
                     'exhausted_within_N': used_before + ntok < N, 'first_words': ' '.join(A.LETTER.findall(body.lower())[:12])})
    diag[lang] = rows
# Italian corpus composition
LAT = set('et in ad cum quod est ut non atque sed enim autem esse quam sunt qui quae ab ex de pro per'.split())
ITA = set('di che il la non per con del della le lo una delle dei nel alla che si più sua suo era'.split())
LAT -= ITA & LAT  # 'non','per','de' ambiguous -> drop from both
ITA -= {'non', 'per', 'de'}; LAT -= {'non', 'per', 'de'}
win = 1000; comp = []
for s in range(0, N, win):
    seg = it[s:s+win]; l = sum(w in LAT for w in seg); i_ = sum(w in ITA for w in seg)
    comp.append((s, l, i_))
lat_tok = sum(w in LAT for w in it); ita_tok = sum(w in ITA for w in it)
diag['it'] = {'latin_marker_tokens': lat_tok, 'italian_marker_tokens': ita_tok,
              'windows_1000_latin_dominated': sum(1 for _, l, i_ in comp if l > i_), 'windows_total': len(comp),
              'first_20': ' '.join(it[:20]), 'composition_by_window': comp}
out['corpus_diag'] = diag
print('diag it', {k: v for k, v in diag['it'].items() if k != 'composition_by_window'}, flush=True)
for lang in ['la', 'de', 'en']: print('diag', lang, [(r['file'], r['body_tokens'], r['exhausted_within_N'], r['footer_leak_tokens_if_exhausted']) for r in diag[lang]], flush=True)

# ---------------------------------------------------------------- 7. Italian-only resample (line classification)
it_only = []
with open(A.IT_CORPUS, encoding='utf-8', errors='replace') as f:
    for line in f:
        ws = A.LETTER.findall(line.lower())
        if not ws: continue
        l = sum(w in LAT for w in ws); i_ = sum(w in ITA for w in ws)
        if i_ >= 2 and i_ > 2*l: it_only.extend(ws)
        if len(it_only) >= N: break
it_only = it_only[:N]
# corpus_it.txt is a single line -> line filter is void; use 50-token windows: keep windows with 0 Latin markers and >=2 Italian markers
allit = A.LETTER.findall(A.IT_CORPUS.read_text(encoding='utf-8', errors='replace').lower())
it_only = []; kept = 0; seen = 0
for s in range(0, len(allit), 50):
    seg = allit[s:s+50]; seen += 1
    if sum(w in LAT for w in seg) == 0 and sum(w in ITA for w in seg) >= 2:
        it_only.extend(seg); kept += 1
    if len(it_only) >= N: break
it_only = it_only[:N]
out['it_only'] = {'n': len(it_only), 'windows_kept': kept, 'windows_seen': seen, 'first_20': ' '.join(it_only[:20]),
                  'latin_marker_tokens': sum(w in LAT for w in it_only), 'italian_marker_tokens': sum(w in ITA for w in it_only)}
corp['it_only'] = it_only

# ---------------------------------------------------------------- 8. Latin re-segmented control
stream = ''.join(la)
def reseg(stream, brk):
    outw = []; cur = []
    for ch in stream:
        cur.append(ch)
        if ch in brk: outw.append(''.join(cur)); cur = []
    if cur: outw.append(''.join(cur))
    return outw
for name, brk in [('la_reseg_esm', set('esm')), ('la_reseg_vowels', set('aeiou')), ('la_reseg_st', set('st'))]:
    ws = reseg(stream, brk)[:N]
    corp[name] = ws
    out.setdefault('reseg_meanlen', {})[name] = round(sum(map(len, ws))/len(ws), 2)

# ---------------------------------------------------------------- 9. Rugg fitted to Latin and to English
def rugg_fit(tokens, seed=7):
    typec = collections.Counter(tokens); ng, parse = A.ngram_grammar(typec)
    words, sizes = A.rugg_generator(typec, parse, len(tokens), seed=seed)
    return words, sizes, ng['cov_tokens'], ng['cov_types']
rl, rl_sizes, rl_ct, rl_cy = rugg_fit(la); corp['rugg_la'] = rl
re_, re_sizes, re_ct, re_cy = rugg_fit(en); corp['rugg_en'] = re_
out['rugg_fits'] = {'rugg_la': {'columns': rl_sizes, 'la_ngram_cov_tok': round(rl_ct, 3), 'la_ngram_cov_typ': round(rl_cy, 3)},
                    'rugg_en': {'columns': re_sizes, 'en_ngram_cov_tok': round(re_ct, 3), 'en_ngram_cov_typ': round(re_cy, 3)}}

# ---------------------------------------------------------------- 3+4. run pair-violation, per-length, adjacency on all
main = {}
for name, toks in corp.items():
    t1 = time.time()
    order, frac, typec, prec = pv(toks)
    byL = pv_by_length(toks, order)
    adj = adjacent_violation(toks, order)
    lm = None
    if name not in ('voy_merged', 'voy_raw', 'gc_v101'):
        lmt = length_matched(toks, voy_m)
        o2, f2, _, _ = pv(lmt)
        lm = round(f2, 4)
    main[name] = {'n_tokens': len(toks), 'n_types': len(typec), 'mean_len': round(sum(map(len, toks))/len(toks), 2),
                  'pair_violation_frac': round(frac, 4), 'adjacent_only_violation_frac': round(adj, 4),
                  'length_matched_to_voynich_pair_violation': lm, 'by_length': byL,
                  'order': ' '.join(A.symname(s) if name.startswith('voy_merged') else s for s in order)}
    print(f"{name:18s} n={len(toks)} typ={len(typec)} len={main[name]['mean_len']} pv={frac:.4f} adj={adj:.4f} lm={lm} "
          + ' '.join(f"L{L}:{v['global_order']}/{v['refit']}" for L, v in byL.items()) + f"  {time.time()-t1:.0f}s", flush=True)
out['main'] = main

# ---------------------------------------------------------------- 11. slot-grammar coverage (a3 functions) on length-matched samples + v101
cov = {}
for name in ['voy_merged', 'gc_v101', 'la', 'it', 'it_only', 'de', 'en', 'la_reseg_esm', 'voy_merged_shuf']:
    toks = corp[name]
    for tag, tt in [('as_is', toks)] + ([('length_matched', length_matched(toks, voy_m))] if name not in ('voy_merged', 'gc_v101', 'voy_merged_shuf') else []):
        tc = collections.Counter(tt); ng, _ = A.ngram_grammar(tc)
        prec_, _ = prec_counts(tt); order_, _, _ = A.best_order(prec_, [s for s, _ in collections.Counter(''.join(tt)).most_common()], restarts=4)
        zg = A.zone_grammar(tc, order_) if len(order_) <= 34 else None
        cov[f'{name}/{tag}'] = {'types': len(tc), 'mean_len': round(sum(map(len, tt))/len(tt), 2), 'ngram_cov_tok': round(ng['cov_tokens'], 3), 'ngram_cov_typ': round(ng['cov_types'], 3),
                                'zone_cov_tok': round(zg['cov_tokens'], 3) if zg else None, 'zone_cov_typ': round(zg['cov_types'], 3) if zg else None}
        print('coverage', f'{name}/{tag}', cov[f'{name}/{tag}'], flush=True)
out['coverage'] = cov

# ---------------------------------------------------------------- 10. one-edit re-implementation (brute force on all types, O(T^2) via bucketing by length)
def one_edit_brute(types):
    byL = collections.defaultdict(list)
    for w in types: byL[len(w)].append(w)
    def lev1(a, b):
        if len(a) == len(b): return sum(x != y for x, y in zip(a, b)) == 1
        if len(a) > len(b): a, b = b, a
        i = 0
        while i < len(a) and a[i] == b[i]: i += 1
        return a[i:] == b[i+1:]
    has = 0
    for w in types:
        L = len(w); ok = False
        for L2 in (L-1, L, L+1):
            for v in byL.get(L2, ()):
                if v != w and lev1(w, v): ok = True; break
            if ok: break
        has += ok
    return has/len(types)
rnd = random.Random(3)
types_v = list(typec_m); samp = rnd.sample(types_v, 1500)
# brute on a 1500-type sample against ALL types
byL = collections.defaultdict(list)
for w in types_v: byL[len(w)].append(w)
def lev1(a, b):
    if len(a) == len(b): return sum(x != y for x, y in zip(a, b)) == 1
    if len(a) > len(b): a, b = b, a
    i = 0
    while i < len(a) and a[i] == b[i]: i += 1
    return a[i:] == b[i+1:]
has = 0
for w in samp:
    ok = any(v != w and lev1(w, v) for L2 in (len(w)-1, len(w), len(w)+1) for v in byL.get(L2, ()))
    has += ok
a3_oe, _ = A.one_edit_fraction(typec_m, 1)
out['one_edit_check'] = {'a3_function_all_types': round(a3_oe, 4), 'brute_force_sample1500': round(has/len(samp), 4)}
print('one-edit', out['one_edit_check'], flush=True)

out['seconds'] = round(time.time()-T0)
json.dump(out, open(RES/'v_a3.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

# ---------------------------------------------------------------- markdown
L = ['# v_a3: adversarial re-check of a3', '',
     f"Reload: a3 N={out['reload']['N_a3']}, mine N={out['reload']['N_mine_merged']} (identical token list: {out['reload']['match']}); "
     f"P words before filtering {out['reload']['P_words_total_incl_dropped']}, dropped {out['reload']['dropped']}", '',
     f"a3 order cost recomputed: {out['reload']['recomputed_cost_of_a3_order']} / {out['reload']['pair_total_mine']} (a3 reports {a3v['pair_violation_weight']} / {a3v['pair_total_weight']}). "
     f"Own LOP heuristic: {out['order_search']['mine_frac']} vs a3 {out['order_search']['a3_frac']}.", '',
     '| corpus | tokens | types | mean len | pair-viol | adjacent-only viol | length-matched to Voynich | L3 glob/refit | L4 | L5 | L6 | L7 |', '|---|---|---|---|---|---|---|---|---|---|---|---|']
for k, r in main.items():
    b = r['by_length']
    cell = lambda L_: f"{b[L_]['global_order']}/{b[L_]['refit']}" if L_ in b else '-'
    L.append(f"| {k} | {r['n_tokens']} | {r['n_types']} | {r['mean_len']} | {r['pair_violation_frac']} | {r['adjacent_only_violation_frac']} | {r['length_matched_to_voynich_pair_violation']} | {cell(3)} | {cell(4)} | {cell(5)} | {cell(6)} | {cell(7)} |")
L += ['', '## Corpus diagnostics', '']
for lang in ['la', 'de', 'en']:
    for r in diag[lang]:
        L.append(f"- {lang} {r['file']}: {r['title_line']} | body tokens {r['body_tokens']} | exhausted within N: {r['exhausted_within_N']} | footer tokens leaked by stale index if exhausted: {r['footer_leak_tokens_if_exhausted']} | starts: {r['first_words']}")
L.append(f"- it (corpus_it.txt first {N} tokens): Latin marker tokens {diag['it']['latin_marker_tokens']}, Italian marker tokens {diag['it']['italian_marker_tokens']}, "
         f"1000-token windows Latin-dominated {diag['it']['windows_1000_latin_dominated']}/{diag['it']['windows_total']}; starts: {diag['it']['first_20']}")
L.append(f"- it_only (50-token windows with 0 Latin markers, >=2 Italian markers): {out['it_only']}")
L += ['', '## Slot-grammar coverage (a3 functions, budgets 20/40/30) as-is vs length-matched to Voynich', '', '| corpus/sample | types | mean len | ngram cov tok | ngram cov typ | zone cov tok | zone cov typ |', '|---|---|---|---|---|---|---|']
for k, r in cov.items(): L.append(f"| {k} | {r['types']} | {r['mean_len']} | {r['ngram_cov_tok']} | {r['ngram_cov_typ']} | {r['zone_cov_tok']} | {r['zone_cov_typ']} |")
L += ['', f"GC v101 (Claston) P tokens: {out['gc_v101']}", '', f"Re-segmented Latin mean lengths: {out['reseg_meanlen']}", '',
      f"Rugg fits: {out['rugg_fits']}", '', f"One-edit check: {out['one_edit_check']}", '', f"runtime {out['seconds']} s"]
(RES/'v_a3.md').write_text('\n'.join(L), encoding='utf-8')
print('written', RES/'v_a3.md', out['seconds'], 's')
