"""a3_wordgrammar.py -- Task a3: the Voynichese word grammar, derived from data.

Everything pure Python 3.12 (no numpy).  Outputs results/a3.json and results/a3.md.

Corpora compared (all normalised the same way: lower case, letters only, space = word break,
first N tokens where N = number of clean ZL paragraph-text tokens):
  voy_merged   ZL3b-n, locus type P only, EVA with glyph merge (see MERGE below)
  voy_raw      same tokens, raw EVA letters
  la, it, de, en  natural languages (Gutenberg / Nuntiaturberichte OCR)
  rugg         table-and-grille generator (3 columns fitted to Voynichese slot inventories)
  selfcite_u   self-citation generator, uniform replacement glyphs
  selfcite_f   self-citation generator, unigram-frequency-weighted replacement glyphs
  *_shuf       control: same tokens with glyphs shuffled inside each word (no positional structure)

MERGE (applied left to right, longest first):
  ckh->K  cth->T  cph->P  cfh->F   (benched gallows)
  ch->C   sh->S
  eee->E  ee->E
  iiin->N iin->N in->N              ('a' is kept as its own symbol, so aiin = a N)
Words containing '?', '@nnn;' codes, apostrophes, digits, or letters outside the basic EVA set
{a c d e f g h i k l m n o p q r s t y} are dropped.
"""
import os as _os  # local paths (the September 2026 scripts hard-coded another machine)
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_CORP = _os.path.join(_HERE, 'data', 'corpora')  # corp_<lang>_<gutenberg id>.txt, see fetch_corpora.py
_EXT = _os.path.join(_HERE, 'data', 'external')  # third-party data (Naibbe, Gaskell & Bowern)
_IT = _os.path.join(_CORP, 'corpus_it.txt')  # vatican5 OCR corpus from the September sample's first words (fetch_corpora.py)
import re, json, random, collections, math, pathlib, sys, time

BASE = pathlib.Path(_HERE)
CORP = pathlib.Path(_CORP)
IT_CORPUS = pathlib.Path(_IT)
RES = BASE / 'results'; RES.mkdir(exist_ok=True)

EVA_OK = set('acdefghiklmnopqrsty')
MERGE_RULES = [('ckh','K'),('cth','T'),('cph','P'),('cfh','F'),('ch','C'),('sh','S'),
               ('eee','E'),('ee','E'),('iiin','N'),('iin','N'),('in','N')]
SYMNAME = {'K':'ckh','T':'cth','P':'cph','F':'cfh','C':'ch','S':'sh','E':'ee','N':'iin'}
def symname(s): return SYMNAME.get(s, s)

def merge_eva(w):
    for a,b in MERGE_RULES: w = w.replace(a,b)
    return w

# ------------------------------------------------------------------ loading
def load_voynich(path=BASE/'data'/'ZL3b-n.words.tsv', merged=True):
    toks = []
    with open(path, encoding='utf-8') as f:
        next(f)
        for l in f:
            fl = l.rstrip('\n').split('\t')
            if fl[2] != 'P': continue
            for w in fl[9].split():
                if '?' in w or not w or set(w) - EVA_OK: continue
                toks.append(merge_eva(w) if merged else w)
    return toks

LETTER = re.compile(r'[^\W\d_]+')
def load_gutenberg(lang, n):
    files = sorted(CORP.glob(f'corp_{lang}_*.txt'))
    toks = []
    for p in files:
        t = p.read_text(encoding='utf-8', errors='replace')
        i = t.find('*** START OF');  j = t.find('*** END OF')
        if i >= 0: t = t[t.find('\n', i)+1:]
        if j >= 0: t = t[:j]
        toks.extend(LETTER.findall(t.lower()))
        if len(toks) >= n: break
    return toks[:n], [p.name for p in files]

def load_italian(n):
    toks = []
    with open(IT_CORPUS, encoding='utf-8', errors='replace') as f:
        for line in f:
            toks.extend(LETTER.findall(line.lower()))
            if len(toks) >= n: break
    return toks[:n]

# ------------------------------------------------------------------ (1) precedence graph + linear order
def precedence_counts(tokens):
    """prec[(x,y)] = number of within-word ordered pairs (i<j) with w[i]=x, w[j]=y, x!=y (token weighted)."""
    prec = collections.Counter(); freq = collections.Counter(); typec = collections.Counter(tokens)
    for w, c in typec.items():
        freq.update({s: c*k for s, k in collections.Counter(w).items()})
        L = len(w)
        for i in range(L):
            for j in range(i+1, L):
                if w[i] != w[j]: prec[(w[i], w[j])] += c
    return prec, freq, typec

def best_order(prec, symbols, restarts=12, seed=1):
    """Linear ordering minimising the token-weighted number of out-of-order pairs (linear ordering problem).
    Init: sort by net precedence; then insertion-move local search to a local optimum; random restarts."""
    rnd = random.Random(seed)
    syms = list(symbols); n = len(syms); idx = {s:i for i,s in enumerate(syms)}
    W = [[0]*n for _ in range(n)]
    for (x,y),c in prec.items(): W[idx[x]][idx[y]] = c
    total = sum(prec.values())
    def cost(order):
        c = 0
        for a in range(n):
            for b in range(a+1, n):
                c += W[order[b]][order[a]]
        return c
    def local_search(order):
        cur = cost(order); improved = True
        while improved:
            improved = False
            for i in range(n):
                s = order[i]; best = (cur, i)
                rest = order[:i] + order[i+1:]
                base = cur - sum(W[s][rest[p]] for p in range(0, i)) - sum(W[rest[p]][s] for p in range(i, n-1))
                viol_before = 0
                viol_after = sum(W[r][s] for r in rest)
                for p in range(0, n):
                    c = base + viol_before + viol_after
                    if c < best[0]: best = (c, p)
                    if p < n-1:
                        viol_before += W[s][rest[p]]; viol_after -= W[rest[p]][s]
                if best[1] != i and best[0] < cur:
                    order = rest[:best[1]] + [s] + rest[best[1]:]; cur = best[0]; improved = True
        return order, cur
    score = {i: sum(W[i]) - sum(W[j][i] for j in range(n)) for i in range(n)}
    init = sorted(range(n), key=lambda i: -score[i])
    best_o, best_c = local_search(init)
    for r in range(restarts):
        o = best_o[:]
        for _ in range(3):
            i, j = rnd.randrange(n), rnd.randrange(n); o[i], o[j] = o[j], o[i]
        o, c = local_search(o)
        if c < best_c: best_o, best_c = o, c
    return [syms[i] for i in best_o], best_c, total

def violation_stats(typec, order):
    rank = {s:i for i,s in enumerate(order)}
    vtok = vtyp = rtok = rtyp = 0; ntok = sum(typec.values()); ntyp = len(typec)
    vpairs = collections.Counter(); gshare = collections.Counter(); bylen = collections.defaultdict(lambda: [0, 0, 0, 0])
    for w, c in typec.items():
        r = [rank[s] for s in w]
        bad = [(w[j], w[i]) for i in range(len(r)) for j in range(i+1, len(r)) if w[i] != w[j] and r[i] > r[j]]
        viol = bool(bad)
        rep = len(set(w)) < len(w)
        L = min(len(w), 9); bylen[L][0] += c; bylen[L][2] += 1
        if viol:
            vtok += c; vtyp += 1; bylen[L][1] += c; bylen[L][3] += 1
            for a, b in set(bad): vpairs[(a, b)] += c     # (a,b): a is placed before b in the order but occurs after it
            for g in set(x for ab in bad for x in ab): gshare[g] += c
        if rep: rtok += c; rtyp += 1
    return {'viol_tokens': vtok/ntok, 'viol_types': vtyp/ntyp, 'repeat_tokens': rtok/ntok, 'repeat_types': rtyp/ntyp,
            'n_tokens': ntok, 'n_types': ntyp,
            'top_violating_pairs': [(symname(a)+'>'+symname(b), c) for (a, b), c in vpairs.most_common(15)],
            'glyph_share_of_violating_tokens': {symname(g): round(c/max(1, vtok), 3) for g, c in gshare.most_common(12)},
            'viol_by_length': {L: {'tokens': v[0], 'viol_tok_frac': round(v[1]/v[0], 3), 'types': v[2], 'viol_typ_frac': round(v[3]/v[2], 3)}
                               for L, v in sorted(bylen.items())}}

def glyph_classes(order, prec, thresh=0.75, min_pairs=20):
    """Heuristic: adjacent glyphs in the order form one class when their mutual precedence is weak
    (max(p,1-p) < thresh) and they co-occur at least min_pairs times."""
    classes = [[order[0]]]
    for a, b in zip(order, order[1:]):
        ab, ba = prec.get((a,b),0), prec.get((b,a),0)
        if ab+ba >= min_pairs and max(ab,ba)/(ab+ba) < thresh: classes[-1].append(b)
        else: classes.append([b])
    return classes

def mean_relpos(typec):
    acc = collections.defaultdict(lambda: [0.0, 0])
    for w, c in typec.items():
        L = len(w)
        for i, s in enumerate(w):
            acc[s][0] += c * (i/(L-1) if L > 1 else 0.5); acc[s][1] += c
    return {s: v[0]/v[1] for s, v in acc.items()}

# ------------------------------------------------------------------ (2) slot template
def zone_grammar(typec, order, budgets=(20, 40, 30)):
    """PREFIX(0-1) CORE(0-1) SUFFIX(0-2) where each glyph belongs to exactly one zone given by two cuts
    in the linear order.  Inventories: top-B1 zone-1 strings, top-B2 zone-2 strings, top-B3 zone-3 units
    (a zone-3 string is accepted if it is a unit or a concatenation of two units).  Cuts chosen to
    maximise token coverage.  Non-monotone words (violations) cannot be parsed."""
    rank = {s:i for i,s in enumerate(order)}; n = len(order)
    best = None
    for c1 in range(0, n+1):
        for c2 in range(c1, n+1):
            z1 = collections.Counter(); z2 = collections.Counter(); z3 = collections.Counter(); parts = {}
            for w, c in typec.items():
                zs = [rank[s] for s in w]
                zone = [0 if r < c1 else (1 if r < c2 else 2) for r in zs]
                if any(zone[i] > zone[i+1] for i in range(len(zone)-1)): continue
                p = ''.join(s for s, z in zip(w, zone) if z == 0); m = ''.join(s for s, z in zip(w, zone) if z == 1)
                sfx = ''.join(s for s, z in zip(w, zone) if z == 2)
                parts[w] = (p, m, sfx); z1[p] += c; z2[m] += c; z3[sfx] += c
            P = {k for k, _ in z1.most_common(budgets[0])} | {''}
            C = {k for k, _ in z2.most_common(budgets[1])} | {''}
            cand = collections.Counter()
            for s, c in z3.items():
                if not s: continue
                cand[s] += c
                for i in range(1, len(s)): cand[s[:i]] += c*0.5; cand[s[i:]] += c*0.5
            S = {k for k, _ in cand.most_common(budgets[2])}
            def sfx_ok(s):
                if s == '' or s in S: return True
                return any(s[:i] in S and s[i:] in S for i in range(1, len(s)))
            cov_t = cov_y = 0
            for w, (p, m, sfx) in parts.items():
                if p in P and m in C and sfx_ok(sfx): cov_t += typec[w]; cov_y += 1
            if best is None or cov_t > best['cov_tokens_n']:
                best = {'cut1': c1, 'cut2': c2, 'cov_tokens_n': cov_t, 'cov_types_n': cov_y,
                        'prefix_zone': [symname(s) for s in order[:c1]], 'core_zone': [symname(s) for s in order[c1:c2]],
                        'suffix_zone': [symname(s) for s in order[c2:]],
                        'PREFIX': sorted(P - {''}, key=lambda k: -z1[k]), 'CORE': sorted(C - {''}, key=lambda k: -z2[k]),
                        'SUFFIX_units': sorted(S, key=lambda k: -cand[k])}
    nt = sum(typec.values()); ny = len(typec)
    best['cov_tokens'] = best['cov_tokens_n']/nt; best['cov_types'] = best['cov_types_n']/ny
    return best

def ngram_grammar(typec, budgets=(20, 40, 30)):
    """Order-free slot grammar with fixed inventory budgets.
    PREFIX = top-B1 word-initial n-grams (n=1..3, token count of words starting with them),
    SUFFIX units = top-B3 word-final n-grams (n=1..4),
    CORE = top-B2 residues after stripping any inventory prefix and 0-2 inventory suffix units
    (each type's residue candidates share its token weight equally).
    Coverage = fraction of types/tokens parsable as PREFIX? CORE? SUFFIX? SUFFIX?  (empty core allowed)."""
    ini = collections.Counter(); fin = collections.Counter()
    for w, c in typec.items():
        for n in range(1, 4):
            if len(w) > n: ini[w[:n]] += c
        for n in range(1, 5):
            if len(w) > n: fin[w[-n:]] += c
    P = [k for k, _ in ini.most_common(budgets[0])]; S = [k for k, _ in fin.most_common(budgets[2])]
    Pset = set(P) | {''}; Sset = set(S)
    def suffix_splits(w):
        out = {len(w)}
        for s1 in Sset:
            if w.endswith(s1):
                i = len(w) - len(s1); out.add(i)
                for s2 in Sset:
                    if w[:i].endswith(s2): out.add(i - len(s2))
        return out
    def decomps(w):
        res = []
        for p in Pset:
            if w.startswith(p):
                for i in suffix_splits(w[len(p):]):
                    res.append((p, w[len(p):len(p)+i], w[len(p)+i:]))
        return res
    corec = collections.Counter(); dec = {}
    for w, c in typec.items():
        d = decomps(w); dec[w] = d
        if d:
            for p, m, s in d: corec[m] += c/len(d)
    C = [k for k, _ in corec.most_common(budgets[1])]; Cset = set(C) | {''}
    cov_t = cov_y = 0; parse = {}
    for w, c in typec.items():
        ok = [t for t in dec[w] if t[1] in Cset]
        if ok:
            cov_t += c; cov_y += 1
            parse[w] = max(ok, key=lambda t: (len(t[0]), len(t[2])))
    nt = sum(typec.values()); ny = len(typec)
    return {'cov_tokens': cov_t/nt, 'cov_types': cov_y/ny, 'PREFIX': P, 'CORE': C, 'SUFFIX_units': S,
            'core_empty_share': corec['']/max(1, sum(corec.values()))}, parse

# ------------------------------------------------------------------ (4) generators
def rugg_generator(voy_typec, parse, n, seed=7):
    """Three columns (prefix, midfix, suffix) with entries and frequencies read off the ngram-grammar parse of
    Voynichese; each word = independent frequency-weighted pick from each column (grille = random cell)."""
    rnd = random.Random(seed)
    cols = [collections.Counter(), collections.Counter(), collections.Counter()]
    for w, (p, m, s) in parse.items():
        c = voy_typec[w]; cols[0][p] += c; cols[1][m] += c; cols[2][s] += c
    tabs = [(list(c.keys()), list(c.values())) for c in cols]
    out = []
    while len(out) < n:
        w = ''.join(rnd.choices(k, v)[0] for k, v in tabs)
        if w: out.append(w)
    return out, [len(c) for c in cols]

def selfcite_generator(seeds, alphabet, weights, n, seed=11, window=30, p_edits=(0.15, 0.55, 0.30), maxlen=12):
    """Timm & Schinner-style self-citation: each new word copies one of the last `window` words
    (recency-weighted, geometric 0.9^age) and applies 0/1/2 random edits (change / insert / delete a glyph)."""
    rnd = random.Random(seed); words = list(seeds)
    ages = [0.9**a for a in range(window)]
    while len(words) < n:
        recent = words[-window:][::-1]
        src = rnd.choices(recent, ages[:len(recent)])[0]
        k = rnd.choices([0, 1, 2], p_edits)[0]; w = list(src)
        for _ in range(k):
            op = rnd.randrange(3)
            if op == 0 and w: w[rnd.randrange(len(w))] = rnd.choices(alphabet, weights)[0]
            elif op == 1 and len(w) < maxlen: w.insert(rnd.randrange(len(w)+1), rnd.choices(alphabet, weights)[0])
            elif op == 2 and len(w) > 1: del w[rnd.randrange(len(w))]
        words.append(''.join(w))
    return words[:n]

def shuffle_within(tokens, seed=3):
    rnd = random.Random(seed); out = []
    for w in tokens:
        l = list(w); rnd.shuffle(l); out.append(''.join(l))
    return out

# ------------------------------------------------------------------ (5) one-edit neighbours
def one_edit_fraction(typec, min_count=1, topk=None):
    types = [w for w, c in typec.items() if c >= min_count]
    if topk: types = [w for w, c in sorted(typec.items(), key=lambda x: -x[1])[:topk]]
    tset = set(types)
    wild = collections.Counter(); dele = collections.Counter()
    for w in types:
        for i in range(len(w)):
            wild[w[:i]+'\x00'+w[i+1:]] += 1; dele[w[:i]+w[i+1:]] += 1
    has = 0
    for w in types:
        ok = False
        for i in range(len(w)):
            if wild[w[:i]+'\x00'+w[i+1:]] > 1: ok = True; break
            if (w[:i]+w[i+1:]) in tset: ok = True; break
        if not ok and dele[w] > 0: ok = True
        if ok: has += 1
    return has/len(types), len(types)

# ------------------------------------------------------------------ driver
def analyse(name, tokens, do_zone=True, budgets=(20, 40, 30)):
    t0 = time.time()
    prec, freq, typec = precedence_counts(tokens)
    syms = [s for s, _ in freq.most_common()]
    order, viol_w, total_w = best_order(prec, syms)
    vs = violation_stats(typec, order)
    rel = mean_relpos(typec)
    classes = glyph_classes(order, prec)
    ng, parse = ngram_grammar(typec, budgets)
    zg = zone_grammar(typec, order, budgets) if do_zone else None
    oe1, nty = one_edit_fraction(typec, 1); oe2, nty2 = one_edit_fraction(typec, 2); oe3, _ = one_edit_fraction(typec, topk=2000)
    top = syms[:16]
    ptab = {}
    for x in top:
        for y in top:
            if x < y:
                a, b = prec.get((x,y),0), prec.get((y,x),0)
                if a+b: ptab[f'{symname(x)}<{symname(y)}'] = {'n': a+b, 'p_x_first': round(a/(a+b), 3)}
    r = {'name': name, 'n_tokens': len(tokens), 'n_types': len(typec), 'alphabet_size': len(syms),
         'mean_len_symbols': sum(len(w) for w in tokens)/len(tokens),
         'symbol_freq': {symname(s): c for s, c in freq.most_common()},
         'order': [symname(s) for s in order], 'order_raw': order,
         'mean_relative_position': {symname(s): round(rel[s], 3) for s in order},
         'pair_violation_weight': viol_w, 'pair_total_weight': total_w, 'pair_violation_frac': viol_w/total_w,
         **vs, 'glyph_classes': [[symname(s) for s in c] for c in classes], 'n_classes': len(classes),
         'precedence_table_top16': ptab,
         'ngram_grammar': ng, 'zone_grammar': zg,
         'one_edit_frac_all_types': oe1, 'one_edit_frac_types_min2': oe2, 'n_types_min2': nty2, 'one_edit_frac_top2000_types': oe3,
         'seconds': round(time.time()-t0, 1)}
    print(f"{name:14s} tok={len(tokens)} typ={len(typec)} alpha={len(syms)} len={r['mean_len_symbols']:.2f} "
          f"pairviol={viol_w/total_w:.4f} violtok={vs['viol_tokens']:.4f} violtyp={vs['viol_types']:.4f} "
          f"ngram cov tok={ng['cov_tokens']:.3f} typ={ng['cov_types']:.3f} "
          + (f"zone cov tok={zg['cov_tokens']:.3f} typ={zg['cov_types']:.3f} " if zg else '')
          + f"1edit={oe1:.3f}/{oe2:.3f}/{oe3:.3f} classes={len(classes)} {r['seconds']}s", flush=True)
    print('   order:', ' '.join(symname(s) for s in order), flush=True)
    return r, typec, parse

def main():
    out = {'task': 'a3 word grammar', 'merge_rules': MERGE_RULES, 'corpora': {}}
    voy_m = load_voynich(merged=True); voy_r = load_voynich(merged=False)
    N = len(voy_m); out['N_tokens'] = N
    print('N =', N)
    res = {}
    res['voy_merged'], voy_typec, voy_parse = analyse('voy_merged', voy_m)
    res['voy_raw'], _, _ = analyse('voy_raw', voy_r)
    res['voy_merged_shuf'], _, _ = analyse('voy_merged_shuf', shuffle_within(voy_m))
    langs = {}
    for lang in ['la', 'de', 'en']:
        toks, files = load_gutenberg(lang, N); langs[lang] = files
        res[lang], _, _ = analyse(lang, toks)
        res[lang+'_shuf'], _, _ = analyse(lang+'_shuf', shuffle_within(toks))
    it = load_italian(N); langs['it'] = [IT_CORPUS.name]
    res['it'], _, _ = analyse('it', it)
    res['it_shuf'], _, _ = analyse('it_shuf', shuffle_within(it))
    out['language_files'] = langs
    rugg, colsizes = rugg_generator(voy_typec, voy_parse, N)
    res['rugg'], _, _ = analyse('rugg', rugg); res['rugg']['column_sizes'] = colsizes
    freq = res['voy_merged']['symbol_freq']; alpha = [s for s in res['voy_merged']['order_raw']]
    wts_f = [freq[symname(s)] for s in alpha]; wts_u = [1]*len(alpha)
    seeds = [merge_eva(w) for w in 'fachys ykal ar ataiin shol shory cthres y kor sholdy'.split()]
    res['selfcite_u'], _, _ = analyse('selfcite_u', selfcite_generator(seeds, alpha, wts_u, N))
    res['selfcite_f'], _, _ = analyse('selfcite_f', selfcite_generator(seeds, alpha, wts_f, N, seed=12))
    res['selfcite_t'], _, _ = analyse('selfcite_t', selfcite_generator(seeds, alpha, wts_f, N, seed=13, p_edits=(0.75, 0.20, 0.05), maxlen=9))
    res['selfcite_t']['note'] = 'tuned: P(edits)=(0.75,0.20,0.05), max length 9, frequency-weighted glyphs, to bring the type count near Voynichese'
    # zero-order control: same lengths, symbols iid from the Voynichese unigram distribution
    rnd = random.Random(5); uni = [''.join(rnd.choices(alpha, wts_f, k=len(w))) for w in voy_m]
    res['voy_unigram'], _, _ = analyse('voy_unigram', uni)
    out['corpora'] = res; out['seeds_selfcite'] = seeds
    json.dump(out, open(RES/'a3.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    L = ['# a3: word grammar (slot structure) -- Voynichese vs languages vs generators', '',
         f'N tokens per corpus = {N} (clean ZL paragraph-text tokens; languages truncated to the same N).', '',
         'Merge: ' + ', '.join(f'{a}->{b}' for a, b in MERGE_RULES), '',
         '| corpus | types | alphabet | mean len | pair-viol frac | viol tokens | viol types | repeat types | ngram-grammar cov tok/typ | zone-grammar cov tok/typ | 1-edit (all types) | 1-edit (types n>=2) | 1-edit (top-2000 types) | viol types len=5 | classes |',
         '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for k, r in res.items():
        z = r['zone_grammar']; g = r['ngram_grammar']
        L.append(f"| {k} | {r['n_types']} | {r['alphabet_size']} | {r['mean_len_symbols']:.2f} | {r['pair_violation_frac']:.4f} | "
                 f"{r['viol_tokens']:.3f} | {r['viol_types']:.3f} | {r['repeat_types']:.3f} | {g['cov_tokens']:.3f}/{g['cov_types']:.3f} | "
                 f"{z['cov_tokens']:.3f}/{z['cov_types']:.3f} | {r['one_edit_frac_all_types']:.3f} | {r['one_edit_frac_types_min2']:.3f} | {r['one_edit_frac_top2000_types']:.3f} | {r['viol_by_length'].get(5, {}).get('viol_typ_frac', '-')} | {r['n_classes']} |")
    L += ['', '## Best linear orders', '']
    for k, r in res.items():
        L.append(f"- **{k}**: " + ' '.join(r['order']))
        L.append(f"  - classes: " + ' | '.join(' '.join(c) for c in r['glyph_classes']))
    v = res['voy_merged']
    L += ['', '## Voynichese (merged): what violates the linear order', '',
          'top violating pairs (X>Y = X is before Y in the best order but occurs after Y; token counts): ' +
          ', '.join(f'{k} {c}' for k, c in v['top_violating_pairs']), '',
          'share of violating tokens in which glyph takes part: ' + ', '.join(f'{g} {x}' for g, x in v['glyph_share_of_violating_tokens'].items()), '',
          'violation rate by word length (symbols): ' + ', '.join(f"len {L_}: tok {d['viol_tok_frac']} typ {d['viol_typ_frac']} (n={d['tokens']})" for L_, d in v['viol_by_length'].items()), '',
          '## Voynichese (merged) zone grammar', '',
          f"prefix zone: {' '.join(v['zone_grammar']['prefix_zone'])}", f"core zone: {' '.join(v['zone_grammar']['core_zone'])}",
          f"suffix zone: {' '.join(v['zone_grammar']['suffix_zone'])}",
          f"PREFIX inventory ({len(v['zone_grammar']['PREFIX'])}): {' '.join(v['zone_grammar']['PREFIX'])}",
          f"CORE inventory ({len(v['zone_grammar']['CORE'])}): {' '.join(v['zone_grammar']['CORE'])}",
          f"SUFFIX units ({len(v['zone_grammar']['SUFFIX_units'])}): {' '.join(v['zone_grammar']['SUFFIX_units'])}",
          '', '## Voynichese (merged) n-gram grammar inventories', '',
          f"PREFIX: {' '.join(v['ngram_grammar']['PREFIX'])}", f"CORE: {' '.join(v['ngram_grammar']['CORE'])}",
          f"SUFFIX units: {' '.join(v['ngram_grammar']['SUFFIX_units'])}", '',
          '(symbols: C=ch S=sh K=ckh T=cth P=cph F=cfh E=ee N=iin)', '',
          '## Voynichese precedence table (top-16 symbols, p = fraction of co-occurrences where first-named precedes)', '']
    for k2, d in sorted(v['precedence_table_top16'].items(), key=lambda x: -x[1]['n'])[:60]:
        L.append(f"- {k2}: n={d['n']} p={d['p_x_first']}")
    (RES/'a3.md').write_text('\n'.join(L), encoding='utf-8')
    print('written', RES/'a3.json', RES/'a3.md')

if __name__ == '__main__':
    main()
