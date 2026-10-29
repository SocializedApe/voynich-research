"""v_a6.py -- adversarial re-check of a6_structure.py (Voynich A/B structure, ZL3b-n EVA).
Independent re-implementation of the key numbers plus targeted probes:
  A  data hygiene: tokens with IVTFF high-ASCII codes '@nnn;' or apostrophes left in by parse_ivtff
  B  sub-word A/B rates recomputed (P only; all loci; Takahashi IT2a-n as second transliteration)
  C  per-folio %-edy / %ed distributions: gap between A and B, leave-one-out accuracy of the threshold rule
  D  'no natural-language pair shifts one word-final pattern from 0.2% to 17%': max suffix/prefix shift for every pair
  E  part 3 recompute (Jaccard, token coverage, top-100, JSD) for the key pairs; top-100 overlap at 3315 tokens; which top-100 words are missing
  F  part 4: correct bound of chi2/n; recompute whole-MS and within-B; within ONE scribe (hand 2) section analysis with shuffle + Italian + Latin controls
  G  part 2 entropies recomputed
Pure Python 3.12. Writes results/v_a6.json and results/v_a6.md. Does not touch a6 files.
"""
import os as _os  # local paths (the September 2026 scripts hard-coded another machine)
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_CORP = _os.path.join(_HERE, 'data', 'corpora')  # corp_<lang>_<gutenberg id>.txt, see fetch_corpora.py
_EXT = _os.path.join(_HERE, 'data', 'external')  # third-party data (Naibbe, Gaskell & Bowern)
_IT = _os.path.join(_CORP, 'corpus_it.txt')  # vatican5 OCR corpus from the September sample's first words (fetch_corpora.py)
import collections, math, random, re, json, pathlib
random.seed(66)
ROOT = pathlib.Path(_HERE)
SCR = pathlib.Path(_CORP)
IT = pathlib.Path(_IT)
OUT = ROOT / 'results'; OUT.mkdir(exist_ok=True)
R = {}; MD = []
def md(s=''): MD.append(s)

def load(fname):
    rows = [l.rstrip('\n').split('\t') for l in open(ROOT/'data'/fname, encoding='utf-8')][1:]
    out = []
    for r in rows:
        folio, line_id, ltype, lang, hand, illus, quire, ps, pe, words = r
        out.append(dict(folio=folio, ltype=ltype, lang=lang, hand=hand, illus=illus, quire=quire, words=[w for w in words.split() if '?' not in w]))
    return out
ZL = load('ZL3b-n.words.tsv'); P = [L for L in ZL if L['ltype']=='P']
tokA = [w for L in P if L['lang']=='A' for w in L['words']]; tokB = [w for L in P if L['lang']=='B' for w in L['words']]
nA, nB = len(tokA), len(tokB)
md('# v_a6: adversarial re-check of a6_structure.py')
md(f'P tokens: A={nA}, B={nB}, all P={sum(len(L["words"]) for L in P)} (a6 reported 10768 / 22905 / 34212).')
R['counts'] = dict(nA=nA, nB=nB, nP=sum(len(L['words']) for L in P))

# ---------------------------------------------------------------- A. data hygiene
bad = [w for L in P for w in L['words'] if not w.isalpha() or not w.islower()]
R['A_hygiene'] = dict(n_nonalpha_tokens=len(bad), examples=bad[:15], n_types_affected=len(set(bad)),
                      note="parse_ivtff leaves IVTFF high-ASCII codes '@nnn;' and apostrophes (uncertain-space marker) inside words; ~0.3% of P tokens")
md(f"\n## A. Data hygiene\n{len(bad)} of {R['counts']['nP']} P tokens ({100*len(bad)/R['counts']['nP']:.2f}%) contain non-letters (IVTFF '@nnn;' codes, apostrophes): e.g. {bad[:8]}. Negligible for rates, but they are spurious 'types' in the sharing statistics.")

# ---------------------------------------------------------------- B. sub-word rates
FE = {'ends -edy': lambda w: w.endswith('edy'), 'contains ed': lambda w: 'ed' in w, 'ends -eedy': lambda w: w.endswith('eedy'),
      'starts l-': lambda w: w.startswith('l'), 'ends -ain': lambda w: w.endswith('ain'), 'ends -dy': lambda w: w.endswith('dy'),
      'starts qo-': lambda w: w.startswith('qo'), 'contains ee': lambda w: 'ee' in w, 'contains cho': lambda w: 'cho' in w,
      'ends -or': lambda w: w.endswith('or'), 'ends -ol': lambda w: w.endswith('ol'), 'starts d-': lambda w: w.startswith('d'),
      'gallows in bench': lambda w: any(g in w for g in ('cth','ckh','cph','cfh')), 'contains eo': lambda w: 'eo' in w}
def rate(t, f): return 100*sum(1 for w in t if f(w))/len(t)
def rates(tA, tB): return {k: (round(rate(tA,f),2), round(rate(tB,f),2)) for k,f in FE.items()}
R['B_rates'] = {}
R['B_rates']['ZL_P'] = rates(tokA, tokB)
allA = [w for L in ZL if L['lang']=='A' for w in L['words']]; allB = [w for L in ZL if L['lang']=='B' for w in L['words']]
R['B_rates']['ZL_all_loci'] = rates(allA, allB)
try:
    IT2 = load('IT2a-n.words.tsv'); ITP = [L for L in IT2 if L['ltype']=='P']
    itA = [w for L in ITP if L['lang']=='A' for w in L['words']]; itB = [w for L in ITP if L['lang']=='B' for w in L['words']]
    R['B_rates']['IT2a_P'] = rates(itA, itB); R['B_rates']['IT2a_P_tokens'] = (len(itA), len(itB))
except Exception as e:
    R['B_rates']['IT2a_P'] = str(e)
md('\n## B. Sub-word rates (% tokens A / B)')
md('| feature | ZL P (a6 set) | ZL all loci | Takahashi IT2a P |'); md('|---|---|---|---|')
for k in FE:
    z = R['B_rates']['ZL_P'][k]; a = R['B_rates']['ZL_all_loci'][k]; t = R['B_rates']['IT2a_P'][k] if isinstance(R['B_rates']['IT2a_P'], dict) else ('-','-')
    md(f'| {k} | {z[0]} / {z[1]} | {a[0]} / {a[1]} | {t[0]} / {t[1]} |')
# after-bench check incl. how much of 'ch' is inside 'cth'-type composites (it is not: c-t-h has no 'ch'), and 'che' vs 'cho' as % of tokens
def after(tokens, bench):
    c = collections.Counter()
    for w in tokens:
        i = 0
        while (j := w.find(bench, i)) >= 0:
            c[w[j+len(bench):j+len(bench)+1] or '$'] += 1; i = j+len(bench)
    n = sum(c.values()); return n, {k: round(100*v/n,1) for k,v in c.most_common(6)}
R['B_after_bench'] = {b: dict(A=after(tokA,b), B=after(tokB,b)) for b in ('ch','sh')}
md(f"After 'ch' (n, % by next char): A {R['B_after_bench']['ch']['A']}, B {R['B_after_bench']['ch']['B']}; after 'sh': A {R['B_after_bench']['sh']['A']}, B {R['B_after_bench']['sh']['B']}")

# ---------------------------------------------------------------- C. per-folio distributions and LOO threshold
fw = collections.defaultdict(list); fm = {}
for L in P: fw[L['folio']].extend(L['words']); fm[L['folio']] = (L['lang'], L['hand'], L['illus'])
folios = [f for f in fw if len(fw[f]) >= 30 and fm[f][0] in 'AB']
def frate(f, fn): return rate(fw[f], fn)
R['C_folio'] = {}
for k in ('ends -edy', 'contains ed', 'contains cho', 'ends -dy'):
    vals = sorted((frate(f, FE[k]), fm[f][0], f) for f in folios)
    A_vals = [v for v,l,f in vals if l=='A']; B_vals = [v for v,l,f in vals if l=='B']
    # leave-one-out: fit best threshold on n-1 folios, test on held-out
    def best_thr(vs):
        best = (-1, None, None)
        cand = sorted(set(v for v,_,_ in vs)) + [1e9]
        for thr in cand:
            for d in (1,-1):
                acc = sum(1 for v,l,_ in vs if ((v >= thr) == (d==1)) == (l=='B'))
                if acc > best[0]: best = (acc, thr, d)
        return best[1], best[2]
    correct = 0
    for i in range(len(vals)):
        train = vals[:i]+vals[i+1:]; thr, d = best_thr(train); v,l,_ = vals[i]
        correct += (((v >= thr) == (d==1)) == (l=='B'))
    # intermediate band: folios between max-of-lower-class and min-of-upper-class
    R['C_folio'][k] = dict(A_max=round(max(A_vals),2), A_p90=round(sorted(A_vals)[int(0.9*len(A_vals))],2), A_median=round(sorted(A_vals)[len(A_vals)//2],2),
                           B_min=round(min(B_vals),2), B_p10=round(sorted(B_vals)[int(0.1*len(B_vals))],2), B_median=round(sorted(B_vals)[len(B_vals)//2],2),
                           loo_accuracy=round(correct/len(vals),4), n=len(vals),
                           A_top3=[(f, round(v,2)) for v,l,f in sorted(vals, reverse=True) if l=='A'][:3], B_bottom3=[(f, round(v,2)) for v,l,f in vals if l=='B'][:3])
    # histogram of per-folio values in 2%-bins (for bimodality)
    bins = collections.Counter(int(v//2)*2 for v,_,_ in vals)
    R['C_folio'][k]['hist_2pct_bins'] = {f'{b}-{b+2}': bins[b] for b in sorted(bins)}
md('\n## C. Per-folio separation (197 labelled folios with >=30 P tokens)')
for k,v in R['C_folio'].items():
    md(f"- {k}: A max {v['A_max']} (median {v['A_median']}), B min {v['B_min']} (median {v['B_median']}); leave-one-out threshold accuracy {v['loo_accuracy']*100:.1f}%; extreme A {v['A_top3']}, lowest B {v['B_bottom3']}; histogram (2%-bins) {v['hist_2pct_bins']}")

# ---------------------------------------------------------------- corpora
def gutenberg(path):
    t = path.read_text(encoding='utf-8', errors='replace'); i = t.find('*** START OF'); j = t.find('*** END OF')
    if i >= 0: t = t[t.find('\n', i)+1:]
    if j >= 0: t = t[:j]
    return t
def nw(t): return re.findall(r"[^\W\d_]+", t.lower())
def corp(lang, idx): return nw(gutenberg(SCR/f'corp_{lang}_{idx}.txt'))
it = nw(IT.read_text(encoding='utf-8', errors='replace'))
la1 = corp('la',227); la2 = [w for w in corp('la',33849)[:85000] if w != 'sidenote']
da1 = corp('da',24747); da2 = corp('da',36942); no1 = corp('no',30027); sv1 = corp('sv',59341)
en1 = corp('en',1342); en2 = corp('en',2701); de1 = corp('de',50285); de2 = corp('de',56156); nl1 = corp('nl',76280); fr1 = corp('fr',19919)
# contamination check: English function words in first nA words of each non-English corpus
eng = {'the','and','of','to','in','is','that','with','for','was','this'}
R['corpus_check'] = {name: dict(n=len(c), english_fw_per_1000_first_nA=round(1000*sum(1 for w in c[:nA] if w in eng)/nA,1), first_words=' '.join(c[:12]))
                     for name, c in [('da_24747',da1),('da_36942',da2),('no_30027',no1),('sv_59341',sv1),('de_50285',de1),('de_56156',de2),('nl_76280',nl1),('fr_19919',fr1),('la_227',la1),('la_33849',la2),('it',it)]}
md('\n## Corpus check (Gutenberg markers found in all used files; English function words per 1000 in first nA words; first words)')
for k,v in R['corpus_check'].items(): md(f"- {k}: n={v['n']}, eng fw/1000={v['english_fw_per_1000_first_nA']}, starts '{v['first_words']}'")

# ---------------------------------------------------------------- D. max suffix/prefix shift per pair
Brand = random.sample(tokB, nA)
PAIRS = [('Voynich A vs B(random nA)', tokA, Brand), ('Voynich A half vs A half', [w for L in P if L['lang']=='A' and L['folio'] in sorted({L['folio'] for L in P if L['lang']=='A'})[::2] for w in L['words']][:nA//2], [w for L in P if L['lang']=='A' and L['folio'] in sorted({L['folio'] for L in P if L['lang']=='A'})[1::2] for w in L['words']][:nA//2]),
         ('Danish vs Norwegian', da1[:nA], no1[:nA]), ('Danish vs Swedish', da1[:nA], sv1[:nA]), ('Danish vs Danish', da1[:nA], da2[:nA]),
         ('English vs English', en1[:nA], en2[:nA]), ('German vs German', de1[:nA], de2[:nA]), ('German vs Dutch', de1[:nA], nl1[:nA]),
         ('Vergil vs Augustine', la1[:nA], la2[:nA]), ('Latin vs Italian', la2[:nA], it[:nA]), ('French vs Italian', fr1[:nA], it[:nA])]
def shape_feats(tokens):
    n = len(tokens); c = collections.Counter()
    for w in tokens:
        for k in (1,2,3):
            if len(w) >= k: c['-'+w[-k:]] += 1; c[w[:k]+'-'] += 1
    return {k: 100*v/n for k,v in c.items()}
R['D_shift'] = {}
md('\n## D. Largest single word-final / word-initial pattern shift between the two sides (% of tokens)')
md('a6 claims no natural-language pair shifts one word-final pattern from 0.2% to 17%. For each pair: top-3 features by absolute difference, and top-3 by ratio among features with >=3% on one side.')
for name, X, Y in PAIRS:
    fx, fy = shape_feats(X), shape_feats(Y); keys = set(fx)|set(fy)
    byabs = sorted(keys, key=lambda k: -abs(fx.get(k,0)-fy.get(k,0)))[:3]
    def ratio(k):
        a, b = fx.get(k,0), fy.get(k,0); lo_, hi_ = min(a,b), max(a,b)
        return hi_/max(lo_, 0.05)
    byrat = sorted([k for k in keys if max(fx.get(k,0),fy.get(k,0)) >= 3], key=lambda k: -ratio(k))[:3]
    R['D_shift'][name] = dict(by_abs=[(k, round(fx.get(k,0),2), round(fy.get(k,0),2)) for k in byabs], by_ratio=[(k, round(fx.get(k,0),2), round(fy.get(k,0),2), round(ratio(k),1)) for k in byrat])
    md(f"- {name}: abs {R['D_shift'][name]['by_abs']}; ratio {R['D_shift'][name]['by_ratio']}")

# ---------------------------------------------------------------- E. part 3 recompute
def share(X, Y):
    tx, ty = collections.Counter(X), collections.Counter(Y); sx, sy = set(tx), set(ty); inter = sx & sy
    return dict(jaccard=round(len(inter)/len(sx|sy),4), typesX_in_Y=round(len(inter)/len(sx),4), tokX_in_Y=round(sum(v for w,v in tx.items() if w in sy)/len(X),4),
                top100_X_in_Y=sum(1 for w,_ in tx.most_common(100) if w in sy)/100, top100_missing=[w for w,_ in tx.most_common(100) if w not in sy][:12])
def jsd(X, Y):
    cx, cy = collections.Counter(X), collections.Counter(Y); nx, ny = len(X), len(Y); keys = set(cx)|set(cy)
    tot = 0
    for w in keys:
        p, q = cx[w]/nx, cy[w]/ny; m = (p+q)/2
        if p: tot += 0.5*p*math.log2(p/m)
        if q: tot += 0.5*q*math.log2(q/m)
    return round(tot,4)
R['E_share'] = {}
md('\n## E. Vocabulary sharing recomputed (independent code, new random B sample) -- jaccard / typesX_in_Y / tokX_in_Y / top100 / JSD bits')
for name, X, Y in PAIRS:
    s = share(X, Y); s['jsd'] = jsd(X, Y) if len(X)==len(Y) else None; R['E_share'][name] = s
    md(f"- {name}: {s['jaccard']} / {s['typesX_in_Y']} / {s['tokX_in_Y']} / {s['top100_X_in_Y']} / {s['jsd']}; top-100 words of X missing in Y: {s['top100_missing']}")
# sample-size dependence of top-100 overlap: 3315 tokens per side
R['E_top100_at_3315'] = {name: share(X[:3315], Y[:3315])['top100_X_in_Y'] for name, X, Y in PAIRS}
md(f"Top-100 overlap at 3315 tokens/side (a6's B-herbal vs A-herbal = 0.72, A-herbal vs A-pharma = 0.77): {R['E_top100_at_3315']}")

# ---------------------------------------------------------------- F. part 4: bound, recompute, within-hand-2
def topic_stats(tb, minfreq=20):
    secs = list(tb); sizes = {s: len(tb[s]) for s in secs}; N = sum(sizes.values())
    per = {s: collections.Counter(tb[s]) for s in secs}; tot = collections.Counter()
    for s in secs: tot.update(per[s])
    out = []
    for w, n in tot.items():
        if n < minfreq: continue
        chi = sum((per[s][w]-n*sizes[s]/N)**2/(n*sizes[s]/N) for s in secs)
        out.append((w, n, chi/n, max(secs, key=lambda s: per[s][w]/sizes[s])))
    return out, sizes
def summ(st):
    c = sorted(x[2] for x in st)
    return dict(n_words=len(st), mean=round(sum(c)/len(c),4), median=round(c[len(c)//2],4), frac_gt_0_5=round(sum(1 for x in c if x>0.5)/len(c),4), top10=[(w,n,round(x,3),p) for w,n,x,p in sorted(st, key=lambda t: -t[1]*t[2])[:10]])
tb = collections.defaultdict(list)
for L in P: tb[L['illus']].extend(L['words'])
tb = {s:v for s,v in tb.items() if len(v) >= 500}
N = sum(len(v) for v in tb.values()); pmin = min(len(v) for v in tb.values())/N
R['F_bound'] = dict(claimed='chi2/n bounded by #sections-1', correct='chi2/n <= (1-p_min)/p_min where p_min = smallest section share', whole_ms=round((1-pmin)/pmin,1), n_sections_minus_1=len(tb)-1)
st, sizes = topic_stats(tb); R['F_whole'] = summ(st)
def controls(tb, label):
    sizes_ = {s: len(v) for s,v in tb.items()}; res = {}
    st, _ = topic_stats(tb); res['voynich'] = summ(st)
    toks = [w for v in tb.values() for w in v]; sh = []
    for rep in range(5):
        random.shuffle(toks); pos = 0; t2 = {}
        for s in tb: t2[s] = toks[pos:pos+sizes_[s]]; pos += sizes_[s]
        sh.append(summ(topic_stats(t2)[0])['mean'])
    res['shuffled_mean_of_5'] = round(sum(sh)/5,4)
    for cname, C in (('italian_spread', it), ('latin_augustine_spread', la2)):
        stp = len(C)//len(tb); t3 = {}
        for k, s in enumerate(tb): t3[s] = C[k*stp:k*stp+sizes_[s]]
        res[cname] = summ(topic_stats(t3)[0])
    # Italian second placement (offset by half a step) to see control variance
    stp = len(it)//len(tb); t4 = {}
    for k, s in enumerate(tb): t4[s] = it[k*stp+stp//2:k*stp+stp//2+sizes_[s]]
    res['italian_spread_offset'] = summ(topic_stats(t4)[0])
    res['sizes'] = sizes_
    return res
R['F_within_B'] = controls({s:[w for L in P if L['lang']=='B' and L['illus']==s for w in L['words']] for s in 'HTBS'}, 'within B')
tb2 = {s:[w for L in P if L['hand']=='2' and L['illus']==s for w in L['words']] for s in 'HBTC'}
tb2 = {s:v for s,v in tb2.items() if len(v) >= 400}
R['F_within_hand2'] = controls(tb2, 'within hand 2')
tb1 = {s:[w for L in P if L['hand']=='1' and L['illus']==s for w in L['words']] for s in 'HP'}
R['F_within_hand1'] = controls(tb1, 'within hand 1 (H vs P)')
md('\n## F. Section-specific vocabulary')
md(f"chi2/n bound: a6 says '#sections-1' ({len(tb)-1}); correct bound is (1-p_min)/p_min = {R['F_bound']['whole_ms']} for the whole-MS section sizes (equal only when sections are equal-sized). Does not affect any reported number.")
md(f"Whole MS recomputed: n_words {R['F_whole']['n_words']}, mean chi2/n {R['F_whole']['mean']}, median {R['F_whole']['median']}, frac>0.5 {R['F_whole']['frac_gt_0_5']} (a6: 257, 0.654, 0.487, 0.486)")
for key in ('F_within_B', 'F_within_hand2', 'F_within_hand1'):
    r = R[key]
    md(f"{key} sizes {r['sizes']}: Voynich mean {r['voynich']['mean']} (n_words {r['voynich']['n_words']}, frac>0.5 {r['voynich']['frac_gt_0_5']}); shuffled {r['shuffled_mean_of_5']}; Italian spread {r['italian_spread']['mean']} / offset placement {r['italian_spread_offset']['mean']}; Latin spread {r['latin_augustine_spread']['mean']}")
    md(f"  top words by chi2 (word, n, chi2/n, peak): {r['voynich']['top10']}")

# ---------------------------------------------------------------- G. part 2 entropies
def H(c): n = sum(c.values()); return -sum(v/n*math.log2(v/n) for v in c.values() if v)
def Hcond(lines, tgt, giv):
    g = collections.defaultdict(collections.Counter)
    for L in lines: g[tuple(L[k] for k in giv)][L[tgt]] += 1
    n = len(lines); return sum(sum(c.values())/n*H(c) for c in g.values())
LS = [L for L in ZL if L['lang'] in 'AB' and L['hand'] != '?']
R['G_entropy'] = dict(n=len(LS), H_lang=round(H(collections.Counter(L['lang'] for L in LS)),4), H_lang_hand=round(Hcond(LS,'lang',['hand']),4), H_lang_section=round(Hcond(LS,'lang',['illus']),4), H_lang_quire=round(Hcond(LS,'lang',['quire']),4),
                      mixed_cells={k: dict(v) for k, v in collections.Counter((L['hand'],L['illus'],L['lang']) for L in LS).items() if False} )
cells = collections.defaultdict(collections.Counter)
for L in LS: cells[(L['hand'],L['illus'])][L['lang']] += 1
R['G_entropy']['mixed_cells'] = {f'hand{h}_{s}': dict(c) for (h,s),c in cells.items() if len(c) > 1}
R['G_entropy']['note'] = 'lang and hand are page-header variables ($L, $H) in IVTFF, so per-folio constancy is by construction, not a finding'
md(f"\n## G. Entropies recomputed (all loci, {len(LS)} lines): H(lang)={R['G_entropy']['H_lang']}, H(lang|hand)={R['G_entropy']['H_lang_hand']}, H(lang|section)={R['G_entropy']['H_lang_section']}, H(lang|quire)={R['G_entropy']['H_lang_quire']}; mixed cells {R['G_entropy']['mixed_cells']} (a6: 0.9698 / 0.0923 / 0.3984; hand3_S 80/1039)")

json.dump(R, open(OUT/'v_a6.json','w',encoding='utf-8'), indent=1, ensure_ascii=False)
open(OUT/'v_a6.md','w',encoding='utf-8').write('\n'.join(MD))
print('\n'.join(MD))
