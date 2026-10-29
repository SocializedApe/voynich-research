"""a4_selfcitation.py -- Timm & Schinner self-citation test + generator comparison.

Pure Python 3.12, no third-party packages.

What it does
  1. Loads ZL3b-n paragraph text (locus P), drops tokens containing '?' or any non a-z char
     (IVTFF extended glyph codes '@nnn;', apostrophes).  Keeps page (folio) / line / paragraph structure.
  2. Builds a "skeleton": for every page the list of lines, each line = (token_count, char_length,
     para_start flag).  Natural-language corpora (la, it, de, en, da) are poured into this exact
     skeleton (same number of pages, lines, tokens per line), so all page/line statistics are
     computed on identical structure.
  3. Self-citation statistics per corpus:
       (a) for every token, distance in tokens back to the nearest earlier token on the same page
           with Levenshtein distance <= 1 (and separately == 0): coverage, median, fraction of all
           tokens with such a predecessor within 10 / 30 tokens / within the previous 2 lines.
       (b) fraction of tokens having >= 1 other token on the same page within LD <= 1
           (also split into exact repeat vs. different type at LD 1).
       (c) whole-corpus type network: fraction of types with an LD-1 neighbour type,
           giant-component share (the statistic Timm & Schinner report as 84.7 % for the VMS).
       Controls: tokens shuffled within page (destroys locality, keeps page vocabulary) and shuffled
       over the whole corpus (destroys page vocabulary too).
  4. Generators: (i) autocopist re-implemented from Timm's Java reference implementation
     (github.com/TorstenTimm/SelfCitationTextgenerator, conf.properties defaults), filled into the
     ZL skeleton (same lines per page, same paragraph starts, line char length as max line length);
     (ii) Rugg-style table-and-grille generator.  Both truncated/padded to the ZL token count.
  5. General statistics for all: h1, h2 (letters, no spaces, and with space symbol), Zipf slope
     (OLS log f vs log r, ranks 1..1000), hapax fraction (types and tokens), word length mean / variance,
     adjacent identical-token rate; raw EVA and glyph-merged EVA for Voynichese and generators.
"""
import os as _os  # local paths (the September 2026 scripts hard-coded another machine)
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_CORP = _os.path.join(_HERE, 'data', 'corpora')  # corp_<lang>_<gutenberg id>.txt, see fetch_corpora.py
_EXT = _os.path.join(_HERE, 'data', 'external')  # third-party data (Naibbe, Gaskell & Bowern)
_IT = _os.path.join(_CORP, 'corpus_it.txt')  # vatican5 OCR corpus from the September sample's first words (fetch_corpora.py)
import sys, os, re, json, math, random, collections, statistics, time

BASE = _HERE
ZL = os.path.join(BASE, 'data', 'ZL3b-n.words.tsv')
CORP = _CORP
IT = _IT
OUT = os.path.join(BASE, 'results')
os.makedirs(OUT, exist_ok=True)
AZ = re.compile(r'^[a-z]+$')

# ----------------------------------------------------------------------------- data loading
def load_zl():
    """returns pages: list of dicts {folio, lines:[{'words':[...], 'para_start':bool}]}"""
    pages = collections.OrderedDict()
    with open(ZL, encoding='utf-8') as f:
        next(f)
        for l in f:
            c = l.rstrip('\n').split('\t')
            if c[2] != 'P':
                continue
            words = [w for w in c[9].split() if AZ.match(w)]
            if not words:
                continue
            pages.setdefault(c[0], []).append({'words': words, 'para_start': c[7] == '1'})
    return [{'folio': k, 'lines': v} for k, v in pages.items()]

def skeleton(pages):
    return [[(len(ln['words']), len(' '.join(ln['words'])), ln['para_start']) for ln in p['lines']] for p in pages]

def flatten(pages):
    """list of (page_idx, line_idx, word)"""
    out = []
    for pi, p in enumerate(pages):
        for li, ln in enumerate(p['lines']):
            for w in ln['words']:
                out.append((pi, li, w))
    return out

def pour(words, skel):
    """pour a flat word list into the skeleton"""
    it = iter(words); pages = []
    for pl in skel:
        lines = []
        for (n, _, ps) in pl:
            lines.append({'words': [next(it) for _ in range(n)], 'para_start': ps})
        pages.append({'folio': '', 'lines': lines})
    return pages

def gutenberg_words(path):
    t = open(path, encoding='utf-8', errors='replace').read()
    i = t.find('*** START OF')
    if i >= 0:
        j = t.find('\n', i); t = t[j + 1:]
    k = t.find('*** END OF')
    if k >= 0:
        t = t[:k]
    t = t.lower()
    return [w for w in re.split(r'[^^\W\d_]+' if False else r'[^a-zà-ÿœæøåßþð]+', t) if w]

def lang_words(lang, need):
    if lang == 'it':
        words = []
        with open(IT, encoding='utf-8', errors='replace') as f:
            for line in f:
                words.extend(w for w in re.split(r'[^a-zà-ÿœæøåßþð]+', line.lower()) if w)
                if len(words) >= need:
                    break
        return words[:need]
    files = sorted(fn for fn in os.listdir(CORP) if fn.startswith(f'corp_{lang}_') and fn.endswith('.txt'))
    words = []
    for fn in files:
        words.extend(gutenberg_words(os.path.join(CORP, fn)))
        if len(words) >= need:
            break
    if len(words) < need:
        raise SystemExit(f'{lang}: only {len(words)} words, need {need}')
    return words[:need]

# ----------------------------------------------------------------------------- Levenshtein <= 1
def ld1(a, b):
    """0 if equal, 1 if Levenshtein distance is 1, 2 otherwise (meaning >1)"""
    if a == b:
        return 0
    la, lb = len(a), len(b)
    d = la - lb
    if d == 0:
        mism = 0
        for x, y in zip(a, b):
            if x != y:
                mism += 1
                if mism > 1:
                    return 2
        return 1
    if d < -1 or d > 1:
        return 2
    if la < lb:
        a, b = b, a
    i = j = 0; skipped = False
    la = len(a); lb = len(b)
    while i < la and j < lb:
        if a[i] == b[j]:
            i += 1; j += 1
        elif skipped:
            return 2
        else:
            skipped = True; i += 1
    return 1

def selfcit_stats(pages):
    """(a) nearest-earlier-similar distances, (b) any-neighbour-on-page fractions."""
    n_tok = 0; n_long = 0
    d1 = []; d0 = []          # distances for tokens that have a predecessor
    d1_lines = []; d0_lines = []
    d1_long = []              # same, target token >= 5 chars
    any_le1 = 0; any_exact = 0; any_ld1_other = 0
    for p in pages:
        toks = []; lines = []
        for li, ln in enumerate(p['lines']):
            for w in ln['words']:
                toks.append(w); lines.append(li)
        n = len(toks); n_tok += n
        lens = [len(t) for t in toks]
        last_exact = {}
        for i in range(n):
            w = toks[i]; lw = lens[i]
            if lw >= 5: n_long += 1
            # exact
            if w in last_exact:
                j = last_exact[w]; d0.append(i - j); d0_lines.append(lines[i] - lines[j])
            # LD<=1 nearest
            j = i - 1
            while j >= 0:
                if -1 <= lens[j] - lw <= 1 and ld1(toks[j], w) <= 1:
                    d1.append(i - j); d1_lines.append(lines[i] - lines[j])
                    if lw >= 5: d1_long.append(i - j)
                    break
                j -= 1
            last_exact[w] = i
        # (b) any neighbour on the page (either direction)
        cnt = collections.Counter(toks)
        types = list(cnt)
        bylen = collections.defaultdict(list)
        for t in types:
            bylen[len(t)].append(t)
        has_nb = {}
        for t in types:
            found = False
            for L in (len(t) - 1, len(t), len(t) + 1):
                for u in bylen.get(L, ()):
                    if u != t and ld1(t, u) == 1:
                        found = True; break
                if found:
                    break
            has_nb[t] = found
        for w in toks:
            ex = cnt[w] >= 2; nb = has_nb[w]
            any_exact += ex; any_ld1_other += nb; any_le1 += (ex or nb)
    def summ(d, dl):
        k = len(d)
        return {
            'coverage': k / n_tok,
            'median_distance_given_hit': statistics.median(d) if d else None,
            'mean_distance_given_hit': sum(d) / k if d else None,
            'frac_all_within_10': sum(1 for x in d if x <= 10) / n_tok,
            'frac_all_within_30': sum(1 for x in d if x <= 30) / n_tok,
            'frac_all_within_prev2lines': sum(1 for x in dl if x <= 2) / n_tok,
            'frac_all_same_line': sum(1 for x in dl if x == 0) / n_tok,
            'frac_hits_within_10': (sum(1 for x in d if x <= 10) / k) if k else None,
        }
    return {
        'tokens': n_tok, 'tokens_len>=5': n_long,
        'long_tokens_LD<=1': {'coverage': len(d1_long) / n_long, 'frac_all_within_10': sum(1 for x in d1_long if x <= 10) / n_long,
                              'frac_all_within_30': sum(1 for x in d1_long if x <= 30) / n_long,
                              'median_distance_given_hit': statistics.median(d1_long) if d1_long else None},
        'nearest_earlier_LD<=1': summ(d1, d1_lines),
        'nearest_earlier_LD0': summ(d0, d0_lines),
        'frac_tokens_with_any_page_neighbour_LD<=1': any_le1 / n_tok,
        'frac_tokens_with_exact_repeat_on_page': any_exact / n_tok,
        'frac_tokens_with_LD1_other_type_on_page': any_ld1_other / n_tok,
    }

def type_network(words):
    """corpus-wide LD1 network over word types (deletion-key index + verification)."""
    cnt = collections.Counter(words)
    types = list(cnt)
    idx = {t: i for i, t in enumerate(types)}
    buckets = collections.defaultdict(list)
    for t in types:
        buckets[t].append(t)
        for i in range(len(t)):
            buckets[t[:i] + t[i + 1:]].append(t)
    parent = list(range(len(types)))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    has = [False] * len(types)
    for key, lst in buckets.items():
        if len(lst) < 2:
            continue
        lst = list(dict.fromkeys(lst))
        for a in range(len(lst)):
            for b in range(a + 1, len(lst)):
                if ld1(lst[a], lst[b]) == 1:
                    ia, ib = idx[lst[a]], idx[lst[b]]
                    has[ia] = has[ib] = True
                    ra, rb = find(ia), find(ib)
                    if ra != rb:
                        parent[ra] = rb
    comp = collections.Counter(find(i) for i in range(len(types)))
    giant = max(comp.values())
    tok_conn = sum(cnt[t] for i, t in enumerate(types) if has[i])
    return {'types': len(types), 'frac_types_with_LD1_neighbour': sum(has) / len(types),
            'frac_tokens_whose_type_has_LD1_neighbour': tok_conn / len(words),
            'giant_component_frac_types': giant / len(types)}

# ----------------------------------------------------------------------------- general stats
MERGE = [('cfh', 'F'), ('cph', 'P'), ('ckh', 'K'), ('cth', 'T'), ('ch', 'C'), ('sh', 'S'),
         ('iiin', 'N'), ('iin', 'N'), ('in', 'N'), ('ee', 'E')]
def merge_glyphs(w):
    out = []; i = 0
    while i < len(w):
        for s, r in MERGE:
            if w.startswith(s, i):
                out.append(r); i += len(s); break
        else:
            out.append(w[i]); i += 1
    return ''.join(out)

def entropies(words):
    s = ''.join(words)
    c1 = collections.Counter(s); n = len(s)
    h1 = -sum(v / n * math.log2(v / n) for v in c1.values())
    c2 = collections.Counter(zip(s, s[1:])); n2 = len(s) - 1
    hj = -sum(v / n2 * math.log2(v / n2) for v in c2.values())
    # H(X2|X1) = H(X1,X2) - H(X1) with X1 distribution over first n2 chars (approx n)
    h2 = hj - h1
    sp = ' '.join(words)
    c1s = collections.Counter(sp); ns = len(sp)
    h1s = -sum(v / ns * math.log2(v / ns) for v in c1s.values())
    c2s = collections.Counter(zip(sp, sp[1:])); n2s = len(sp) - 1
    h2s = -sum(v / n2s * math.log2(v / n2s) for v in c2s.values()) - h1s
    return h1, h2, h1s, h2s

def zipf_slope(words, maxrank=1000):
    f = sorted(collections.Counter(words).values(), reverse=True)[:maxrank]
    xs = [math.log10(r + 1) for r in range(len(f))]; ys = [math.log10(v) for v in f]
    mx = sum(xs) / len(xs); my = sum(ys) / len(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)

def general_stats(words, merged=False):
    if merged:
        words = [merge_glyphs(w) for w in words]
    cnt = collections.Counter(words)
    h1, h2, h1s, h2s = entropies(words)
    L = [len(w) for w in words]
    m = sum(L) / len(L)
    var = sum((x - m) ** 2 for x in L) / len(L)
    adj = sum(1 for a, b in zip(words, words[1:]) if a == b) / (len(words) - 1)
    hap = sum(1 for v in cnt.values() if v == 1)
    return {'tokens': len(words), 'types': len(cnt), 'TTR': len(cnt) / len(words),
            'h1_letters': round(h1, 4), 'h2_letters': round(h2, 4),
            'h1_with_space': round(h1s, 4), 'h2_with_space': round(h2s, 4),
            'zipf_slope_r1_1000': round(zipf_slope(words), 4),
            'hapax_frac_types': round(hap / len(cnt), 4), 'hapax_frac_tokens': round(hap / len(words), 4),
            'wordlen_mean': round(m, 4), 'wordlen_var': round(var, 4),
            'adjacent_repeat_rate': round(adj, 5),
            'top10': cnt.most_common(10)}

# ----------------------------------------------------------------------------- autocopist generator
# Tables transcribed from Timm's Glyph.java (cumulative weights 0..100) and conf.properties defaults.
LIGS = ['cthh', 'ckhh', 'iiin', 'iiir', 'iiil', 'iiim', 'iiis', 'cth', 'ckh', 'cph', 'cfh', 'ith', 'ikh', 'iph', 'ifh',
        'eee', 'iin', 'iir', 'iil', 'iim', 'iis', 'ee', 'in', 'ir', 'il', 'im', 'is', 'ol', 'or', 'al', 'ar', 'om',
        'am', 'og', 'ag', 'dy', 'qo', 'ch', 'sh']
def tok(w):
    out = []; i = 0
    while i < len(w):
        for s in LIGS:
            if w.startswith(s, i):
                out.append(s); i += len(s); break
        else:
            out.append(w[i]); i += 1
    return out

SIMILAR = {  # glyph -> [(cumweight, replacement)]  (Glyph.java)
    'k': [(77, 't'), (94, 'p'), (100, 'f')], 't': [(84, 'k'), (96, 'p'), (100, 'f')],
    'p': [(59, 'k'), (97, 't'), (100, 'f')], 'f': [(56, 'k'), (92, 't'), (100, 'p')],
    'o': [(100, 'y')], 'y': [(100, 'o')], 'd': [(90, 'd'), (100, 's')], 's': [(75, 'r'), (100, 'd')],
    'g': [(100, 'm')], 'n': [(50, 'r'), (63, 'in'), (100, 'iin')], 'l': [(100, 'r')], 'r': [(50, 'r'), (100, 's')],
    'a': [(98, 'a'), (100, 'o')], 'e': [(50, 'e'), (99, 'ee'), (100, 'eee')],
    # NOTE: 'ee'->'ch'/'sh' back-substitution is MY addition (Glyph.java summary showed only ch->ee);
    # without it the generated vocabulary drifts irreversibly to e-words (eo, ey, eeo, eey).
    'ee': [(40, 'e'), (60, 'ee'), (65, 'eee'), (90, 'ch'), (100, 'sh')], 'eee': [(50, 'ee'), (80, 'e'), (100, 'ch')],
    'ch': [(10, 'ee'), (90, 'sh'), (97, 'ckh'), (100, 'cth')], 'sh': [(10, 'ee'), (90, 'ch'), (97, 'ckh'), (100, 'cth')],
    'ckh': [(50, 'cth'), (90, 'ch'), (100, 'sh')], 'cth': [(50, 'ckh'), (90, 'ch'), (100, 'sh')],
    'cph': [(50, 'cfh'), (100, 'ch')], 'cfh': [(50, 'cph'), (100, 'ch')],
    'in': [(8, 'n'), (84, 'iin'), (87, 'iiin'), (97, 'ir'), (100, 'il')],
    'iin': [(13, 'n'), (70, 'in'), (74, 'iiin'), (97, 'iir'), (100, 'il')],
    'iiin': [(6, 'n'), (31, 'in'), (90, 'iin'), (98, 'ir'), (100, 'iiin')],
    'ir': [(6, 'r'), (33, 'in'), (95, 'iin'), (100, 'iiir')], 'iir': [(6, 'r'), (30, 'in'), (89, 'iin'), (100, 'iiir')],
    'iiir': [(50, 'iir'), (100, 'iiin')], 'il': [(50, 'in'), (100, 'ir')],
    'ol': [(30, 'or'), (63, 'al'), (100, 'ar')], 'or': [(47, 'ol'), (73, 'al'), (100, 'ar')],
    'al': [(48, 'ol'), (72, 'or'), (100, 'ar')], 'ar': [(49, 'ol'), (73, 'or'), (100, 'al')],
    'om': [(45, 'ol'), (94, 'or'), (98, 'og'), (100, 'om')], 'am': [(45, 'al'), (94, 'ar'), (98, 'ag'), (100, 'am')],
    'og': [(50, 'om'), (100, 'or')], 'ag': [(50, 'am'), (100, 'ar')],
    'dy': [(10, 'd'), (100, 'dy')], 'm': [(100, 'm')], 'qo': [(100, 'qo')], 'x': [(100, 'x')],
}
FINAL_SUB = {  # word-final substitutions (Glyph.java combinableFinalSubstitutionMap)
    'om': [(8, 'o'), (30, 'y'), (75, 'ol'), (100, 'or')], 'am': [(4, 'o'), (30, 'y'), (70, 'al'), (100, 'ar')],
    'og': [(8, 'o'), (30, 'y'), (55, 'or'), (80, 'al'), (100, 'ar')], 'ag': [(4, 'o'), (30, 'y'), (65, 'ol'), (80, 'or'), (100, 'ar')],
    'ol': [(8, 'o'), (30, 'y'), (54, 'or'), (81, 'al'), (100, 'ar')], 'or': [(8, 'o'), (30, 'y'), (63, 'ol'), (81, 'al'), (100, 'ar')],
    'al': [(4, 'o'), (30, 'y'), (64, 'ol'), (81, 'or'), (100, 'ar')], 'ar': [(4, 'o'), (30, 'y'), (64, 'ol'), (82, 'or'), (100, 'al')],
    'y': [(20, 'o'), (44, 'ol'), (60, 'or'), (75, 'al'), (100, 'ar')], 'o': [(20, 'y'), (44, 'ol'), (60, 'or'), (75, 'al'), (100, 'ar')],
    'd': [(70, 'dy'), (100, 'd')], 'dy': [(10, 'd'), (100, 'dy')],
}
PREFIX_OK = {'l': ['k', 't', 'p', 'f', 'd', 'ch', 'sh', 'o', 'a', 'e', 'ee'], 'o': ['k', 't', 'p', 'f', 'd', 'ch', 'sh'],
             'y': ['k', 't', 'p', 'f', 'd', 'ch', 'sh'], 'ch': ['k', 't', 'p', 'f', 'd', 'ol', 'or', 'al', 'ar'],
             'sh': ['k', 't', 'p', 'f', 'd', 'ol', 'or', 'al', 'ar'], 'q': ['o', 'y'], 'd': ['a'], 'x': ['ol', 'or', 'al', 'ar']}
GALLOWS = ['k', 't', 'p', 'f']
CURVE = set('e h d s y o ch sh ckh cth cph cfh cthh ckhh al ol x l a ee eee or ar dy qo'.split())
ITYPE = {'in', 'iin', 'iiin', 'ir', 'iir', 'iiir', 'il', 'iil', 'iiil', 'im', 'iim', 'iiim', 'is', 'iis', 'iiis', 'i'}
FINAL_ONLY = {'in', 'iin', 'iiin', 'iir', 'iiir', 'iil', 'iiil', 'im', 'iim', 'iiim', 'm', 'g', 'n', 'om', 'am', 'og', 'ag'}
START_OK = {'qo', 'o', 'a', 'y', 'ch', 'sh', 's', 'd', 'k', 't', 'p', 'f', 'x', 'l', 'ckh', 'cth', 'cph', 'cfh', 'r', 'ol', 'or', 'al', 'ar', 'e', 'ee'}
COMBINABLE = {'ol', 'al', 'or', 'ar'}
LINE_FINAL_MAP = {'ol': 'om', 'or': 'om', 'al': 'am', 'ar': 'am', 'om': 'og', 'am': 'ag', 'in': 'n', 'iin': 'im', 'iiin': 'im'}

def can_follow(a, b):
    """curveline-style adjacency rule (my transcription of Timm's CurveLineCanFollow; see caveats)."""
    if a == '':
        return b in START_OK
    if b == '':
        return a not in GALLOWS and a not in ('qo', 'q')
    if a in FINAL_ONLY:
        return False
    if a in GALLOWS:
        return b in ('a', 'e', 'ee', 'eee', 'o', 'y', 'ch', 'sh', 'ol', 'or', 'al', 'ar', 'al')
    if b in ITYPE:
        return a in ('a', 'o')
    if a == 'qo' or a == 'q':
        return b in GALLOWS or b in ('ch', 'sh', 'l', 'e', 'ee', 'd', 'o', 'ckh', 'cth')
    if a in ITYPE:
        return False
    if b in GALLOWS:
        return a in CURVE or a in ('qo',)
    return True

def valid(g):
    if not g:
        return False
    if not can_follow('', g[0]):
        return False
    s = ''.join(g)
    if 'eeee' in s or len(s) > 12:
        return False
    for x, y in zip(g, g[1:]):
        if not can_follow(x, y):
            return False
    return can_follow(g[-1], '')

def pick(rng, table):
    r = rng.randint(1, 100)
    for c, v in table:
        if r <= c:
            return v
    return table[-1][1]

class Autocopist:
    """Re-implementation of Timm's SelfCitationTextGenerator with conf.properties defaults:
    add_remove 20 %, combine_split 30 %, replace 50 %, reuse_last 10 %, same_position 28 %,
    suggestions 'top' 40 % (i-type >= 20 %, dy-type >= 25 %  [Currier B thresholds]),
    max_repeat_count 3, dismiss combined-as-source 30 %, word-final substitutions on,
    paragraph-initial gallow 94 %, initial line = Timm's Currier-B sample line."""
    def __init__(self, seed=19):
        self.rng = random.Random(seed)
        self.all_lines = []       # every generated line (list of glyph lists)
        self.page_lines = []
        self.stat_i = self.stat_dy = self.stat_tot = 0
        self.page_counts = collections.Counter()
        self.doc_counts = collections.Counter()
        self.rep_type = None; self.rep_n = 0
        self.last_source = None; self.last_gen = None
        self.combined = set()

    @staticmethod
    def ttype(g):
        s = ''.join(g)
        if 'i' in s: return 'i'
        if g[-1] in ('dy', 'y', 'd') or 'dy' in g: return 'dy'
        if any(x in COMBINABLE for x in g): return 'ol'
        return 'u'

    def remember(self, g):
        t = self.ttype(g); self.stat_tot += 1
        if t == 'i': self.stat_i += 1
        if t == 'dy': self.stat_dy += 1
        self.page_counts[''.join(g)] += 1; self.doc_counts[''.join(g)] += 1
        if t == self.rep_type: self.rep_n += 1
        else: self.rep_type = t; self.rep_n = 1

    def suggest(self):
        if self.stat_tot < 20: return None
        want = None
        if self.stat_i / self.stat_tot < 0.20: want = 'i'
        elif self.stat_dy / self.stat_tot < 0.25: want = 'dy'
        if not want: return None
        for src in (self.page_counts, self.doc_counts):
            best = None
            for w, c in src.most_common():
                if self.ttype(tok(w)) == want:
                    best = tok(w); break
            if best: return best
        return None

    def choose_source(self, cur_line, line_initial):
        rng = self.rng
        if not self.page_lines:                      # first line of page: random line of the document
            line = rng.choice(self.all_lines)
        else:
            k = len(self.page_lines)
            line = self.page_lines[k - 1 - rng.randrange(max(2, k) - 1)] if k > 1 else self.page_lines[0]
        p_same = max(10, 14) if line_initial else 28
        if rng.randint(1, 100) <= p_same and len(cur_line) < len(line):
            pos = len(cur_line)
        else:
            pos = rng.randrange(len(line))
        g1 = line[pos]
        g2 = line[pos + 1] if pos + 1 < len(line) else (line[pos - 1] if pos > 0 else line[pos])
        return list(g1), list(g2)

    # ---- morph operations
    def replace(self, g, n):
        rng = self.rng
        for _ in range(8):
            h = list(g)
            for j in range(n):
                pos = rng.randrange(len(h))
                final = (j > 0 and pos == len(h) - 1 and h[pos] in FINAL_SUB)
                tab = FINAL_SUB[h[pos]] if final else SIMILAR.get(h[pos])
                if not tab: continue
                sub = pick(rng, tab)
                if sub in GALLOWS and pos + 1 < len(h) and h[pos + 1] in GALLOWS:
                    del h[pos + 1]
                cand = h[:pos] + tok(sub) + h[pos + 1:]
                if sub in [x for i, x in enumerate(h) if i != pos] and sub not in COMBINABLE and rng.randint(1, 100) <= 80:
                    continue
                if valid(cand): h = cand
            if h != g and valid(h): return h
        return None

    def add(self, g, para_init, line_init):
        rng = self.rng
        if len(g) >= 6:
            return self.remove(g)
        p_gallow = 80 if (para_init and line_init) else 8
        if rng.randint(1, 100) <= p_gallow:
            gal = pick(rng, [(34, 'k'), (49, 't'), (89, 'p'), (100, 'f')] if para_init else [(34, 'k'), (49, 't'), (89, 'k'), (100, 't')])
            if para_init and line_init:
                cand = [gal] + g
                if not valid(cand): cand = [gal, rng.choice(['o', 'a'])] + g
                if valid(cand): return cand
            else:
                if any(x in GALLOWS for x in g) and rng.randint(1, 100) <= 90: return self.remove(g)
                for _ in range(5):
                    pos = rng.randrange(len(g) + 1)
                    cand = g[:pos] + [gal] + g[pos:]
                    if valid(cand): return cand
        for _ in range(7):
            pre = rng.choice(['q', 'o', 'y', 'd', 'ch', 'sh', 'l', 'x', 'o', 'y', 'ch'])
            if g[0] not in PREFIX_OK[pre]: continue
            if pre == 'q': cand = ['qo'] + g[1:] if g[0] == 'o' else ['qo'] + g
            else: cand = [pre] + g
            if valid(cand):
                if pre in ('d', 'ch', 'sh') and len(cand) > 2 and rng.randint(1, 100) <= 70 and cand[1] in ('d', 'ch', 'sh'):
                    alt = [pre, rng.choice(GALLOWS)] + cand[2:]
                    if valid(alt): return alt
                return cand
        return self.remove(g)

    def remove(self, g):
        rng = self.rng
        if len(g) <= 2: return None
        h = g[1:]
        if h[0] in GALLOWS and len(h) > 1 and rng.randint(1, 100) <= 50:
            if h[1][0] == 'a': h = ['d'] + h[1:]
            elif h[1][0] in 'eo': h = ['ch'] + h[1:]
        if h[0] == 'q': h = ['qo'] + h[1:] if len(h) > 1 and h[1] == 'o' else h[1:]
        return h if valid(h) else None

    def combine(self, g1, g2):
        rng = self.rng
        L = len(g1)
        p = 96 if L <= 5 else (4 if L <= 8 else 0)
        if rng.randint(1, 100) > p: return None
        r = rng.randint(1, 100)
        if r <= 40: sub = g1[:rng.randint(1, len(g1))]
        elif r <= 60: sub = g1[:-1] or g1
        else:
            k = next((i + 1 for i, x in enumerate(g1) if x in COMBINABLE), len(g1) - 1 or 1); sub = g1[:k]
        tail = list(g2)
        if sub and sub[-1] in COMBINABLE and tail and tail[0] in ('l', 'r', 's'): tail = tail[1:]
        cand = sub + tail
        if 0 < len(cand) < 9 and valid(cand): return cand
        return None

    def split(self, g):
        for i in range(1, len(g)):
            if (not can_follow(g[i - 1], g[i])) or g[i - 1] in COMBINABLE or g[i] in GALLOWS:
                a, b = g[:i], g[i:]
                if (len(a) > 1 or a[0] in COMBINABLE) and len(b) > 1 and valid(a) and valid(b): return [a, b]
        return None

    def morph(self, g1, g2, para_init, line_init):
        rng = self.rng
        r = 0 if (para_init and line_init) else rng.randint(0, 100)
        if r <= 20:
            h = self.add(g1, para_init, line_init); return [h] if h else None
        if r <= 50:
            if rng.randint(1, 100) <= 50:
                h = self.combine(g1, g2)
                if h: self.combined.add(''.join(h)); return [h]
            s = self.split(g1)
            if s: return s
            r = 100
        rr = rng.randint(1, 100)
        n = 1 if rr <= 30 else (3 if rr <= 40 else 2)
        h = self.replace(g1, n)
        if h is None and n > 1: h = self.replace(g1, 1)
        return [h] if h else None

    # ---- line generation
    def gen_line(self, maxlen, para_init, line_init_prefix=True):
        rng = self.rng
        line = []; length = 0; tries = 0
        while True:
            if length + (tries // 3) >= maxlen or tries > 130: break
            line_init = not line
            src2 = None
            if self.last_gen and rng.randint(1, 100) <= 10:
                g1 = list(self.last_gen); g2 = g1
                if g1[-1] in COMBINABLE and len(g1) > 2 and rng.randint(1, 100) <= 50: g1 = g1[:-1] + [g1[-1]]
            else:
                g1, g2 = self.choose_source(line, line_init)
                sug = self.suggest() if rng.randint(1, 100) <= 40 else None
                if sug: g1 = sug
            tries += 1
            if self.last_source == g1 and tries < 100: continue
            if ''.join(g1) in self.combined and rng.randint(1, 100) <= 30 and tries < 100: continue
            out = self.morph(g1, g2, para_init, line_init)
            if out is None:
                if tries > 100: out = [g1]        # force
                else: continue
            self.last_source = g1
            for h in out:
                if not h or not valid(h): continue
                if line_init and rng.randint(1, 100) <= 30 and h[0] not in ('o', 'y', 'd', 's') and not (para_init and h[0] in GALLOWS):
                    pre = pick(rng, [(45, 'o'), (75, 'y'), (90, 'd'), (100, 's')])
                    if valid([pre] + h): h = [pre] + h
                if para_init and line_init and h[0] not in GALLOWS and rng.randint(1, 100) <= 94:
                    gal = pick(rng, [(34, 'k'), (49, 't'), (89, 'p'), (100, 'f')])
                    if valid([gal] + h): h = [gal] + h
                    elif valid([gal, 'o'] + h): h = [gal, 'o'] + h
                t = self.ttype(h)
                if t == self.rep_type and self.rep_n >= 3 and tries < 100: continue
                if line and h == line[-1] and rng.randint(1, 100) > 50: continue
                w = ''.join(h); need = len(w) + (1 if line else 0)
                if length + need > maxlen:
                    if h[-1] in LINE_FINAL_MAP:          # tryToTrim: line-final glyph variants
                        h2 = h[:-1] + [LINE_FINAL_MAP[h[-1]]]; w2 = ''.join(h2)
                        if length + len(w2) + (1 if line else 0) <= maxlen: h = h2; w = w2; need = len(w2) + (1 if line else 0)
                        else: tries += 3; continue
                    else:
                        tries += 3; continue
                line.append(h); length += need; self.remember(h); self.last_gen = h; line_init = False
                tries = 0
            if length >= maxlen - 2: break
        if not line:
            line = [tok('daiin')]
        return line

    def generate(self, skel):
        init = [tok(w) for w in 'pchal shal shorchdy okeor okain shedy pchedy qotchedy qotar ol lkar'.split()]
        self.all_lines.append(init)
        pages = []
        for pl in skel:
            self.page_lines = []; self.page_counts = collections.Counter()
            lines = []
            for (n, clen, ps) in pl:
                maxlen = max(clen, 8)
                if not self.page_lines and not self.all_lines: pass
                ln = self.gen_line(maxlen, ps)
                self.page_lines.append(ln); self.all_lines.append(ln)
                lines.append({'words': [''.join(g) for g in ln], 'para_start': ps})
            pages.append({'folio': '', 'lines': lines})
        return pages

# ----------------------------------------------------------------------------- Rugg table-and-grille
class Rugg:
    """Table-and-grille generator (Rugg 2004 'An elegant hoax?', Cryptologia 28:1).
    Table: R rows x 3 columns (prefix / midfix / suffix), cells filled at random from fixed syllable lists
    with some blanks.  Grille: card with 3 holes (one per column) at row offsets (0, d1, d2); it is moved
    down one row per word (wrapping); a new grille (offsets) every page, a new table every 4 pages.
    Consecutive words therefore come from adjacent rows, and cells recur with period R per grille."""
    PRE = ['qo', 'o', 'ch', 'sh', 'd', 's', 'y', 'ok', 'ot', 'qok', 'qot', 'ol', 'k', 't', 'p', 'l', 'r', 'da', 'so', 'cho', '', '', '', '']
    MID = ['a', 'o', 'e', 'ee', 'ch', 'sh', 'k', 't', 'ke', 'te', 'ai', 'aii', 'ol', 'ed', 'od', 'eo', 'che', 'l', '', '', '', '']
    SUF = ['y', 'dy', 'in', 'iin', 'n', 'r', 'ar', 'or', 'al', 'ol', 'am', 'ey', 'edy', 'eey', 'ody', 'aiin', 'ain', 's', 'l', '', '', '']
    def __init__(self, seed=19, rows=36):
        self.rng = random.Random(seed); self.R = rows
    def new_table(self):
        r = self.rng
        return [(r.choice(self.PRE), r.choice(self.MID), r.choice(self.SUF)) for _ in range(self.R)]
    def generate(self, skel):
        r = self.rng; pages = []; table = None
        for pi, pl in enumerate(skel):
            if pi % 4 == 0: table = self.new_table()
            d1, d2 = r.randrange(self.R), r.randrange(self.R)
            pos = r.randrange(self.R)
            lines = []
            for (n, clen, ps) in pl:
                words = []
                while len(words) < n:
                    w = table[pos % self.R][0] + table[(pos + d1) % self.R][1] + table[(pos + d2) % self.R][2]
                    pos += 1
                    if w: words.append(w)
                lines.append({'words': words, 'para_start': ps})
            pages.append({'folio': '', 'lines': lines})
        return pages

class RuggSorted(Rugg):
    """Rugg & Taylor style variant: table of R rows x K column-triples (prefix, midfix, suffix), each column
    filled with syllables of its type SORTED alphabetically (a 'systematically filled' table, so vertically
    adjacent cells hold similar syllables), ~15 % blank cells.  Grille = 3 holes, each with a row offset
    (0..2) and a triple offset; the grille moves down one row per word, then to the next triple.
    Period per grille = R*K words.  New grille per page, new table every 4 pages."""
    def __init__(self, seed=19, rows=40, triples=4):
        super().__init__(seed, rows); self.K = triples
    def col(self, lst):
        r = self.rng
        cells = sorted(r.choice([s for s in lst if s]) for _ in range(self.R))
        return [c if r.random() > 0.15 else '' for c in cells]
    def new_table(self):
        cols = []
        for _ in range(self.K):
            cols += [self.col(self.PRE), self.col(self.MID), self.col(self.SUF)]
        return cols
    def generate(self, skel):
        r = self.rng; pages = []; table = None
        R, K = self.R, self.K
        for pi, pl in enumerate(skel):
            if pi % 4 == 0: table = self.new_table()
            dr = [r.randrange(3) for _ in range(3)]; dt = [r.randrange(K) for _ in range(3)]
            p = r.randrange(R * K)
            lines = []
            for (n, clen, ps) in pl:
                words = []
                while len(words) < n:
                    row, t = p % R, (p // R) % K
                    w = ''.join(table[3 * ((t + dt[i]) % K) + i][(row + dr[i]) % R] for i in range(3))
                    p += 1
                    if w: words.append(w)
                lines.append({'words': words, 'para_start': ps})
            pages.append({'folio': '', 'lines': lines})
        return pages

# ----------------------------------------------------------------------------- controls
def shuffle_within_page(pages, seed=1):
    rng = random.Random(seed); out = []
    for p in pages:
        ws = [w for ln in p['lines'] for w in ln['words']]; rng.shuffle(ws)
        it = iter(ws)
        out.append({'folio': p['folio'], 'lines': [{'words': [next(it) for _ in ln['words']], 'para_start': ln['para_start']} for ln in p['lines']]})
    return out

def shuffle_global(pages, seed=2):
    rng = random.Random(seed)
    ws = [w for p in pages for ln in p['lines'] for w in ln['words']]; rng.shuffle(ws)
    return pour(ws, skeleton(pages))

# ----------------------------------------------------------------------------- main
def main():
    t0 = time.time()
    zl = load_zl(); skel = skeleton(zl)
    zl_words = [w for p in zl for ln in p['lines'] for w in ln['words']]
    N = len(zl_words)
    print(f'ZL P text: {len(zl)} pages, {sum(len(p) for p in skel)} lines, {N} tokens', flush=True)
    corpora = collections.OrderedDict()
    corpora['voynich_ZL'] = zl
    for lang in ['la', 'it', 'de', 'en', 'da']:
        corpora[lang] = pour(lang_words(lang, N), skel)
    ac = Autocopist(19).generate(skel)
    corpora['autocopist_s19'] = ac
    corpora['autocopist_s7'] = Autocopist(7).generate(skel)
    corpora['rugg_grille'] = Rugg(19).generate(skel)
    corpora['rugg_sorted'] = RuggSorted(19).generate(skel)
    with open(os.path.join(OUT, 'a4_autocopist_sample.txt'), 'w', encoding='utf-8') as f:
        for p in ac[:3]:
            for ln in p['lines']:
                f.write(('% ' if ln['para_start'] else '  ') + ' '.join(ln['words']) + '\n')
            f.write('----\n')
    with open(os.path.join(OUT, 'a4_rugg_sample.txt'), 'w', encoding='utf-8') as f:
        for key in ('rugg_grille', 'rugg_sorted'):
            f.write(f'==== {key}\n')
            for p in corpora[key][:2]:
                for ln in p['lines']:
                    f.write(' '.join(ln['words']) + '\n')
                f.write('----\n')
    results = collections.OrderedDict()
    for name, pages in list(corpora.items()):
        words = [w for p in pages for ln in p['lines'] for w in ln['words']]
        t1 = time.time()
        res = {'selfcitation': selfcit_stats(pages),
               'selfcitation_shuffled_within_page': selfcit_stats(shuffle_within_page(pages)),
               'selfcitation_shuffled_global': selfcit_stats(shuffle_global(pages)),
               'type_network': type_network(words),
               'general_raw': general_stats(words)}
        if name.startswith(('voynich', 'autocopist', 'rugg')):
            res['general_glyphmerged'] = general_stats(words, merged=True)
        results[name] = res
        print(f'{name}: done in {time.time()-t1:.1f}s', flush=True)
    results['_meta'] = {'tokens_per_corpus': N, 'pages': len(zl), 'lines': sum(len(p) for p in skel),
                        'page_tokens_median': statistics.median(sum(x[0] for x in pl) for pl in skel),
                        'page_tokens_min_max': [min(sum(x[0] for x in pl) for pl in skel), max(sum(x[0] for x in pl) for pl in skel)],
                        'runtime_s': round(time.time() - t0, 1)}
    json.dump(results, open(os.path.join(OUT, 'a4.json'), 'w'), indent=1)
    write_md(results)

def write_md(R):
    names = [k for k in R if not k.startswith('_')]
    L = ['# a4: self-citation test and generator comparison', '',
         f"ZL3b-n paragraph text (locus P), {R['_meta']['tokens_per_corpus']} tokens, {R['_meta']['pages']} pages, {R['_meta']['lines']} lines; "
         'every comparison corpus poured into the identical page/line skeleton.', '',
         '## 1. Nearest earlier similar token on the same page', '',
         '| corpus | cover LD<=1 | median dist | <=10 tok | <=30 tok | prev 2 lines | same line | cover LD0 | median LD0 | LD0 <=10 | LD0 prev2 |',
         '|---|---|---|---|---|---|---|---|---|---|---|']
    def row(name, s):
        a = s['nearest_earlier_LD<=1']; b = s['nearest_earlier_LD0']
        return (f"| {name} | {a['coverage']:.3f} | {a['median_distance_given_hit']} | {a['frac_all_within_10']:.3f} | {a['frac_all_within_30']:.3f} | "
                f"{a['frac_all_within_prev2lines']:.3f} | {a['frac_all_same_line']:.3f} | {b['coverage']:.3f} | {b['median_distance_given_hit']} | {b['frac_all_within_10']:.3f} | {b['frac_all_within_prev2lines']:.3f} |")
    for n in names:
        L.append(row(n, R[n]['selfcitation']))
    L += ['', 'Controls (same corpora, tokens shuffled within page / globally):', '',
          '| corpus | real <=10 | within-page-shuffle <=10 | global-shuffle <=10 | real prev2 | wp-shuffle prev2 | real cover | wp-shuffle cover | global cover |', '|---|---|---|---|---|---|---|---|---|']
    for n in names:
        a = R[n]['selfcitation']['nearest_earlier_LD<=1']; b = R[n]['selfcitation_shuffled_within_page']['nearest_earlier_LD<=1']; c = R[n]['selfcitation_shuffled_global']['nearest_earlier_LD<=1']
        L.append(f"| {n} | {a['frac_all_within_10']:.3f} | {b['frac_all_within_10']:.3f} | {c['frac_all_within_10']:.3f} | {a['frac_all_within_prev2lines']:.3f} | {b['frac_all_within_prev2lines']:.3f} | {a['coverage']:.3f} | {b['coverage']:.3f} | {c['coverage']:.3f} |")
    L += ['', 'Target tokens of length >= 5 only (source any length):', '',
          '| corpus | share of tokens >=5 | cover | <=10 tok | <=30 tok | median | wp-shuffle <=10 | global-shuffle <=10 |', '|---|---|---|---|---|---|---|---|']
    for n in names:
        s = R[n]['selfcitation']; a = s['long_tokens_LD<=1']; b = R[n]['selfcitation_shuffled_within_page']['long_tokens_LD<=1']; c = R[n]['selfcitation_shuffled_global']['long_tokens_LD<=1']
        L.append(f"| {n} | {s['tokens_len>=5']/s['tokens']:.3f} | {a['coverage']:.3f} | {a['frac_all_within_10']:.3f} | {a['frac_all_within_30']:.3f} | {a['median_distance_given_hit']} | {b['frac_all_within_10']:.3f} | {c['frac_all_within_10']:.3f} |")
    L += ['', '## 2. Tokens with at least one LD<=1 neighbour anywhere on the same page', '',
          '| corpus | any LD<=1 | exact repeat on page | different type at LD1 | global-shuffle any LD<=1 | types w/ LD1 nb (corpus) | giant comp. (types) |', '|---|---|---|---|---|---|---|']
    for n in names:
        s = R[n]['selfcitation']; g = R[n]['selfcitation_shuffled_global']; t = R[n]['type_network']
        L.append(f"| {n} | {s['frac_tokens_with_any_page_neighbour_LD<=1']:.3f} | {s['frac_tokens_with_exact_repeat_on_page']:.3f} | {s['frac_tokens_with_LD1_other_type_on_page']:.3f} | {g['frac_tokens_with_any_page_neighbour_LD<=1']:.3f} | {t['frac_types_with_LD1_neighbour']:.3f} | {t['giant_component_frac_types']:.3f} |")
    L += ['', '## 3. General statistics (raw letters; Voynich/generators raw EVA)', '',
          '| corpus | types | h1 | h2 | h1+sp | h2+sp | Zipf slope | hapax/types | hapax/tokens | wlen mean | wlen var | adj repeat |', '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for n in names:
        g = R[n]['general_raw']
        L.append(f"| {n} | {g['types']} | {g['h1_letters']} | {g['h2_letters']} | {g['h1_with_space']} | {g['h2_with_space']} | {g['zipf_slope_r1_1000']} | {g['hapax_frac_types']} | {g['hapax_frac_tokens']} | {g['wordlen_mean']} | {g['wordlen_var']} | {g['adjacent_repeat_rate']} |")
    L += ['', 'Glyph-merged EVA (ch sh ckh cth cph cfh -> 1 symbol each, in/iin/iiin -> N, ee -> E):', '',
          '| corpus | h1 | h2 | wlen mean | wlen var |', '|---|---|---|---|---|']
    for n in names:
        if 'general_glyphmerged' in R[n]:
            g = R[n]['general_glyphmerged']
            L.append(f"| {n} | {g['h1_letters']} | {g['h2_letters']} | {g['wordlen_mean']} | {g['wordlen_var']} |")
    L += ['', 'Top-10 tokens:', '']
    for n in names:
        L.append(f"- {n}: " + ', '.join(f'{w}({c})' for w, c in R[n]['general_raw']['top10']))
    open(os.path.join(OUT, 'a4.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')

if __name__ == '__main__':
    main()
