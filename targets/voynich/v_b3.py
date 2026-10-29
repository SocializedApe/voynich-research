"""v_b3.py -- adversarial verification of b3_bakeoff.py (the generator bake-off).  Pure Python 3.12, stdlib only.

Recomputes with its own code (nothing imported from b3 or a4 for the quantities it checks):
  0. re-run comparison: committed results/b3.json (git HEAD) vs the re-run b3.json in the working tree
  1. own loaders: ZL3b-n locus P (csv by column name), shipped Naibbe ciphertext, Gaskell & Bowern gibberish;
     Latin through a4.lang_words (file loading only) and the autocopist through a4.Autocopist (the generator
     under test)
  2. independent battery subset: h2/h3 raw and merged (direct conditional entropy), Zipf, TTR, hapax, adjacent
     exact / LD<=1 (own LD<=1 test, validated against a DP Levenshtein), self-citation coverage / within 10 /
     within-page-shuffle ratio (seed-1 replication of b3's shuffle and 20 fresh shuffles), positional lock,
     MZ-style R(s) peak (b3's 3 shuffles replicated and 20 fresh shuffles), token predictability, character
     3-gram cross-entropy, JSD halves; full length and short (first 10,053 tokens)
  3. own match rule on the subset and agreement with b3's marks
  4. tolerance fairness: 20-group block-jackknife SE of every subset item for the real text and the candidates,
     tol / SE, a noise-aware re-score; a family-weighted re-count of b3's own 37-item marks
  5. gibberish at equal size: 38 writers each against Voynich chunks of the same token count; a whole-manuscript
     short reference instead of the herbal-A opening
  6. Naibbe port: own transcription of naibbe.py (token-for-token vs b3.Naibbe), decryption of the shipped
     ciphertext against the shipped plaintext, deck composition (52 vs 78 cards) from the unigram tokens,
     10-seed distribution of the port vs the shipped ciphertext, and the full 37-item battery port vs shipped
     (b3.battery used there only as the instrument, not as a check of b3's numbers)
  7. Naibbe long range: R(s) on plaintext words, on the decrypted letter units and on the ciphertext; a
     Pliny-then-Dante plaintext; pouring cannot reorder tokens
  8. section-5 sentence checks against the numbers
Writes results/v_b3.json and results/v_b3.md.  Does not modify b3 files.  python v_b3.py --md-only rewrites the md
from the json.
"""
import os as _os  # local paths (the September 2026 scripts hard-coded another machine)
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_CORP = _os.path.join(_HERE, 'data', 'corpora')  # corp_<lang>_<gutenberg id>.txt, see fetch_corpora.py
_EXT = _os.path.join(_HERE, 'data', 'external')  # third-party data (Naibbe, Gaskell & Bowern)
_IT = _os.path.join(_CORP, 'corpus_it.txt')  # vatican5 OCR corpus from the September sample's first words (fetch_corpora.py)
import sys, os, re, json, math, random, collections, statistics, time, csv, unicodedata, subprocess

BASE = _HERE
sys.path.insert(0, BASE)
OUT = os.path.join(BASE, 'results')
ZLF = os.path.join(BASE, 'data', 'ZL3b-n.words.tsv')
NAIBBE_DIR = os.path.join(_EXT, 'naibbe', 'out')
GIB_DIR = os.path.join(_EXT, 'gaskell_voynich', 'data', 'gib')
SCALES = [16, 32, 64, 128, 256, 512, 1024, 2048]
N_SHORT = 10053
AZ = re.compile(r'[a-z]+')
T0 = time.time()


def log(*a):
    print(f'[{time.time() - T0:6.1f}s]', *a, flush=True)


# ============================================================================ loaders (own code)
def load_zl():
    pages = collections.OrderedDict(); lang = collections.defaultdict(collections.Counter)
    with open(ZLF, encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE):
            if row['locus_type'] != 'P':
                continue
            ws = [w for w in row['line_words'].split() if AZ.fullmatch(w)]
            if not ws:
                continue
            pages.setdefault(row['folio'], []).append({'words': ws, 'para_start': row['para_start'] == '1'})
            lang[row['folio']][row['lang']] += 1
    return [{'folio': k, 'lines': v, 'lang': lang[k].most_common(1)[0][0]} for k, v in pages.items()]


def skel_of(pages):
    return [[(len(l['words']), len(' '.join(l['words'])), l['para_start']) for l in p['lines']] for p in pages]


def pour(words, skel):
    k = 0; out = []
    for pl in skel:
        lines = []
        for n, _, ps in pl:
            lines.append({'words': words[k:k + n], 'para_start': ps}); k += n
        out.append({'folio': '', 'lines': lines})
    assert k <= len(words)
    return out


def flat(pages):
    return [w for p in pages for l in p['lines'] for w in l['words']]


def page_tokens(pages):
    return [[w for l in p['lines'] for w in l['words']] for p in pages]


def truncate(pages, n):
    out = []; k = 0
    for p in pages:
        if k >= n:
            break
        lines = []
        for l in p['lines']:
            if k >= n:
                break
            ws = l['words'][:n - k]; k += len(ws); lines.append({'words': ws, 'para_start': l['para_start']})
        out.append({'folio': p.get('folio', ''), 'lines': lines, 'lang': p.get('lang')})
    return out


def deaccent(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))


def load_gibberish():
    files = []
    for fn in sorted(os.listdir(GIB_DIR)):
        if not fn.lower().endswith('.txt'):
            continue
        raw = open(os.path.join(GIB_DIR, fn), encoding='utf-8', errors='replace').read()
        toks = AZ.findall(deaccent(raw).lower())
        files.append({'file': fn, 'tokens': toks, 'nonascii_letters': sum(1 for c in raw if ord(c) > 127 and c.isalpha()),
                      'hyphen_breaks': len(re.findall(r'[A-Za-z]-\s*\n', raw))})
    return files


def read_cipher_lines(path):
    """shipped ciphertext -> list of token lists, one per file line (blank lines kept as [])"""
    return [AZ.findall(line.lower()) for line in open(path, encoding='utf-8', errors='replace')]


# ============================================================================ Levenshtein <= 1 (own code)
def le1(a, b):
    """True iff Levenshtein(a, b) <= 1; common-prefix / common-suffix test"""
    if a == b:
        return True
    la, lb = len(a), len(b)
    if la - lb > 1 or lb - la > 1:
        return False
    m = min(la, lb); i = 0
    while i < m and a[i] == b[i]:
        i += 1
    j = 0
    while j < m - i and a[la - 1 - j] == b[lb - 1 - j]:
        j += 1
    return max(la, lb) - (i + j) <= 1


def lev_dp(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


# ============================================================================ battery subset (own code)
MRG = re.compile('cfh|cph|ckh|cth|ch|sh|iiin|iin|in|ee')
MSYM = {'cfh': 'F', 'cph': 'P', 'ckh': 'K', 'cth': 'T', 'ch': 'C', 'sh': 'S', 'iiin': 'N', 'iin': 'N', 'in': 'N', 'ee': 'E'}


def merge(w):
    return MRG.sub(lambda m: MSYM[m.group(0)], w)


def pstrings(pt, merged=False):
    return [' ' + ' '.join(merge(w) if merged else w for w in ws) + ' ' for ws in pt]


def cond_H(strings, k):
    """H(X_n | previous k-1 symbols) in bits = sum_ctx p(ctx) H(next | ctx), contexts inside each string"""
    tab = collections.defaultdict(collections.Counter)
    for s in strings:
        for i in range(k - 1, len(s)):
            tab[s[i - k + 1:i]][s[i]] += 1
    N = sum(sum(c.values()) for c in tab.values()); h = 0.0
    for c in tab.values():
        m = sum(c.values())
        h += (m * math.log2(m) - sum(v * math.log2(v) for v in c.values())) / N
    return h


def zipf_slope(cnt, maxrank=1000):
    f = sorted(cnt.values(), reverse=True)[:maxrank]
    xs = [math.log10(r) for r in range(1, len(f) + 1)]; ys = [math.log10(v) for v in f]
    mx = sum(xs) / len(xs); my = sum(ys) / len(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)


def dkeys(w):
    return {w[:i] + w[i + 1:] for i in range(len(w))}


def skeys(w):
    return {(i, w[:i] + w[i + 1:]) for i in range(len(w))}


def selfcit(pt, coverage=True):
    """share of tokens with an LD<=1 token among the previous 10 on the same page, and (coverage) anywhere earlier
    on the same page (deletion / substitution key index)"""
    n = w10 = cov = 0
    for ws in pt:
        n += len(ws)
        se = set(); sd = set(); ss = set()
        for i, w in enumerate(ws):
            if any(le1(ws[j], w) for j in range(max(0, i - 10), i)):
                w10 += 1
            if coverage:
                dk = dkeys(w); sk = skeys(w)
                if w in se or w in sd or not dk.isdisjoint(se) or not sk.isdisjoint(ss):
                    cov += 1
                se.add(w); sd |= dk; ss |= sk
    return (cov / n if coverage else None), w10 / n


def shuffle_pages(pt, rng):
    out = []
    for ws in pt:
        x = list(ws); rng.shuffle(x); out.append(x)
    return out


def top5(cnt):
    return {g for g, _ in sorted(cnt.items(), key=lambda kv: -kv[1])[:5]}


def poslock(words):
    mw = [merge(w) for w in words]
    ti = top5(collections.Counter(w[0] for w in mw)); tf = top5(collections.Counter(w[-1] for w in mw))
    return sum(1 for w in mw if w[0] in ti and w[-1] in tf) / len(mw)


def Hc(cnt):
    n = sum(cnt.values())
    return math.log2(n) - sum(v * math.log2(v) for v in cnt.values()) / n


def block_H(seq, s):
    P = len(seq) // s
    return sum(Hc(collections.Counter(seq[j * s:(j + 1) * s])) for j in range(P)) / P


def mz(words, rng, nshuf):
    """R(s) = mean block entropy of shuffled copies - mean block entropy of the real order (= D_real - D_shuf)"""
    shufs = []
    for _ in range(nshuf):
        x = list(words); rng.shuffle(x); shufs.append(x)
    curve = collections.OrderedDict()
    for s in SCALES:
        if len(words) // s < 4:
            continue
        curve[s] = sum(block_H(x, s) for x in shufs) / nshuf - block_H(words, s)
    peak = max(curve, key=curve.get)
    return curve, peak, curve[peak]


def first_max(cnt):
    best = None; bv = -1
    for k, v in cnt.items():           # insertion order: the first-seen key wins ties
        if v > bv:
            best, bv = k, v
    return best


def predict(pt):
    strs = pstrings(pt); V = len(set(''.join(strs)))
    acc = []; bits = []
    for fold in (0, 1):
        tr = [ws for i, ws in enumerate(pt) if i % 2 == fold]; te = [ws for i, ws in enumerate(pt) if i % 2 != fold]
        succ = collections.defaultdict(collections.Counter); uni = collections.Counter()
        for ws in tr:
            uni.update(ws)
            for a, b in zip(ws, ws[1:]):
                succ[a][b] += 1
        best = {a: first_max(c) for a, c in succ.items()}; dflt = first_max(uni)
        hit = tot = 0
        for ws in te:
            for a, b in zip(ws, ws[1:]):
                tot += 1; hit += (best.get(a, dflt) == b)
        acc.append(hit / tot)
        tri = collections.Counter(); ctx = collections.Counter()
        for s in pstrings(tr):
            for i in range(2, len(s)):
                tri[s[i - 2:i + 1]] += 1; ctx[s[i - 2:i]] += 1
        lp = 0.0; n = 0
        for s in pstrings(te):
            for i in range(2, len(s)):
                lp -= math.log2((tri.get(s[i - 2:i + 1], 0) + 0.1) / (ctx.get(s[i - 2:i], 0) + 0.1 * V)); n += 1
        bits.append(lp / n)
    return sum(acc) / 2, sum(bits) / 2


def bigram_dist(strings):
    c = collections.Counter()
    for s in strings:
        c.update(s[i:i + 2] for i in range(len(s) - 1))
    n = sum(c.values())
    return {k: v / n for k, v in c.items()}


def jsd(p, q):
    d = 0.0
    for k in set(p) | set(q):
        a = p.get(k, 0.0); b = q.get(k, 0.0); m = (a + b) / 2
        if a:
            d += a / 2 * math.log2(a / m)
        if b:
            d += b / 2 * math.log2(b / m)
    return d


ITEMS = ['a_h2_raw', 'a_h3_raw', 'a_h2_mrg', 'a_h3_mrg', 'c_zipf', 'c_ttr', 'c_hapax_types', 'c_hapax_tokens',
         'd_adj_exact', 'd_adj_ld1', 'e_cover', 'e_w10', 'e_w10_shuf', 'e_ratio', 'f_lock', 'h_peak_log2s', 'h_peak_R',
         'i_tok_acc', 'i_char_bits', 'k_jsd_halves']
LABEL = {'a_h2_raw': 'h2 raw', 'a_h3_raw': 'h3 raw', 'a_h2_mrg': 'h2 mrg', 'a_h3_mrg': 'h3 mrg', 'c_zipf': 'Zipf', 'c_ttr': 'TTR',
         'c_hapax_types': 'hapax/types', 'c_hapax_tokens': 'hapax/tokens', 'd_adj_exact': 'adj exact', 'd_adj_ld1': 'adj LD<=1',
         'e_cover': 'sc cover', 'e_w10': 'sc <=10', 'e_w10_shuf': 'sc <=10 shuf', 'e_ratio': 'sc ratio', 'f_lock': 'pos lock',
         'h_peak_log2s': 'MZ peak log2 s', 'h_peak_R': 'MZ peak R', 'i_tok_acc': 'tok pred', 'i_char_bits': 'char 3g bits',
         'k_jsd_halves': 'JSD halves'}


def battery(pages, extras=False):
    pt = page_tokens(pages); words = [w for ws in pt for w in ws]; N = len(words)
    ps = pstrings(pt); pm = pstrings(pt, merged=True)
    R = collections.OrderedDict(); X = {}
    R['a_h2_raw'] = cond_H(ps, 2); R['a_h3_raw'] = cond_H(ps, 3); R['a_h2_mrg'] = cond_H(pm, 2); R['a_h3_mrg'] = cond_H(pm, 3)
    cnt = collections.Counter(words); hap = sum(1 for v in cnt.values() if v == 1)
    R['c_zipf'] = zipf_slope(cnt); R['c_ttr'] = len(cnt) / N; R['c_hapax_types'] = hap / len(cnt); R['c_hapax_tokens'] = hap / N
    R['d_adj_exact'] = sum(a == b for a, b in zip(words, words[1:])) / (N - 1)
    R['d_adj_ld1'] = sum(le1(a, b) for a, b in zip(words, words[1:])) / (N - 1)
    cov, w10 = selfcit(pt)
    _, w10s = selfcit(shuffle_pages(pt, random.Random(1)), coverage=False)   # same procedure and seed as a4.shuffle_within_page
    R['e_cover'] = cov; R['e_w10'] = w10; R['e_w10_shuf'] = w10s; R['e_ratio'] = w10 / w10s
    R['f_lock'] = poslock(words)
    curve, peak, pr = mz(words, random.Random(3), 3)                          # same shuffles as b3 (random.Random(3), 3 copies)
    R['h_peak_log2s'] = math.log2(peak); R['h_peak_R'] = pr; X['mz_curve'] = {str(k): v for k, v in curve.items()}
    R['i_tok_acc'], R['i_char_bits'] = predict(pt)
    h = len(pm) // 2; R['k_jsd_halves'] = jsd(bigram_dist(pm[:h]), bigram_dist(pm[h:]))
    X['tokens'] = N; X['pages'] = len(pt)
    if extras:
        rs = []
        for sd in range(101, 121):
            _, ws = selfcit(shuffle_pages(pt, random.Random(sd)), coverage=False); rs.append(w10 / ws)
        X['e_ratio_20shuf'] = {'mean': statistics.mean(rs), 'sd': statistics.stdev(rs), 'min': min(rs), 'max': max(rs)}
        c20, p20, r20 = mz(words, random.Random(303), 20)
        X['mz_20shuf'] = {'peak_log2s': math.log2(p20), 'peak_R': r20, 'curve': {str(k): v for k, v in c20.items()}}
    return R, X


# ============================================================================ match rule (own code)
def tolerances(res, real='voynich_ZL', ac=('autocopist_s19', 'autocopist_s7')):
    return {k: max(0.10 * abs(res[real][k]), abs(res[ac[0]][k] - res[ac[1]][k])) for k in ITEMS}


def marks(res, tol, real='voynich_ZL'):
    return {n: {k: abs(r[k] - res[real][k]) <= tol[k] for k in ITEMS} for n, r in res.items()}


# ============================================================================ Naibbe (own transcription of naibbe.py v1)
def naibbe_tables():
    g = {}
    with open(os.path.join(NAIBBE_DIR, 'references_naibbe_tables.csv'), encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            g[row['code'].strip()] = row['glyphs'].strip()
    return g


DECK52 = [('alpha', 20), ('beta1', 8), ('beta2', 8), ('beta3', 8), ('gamma1', 4), ('gamma2', 4)]
DECK78 = [('alpha', 28), ('beta1', 14), ('beta2', 11), ('beta3', 11), ('gamma1', 7), ('gamma2', 7)]
TABLES = [t for t, _ in DECK52]


def my_clean(line):
    s = ''.join(c for c in unicodedata.normalize('NFD', line) if unicodedata.category(c) != 'Mn')
    rep = {'æ': 'ae', 'Æ': 'ae', 'œ': 'oe', 'Œ': 'oe', 'ð': 'd', 'Ð': 'd', 'þ': 'th', 'Þ': 'th', 'ł': 'l', 'Ł': 'l', 'ß': 'ss', 'ø': 'o', 'Ø': 'o'}
    s = ''.join(rep.get(c, c) for c in s)
    s = ''.join(c for c in s if c.isalpha()).upper().replace('W', 'UU').replace('J', 'I').replace('K', 'C')
    return s.lower()


def my_naibbe(path, seed, use78=False, need=10 ** 9, reset_per_line=True):
    """naibbe.py __main__ loop, one random.Random(seed) in place of the module-level random; v1 rule (reject a bigram
    token only if it equals a unigram glyph).  reset_per_line=False is a control (one deck running across lines).
    Returns (lines of tokens, retries)"""
    rng = random.Random(seed); G = naibbe_tables(); uni = {g for c, g in G.items() if c.startswith('unigram_')}
    deckspec = DECK78 if use78 else DECK52; retries = 0; lines = []; n = 0
    deck = []; di = 0
    for raw in open(path, encoding='utf-8', errors='replace'):
        text = my_clean(raw)
        if not text:
            lines.append([]); continue
        grams = []; i = 0
        while i < len(text):
            if i == len(text) - 1 or rng.random() < 17 / 36:
                grams.append(text[i]); i += 1
            else:
                grams.append(text[i:i + 2]); i += 2
        if reset_per_line:
            deck = [t for t, c in deckspec for _ in range(c)]; rng.shuffle(deck); di = 0
        out = []
        for g in grams:
            if len(g) == 1:
                if di >= len(deck):
                    deck = [t for t, c in deckspec for _ in range(c)]; rng.shuffle(deck); di = 0
                t = deck[di]; di += 1; code = f'unigram_{t}_{g}'; out.append(G.get(code, code))
            else:
                while True:
                    if di >= len(deck):
                        deck = [t for t, c in deckspec for _ in range(c)]; rng.shuffle(deck); di = 0
                    tp = deck[di]; di += 1
                    if di >= len(deck):
                        deck = [t for t, c in deckspec for _ in range(c)]; rng.shuffle(deck); di = 0
                    ts = deck[di]; di += 1
                    cp = f'prefix_{tp}_{g[0]}'; cs = f'suffix_{ts}_{g[1]}'
                    tok = G.get(cp, cp) + G.get(cs, cs)
                    if tok not in uni:
                        out.append(tok); break
                    retries += 1
        lines.append(out); n += len(out)
        if n >= need:
            break
    return lines, retries


def naibbe_decoder():
    G = naibbe_tables(); uni = collections.defaultdict(list); pre = {}; suf = {}
    for c, g in G.items():
        st, t, l = c.split('_')
        if st == 'unigram':
            uni[g].append((t, l))
        elif st == 'prefix':
            pre[g] = (t, l)
        else:
            suf[g] = (t, l)
    def dec(tok):
        """-> (set of candidate plaintext letter strings, [card tables, in draw order], kind uni / bi / amb / none).
        A token in the unigram glyph set is a unigram (v1 rejects bigram tokens equal to a unigram glyph); otherwise every
        prefix + suffix split is a candidate (all of length 2)."""
        if tok in uni:
            v = uni[tok]
            return {x[1] for x in v}, ([v[0][0]] if len(v) == 1 else ['beta2|beta3']), 'uni'
        sols = [(pre[tok[:k]][1] + suf[tok[k:]][1], [pre[tok[:k]][0], suf[tok[k:]][0]]) for k in range(1, len(tok)) if tok[:k] in pre and tok[k:] in suf]
        if not sols:
            return set(), [], 'none'
        return {x[0] for x in sols}, sols[0][1], ('bi' if len({x[0] for x in sols}) == 1 else 'amb')
    return dec


def align(cipher_lines, plain_lines, dec):
    """decrypt line by line against the plaintext (cleaned as naibbe.py does); returns (lines exact, lines failing,
    token kinds, flat list of plaintext units = the respaced plaintext the cipher actually encrypted)"""
    ok = bad = 0; kinds = collections.Counter(); units = []
    for ct, raw in zip(cipher_lines, plain_lines):
        c = my_clean(raw)
        if not ct and not c:
            continue
        pos = 0; good = True; lu = []
        for w in ct:
            cs, _, kind = dec(w); kinds[kind] += 1
            L = len(next(iter(cs))) if cs else 1
            seg = c[pos:pos + L]
            if seg not in cs:
                good = False
            lu.append(seg if seg in cs else (sorted(cs)[0] if cs else '?')); pos += L
        good = good and pos == len(c)
        ok += good; bad += (not good); units.extend(lu)
    return ok, bad, dict(kinds), units


def deck_test(lines, dec):
    """table counts among unigram tokens (one card each; 'dar' = beta2/beta3 split half and half); plus the variance,
    over lines, of the number of alpha cards among the first 40 visible cards of the line (unigram = 1 card, accepted
    bigram = prefix + suffix card): a deck reshuffled at every line start gives a hypergeometric (small) variance"""
    cnt = collections.Counter(); n_uni = n_tok = 0; alpha40 = []
    for ws in lines:
        cards = []
        for w in ws:
            n_tok += 1
            _, tabs, kind = dec(w); cards.extend(tabs)
            if kind == 'uni':
                n_uni += 1
                for t in (['beta2', 'beta3'] if tabs == ['beta2|beta3'] else tabs):
                    cnt[t] += 1 / (2 if tabs == ['beta2|beta3'] else 1)
        if len(cards) >= 40:
            alpha40.append(sum(1 for t in cards[:40] if t == 'alpha'))
    tot = sum(cnt.values()); out = {'unigram_tokens': n_uni, 'tokens': n_tok, 'unigram_share': n_uni / n_tok,
                                     'table_share': {t: cnt[t] / tot for t in TABLES},
                                     'alpha_in_first40_cards': {'lines': len(alpha40), 'mean': statistics.mean(alpha40), 'var': statistics.pvariance(alpha40)}}
    for name, spec in (('chi2_52', DECK52), ('chi2_78', DECK78)):
        S = sum(c for _, c in spec)
        out[name] = sum((cnt[t] - tot * c / S) ** 2 / (tot * c / S) for t, c in spec)
    return out


# ============================================================================ helpers for section 5
def unit_metrics(toks, rng):
    """metrics of one writer file / one Voynich chunk treated as a single page"""
    s = [' ' + ' '.join(toks) + ' ']; cnt = collections.Counter(toks); n = len(toks)
    _, w10 = selfcit([toks], coverage=False)
    sh = []
    for _ in range(5):
        x = list(toks); rng.shuffle(x); sh.append(selfcit([x], coverage=False)[1])
    msh = sum(sh) / 5
    return {'h2_raw': cond_H(s, 2), 'ttr': len(cnt) / n, 'hapax_types': sum(1 for v in cnt.values() if v == 1) / len(cnt),
            'adj_exact': sum(a == b for a, b in zip(toks, toks[1:])) / (n - 1), 'adj_ld1': sum(le1(a, b) for a, b in zip(toks, toks[1:])) / (n - 1),
            'sc_w10': w10, 'sc_ratio': (w10 / msh) if msh else None, 'pos_lock': poslock(toks)}


def quant(xs, q):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    i = (len(xs) - 1) * q; lo = int(math.floor(i)); hi = int(math.ceil(i))
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


# ============================================================================ main
def main():
    RES = collections.OrderedDict()
    # ---------------------------------------------------------------- 0. re-run vs committed
    committed = json.loads(subprocess.run(['git', 'show', 'HEAD:targets/voynich/results/b3.json'], cwd=BASE, capture_output=True,
                                          check=True).stdout.decode('utf-8'))
    rerun = json.load(open(os.path.join(OUT, 'b3.json'), encoding='utf-8'))
    diff = {}
    for part in ('full', 'short'):
        for n in committed[part]:
            d = {k: [committed[part][n][k], rerun[part][n][k]] for k in committed[part][n]
                 if committed[part][n][k] is not None and abs(committed[part][n][k] - rerun[part][n][k]) > 1e-9}
            if d:
                diff[f'{part}:{n}'] = d
    RES['rerun'] = {'corpora_with_changed_values': sorted(diff), 'n_changed_values': sum(len(v) for v in diff.values()),
                    'tol_changed': [k for k in committed['tol_full'] if abs(committed['tol_full'][k] - rerun['tol_full'][k]) > 1e-12]
                    + [k for k in committed['tol_short'] if abs(committed['tol_short'][k] - rerun['tol_short'][k]) > 1e-12],
                    'matches_full_committed': committed['matches_full'], 'matches_full_rerun': rerun['matches_full'],
                    'matches_short_committed': committed['matches_short'], 'matches_short_rerun': rerun['matches_short'],
                    'italian_top10_committed': committed['extra_full']['italian']['top10'], 'italian_top10_rerun': rerun['extra_full']['italian']['top10'],
                    'naibbe_port_check_identical': committed['meta']['naibbe_port_check'] == rerun['meta']['naibbe_port_check'],
                    'diff': diff}
    it_head = open(_IT, encoding='utf-8', errors='replace').read(300) if os.path.exists(_IT) else None
    RES['rerun']['italian_file_first_chars_today'] = it_head
    log('rerun', {k: v for k, v in RES['rerun'].items() if k not in ('diff', 'italian_file_first_chars_today')})

    # ---------------------------------------------------------------- 1. loaders
    zl = load_zl(); skel = skel_of(zl); N = len(flat(zl))
    import a4_selfcitation as A          # file loading (lang_words) and the autocopist generator only
    import b3_bakeoff as B               # the Naibbe port class (generator under test) and, in 6d only, B.battery as instrument
    ref = A.load_zl()
    RES['data'] = {'pages': len(zl), 'lines': sum(len(p) for p in skel), 'tokens': N,
                   'same_tokens_as_a4_loader': flat(zl) == flat(ref), 'currier_pages': dict(collections.Counter(p['lang'] for p in zl))}
    short_lang = collections.Counter()
    k = 0
    for p in zl:
        for l in p['lines']:
            for w in l['words']:
                if k < N_SHORT:
                    short_lang[p['lang']] += 1
                k += 1
    RES['data']['short_tokens_by_currier'] = dict(short_lang)
    RES['data']['short_last_folio'] = truncate(zl, N_SHORT)[-1]['folio']
    # LD check
    rng = random.Random(123); types = list(set(flat(zl))); bad = []; nchk = 0
    for _ in range(40000):
        a, b = rng.choice(types), rng.choice(types)
        if rng.random() < 0.5:   # make near pairs too
            i = rng.randrange(len(a) + 1); b = a[:i] + rng.choice('abcdefghiklmnopqrstxy') + a[i + rng.choice((0, 1)):]
        nchk += 1
        if (lev_dp(a, b) <= 1) != le1(a, b):
            bad.append((a, b))
    for a, b in [('abc', 'ab'), ('abc', 'bc'), ('abc', 'ac'), ('ab', 'ba'), ('aab', 'ab'), ('aba', 'aa'), ('a', ''), ('abcd', 'abdc'), ('daiin', 'dain'), ('qokeey', 'okeey')]:
        nchk += 1
        if (lev_dp(a, b) <= 1) != le1(a, b):
            bad.append((a, b))
    RES['ld_check'] = {'pairs': nchk, 'disagreements': bad[:10], 'n_disagree': len(bad)}
    log('ld check', RES['ld_check'])

    corp = collections.OrderedDict()
    corp['voynich_ZL'] = zl
    corp['latin'] = pour(A.lang_words('la', N), skel)
    ship_lines = read_cipher_lines(os.path.join(NAIBBE_DIR, 'encrypted_nathist_output_ciphertext.txt'))
    ship = [w for ws in ship_lines for w in ws]
    corp['naibbe_pliny'] = pour(ship[:N], skel)
    corp['autocopist_s19'] = A.Autocopist(19).generate(skel)
    corp['autocopist_s7'] = A.Autocopist(7).generate(skel)
    gfiles = load_gibberish(); gib = [w for f in gfiles for w in f['tokens']]
    corp['gaskell_gibberish'] = pour((gib * (-(-N // len(gib))))[:N], skel)
    RES['gibberish_files'] = {'files': len(gfiles), 'tokens': len(gib), 'per_file_min_max_median': [min(len(f['tokens']) for f in gfiles), max(len(f['tokens']) for f in gfiles), statistics.median(len(f['tokens']) for f in gfiles)],
                              'nonascii_letters': sum(f['nonascii_letters'] for f in gfiles), 'hyphen_line_breaks': sum(f['hyphen_breaks'] for f in gfiles)}
    ne = [ws for ws in ship_lines if ws]
    RES['naibbe_shipped'] = {'tokens': len(ship), 'nonempty_lines': len(ne), 'mean_tokens_per_line': len(ship) / len(ne)}
    log('corpora', {n: len(flat(p)) for n, p in corp.items()}, RES['gibberish_files'], RES['naibbe_shipped'])

    # ---------------------------------------------------------------- 2. independent battery (full and short)
    full = collections.OrderedDict(); short = collections.OrderedDict(); xf = {}; xs = {}
    for n, p in corp.items():
        full[n], xf[n] = battery(p, extras=(n != 'autocopist_s7'))
        short[n], xs[n] = battery(truncate(p, N_SHORT))
        log('battery', n)
    RES['indep_full'] = full; RES['indep_short'] = short; RES['indep_extra_full'] = xf
    # ---------------------------------------------------------------- 3. match rule + agreement with b3
    tf = tolerances(full); ts = tolerances(short); mf = marks(full, tf); ms = marks(short, ts)
    agree = {}
    for part, mk, bm, bres, ires in (('full', mf, rerun['marks_full'], rerun['full'], full), ('short', ms, rerun['marks_short'], rerun['short'], short)):
        for n in corp:
            dis = [k for k in ITEMS if mk[n][k] != bm[n][k]]
            maxrel = max(abs(ires[n][k] - bres[n][k]) / (abs(bres[n][k]) or 1) for k in ITEMS)
            agree[f'{part}:{n}'] = {'subset_matches_indep': sum(mk[n].values()), 'subset_matches_b3': sum(bm[n][k] for k in ITEMS),
                                    'mark_disagreements': dis, 'max_rel_diff_vs_b3': maxrel,
                                    'worst_item': max(ITEMS, key=lambda k: abs(ires[n][k] - bres[n][k]) / (abs(bres[n][k]) or 1))}
    RES['tol_full'] = tf; RES['tol_short'] = ts; RES['marks_full'] = mf; RES['marks_short'] = ms; RES['agreement'] = agree
    log('agreement', {k: (v['subset_matches_indep'], v['subset_matches_b3'], v['mark_disagreements'], round(v['max_rel_diff_vs_b3'], 5)) for k, v in agree.items()})

    # ---------------------------------------------------------------- 4. tolerance fairness: block jackknife
    G = 20
    jk = {}
    for n in ('voynich_ZL', 'latin', 'naibbe_pliny', 'autocopist_s19'):
        pages = corp[n]; P = len(pages); bounds = [round(P * g / G) for g in range(G + 1)]
        vals = {k: [] for k in ITEMS}
        for g in range(G):
            sub = pages[:bounds[g]] + pages[bounds[g + 1]:]
            r, _ = battery(sub)
            for k in ITEMS:
                vals[k].append(r[k])
        jk[n] = {k: math.sqrt((G - 1) / G * sum((v - statistics.mean(vals[k])) ** 2 for v in vals[k])) for k in ITEMS}
        log('jackknife', n)
    RES['jackknife_se'] = jk
    fair = {}
    for k in ITEMS:
        se = jk['voynich_ZL'][k]
        fair[k] = {'real': full['voynich_ZL'][k], 'tol': tf[k], 'se_real': se, 'tol_over_se': (tf[k] / se) if se else None,
                   'tol_over_real': tf[k] / abs(full['voynich_ZL'][k]) if full['voynich_ZL'][k] else None,
                   'A_minus_B_b3': rerun['full']['voynich_A'][k] - rerun['full']['voynich_B'][k]}
    RES['tolerance_fairness'] = fair
    noise = {}
    for n in ('latin', 'naibbe_pliny', 'autocopist_s19'):
        m = {}
        for k in ITEMS:
            band = max(tf[k], 2 * math.sqrt(jk['voynich_ZL'][k] ** 2 + jk[n][k] ** 2))
            m[k] = abs(full[n][k] - full['voynich_ZL'][k]) <= band
        noise[n] = {'matches_noise_rule': sum(m.values()), 'matches_b3_rule': sum(mf[n].values()), 'gained': [k for k in ITEMS if m[k] and not mf[n][k]]}
    RES['noise_rule'] = noise
    FAM = collections.OrderedDict([
        ('entropy', ['a_h0_raw', 'a_h1_raw', 'a_h2_raw', 'a_h3_raw', 'a_h2_mrg', 'a_h3_mrg']),
        ('word length', ['b_len_mean', 'b_len_sd', 'b_len1', 'b_len9']),
        ('vocabulary', ['c_zipf', 'c_ttr', 'c_hapax_types', 'c_hapax_tokens', 'c_heaps', 'j_one_page']),
        ('adjacency', ['d_adj_exact', 'd_adj_ld1']),
        ('self-citation', ['e_cover', 'e_w10', 'e_prev2', 'e_w10_shuf', 'e_ratio']),
        ('slot grammar', ['f_irrev', 'f_lock']),
        ('line position', ['g_len_first', 'g_len_mid', 'g_len_last', 'g_gal_init', 'g_gal_mid']),
        ('long range', ['h_peak_log2s', 'h_peak_R']),
        ('predictability', ['i_tok_acc', 'i_char_bits']),
        ('page level / drift', ['j_jacc_excess', 'k_jsd_halves', 'k_jsd_oddeven'])])
    assert sorted(k for v in FAM.values() for k in v) == sorted(rerun['full']['voynich_ZL'])
    fam = {}
    for n in rerun['full']:
        fam[n] = {part: round(sum(sum(rerun[f'marks_{part}'][n][k] for k in ks) / len(ks) for ks in FAM.values()), 2) for part in ('full', 'short')}
    RES['family_count'] = {'families': FAM, 'scores_out_of_10': fam}
    free = [k for k in rerun['tol_full'] if rerun['full']['voynich_ZL'][k] and rerun['tol_full'][k] >= abs(rerun['full']['voynich_ZL'][k])]
    RES['items_tol_ge_real_full'] = free
    RES['items_tol_ge_real_short'] = [k for k in rerun['tol_short'] if rerun['short']['voynich_ZL'][k] and rerun['tol_short'][k] >= abs(rerun['short']['voynich_ZL'][k])]
    RES['spread_set_tol_full'] = [k for k in rerun['tol_full'] if rerun['tol_full'][k] > 0.10 * abs(rerun['full']['voynich_ZL'][k]) + 1e-15]
    log('fairness done', noise, fam)

    # ---------------------------------------------------------------- 5. gibberish at equal size
    zflat = flat(zl); rng5 = random.Random(55); K = 40
    gm = []; vm = []; inband = collections.Counter(); nband = collections.Counter()
    for f in gfiles:
        t = f['tokens']; n = len(t)
        g = unit_metrics(t, rng5); gm.append(g)
        chunks = []
        for _ in range(K):
            s = rng5.randrange(len(zflat) - n); chunks.append(unit_metrics(zflat[s:s + n], rng5))
        vm.extend(chunks)
        for m in g:
            lo = quant([c[m] for c in chunks], 0.05); hi = quant([c[m] for c in chunks], 0.95)
            if g[m] is not None and lo is not None:
                nband[m] += 1; inband[m] += (lo <= g[m] <= hi)
    per = {}
    for m in gm[0]:
        per[m] = {'gib_median': quant([x[m] for x in gm], 0.5), 'gib_q25_q75': [quant([x[m] for x in gm], 0.25), quant([x[m] for x in gm], 0.75)],
                  'voy_median': quant([x[m] for x in vm], 0.5), 'voy_q25_q75': [quant([x[m] for x in vm], 0.25), quant([x[m] for x in vm], 0.75)],
                  'gib_files_inside_voy_5_95': f'{inband[m]}/{nband[m]}'}
    RES['gibberish_per_writer'] = per
    # whole-manuscript short reference: every third page from the start until 10,053 tokens
    alt = []; k = 0
    for i in range(0, len(zl), 3):
        if k >= N_SHORT:
            break
        alt.append(zl[i]); k += sum(len(l['words']) for l in zl[i]['lines'])
    alt = truncate(alt, N_SHORT); ra, _ = battery(alt)
    RES['short_reference_whole_ms'] = {'pages_used': len(alt), 'currier': dict(collections.Counter(p['lang'] for p in alt)), 'values': ra}
    ts_alt = {k: max(0.10 * abs(ra[k]), abs(short['autocopist_s19'][k] - short['autocopist_s7'][k])) for k in ITEMS}
    RES['short_whole_ms_matches'] = {n: sum(abs(short[n][k] - ra[k]) <= ts_alt[k] for k in ITEMS) for n in corp if n != 'voynich_ZL'}
    RES['short_herbalA_matches'] = {n: sum(ms[n].values()) for n in corp if n != 'voynich_ZL'}
    log('gibberish per writer', per, RES['short_whole_ms_matches'])

    # ---------------------------------------------------------------- 6. Naibbe port
    pl_path = os.path.join(NAIBBE_DIR, 'input_examples_nathist_book16.txt'); dc_path = os.path.join(NAIBBE_DIR, 'input_examples_divina_commedia.txt')
    csvp = os.path.join(NAIBBE_DIR, 'references_naibbe_tables.csv')
    nbB = B.Naibbe(csvp, seed=19); b3_lines = nbB.generate(pl_path, 10 ** 9)
    my_lines, my_retries = my_naibbe(pl_path, 19)
    b3_tok = [w for ws, _ in b3_lines for w in ws]; my_tok = [w for ws in my_lines for w in ws]
    nb6 = {'port_vs_own_transcription_identical': b3_tok == my_tok, 'port_tokens': len(b3_tok), 'own_tokens': len(my_tok),
           'retries_port': nbB.retries, 'retries_own': my_retries}
    dec = naibbe_decoder()
    # decrypt the shipped ciphertext line by line against the shipped plaintext
    pl_raw = open(pl_path, encoding='utf-8', errors='replace').read().split('\n')
    ok, bad_l, kinds, ship_units = align(ship_lines, pl_raw, dec)
    nb6['shipped_decrypts_to_shipped_plaintext'] = {'lines_ok': ok, 'lines_bad': bad_l, 'token_kinds': kinds,
                                                     'line_counts': [len(ship_lines), len(pl_raw)],
                                                     'unit_share_1letter': sum(1 for u in ship_units if len(u) == 1) / len(ship_units)}
    nb6['deck_shipped'] = deck_test(ship_lines, dec)
    nb6['deck_port52'] = deck_test(my_lines, dec)
    l78, _ = my_naibbe(pl_path, 19, use78=True)
    nb6['deck_own78_control'] = deck_test(l78, dec)
    lc, _ = my_naibbe(pl_path, 19, reset_per_line=False)
    nb6['deck_own52_one_running_deck_control'] = deck_test(lc, dec)
    seeds = [19, 1, 2, 3, 4, 5, 6, 7, 8, 9]; sv = []; tokn = []
    for sd in seeds:
        ls, _ = my_naibbe(pl_path, sd); tk = [w for ws in ls for w in ws]; tokn.append(len(tk))
        r, _ = battery(pour(tk[:N], skel)); sv.append(r)
    for sd in (19, 1, 2):
        ls, _ = my_naibbe(pl_path, sd, use78=True); tk = [w for ws in ls for w in ws]
        r, _ = battery(pour(tk[:N], skel)); nb6.setdefault('v78_values', []).append(r)
    dist = {}
    for kk in ITEMS:
        xsv = [r[kk] for r in sv]; mu = statistics.mean(xsv); sdv = statistics.stdev(xsv)
        dist[kk] = {'shipped': full['naibbe_pliny'][kk], 'port_mean': mu, 'port_sd': sdv, 'port_min': min(xsv), 'port_max': max(xsv),
                    'z_shipped': (full['naibbe_pliny'][kk] - mu) / sdv if sdv else None,
                    'v78_mean': statistics.mean(r[kk] for r in nb6['v78_values']), 'tol_b3_rule': tf[kk]}
    nb6['seed_distribution'] = dist
    nb6['seed_token_counts'] = {'port_seeds': tokn, 'shipped': len(ship)}
    nb6['port_marks_range_subset'] = [sum(abs(r[kk] - full['voynich_ZL'][kk]) <= tf[kk] for kk in ITEMS) for r in sv]
    del nb6['v78_values']
    # 6d: full 37-item battery (b3.battery as the instrument) port seed 19 vs shipped
    ext = {}
    port_pages = pour(b3_tok[:N], skel)
    bp = B.battery(port_pages, 'port', ext); bs = rerun['full']['naibbe_pliny']
    bp_s = B.battery(truncate(port_pages, N_SHORT), 'port_s', ext); bs_s = rerun['short']['naibbe_pliny']
    def mk(vals, part):
        return {kk: abs(vals[kk] - rerun[part]['voynich_ZL'][kk]) <= rerun[f'tol_{part}'][kk] for kk in vals}
    mp, msh = mk(bp, 'full'), mk(bs, 'full'); mps, mss = mk(bp_s, 'short'), mk(bs_s, 'short')
    nb6['battery37'] = {'port_full_matches': sum(mp.values()), 'shipped_full_matches': sum(msh.values()),
                        'port_short_matches': sum(mps.values()), 'shipped_short_matches': sum(mss.values()),
                        'items_mark_differs_full': [kk for kk in mp if mp[kk] != msh[kk]], 'items_mark_differs_short': [kk for kk in mps if mps[kk] != mss[kk]],
                        'items_port_shipped_gap_gt_tol_full': {kk: [bp[kk], bs[kk]] for kk in bp if abs(bp[kk] - bs[kk]) > rerun['tol_full'][kk]}}
    RES['naibbe_port'] = nb6
    log('naibbe port', {k: v for k, v in nb6.items() if k not in ('seed_distribution',)})

    # ---------------------------------------------------------------- 7. Naibbe long range
    def plain_words(path, nlines=None):
        out = []
        for i, raw in enumerate(open(path, encoding='utf-8', errors='replace')):
            if nlines is not None and i >= nlines:
                break
            out.extend(AZ.findall(deaccent(raw).lower()))
        return out
    lr = collections.OrderedDict()
    def curve(name, seq):
        c, p, r = mz(seq, random.Random(707), 10)
        lr[name] = {'tokens': len(seq), 'types': len(set(seq)), 'peak_log2s': math.log2(p), 'peak_R': r, 'curve': {str(k): v for k, v in c.items()}}
    curve('naibbe_pliny ciphertext (first N)', ship[:N])
    curve('naibbe_pliny decrypted letter units (first N)', ship_units[:N])
    curve('Pliny NH 16 plaintext words (whole book)', plain_words(pl_path))
    dc_lines, _ = my_naibbe(dc_path, 19, need=N); dc_tok = [w for ws in dc_lines for w in ws][:N]
    nb_dc = B.Naibbe(csvp, seed=19).generate(dc_path, N); dc_b3 = [w for ws, _ in nb_dc for w in ws][:N]
    dc_ok, dc_bad, _, dc_units = align(dc_lines, open(dc_path, encoding='utf-8', errors='replace').read().split('\n'), dec)
    lr_meta = {'divcom_own_equals_b3_port': dc_tok == dc_b3, 'divcom_plaintext_lines_used': len(dc_lines), 'divcom_decrypt_lines_ok_bad': [dc_ok, dc_bad]}
    curve('naibbe_divcom ciphertext (first N)', dc_tok)
    curve('naibbe_divcom decrypted letter units', dc_units[:N])
    curve('Divina Commedia plaintext words (lines encrypted)', plain_words(dc_path, len(dc_lines)))
    nw = lr['Pliny NH 16 plaintext words (whole book)']['tokens']
    curve('latin control, same word count as Pliny', A.lang_words('la', nw))
    curve('voynich_ZL, same token count as Pliny words', zflat[:nw])
    curve('voynich_ZL (full)', zflat)
    # pouring cannot reorder tokens
    lr_meta['pour_preserves_order'] = flat(pour(ship[:N], skel)) == ship[:N]
    # hybrid probe: Pliny ciphertext then Dante ciphertext, half each
    mixtok = ship[:N // 2] + dc_tok[:N - N // 2]
    rmix, _ = battery(pour(mixtok, skel))
    lr_meta['pliny_then_dante'] = {'k_jsd_halves': rmix['k_jsd_halves'], 'h_peak_R': rmix['h_peak_R'], 'h_peak_log2s': rmix['h_peak_log2s'],
                                   'matches_subset': sum(abs(rmix[kk] - full['voynich_ZL'][kk]) <= tf[kk] for kk in ITEMS)}
    RES['naibbe_long_range'] = {'curves': lr, 'meta': lr_meta}
    log('long range', {k: (v['tokens'], round(v['peak_R'], 4), v['peak_log2s']) for k, v in lr.items()}, lr_meta)

    RES['_meta'] = {'runtime_s': round(time.time() - T0, 1), 'N': N, 'N_short': N_SHORT}
    json.dump(RES, open(os.path.join(OUT, 'v_b3.json'), 'w', encoding='utf-8'), indent=1, default=str)
    log('json written')
    return RES


# ============================================================================ markdown
def f3(v):
    if v is None:
        return '-'
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, (int,)):
        return str(v)
    return f'{v:.3g}' if abs(v) < 0.01 else f'{v:.3f}'


def write_md(R):
    committed = json.loads(subprocess.run(['git', 'show', 'HEAD:targets/voynich/results/b3.json'], cwd=BASE, capture_output=True, check=True).stdout.decode('utf-8'))
    rr = json.load(open(os.path.join(OUT, 'b3.json'), encoding='utf-8'))
    I = R['indep_full']; Is = R['indep_short']
    cf, rf = committed['full'], rr['full']
    L = ['# v_b3: adversarial verification of b3 (generator bake-off)', '',
         f"Runtime {R['_meta']['runtime_s']} s.  ZL3b-n locus P: {R['data']['tokens']} tokens, {R['data']['pages']} pages, {R['data']['lines']} lines "
         f"(own csv loader; identical token list to a4.load_zl: {R['data']['same_tokens_as_a4_loader']}).  Own LD<=1 test vs DP Levenshtein: "
         f"{R['ld_check']['pairs']} pairs, {R['ld_check']['n_disagree']} disagreements.  Nothing below imports b3 or a4 for a checked quantity; "
         'a4.lang_words (Latin file loading), a4.Autocopist and b3.Naibbe (generators under test) are reused, and b3.battery is used only in section 5 (port vs shipped, 37 items) as '
         'the instrument for port-vs-shipped.', '']
    # ---- 0
    rer = R['rerun']
    L += ['## 0. Re-run of b3_bakeoff.py as-is (11 Oct 2026, corpora and Naibbe repo downloaded today)', '',
          f"Changed values against the committed b3.json: {rer['n_changed_values']}, all in {', '.join(rer['corpora_with_changed_values'])}.  Tolerances changed: "
          f"{rer['tol_changed'] or 'none'}.  Naibbe port check identical: {rer['naibbe_port_check_identical']}.  Every other corpus (ZL, A, B, Latin, English, "
          'both autocopists, both Rugg tables, the three Naibbe ciphertexts, gibberish) reproduces to the last digit.', '',
          '| corpus | full committed | full re-run | short committed | short re-run |', '|---|---|---|---|---|']
    for n in rer['matches_full_committed']:
        L.append(f"| {n} | {rer['matches_full_committed'][n]} | {rer['matches_full_rerun'][n]} | {rer['matches_short_committed'][n]} | {rer['matches_short_rerun'][n]} |")
    L += ['', 'Why Italian moved: a4.lang_words("it") reads targets/vatican5/corpus_it.txt, a git-ignored file that vatican5/build_it_lm.py '
          'regenerates from Nuntiaturberichte OCR.  The September run read a build that opened "cumque predictus fcrdiuandu s rex nuper in romanorum '
          'regem electus" (a Latin passage; v_a4.md) with top words ' + ', '.join(f'{w}({c})' for w, c in rer['italian_top10_committed'][:6]) +
          '; the copy in this checkout (built 14 Sept on this machine) opens with OCR debris and German editorial text ("' +
          ' '.join((rer['italian_file_first_chars_today'] or '').split()[:12]) + ' ...") and has top words ' +
          ', '.join(f'{w}({c})' for w, c in rer['italian_top10_rerun'][:6]) + '.  Neither build is a clean Italian text; the Italian row is not '
          'reproducible from the repository and should be read as "OCR nunciature Italian, build-dependent".', '']
    # ---- claims table
    def ac_range(key, part='full'):
        return [rr[part]['autocopist_s19'][key], rr[part]['autocopist_s7'][key]]
    nb = R['naibbe_port']; lr = R['naibbe_long_range']
    rows = []
    def row(claim, b3v, rerv, indv, verdict):
        rows.append(f'| {claim} | {b3v} | {rerv} | {indv} | {verdict} |')
    cm, rm = committed['matches_full'], rr['matches_full']; cms, rms = committed['matches_short'], rr['matches_short']
    sub_ind = lambda n, part='full': sum(R['marks_' + part][n].values())
    row('B pages fail 18/37 (short)', f"{37 - cms['voynich_B']}", f"{37 - rms['voynich_B']}", '-', 'confirmed')
    row('three Naibbe score best, 17/37 full and short', f"{cm['naibbe_pliny']}/{cm['naibbe_pliny_lines']}/{cm['naibbe_divcom']} full; {cms['naibbe_pliny']}/{cms['naibbe_pliny_lines']}/{cms['naibbe_divcom']} short",
        f"{rm['naibbe_pliny']}/{rm['naibbe_pliny_lines']}/{rm['naibbe_divcom']}; {rms['naibbe_pliny']}/{rms['naibbe_pliny_lines']}/{rms['naibbe_divcom']}",
        f"subset (20 items) naibbe_pliny {sub_ind('naibbe_pliny')} full / {sub_ind('naibbe_pliny', 'short')} short",
        'corrected: divcom short is 16; "17 full, 16-17 short"')
    row('Rugg-sorted and Italian next (13-14)', f"rugg_sorted {cm['rugg_sorted']}/{cms['rugg_sorted']}, italian {cm['italian']}/{cms['italian']}",
        f"rugg_sorted {rm['rugg_sorted']}/{rms['rugg_sorted']}, italian {rm['italian']}/{rms['italian']}", '-',
        'corrected: Italian short was 12 in Sept, and is 9 full / 8 short with today\'s corpus_it.txt (not reproducible); autocopist_s7 short is 14')
    row('others trail at 8-14', 'latin 9/10, english 9/9, ac19 9/10, ac7 9/14, grille 8/10, gibberish 9/9', 'same', '-', 'confirmed (the 14 is ac7 short, which ties the "next" group)')
    blab = dict((k, l) for k, l in rr['meta']['items'])
    allfail_f = [blab[k] for k in rr['marks_full']['voynich_ZL'] if not any(rr['marks_full'][n][k] for n in rr['marks_full'] if not n.startswith('voynich'))]
    allfail_c = [blab[k] for k in committed['marks_full']['voynich_ZL'] if not any(committed['marks_full'][n][k] for n in committed['marks_full'] if not n.startswith('voynich'))]
    own_f = [LABEL[k] for k in ('d_adj_exact', 'd_adj_ld1', 'e_w10', 'h_peak_R', 'k_jsd_halves') if not any(R['marks_full'][n][k] for n in R['marks_full'] if n != 'voynich_ZL')]
    vfail = {k: [n for n in ('voynich_A', 'voynich_B') if not rr['marks_full'][n][k]] for k in ('h_peak_R', 'k_jsd_halves')}
    row('every non-Voynich corpus fails adj exact, adj LD<=1, sc <=10, MZ peak R and (full) JSD halves', f"full all-fail list: {', '.join(allfail_c)}", f"full all-fail list: {', '.join(allfail_f)}",
        f"own rule, 5 corpora: all fail {', '.join(own_f)}",
        f"confirmed as arithmetic; but MZ peak R is also failed by voynich_{'/'.join(x[-1] for x in vfail['h_peak_R'])} and JSD halves by voynich_{'/'.join(x[-1] for x in vfail['k_jsd_halves'])}: both items reward the A+B mixture, which no single-regime generator was given")
    row('JSD halves 0.063; languages 0.003-0.007, autocopist 0.02, Rugg 0.003-0.01, Naibbe 0.002',
        f"{cf['voynich_ZL']['k_jsd_halves']:.3f}; la {cf['latin']['k_jsd_halves']:.4f} it {cf['italian']['k_jsd_halves']:.4f} en {cf['english']['k_jsd_halves']:.4f}",
        f"{rf['voynich_ZL']['k_jsd_halves']:.3f}; it {rf['italian']['k_jsd_halves']:.4f}", f"ZL {I['voynich_ZL']['k_jsd_halves']:.4f}, la {I['latin']['k_jsd_halves']:.4f}, naibbe {I['naibbe_pliny']['k_jsd_halves']:.4f}, ac19 {I['autocopist_s19']['k_jsd_halves']:.4f}", 'confirmed')
    lang = ('latin', 'italian', 'english')
    h2d = [rf[n]['a_h2_raw'] - rf['voynich_ZL']['a_h2_raw'] for n in lang]; h3d = [rf[n]['a_h3_raw'] - rf['voynich_ZL']['a_h3_raw'] for n in lang]
    row('languages: h2/h3 about 1 bit too high', f"h2 +{min(h2d[0],h2d[2]):.2f}..+{max(h2d[0],h2d[2]):.2f} (la, en), it +{cf['italian']['a_h2_raw']-cf['voynich_ZL']['a_h2_raw']:.2f}",
        f"h2 +{min(h2d):.2f}..+{max(h2d):.2f}; h3 +{min(h3d):.2f}..+{max(h3d):.2f}", f"latin h2 +{I['latin']['a_h2_raw']-I['voynich_ZL']['a_h2_raw']:.2f}, h3 +{I['latin']['a_h3_raw']-I['voynich_ZL']['a_h3_raw']:.2f}",
        'confirmed for h2 (+1.1 to +1.3); h3 is +0.7 to +1.0 (Sept); wording "0.7-1.3 bits"')
    row('languages: positional lock 0.26-0.35 vs 0.64', f"{cf['english']['f_lock']:.3f}-{cf['italian']['f_lock']:.3f}", f"{min(rf[n]['f_lock'] for n in lang):.3f}-{max(rf[n]['f_lock'] for n in lang):.3f}", f"latin {I['latin']['f_lock']:.3f}, ZL {I['voynich_ZL']['f_lock']:.3f}", 'confirmed')
    acz = ac_range('c_zipf'); tz = rr['tol_full']['c_zipf']
    row('autocopist reproduces the Zipf neighbourhood', f"{acz[0]:.3f} / {acz[1]:.3f} vs {rf['voynich_ZL']['c_zipf']:.3f}, tol {tz:.3f}", 'fails (both seeds, full and short)',
        f"ac19 {I['autocopist_s19']['c_zipf']:.3f} vs {I['voynich_ZL']['c_zipf']:.3f}, mark {R['marks_full']['autocopist_s19']['c_zipf']}", 'corrected: the autocopist fails Zipf in both seeds at both lengths')
    row('autocopist reproduces sc ratio and MZ peak position', f"ratio {ac_range('e_ratio')[0]:.3f}/{ac_range('e_ratio')[1]:.3f}; peak 2^9", 'same',
        f"ratio {I['autocopist_s19']['e_ratio']:.3f} (20 shuffles {R['indep_extra_full']['autocopist_s19']['e_ratio_20shuf']['mean']:.3f} +- {R['indep_extra_full']['autocopist_s19']['e_ratio_20shuf']['sd']:.3f}); peak 2^{I['autocopist_s19']['h_peak_log2s']:.0f}", 'confirmed')
    ac_h2 = [a - rf['voynich_ZL']['a_h2_raw'] for a in ac_range('a_h2_raw')]; ac_m2 = [a - rf['voynich_ZL']['a_h2_mrg'] for a in ac_range('a_h2_mrg')]
    row('autocopist: a 1-bit excess in glyph entropy', f"h2 raw +{min(ac_h2):.2f}..+{max(ac_h2):.2f}, h2 mrg +{min(ac_m2):.2f}..+{max(ac_m2):.2f}", 'same',
        f"ac19 h2 raw +{I['autocopist_s19']['a_h2_raw']-I['voynich_ZL']['a_h2_raw']:.2f}, mrg +{I['autocopist_s19']['a_h2_mrg']-I['voynich_ZL']['a_h2_mrg']:.2f}", 'corrected: the excess is 0.4-0.6 bits, not 1 bit')
    row('autocopist: TTR 0.34-0.38 vs 0.21, Heaps 0.85-0.88 vs 0.74, gallows mid 0.26-0.37 vs 0.065, token pred near zero',
        f"TTR {ac_range('c_ttr')[1]:.3f}-{ac_range('c_ttr')[0]:.3f}; tok pred {ac_range('i_tok_acc')[0]:.4f}/{ac_range('i_tok_acc')[1]:.4f}", 'same',
        f"TTR {I['autocopist_s19']['c_ttr']:.3f}; tok pred {I['autocopist_s19']['i_tok_acc']:.4f} vs {I['voynich_ZL']['i_tok_acc']:.4f}", 'confirmed')
    row('Rugg grille hapax/types 0.06, MZ R 2.0; sorted 9 % exact repeats', f"{cf['rugg_grille']['c_hapax_types']:.3f}, {cf['rugg_grille']['h_peak_R']:.2f}; {cf['rugg_sorted']['d_adj_exact']:.3f}", 'same', 'not recomputed', 'confirmed (re-run)')
    nz = rf['naibbe_pliny']['c_zipf']; ndz = rf['naibbe_divcom']['c_zipf']
    row('Naibbe matches character entropies, word length, positional lock, char predictability and Zipf slope',
        f"Zipf {nz:.3f} / {ndz:.3f} vs {rf['voynich_ZL']['c_zipf']:.3f} (tol {tz:.3f})", 'Zipf fails (all three, full and short)',
        f"Zipf {I['naibbe_pliny']['c_zipf']:.3f}, mark {R['marks_full']['naibbe_pliny']['c_zipf']}; h2 raw mark {R['marks_full']['naibbe_pliny']['a_h2_raw']}, lock mark {R['marks_full']['naibbe_pliny']['f_lock']}, char3g mark {R['marks_full']['naibbe_pliny']['i_char_bits']}",
        'corrected: Zipf is a Naibbe fail; the rest confirmed')
    nbR = [max(abs(d['R']) for d in rr['extra_full'][n]['mz_curve'].values()) for n in ('naibbe_pliny', 'naibbe_divcom')]
    row('Naibbe: R(s) about 0.003 bits at every scale, vs 0.29 real, 0.08-0.16 languages',
        f"peak {cf['naibbe_pliny']['h_peak_R']:.4f} / {cf['naibbe_divcom']['h_peak_R']:.4f}; languages {cf['latin']['h_peak_R']:.3f}-{cf['english']['h_peak_R']:.3f}",
        f"max |R| {max(nbR):.4f}; italian now {rf['italian']['h_peak_R']:.3f}",
        f"peak {I['naibbe_pliny']['h_peak_R']:.4f}; 20 shuffles {R['indep_extra_full']['naibbe_pliny']['mz_20shuf']['peak_R']:.4f}; real {I['voynich_ZL']['h_peak_R']:.3f}",
        'confirmed in substance: |R| <= 0.009 at every scale; language range 0.06-0.16 with today\'s Italian')
    row('Naibbe: too few hapaxes, sc ratio 0.96-0.98 vs 1.13, no line-initial gallows preference',
        f"hapax/types {cf['naibbe_pliny']['c_hapax_types']:.3f}; ratio {cf['naibbe_pliny']['e_ratio']:.3f}/{cf['naibbe_pliny_lines']['e_ratio']:.3f}/{cf['naibbe_divcom']['e_ratio']:.3f}", 'same',
        f"ratio {I['naibbe_pliny']['e_ratio']:.3f} (20 shuffles {R['indep_extra_full']['naibbe_pliny']['e_ratio_20shuf']['mean']:.3f} +- {R['indep_extra_full']['naibbe_pliny']['e_ratio_20shuf']['sd']:.3f})", 'confirmed')
    row('gibberish: h2 3.9 bits, positional lock 0.14', f"{cf['gaskell_gibberish']['a_h2_raw']:.3f}, {cf['gaskell_gibberish']['f_lock']:.3f}", 'same',
        f"pooled {I['gaskell_gibberish']['a_h2_raw']:.3f}, {I['gaskell_gibberish']['f_lock']:.3f}; per writer median h2 {R['gibberish_per_writer']['h2_raw']['gib_median']:.2f} vs Voynich chunks {R['gibberish_per_writer']['h2_raw']['voy_median']:.2f}, lock {R['gibberish_per_writer']['pos_lock']['gib_median']:.2f} vs {R['gibberish_per_writer']['pos_lock']['voy_median']:.2f}",
        'confirmed; the pooled h2 mixes 38 writers, but the per-writer comparison at equal size gives the same verdict')
    acR = ac_range('h_peak_R')
    row('long-range and drift items demand what neither (Naibbe, autocopist) supplies', f"autocopist MZ R {acR[0]:.3f}/{acR[1]:.3f} vs {rf['voynich_ZL']['h_peak_R']:.3f}", 'same',
        f"ac19 R {I['autocopist_s19']['h_peak_R']:.3f}", 'corrected: the autocopist overshoots the long-range peak (0.47 vs 0.29) rather than lacking it; only the A-to-B drift (JSD halves) is missing from both')
    sc = R['data']['short_tokens_by_currier']; ash = sc.get('A', 0) / sum(sc.values())
    row('first 10,053 ZL tokens are almost entirely Currier-A herbal pages, so voynich_A short is nearly the same text', '-', '-',
        f"{sc} tokens by page language ({ash:.0%} A); last page {R['data']['short_last_folio']}",
        'corrected: herbal pages f1r-f58v, but only about three quarters Currier A (the Currier-B herbal leaves fall inside); voynich_A short and voynich_ZL short still agree on 37/37 items')
    row('naibbe_pliny_lines: 1,063 shipped lines; 207 pages', '1,063 lines; table 200 pages, 1044 lines', 'same', f"{R['naibbe_shipped']['nonempty_lines']} non-empty lines, {R['naibbe_shipped']['mean_tokens_per_line']:.1f} tokens/line",
        'corrected: the construction yields 200 pages (1,044 lines used), not 207')
    row('gibberish 38 files, 10,075 clean tokens', f"{committed['meta']['gibberish']['files']}, {committed['meta']['gibberish']['clean_tokens']}", f"{rr['meta']['gibberish']['clean_tokens']}", f"{R['gibberish_files']['files']}, {R['gibberish_files']['tokens']}", 'confirmed')
    row('port re-encrypts Pliny close to the shipped file (34,625 vs 34,764 tokens)', f"{committed['meta']['naibbe_port_check']['port_tokens']} vs {committed['meta']['naibbe_port_check']['shipped_tokens']}", 'same',
        f"own transcription identical to port: {nb['port_vs_own_transcription_identical']}; 10 seeds {min(nb['seed_token_counts']['port_seeds'])}-{max(nb['seed_token_counts']['port_seeds'])}", 'confirmed (see 6)')
    row('pre-registered: battery and rule fixed before any score was computed', 'asserted in docstring and section 6', '-', 'script and results first appear in one commit (f1a99b941, 16 Sept)',
        'not reproducible from the record: no timestamp separates the battery from the results; NOTES.md section 7 (15 Sept) named the idea and a different item list')
    L += ['## 1. Claims in b3.md against the numbers', '',
          'b3 value = committed b3.json / b3.md; re-run = b3_bakeoff.py run today; independent = this script (own code, 20-item subset, same corpora).', '',
          '| claim in b3.md | b3 value | re-run value | independent value | verdict |', '|---|---|---|---|---|'] + rows + ['']
    # ---- independent subset table
    L += ['## 2. Independent recomputation of the subset (full length)', '',
          'Max relative difference to b3 per corpus over the 20 items (b3 re-run values): ' +
          '; '.join(f"{k.split(':')[1]} {v['max_rel_diff_vs_b3']:.2g} ({LABEL[v['worst_item']]})" for k, v in R['agreement'].items() if k.startswith('full:')) + '.  '
          'Short battery: ' + '; '.join(f"{k.split(':')[1]} {v['max_rel_diff_vs_b3']:.2g}" for k, v in R['agreement'].items() if k.startswith('short:')) + '.', '',
          'Mark disagreements with b3 under the same rule (subset): ' + ('; '.join(f"{k}: {', '.join(LABEL[x] for x in v['mark_disagreements'])}" for k, v in R['agreement'].items() if v['mark_disagreements']) or 'none') + '.', '']
    hdr = '| corpus | ' + ' | '.join(LABEL[k] for k in ITEMS) + ' | matched (subset) |'
    L += [hdr, '|' + '---|' * (len(ITEMS) + 2)]
    for n, r in I.items():
        L.append(f'| {n} | ' + ' | '.join(f3(r[k]) + (' ✓' if R['marks_full'][n][k] else ' ✗') for k in ITEMS) + f" | {sum(R['marks_full'][n].values())}/{len(ITEMS)} |")
    L += ['', 'Short (first 10,053 tokens):', '', hdr, '|' + '---|' * (len(ITEMS) + 2)]
    for n, r in Is.items():
        L.append(f'| {n} | ' + ' | '.join(f3(r[k]) + (' ✓' if R['marks_short'][n][k] else ' ✗') for k in ITEMS) + f" | {sum(R['marks_short'][n].values())}/{len(ITEMS)} |")
    X = R['indep_extra_full']
    L += ['', 'Shuffle noise (b3 uses one within-page shuffle for e and three token shuffles for h):', '',
          '| corpus | sc ratio, seed 1 | sc ratio, 20 shuffles mean +- sd [min, max] | MZ peak R, 3 shuffles | MZ peak R, 20 shuffles | peak log2 s, 3 / 20 |', '|---|---|---|---|---|---|']
    for n in X:
        if 'e_ratio_20shuf' in X[n]:
            e = X[n]['e_ratio_20shuf']; m = X[n]['mz_20shuf']
            L.append(f"| {n} | {I[n]['e_ratio']:.3f} | {e['mean']:.3f} +- {e['sd']:.3f} [{e['min']:.3f}, {e['max']:.3f}] | {I[n]['h_peak_R']:.4f} | {m['peak_R']:.4f} | {I[n]['h_peak_log2s']:.0f} / {m['peak_log2s']:.0f} |")
    # ---- 3 fairness
    F = R['tolerance_fairness']
    L += ['', '## 3. Is the tolerance rule fair?', '',
          'Block jackknife over 20 contiguous page groups gives the sampling SE of each item on the real text.  tol/SE < 2 means the rule is '
          'stricter than the real text\'s own sampling noise (a candidate identical in law to Voynichese would fail often); tol/SE > 10 means the item is '
          'nearly free.  A-B = difference between the Currier A and B pages (b3 re-run), the text\'s own heterogeneity.', '',
          '| item | real | tol | tol/real | SE (jackknife) | tol/SE | A - B |', '|---|---|---|---|---|---|---|']
    for k in ITEMS:
        d = F[k]
        L.append(f"| {LABEL[k]} | {f3(d['real'])} | {f3(d['tol'])} | {f3(d['tol_over_real'])} | {f3(d['se_real'])} | {f3(d['tol_over_se'])} | {f3(d['A_minus_B_b3'])} |")
    L += ['', f"Items of the 37 whose tolerance is at least the real value itself (any value between 0 and twice the real value matches), full: {', '.join(R['items_tol_ge_real_full'])}; short: {', '.join(R['items_tol_ge_real_short'])}.",
          f"Items whose full-length tolerance is set by the autocopist seed spread rather than 10 %: {', '.join(R['spread_set_tol_full'])}.", '',
          'Noise-aware re-score (match iff |v - real| <= max(tol, 2 sqrt(SE_real^2 + SE_corpus^2)), subset of 20, full length): ' +
          '; '.join(f"{n} {v['matches_b3_rule']} -> {v['matches_noise_rule']} (gains {', '.join(LABEL[x] for x in v['gained']) or 'none'})" for n, v in R['noise_rule'].items()) + '.', '',
          'Family-weighted count of b3\'s own 37 marks (re-run json; 10 families, each scored as the share of its items matched, so the six correlated entropy items count once):', '',
          '| corpus | items full | family score full (of 10) | items short | family score short |', '|---|---|---|---|---|']
    for n, v in R['family_count']['scores_out_of_10'].items():
        L.append(f"| {n} | {rr['matches_full'][n]} | {v['full']} | {rr['matches_short'][n]} | {v['short']} |")
    # ---- 4 gibberish
    G = R['gibberish_per_writer']
    L += ['', '## 4. Gibberish at equal size', '',
          f"{R['gibberish_files']['files']} files, {R['gibberish_files']['tokens']} tokens (per file min/max/median {R['gibberish_files']['per_file_min_max_median']}); "
          f"{R['gibberish_files']['nonascii_letters']} non-ASCII letters before accent stripping; {R['gibberish_files']['hyphen_line_breaks']} hyphenated line breaks split into two tokens.  "
          'Each writer\'s file is compared, as one page, with 40 random runs of the same number of consecutive Voynich tokens (all metrics on the run as one page).', '',
          '| metric | gibberish median [IQR] | Voynich chunks median [IQR] | gibberish files inside Voynich 5-95 % |', '|---|---|---|---|']
    for m, d in G.items():
        L.append(f"| {m} | {f3(d['gib_median'])} [{f3(d['gib_q25_q75'][0])}, {f3(d['gib_q25_q75'][1])}] | {f3(d['voy_median'])} [{f3(d['voy_q25_q75'][0])}, {f3(d['voy_q25_q75'][1])}] | {d['gib_files_inside_voy_5_95']} |")
    sr = R['short_reference_whole_ms']
    L += ['', f"Whole-manuscript short reference (every third page from f1r, {sr['pages_used']} pages, Currier {sr['currier']}) instead of the herbal-A opening; subset matches out of 20: " +
          '; '.join(f"{n} {R['short_herbalA_matches'][n]} -> {R['short_whole_ms_matches'][n]}" for n in R['short_whole_ms_matches']) + '.', '']
    # ---- 5 naibbe port
    L += ['## 5. Naibbe port fidelity', '',
          f"- Own transcription of naibbe.py (v1) with random.Random(19) vs b3.Naibbe(seed 19) on Pliny: identical token stream: {nb['port_vs_own_transcription_identical']} ({nb['port_tokens']} tokens, retries {nb['retries_port']} / {nb['retries_own']}).",
          f"- Shipped ciphertext decrypted with the shipped tables (a token in the unigram glyph set is a unigram; otherwise every prefix + suffix split is a candidate) against the shipped plaintext, cleaned as naibbe.py cleans it: "
          f"{nb['shipped_decrypts_to_shipped_plaintext']['lines_ok']} of {nb['shipped_decrypts_to_shipped_plaintext']['lines_ok'] + nb['shipped_decrypts_to_shipped_plaintext']['lines_bad']} lines exact; token kinds {nb['shipped_decrypts_to_shipped_plaintext']['token_kinds']} "
          f"(amb = more than one split, resolved by the plaintext).  No bigram token equals a unigram glyph, so UNAMBIGUOUS was on.  Share of one-letter units {nb['shipped_decrypts_to_shipped_plaintext']['unit_share_1letter']:.3f} (RESPACING 17 gives 17/36 = 0.472 plus the forced last letter of each line).",
          '- Deck.  Table shares among unigram tokens (52 cards: alpha .385, beta .154 each, gamma .077 each; 78 cards: alpha .359, beta1 .179, beta2/3 .141, gamma .090), '
          'and the variance over lines of the number of alpha cards among the first 40 visible cards (a deck reshuffled at every line start is hypergeometric, about 2.2-2.7; one deck running across lines is larger):', '',
          '| text | unigram tokens | unigram share | alpha | beta1 | beta2 | beta3 | gamma1 | gamma2 | chi2 vs 52 | chi2 vs 78 | alpha in first 40 cards: lines, mean, var |', '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for lab, d in (('shipped Pliny', nb['deck_shipped']), ('port (= own transcription), 52 cards, seed 19', nb['deck_port52']), ('own 78-card control', nb['deck_own78_control']),
                   ('own 52-card control, one deck across lines', nb['deck_own52_one_running_deck_control'])):
        a = d['alpha_in_first40_cards']
        L.append(f"| {lab} | {d['unigram_tokens']} | {d['unigram_share']:.3f} | " + ' | '.join(f"{d['table_share'][t]:.3f}" for t in TABLES) + f" | {d['chi2_52']:.1f} | {d['chi2_78']:.1f} | {a['lines']}, {a['mean']:.2f}, {a['var']:.2f} |")
    L += ['', f"- Ten seeds of the port on the Pliny plaintext (token counts {nb['seed_token_counts']['port_seeds']}; shipped {nb['seed_token_counts']['shipped']}); subset matches per seed {nb['port_marks_range_subset']}:", '',
          '| item | shipped | port mean +- sd [min, max] | z(shipped) | 78-card mean | b3 tol |', '|---|---|---|---|---|---|']
    for k, d in nb['seed_distribution'].items():
        L.append(f"| {LABEL[k]} | {f3(d['shipped'])} | {f3(d['port_mean'])} +- {f3(d['port_sd'])} [{f3(d['port_min'])}, {f3(d['port_max'])}] | {f3(d['z_shipped'])} | {f3(d['v78_mean'])} | {f3(d['tol_b3_rule'])} |")
    b37 = nb['battery37']
    L += ['', f"- Full 37-item battery (b3.battery as instrument, b3's tolerances): port seed 19 matches {b37['port_full_matches']} full / {b37['port_short_matches']} short; shipped {b37['shipped_full_matches']} / {b37['shipped_short_matches']}.  "
          f"Items whose mark differs: full {b37['items_mark_differs_full'] or 'none'}, short {b37['items_mark_differs_short'] or 'none'}.  Items where port and shipped differ by more than tol: {list(b37['items_port_shipped_gap_gt_tol_full']) or 'none'}.", '']
    # ---- 6 long range
    L += ['## 6. Naibbe long range: cipher property or skeleton artefact?', '',
          f"Pouring only cuts the flat token stream into lines and pages; it never reorders tokens (assert: {lr['meta']['pour_preserves_order']}), and R(s) is computed on the flat stream, so the skeleton cannot remove long-range structure.  "
          f"R(s) with 10 shuffles (random.Random(707)); divcom own transcription = b3 port: {lr['meta']['divcom_own_equals_b3_port']}.", '',
          '| sequence | tokens | types | peak log2 s | peak R | ' + ' | '.join(str(s) for s in SCALES) + ' |', '|---|---|---|---|---|' + '---|' * len(SCALES)]
    for n, d in lr['curves'].items():
        L.append(f"| {n} | {d['tokens']} | {d['types']} | {d['peak_log2s']:.0f} | {d['peak_R']:.4f} | " + ' | '.join(f3(d['curve'].get(str(s))) for s in SCALES) + ' |')
    mx = lr['meta']['pliny_then_dante']
    L += ['', f"Hybrid probe (first half Naibbe-Pliny ciphertext, second half Naibbe-Dante ciphertext, poured): JSD halves {mx['k_jsd_halves']:.4f} (real {I['voynich_ZL']['k_jsd_halves']:.4f}), "
          f"MZ peak R {mx['h_peak_R']:.4f} at 2^{mx['h_peak_log2s']:.0f}; subset matches {mx['matches_subset']}/20.", '']
    L += ['## 7. Method critique', ''] + CRITIQUE + ['', '## 8. Corrected wording for the b3 conclusion (section 5)', '', CORRECTED, '', '## 9. Checked / not checked', ''] + CHECKED
    open(os.path.join(OUT, 'v_b3.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')


CRITIQUE = [
    '1. **Reproducibility.**  The re-run reproduces every committed number except the 72 Italian values (36 items, full and short).  The Italian control '
    'reads a git-ignored file that vatican5/build_it_lm.py rebuilds from Nuntiaturberichte OCR; the September build and the one in this checkout differ '
    '(section 0), and neither is clean Italian (Latin passages, German editorial text, OCR debris; v->u, j->i, k->c, w->u, y->i, so its h0 and the '
    '"gallows" items are not comparable).  Italian drops from 14/12 to 9/8.  Freeze a corpus file under data/ with a checksum or drop the row.',
    '2. **"Pre-registered" is not supported by the record.**  The battery and rule sit in BATTERY_TEXT inside b3_bakeoff.py; the docstring and section 6 '
    'say they were fixed before any score was computed.  The script, b3.json and b3.md first appear together in commit f1a99b941 (16 Sept, "Commit all '
    'pending working files"), and the hard-coded CONCLUSION, which quotes the scores, is in the same file.  NOTES.md section 7 (commit f602841aa, '
    '15 Sept) called for a pre-registered bake-off one day earlier, but with a different list (illustration-by-scribe co-clustering, A/B separability, '
    'the f and p rules), none of which is in b3.  The items were also chosen after a1-a6 had shown, on the same transcription, where Voynichese is '
    'extreme.  Accurate wording: "battery and match rule written into the script before the scores were tabulated (self-reported, no external timestamp)".',
    '3. **The tolerance rule.**  (a) The 10 % band ignores sampling noise.  A 20-block page jackknife puts tol below two standard errors on adj exact '
    '(tol/SE 0.88), adj LD<=1 (1.9), sc cover (1.9), sc <=10 (1.7), sc <=10 shuf (1.6), MZ peak R (0.92), tok pred (1.2), JSD halves (0.37) and MZ peak '
    'position (0.40).  That covers all six subset items b3 lists as failed by every non-Voynich corpus at full length (adj exact, adj LD<=1, sc <=10, '
    'MZ peak R, tok pred, JSD halves), so a text from the same process as Voynichese would often fail them too.  The candidates still miss them by many standard errors (Naibbe adj exact -7.0, adj LD<=1 -12.5, sc <=10 -7.2, MZ peak R -8.8 combined SE; '
    'Latin -8.5 to -18.6).  A noise-aware rule (max(tol, 2 x combined SE)) moves only a few marks: Naibbe 7 -> 9 of 20 (TTR, tok pred), autocopist 3 -> 4, '
    'Latin 2 -> 2.  The ranking holds.  (b) Some items are generous: hapax/types tol/SE 8.8, h2/h3 4.4-5.9, sc ratio 5.9.  On gallows mid and JSD '
    'odd/even the autocopist seed spread makes tol at least the real value, so anything between 0 and about twice the real value matches.  (c) The '
    'spread term, one generator\'s seed-to-seed difference, sets the tolerance on 8 of 37 items for every candidate.  (d) Correlated items count '
    'separately: six entropy items, five self-citation items.  Weighting each of 10 families equally gives Naibbe 4.3/10, Rugg-sorted 3.6 and the rest '
    '2.0-2.4 (full length).  The order is unchanged, but Naibbe\'s 17/37 includes all six entropy items.  (e) Some marks sit on a knife edge: '
    'autocopist_s7 short h2 mrg passes in b3 (|diff| 0.247 vs tol 0.249) and fails under this script\'s estimator (0.250 vs 0.248); the two h2 '
    'estimators differ by 0.002 bits.  (f) The MZ peak position is noise: jackknife SE 2.5 octaves, and the ZL peak moves from 2^10 with 3 shuffles to '
    '2^9 with 20.  b3 notes this in section 6; the item should not be scored.',
    '4. **Two "all-fail" items measure the real text\'s composition.**  JSD halves and MZ peak R on ZL are inflated by the A+B mixture (the first half '
    'of the pages is mostly A, the second mostly B).  The Currier A pages and the Currier B pages each fail both items under the same rule (b3\'s own '
    'reference rows).  No generator was given two regimes, so every one fails these items by construction.  That says nothing new about any family '
    'beyond "single regime".',
    '5. **Gibberish.**  The full battery cycles 10,075 tokens four times, so hapax and one-page types are 0 by construction; b3 says so.  The short battery is '
    'the same size, but it pools 38 writers and pours them across ZL pages, so pages straddle writers.  At equal size per writer (each file against 40 '
    'Voynich runs of the same token count), h2 is 3.07 vs 1.92 (0/38 files inside the Voynich 5-95 % band) and positional lock 0.32 vs 0.68 (1/38 files '
    'inside).  The exclusion stands.  The writer changes do create drift: gibberish short JSD halves 0.066 and MZ R 0.59 are above the real short '
    'values (0.040, 0.150), so a multi-writer text fails these items by having too much drift.  Minor: 9 hyphenated line breaks split into two tokens; '
    '164 accented letters stripped.  The short reference (first 10,053 ZL tokens) is herbal f1r-f58v, about 73 % Currier A and 27 % B, not "almost '
    'entirely A".  Using every third page of the whole manuscript instead moves subset scores by at most 2 (Latin 2 -> 1, Naibbe 7 -> 8, autocopist '
    '4 -> 3 / 4 -> 2, gibberish 2 -> 3).',
    '6. **The Naibbe port is faithful.**  An independent line-by-line transcription of naibbe.py (v1) reproduces b3.Naibbe token for token (34,625 '
    'tokens, 1,353 retries; Dante also identical).  The shipped ciphertext decrypts exactly to the shipped plaintext (1,063/1,063 lines), and no bigram '
    'token equals a unigram glyph, so UNAMBIGUOUS was on.  The unigram table shares fit the 52-card deck (chi2 1.8, against 184 for 78 cards).  The '
    'per-line variance of alpha cards among the first 40 (2.80) matches a deck reshuffled at every line (port 2.70; one-running-deck control 4.46).  '
    'So the shipped file was made with naibbe.py\'s v1 configuration, not v2\'s 78-card default, which closes b3\'s "not checked" item.  On the battery the '
    'port matches the shipped file at b3\'s resolution: identical marks on all 37 items (17 full, 17 short).  Only adj Jaccard xs differs by more than '
    'tol (0.0061 vs 0.0108; both fail).  Against 10 seeds the shipped file lies just outside the seed range on Zipf (-0.921 vs -0.917 to -0.900) and '
    'sc <=10 (0.152 vs 0.145 to 0.149).  Both gaps are under a fifth of tol; the cause was not identified.',
    '7. **The missing long-range structure in Naibbe comes from the cipher, not the skeleton.**  Pouring never reorders tokens, and R(s) runs on the flat '
    'stream: naibbe_pliny and naibbe_pliny_lines have the same R.  The plaintext carries topic structure: Pliny NH 16 words R 0.100 at 8,998 words, '
    'against 0.056 for the Latin control and 0.143 for Voynich at the same count.  The decrypted 1-2-letter units the cipher actually encodes keep '
    '0.020, and the ciphertext 0.004 (Dante: 0.056 -> 0.025 -> 0.004).  Respacing into letter units removes most of the word-level signal, and the '
    'homophonic table draws remove the rest.  Hybrid probe: Naibbe-Pliny ciphertext followed by Naibbe-Dante ciphertext, a Latin-to-Italian switch in '
    'the plaintext, gives JSD halves 0.0033 (real 0.063) and MZ R 0.028.  With fixed tables Naibbe flattens even a change of language, so b3\'s open '
    'hybrid ("a Naibbe-like encoding of a text with real topic structure") would not supply the A/B drift unless the tables or the respacing themselves '
    'changed between A and B.  Naibbe also has no line mechanism, so "no line-initial gallows preference" follows from its specification; keeping the '
    'shipped line breaks gives 0.033.',
    '8. **Some items depend on the alphabet.**  The gallows items (k, t, p, f) and the merged-glyph items (ch, sh, in, ee) are defined on EVA.  On Latin, '
    'English, Italian and the gibberish they count ordinary letters: Latin "gallows init" 0.199 matches Voynich 0.223 by accident, and the Italian build '
    'has no k at all.  Matches and fails on these items carry no meaning for non-EVA corpora.',
    '9. **Shuffle noise is small.**  The sc ratio from one shuffle and from 20 shuffles: ZL 1.130 vs 1.124 +- 0.005, autocopist 1.196 vs 1.193 +- 0.009, '
    'Naibbe 0.977 vs 0.984 +- 0.009.  The MZ peak R from 3 and from 20 shuffles agrees within 0.003 bits.  b3\'s single shuffle is adequate.',
]
CORRECTED = (
    'Under a rule that the real text\'s own Currier-B pages fail on 18 of 37 items (short battery), no generator or control comes close to Voynichese.  '
    'The three Naibbe ciphertexts score best (17/37 at full length, 16-17 short; 4.3 of 10 item families).  Rugg-sorted is next at full length (14; 13 '
    'short, where autocopist_s7 reaches 14).  The autocopist, Rugg grille, Latin, English and human gibberish trail at 8-10 (autocopist_s7 short: 14).  '
    'The Italian control is not reproducible: its git-ignored OCR corpus was rebuilt, giving 14/12 in September and 9/8 today.  It is left out of the '
    'ranking.  The counts are a ranking under a deliberately narrow rule, not pass/fail verdicts.  On adjacency, self-citation, MZ peak height, token '
    'predictability and half-to-half drift the 10 % tolerance is narrower than twice the real text\'s own sampling error.  The candidates miss those '
    'items by many standard errors, though, so the ranking survives a noise-aware rule.  Every non-Voynich corpus fails the adjacent-repeat rates (exact '
    'and LD<=1), self-citation within 10 tokens, the MZ peak height and (full length) the first-half/second-half glyph-bigram divergence (JSD halves '
    '0.063 bits; language controls 0.003-0.007, autocopist 0.02, Rugg 0.003-0.01, Naibbe 0.002).  The last two are also failed by the Currier A and B '
    'pages on their own.  They measure the A+B mixture of the real text, which no generator was given.  By family: '
    'natural language is excluded by the conditional character entropies (h2 1.1-1.3 bits and h3 0.7-1.0 bits too high), positional lock (0.26-0.35 vs '
    '0.64) and character 3-gram cross-entropy.  The autocopist reproduces the self-citation ratio and the MZ peak position but fails the Zipf slope '
    '(-0.83 to -0.86 vs -1.04).  It is excluded by vocabulary growth (TTR 0.34-0.38 vs 0.21, hapax/tokens, Heaps 0.85-0.88 vs 0.74), a 0.4-0.6-bit '
    'excess in glyph entropy, gallows in line-interior position (0.26-0.37 vs 0.065), near-zero token predictability, and a long-range peak that '
    'overshoots (0.47 vs 0.29 bits).  The Rugg grille is excluded by an almost hapax-free vocabulary that changes wholesale every four pages '
    '(hapax/types 0.06, MZ peak R 2.0 bits); the sorted variant by 9 % exact adjacent repeats.  The Naibbe cipher matches the character entropies, '
    'mean word length, positional lock and character predictability to within tolerance but misses the Zipf slope (-0.89 to -0.92 vs -1.04).  It is '
    'excluded by the absence of long-range structure (|R(s)| <= 0.009 bits at every scale, vs 0.29 for the real text and 0.08-0.16 for Latin and '
    'English).  That is a property of the cipher, which cuts the plaintext into one- and two-letter units (Pliny plaintext 0.10 -> letter units 0.02 '
    '-> ciphertext 0.004), not of the page skeleton.  It is further excluded by too few hapaxes, weak self-citation (ratio 0.96-0.98 vs 1.13) and no '
    'line-initial gallows preference (it has no line mechanism).  Human gibberish is excluded by character entropy (h2 3.9 bits pooled; 3.1 per '
    'writer against 1.9 for Voynich runs of the same length) and the absence of slot grammar (positional lock 0.14 pooled; 0.32 per writer against '
    '0.68).  No single family therefore remains compatible as written.  The glyph-level items favour a verbose-cipher-like encoding (Naibbe).  The '
    'self-citation ratio favours a copy-and-modify process, though the autocopist overshoots the absolute self-citation and long-range levels.  The '
    'drift items demand a regime change between A and B that none of the generators was built to have.  A Naibbe encoding of a topically structured or '
    'bilingual plaintext under fixed tables does not supply that change (Pliny-then-Dante ciphertext: JSD halves 0.003, MZ R 0.03); a cipher account '
    'would need the tables or the respacing themselves to change between A and B.  The bake-off does not exclude such hybrids, nor an autocopist with a '
    'tighter glyph grammar and a drifting source, and it says nothing about meaning.  (Title and section 0: replace "pre-registered" with "fixed '
    'battery, written into the script before the scores were tabulated".)')
CHECKED = [
    '- Checked: b3_bakeoff.py re-run as-is on 11 Oct 2026 with today\'s 38 Gutenberg files, the Naibbe repo at f2675ec and the 38 Gaskell & Bowern '
    'files.  Every committed value is identical except Italian, and the cause is identified (section 0).  results/b3.json and b3.md in the working '
    'tree now hold the re-run (only the Italian rows differ); `git checkout -- results/b3.json results/b3.md` restores the committed version.',
    '- Checked: 20 of the 37 items recomputed with independent code (own TSV loader, conditional entropy, glyph merge, LD<=1 test, self-citation, '
    'positional lock, MZ R(s), predictability, JSD) on voynich_ZL, latin, naibbe_pliny, autocopist_s19, autocopist_s7 and gaskell_gibberish, full and '
    'short.  Maximum relative difference from b3 is 0.2 %.  The causes are b3\'s h2, which drops each page\'s last bigram, and its 3-gram model, whose '
    'context count includes unfollowed bigrams.  One mark differs (autocopist_s7 short h2 mrg, on the boundary).',
    '- Checked: the own LD<=1 test against a DP Levenshtein on 40,010 pairs (0 disagreements); the seed-1 within-page shuffle and b3\'s three MZ '
    'shuffles replicated exactly; 20-shuffle noise for both.',
    '- Checked: the match rule re-implemented; 20-block jackknife SE for ZL, Latin, Naibbe-Pliny and autocopist_s19; a noise-aware re-score; a '
    'family-weighted re-count of b3\'s 37 marks.',
    '- Checked: gibberish per writer at equal size against Voynich runs of the same length; a whole-manuscript short reference.',
    '- Checked: the Naibbe port against an independent transcription of naibbe.py (identical); the shipped ciphertext decrypted against the shipped '
    'plaintext (exact); the deck (52 cards, reshuffled per line); 10 port seeds and 3 78-card runs on the subset; port vs shipped on all 37 items '
    '(b3.battery used as the instrument).',
    '- Checked: Naibbe long range on plaintext words, decrypted units and ciphertext; that pouring preserves token order; a Pliny-then-Dante hybrid.',
    '- Checked: every sentence of b3 section 5 against the committed and re-run numbers (section 1 table).',
    '- Not checked: the other 17 items (h0, h1, the length items, Heaps, sc prev2, irrev bigr, the line-position items, types on one page, adj '
    'Jaccard xs, JSD odd/even) were not recomputed independently.  Their values only reproduce on re-run.',
    '- Not checked: English, the two Rugg generators, the voynich_A / voynich_B rows and naibbe_pliny_lines were not recomputed (re-run only).  The '
    'autocopist\'s fidelity to Timm\'s Java code is a4\'s caveat (v_a4).',
    '- Not checked: which corpus_it.txt build the September run used.  The file is git-ignored; only its first words survive, in v_a4.md.',
    '- Not checked: why the shipped Naibbe file sits just outside the 10-seed range on Zipf and sc <=10.  The structure is identical; the gaps are '
    'under a fifth of tol.',
    '- Not checked: completeness of the 38 Gaskell & Bowern files against the paper (10,075 tokens here, about 10,053 reported).',
    '- User must verify: the corrected wording before anything reaches NOTES.md or docs/ (neither edited here).',
]

if __name__ == '__main__':
    if '--md-only' in sys.argv:
        R = json.load(open(os.path.join(OUT, 'v_b3.json'), encoding='utf-8'))
    else:
        R = main()
        R = json.loads(json.dumps(R, default=str))
    write_md(R)
    log('md written')
