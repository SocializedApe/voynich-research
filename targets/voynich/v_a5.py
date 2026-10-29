"""v_a5.py -- adversarial re-check of a5_cipher.py (does not modify a5 files).

Writes results/v_a5.json and results/v_a5.md.
Checks:
  A. independent recomputation of Voynich h1/h2 (raw, merged; nospace/space) with own entropy code,
     proper conditional entropy H(X_n|X_{n-1}) using the (n-1)-prefix marginal.
  B. EVA-independent segmentation: same statistics on Currier (CD2a) and v101 (GC2a) alphabets
     (one character per glyph), P loci, same filters.
  C. language-corpus artefacts: non-ASCII share, Latin admixture in the 'Italian' OCR sample,
     OCR-noise proxies; recompute h1/h2 with diacritics folded to base letters; single-book samples.
  D. positional table: which raw-EVA symbols are >=90% locked and whether they are EVA halves (c,h,i).
  E. reproduce BPE step-12, null-removal for 'h' and 'o', info-budget bits for Voynich raw & Italian.
  F. plug-in bias sanity: h2 on halves of the sample.
"""
import os as _os  # local paths (the September 2026 scripts hard-coded another machine)
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_CORP = _os.path.join(_HERE, 'data', 'corpora')  # corp_<lang>_<gutenberg id>.txt, see fetch_corpora.py
_EXT = _os.path.join(_HERE, 'data', 'external')  # third-party data (Naibbe, Gaskell & Bowern)
_IT = _os.path.join(_CORP, 'corpus_it.txt')  # vatican5 OCR corpus from the September sample's first words (fetch_corpora.py)
import collections, csv, json, math, pathlib, re, sys, unicodedata, time
HERE = pathlib.Path(_HERE)
sys.path.insert(0, str(HERE))
import a5_cipher as A   # reuse its loaders so we test exactly its sample
RES = HERE / 'results'; RES.mkdir(exist_ok=True)
L2 = math.log2
T0 = time.time()
out = {}

def H(counter):
    n = sum(counter.values()); return -sum(c / n * L2(c / n) for c in counter.values())

def cond_h2(stream):
    """H(X_n | X_{n-1}) with the correct marginal over the first n-1 positions."""
    bi = collections.Counter(zip(stream, stream[1:])); prev = collections.Counter(stream[:-1])
    return H(bi) - H(prev)

def profile(words):
    """words = list of tuples of symbols."""
    ns = [s for w in words for s in w]
    sp = []
    for w in words: sp.extend(w); sp.append(' ')
    uni = collections.Counter(ns)
    return dict(nsym=len(uni), nsym_ge20=sum(1 for v in uni.values() if v >= 20), nchars=len(ns),
                h1_nospace=round(H(uni), 3), h2_nospace=round(cond_h2(ns), 3),
                h1_space=round(H(collections.Counter(sp)), 3), h2_space=round(cond_h2(sp), 3),
                mean_wlen=round(len(ns) / len(words), 3), types=len(set(words)))

# ------------------------------------------------------------------ A. Voynich raw / merged
vw, vinfo = A.load_voynich(); N = len(vw)
vm = [A.merge_glyphs(w) for w in vw]
out['A_voynich'] = dict(sample=vinfo | dict(tokens=N),
                        raw=profile([tuple(w) for w in vw]), mrg=profile([tuple(w) for w in vm]))
# halves (plug-in bias / stability)
h = N // 2
out['A_voynich']['raw_first_half'] = profile([tuple(w) for w in vw[:h]])
out['A_voynich']['raw_second_half'] = profile([tuple(w) for w in vw[h:]])

# ------------------------------------------------------------------ B. Currier and v101 alphabets
def load_alt(fname):
    rows = list(csv.DictReader(open(HERE / 'data' / fname, encoding='utf-8'), delimiter='\t'))
    P = [r for r in rows if r['locus_type'] == 'P']
    ws = []; dq = do = 0
    for r in P:
        for w in r['line_words'].split():
            if '?' in w: dq += 1; continue
            if re.search(r'[@;!\'"*]', w): do += 1; continue   # weirdo codes / IVTFF residue
            ws.append(w)
    return ws, dict(lines=len(P), dropped_unread=dq, dropped_odd=do, tokens=len(ws))
alt = {}
for fname, label in [('CD2a-n.words.tsv', 'currier_CD2a'), ('GC2a-n.words.tsv', 'v101_GC2a'), ('IT2a-n.words.tsv', 'takahashi_IT2a_eva'), ('RF1b-er.words.tsv', 'RF1b_eva')]:
    ws, info = load_alt(fname)
    cnt = collections.Counter(ch for w in ws for ch in w)
    alt[label] = dict(info=info, alphabet=''.join(sorted(cnt)), **profile([tuple(w) for w in ws]))
    # positional lock count >=90% on symbols with >=20 occurrences
    pos = A.positional([tuple(w) for w in ws]); pos.pop('detail')
    alt[label]['positional'] = pos
# GC2a: v101 uses digits and capitals as single glyphs; Currier too. Also compute Currier restricted to
# the folios that both CD2a and ZL3b cover, EVA raw on the same folios, for an apples-to-apples check.
rowsCD = list(csv.DictReader(open(HERE / 'data' / 'CD2a-n.words.tsv', encoding='utf-8'), delimiter='\t'))
cd_lines = {r['line_id'] for r in rowsCD if r['locus_type'] == 'P' and r['line_words'].strip()}
rowsZL = list(csv.DictReader(open(HERE / 'data' / 'ZL3b-n.words.tsv', encoding='utf-8'), delimiter='\t'))
zl_same = [w for r in rowsZL if r['locus_type'] == 'P' and r['line_id'] in cd_lines for w in r['line_words'].split() if '?' not in w and re.fullmatch(r'[a-z]+', w)]
alt['eva_raw_on_CD2a_lines'] = dict(tokens=len(zl_same), **profile([tuple(w) for w in zl_same]))
alt['eva_mrg_on_CD2a_lines'] = dict(tokens=len(zl_same), **profile([tuple(A.merge_glyphs(w)) for w in zl_same]))
out['B_alt_transliterations'] = alt

# ------------------------------------------------------------------ C. language corpora
langs = {}; files = {}
for lg in A.LANGS: langs[lg], files[lg] = A.load_lang(lg, N)

def fold(w):
    return ''.join(c for c in unicodedata.normalize('NFD', w) if not unicodedata.combining(c))
def ascii_only(w): return re.sub(r'[^a-z]', '', fold(w).replace('æ', 'ae').replace('œ', 'oe').replace('ß', 'ss').replace('ø', 'o').replace('å', 'a'))

LAT_ONLY = {'quod', 'cum', 'ut', 'est', 'sed', 'enim', 'autem', 'atque', 'quae', 'ac', 'nec', 'esse', 'sunt', 'ex', 'ab', 'pro', 'eius', 'eorum', 'etiam', 'tamen', 'igitur', 'vero', 'uero'}
ITA_ONLY = {'che', 'di', 'il', 'la', 'lo', 'gli', 'della', 'del', 'delle', 'dei', 'sono', 'ha', 'una', 'uno', 'con', 'si', 'questo', 'questa', 'sua', 'suo', 'come', 'anco', 'esser', 'essere', 'molto', 'quel', 'quella', 'se', 'piu', 'quando', 'perche', 'cosa', 'ma'}
def lat_ita_score(c):
    l = sum(c[w] for w in LAT_ONLY) + sum(v for w, v in c.items() if len(w) > 4 and (w.endswith('que') or w.endswith('ibus') or w.endswith('orum') or w.endswith('arum') or w.endswith('ntur')))
    t = sum(c[w] for w in ITA_ONLY)
    return l, t
def latin_share(words, win=200):
    lat = ita = 0; nwin = 0
    for i in range(0, len(words) - win + 1, win):
        c = collections.Counter(words[i:i + win]); nwin += 1
        l, t = lat_ita_score(c)
        if l > t: lat += 1
        elif t > l: ita += 1
    return dict(windows=nwin, latin_windows=lat, italian_windows=ita, latin_share=round(lat / nwin, 3))

C = {}
for lg in A.LANGS:
    ws = langs[lg]
    cnt = collections.Counter(ch for w in ws for ch in w)
    nonascii_tok = sum(1 for w in ws if any(ord(c) > 127 for c in w))
    single = sum(1 for w in ws if len(w) == 1)
    C[lg] = dict(files=files[lg], tokens=len(ws), alphabet=''.join(sorted(cnt)),
                 nonascii_symbol_types=sum(1 for s in cnt if ord(s) > 127),
                 nonascii_token_share=round(nonascii_tok / len(ws), 4),
                 single_letter_token_share=round(single / len(ws), 4),
                 top15=[w for w, _ in collections.Counter(ws).most_common(15)],
                 as_loaded=profile([tuple(w) for w in ws]),
                 folded_ascii=profile([tuple(ascii_only(w)) for w in ws if ascii_only(w)]))
    if lg == 'it': C[lg]['latin_admixture'] = latin_share(ws)
# Italian: Italian-only windows vs Latin-only windows, same statistics
itw = langs['it']; win = 200; ital = []; latn = []
for i in range(0, len(itw) - win + 1, win):
    seg = itw[i:i + win]; c = collections.Counter(seg)
    l, t = lat_ita_score(c)
    (ital if t > l else latn if l > t else []).extend(seg)
C['it']['italian_only_windows'] = dict(tokens=len(ital), **(profile([tuple(w) for w in ital]) if ital else {}))
C['it']['latin_only_windows'] = dict(tokens=len(latn), **(profile([tuple(w) for w in latn]) if latn else {}))
# Italian: a later, presumably cleaner slice of the corpus (skip 200k words) to test stability
full_it = A.tokenize(A.IT_FILE.read_text(encoding='utf-8', errors='replace'))
it_late = full_it[200000:200000 + N]
C['it']['later_slice_200k'] = dict(latin_admixture=latin_share(it_late), **profile([tuple(w) for w in it_late]))
# OCR-noise proxy: share of tokens that are hapax AND contain a consonant run >= 4 (rare in real Italian)
def noise_proxy(ws):
    c = collections.Counter(ws)
    bad = sum(1 for w in c if c[w] == 1 and re.search(r'[^aeiou]{4,}', w))
    return dict(hapax_types=sum(1 for v in c.values() if v == 1), hapax_with_4consonant_run=bad)
C['it']['ocr_noise_proxy'] = noise_proxy(itw); C['la']['ocr_noise_proxy'] = noise_proxy(langs['la']); C['de']['noise_proxy'] = noise_proxy(langs['de'])
# single-book samples (longest file per language), same N, skip 2000 -- checks the multi-book mixing
single = {}
for lg in ['la', 'de', 'en', 'fr', 'da']:
    fs = [f for f in sorted(A.CORP.glob(f'corp_{lg}_*.txt')) if f.name != 'corp_la_50280.txt']
    best = None
    for f in fs:
        t = A.tokenize(A.gutenberg_body(f.read_text(encoding='utf-8', errors='replace')))[2000:]
        if best is None or len(t) > len(best[1]): best = (f.name, t)
    t = best[1][:N]
    c = collections.Counter(t)
    single[lg] = dict(file=best[0], tokens=len(t), types=len(c), hapax_frac_types=round(sum(1 for v in c.values() if v == 1) / len(c), 3),
                      **{k: v for k, v in profile([tuple(w) for w in t]).items() if k.startswith('h')})
C['single_book_samples'] = single
out['C_corpora'] = C

# ------------------------------------------------------------------ D. positional artefacts
posr = A.positional([tuple(w) for w in vw]); posm = A.positional([tuple(w) for w in vm])
def locked(pos):
    return {s: max(('initial', 'medial', 'final'), key=lambda c: d[c]) + f" {max(d['initial'], d['medial'], d['final']):.3f}"
            for s, d in pos['detail'].items() if max(d['initial'], d['medial'], d['final']) >= .9}
out['D_positional'] = dict(raw_locked=locked(posr), mrg_locked=locked(posm),
                           raw_mi=posr['mi_symbol_position_bits'], mrg_mi=posm['mi_symbol_position_bits'],
                           note='raw EVA c/h/i are halves of bench (ch, sh) and minim (in, iin) composites; their lock is a transliteration artefact.')
# language MI with folded alphabets (removes rare accented letters that inflate French)
out['D_positional']['lang_mi_folded'] = {lg: A.positional([tuple(ascii_only(w)) for w in langs[lg] if ascii_only(w)])['mi_symbol_position_bits'] for lg in A.LANGS}
out['D_positional']['lang_locked_folded'] = {lg: locked(A.positional([tuple(ascii_only(w)) for w in langs[lg] if ascii_only(w)])) for lg in A.LANGS}

# ------------------------------------------------------------------ E. reproduce BPE / nulls / info budget
tr = A.bpe_trajectory(vw, 12)
out['E_bpe_raw_step12'] = tr[12]
tr_it = A.bpe_trajectory(langs['it'], 12)
out['E_bpe_it_step12'] = tr_it[12]
def remove_glyph(words, g):
    ww = [tuple(c for c in w if c != g) for w in words]; return [w for w in ww if w]
out['E_nulls'] = {f'raw_minus_{g}': profile(remove_glyph(vw, g)) for g in 'oh'}
out['E_nulls']['mrg_minus_o'] = profile(remove_glyph(vm, 'o'))
out['E_info'] = dict(voy_raw=A.cv_bits(vw), it=A.cv_bits(langs['it']))
out['E_info']['voy_raw_shuffled_folds_note'] = 'folds are consecutive blocks; Voynich sections (Currier A/B) make test folds differ from training folds more than a single novel would'

# ------------------------------------------------------------------ F. word inventory checks
def wstats(ws):
    c = collections.Counter(ws); n = len(ws)
    return dict(tokens=n, types=len(c), hapax_frac_types=round(sum(1 for v in c.values() if v == 1) / len(c), 3))
out['F_words'] = dict(voy_P=wstats(vw), voy_P_mrg_types=len(set(vm)),
                      voy_currierA=wstats([w for r in rowsZL if r['locus_type'] == 'P' and r['lang'] == 'A' for w in r['line_words'].split() if '?' not in w and re.fullmatch('[a-z]+', w)]),
                      voy_currierB=wstats([w for r in rowsZL if r['locus_type'] == 'P' and r['lang'] == 'B' for w in r['line_words'].split() if '?' not in w and re.fullmatch('[a-z]+', w)]),
                      langs={lg: wstats(langs[lg]) for lg in A.LANGS})
# ------------------------------------------------------------------ G. distance-k conditional entropy (transposition claim)
def hk(stream, k):
    bi = collections.Counter(zip(stream, stream[k:])); prev = collections.Counter(stream[:-k])
    return round(H(bi) - H(prev), 3)
G = {}
for name, ws in [('voy_raw', vw), ('voy_mrg', vm), ('la', langs['la']), ('it', langs['it']), ('de', langs['de'])]:
    st = [c for w in ws for c in w]
    G[name] = {f'H(X_n|X_n-{k})': hk(st, k) for k in (1, 2, 3, 4, 8)} | {'h1': round(H(collections.Counter(st)), 3)}
out['G_distance_k'] = G

# ------------------------------------------------------------------ H. uncertain-space commas joined instead of split
def parse_join(path):
    ws = []
    for raw in pathlib.Path(path).read_text(encoding='utf-8', errors='replace').splitlines():
        m = re.match(r'<(f\d+[rv]\d?|\w+)\.(\d+),([@+*=])([A-Za-z])(\w*)>\s*(.*)$', raw)
        if not m or m.group(4) != 'P': continue
        t = m.group(6)
        t = re.sub(r'<![^>]*>', '', t); t = re.sub(r'<[^>]*>', '', t); t = re.sub(r'\{[^}]*\}', '', t)
        t = re.sub(r'\[([^\]:]*):[^\]]*\]', r'\1', t)
        t = t.replace(',', '')            # JOIN uncertain breaks
        ws.extend(w for w in t.split('.') if w and '?' not in w and re.fullmatch(r'[a-z]+', w))
    return ws
vj = parse_join(HERE / 'data' / 'ZL3b-n.txt')
out['H_comma_joined'] = dict(tokens=len(vj), raw=profile([tuple(w) for w in vj]), mrg=profile([tuple(A.merge_glyphs(w)) for w in vj]),
                             words=wstats(vj), note='a5 treats IVTFF "," (uncertain space) as a break; here it is joined')

# ------------------------------------------------------------------ I. Latin without [Sidenote: ...] apparatus
def load_la_clean(n):
    outw = []
    for f in ['corp_la_227.txt', 'corp_la_33849.txt']:
        t = A.gutenberg_body((A.CORP / f).read_text(encoding='utf-8', errors='replace'))
        t = re.sub(r'\[Sidenote:[^\]]*\]', ' ', t, flags=re.S)
        t = re.sub(r'\[[0-9]+\]', ' ', t)
        outw.append(A.tokenize(t)[2000:])
    share = math.ceil(n / 2); return (outw[0][:share] + outw[1][:share])[:n]
la_clean = load_la_clean(N)
la_sn = sum(1 for w in langs['la'] if w in ('sidenote', 'ps', 'rom', 'mat', 'joan', 'cor', 'luc', 'gen', 'jac', 'pet'))
conf_only = A.tokenize(re.sub(r'\[Sidenote:[^\]]*\]', ' ', A.gutenberg_body((A.CORP / 'corp_la_33849.txt').read_text(encoding='utf-8', errors='replace')), flags=re.S))[2000:2000 + N]
out['I_latin_clean'] = dict(apparatus_tokens_in_a5_latin_sample=la_sn, share=round(la_sn / N, 4),
                            aeneid_plus_confessiones_no_sidenote=profile([tuple(w) for w in la_clean]) | wstats(la_clean),
                            confessiones_only_no_sidenote=dict(tokens=len(conf_only)) | profile([tuple(w) for w in conf_only]) | wstats(conf_only)
                            | dict(cv=A.cv_bits(conf_only), lzma=A.compress_bits(conf_only)),
                            a5_latin_lzma=A.compress_bits(langs['la']), voy_lzma=A.compress_bits(vw))
out['runtime_s'] = round(time.time() - T0, 1)
(RES / 'v_a5.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')
for k in ('G_distance_k', 'H_comma_joined', 'I_latin_clean', 'runtime_s'):
    print(k, json.dumps(out[k], indent=1, ensure_ascii=True))
