"""a6_structure.py -- internal structure of the Voynich MS text (ZL3b-n, paragraph text).
(1) unsupervised Currier A/B recovery from per-folio word / merged-glyph-bigram distributions
(2) lang x hand x section cross-tabulation, conditional entropies
(3) vocabulary sharing A<->B calibrated against Latin/Italian/Germanic corpora
(4) section-specific 'topic' words (chi-square + KL) calibrated against natural language and shuffled text
Pure Python 3.12, no third-party packages. Writes results/a6.json and results/a6.md
"""
import os as _os  # local paths (the September 2026 scripts hard-coded another machine)
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_CORP = _os.path.join(_HERE, 'data', 'corpora')  # corp_<lang>_<gutenberg id>.txt, see fetch_corpora.py
_EXT = _os.path.join(_HERE, 'data', 'external')  # third-party data (Naibbe, Gaskell & Bowern)
_IT = _os.path.join(_CORP, 'corpus_it.txt')  # vatican5 OCR corpus from the September sample's first words (fetch_corpora.py)
import collections, math, random, re, json, pathlib, itertools
random.seed(6)
ROOT = pathlib.Path(_HERE)
SCR = pathlib.Path(_CORP)
IT = pathlib.Path(_IT)
OUT = ROOT / 'results'; OUT.mkdir(exist_ok=True)
R = {}   # results dict
MD = []  # markdown lines
def md(s=''): MD.append(s)

# ---------------------------------------------------------------- load Voynich
rows = [l.rstrip('\n').split('\t') for l in open(ROOT/'data'/'ZL3b-n.words.tsv', encoding='utf-8')][1:]
LINES = []
for r in rows:
    folio, line_id, ltype, lang, hand, illus, quire, ps, pe, words = r
    ws = [w for w in words.split() if '?' not in w]
    LINES.append(dict(folio=folio, line=line_id, ltype=ltype, lang=lang, hand=hand, illus=illus, quire=quire, words=ws))
P = [L for L in LINES if L['ltype'] == 'P']
ntok = sum(len(L['words']) for L in P)
R['data'] = dict(file='ZL3b-n.words.tsv', lines_all=len(LINES), lines_P=len(P), tokens_P=ntok,
                 tokens_all=sum(len(L['words']) for L in LINES))
md('# a6: internal structure of the Voynich text (ZL3b-n, EVA)')
md(f"Paragraph text (locus P) only unless stated: {len(P)} lines, {ntok} clean tokens (words with ? dropped); all loci: {R['data']['tokens_all']} tokens.")

# ---------------------------------------------------------------- glyph merge
MERGE_BASIC = [('ckh','K'),('cth','T'),('cph','P'),('cfh','F'),('ch','C'),('sh','S'),('iiin','M'),('iin','N'),('in','I'),('eee','3'),('ee','E')]
def merge(w, table=MERGE_BASIC):
    for a,b in table: w = w.replace(a,b)
    return w
R['glyph_merge'] = {'basic': MERGE_BASIC}

# ================================================================ PART 1: unsupervised A/B
md('\n## 1. Unsupervised recovery of the Currier A/B split')
folio_words = collections.defaultdict(list); folio_meta = {}
for L in P:
    folio_words[L['folio']].extend(L['words']); folio_meta[L['folio']] = (L['lang'], L['hand'], L['illus'])
MINTOK = 30
folios = [f for f in folio_words if len(folio_words[f]) >= MINTOK]
md(f"Folios with >= {MINTOK} paragraph tokens: {len(folios)} (of {len(folio_words)}); lang labels among them: " +
   str(dict(collections.Counter(folio_meta[f][0] for f in folios))))
allc = collections.Counter(w for f in folios for w in folio_words[f])
TOPW = [w for w,_ in allc.most_common(300)]
def vec_words(f, feats=TOPW):
    c = collections.Counter(folio_words[f]); n = len(folio_words[f])
    return [math.sqrt(c[w]/n) for w in feats]   # Hellinger embedding of relative frequencies
def bigrams_of(words):
    out = collections.Counter()
    for w in words:
        m = '^' + merge(w) + '$'
        for i in range(len(m)-1): out[m[i:i+2]] += 1
    return out
allbg = collections.Counter()
for f in folios: allbg.update(bigrams_of(folio_words[f]))
TOPBG = [b for b,_ in allbg.most_common(200)]
def vec_bg(f, feats=TOPBG):
    c = bigrams_of(folio_words[f]); n = sum(c.values())
    return [math.sqrt(c[b]/n) for b in feats]

def kmeans(X, k=2, restarts=30, iters=100):
    best = None
    for r in range(restarts):
        cent = random.sample(X, k)
        for _ in range(iters):
            lab = [min(range(k), key=lambda j: sum((a-b)**2 for a,b in zip(x, cent[j]))) for x in X]
            new = []
            for j in range(k):
                mem = [x for x,l in zip(X,lab) if l == j]
                new.append([sum(col)/len(mem) for col in zip(*mem)] if mem else random.choice(X))
            if new == cent: break
            cent = new
        inertia = sum(min(sum((a-b)**2 for a,b in zip(x,c)) for c in cent) for x in X)
        if best is None or inertia < best[0]: best = (inertia, lab)
    return best[1]
def ward(X, k=2):
    n = len(X); clusters = {i: [i] for i in range(n)}; cent = {i: list(X[i]) for i in range(n)}
    def d(i,j):
        ni, nj = len(clusters[i]), len(clusters[j])
        return (ni*nj/(ni+nj)) * sum((a-b)**2 for a,b in zip(cent[i], cent[j]))
    D = {(i,j): d(i,j) for i in clusters for j in clusters if i < j}
    while len(clusters) > k:
        (i,j) = min(D, key=D.get)
        ni, nj = len(clusters[i]), len(clusters[j])
        cent[i] = [(a*ni + b*nj)/(ni+nj) for a,b in zip(cent[i], cent[j])]
        clusters[i] += clusters.pop(j); del cent[j]
        D = {key: v for key, v in D.items() if j not in key}
        for m in clusters:
            if m != i: D[(min(i,m), max(i,m))] = d(i,m)
    lab = [0]*n
    for ci, (c, mem) in enumerate(clusters.items()):
        for m in mem: lab[m] = ci
    return lab
def agreement(lab, folios):
    idx = [i for i,f in enumerate(folios) if folio_meta[f][0] in 'AB']
    truth = [folio_meta[folios[i]][0] for i in idx]; pred = [lab[i] for i in idx]
    best = 0; bestmap = None
    for mp in ({0:'A',1:'B'}, {0:'B',1:'A'}):
        acc = sum(1 for t,p in zip(truth,pred) if mp[p] == t)/len(idx)
        if acc > best: best, bestmap = acc, mp
    conf = collections.Counter((t, bestmap[p]) for t,p in zip(truth,pred))
    mis = [folios[i] for i,(t,p) in zip(idx, zip(truth,pred)) if bestmap[p] != t]
    unl = collections.Counter(bestmap[lab[i]] for i,f in enumerate(folios) if folio_meta[f][0] == '?')
    return dict(accuracy=round(best,4), n_labelled=len(idx), confusion={f'true{t}_pred{p}': v for (t,p),v in sorted(conf.items())},
                misassigned=mis, unlabelled_folios_assigned=dict(unl)), bestmap
R['part1'] = {}
Xw = [vec_words(f) for f in folios]; Xb = [vec_bg(f) for f in folios]
for name, X, algo in [('words300_hellinger_kmeans', Xw, kmeans), ('words300_hellinger_ward', Xw, ward),
                      ('mergedbigram200_hellinger_kmeans', Xb, kmeans), ('mergedbigram200_hellinger_ward', Xb, ward)]:
    lab = algo(X); res, mp = agreement(lab, folios); R['part1'][name] = res
    md(f"- {name}: agreement with Currier lang on {res['n_labelled']} labelled folios = {res['accuracy']*100:.1f}%; confusion {res['confusion']}; misassigned: {', '.join(res['misassigned']) or 'none'}; '?' folios -> {res['unlabelled_folios_assigned']}")
# which features separate A and B (token-level, P text)
tokA = [w for L in P if L['lang']=='A' for w in L['words']]; tokB = [w for L in P if L['lang']=='B' for w in L['words']]
cA, cB = collections.Counter(tokA), collections.Counter(tokB); nA, nB = len(tokA), len(tokB)
R['part1']['tokens_A'] = nA; R['part1']['tokens_B'] = nB
def lo(w):
    return math.log(((cB[w]+0.5)/(nB+1)) / ((cA[w]+0.5)/(nA+1)))
cand = [w for w in set(cA)|set(cB) if cA[w]+cB[w] >= 30]
cand.sort(key=lo)
featA = [(w, cA[w], cB[w], round(1000*cA[w]/nA,2), round(1000*cB[w]/nB,2), round(lo(w),2)) for w in cand[:20]]
featB = [(w, cA[w], cB[w], round(1000*cA[w]/nA,2), round(1000*cB[w]/nB,2), round(lo(w),2)) for w in cand[::-1][:20]]
R['part1']['most_A_words'] = featA; R['part1']['most_B_words'] = featB
md(f"\nToken-level A vs B (P text, A={nA} tokens, B={nB} tokens). Format: word nA/nB (per-mille A/per-mille B, log-odds B over A, +0.5 smoothing), words with >= 30 tokens.")
md('Most A-specific: ' + '; '.join(f"{w} {a}/{b} ({pa}/{pb}, {l})" for w,a,b,pa,pb,l in featA))
md('Most B-specific: ' + '; '.join(f"{w} {a}/{b} ({pa}/{pb}, {l})" for w,a,b,pa,pb,l in featB))
named = ['chedy','shedy','qokeedy','qokedy','qokain','qokaiin','chol','chor','daiin','dain','ol','or','shol','sho','cho','okeey','oteey','qol','lchedy','aiin','dar','dal','chey','shey','ar','al','okaiin','otaiin','saiin']
R['part1']['named_words'] = {w: dict(A=cA[w], B=cB[w], permilleA=round(1000*cA[w]/nA,2), permilleB=round(1000*cB[w]/nB,2), logodds_B_over_A=round(lo(w),2)) for w in named}
md('Named diagnostic words (per-mille A / per-mille B): ' + '; '.join(f"{w} {R['part1']['named_words'][w]['permilleA']}/{R['part1']['named_words'][w]['permilleB']}" for w in named))
def rate(tokens, pred):
    return sum(1 for w in tokens if pred(w))/len(tokens)
subf = {
 'word ends -dy': lambda w: w.endswith('dy'), 'word ends -edy': lambda w: w.endswith('edy'), 'word ends -eedy': lambda w: w.endswith('eedy'),
 'word ends -y': lambda w: w.endswith('y'), 'word ends -in': lambda w: w.endswith('in'), 'word ends -aiin': lambda w: w.endswith('aiin'),
 'word ends -ol': lambda w: w.endswith('ol'), 'word ends -or': lambda w: w.endswith('or'), 'word ends -l': lambda w: w.endswith('l'), 'word ends -r': lambda w: w.endswith('r'),
 'word ends -ain': lambda w: w.endswith('ain'), 'word ends -am': lambda w: w.endswith('am'),
 'word starts qo-': lambda w: w.startswith('qo'), 'word starts ch-': lambda w: w.startswith('ch'), 'word starts sh-': lambda w: w.startswith('sh'),
 'word starts o-': lambda w: w.startswith('o'), 'word starts d-': lambda w: w.startswith('d'), 'word starts y-': lambda w: w.startswith('y'), 'word starts s-': lambda w: w.startswith('s'),
 'word starts ok-/ot-': lambda w: w.startswith(('ok','ot')), 'word starts l-': lambda w: w.startswith('l'),
 'contains ed': lambda w: 'ed' in w, 'contains eed': lambda w: 'eed' in w, 'contains eo': lambda w: 'eo' in w, 'contains cho': lambda w: 'cho' in w, 'contains che': lambda w: 'che' in w,
 'contains cth/ckh/cph/cfh': lambda w: any(g in w for g in ('cth','ckh','cph','cfh')), 'contains k': lambda w: 'k' in w, 'contains t': lambda w: 't' in w, 'contains p': lambda w: 'p' in w, 'contains f': lambda w: 'f' in w,
 'contains l': lambda w: 'l' in w, 'contains ee': lambda w: 'ee' in w, 'contains ii': lambda w: 'ii' in w, 'contains ai': lambda w: 'ai' in w, 'contains m': lambda w: 'm' in w,
}
R['part1']['subword_features'] = {k: dict(A=round(100*rate(tokA,f),2), B=round(100*rate(tokB,f),2), ratio_B_over_A=round(rate(tokB,f)/max(rate(tokA,f),1e-9),2)) for k,f in subf.items()}
md('\nSub-word features (% of tokens, A / B / ratio B:A): ' + '; '.join(f"{k} {v['A']}/{v['B']}/{v['ratio_B_over_A']}" for k,v in R['part1']['subword_features'].items()))
def after_bench(tokens, bench):
    c = collections.Counter()
    for w in tokens:
        i = 0
        while True:
            j = w.find(bench, i)
            if j < 0: break
            nxt = w[j+len(bench):j+len(bench)+1] or '$'
            c[nxt] += 1; i = j+len(bench)
    n = sum(c.values()); return n, {k: round(100*v/n,1) for k,v in c.most_common()}
R['part1']['after_bench'] = {}
for bench in ('ch','sh'):
    nAb, dA = after_bench(tokA, bench); nBb, dB = after_bench(tokB, bench)
    R['part1']['after_bench'][bench] = dict(n_A=nAb, n_B=nBb, A=dA, B=dB)
    keys = sorted(set(dA)|set(dB), key=lambda k: -(dA.get(k,0)+dB.get(k,0)))
    md(f"Character after '{bench}' (% of {bench} occurrences, $ = word end; A n={nAb}, B n={nBb}): " + '; '.join(f"{k}: {dA.get(k,0)}/{dB.get(k,0)}" for k in keys[:10]))
def folio_rate(f, pred): ws = folio_words[f]; return sum(1 for w in ws if pred(w))/len(ws)
R['part1']['single_feature_folio_accuracy'] = {}
for k in ['word ends -edy','word ends -dy','contains ed','word starts qo-','word ends -ol','contains cho','contains che','word ends -aiin','contains l']:
    lab_f = [f for f in folios if folio_meta[f][0] in 'AB']
    vals = sorted((folio_rate(f, subf[k]), folio_meta[f][0]) for f in lab_f)
    best = 0; bt = None
    for i in range(len(vals)+1):
        thr = vals[i][0] if i < len(vals) else 1.1
        for direction in (1,-1):
            acc = sum(1 for v,l in vals if ((v >= thr) == (direction==1)) == (l=='B'))/len(vals)
            if acc > best: best, bt = acc, (round(thr*100,2), 'B if >=' if direction==1 else 'B if <')
    R['part1']['single_feature_folio_accuracy'][k] = dict(accuracy=round(best,4), threshold_pct=bt[0], rule=bt[1])
md('Best single-feature per-folio rule accuracy (threshold fitted on the same folios, so optimistic): ' + '; '.join(f"{k}: {v['accuracy']*100:.1f}% ({v['rule']} {v['threshold_pct']}%)" for k,v in R['part1']['single_feature_folio_accuracy'].items()))

# ================================================================ PART 2: lang x hand x section
md('\n## 2. Language x scribe (Davis hand) x section, line level')
def crosstab(lines, keys):
    return collections.Counter(tuple(L[k] for k in keys) for L in lines)
def entropy(counter):
    n = sum(counter.values()); return -sum(v/n*math.log2(v/n) for v in counter.values() if v)
def cond_entropy(lines, target, given):
    n = len(lines); tot = 0
    for g, grp in itertools.groupby(sorted(lines, key=lambda L: tuple(L[k] for k in given)), key=lambda L: tuple(L[k] for k in given)):
        grp = list(grp); c = collections.Counter(L[target] for L in grp); tot += len(grp)/n*entropy(c)
    return tot
R['part2'] = {}
for scope, LS in [('all_loci', [L for L in LINES if L['lang'] in 'AB' and L['hand'] != '?']), ('P_only', [L for L in P if L['lang'] in 'AB' and L['hand'] != '?'])]:
    ct = crosstab(LS, ['hand','illus','lang'])
    hands = sorted(set(L['hand'] for L in LS)); secs = sorted(set(L['illus'] for L in LS))
    tab = {}
    for h in hands:
        for s in secs:
            a, b = ct[(h,s,'A')], ct[(h,s,'B')]
            if a+b: tab[f'hand{h}_{s}'] = dict(A=a, B=b)
    Hl = entropy(collections.Counter(L['lang'] for L in LS))
    info = dict(n_lines=len(LS), H_lang_bits=round(Hl,4),
                H_lang_given_hand=round(cond_entropy(LS,'lang',['hand']),4), H_lang_given_section=round(cond_entropy(LS,'lang',['illus']),4),
                H_lang_given_hand_and_section=round(cond_entropy(LS,'lang',['hand','illus']),4),
                H_hand_given_lang=round(cond_entropy(LS,'hand',['lang']),4), H_hand_bits=round(entropy(collections.Counter(L['hand'] for L in LS)),4),
                H_section_given_lang=round(cond_entropy(LS,'illus',['lang']),4), H_section_bits=round(entropy(collections.Counter(L['illus'] for L in LS)),4),
                lang_by_hand={h: dict(collections.Counter(L['lang'] for L in LS if L['hand']==h)) for h in hands},
                lang_by_section={s: dict(collections.Counter(L['lang'] for L in LS if L['illus']==s)) for s in secs},
                hand_x_section_x_lang=tab)
    def maj_acc(keys):
        grp = collections.defaultdict(collections.Counter)
        for L in LS: grp[tuple(L[k] for k in keys)][L['lang']] += 1
        return round(sum(max(c.values()) for c in grp.values())/len(LS),4)
    info['majority_rule_accuracy'] = dict(from_hand=maj_acc(['hand']), from_section=maj_acc(['illus']), from_hand_and_section=maj_acc(['hand','illus']), from_quire=maj_acc(['quire']))
    mixed = {k: v for k,v in tab.items() if v['A'] and v['B']}
    info['mixed_hand_section_cells'] = mixed
    R['part2'][scope] = info
    md(f"\n### {scope}: {len(LS)} lines with lang in A/B and known hand")
    md('lang by hand: ' + '; '.join(f"hand {h}: A={c.get('A',0)} B={c.get('B',0)}" for h,c in info['lang_by_hand'].items()))
    md('lang by section: ' + '; '.join(f"{s}: A={c.get('A',0)} B={c.get('B',0)}" for s,c in info['lang_by_section'].items()))
    md('hand x section (A/B lines): ' + '; '.join(f"{k} {v['A']}/{v['B']}" for k,v in tab.items()))
    md(f"H(lang)={info['H_lang_bits']} bits; H(lang|hand)={info['H_lang_given_hand']}; H(lang|section)={info['H_lang_given_section']}; H(lang|hand,section)={info['H_lang_given_hand_and_section']}. "
       f"Majority-rule accuracy predicting lang: from hand {info['majority_rule_accuracy']['from_hand']*100:.1f}%, from section {info['majority_rule_accuracy']['from_section']*100:.1f}%, from both {info['majority_rule_accuracy']['from_hand_and_section']*100:.1f}%, from quire {info['majority_rule_accuracy']['from_quire']*100:.1f}%.")
    md(f"H(hand)={info['H_hand_bits']}, H(hand|lang)={info['H_hand_given_lang']}; H(section)={info['H_section_bits']}, H(section|lang)={info['H_section_given_lang']}.")
    md('Mixed cells (same hand, same section, both languages): ' + (', '.join(f"{k} A={v['A']} B={v['B']}" for k,v in mixed.items()) or 'none'))
mixedcells = [(k.split('_')[0][4:], k.split('_')[1]) for k in R['part2']['P_only']['mixed_hand_section_cells']]
R['part2']['clustering_within_mixed_cells'] = {}
for h, s in mixedcells:
    fs = [f for f in folios if folio_meta[f][1]==h and folio_meta[f][2]==s and folio_meta[f][0] in 'AB']
    if len(set(folio_meta[f][0] for f in fs)) < 2 or len(fs) < 4: continue
    lab = kmeans([vec_words(f) for f in fs]); res, _ = agreement(lab, fs)
    R['part2']['clustering_within_mixed_cells'][f'hand{h}_{s}'] = dict(n_folios=len(fs), labels=dict(collections.Counter(folio_meta[f][0] for f in fs)), kmeans_accuracy=res['accuracy'], misassigned=res['misassigned'])
md('k-means (top-300 words) restricted to folios of one hand and one section that contain both languages: ' + ('; '.join(f"{k}: {v['labels']} -> {v['kmeans_accuracy']*100:.1f}% agreement, misassigned {v['misassigned']}" for k,v in R['part2']['clustering_within_mixed_cells'].items()) or 'no such cell with >= 4 folios'))
R['part2']['features_by_hand_lang'] = {}
for h in '12345':
    for l in 'AB':
        t = [w for L in P if L['hand']==h and L['lang']==l for w in L['words']]
        if len(t) > 200: R['part2']['features_by_hand_lang'][f'hand{h}_{l}'] = dict(tokens=len(t), pct_edy=round(100*rate(t, subf['word ends -edy']),2), pct_qo=round(100*rate(t, subf['word starts qo-']),2), pct_ol=round(100*rate(t, subf['word ends -ol']),2), pct_cho=round(100*rate(t, subf['contains cho']),2))
md('Per hand x lang (tokens; %-edy, %qo-, %-ol, %cho): ' + '; '.join(f"{k} ({v['tokens']}; {v['pct_edy']}, {v['pct_qo']}, {v['pct_ol']}, {v['pct_cho']})" for k,v in R['part2']['features_by_hand_lang'].items()))
R['part2']['features_by_section_lang'] = {}
for s in 'HABCPSTZ':
    for l in 'AB':
        t = [w for L in P if L['illus']==s and L['lang']==l for w in L['words']]
        if len(t) > 200: R['part2']['features_by_section_lang'][f'{s}_{l}'] = dict(tokens=len(t), pct_edy=round(100*rate(t, subf['word ends -edy']),2), pct_qo=round(100*rate(t, subf['word starts qo-']),2), pct_ol=round(100*rate(t, subf['word ends -ol']),2), pct_cho=round(100*rate(t, subf['contains cho']),2))
md('Per section x lang (tokens; %-edy, %qo-, %-ol, %cho): ' + '; '.join(f"{k} ({v['tokens']}; {v['pct_edy']}, {v['pct_qo']}, {v['pct_ol']}, {v['pct_cho']})" for k,v in R['part2']['features_by_section_lang'].items()))

# ---- 2b: does one scribe's language shift with section? hand x section feature table; misassigned folios
R['part2']['features_by_hand_section'] = {}
for h in '12345':
    for sec in 'HABCPSTZ':
        t = [w for L in P if L['hand']==h and L['illus']==sec for w in L['words']]
        if len(t) > 200:
            R['part2']['features_by_hand_section'][f'hand{h}_{sec}'] = dict(tokens=len(t), lang=dict(collections.Counter(L['lang'] for L in P if L['hand']==h and L['illus']==sec)),
                pct_edy=round(100*rate(t, subf['word ends -edy']),2), pct_qo=round(100*rate(t, subf['word starts qo-']),2), pct_ol=round(100*rate(t, subf['word ends -ol']),2),
                pct_cho=round(100*rate(t, subf['contains cho']),2), pct_ain=round(100*rate(t, subf['word ends -ain']),2), pct_l_start=round(100*rate(t, subf['word starts l-']),2))
md('Per hand x section (tokens; lang; %-edy, %qo-, %-ol, %cho, %-ain, %l-): ' + '; '.join(f"{k} ({v['tokens']}; {v['lang']}; {v['pct_edy']}, {v['pct_qo']}, {v['pct_ol']}, {v['pct_cho']}, {v['pct_ain']}, {v['pct_l_start']})" for k,v in R['part2']['features_by_hand_section'].items()))
R['part2']['misassigned_folio_profiles'] = {}
for f in ['f58r','f58v','fRos','f57r','f48r','f88v','f90v2']:
    if f in folio_words:
        t = folio_words[f]
        R['part2']['misassigned_folio_profiles'][f] = dict(lang=folio_meta[f][0], hand=folio_meta[f][1], section=folio_meta[f][2], tokens=len(t),
            pct_edy=round(100*rate(t, subf['word ends -edy']),2), pct_qo=round(100*rate(t, subf['word starts qo-']),2), pct_ol=round(100*rate(t, subf['word ends -ol']),2), pct_cho=round(100*rate(t, subf['contains cho']),2), pct_ain=round(100*rate(t, subf['word ends -ain']),2), pct_l_start=round(100*rate(t, subf['word starts l-']),2))
md('Profiles of folios misassigned by some clustering (lang, hand, section, tokens; %-edy, %qo-, %-ol, %cho, %-ain, %l-): ' + '; '.join(f"{f}: {v['lang']},{v['hand']},{v['section']},{v['tokens']}; {v['pct_edy']}, {v['pct_qo']}, {v['pct_ol']}, {v['pct_cho']}, {v['pct_ain']}, {v['pct_l_start']}" for f,v in R['part2']['misassigned_folio_profiles'].items()))
md('Reference A overall: %-edy 0.20, %qo- 9.99, %-ol 14.52, %cho 16.12, %-ain 2.12, %l- 0.81; B overall: 17.34, 17.72, 7.08, 2.70, 5.95, 5.75')

# ================================================================ PART 3: vocabulary sharing
md('\n## 3. Vocabulary sharing between A and B, calibrated')
def gutenberg(path):
    t = path.read_text(encoding='utf-8', errors='replace')
    i = t.find('*** START OF'); j = t.find('*** END OF')
    if i >= 0: t = t[t.find('\n', i)+1:]
    if j >= 0: t = t[:j]
    return t
def norm_words(t):
    return re.findall(r"[^\W\d_]+", t.lower())
CORP = {}
def corpus(lang, idx):
    key = f'{lang}_{idx}'
    if key not in CORP: CORP[key] = norm_words(gutenberg(SCR/f'corp_{lang}_{idx}.txt'))
    return CORP[key]
def corpus_it():
    if 'it' not in CORP: CORP['it'] = norm_words(IT.read_text(encoding='utf-8', errors='replace'))
    return CORP['it']
def share(X, Y):
    tx, ty = collections.Counter(X), collections.Counter(Y)
    sx, sy = set(tx), set(ty)
    inter = sx & sy
    sx2 = {w for w,v in tx.items() if v >= 2}; sy2 = {w for w,v in ty.items() if v >= 2}
    return dict(nX=len(X), nY=len(Y), typesX=len(sx), typesY=len(sy), jaccard=round(len(inter)/len(sx|sy),4),
                typesX_in_Y=round(len(inter)/len(sx),4), typesY_in_X=round(len(inter)/len(sy),4),
                tokX_in_Y=round(sum(v for w,v in tx.items() if w in sy)/len(X),4), tokY_in_X=round(sum(v for w,v in ty.items() if w in sx)/len(Y),4),
                types_freq2_X_in_Y=round(len(sx2 & sy)/len(sx2),4), types_freq2_Y_in_X=round(len(sy2 & sx)/len(sy2),4),
                top100_X_in_Y=round(sum(1 for w,_ in tx.most_common(100) if w in sy)/100,3), top100_Y_in_X=round(sum(1 for w,_ in ty.most_common(100) if w in sx)/100,3))
N3 = nA
R['part3'] = dict(size_matched_tokens=N3, comparisons={})
folA = sorted({L['folio'] for L in P if L['lang']=='A'}); folB = sorted({L['folio'] for L in P if L['lang']=='B'})
Bord = tokB[:N3]; Brand = random.sample(tokB, N3)
comps = [('Voynich A (all) vs B (all)', tokA, tokB), ('Voynich A vs B (first nA tokens of B)', tokA, Bord), ('Voynich A vs B (random nA tokens of B)', tokA, Brand)]
A1 = [w for L in P if L['lang']=='A' and folA.index(L['folio'])%2==0 for w in L['words']]; A2 = [w for L in P if L['lang']=='A' and folA.index(L['folio'])%2==1 for w in L['words']]
B1 = [w for L in P if L['lang']=='B' and folB.index(L['folio'])%2==0 for w in L['words']]; B2 = [w for L in P if L['lang']=='B' and folB.index(L['folio'])%2==1 for w in L['words']]
h = N3//2
comps += [('Voynich A half vs A half (alternate folios, nA/2 each)', A1[:h], A2[:h]), ('Voynich B half vs B half (alternate folios, nA/2 each)', B1[:h], B2[:h]),
          ('Voynich B half vs B half (alternate folios, nA each)', B1[:N3], B2[:N3]),
          ('Voynich A half vs B half (nA/2 each)', A1[:h], B1[:h])]
Bbio = [w for L in P if L['lang']=='B' and L['illus']=='B' for w in L['words']]; Bstar = [w for L in P if L['lang']=='B' and L['illus']=='S' for w in L['words']]
Bherb = [w for L in P if L['lang']=='B' and L['illus']=='H' for w in L['words']]
Aherb = [w for L in P if L['lang']=='A' and L['illus']=='H' for w in L['words']]; Apharm = [w for L in P if L['lang']=='A' and L['illus']=='P' for w in L['words']]
m1 = min(len(Bherb),len(Aherb)); m2 = min(len(Apharm),len(Aherb))
comps += [('Voynich B-bio vs B-stars (nA/2 each)', Bbio[:h], Bstar[:h]), (f'Voynich B-herbal vs A-herbal (same section, {m1} each)', Bherb[:m1], Aherb[:m1]),
          (f'Voynich A-herbal vs A-pharma ({m2} each)', Aherb[:m2], Apharm[:m2])]
la1 = corpus('la',227)  # Vergil, Aeneid
la2 = [w for w in corpus('la',33849)[:85000] if w != 'sidenote']  # Augustine, Confessiones: text proper is the first ~85k words, after that editorial apparatus (mss/ed/abcd); [Sidenote:] markers stripped. la_50280 (Latin Phrase-Book) excluded: mostly English
it = corpus_it()
comps += [('Latin Augustine (la_33849): first vs second nA of same book', la2[:N3], la2[N3:2*N3]), ('Latin Augustine: first vs second nA/2 of same book', la2[:h], la2[h:2*h]),
          ('Latin Augustine: first nA vs nA starting 60k words later', la2[:N3], la2[60000:60000+N3]),
          ('Latin: Vergil Aeneid (la_227) vs Augustine (la_33849)', la1[:N3], la2[:N3]), ('Latin: Vergil first vs second nA', la1[:N3], la1[N3:2*N3]),
          ('Latin Augustine vs Italian (Nuntiatur)', la2[:N3], it[:N3]), ('Italian: first vs second nA', it[:N3], it[N3:2*N3]),
          ('Italian first nA vs Italian 1M words later', it[:N3], it[1000000:1000000+N3]),
          ('Danish da_24747 vs Norwegian no_30027', corpus('da',24747)[:N3], corpus('no',30027)[:N3]), ('Danish da_24747 vs Swedish sv_59341', corpus('da',24747)[:N3], corpus('sv',59341)[:N3]),
          ('Danish da_24747 vs Danish da_36942', corpus('da',24747)[:N3], corpus('da',36942)[:N3]),
          ('English en_1342 vs en_2701', corpus('en',1342)[:N3], corpus('en',2701)[:N3]), ('English en_1342 first vs second nA', corpus('en',1342)[:N3], corpus('en',1342)[N3:2*N3]),
          ('German de_50285 vs Dutch nl_76280', corpus('de',50285)[:N3], corpus('nl',76280)[:N3]), ('German de_50285 vs German de_56156', corpus('de',50285)[:N3], corpus('de',56156)[:N3]),
          ('French fr_19919 vs Italian', corpus('fr',19919)[:N3], it[:N3])]
md(f"Measures: types of X found in Y (typesX_in_Y), tokens of X covered by Y's vocabulary (tokX_in_Y), same with X types of freq>=2 only, Jaccard of type sets, share of X's top-100 words present in Y. Size-matched: nA={N3} tokens per side unless stated (nA/2={h}). Natural-language corpora normalised to lower-case letter-only words.")
md('| comparison | nX | nY | typesX | typesY | typesX_in_Y | typesY_in_X | f>=2 X_in_Y | f>=2 Y_in_X | tokX_in_Y | tokY_in_X | jaccard | top100 X_in_Y |')
md('|---|---|---|---|---|---|---|---|---|---|---|---|---|')
for name, X, Y in comps:
    s = share(X, Y); R['part3']['comparisons'][name] = s
    md(f"| {name} | {s['nX']} | {s['nY']} | {s['typesX']} | {s['typesY']} | {s['typesX_in_Y']} | {s['typesY_in_X']} | {s['types_freq2_X_in_Y']} | {s['types_freq2_Y_in_X']} | {s['tokX_in_Y']} | {s['tokY_in_X']} | {s['jaccard']} | {s['top100_X_in_Y']} |")
def jsd(X, Y):
    cx, cy = collections.Counter(X), collections.Counter(Y); nx, ny = len(X), len(Y)
    def kl(p, q): return sum(pv*math.log2(pv/q[w]) for w,pv in p.items() if pv)
    p = {w: cx[w]/nx for w in set(cx)|set(cy)}; q = {w: cy[w]/ny for w in p}; m = {w: (p[w]+q[w])/2 for w in p}
    return round(0.5*kl(p,m)+0.5*kl(q,m),4)
R['part3']['jsd_unigram_bits'] = {name: jsd(X,Y) for name,X,Y in comps if len(X)==len(Y)}
md('Jensen-Shannon divergence of word-unigram distributions (bits, equal sizes only): ' + '; '.join(f"{k}: {v}" for k,v in R['part3']['jsd_unigram_bits'].items()))

# ================================================================ PART 4: topic words
md('\n## 4. Section-specific vocabulary (topic words)')
def topic_stats(tokens_by_section, minfreq=20):
    secs = list(tokens_by_section); sizes = {s: len(tokens_by_section[s]) for s in secs}; N = sum(sizes.values())
    tot = collections.Counter(); per = {s: collections.Counter(tokens_by_section[s]) for s in secs}
    for s in secs: tot.update(per[s])
    out = []
    for w, n in tot.items():
        if n < minfreq: continue
        chi = 0; kl = 0
        for s in secs:
            e = n*sizes[s]/N; o = per[s][w]
            chi += (o-e)**2/e
            if o: kl += (o/n)*math.log2((o/n)/(sizes[s]/N))
        top = max(secs, key=lambda s: per[s][w]/sizes[s])
        out.append(dict(word=w, n=n, chi2=round(chi,1), chi2_per_token=round(chi/n,3), kl_bits=round(kl,3), peak_section=top, counts={s: per[s][w] for s in secs}))
    out.sort(key=lambda d: -d['chi2'])
    return out, sizes
def summarize(stats, label):
    chis = [d['chi2_per_token'] for d in stats]; kls = [d['kl_bits'] for d in stats]
    srt = sorted(chis)
    return dict(label=label, n_words=len(stats), mean_chi2_per_token=round(sum(chis)/len(chis),4), median_chi2_per_token=round(srt[len(srt)//2],4),
                p90_chi2_per_token=round(srt[int(0.9*len(srt))],4), mean_kl_bits=round(sum(kls)/len(kls),4),
                frac_words_chi2_per_token_gt_0_5=round(sum(1 for c in chis if c > 0.5)/len(chis),4), frac_words_chi2_per_token_gt_1=round(sum(1 for c in chis if c > 1)/len(chis),4),
                top30=[(d['word'], d['n'], d['chi2'], d['chi2_per_token'], d['peak_section']) for d in stats[:30]])
R['part4'] = {}
bysec = collections.defaultdict(list)
for L in P: bysec[L['illus']].append(L['words'])
secs_ok = [s for s in bysec if sum(len(x) for x in bysec[s]) >= 500]
tbs = {s: [w for ws in bysec[s] for w in ws] for s in secs_ok}
sizes = {s: len(tbs[s]) for s in secs_ok}
md(f"Italian corpus: {len(it)} words (Nuntiaturberichte OCR, a stable Italian/French/Latin mix); Latin: Vergil {len(la1)}, Augustine {len(la2)} words (text proper only, apparatus after word 85k and sidenote markers removed; la_50280 Latin Phrase-Book dropped, mostly English). Sections (P text tokens): {sizes}. Words with >= 20 tokens. Statistic: chi-square of the word's section counts against uniform-by-section-size expectation, reported as chi2 and chi2/n (n = word tokens; chi2/n is independent of word frequency and bounded by number of sections minus 1), plus KL divergence (bits) of the word's section distribution from the section-size distribution.")
vs, _ = topic_stats(tbs); R['part4']['voynich_sections'] = summarize(vs, 'Voynich P text by section')
R['part4']['voynich_sections']['top30_with_counts'] = [(d['word'], d['n'], d['chi2'], d['peak_section'], d['counts']) for d in vs[:30]]
md('Top 30 section-specific Voynich words (word, n, chi2, peak section, counts by section): ' + '; '.join(f"{w} n={n} chi2={c} peak={p} {cnt}" for w,n,c,p,cnt in R['part4']['voynich_sections']['top30_with_counts']))
sh_summ = []
alltok = [w for s in secs_ok for w in tbs[s]]
for rep in range(5):
    random.shuffle(alltok); pos = 0; tb = {}
    for s in secs_ok: tb[s] = alltok[pos:pos+sizes[s]]; pos += sizes[s]
    st, _ = topic_stats(tb); sh_summ.append(summarize(st, f'shuffled Voynich rep{rep}'))
def avg(key): return round(sum(s[key] for s in sh_summ)/len(sh_summ),4)
R['part4']['voynich_shuffled'] = dict(reps=len(sh_summ), mean_chi2_per_token=avg('mean_chi2_per_token'), median_chi2_per_token=avg('median_chi2_per_token'), p90_chi2_per_token=avg('p90_chi2_per_token'), mean_kl_bits=avg('mean_kl_bits'), frac_words_chi2_per_token_gt_0_5=avg('frac_words_chi2_per_token_gt_0_5'), frac_words_chi2_per_token_gt_1=avg('frac_words_chi2_per_token_gt_1'), top30_example=sh_summ[0]['top30'][:10], max_chi2_per_token_seen=max(max(d[3] for d in s['top30']) for s in sh_summ))
def nl_sections(words, label):
    pos = 0; tb = {}
    for s in secs_ok: tb[s] = words[pos:pos+sizes[s]]; pos += sizes[s]
    st, _ = topic_stats(tb); return summarize(st, label), st
NLS = {}
NLS['italian_contiguous'], _ = nl_sections(it, 'Italian Nuntiatur contiguous chunks')
STEP_IT = len(it)//len(secs_ok)
R['part4']['italian_corpus_words'] = len(it); R['part4']['italian_spread_step'] = STEP_IT
it_spread = [w for k in range(len(secs_ok)) for w in it[k*STEP_IT:k*STEP_IT+sizes[secs_ok[k]]]]
NLS['italian_spread'], st_it = nl_sections(it_spread, 'Italian Nuntiatur chunks 700k words apart')
lat_concat = la2
NLS['latin_augustine_contiguous'], _ = nl_sections(la2, 'Latin Augustine, contiguous chunks')
STEP_LA = len(la2)//len(secs_ok)
NLS['latin_augustine_spread'], _ = nl_sections([w for k in range(len(secs_ok)) for w in la2[k*STEP_LA:k*STEP_LA+sizes[secs_ok[k]]]], 'Latin Augustine, chunks spread through the book')
rot = []; ptr = {0:0,1:0}; books = [la1, la2]
for k, s in enumerate(secs_ok):
    b = k % 2; rot.extend(books[b][ptr[b]:ptr[b]+sizes[s]]); ptr[b] += sizes[s]
NLS['latin_two_authors_alternating'], _ = nl_sections(rot, 'Latin, sections drawn alternately from Vergil and Augustine (two-document structure)')
NLS['english_contiguous'], _ = nl_sections(corpus('en',2701) + corpus('en',2554), 'English 2 books concatenated, contiguous')
en_shuf = (corpus('en',2701) + corpus('en',2554))[:sum(sizes.values())]; random.shuffle(en_shuf)
NLS['english_shuffled'], _ = nl_sections(en_shuf, 'English shuffled tokens (no topic structure)')
R['part4']['natural_language'] = NLS
md('\nCalibration (same section sizes; words >= 20 tokens):')
md('| corpus | n words | mean chi2/n | median chi2/n | p90 chi2/n | mean KL bits | frac chi2/n>0.5 | frac chi2/n>1 | top-5 words |')
md('|---|---|---|---|---|---|---|---|---|')
def row(lbl, s): md(f"| {lbl} | {s['n_words']} | {s['mean_chi2_per_token']} | {s['median_chi2_per_token']} | {s['p90_chi2_per_token']} | {s['mean_kl_bits']} | {s['frac_words_chi2_per_token_gt_0_5']} | {s['frac_words_chi2_per_token_gt_1']} | {', '.join(f'{t[0]}({t[4]})' for t in s['top30'][:5]) if 'top30' in s else ''} |")
row('Voynich by section', R['part4']['voynich_sections'])
md(f"| Voynich shuffled (mean of 5) | | {R['part4']['voynich_shuffled']['mean_chi2_per_token']} | {R['part4']['voynich_shuffled']['median_chi2_per_token']} | {R['part4']['voynich_shuffled']['p90_chi2_per_token']} | {R['part4']['voynich_shuffled']['mean_kl_bits']} | {R['part4']['voynich_shuffled']['frac_words_chi2_per_token_gt_0_5']} | {R['part4']['voynich_shuffled']['frac_words_chi2_per_token_gt_1']} | max chi2/n seen {R['part4']['voynich_shuffled']['max_chi2_per_token_seen']} |")
for k, s in NLS.items(): row(k, s)
def within(langsel, label):
    tb = collections.defaultdict(list)
    for L in P:
        if L['lang'] == langsel: tb[L['illus']].extend(L['words'])
    tb = {s: v for s, v in tb.items() if len(v) >= 500}
    st, sz = topic_stats(tb); summ = summarize(st, label); summ['sizes'] = sz
    summ['top30_with_counts'] = [(d['word'], d['n'], d['chi2'], d['peak_section'], d['counts']) for d in st[:30]]
    toks = [w for s in tb for w in tb[s]]; random.shuffle(toks); pos = 0; tb2 = {}
    for s in tb: tb2[s] = toks[pos:pos+len(tb[s])]; pos += len(tb[s])
    st2, _ = topic_stats(tb2); s2 = summarize(st2, label+' shuffled')
    tb3 = {}
    stp = len(it)//len(tb)
    for k, s in enumerate(tb): tb3[s] = it[k*stp:k*stp+len(tb[s])]
    st3, _ = topic_stats(tb3); s3 = summarize(st3, label+' Italian same sizes')
    tb4 = {}; stp2 = len(la2)//len(tb)
    for k, s in enumerate(tb): tb4[s] = la2[k*stp2:k*stp2+len(tb[s])]
    st4, _ = topic_stats(tb4); s4 = summarize(st4, label+' Latin Augustine spread, same sizes')
    return dict(voynich=summ, shuffled=s2, italian=s3, latin=s4)
R['part4']['within_B'] = within('B', 'within language B by section'); R['part4']['within_A'] = within('A', 'within language A by section')
for k in ('within_B', 'within_A'):
    md(f"\n{k} sizes: {R['part4'][k]['voynich']['sizes']}")
    for sub in ('voynich','shuffled','italian','latin'): row(f'{k} {sub}', R['part4'][k][sub])
    md(f"Top 30 {k} Voynich words: " + '; '.join(f"{t[0]} n={t[1]} chi2/n={t[3]} peak={t[4]}" for t in R['part4'][k]['voynich']['top30']))
def frac_between(v, lo_, hi_): return round((v-lo_)/(hi_-lo_),3) if hi_ != lo_ else None
R['part4']['position'] = dict(
    all_sections_vs_italian_spread=frac_between(R['part4']['voynich_sections']['mean_chi2_per_token'], R['part4']['voynich_shuffled']['mean_chi2_per_token'], NLS['italian_spread']['mean_chi2_per_token']),
    all_sections_vs_latin_two_authors=frac_between(R['part4']['voynich_sections']['mean_chi2_per_token'], R['part4']['voynich_shuffled']['mean_chi2_per_token'], NLS['latin_two_authors_alternating']['mean_chi2_per_token']),
    all_sections_vs_latin_augustine_spread=frac_between(R['part4']['voynich_sections']['mean_chi2_per_token'], R['part4']['voynich_shuffled']['mean_chi2_per_token'], NLS['latin_augustine_spread']['mean_chi2_per_token']),
    within_B_vs_italian=frac_between(R['part4']['within_B']['voynich']['mean_chi2_per_token'], R['part4']['within_B']['shuffled']['mean_chi2_per_token'], R['part4']['within_B']['italian']['mean_chi2_per_token']),
    within_B_vs_latin=frac_between(R['part4']['within_B']['voynich']['mean_chi2_per_token'], R['part4']['within_B']['shuffled']['mean_chi2_per_token'], R['part4']['within_B']['latin']['mean_chi2_per_token']),
    within_A_vs_italian=frac_between(R['part4']['within_A']['voynich']['mean_chi2_per_token'], R['part4']['within_A']['shuffled']['mean_chi2_per_token'], R['part4']['within_A']['italian']['mean_chi2_per_token']),
    within_A_vs_latin=frac_between(R['part4']['within_A']['voynich']['mean_chi2_per_token'], R['part4']['within_A']['shuffled']['mean_chi2_per_token'], R['part4']['within_A']['latin']['mean_chi2_per_token']))
md(f"\nPosition of Voynich mean chi2/n on a 0 (shuffled) .. 1 (natural language) scale: {R['part4']['position']}")
def spearman(a, b):
    def rk(x):
        s = sorted(range(len(x)), key=lambda i: x[i]); r = [0]*len(x)
        for i, j in enumerate(s): r[j] = i
        return r
    ra, rb = rk(a), rk(b); n = len(a); ma = (n-1)/2
    cov = sum((x-ma)*(y-ma) for x,y in zip(ra,rb)); va = sum((x-ma)**2 for x in ra); vb = sum((y-ma)**2 for y in rb)
    return round(cov/math.sqrt(va*vb),3)
R['part4']['spearman_logfreq_vs_chi2_per_token'] = dict(voynich=spearman([math.log(d['n']) for d in vs], [d['chi2_per_token'] for d in vs]),
    italian_spread=spearman([math.log(d['n']) for d in st_it], [d['chi2_per_token'] for d in st_it]))
md(f"Spearman(log frequency, chi2/n): {R['part4']['spearman_logfreq_vs_chi2_per_token']}")

json.dump(R, open(OUT/'a6.json','w',encoding='utf-8'), indent=1, ensure_ascii=False)
open(OUT/'a6.md','w',encoding='utf-8').write('\n'.join(MD))
print('\n'.join(MD))
