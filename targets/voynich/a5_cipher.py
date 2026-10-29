"""a5_cipher.py -- cipher-class feasibility tests on Voynich ZL3b paragraph text.

Pure Python 3.12 (no third-party packages).  Writes results/a5.json and results/a5.md.

Method summary (every choice is deliberate and stated):
  * Voynich sample = ZL3b-n, locus_type P only, words containing '?' dropped, words containing any
    non a-z character dropped (IVTFF weirdo codes '@nnn;' and apostrophes; 96 tokens = 0.3%).
  * Two glyph segmentations of the same text:
      raw  = one EVA letter per symbol
      mrg  = ligature merge applied in this order (longest first):
             cfh ckh cph cth -> F K P T ; ch -> C ; sh -> S ; iiin -> N ; iin -> M ; in -> I ; eee -> 3 ; ee -> E
  * Language samples: Gutenberg files (header/footer stripped), lower-cased, NFC, letters only
    (str.isalpha), any non-letter = word break.  Skip first 2000 words of each file (prefaces),
    then take an equal share from each file so that the total token count equals the Voynich sample.
    Italian = targets/vatican5/corpus_it.txt (already lower-case, no punctuation), same treatment.
  * h1 = unigram entropy of the symbol stream; h2 = H(X_n | X_{n-1}) = H(bigram) - H(unigram),
    computed two ways: 'nospace' (words concatenated, cross-word pairs included) and 'space'
    (word break is a symbol).  All entropies in bits, plug-in (maximum likelihood) estimates.
  * Positional constraint: for symbols with >= 20 occurrences, position class of each occurrence is
    one of single / initial / medial / final; we report the count of symbol types with >= 90 % of
    occurrences in one class, the count with 100 %, and the mutual information I(symbol; position).
  * Zipf slope: least squares of log2 freq on log2 rank over ranks 1..min(1000, types).
  * Information budget: 10-fold cross-validated word-bigram model, folds = blocks of consecutive
    lines/words, Witten-Bell interpolation bigram->unigram->unk; an unknown word costs the
    unigram unk mass plus a character-bigram spelling cost (trained on the training fold).
    Also reported: lzma / bz2 compressed size of the space-separated text.
"""
import os as _os  # local paths (the September 2026 scripts hard-coded another machine)
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_CORP = _os.path.join(_HERE, 'data', 'corpora')  # corp_<lang>_<gutenberg id>.txt, see fetch_corpora.py
_EXT = _os.path.join(_HERE, 'data', 'external')  # third-party data (Naibbe, Gaskell & Bowern)
_IT = _os.path.join(_CORP, 'corpus_it.txt')  # vatican5 OCR corpus from the September sample's first words (fetch_corpora.py)
import collections, csv, json, math, os, pathlib, re, sys, unicodedata, lzma, bz2

HERE = pathlib.Path(_HERE)
RES = HERE / 'results'; RES.mkdir(exist_ok=True)
CORP = pathlib.Path(_CORP)
IT_FILE = pathlib.Path(_IT)
LANGS = ['la', 'it', 'de', 'en', 'fr', 'da']
LOG2 = math.log2

# ----------------------------------------------------------------------------- loading
def load_voynich():
    rows = list(csv.DictReader(open(HERE / 'data' / 'ZL3b-n.words.tsv', encoding='utf-8'), delimiter='\t'))
    P = [r for r in rows if r['locus_type'] == 'P']
    words = []; dropped_q = dropped_odd = 0
    for r in P:
        for w in r['line_words'].split():
            if '?' in w: dropped_q += 1; continue
            if not re.fullmatch(r'[a-z]+', w): dropped_odd += 1; continue
            words.append(w)
    return words, dict(lines=len(P), dropped_unread=dropped_q, dropped_weirdo=dropped_odd)

MERGES = [('cfh', 'F'), ('ckh', 'K'), ('cph', 'P'), ('cth', 'T'), ('ch', 'C'), ('sh', 'S'),
          ('iiin', 'N'), ('iin', 'M'), ('in', 'I'), ('eee', '3'), ('ee', 'E')]
def merge_glyphs(w):
    for a, b in MERGES: w = w.replace(a, b)
    return w

def gutenberg_body(txt):
    s = txt.find('*** START OF'); e = txt.find('*** END OF')
    if s >= 0: txt = txt[txt.find('\n', s) + 1:]
    if e >= 0: txt = txt[:e]
    return txt

def tokenize(txt):
    txt = unicodedata.normalize('NFC', txt.lower())
    return re.findall(r'[^\W\d_]+', txt)   # runs of Unicode letters

def load_lang(lang, n, skip=2000):
    # corp_la_50280 is Meissner's bilingual "Latin Phrase-Book" (half English) -> excluded
    files = [f for f in sorted(CORP.glob(f'corp_{lang}_*.txt')) if f.name != 'corp_la_50280.txt'] if lang != 'it' else [IT_FILE]
    toks_per = []
    for f in files:
        t = f.read_text(encoding='utf-8', errors='replace')
        if lang != 'it': t = gutenberg_body(t)
        toks_per.append(tokenize(t)[skip:])
    share = math.ceil(n / len(files)); out = []
    for t in toks_per: out.extend(t[:share])
    # if some file was short, top up from the longest
    if len(out) < n:
        longest = max(toks_per, key=len); out.extend(longest[share:share + n - len(out)])
    return out[:n], [f.name for f in files]

# ----------------------------------------------------------------------------- statistics
def entropy(counter):
    n = sum(counter.values()); return -sum(c / n * LOG2(c / n) for c in counter.values())

def h1h2(words, space):
    """words: list of tuples of symbols. Returns (h0, h1, h2, nsym, ntok)."""
    if space:
        stream = []
        for w in words: stream.extend(w); stream.append(' ')
    else:
        stream = [s for w in words for s in w]
    uni = collections.Counter(stream); bi = collections.Counter(zip(stream, stream[1:]))
    H1 = entropy(uni); Hbi = entropy(bi)
    return dict(h0=LOG2(len(uni)), h1=H1, h2=Hbi - H1, nsym=len(uni), nstream=len(stream))

def positional(words, minc=20):
    pos = collections.defaultdict(collections.Counter); tot = collections.Counter()
    for w in words:
        L = len(w)
        for i, s in enumerate(w):
            c = 'single' if L == 1 else 'initial' if i == 0 else 'final' if i == L - 1 else 'medial'
            pos[s][c] += 1; tot[s] += 1
    syms = [s for s in tot if tot[s] >= minc]
    N = sum(tot[s] for s in syms)
    # mutual information I(S;Pos)
    pc = collections.Counter()
    for s in syms: pc.update(pos[s])
    mi = 0.0
    for s in syms:
        for c, k in pos[s].items():
            p = k / N; mi += p * LOG2(p / ((tot[s] / N) * (pc[c] / N)))
    def frac(s, cls): return pos[s][cls] / tot[s]
    detail = {s: dict(n=tot[s], initial=round(frac(s, 'initial'), 3), medial=round(frac(s, 'medial'), 3),
                      final=round(frac(s, 'final'), 3), single=round(frac(s, 'single'), 3)) for s in syms}
    def cnt(th, cls): return sum(1 for s in syms if pos[s][cls] / tot[s] >= th)
    def never(cls): return sum(1 for s in syms if pos[s][cls] == 0)
    return dict(n_symbols=len(syms), mi_symbol_position_bits=round(mi, 4),
                ge90_initial=cnt(.9, 'initial'), ge90_final=cnt(.9, 'final'), ge90_medial=cnt(.9, 'medial'),
                only_initial=cnt(1.0, 'initial'), only_final=cnt(1.0, 'final'),
                never_initial=never('initial'), never_final=never('final'),
                frac_types_ge90_any=round(sum(1 for s in syms if max(pos[s][c] / tot[s] for c in ('initial', 'medial', 'final')) >= .9) / len(syms), 3),
                detail=detail)

def zipf_slope(freqs, maxrank=1000):
    fs = sorted(freqs, reverse=True)[:maxrank]
    xs = [LOG2(i + 1) for i in range(len(fs))]; ys = [LOG2(f) for f in fs]
    mx = sum(xs) / len(xs); my = sum(ys) / len(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)

def word_stats(words):
    c = collections.Counter(words); n = len(words)
    lens = [len(w) for w in words]; m = sum(lens) / n
    sd = math.sqrt(sum((l - m) ** 2 for l in lens) / n)
    fs = sorted(c.values(), reverse=True); cum = 0; k50 = k90 = None
    for i, f in enumerate(fs):
        cum += f
        if k50 is None and cum >= .5 * n: k50 = i + 1
        if k90 is None and cum >= .9 * n: k90 = i + 1; break
    return dict(tokens=n, types=len(c), ttr=round(len(c) / n, 4), hapax=sum(1 for v in c.values() if v == 1),
                hapax_frac_types=round(sum(1 for v in c.values() if v == 1) / len(c), 4),
                hapax_frac_tokens=round(sum(1 for v in c.values() if v == 1) / n, 4),
                mean_len=round(m, 3), sd_len=round(sd, 3), zipf_slope=round(zipf_slope(c.values()), 3),
                types_for_50pct=k50, types_for_90pct=k90, word_h1=round(entropy(c), 3),
                top10=[w for w, _ in c.most_common(10)])

def full_profile(words):
    t = [tuple(w) for w in words]
    return dict(nospace=h1h2(t, False), space=h1h2(t, True), pos=positional(t), words=word_stats(words))

def rnd(d, k=3):
    if isinstance(d, float): return round(d, k)
    if isinstance(d, dict): return {a: rnd(b, k) for a, b in d.items()}
    if isinstance(d, list): return [rnd(b, k) for b in d]
    return d

# ----------------------------------------------------------------------------- BPE
def bpe_trajectory(words, steps=12):
    seqs = [list(w) for w in words]; traj = []
    def snap(step, merged):
        t = [tuple(s) for s in seqs]
        a = h1h2(t, False); b = h1h2(t, True)
        traj.append(dict(step=step, merge=merged, nsym=a['nsym'], h1_nospace=round(a['h1'], 3), h2_nospace=round(a['h2'], 3),
                         h1_space=round(b['h1'], 3), h2_space=round(b['h2'], 3),
                         mean_word_len=round(sum(len(s) for s in seqs) / len(seqs), 3),
                         perplexity_h1=round(2 ** a['h1'], 2)))
    snap(0, None)
    for k in range(1, steps + 1):
        pc = collections.Counter()
        for s in seqs: pc.update(zip(s, s[1:]))
        (x, y), f = pc.most_common(1)[0]; xy = x + y
        for s in seqs:
            i = 0
            while i < len(s) - 1:
                if s[i] == x and s[i + 1] == y: s[i:i + 2] = [xy]
                i += 1
        snap(k, f'{x}+{y} ({f})')
    return traj

# ----------------------------------------------------------------------------- abjad
VOW = set('aeiou')
def is_vowel(ch):
    base = unicodedata.normalize('NFD', ch)[0]
    return base in VOW

def devowel(words, keep_initial=False):
    out = []
    for w in words:
        if keep_initial: nw = w[0] + ''.join(c for c in w[1:] if not is_vowel(c))
        else: nw = ''.join(c for c in w if not is_vowel(c))
        if nw: out.append(nw)
    return out

# ----------------------------------------------------------------------------- syllables
def syllabify(w):
    """Crude max-onset syllabifier on letters: nucleus = maximal vowel run; single interior consonant
    goes to next syllable; of 2+ interior consonants the first stays in the coda."""
    groups = re.findall(r'[^aeiouyäöüàèéìòùâêîôûëïœæøå]+|[aeiouyäöüàèéìòùâêîôûëïœæøå]+', w)
    isv = [is_vowel(g[0]) or g[0] in 'yäöüàèéìòùâêîôûëïœæøå' for g in groups]
    if not any(isv): return [w]
    syls = []; cur = ''
    for i, g in enumerate(groups):
        if isv[i]:
            cur += g
            # decide coda from following consonant cluster
            if i + 1 < len(groups) and not isv[i + 1]:
                nxt = groups[i + 1]
                if i + 2 < len(groups):   # interior cluster
                    coda = nxt[:-1] if len(nxt) > 1 else ''
                    cur += coda; syls.append(cur); cur = nxt[len(coda):]
                else:                     # final cluster
                    cur += nxt; syls.append(cur); cur = ''
            else:
                syls.append(cur); cur = ''
        else:
            if i == 0: cur += g
    if cur: syls.append(cur)
    return syls

# ----------------------------------------------------------------------------- info budget
class WBBigram:
    def __init__(self, words):
        self.uni = collections.Counter(words); self.N = len(words)
        self.bi = collections.defaultdict(collections.Counter)
        for a, b in zip(['<s>'] + words[:-1], words): self.bi[a][b] += 1
        self.bin = {a: sum(c.values()) for a, c in self.bi.items()}
        self.T1 = len(self.uni)
        # char bigram for unknown-word spelling (with end symbol), add-one over training alphabet
        self.cb = collections.defaultdict(collections.Counter); self.alpha = set()
        for w in self.uni:
            for a, b in zip('^' + w, w + '$'): self.cb[a][b] += 1; self.alpha.add(b)
        self.alpha.add('$'); self.cbn = {a: sum(c.values()) for a, c in self.cb.items()}
    def p_uni(self, w):
        # Witten-Bell: known words get c/(N+T), unk mass T/(N+T) spread by spelling model
        if w in self.uni: return self.uni[w] / (self.N + self.T1)
        return (self.T1 / (self.N + self.T1)) * self.p_spell(w)
    def p_spell(self, w):
        p = 1.0; V = len(self.alpha) + 1
        for a, b in zip('^' + w, w + '$'):
            p *= (self.cb[a][b] + 1) / (self.cbn.get(a, 0) + V)
        return p
    def p(self, prev, w):
        pu = self.p_uni(w)
        if prev in self.bi:
            n = self.bin[prev]; t = len(self.bi[prev]); lam = n / (n + t)
            return lam * self.bi[prev][w] / n + (1 - lam) * pu
        return pu

def cv_bits(words, folds=10):
    n = len(words); bits = 0.0; unk_tokens = 0; unk_bits = 0.0
    for k in range(folds):
        lo, hi = k * n // folds, (k + 1) * n // folds
        test = words[lo:hi]; train = words[:lo] + words[hi:]
        m = WBBigram(train); prev = '<s>'
        for w in test:
            b = -LOG2(m.p(prev, w)); bits += b
            if w not in m.uni: unk_tokens += 1; unk_bits += b
            prev = w
    chars = sum(len(w) for w in words)
    return dict(total_bits=round(bits), bits_per_word=round(bits / n, 3), bits_per_char=round(bits / chars, 3),
                chars=chars, unk_tokens=unk_tokens, unk_frac=round(unk_tokens / n, 4), unk_bits=round(unk_bits),
                known_bits_per_word=round((bits - unk_bits) / max(1, n - unk_tokens), 3))

def compress_bits(words):
    s = ' '.join(words).encode('utf-8')
    return dict(raw_bytes=len(s), lzma_bits=8 * len(lzma.compress(s, preset=9 | lzma.PRESET_EXTREME)),
                bz2_bits=8 * len(bz2.compress(s, 9)))

def word_bigram_insample(words):
    c1 = collections.Counter(words); c2 = collections.Counter(zip(words, words[1:]))
    return dict(H1_word=round(entropy(c1), 3), H2_word_cond=round(entropy(c2) - entropy(collections.Counter(words[:-1])), 3))

# ----------------------------------------------------------------------------- main
def main():
    out = {}
    vw, vinfo = load_voynich(); N = len(vw)
    vm = [merge_glyphs(w) for w in vw]
    out['sample'] = dict(voynich=vinfo | dict(tokens=N, types=len(set(vw))), match_tokens=N)
    langs = {}; files = {}
    for lg in LANGS:
        langs[lg], files[lg] = load_lang(lg, N)
    out['sample']['lang_files'] = files
    out['sample']['lang_tokens'] = {lg: len(v) for lg, v in langs.items()}

    # ---- (1) substitution / transposition: h1, h2, positional constraints
    prof = {'voy_raw': full_profile(vw), 'voy_mrg': full_profile(vm)}
    for lg in LANGS: prof[lg] = full_profile(langs[lg])
    # Currier A / B split for reference
    rows = list(csv.DictReader(open(HERE / 'data' / 'ZL3b-n.words.tsv', encoding='utf-8'), delimiter='\t'))
    for L in 'AB':
        ws = [w for r in rows if r['locus_type'] == 'P' and r['lang'] == L for w in r['line_words'].split()
              if '?' not in w and re.fullmatch(r'[a-z]+', w)]
        t = [tuple(w) for w in ws]
        prof[f'voy_raw_currier{L}'] = dict(nospace=h1h2(t, False), space=h1h2(t, True), tokens=len(ws))
    out['t1_profiles'] = rnd(prof)

    # ---- (2) BPE trajectory
    out['t2_bpe'] = dict(voynich_raw=bpe_trajectory(vw), voynich_mrg=bpe_trajectory(vm),
                         latin=bpe_trajectory(langs['la']), german=bpe_trajectory(langs['de']))
    # extended: 40 merges, keep every 4th snapshot, to see whether h1-h2 gap ever closes
    ext = {}
    for name, ws in [('voynich_raw', vw), ('latin', langs['la']), ('italian', langs['it'])]:
        tr = bpe_trajectory(ws, 40)
        ext[name] = [dict(r, gap=round(r['h1_nospace'] - r['h2_nospace'], 3), ratio=round(r['h2_nospace'] / r['h1_nospace'], 3)) for r in tr if r['step'] % 4 == 0]
    out['t2_bpe_extended'] = ext

    # ---- (3) abjad
    ab = {}
    for lg in ('la', 'it', 'de'):
        dv = devowel(langs[lg]); dvi = devowel(langs[lg], keep_initial=True)
        ab[lg + '_novowel'] = full_profile(dv); ab[lg + '_novowel_keepinitial'] = full_profile(dvi)
        ab[lg + '_novowel']['tokens_after'] = len(dv)
    for k in ab: ab[k]['pos'].pop('detail', None)
    out['t3_abjad'] = rnd(ab)

    # ---- (4) nulls: remove top-5 glyphs individually
    def null_test(words, label):
        cnt = collections.Counter(ch for w in words for ch in w); top = [s for s, _ in cnt.most_common(5)]
        base = h1h2([tuple(w) for w in words], False); res = dict(base=dict(h1=round(base['h1'], 3), h2=round(base['h2'], 3), nsym=base['nsym']), removed={})
        for g in top:
            ww = [tuple(c for c in w if c != g) for w in words]; ww = [w for w in ww if w]
            a = h1h2(ww, False); b = h1h2(ww, True)
            res['removed'][g] = dict(glyph_share=round(cnt[g] / sum(cnt.values()), 4), h1_nospace=round(a['h1'], 3), h2_nospace=round(a['h2'], 3),
                                     h2_space=round(b['h2'], 3), nsym=a['nsym'], mean_word_len=round(sum(len(w) for w in ww) / len(ww), 3),
                                     delta_h2=round(a['h2'] - base['h2'], 3))
        # cumulative
        cur = words; cum = []
        for g in top:
            cur = [''.join(c for c in w if c != g) for w in cur]; cur = [w for w in cur if w]
            a = h1h2([tuple(w) for w in cur], False); cum.append(dict(removed_so_far=top[:top.index(g) + 1], h1=round(a['h1'], 3), h2=round(a['h2'], 3), nsym=a['nsym'], mean_word_len=round(sum(len(w) for w in cur) / len(cur), 3), stream_kept=round(a['nstream'] / base['nstream'], 3), tokens_left=len(cur)))
        res['cumulative'] = cum
        return res
    out['t4_nulls'] = dict(voynich_raw=null_test(vw, 'raw'), voynich_mrg=null_test(vm, 'mrg'), latin=null_test(langs['la'], 'la'), german=null_test(langs['de'], 'de'))

    # ---- (5) word-as-letter / syllable
    t5 = dict(voynich=dict(P_tokens=N, P_types=len(set(vw)), P_hapax=prof['voy_raw']['words']['hapax'],
                           all_loci_tokens=None, all_loci_types=None))
    allw = [w for r in rows for w in r['line_words'].split() if '?' not in w]
    t5['voynich']['all_loci_tokens'] = len(allw); t5['voynich']['all_loci_types'] = len(set(allw))
    allw2 = [w for w in allw if re.fullmatch(r'[a-z]+', w)]
    t5['voynich']['all_loci_types_az_only'] = len(set(allw2))
    # Heaps growth curve for Voynich and languages
    def heaps(words, pts=(5000, 10000, 20000, 30000)):
        seen = set(); res = {};
        for i, w in enumerate(words, 1):
            seen.add(w)
            if i in pts: res[i] = len(seen)
        res[len(words)] = len(seen); return res
    t5['heaps'] = {'voy_raw': heaps(vw)} | {lg: heaps(langs[lg]) for lg in LANGS}
    inv = {}
    for lg in ('la', 'it', 'de', 'en'):
        letters = collections.Counter(ch for w in langs[lg] for ch in w)
        syl = collections.Counter(s for w in langs[lg] for s in syllabify(w))
        inv[lg] = dict(letter_types=len(letters), letter_types_ge20=sum(1 for v in letters.values() if v >= 20),
                       syllable_tokens=sum(syl.values()), syllable_types=len(syl), syllable_types_ge2=sum(1 for v in syl.values() if v >= 2),
                       syllables_for_90pct=(lambda fs: next(i + 1 for i, c in enumerate(__import__('itertools').accumulate(fs)) if c >= .9 * sum(fs)))(sorted(syl.values(), reverse=True)),
                       word_types=len(set(langs[lg])), syl_per_word=round(sum(syl.values()) / len(langs[lg]), 3),
                       example_syllabification=[syllabify(w) for w in langs[lg][100:105]])
    t5['inventories'] = inv
    out['t5_word_types'] = t5

    # ---- (6) information budget
    t6 = {}
    for name, ws in [('voy_raw', vw), ('voy_mrg', vm)] + [(lg, langs[lg]) for lg in LANGS]:
        t6[name] = cv_bits(ws) | compress_bits(ws) | word_bigram_insample(ws)
    # capacity: how many Latin chars/words could the Voynich bits encode at Latin's rate
    for lg in ('la', 'it', 'de'):
        t6[f'capacity_vs_{lg}'] = dict(
            voy_raw_bits_over_lang_bits=round(t6['voy_raw']['total_bits'] / t6[lg]['total_bits'], 3),
            equiv_plaintext_words_bigram=round(t6['voy_raw']['total_bits'] / t6[lg]['bits_per_word']),
            equiv_plaintext_chars_bigram=round(t6['voy_raw']['total_bits'] / t6[lg]['bits_per_char']),
            lzma_ratio=round(t6['voy_raw']['lzma_bits'] / t6[lg]['lzma_bits'], 3),
            equiv_plaintext_chars_lzma=round(t6['voy_raw']['lzma_bits'] / (t6[lg]['lzma_bits'] / t6[lg]['chars'])))
    out['t6_info_budget'] = t6

    (RES / 'a5.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')
    write_md(out)

def write_md(o):
    L = []; A = L.append
    A('# a5: cipher-class feasibility tests (ZL3b paragraph text)\n')
    s = o['sample']; A(f"Sample: {s['voynich']['tokens']} Voynich P-locus tokens ({s['voynich']['types']} types), {s['voynich']['dropped_unread']} unread + {s['voynich']['dropped_weirdo']} weirdo tokens dropped; each language sample = {s['match_tokens']} tokens.\n")
    A('## (1) Letter-level profile (invariant under 1:1 substitution)\n')
    A('| text | nsym | h1 nosp | h2 nosp | h1 sp | h2 sp | h1-h2 | I(sym;pos) | >=90% one pos | 100% one pos (init/final) | never init | never final | mean wlen | types | hapax% |')
    A('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    for k, p in o['t1_profiles'].items():
        if 'pos' not in p:
            A(f"| {k} | {p['nospace']['nsym']} | {p['nospace']['h1']} | {p['nospace']['h2']} | {p['space']['h1']} | {p['space']['h2']} | {round(p['nospace']['h1']-p['nospace']['h2'],3)} | | | | | | | | |"); continue
        q = p['pos']; w = p['words']
        A(f"| {k} | {p['nospace']['nsym']} | {p['nospace']['h1']} | {p['nospace']['h2']} | {p['space']['h1']} | {p['space']['h2']} | {round(p['nospace']['h1']-p['nospace']['h2'],3)} | {q['mi_symbol_position_bits']} | {q['ge90_initial']}/{q['ge90_medial']}/{q['ge90_final']} of {q['n_symbols']} | {q['only_initial']}/{q['only_final']} | {q['never_initial']} | {q['never_final']} | {w['mean_len']} | {w['types']} | {round(100*w['hapax_frac_types'],1)} |")
    A('\nPer-symbol position shares (symbols with >=20 occurrences), Voynich raw EVA:\n')
    d = o['t1_profiles']['voy_raw']['pos']['detail']
    A('| sym | n | initial | medial | final | single |'); A('|---|---|---|---|---|---|')
    for sname, v in sorted(d.items(), key=lambda kv: -kv[1]['n']): A(f"| {sname} | {v['n']} | {v['initial']} | {v['medial']} | {v['final']} | {v['single']} |")
    A('\n## (2) Greedy pair-merge (BPE) trajectory\n')
    for k, tr in o['t2_bpe'].items():
        A(f'\n### {k}\n'); A('| step | merge (count) | nsym | h1 nosp | h2 nosp | h2 sp | mean wlen | 2^h1 |'); A('|---|---|---|---|---|---|---|---|')
        for r in tr: A(f"| {r['step']} | {r['merge']} | {r['nsym']} | {r['h1_nospace']} | {r['h2_nospace']} | {r['h2_space']} | {r['mean_word_len']} | {r['perplexity_h1']} |")
    A('\nExtended BPE (every 4th step to 40): step: nsym / h1 / h2 nosp / h2 sp / gap h1-h2 / ratio h2/h1 / mean wlen\n')
    for k, tr in o['t2_bpe_extended'].items():
        A(f"- {k}: " + '; '.join(f"{r['step']}: {r['nsym']} / {r['h1_nospace']} / {r['h2_nospace']} / {r['h2_space']} / {r['gap']} / {r['ratio']} / {r['mean_word_len']}" for r in tr))
    A('\n## (3) Abjad (vowels removed)\n')
    A('| text | nsym | h1 nosp | h2 nosp | h2 sp | mean wlen | types | hapax% | zipf | I(sym;pos) |'); A('|---|---|---|---|---|---|---|---|---|---|')
    for k in ('voy_raw', 'voy_mrg', 'la', 'it', 'de'):
        p = o['t1_profiles'][k]; A(f"| {k} | {p['nospace']['nsym']} | {p['nospace']['h1']} | {p['nospace']['h2']} | {p['space']['h2']} | {p['words']['mean_len']} | {p['words']['types']} | {round(100*p['words']['hapax_frac_types'],1)} | {p['words']['zipf_slope']} | {p['pos']['mi_symbol_position_bits']} |")
    for k, p in o['t3_abjad'].items():
        A(f"| {k} | {p['nospace']['nsym']} | {p['nospace']['h1']} | {p['nospace']['h2']} | {p['space']['h2']} | {p['words']['mean_len']} | {p['words']['types']} | {round(100*p['words']['hapax_frac_types'],1)} | {p['words']['zipf_slope']} | {p['pos']['mi_symbol_position_bits']} |")
    A('\n## (4) Null-glyph test: remove each of the 5 most frequent glyphs\n')
    for k, r in o['t4_nulls'].items():
        A(f"\n### {k}: base h1={r['base']['h1']} h2={r['base']['h2']} nsym={r['base']['nsym']}\n"); A('| removed | share | h1 | h2 nosp | delta h2 | h2 sp | nsym | mean wlen |'); A('|---|---|---|---|---|---|---|---|')
        for g, v in r['removed'].items(): A(f"| {g} | {v['glyph_share']} | {v['h1_nospace']} | {v['h2_nospace']} | {v['delta_h2']} | {v['h2_space']} | {v['nsym']} | {v['mean_word_len']} |")
        A('cumulative: ' + '; '.join(f"-{''.join(c['removed_so_far'])}: h1={c['h1']} h2={c['h2']} wlen={c['mean_word_len']} stream_kept={c['stream_kept']}" for c in r['cumulative']))
    A('\n## (5) Word types vs letters / syllables / words\n')
    t = o['t5_word_types']; A(f"Voynich: P tokens {t['voynich']['P_tokens']}, P types {t['voynich']['P_types']}, hapax {t['voynich']['P_hapax']}; all loci tokens {t['voynich']['all_loci_tokens']}, types {t['voynich']['all_loci_types']} (a-z only: {t['voynich']['all_loci_types_az_only']}).\n")
    A('Heaps growth (types after n tokens): ' + json.dumps(t['heaps']) + '\n')
    A('| lang | letter types (>=20) | syllable tokens | syllable types | syl types >=2 | syl for 90% | syl/word | word types |'); A('|---|---|---|---|---|---|---|---|')
    for lg, v in t['inventories'].items(): A(f"| {lg} | {v['letter_types']} ({v['letter_types_ge20']}) | {v['syllable_tokens']} | {v['syllable_types']} | {v['syllable_types_ge2']} | {v['syllables_for_90pct']} | {v['syl_per_word']} | {v['word_types']} |")
    A('\n## (6) Information budget (10-fold CV Witten-Bell word bigram + spelling model; lzma)\n')
    A('| text | chars | total bits | bits/word | bits/char | unk frac | known bits/word | lzma bits | bz2 bits | H1 word | H2 word (in-sample) |'); A('|---|---|---|---|---|---|---|---|---|---|---|')
    for k, v in o['t6_info_budget'].items():
        if k.startswith('capacity'): continue
        A(f"| {k} | {v['chars']} | {v['total_bits']} | {v['bits_per_word']} | {v['bits_per_char']} | {v['unk_frac']} | {v['known_bits_per_word']} | {v['lzma_bits']} | {v['bz2_bits']} | {v['H1_word']} | {v['H2_word_cond']} |")
    for k, v in o['t6_info_budget'].items():
        if k.startswith('capacity'): A(f"- {k}: {json.dumps(v)}")
    (RES / 'a5.md').write_text('\n'.join(L), encoding='utf-8')

if __name__ == '__main__':
    main()
