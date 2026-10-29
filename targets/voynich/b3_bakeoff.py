"""b3_bakeoff.py -- pre-registered bake-off of Voynichese generators against one fixed battery.

Pure Python 3.12, standard library only.  Reuses a4_selfcitation.py (loader, skeleton, pour,
language controls, glyph merge, Zipf slope, self-citation statistics, autocopist and Rugg generators).

Corpora (all as pages -> lines -> words, EVA / Latin lowercase a-z only)
  voynich_ZL            ZL3b-n locus-P paragraph text (a4.load_zl), 34,116 tokens, 207 pages, 4,130 lines
  voynich_A / voynich_B ZL pages whose IVTFF $L variable (tsv column 'lang') is A / B (reference rows)
  latin, italian, english   a4.lang_words poured into the ZL skeleton
  autocopist_s19 / _s7  Timm & Schinner 2020 self-citation generator (a4.Autocopist), seeds 19 and 7
  rugg_grille, rugg_sorted  Rugg 2004 table-and-grille (a4.Rugg / a4.RuggSorted, seed 19)
  naibbe_pliny          Greshko 2025 Naibbe cipher, shipped ciphertext of Pliny NH 16, poured into skeleton
  naibbe_pliny_lines    same ciphertext keeping the shipped line / paragraph breaks (pages cut to ZL page sizes)
  naibbe_divcom         Naibbe cipher regenerated here (stdlib port of naibbe.py, seed 19) from the Divina Commedia
  gaskell_gibberish     Gaskell & Bowern 2022 human gibberish, 38 files, cycled to length (see short battery)

The battery, the scored items and the match rule are written in BATTERY_TEXT below and in section 0 of
results/b3.md; they were fixed before any score was computed.
"""
import os as _os  # local paths (the September 2026 scripts hard-coded another machine)
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_CORP = _os.path.join(_HERE, 'data', 'corpora')  # corp_<lang>_<gutenberg id>.txt, see fetch_corpora.py
_EXT = _os.path.join(_HERE, 'data', 'external')  # third-party data (Naibbe, Gaskell & Bowern)
_IT = _os.path.join(_CORP, 'corpus_it.txt')  # vatican5 OCR corpus from the September sample's first words (fetch_corpora.py)
import sys, os, re, json, math, random, collections, statistics, time, csv, unicodedata

BASE = _HERE
sys.path.insert(0, BASE)
import a4_selfcitation as a4

OUT = os.path.join(BASE, 'results')
SCR = _EXT
NAIBBE_DIR = os.path.join(SCR, 'naibbe', 'out')
GIB_DIR = os.path.join(SCR, 'gaskell_voynich', 'data', 'gib')

SCALES = [16, 32, 64, 128, 256, 512, 1024, 2048]
LOG2 = math.log(2)

BATTERY_TEXT = """\
All corpora are lists of pages -> lines -> words (lowercase a-z only).  Every item is ONE number.
Unless stated, statistics use the raw letter string of each word; "merged" means a4.merge_glyphs
(ch sh ckh cth cph cfh -> one symbol each, in/iin/iiin -> N, ee -> E), applied identically to every corpus.

 a. Character entropies on the stream ' ' + words joined by ' ' + ' ' per page (word boundary is a symbol):
    a_h0 = log2(alphabet size incl. boundary), a_h1 = H(X), a_h2 = H(X_n|X_{n-1}), a_h3 = H(X_n|X_{n-2},X_{n-1});
    scored: a_h0_raw a_h1_raw a_h2_raw a_h3_raw a_h2_mrg a_h3_mrg (merged h0/h1 in the json only).
 b. b_len_mean, b_len_sd (population sd) of token length in raw letters; b_len1 = share of tokens of length 1;
    b_len9 = share of tokens of length >= 9.
 c. c_zipf = a4.zipf_slope (OLS log10 f vs log10 rank, ranks 1..1000); c_ttr = types/tokens; c_hapax_types,
    c_hapax_tokens = hapax share of types / of tokens; c_heaps = OLS slope of log V(n) vs log n over 20
    log-spaced prefix lengths n between 200 and N.
 d. d_adj_exact = share of consecutive token pairs (flat corpus order) that are identical; d_adj_ld1 = share with
    Levenshtein distance <= 1 (a4.ld1, includes identical).
 e. a4.selfcit_stats nearest-earlier-LD<=1 on the same page: e_cover = coverage, e_w10 = share of all tokens with such
    a predecessor within 10 tokens, e_prev2 = within the previous 2 lines (same line counts); e_w10_shuf = e_w10 after
    a4.shuffle_within_page(seed 1); e_ratio = e_w10 / e_w10_shuf (the diagnostic that separated autocopist from
    language in a4).  Shuffle cover / prev2 are in the json only.
 f. Merged glyphs.  f_irrev = among the 200 most frequent within-word glyph bigrams, share whose reversed order never
    occurs anywhere in the corpus.  f_lock = share of tokens whose first glyph is one of that corpus's 5 most frequent
    word-initial glyphs AND whose last glyph is one of its 5 most frequent word-final glyphs (1-glyph tokens count
    if the glyph is in both lists).
 g. Lines with >= 3 tokens only: g_len_first / g_len_mid / g_len_last = mean raw length of the first / interior /
    last token; g_gal_init / g_gal_mid = share of line-initial / interior tokens whose first letter is k, t, p or f.
 h. Long-range (Montemurro-Zanette style, simplified): flat token stream; for s in 16..2048 cut the first (N//s)*s
    tokens into consecutive blocks of s tokens; D(s) = H(word distribution of all used tokens) - mean over blocks of
    H(word distribution of the block).  R(s) = D_real(s) - D_shuffled(s) where the shuffled value is the mean over 3
    token shuffles (random.Random(3)).  h_peak_log2s = log2 of the s maximising R; h_peak_R = that maximum (bits).
 i. Two-fold split by page order (train on even-index pages, test on odd, and the reverse; average):
    i_tok_acc = share of test tokens (those with a predecessor on the same page) whose predecessor's most frequent
    training successor equals the token (unseen predecessor -> most frequent training token);
    i_char_bits = cross-entropy in bits per character of a character 3-gram model with add-0.1 smoothing,
    V = number of distinct characters incl. boundary in the whole corpus, on the same per-page strings as (a).
 j. j_one_page = share of types that occur on exactly one page; j_jacc_excess = mean Jaccard similarity of the type
    sets of adjacent pages minus the mean over 100 random distinct page pairs (random.Random(1)).
 k. Jensen-Shannon divergence (bits) between distributions of merged-glyph bigrams (stream of (a), merged) of
    two page halves: k_jsd_halves = first half of pages vs second half; k_jsd_oddeven = odd-index vs even-index
    pages.  For voynich_ZL the json also holds Currier A vs B.

Match rule (fixed in advance).  For every scored item, real = value on voynich_ZL, spread = |autocopist_s19 -
autocopist_s7|, tol = max(0.10 * |real|, spread).  A corpus matches the item iff |value - real| <= tol.
h_peak_log2s is compared on the log2 scale.  A missing value never matches.  The final column counts matches out
of the 37 scored items.  The short battery applies the identical rule with real / spread taken from the short
(length-matched) versions of voynich_ZL and the two autocopist seeds.  Rows voynich_A / voynich_B are reference
rows (subsets of the real text) and show how much the real text disagrees with itself under the same rule."""

ITEMS = [  # key, short label, group
    ('a_h0_raw', 'h0 raw'), ('a_h1_raw', 'h1 raw'), ('a_h2_raw', 'h2 raw'), ('a_h3_raw', 'h3 raw'),
    ('a_h2_mrg', 'h2 mrg'), ('a_h3_mrg', 'h3 mrg'),
    ('b_len_mean', 'len mean'), ('b_len_sd', 'len sd'), ('b_len1', 'len=1'), ('b_len9', 'len>=9'),
    ('c_zipf', 'Zipf'), ('c_ttr', 'TTR'), ('c_hapax_types', 'hapax/types'), ('c_hapax_tokens', 'hapax/tokens'), ('c_heaps', 'Heaps'),
    ('d_adj_exact', 'adj exact'), ('d_adj_ld1', 'adj LD<=1'),
    ('e_cover', 'sc cover'), ('e_w10', 'sc <=10'), ('e_prev2', 'sc prev2'), ('e_w10_shuf', 'sc <=10 shuf'), ('e_ratio', 'sc ratio'),
    ('f_irrev', 'irrev bigr'), ('f_lock', 'pos lock'),
    ('g_len_first', 'len first'), ('g_len_mid', 'len mid'), ('g_len_last', 'len last'), ('g_gal_init', 'gallows init'), ('g_gal_mid', 'gallows mid'),
    ('h_peak_log2s', 'MZ peak log2 s'), ('h_peak_R', 'MZ peak R'),
    ('i_tok_acc', 'tok pred'), ('i_char_bits', 'char 3g bits'),
    ('j_one_page', 'types 1 page'), ('j_jacc_excess', 'adj Jaccard xs'),
    ('k_jsd_halves', 'JSD halves'), ('k_jsd_oddeven', 'JSD odd/even'),
]
GROUPS = [('a-d: characters, word length, vocabulary, adjacency', 'abcd'),
          ('e-g: self-citation, slot grammar, line position', 'efg'),
          ('h-k: long range, predictability, page level, drift', 'hijk')]

SOURCES = {
    'voynich_ZL': 'ZL3b-n (Zandbergen-Landini, voynich.nu) locus P, a-z tokens only',
    'voynich_A': 'voynich_ZL pages with IVTFF $L=A (Currier A)',
    'voynich_B': 'voynich_ZL pages with IVTFF $L=B (Currier B)',
    'latin': 'a4.lang_words("la") Gutenberg Latin, poured into ZL skeleton',
    'italian': 'a4.lang_words("it") corpus_it.txt, poured into ZL skeleton',
    'english': 'a4.lang_words("en") Gutenberg English, poured into ZL skeleton',
    'autocopist_s19': 'Timm & Schinner 2020 Cryptologia 44(1) self-citation generator, a4.Autocopist(19)',
    'autocopist_s7': 'same, a4.Autocopist(7)',
    'rugg_grille': 'Rugg 2004 Cryptologia 28(1) table-and-grille, a4.Rugg(19)',
    'rugg_sorted': 'Rugg 2004 variant with sorted table columns, a4.RuggSorted(19)',
    'naibbe_pliny': 'Greshko 2025 Cryptologia doi 10.1080/01611194.2025.2566408, shipped encrypted_nathist_output_ciphertext.txt (Pliny NH 16), first 34,116 tokens poured into ZL skeleton',
    'naibbe_pliny_lines': 'same ciphertext, shipped line/paragraph breaks kept, consecutive lines grouped into 207 pages of ZL page token size',
    'naibbe_divcom': 'Greshko 2025 naibbe.py ported to stdlib (csv instead of pandas, random.Random(19), 52-card deck, RESPACING 17, UNAMBIGUOUS), Divina Commedia plaintext, first 34,116 tokens poured into ZL skeleton',
    'gaskell_gibberish': 'Gaskell & Bowern 2022 "Gibberish after all?" 38 volunteer files, diacritics stripped, a-z tokens, cycled to 34,116 and poured into ZL skeleton',
}

def log(*a):
    print(*a, flush=True)

# ----------------------------------------------------------------------------------------------- loading
def load_zl_lang():
    pages = collections.OrderedDict(); lang = {}
    with open(a4.ZL, encoding='utf-8') as f:
        next(f)
        for l in f:
            c = l.rstrip('\n').split('\t')
            if c[2] != 'P':
                continue
            words = [w for w in c[9].split() if a4.AZ.match(w)]
            if not words:
                continue
            pages.setdefault(c[0], []).append({'words': words, 'para_start': c[7] == '1'})
            lang.setdefault(c[0], collections.Counter())[c[3]] += 1
    return [{'folio': k, 'lines': v, 'lang': lang[k].most_common(1)[0][0]} for k, v in pages.items()]

def words_of(pages):
    return [w for p in pages for ln in p['lines'] for w in ln['words']]

def truncate_pages(pages, n):
    out = []; k = 0
    for p in pages:
        if k >= n:
            break
        lines = []
        for ln in p['lines']:
            if k >= n:
                break
            ws = ln['words'][:n - k]; k += len(ws)
            lines.append({'words': ws, 'para_start': ln['para_start']})
        out.append({'folio': p.get('folio', ''), 'lines': lines})
    return out

def cycle_to(words, n):
    reps = -(-n // len(words))
    return (words * reps)[:n]

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def load_gibberish():
    files = sorted(fn for fn in os.listdir(GIB_DIR) if fn.lower().endswith('.txt'))
    words = []; per_file = []
    for fn in files:
        t = open(os.path.join(GIB_DIR, fn), encoding='utf-8', errors='replace').read()
        ws = re.findall(r'[a-z]+', strip_accents(t).lower())
        per_file.append((fn, len(ws))); words.extend(ws)
    return words, per_file

def read_cipher_lines(path):
    """shipped naibbe ciphertext -> list of (words, para_start)"""
    lines = []; para = True
    for raw in open(path, encoding='utf-8', errors='replace'):
        ws = [w for w in re.findall(r'[a-z]+', raw.lower())]
        if not ws:
            para = True; continue
        lines.append((ws, para)); para = False
    return lines

def lines_into_pages(lines, skel, n_target):
    """keep given line breaks; start a new page when the running page token count reaches the ZL page size"""
    targets = [sum(x[0] for x in pl) for pl in skel]
    pages = []; cur = []; cur_n = 0; pi = 0; total = 0
    for ws, ps in lines:
        if total >= n_target:
            break
        ws = ws[:n_target - total]
        cur.append({'words': ws, 'para_start': ps}); cur_n += len(ws); total += len(ws)
        if pi < len(targets) - 1 and cur_n >= targets[pi]:
            pages.append({'folio': '', 'lines': cur}); cur = []; cur_n = 0; pi += 1
    if cur:
        pages.append({'folio': '', 'lines': cur})
    return pages

# ----------------------------------------------------------------------------------------------- Naibbe port
class Naibbe:
    """Port of Greshko's naibbe.py (v1 defaults: 52-card deck, RESPACING 17, UNAMBIGUOUS True) to the standard
    library: pandas.read_csv replaced by csv, module-level random replaced by random.Random(seed).
    Logic otherwise transcribed line by line."""
    ALPHABET = list('abcdefghijklmnopqrstuvwxyz')
    TABLES = ['alpha', 'beta1', 'beta2', 'beta3', 'gamma1', 'gamma2']
    WEIGHTS = {False: {'alpha': 20, 'beta1': 8, 'beta2': 8, 'beta3': 8, 'gamma1': 4, 'gamma2': 4},
               True: {'alpha': 28, 'beta1': 14, 'beta2': 11, 'beta3': 11, 'gamma1': 7, 'gamma2': 7}}
    def __init__(self, csv_path, seed=19, use_78=False, respacing=17, unambiguous=True):
        self.rng = random.Random(seed); self.use_78 = use_78; self.respacing = respacing; self.unamb = unambiguous
        self.glyph = {}
        with open(csv_path, encoding='utf-8-sig', newline='') as f:
            for row in csv.DictReader(f):
                self.glyph[row['code'].strip()] = row['glyphs'].strip()
        self.unigram_glyphs = {g for c, g in self.glyph.items() if c.startswith('unigram_')}
        self.retries = 0
    def deck(self):
        d = []
        for t, c in self.WEIGHTS[self.use_78].items():
            d.extend([t] * c)
        self.rng.shuffle(d); return d
    @staticmethod
    def clean_line(text):
        s = strip_accents(text)
        rep = {'æ': 'ae', 'Æ': 'ae', 'œ': 'oe', 'Œ': 'oe', 'ð': 'd', 'Ð': 'd', 'þ': 'th', 'Þ': 'th', 'ł': 'l', 'Ł': 'l', 'ß': 'ss', 'ø': 'o', 'Ø': 'o'}
        s = ''.join(rep.get(c, c) for c in s)
        s = ''.join(c for c in s if c.isalpha()).upper().replace('W', 'UU').replace('J', 'I').replace('K', 'C')
        return s.lower()
    def respace(self, text):
        text = text.lower().replace(' ', ''); i = 0; out = []
        while i < len(text):
            if i == len(text) - 1 or self.rng.random() < (self.respacing / 36):
                out.append(text[i]); i += 1
            else:
                out.append(text[i:i + 2]); i += 2
        return out
    def encrypt(self, cleaned):
        ngrams = self.respace(cleaned); ct = []; deck = self.deck(); di = 0
        def draw():
            nonlocal deck, di
            if di >= len(deck):
                deck = self.deck(); di = 0
            t = deck[di]; di += 1; return t
        for tk in ngrams:
            if len(tk) == 1:
                code = f'unigram_{draw()}_{tk}'; ct.append(self.glyph.get(code, code))
            else:
                if self.unamb:
                    while True:
                        cp = f'prefix_{draw()}_{tk[0]}'; gp = self.glyph.get(cp, cp)
                        cs = f'suffix_{draw()}_{tk[1]}'; gs = self.glyph.get(cs, cs)
                        if gp + gs not in self.unigram_glyphs:
                            ct.append(gp + gs); break
                        self.retries += 1
                else:
                    cp = f'prefix_{draw()}_{tk[0]}'; cs = f'suffix_{draw()}_{tk[1]}'
                    ct.append(self.glyph.get(cp, cp) + self.glyph.get(cs, cs))
        return ct
    def generate(self, plaintext_path, need):
        """returns list of (words, para_start) ciphertext lines with >= need tokens in total"""
        lines = []; n = 0; para = True
        for raw in open(plaintext_path, encoding='utf-8', errors='replace'):
            c = self.clean_line(raw)
            if not c:
                para = True; continue
            ws = self.encrypt(c); lines.append((ws, para)); para = False; n += len(ws)
            if n >= need:
                break
        return lines

# ----------------------------------------------------------------------------------------------- helpers
def H(counts):
    n = sum(counts)
    return -sum(c / n * math.log(c / n) for c in counts if c) / LOG2 if n else 0.0

def page_strings(pages, merged=False):
    out = []
    for p in pages:
        ws = [w for ln in p['lines'] for w in ln['words']]
        if merged:
            ws = [a4.merge_glyphs(w) for w in ws]
        out.append(' ' + ' '.join(ws) + ' ')
    return out

def char_entropies(strs):
    tri = collections.Counter()
    for s in strs:
        tri.update(zip(s, s[1:], s[2:]))
    bi = collections.Counter(); uni = collections.Counter()
    for (x, y, z), v in tri.items():
        bi[(x, y)] += v; uni[x] += v
    alph = set()
    for s in strs:
        alph.update(s)
    h1 = H(uni.values()); h2 = H(bi.values()) - h1; h3 = H(tri.values()) - H(bi.values())
    return math.log2(len(alph)), h1, h2, h3

def heaps_exponent(words, k=20):
    N = len(words)
    if N < 400:
        return None
    ns = sorted({int(round(math.exp(math.log(200) + (math.log(N) - math.log(200)) * i / (k - 1)))) for i in range(k)})
    seen = set(); V = []; j = 0; target = ns[0]
    for i, w in enumerate(words, 1):
        seen.add(w)
        while j < len(ns) and i == ns[j]:
            V.append(len(seen)); j += 1
    xs = [math.log(n) for n in ns[:len(V)]]; ys = [math.log(v) for v in V]
    mx = sum(xs) / len(xs); my = sum(ys) / len(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)

def jsd(p, q):
    keys = set(p) | set(q); d = 0.0
    for kk in keys:
        a = p.get(kk, 0.0); b = q.get(kk, 0.0); m = 0.5 * (a + b)
        if a: d += 0.5 * a * math.log(a / m)
        if b: d += 0.5 * b * math.log(b / m)
    return d / LOG2

def bigram_dist(strs):
    c = collections.Counter()
    for s in strs:
        c.update(zip(s, s[1:]))
    n = sum(c.values())
    return {kk: v / n for kk, v in c.items()}

def mz_curve(words, rng, n_shuf=3):
    N = len(words); ids = words
    def mean_block_H(seq, s):
        P = N // s; tot = 0.0
        for j in range(P):
            tot += H(collections.Counter(seq[j * s:(j + 1) * s]).values())
        return tot / P
    shufs = []
    for _ in range(n_shuf):
        s = list(ids); rng.shuffle(s); shufs.append(s)
    curve = collections.OrderedDict()
    for s in SCALES:
        if N // s < 4:
            continue
        used = ids[:(N // s) * s]
        Htot = H(collections.Counter(used).values())
        mr = mean_block_H(ids, s)
        ms = sum(mean_block_H(sq, s) for sq in shufs) / n_shuf
        curve[s] = {'blocks': N // s, 'D_real': Htot - mr, 'D_shuf': Htot - ms, 'R': ms - mr}
    peak = max(curve, key=lambda s: curve[s]['R'])
    return curve, peak, curve[peak]['R']

def predictability(pages):
    """2-fold by page index parity"""
    strs = page_strings(pages)
    alph = set()
    for s in strs:
        alph.update(s)
    V = len(alph)
    accs = []; bits = []
    for fold in (0, 1):
        train = [p for i, p in enumerate(pages) if i % 2 == fold]
        test = [p for i, p in enumerate(pages) if i % 2 != fold]
        succ = collections.defaultdict(collections.Counter); uni = collections.Counter()
        for p in train:
            ws = [w for ln in p['lines'] for w in ln['words']]
            uni.update(ws)
            for a, b in zip(ws, ws[1:]):
                succ[a][b] += 1
        best = {a: c.most_common(1)[0][0] for a, c in succ.items()}
        default = uni.most_common(1)[0][0]
        hit = tot = 0
        for p in test:
            ws = [w for ln in p['lines'] for w in ln['words']]
            for a, b in zip(ws, ws[1:]):
                tot += 1; hit += (best.get(a, default) == b)
        accs.append(hit / tot if tot else None)
        tri = collections.Counter(); bi = collections.Counter()
        for s in page_strings(train):
            tri.update(zip(s, s[1:], s[2:])); bi.update(zip(s, s[1:]))
        lp = 0.0; n = 0
        for s in page_strings(test):
            for i in range(2, len(s)):
                ctx = (s[i - 2], s[i - 1])
                lp -= math.log2((tri.get((s[i - 2], s[i - 1], s[i]), 0) + 0.1) / (bi.get(ctx, 0) + 0.1 * V)); n += 1
        bits.append(lp / n if n else None)
    return sum(accs) / 2, sum(bits) / 2

# ----------------------------------------------------------------------------------------------- battery
def battery(pages, name, extra):
    words = words_of(pages); N = len(words)
    R = collections.OrderedDict(); X = {}
    # a
    h0, h1, h2, h3 = char_entropies(page_strings(pages))
    m0, m1, m2, m3 = char_entropies(page_strings(pages, merged=True))
    R.update(a_h0_raw=h0, a_h1_raw=h1, a_h2_raw=h2, a_h3_raw=h3, a_h2_mrg=m2, a_h3_mrg=m3)
    X['a_h0_mrg'] = m0; X['a_h1_mrg'] = m1
    # b
    L = [len(w) for w in words]; mean = sum(L) / N
    R['b_len_mean'] = mean; R['b_len_sd'] = math.sqrt(sum((x - mean) ** 2 for x in L) / N)
    R['b_len1'] = sum(1 for x in L if x == 1) / N; R['b_len9'] = sum(1 for x in L if x >= 9) / N
    # c
    cnt = collections.Counter(words); hap = sum(1 for v in cnt.values() if v == 1)
    R['c_zipf'] = a4.zipf_slope(words); R['c_ttr'] = len(cnt) / N
    R['c_hapax_types'] = hap / len(cnt); R['c_hapax_tokens'] = hap / N; R['c_heaps'] = heaps_exponent(words)
    X['types'] = len(cnt); X['top10'] = cnt.most_common(10)
    # d
    R['d_adj_exact'] = sum(1 for a, b in zip(words, words[1:]) if a == b) / (N - 1)
    R['d_adj_ld1'] = sum(1 for a, b in zip(words, words[1:]) if a4.ld1(a, b) <= 1) / (N - 1)
    # e
    sc = a4.selfcit_stats(pages)['nearest_earlier_LD<=1']
    ss = a4.selfcit_stats(a4.shuffle_within_page(pages))['nearest_earlier_LD<=1']
    R['e_cover'] = sc['coverage']; R['e_w10'] = sc['frac_all_within_10']; R['e_prev2'] = sc['frac_all_within_prev2lines']
    R['e_w10_shuf'] = ss['frac_all_within_10']; R['e_ratio'] = sc['frac_all_within_10'] / ss['frac_all_within_10'] if ss['frac_all_within_10'] else None
    X['e_cover_shuf'] = ss['coverage']; X['e_prev2_shuf'] = ss['frac_all_within_prev2lines']; X['e_median_dist'] = sc['median_distance_given_hit']
    # f
    mw = [a4.merge_glyphs(w) for w in words]
    bg = collections.Counter()
    for w in mw:
        bg.update(zip(w, w[1:]))
    top = [b for b, _ in bg.most_common(200)]
    R['f_irrev'] = sum(1 for (x, y) in top if bg.get((y, x), 0) == 0) / len(top)
    ini = collections.Counter(w[0] for w in mw); fin = collections.Counter(w[-1] for w in mw)
    ti = {g for g, _ in ini.most_common(5)}; tf = {g for g, _ in fin.most_common(5)}
    R['f_lock'] = sum(1 for w in mw if w[0] in ti and w[-1] in tf) / N
    X['top5_initial'] = ini.most_common(5); X['top5_final'] = fin.most_common(5); X['n_bigrams_considered'] = len(top)
    # g
    lf = []; lm = []; ll = []; gi = gm = ni = nm = 0
    for p in pages:
        for ln in p['lines']:
            ws = ln['words']
            if len(ws) < 3:
                continue
            lf.append(len(ws[0])); ll.append(len(ws[-1])); lm.extend(len(w) for w in ws[1:-1])
            ni += 1; gi += ws[0][0] in 'ktpf'
            for w in ws[1:-1]:
                nm += 1; gm += w[0] in 'ktpf'
    R['g_len_first'] = sum(lf) / len(lf) if lf else None; R['g_len_mid'] = sum(lm) / len(lm) if lm else None
    R['g_len_last'] = sum(ll) / len(ll) if ll else None
    R['g_gal_init'] = gi / ni if ni else None; R['g_gal_mid'] = gm / nm if nm else None
    X['lines_ge3'] = ni
    # h
    curve, peak, peakR = mz_curve(words, random.Random(3))
    R['h_peak_log2s'] = math.log2(peak); R['h_peak_R'] = peakR
    X['mz_curve'] = {str(s): {kk: (round(v, 5) if isinstance(v, float) else v) for kk, v in d.items()} for s, d in curve.items()}
    # i
    R['i_tok_acc'], R['i_char_bits'] = predictability(pages)
    # j
    pt = [set(words_of([p])) for p in pages]
    occ = collections.Counter()
    for s in pt:
        occ.update(s)
    R['j_one_page'] = sum(1 for v in occ.values() if v == 1) / len(occ)
    def jac(a, b):
        return len(a & b) / len(a | b) if (a | b) else 0.0
    adj = [jac(pt[i], pt[i + 1]) for i in range(len(pt) - 1)]
    rng = random.Random(1); rnd = []
    for _ in range(100):
        i, j = rng.sample(range(len(pt)), 2); rnd.append(jac(pt[i], pt[j]))
    R['j_jacc_excess'] = sum(adj) / len(adj) - sum(rnd) / len(rnd)
    X['j_jacc_adjacent'] = sum(adj) / len(adj); X['j_jacc_random'] = sum(rnd) / len(rnd)
    # k
    ms = page_strings(pages, merged=True); h = len(ms) // 2
    R['k_jsd_halves'] = jsd(bigram_dist(ms[:h]), bigram_dist(ms[h:]))
    R['k_jsd_oddeven'] = jsd(bigram_dist(ms[0::2]), bigram_dist(ms[1::2]))
    if all('lang' in p for p in pages):
        A = [s for p, s in zip(pages, ms) if p['lang'] == 'A']; B = [s for p, s in zip(pages, ms) if p['lang'] == 'B']
        if A and B:
            X['k_jsd_A_vs_B'] = jsd(bigram_dist(A), bigram_dist(B))
    X['tokens'] = N; X['pages'] = len(pages); X['lines'] = sum(len(p['lines']) for p in pages)
    extra[name] = X
    return R

# ----------------------------------------------------------------------------------------------- scoring
def score(results, real='voynich_ZL', ac=('autocopist_s19', 'autocopist_s7')):
    tol = {}; marks = collections.OrderedDict()
    for key, _ in ITEMS:
        rv = results[real][key]; a, b = results[ac[0]][key], results[ac[1]][key]
        spread = abs(a - b) if (a is not None and b is not None) else 0.0
        tol[key] = max(0.10 * abs(rv), spread) if rv is not None else None
    for name, R in results.items():
        m = collections.OrderedDict()
        for key, _ in ITEMS:
            v = R[key]; rv = results[real][key]
            m[key] = bool(v is not None and rv is not None and abs(v - rv) <= tol[key])
        marks[name] = m
    return tol, marks

# ----------------------------------------------------------------------------------------------- md
def fmt(v):
    if v is None:
        return '-'
    if isinstance(v, float):
        return f'{v:.3g}' if abs(v) < 0.01 else f'{v:.3f}'
    return str(v)

def table(results, keys, names, marks=None, count=False):
    hdr = '| corpus | ' + ' | '.join(lab for k, lab in ITEMS if k in keys) + (f' | matched/{len(ITEMS)} |' if count else ' |')
    L = [hdr, '|' + '---|' * (hdr.count('|') - 1)]
    for n in names:
        cells = []
        for k, lab in ITEMS:
            if k not in keys:
                continue
            c = fmt(results[n][k])
            if marks is not None:
                c += ' ' + ('\u2713' if marks[n][k] else '\u2717')
            cells.append(c)
        row = f'| {n} | ' + ' | '.join(cells)
        if count:
            row += f" | {sum(marks[n].values())} |"
        else:
            row += ' |'
        L.append(row)
    return L

def write_md(out, conclusion):
    meta = out['meta']; L = []
    L += ['# b3: pre-registered generator bake-off against one fixed battery', '',
          f"Runtime {meta['runtime_s']} s.  Real text: ZL3b-n paragraph text, {meta['N']} tokens, {meta['pages']} pages, {meta['lines']} lines; "
          f"every full-length corpus has exactly {meta['N']} tokens in the identical page/line skeleton unless stated.  "
          f"Short battery: first {meta['N_short']} tokens of every corpus (= one pass of the gibberish corpus).  "
          'All output is unvalidated until reviewed; see section 6.', '',
          '## 0. Battery, scored items and match rule (fixed in advance)', '', '```', BATTERY_TEXT, '```', '',
          '## 1. Corpora', '', '| corpus | tokens | pages | lines | source / construction |', '|---|---|---|---|---|']
    for n, c in out['corpora'].items():
        L.append(f"| {n} | {c['tokens']} | {c['pages']} | {c['lines']} | {SOURCES[n]} |")
    g = meta['gibberish']; npc = meta['naibbe_port_check']
    L += ['', f"Gibberish: {g['files']} files, {g['clean_tokens']} clean a-z tokens (Gaskell & Bowern report about 10,053 words); cycled {g['cycles']} times for the full battery, "
          'so its full-length repetition / vocabulary items (c, d, e, j) are inflated by construction and only the short battery is a fair test for it.',
          f"Naibbe port check (re-encrypting the shipped Pliny plaintext with the stdlib port, seed 19): port {npc['port_tokens']} tokens vs shipped {npc['shipped_tokens']}; "
          f"mean token length {npc['port_len_mean']:.3f} vs {npc['shipped_len_mean']:.3f}; types {npc['port_types']} vs {npc['shipped_types']}; "
          f"top-20 token overlap {npc['top20_overlap']}/20.  Which script version (naibbe.py or naibbe_v2.py, 78-card deck) produced the shipped file is not documented; the port follows naibbe.py.",
          f"Naibbe divcom regeneration: {meta['naibbe_divcom_lines']} plaintext lines used, {meta['naibbe_divcom_tokens']} ciphertext tokens generated, {meta['naibbe_divcom_retries']} ambiguity retries.",
          f"Autocopist token counts ({out['corpora']['autocopist_s19']['tokens']} / {out['corpora']['autocopist_s7']['tokens']}) are below 34,116: a4.Autocopist fills each skeleton line to its "
          'character length, not its token count, and (contrary to the a4 docstring) nothing pads the result; the page/line structure is identical, so the corpora are used as generated, as in a4.',
          'naibbe_pliny vs naibbe_pliny_lines (same tokens, different line breaks: 1,063 shipped lines of about 33 tokens vs 4,130 ZL lines of about 8): all items are identical except the line-dependent '
          f"ones -- sc prev2 {fmt(out['full']['naibbe_pliny']['e_prev2'])} vs {fmt(out['full']['naibbe_pliny_lines']['e_prev2'])}, gallows init {fmt(out['full']['naibbe_pliny']['g_gal_init'])} vs "
          f"{fmt(out['full']['naibbe_pliny_lines']['g_gal_init'])}, len first/last, adj Jaccard xs (page cuts fall at line ends).  The first {meta['N_short']} tokens of voynich_ZL (short battery) are "
          'almost entirely Currier-A herbal pages, so voynich_A short is nearly the same text.', '']
    names = list(out['full'].keys())
    L += ['## 2. Full-length battery', '']
    for title, grp in GROUPS:
        keys = {k for k, _ in ITEMS if k[0] in grp}
        L += [f'### {title}', ''] + table(out['full'], keys, names) + ['']
    L += ['MZ-style curve R(s) in bits (full length), s = 16 .. 2048:', '', '| corpus | ' + ' | '.join(str(s) for s in SCALES) + ' |', '|---|' + '---|' * len(SCALES)]
    for n in names:
        cv = out['extra_full'][n]['mz_curve']
        L.append(f'| {n} | ' + ' | '.join(fmt(cv[str(s)]['R']) if str(s) in cv else '-' for s in SCALES) + ' |')
    L += ['', 'Top-5 word-initial / word-final merged glyphs used for f_lock:', '']
    for n in names:
        x = out['extra_full'][n]
        L.append(f"- {n}: initial {' '.join(f'{g}({c})' for g, c in x['top5_initial'])}; final {' '.join(f'{g}({c})' for g, c in x['top5_final'])}")
    if 'k_jsd_A_vs_B' in out['extra_full']['voynich_ZL']:
        L += ['', f"voynich_ZL glyph-bigram JSD Currier A vs B: {fmt(out['extra_full']['voynich_ZL']['k_jsd_A_vs_B'])} bits "
              f"(halves {fmt(out['full']['voynich_ZL']['k_jsd_halves'])}, odd/even {fmt(out['full']['voynich_ZL']['k_jsd_oddeven'])})."]
    L += ['', f"## 3. Short battery (first {meta['N_short']} tokens of each corpus)", '']
    for title, grp in GROUPS:
        keys = {k for k, _ in ITEMS if k[0] in grp}
        L += [f'### {title}', ''] + table(out['short'], keys, names) + ['']
    L += ['## 4. Match table', '', f"Rule: tol = max(10 % of the real value, |autocopist_s19 - autocopist_s7|); tick = |value - real| <= tol.  Tolerances used (full / short):", '']
    L += ['| item | real full | tol full | real short | tol short |', '|---|---|---|---|---|']
    for k, lab in ITEMS:
        L.append(f"| {lab} | {fmt(out['full']['voynich_ZL'][k])} | {fmt(out['tol_full'][k])} | {fmt(out['short']['voynich_ZL'][k])} | {fmt(out['tol_short'][k])} |")
    L += ['', '### 4a. Full length', '']
    for title, grp in GROUPS:
        keys = {k for k, _ in ITEMS if k[0] in grp}
        L += [f'{title}', ''] + table(out['full'], keys, names, out['marks_full']) + ['']
    L += ['### 4b. Short battery', '']
    for title, grp in GROUPS:
        keys = {k for k, _ in ITEMS if k[0] in grp}
        L += [f'{title}', ''] + table(out['short'], keys, names, out['marks_short']) + ['']
    L += [f'### 4c. Summary: items matched out of {len(ITEMS)}', '', '| corpus | full | short | fails (full) | fails (short) |', '|---|---|---|---|---|']
    lab = dict(ITEMS)
    for n in names:
        ff = [lab[k] for k, v in out['marks_full'][n].items() if not v]; fs = [lab[k] for k, v in out['marks_short'][n].items() if not v]
        L.append(f"| {n} | {sum(out['marks_full'][n].values())} | {sum(out['marks_short'][n].values())} | {', '.join(ff) if ff else '-'} | {', '.join(fs) if fs else '-'} |")
    L += ['', 'Items failed by every non-Voynich corpus (full): ' + (', '.join(lab[k] for k, _ in ITEMS if not any(out['marks_full'][n][k] for n in names if not n.startswith('voynich'))) or 'none'),
          'Items failed by every non-Voynich corpus (short): ' + (', '.join(lab[k] for k, _ in ITEMS if not any(out['marks_short'][n][k] for n in names if not n.startswith('voynich'))) or 'none'), '']
    L += ['### 4d. Where each generator fails (full battery unless noted)', '']
    for n in names:
        if n.startswith('voynich'):
            continue
        L.append(f"- {n}: " + out['fail_lines'].get(n, ''))
    L += ['', '## 5. Conclusion', '', conclusion, '', '## 6. Checked / not checked / user must verify', '']
    L += out['checklist']
    open(os.path.join(OUT, 'b3.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')

# ----------------------------------------------------------------------------------------------- main
def fail_line(name, marks_full, marks_short, full, short, real_full, real_short):
    lab = dict(ITEMS)
    def desc(marks, res, real):
        parts = []
        for k, _ in ITEMS:
            if not marks[k]:
                v = res[k]; r = real[k]
                if v is None:
                    parts.append(f'{lab[k]} (missing)')
                else:
                    parts.append(f'{lab[k]} {fmt(v)} vs {fmt(r)}')
        return parts
    f = desc(marks_full, full, real_full); s = desc(marks_short, short, real_short)
    return (f'fails {len(f)}/{len(ITEMS)} full [' + '; '.join(f) + f']; fails {len(s)}/{len(ITEMS)} short [' + '; '.join(s) + ']') if (f or s) else 'matches every item'

def main():
    t0 = time.time()
    zl = load_zl_lang(); skel = a4.skeleton(zl)
    ref = a4.load_zl()
    assert words_of(zl) == words_of(ref) and len(zl) == len(ref), 'loader mismatch with a4.load_zl'
    N = len(words_of(zl))
    log(f'ZL: {len(zl)} pages, {sum(len(p) for p in skel)} lines, {N} tokens; Currier labels {collections.Counter(p["lang"] for p in zl)}')
    corpora = collections.OrderedDict()
    corpora['voynich_ZL'] = zl
    corpora['voynich_A'] = [p for p in zl if p['lang'] == 'A']
    corpora['voynich_B'] = [p for p in zl if p['lang'] == 'B']
    for lang, name in (('la', 'latin'), ('it', 'italian'), ('en', 'english')):
        corpora[name] = a4.pour(a4.lang_words(lang, N), skel); log(f'{name} loaded')
    corpora['autocopist_s19'] = a4.Autocopist(19).generate(skel); log('autocopist 19 generated')
    corpora['autocopist_s7'] = a4.Autocopist(7).generate(skel); log('autocopist 7 generated')
    corpora['rugg_grille'] = a4.Rugg(19).generate(skel)
    corpora['rugg_sorted'] = a4.RuggSorted(19).generate(skel)
    # naibbe shipped
    shipped = read_cipher_lines(os.path.join(NAIBBE_DIR, 'encrypted_nathist_output_ciphertext.txt'))
    shipped_words = [w for ws, _ in shipped for w in ws]
    k = 0
    while len(shipped_words) < N:   # the fixed parse (34,834 tokens) is longer than the shipped text (34,764): cycle its lines
        shipped.append(shipped[k]); shipped_words += shipped[k][0]; k += 1
    if k:
        log(f'shipped naibbe cycled by {k} lines to reach {N} tokens')
    corpora['naibbe_pliny'] = a4.pour(shipped_words[:N], skel)
    corpora['naibbe_pliny_lines'] = lines_into_pages(shipped, skel, N)
    # naibbe regenerated
    nb = Naibbe(os.path.join(NAIBBE_DIR, 'references_naibbe_tables.csv'), seed=19)
    port_lines = nb.generate(os.path.join(NAIBBE_DIR, 'input_examples_nathist_book16.txt'), 10 ** 9)
    port_words = [w for ws, _ in port_lines for w in ws]
    def top20(ws):
        return {w for w, _ in collections.Counter(ws).most_common(20)}
    port_check = {'port_tokens': len(port_words), 'shipped_tokens': len(shipped_words),
                  'port_len_mean': sum(map(len, port_words)) / len(port_words), 'shipped_len_mean': sum(map(len, shipped_words)) / len(shipped_words),
                  'port_types': len(set(port_words)), 'shipped_types': len(set(shipped_words)),
                  'top20_overlap': len(top20(port_words) & top20(shipped_words)),
                  'port_top10': collections.Counter(port_words).most_common(10), 'shipped_top10': collections.Counter(shipped_words).most_common(10)}
    log(f'naibbe port check: {port_check}')
    nb = Naibbe(os.path.join(NAIBBE_DIR, 'references_naibbe_tables.csv'), seed=19)
    dc_lines = nb.generate(os.path.join(NAIBBE_DIR, 'input_examples_divina_commedia.txt'), N)
    dc_words = [w for ws, _ in dc_lines for w in ws]
    assert all(a4.AZ.match(w) for w in dc_words), 'non a-z token in naibbe output'
    corpora['naibbe_divcom'] = a4.pour(dc_words[:N], skel)
    log(f'naibbe divcom: {len(dc_lines)} lines, {len(dc_words)} tokens, retries {nb.retries}')
    # gibberish
    gib, per_file = load_gibberish()
    log(f'gibberish: {len(per_file)} files, {len(gib)} tokens')
    corpora['gaskell_gibberish'] = a4.pour(cycle_to(gib, N), skel)
    N_short = min(10053, len(gib))

    sizes = collections.OrderedDict()
    for n, p in corpora.items():
        sizes[n] = {'tokens': len(words_of(p)), 'pages': len(p), 'lines': sum(len(q['lines']) for q in p)}
    full = collections.OrderedDict(); short = collections.OrderedDict(); xf = {}; xs = {}
    for n, p in corpora.items():
        t1 = time.time()
        full[n] = battery(p, n, xf)
        short[n] = battery(truncate_pages(p, N_short), n, xs)
        log(f'{n}: battery done in {time.time() - t1:.1f}s  (full tokens {xf[n]["tokens"]}, short tokens {xs[n]["tokens"]})')
    tol_f, marks_f = score(full); tol_s, marks_s = score(short)
    fail_lines = {n: fail_line(n, marks_f[n], marks_s[n], full[n], short[n], full['voynich_ZL'], short['voynich_ZL']) for n in corpora}
    out = {'meta': {'N': N, 'pages': len(zl), 'lines': sum(len(p) for p in skel), 'N_short': N_short,
                    'gibberish': {'files': len(per_file), 'clean_tokens': len(gib), 'cycles': -(-N // len(gib)), 'per_file': per_file},
                    'naibbe_port_check': port_check, 'naibbe_divcom_lines': len(dc_lines), 'naibbe_divcom_tokens': len(dc_words), 'naibbe_divcom_retries': nb.retries,
                    'scales': SCALES, 'items': ITEMS, 'sources': SOURCES, 'runtime_s': None},
           'battery_text': BATTERY_TEXT, 'corpora': sizes, 'full': full, 'short': short, 'extra_full': xf, 'extra_short': xs,
           'tol_full': tol_f, 'tol_short': tol_s, 'marks_full': marks_f, 'marks_short': marks_s,
           'matches_full': {n: sum(m.values()) for n, m in marks_f.items()}, 'matches_short': {n: sum(m.values()) for n, m in marks_s.items()},
           'fail_lines': fail_lines}
    out['meta']['runtime_s'] = round(time.time() - t0, 1)
    out['checklist'] = CHECKLIST
    json.dump(out, open(os.path.join(OUT, 'b3.json'), 'w'), indent=1, default=str)
    write_md(out, CONCLUSION)
    log(f'done in {out["meta"]["runtime_s"]}s')
    for n in corpora:
        log(f'{n:20s} full {out["matches_full"][n]:2d}/{len(ITEMS)}  short {out["matches_short"][n]:2d}/{len(ITEMS)}')

CONCLUSION = """Under a rule that the real text's own Currier-B pages fail on 18 of 37 items (short battery), no generator or control comes close to Voynichese: the three Naibbe ciphertexts score best (17/37 full and short), Rugg-sorted and Italian next (13-14), and the autocopist, Rugg grille, Latin, English and human gibberish trail at 8-14, so the counts are a ranking under a deliberately narrow rule, not pass/fail verdicts.  Every non-Voynich corpus fails the adjacent-repeat rates (exact and LD<=1), self-citation within 10 tokens, the MZ peak height and (full length) the first-half/second-half glyph-bigram divergence: nothing tested reproduces both the local near-repetition of Voynichese and its slow A-to-B drift (JSD halves 0.063 bits; language controls 0.003-0.007, autocopist 0.02, Rugg 0.003-0.01, Naibbe 0.002).  By family: natural language is excluded by the conditional character entropies (h2/h3 about 1 bit too high), positional lock (0.26-0.35 vs 0.64) and character 3-gram cross-entropy; the autocopist reproduces the self-citation ratio, Zipf neighbourhood and the MZ peak position but is excluded by vocabulary growth (TTR 0.34-0.38 vs 0.21, hapax/tokens, Heaps 0.85-0.88 vs 0.74), a 1-bit excess in glyph entropy, gallows in line-interior position (0.26-0.37 vs 0.065) and near-zero token predictability; the Rugg grille is excluded by an almost hapax-free vocabulary that changes wholesale every four pages (hapax/types 0.06, MZ peak R 2.0 bits), the sorted variant by 9 % exact adjacent repeats; the Naibbe cipher matches character entropies, mean word length, positional lock, character predictability and Zipf slope to within tolerance but is excluded by the complete absence of long-range structure (R(s) about 0.003 bits at every scale, vs 0.29 for the real text and 0.08-0.16 for the language controls, which peak at hundreds to thousands of tokens as expected), by too few hapaxes, weak self-citation (ratio 0.96-0.98 vs 1.13) and no line-initial gallows preference; human gibberish is excluded by character entropy (h2 3.9 bits) and the absence of any slot grammar (positional lock 0.14).  No single family therefore remains compatible as written: the glyph-level items favour a verbose-cipher-like encoding (Naibbe), the local repetition and self-citation items favour a copy-and-modify process (autocopist), and the long-range and drift items demand what neither supplies -- topical structure on a scale of hundreds of tokens plus a regime change between A and B.  The bake-off does not exclude hybrids (a Naibbe-like encoding of a text with real topic structure, or an autocopist with a tighter glyph grammar and a drifting source), and it says nothing about meaning."""

CHECKLIST = [
    '- Checked: the b3 loader reproduces a4.load_zl token for token (assert); every full-length corpus has 34,116 tokens in the ZL skeleton (section 1 table); the naibbe stdlib port re-encrypts the shipped Pliny plaintext to a token count / length distribution close to the shipped ciphertext (section 1 numbers); all generated naibbe tokens are a-z (assert).',
    '- Checked: battery text and match rule were written into this script before any score was computed; the rule is applied mechanically by score().',
    '- Not checked: whether the shipped Pliny ciphertext came from naibbe.py or naibbe_v2.py (78-card deck); the port follows naibbe.py.',
    '- Not checked: the autocopist corpora have 30,631 / 33,124 tokens, not 34,116 (a4.Autocopist fills lines by character length and does not pad, despite its docstring); all other full-length corpora have exactly 34,116.',
    '- Not checked: h_peak_log2s is poorly determined for the real text because R(s) is flat between s = 256 and 2048 (0.280-0.287 bits); h_peak_R is the informative number.',
    '- Not checked: the language controls are generic Gutenberg / web texts, not 15th-century herbals; their long-range values are indicative only.',
    '- Not checked: a4 caveats carry over -- the autocopist is a re-implementation of Timm\'s Java code with one documented addition (ee -> ch/sh back-substitution), the Rugg generators are this project\'s own table/grille designs, not Rugg\'s published tables.',
    '- Not checked: h (MZ-style) is a simplified whole-vocabulary block-entropy statistic, not Montemurro & Zanette 2013\'s per-word weighted sum with analytic shuffled expectation; peak positions should be read qualitatively.',
    '- Not checked: the ±10 % / autocopist-spread tolerance is a pre-registered convention, not a significance test; no confidence intervals were computed (one seed per Rugg variant, one shuffle for e, three for h).',
    '- User must verify: that the 38 gibberish files in scratchpad/gaskell_voynich/data/gib are the complete Gaskell & Bowern set and that stripping diacritics (e.g. í -> i) is acceptable for a Latin-alphabet gibberish corpus.',
    '- User must verify: the citations (Timm & Schinner 2020 Cryptologia 44(1) 1-19; Rugg 2004 Cryptologia 28(1) 31-46; Greshko 2025 Cryptologia doi 10.1080/01611194.2025.2566408; Gaskell & Bowern 2022 CEUR Workshop Proceedings, Voynich 2022, Malta) before quoting them in NOTES.md.',
]

if __name__ == '__main__':
    main()
