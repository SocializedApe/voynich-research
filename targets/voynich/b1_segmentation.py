"""b1_segmentation.py -- closing the segmentation gap named in NOTES.md section 2.

Two questions:
 (1) Do the ZL statistics depend on treating IVTFF uncertain spaces (',') as word breaks?
     CERTAIN tokenisation = words joined across ',', split only at '.';  ALL = the existing TSV
     (every ',' a break).  Same battery on both.
 (2) Does a European language WRITTEN SYLLABICALLY reproduce the Voynichese profile?  Latin prose
     (Confessiones), Latin verse (Aeneid) and 16th-c. Italian are cut into syllables by a stated rule,
     the syllables are treated as words, and the same battery is run; a 'CV-rigid' variant trims each
     syllable to one consonant + one vowel.

Pure Python 3.12.  Writes results/b1.json and results/b1.md.  Reuses a1_charstats (entropy helpers,
merge tokenisers) and a3_wordgrammar (precedence counts, linear-order search, violation statistics).

METHOD CHOICES (all of them)
----------------------------
Voynich text
  * data/ZL3b-n.txt re-parsed here with the same regexes as parse_ivtff.py (page headers skipped, locus
    lines matched, <!..> <..> {..} removed, [a:b] -> a).  Only locus type P (paragraph text).
  * CERTAIN: ',' deleted (the two halves become one word), '.' splits.  ALL: data/ZL3b-n.words.tsv as
    produced by parse_ivtff.py (',' -> break).  The re-parse in 'split' mode is checked to reproduce the
    TSV token list exactly.
  * Filter (a3's): words containing '?' or any character outside {a c d e f g h i k l m n o p q r s t y}
    are dropped.  In CERTAIN a join with a '?' word drops the whole joined word.
  * Alphabets: RAW EVA (one character = one symbol); MERGE-A3 (ckh cth cph cfh ch sh eee ee iiin iin in
    -> one symbol each; the alphabet of NOTES 4.3 and 4.4); MERGE2-A1 (a1's merge2: benches, bench
    gallows, i/e groups, aiin ain in, qo; the 'merged' row of NOTES 4.1).  Multi-character glyphs are
    mapped to private-use code points so every statistic sees one character per symbol.
  * ALL is additionally truncated to the CERTAIN token count (ALL_trunc) so that the size-dependent
    statistics (types, hapax, Zipf) are compared at equal token count.

Languages
  * Latin prose: corp_la_33849 (Augustine, Confessiones); Latin verse: corp_la_227 (Aeneid); Gutenberg
    header/footer stripped at '*** START OF' / '*** END OF'; lower-case; a word = maximal run of Unicode
    letters (a3's LETTER regex).  Italian: targets/vatican5/corpus_it.txt (already lower-cased; about 8% Latin
    tokens per v_a3).  No tokens skipped at the start (as in a3).
  * Sample size: the first N tokens of each tokenisation, N = number of clean ZL ALL tokens.  For the
    syllable tokenisations N SYLLABLES are taken (equal token count with Voynichese, not equal text).

Syllabification rule (applied inside each orthographic word; word boundaries are always syllable
boundaries)
  * Vowels = a e i o u y.  A 'u' immediately after 'q' is treated as a consonant (qu = one onset).
  * A nucleus = a maximal run of vowels (diphthongs and hiatus are NOT separated: 'ae', 'io', 'uo' are
    one nucleus; this under-counts Latin syllables slightly).
  * Consonant cluster C1..Ck between two nuclei:  k=1 -> V|CV ;  k>=2 -> the split is placed before the
    longest tail of the cluster that is a permitted onset: 3-letter onsets {str spr scr spl scl sch chr
    thr phr}, 2-letter onsets {bl br cl cr dr fl fr gl gr pl pr tr ph th ch qu gn st sp sc sm sn}, else
    before the last consonant (VC|CV, so double consonants split: 'tt' -> t|t).
  * Word-initial consonants join the first syllable, word-final consonants the last.  A word with no
    vowel is one syllable.
  * Examples: 'confessiones' -> con fes sio nes ; 'instrumentum' -> in stru men tum ; 'quae' -> quae ;
    'aeneidos' -> ae nei dos ; 'troiae' -> troiae (one nucleus) ; 'signore' -> si gno re.
  * CV-rigid variant: each syllable -> (first consonant of its onset, if any) + (first vowel of its
    nucleus, if any); coda dropped.  'stru' -> 'su', 'men' -> 'me', 'quae' -> 'qa', 'ae' -> 'a'.
    A vowel-less syllable keeps its first consonant.
  * Bisyllabic variants (added because live hypothesis (a) in NOTES makes a 4-5 glyph Voynich word equal
    to about two 2-3 glyph units): syl2 = syllables 1+2, 3+4, ... of each word joined into one token, an
    odd final syllable alone ('confessiones' -> confes siones, 'arma' -> arma, 'cano' -> cano); cv2 = the
    same chunks after CV trimming ('confessiones' -> cofe sine).  Word boundaries are never crossed.

Statistics (identical code path for every corpus)
  * tokens, types, hapax fraction of types, Zipf slope = OLS of log10 freq on log10 rank, ranks
    1..min(1000, types) (a2's definition).
  * word length in symbols: mean, variance, and variance/mean of (length-1) (a2's dispersion index).
  * h1, h2 with spaces (space is a symbol; line ends are not marked) and without spaces (tokens
    concatenated), plug-in estimates, bits (a1's stream_stats); h2 within-word.
  * positional lock (a5): symbols with >= 20 occurrences; position class single/initial/medial/final;
    'locked' = >= 90% of occurrences in one of initial/medial/final; reported as fraction of symbol
    types, plus I(symbol; position) in bits.
  * pair-violation rigidity (a3): token-weighted fraction of within-word ordered pairs of distinct
    symbols that are out of order under the best linear order of the alphabet (a3.best_order, 12
    restarts); 'length-matched' = the corpus resampled with replacement inside each word length to the
    word-length histogram of ZL ALL merge-a3 (v_a3's length_matched, nearest available length when a
    length is absent); reported n/a when the corpus has no token longer than 2 symbols.  Also the
    violation fraction by word length (2,3,4,5) under the global order.
  * Shuffle null: symbols shuffled inside each word (a3.shuffle_within), reported for the syllable
    tokenisations.
"""
import os as _os  # local paths (the September 2026 scripts hard-coded another machine)
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_CORP = _os.path.join(_HERE, 'data', 'corpora')  # corp_<lang>_<gutenberg id>.txt, see fetch_corpora.py
_EXT = _os.path.join(_HERE, 'data', 'external')  # third-party data (Naibbe, Gaskell & Bowern)
_IT = _os.path.join(_CORP, 'corpus_it.txt')  # vatican5 OCR corpus from the September sample's first words (fetch_corpora.py)
import sys, re, json, math, random, collections, pathlib, time
BASE = pathlib.Path(_HERE)
sys.path.insert(0, str(BASE))
import a1_charstats as A1
import a3_wordgrammar as A3

DATA = BASE / 'data'; RES = BASE / 'results'; RES.mkdir(exist_ok=True)
CORP = A1.CORP; IT_CORPUS = A1.IT_CORPUS
T0 = time.time()
EVA_OK = A3.EVA_OK

# ------------------------------------------------------------------ Voynich parsing (two tokenisations)
def parse_ivtff_P(path, comma):
    """comma='split' -> ',' is a break (parse_ivtff.py behaviour); comma='join' -> ',' deleted."""
    lines_out = []
    for raw in pathlib.Path(path).read_text(encoding='utf-8', errors='replace').splitlines():
        if raw.startswith('#') or not raw.strip(): continue
        m = re.match(r'<(f\d+[rv]\d?|[a-z]\w*)>\s*<!([^>]*)>', raw)
        if m and '.' not in m.group(1): continue
        m = re.match(r'<(f\d+[rv]\d?|\w+)\.(\d+),([@+*=])([A-Za-z])(\w*)>\s*(.*)$', raw)
        if not m: continue
        folio, ln, tag, ltype, sub, text = m.groups()
        if ltype != 'P': continue
        t = re.sub(r'<![^>]*>', '', text)
        t = re.sub(r'<[^>]*>', '', t)
        t = re.sub(r'\{[^}]*\}', '', t)
        t = re.sub(r'\[([^\]:]*):[^\]]*\]', r'\1', t)
        t = t.replace(',', '.' if comma == 'split' else '')
        lines_out.append([w for w in t.split('.') if w])
    return lines_out

def tsv_P_lines(path):
    out = []
    with open(path, encoding='utf-8') as f:
        next(f)
        for l in f:
            fl = l.rstrip('\n').split('\t')
            if fl[2] == 'P': out.append(fl[9].split())
    return out

def clean(lines):
    toks = []; drop = collections.Counter(); total = 0
    for ws in lines:
        for w in ws:
            total += 1
            if '?' in w: drop['?'] += 1; continue
            if set(w) - EVA_OK: drop['nonEVA'] += 1; continue
            toks.append(w)
    return toks, total, dict(drop)

# ------------------------------------------------------------------ alphabets -> one char per symbol
_PUA = {}
def pua(tok):
    if len(tok) == 1: return tok
    if tok not in _PUA: _PUA[tok] = chr(0xE000 + len(_PUA))
    return _PUA[tok]
PUA_NAME = lambda ch: next((k for k, v in _PUA.items() if v == ch), ch)

def to_symbols(words, tokenizer):
    return [''.join(pua(t) for t in tokenizer(w)) for w in words]

def tok_a3(w):
    """a3 merge as a token list (same rules/order as A3.merge_eva)."""
    m = A3.merge_eva(w)
    return [A3.SYMNAME.get(c, c) for c in m]

ALPHABETS = {'raw': A1.tok_raw, 'merge_a3': tok_a3, 'merge2_a1': A1.tok_m2}

# ------------------------------------------------------------------ statistics
def ols_slope(xs, ys):
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)

def zipf_hapax(tokens):
    c = collections.Counter(tokens); freqs = sorted(c.values(), reverse=True)
    r = min(1000, len(freqs))
    slope = ols_slope([math.log10(i + 1) for i in range(r)], [math.log10(freqs[i]) for i in range(r)])
    hap = sum(1 for v in freqs if v == 1)
    return {'types': len(c), 'zipf_slope_1_1000': round(slope, 4), 'ranks_used': r,
            'hapax_type_frac': round(hap / len(c), 4), 'hapax_token_frac': round(hap / len(tokens), 4),
            'top1_share': round(freqs[0] / len(tokens), 4), 'top5': c.most_common(5)}

def length_stats(tokens):
    L = [len(w) for w in tokens]; n = len(L); m = sum(L) / n
    var = sum((x - m) ** 2 for x in L) / n
    m1 = m - 1
    return {'mean': round(m, 3), 'variance': round(var, 3), 'disp_len_minus1': round(var / m1, 3) if m1 > 0 else None,
            'max': max(L), 'hist': dict(sorted(collections.Counter(L).items()))}

def positional(words, minc=20):
    pos = collections.defaultdict(collections.Counter); tot = collections.Counter()
    for w in words:
        L = len(w)
        for i, s in enumerate(w):
            c = 'single' if L == 1 else 'initial' if i == 0 else 'final' if i == L - 1 else 'medial'
            pos[s][c] += 1; tot[s] += 1
    syms = [s for s in tot if tot[s] >= minc]
    N = sum(tot[s] for s in syms); pc = collections.Counter()
    for s in syms: pc.update(pos[s])
    mi = sum((k / N) * math.log2((k / N) / ((tot[s] / N) * (pc[c] / N))) for s in syms for c, k in pos[s].items())
    locked = [s for s in syms if max(pos[s][c] / tot[s] for c in ('initial', 'medial', 'final')) >= .9]
    return {'n_symbols': len(syms), 'locked_frac': round(len(locked) / len(syms), 3) if syms else None,
            'locked_n': len(locked), 'locked_symbols': [PUA_NAME(s) for s in locked], 'mi_bits': round(mi, 4)}

def pair_violation(tokens, restarts=12):
    prec, freq, typec = A3.precedence_counts(tokens)
    syms = [s for s, _ in freq.most_common()]
    order, viol, tot = A3.best_order(prec, syms, restarts=restarts)
    rank = {s: i for i, s in enumerate(order)}
    byL = {}
    for L in (2, 3, 4, 5, 6):
        bad = t = 0
        for w, c in typec.items():
            if len(w) != L: continue
            for i in range(L):
                for j in range(i + 1, L):
                    if w[i] != w[j]:
                        t += c; bad += c * (rank[w[i]] > rank[w[j]])
        if t: byL[L] = round(bad / t, 4)
    return {'pair_violation_frac': round(viol / tot, 4) if tot else None, 'pairs': tot,
            'order': ' '.join(PUA_NAME(s) for s in order), 'by_length': byL}

def length_matched(tokens, target_hist, seed=17):
    """v_a3's resampler; also returns the fraction of target tokens whose exact length exists in the pool."""
    rnd = random.Random(seed); byL = collections.defaultdict(list)
    for w in tokens: byL[len(w)].append(w)
    Ls = sorted(byL); out = []; exact = 0
    for L, k in target_hist.items():
        pool = byL.get(L)
        if pool: exact += k
        else: pool = byL[min(Ls, key=lambda x: abs(x - L))]
        out.extend(rnd.choice(pool) for _ in range(k))
    return out, exact / sum(target_hist.values())

def battery(tokens, label, target_hist=None, do_lm=True):
    t1 = time.time()
    st = A1.full_stats([list(w) for w in tokens], label)
    r = {'label': label, 'n_tokens': len(tokens), 'n_symbols_total': st['n_letters'],
         'alphabet': st['without_spaces']['inventory'],
         **zipf_hapax(tokens), 'length': length_stats(tokens),
         'h1_sp': round(st['with_spaces']['h1'], 4), 'h2_sp': round(st['with_spaces']['h2'], 4),
         'h1_nosp': round(st['without_spaces']['h1'], 4), 'h2_nosp': round(st['without_spaces']['h2'], 4),
         'h1_minus_h2_nosp': round(st['without_spaces']['h1'] - st['without_spaces']['h2'], 4),
         'h2_within_word': round(st['without_spaces']['h2_within_word'], 4),
         'H_word_bits': round(st['word_entropy']['H_word_bits'], 3),
         'positional': positional(tokens), 'pair': pair_violation(tokens)}
    if do_lm and target_hist is not None:
        if max(len(w) for w in tokens) < 3:
            r['pair_length_matched'] = None; r['pair_length_matched_note'] = 'n/a: no token longer than 2 symbols'
            r['lm_exact_length_coverage'] = None
        else:
            lm, cov = length_matched(tokens, target_hist)
            r['pair_length_matched'] = pair_violation(lm)['pair_violation_frac']
            r['lm_exact_length_coverage'] = round(cov, 3)
    r['seconds'] = round(time.time() - t1, 1)
    print(f"{label:28s} tok={r['n_tokens']} typ={r['types']} len={r['length']['mean']}/{r['length']['variance']} "
          f"zipf={r['zipf_slope_1_1000']} hapax={r['hapax_type_frac']} h2sp={r['h2_sp']} h2={r['h2_nosp']} "
          f"lock={r['positional']['locked_frac']} pv={r['pair']['pair_violation_frac']} lm={r.get('pair_length_matched')} {r['seconds']}s", flush=True)
    return r

# ------------------------------------------------------------------ languages + syllabifier
def load_book(path):
    t = path.read_text(encoding='utf-8', errors='replace')
    i = t.find('*** START OF'); j = t.find('*** END OF')
    k = t.find('\n', i) + 1 if i >= 0 else 0
    body = t[k:j] if j >= 0 else t[k:]
    return A3.LETTER.findall(body.lower())

def load_italian_all(max_chars=4_000_000):
    return A3.LETTER.findall(IT_CORPUS.read_text(encoding='utf-8', errors='replace')[:max_chars].lower())

VOW = set('aeiouy')
ON3 = {'str', 'spr', 'scr', 'spl', 'scl', 'sch', 'chr', 'thr', 'phr'}
ON2 = {'bl', 'br', 'cl', 'cr', 'dr', 'fl', 'fr', 'gl', 'gr', 'pl', 'pr', 'tr', 'ph', 'th', 'ch', 'qu', 'gn', 'st', 'sp', 'sc', 'sm', 'sn'}

def is_vowel(w, i):
    return w[i] in VOW and not (w[i] == 'u' and i > 0 and w[i - 1] == 'q')

def syllabify(w):
    v = [is_vowel(w, i) for i in range(len(w))]
    nuclei = []; i = 0
    while i < len(w):
        if v[i]:
            j = i
            while j < len(w) and v[j]: j += 1
            nuclei.append((i, j)); i = j
        else: i += 1
    if len(nuclei) <= 1: return [w]
    cuts = []
    for (s0, e0), (s1, e1) in zip(nuclei, nuclei[1:]):
        cl = w[e0:s1]; k = len(cl)
        if k == 1: cut = e0
        elif cl[-3:] in ON3 and k >= 3: cut = s1 - 3
        elif cl[-2:] in ON2: cut = s1 - 2
        else: cut = s1 - 1
        cuts.append(cut)
    out = []; start = 0
    for c in cuts: out.append(w[start:c]); start = c
    out.append(w[start:])
    return [s for s in out if s]

def cv_trim(syl):
    i = 0
    while i < len(syl) and not is_vowel(syl, i): i += 1
    onset = syl[:i]; nucleus = syl[i:i + 1] if i < len(syl) else ''
    if not nucleus: return onset[:1] if onset else syl
    return (onset[:1] if onset else '') + nucleus

def syl_tokens(words):
    return [s for w in words for s in syllabify(w)]

def syl2_chunks(words):
    """Bisyllabic chunks inside each word: syllables 1+2, 3+4, ...; an odd final syllable stands alone."""
    out = []
    for w in words:
        s = syllabify(w)
        for i in range(0, len(s), 2): out.append(s[i:i + 2])
    return out

def syl2_tokens(words):
    return [''.join(c) for c in syl2_chunks(words)]

# ================================================================== main
def main():
    out = {'method': __doc__, 'part1': {}, 'part2': {}, 'checks': {}}
    # ---------- part 1
    tsv_lines = tsv_P_lines(DATA / 'ZL3b-n.words.tsv')
    split_lines = parse_ivtff_P(DATA / 'ZL3b-n.txt', 'split')
    join_lines = parse_ivtff_P(DATA / 'ZL3b-n.txt', 'join')
    out['checks']['reparse_split_equals_tsv'] = [w for l in split_lines for w in l] == [w for l in tsv_lines for w in l]
    all_raw, all_total, all_drop = clean(tsv_lines)
    cer_raw, cer_total, cer_drop = clean(join_lines)
    n_comma = sum(len(a) - len(b) for a, b in zip(split_lines, join_lines))
    out['checks'].update({'P_lines': len(tsv_lines), 'ALL_words_before_filter': all_total, 'ALL_dropped': all_drop,
                          'CERTAIN_words_before_filter': cer_total, 'CERTAIN_dropped': cer_drop,
                          'uncertain_spaces_joined': n_comma,
                          'CERTAIN_words_that_contain_a_join': sum(1 for a, b in zip(split_lines, join_lines) for w in b if w not in a)})
    print('checks', out['checks'], flush=True)
    N_all = len(all_raw); N_cer = len(cer_raw)
    voy_sets = {'ALL': all_raw, 'CERTAIN': cer_raw, 'ALL_trunc': all_raw[:N_cer]}
    sym = {(k, a): to_symbols(v, tk) for k, v in voy_sets.items() for a, tk in ALPHABETS.items()}
    hists = {a: collections.Counter(len(w) for w in sym[('ALL', a)]) for a in ALPHABETS}
    target_hist = hists['merge_a3']          # languages are matched to ALL merge-a3 (as in v_a3)
    p1 = {}
    for k in voy_sets:
        for a in ALPHABETS:                  # CERTAIN/x is matched to ALL/x (same alphabet)
            p1[f'{k}/{a}'] = battery(sym[(k, a)], f'ZL {k} {a}', hists[a], do_lm=(k == 'CERTAIN'))
    # per-language (Currier) is not repeated here; the comparison is tokenisation-only.
    # what the joined words look like
    joined = [w for a, b in zip(split_lines, join_lines) for w in b if w not in a and '?' not in w and not (set(w) - EVA_OK)]
    jc = collections.Counter(joined)
    out['part1'] = {'N_ALL': N_all, 'N_CERTAIN': N_cer, 'stats': p1,
                    'joined_words': {'n': len(joined), 'mean_len_raw': round(sum(map(len, joined)) / len(joined), 2),
                                     'frac_that_are_ALL_types': round(sum(1 for w in joined if w in set(all_raw)) / len(joined), 3),
                                     'top20': jc.most_common(20)}}
    # ---------- part 2
    books = {'la_prose': load_book(CORP / 'corp_la_33849.txt'), 'la_verse': load_book(CORP / 'corp_la_227.txt'),
             'it': load_italian_all()}
    ex = {w: syllabify(w) for w in ['confessiones', 'instrumentum', 'quae', 'aeneidos', 'arma', 'virumque', 'cano', 'troiae',
                                   'misericordia', 'magister', 'pastor', 'esse', 'illustrissimo', 'signore', 'sanctissimo', 'perche', 'gli']}
    out['part2']['examples'] = {w: {'syl': s, 'cv': [cv_trim(x) for x in s]} for w, s in ex.items()}
    print('examples', out['part2']['examples'], flush=True)
    p2 = {}; corpora_info = {}
    for name, words in books.items():
        syl_all = syl_tokens(words)
        corpora_info[name] = {'words_available': len(words), 'syllables_available': len(syl_all),
                              'syllables_per_word': round(len(syl_all) / len(words), 3),
                              'words_used_for_N_syllables': None}
        # how many words the first N syllables span
        acc = 0
        for i, w in enumerate(words):
            acc += len(syllabify(w))
            if acc >= N_all: corpora_info[name]['words_used_for_N_syllables'] = i + 1; break
        syl2_all = syl2_tokens(words)
        variants = {'words': words[:N_all], 'syl': syl_all[:N_all], 'cv': [cv_trim(s) for s in syl_all[:N_all]],
                    'syl2': syl2_all[:N_all], 'cv2': [''.join(cv_trim(s) for s in chunk) for chunk in syl2_chunks(words)][:N_all]}
        for v, toks in variants.items():
            p2[f'{name}/{v}'] = battery(toks, f'{name} {v}', target_hist)
        p2[f'{name}/syl_shuf'] = battery(A3.shuffle_within(variants['syl']), f'{name} syl_shuf', target_hist)
    out['part2']['corpora'] = corpora_info; out['part2']['stats'] = p2
    out['seconds'] = round(time.time() - T0)
    json.dump(out, open(RES / 'b1.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    write_md(out)
    print('written', RES / 'b1.json', RES / 'b1.md', out['seconds'], 's')

# ------------------------------------------------------------------ markdown
def row(label, r):
    L = r['length']; P = r['positional']; pv = r['pair']
    lm = r.get('pair_length_matched'); cov = r.get('lm_exact_length_coverage')
    lm = '-' if lm is None else (f'{lm:.3f}' + (f' (cov {cov:.2f})' if cov is not None and cov < 0.999 else ''))
    bl = pv['by_length']
    return (f"| {label} | {r['n_tokens']} | {r['types']} | {r['alphabet']} | {L['mean']:.2f} | {L['variance']:.2f} | {L['disp_len_minus1']} | "
            f"{r['zipf_slope_1_1000']:.3f} | {100*r['hapax_type_frac']:.1f} | {r['h1_sp']:.3f} | {r['h2_sp']:.3f} | {r['h1_nosp']:.3f} | {r['h2_nosp']:.3f} | "
            f"{r['h2_within_word']:.3f} | {P['locked_frac']} ({P['locked_n']}/{P['n_symbols']}) | {P['mi_bits']:.3f} | {pv['pair_violation_frac']:.3f} | {lm} | "
            f"{bl.get(2, '-')} / {bl.get(3, '-')} / {bl.get(4, '-')} / {bl.get(5, '-')} |")
HDR = ("| corpus | tokens | types | alphabet | len mean | len var | var/mean(len-1) | Zipf 1-1000 | hapax % types | h1 sp | h2 sp | h1 | h2 | h2 within | locked frac (n/N) | MI sym;pos | pair-viol | pair-viol length-matched | viol by len 2/3/4/5 |\n"
       "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")

def write_md(o):
    p1 = o['part1']; p2 = o['part2']; c = o['checks']
    L = ['# b1: segmentation controls -- certain-space tokenisation of ZL, and syllabically written Latin / Italian', '',
         f"Runtime {o['seconds']} s. Method choices are listed in the docstring of b1_segmentation.py (also stored in b1.json 'method').", '',
         '## Part 1. ZL paragraph text: ALL (every IVTFF comma a break) vs CERTAIN (commas joined, periods split)', '',
         f"Re-parse in split mode reproduces the TSV token list: {c['reparse_split_equals_tsv']}. P lines {c['P_lines']}. "
         f"Uncertain spaces joined: {c['uncertain_spaces_joined']}. ALL: {c['ALL_words_before_filter']} words before filter, dropped {c['ALL_dropped']}, N = {p1['N_ALL']}. "
         f"CERTAIN: {c['CERTAIN_words_before_filter']} words before filter, dropped {c['CERTAIN_dropped']}, N = {p1['N_CERTAIN']}; "
         f"{c['CERTAIN_words_that_contain_a_join']} CERTAIN words contain at least one join.", '',
         f"Joined words (clean): n={p1['joined_words']['n']}, mean raw length {p1['joined_words']['mean_len_raw']}, fraction that are already word types of ALL {p1['joined_words']['frac_that_are_ALL_types']}; "
         f"most common: {', '.join(f'{w} {n}' for w, n in p1['joined_words']['top20'])}", '',
         'ALL_trunc = ALL cut to the CERTAIN token count (size-matched comparison for types/hapax/Zipf). Length-matched pair-violation is computed for CERTAIN against the ALL merge-a3 length histogram.', '',
         HDR]
    for k, r in p1['stats'].items(): L.append(row(k, r))
    L += ['', '### Movement of NOTES.md figures (ALL -> CERTAIN)', '']
    A = p1['stats']; keys = [('raw', 'raw EVA'), ('merge_a3', 'merge-a3 (NOTES 4.3/4.4 alphabet)'), ('merge2_a1', 'merge2-a1 (NOTES 4.1 merged row)')]
    L.append('| statistic | alphabet | ALL | ALL_trunc | CERTAIN | delta CERTAIN-ALL |'); L.append('|---|---|---|---|---|---|')
    def line(stat, a, f):
        x, y, z = f(A[f'ALL/{a}']), f(A[f'ALL_trunc/{a}']), f(A[f'CERTAIN/{a}'])
        L.append(f'| {stat} | {a} | {x} | {y} | {z} | {round(z - x, 4)} |')
    for a, _ in keys:
        line('mean word length', a, lambda r: r['length']['mean']); line('word length variance', a, lambda r: r['length']['variance'])
        line('h1 no spaces', a, lambda r: r['h1_nosp']); line('h2 no spaces', a, lambda r: r['h2_nosp'])
        line('h2 with spaces', a, lambda r: r['h2_sp']); line('h2 within word', a, lambda r: r['h2_within_word'])
        line('pair-violation', a, lambda r: r['pair']['pair_violation_frac']); line('locked fraction', a, lambda r: r['positional']['locked_frac'])
        line('MI symbol;position', a, lambda r: r['positional']['mi_bits'])
    line('types', 'raw', lambda r: r['types']); line('hapax % types', 'raw', lambda r: round(100 * r['hapax_type_frac'], 1)); line('Zipf slope 1-1000', 'raw', lambda r: r['zipf_slope_1_1000'])
    L.append(f"| pair-violation length-matched to ALL | merge_a3 | {A['ALL/merge_a3']['pair']['pair_violation_frac']} | - | {A['CERTAIN/merge_a3'].get('pair_length_matched')} | |")
    L += ['', '## Part 2. Syllabically written Latin and Italian vs Voynichese', '',
          'Corpora: ' + '; '.join(f"{k}: {v['words_available']} words -> {v['syllables_available']} syllables ({v['syllables_per_word']} per word); first {p1['N_ALL']} syllables span {v['words_used_for_N_syllables']} words" for k, v in p2['corpora'].items()), '',
          'Syllabifier examples: ' + '; '.join(f"{w} -> {' '.join(d['syl'])} -> CV {' '.join(d['cv'])}" for w, d in p2['examples'].items()), '',
          'Rows: words = ordinary orthographic words; syl = syllables as words; cv = syllables trimmed to consonant+vowel; syl2 / cv2 = bisyllabic chunks (plain / CV-trimmed); syl_shuf = symbols shuffled inside each syllable (null for pair-violation). '
          'Voynich reference rows repeated from Part 1. All corpora at N = ZL ALL token count. "cov" after a length-matched value = fraction of the Voynich length histogram for which the corpus has tokens of exactly that length (the rest are filled from the nearest length).', '', HDR]
    for k in ['ALL/raw', 'ALL/merge_a3', 'ALL/merge2_a1']: L.append(row('ZL ' + k, p1['stats'][k]))
    for k, r in p2['stats'].items(): L.append(row(k, r))
    L += ['', '### Match table: which Voynich figures does each tokenisation reproduce?', '',
          'Voynich targets (ZL ALL): pair-violation length-matched 0.160 (merge-a3) / 0.157 (raw); length mean/var 4.11/2.48 merged, 5.07/3.73 raw; h2 with spaces (raw EVA) and without; hapax 69-70 %; Zipf -1.04; locked fraction 0.21-0.31; MI 0.69-0.73.', '',
          '| corpus | pair-viol (lm) vs 0.16 | len mean vs 4.1-5.1 | len var vs 2.5-3.7 | h2 sp vs Voynich raw | hapax % vs 69.7 | Zipf vs -1.04 | locked vs 0.21-0.31 | MI vs 0.69-0.73 |', '|---|---|---|---|---|---|---|---|---|']
    vr = p1['stats']['ALL/raw']
    for k, r in p2['stats'].items():
        lm = r.get('pair_length_matched'); lm_s = f"{lm:.3f}" if lm is not None else f"as-is {r['pair']['pair_violation_frac']:.3f}"
        L.append(f"| {k} | {lm_s} | {r['length']['mean']:.2f} | {r['length']['variance']:.2f} | {r['h2_sp']:.3f} (Voy {vr['h2_sp']:.3f}) | {100*r['hapax_type_frac']:.1f} | {r['zipf_slope_1_1000']:.3f} | {r['positional']['locked_frac']} | {r['positional']['mi_bits']:.3f} |")
    L += ['', 'All output is unvalidated until user review.']
    (RES / 'b1.md').write_text('\n'.join(L) + '\n', encoding='utf-8')

if __name__ == '__main__':
    main()
