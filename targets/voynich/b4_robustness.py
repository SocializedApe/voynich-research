"""b4_robustness.py -- Task b4: robustness items listed as 'not computed' in NOTES.md (sections 4.1, 4.7, 8).

Pure Python 3.12, no third-party packages.  Outputs results/b4.json and results/b4.md.

WHAT IS COMPUTED (method choices are explicit; every number is unvalidated until reviewed)
------------------------------------------------------------------------------------------
Data
  * ZL3b-n.words.tsv, locus_type P only, words containing '?' dropped, EVA words must match [a-z]+
    (identical to a1_charstats.py).  Subsets ALL (A + B + lang '?'), A, B.  Cross-checks on RF1b-er (EVA)
    and GC2a-n (v101; words containing '@' dropped, every character a symbol).
  * Alphabets: raw (one EVA character = one symbol) and merge2 from a1
    (ckh cth cph cfh ch sh iiin iin eee ee aiin ain in qo; greedy longest match).
  * Languages: single Gutenberg books la 33849 (Confessiones; '[Sidenote: ...]' blocks removed),
    de 50285, en 1342, fr 62215, da 36942, and targets/vatican5/corpus_it.txt.  Header/footer stripped at
    '*** START OF' / '*** END OF'.  Normalisation: lower case; str.isalpha() characters are letters,
    everything else a word break.  'folded' = diacritics stripped (NFKD, combining marks removed,
    ss/ae/oe/o substitutions for sharp s, ae, oe, o-slash) so the alphabet is the 26 Latin letters plus
    whatever survives; 'unfolded' keeps accented letters as distinct symbols (as in a1).  The folded
    variant is the primary one (NOTES quotes the folded 3.32 floor); unfolded h1/h2 are given alongside.
    Samples are the first N letters (whole words) of the book, N = ZL ALL letters and N = ZL A letters.

(1) Entropies  h_k = H(X_n | X_{n-k+1..n-1}) = H(k-gram) - H((k-1)-gram context), plug-in, log2, k = 1..4,
    with spaces (words joined by a space symbol; line ends are spaces) and without (words concatenated,
    n-grams span word boundaries).  Bias diagnostics: Miller-Madow (each block entropy gets
    +(m-1)/(2 N ln 2), m = occupied bins) and the same plug-in estimate on each half of the sample (first
    half / second half of the word list).  h4 is reported for every sample but is not trustworthy where
    the half-sample value differs from the full one by more than a few hundredths (the table shows this).

(2) Per-hand statistics for Davis's hands 1-5 as given in the IVTFF headers, split by Currier language:
    h1, h2 (raw, no spaces), mean word length, hapax type fraction, Zipf slope (OLS of log10 freq on
    log10 rank, ranks 1..min(1000, types); as a2), -edy and qo- token rates.  Cells with fewer than 200
    tokens are omitted; hapax and Zipf are size dependent, so cells with >= 10,000 tokens are also given
    on their first 10,000 tokens.  A folio-permutation test of hand 2 against hand 3 inside Currier B is
    added so that 'same language, different scribe' has a p-value.

(3) Bootstrap: folios resampled with replacement (500 resamples, random.Random(2026)); statistics are
    recomputed from per-folio counts (bigrams do not cross folio boundaries, which drops about one bigram
    in a thousand).  A delete-one-folio jackknife SE is given alongside, because resampling folios with
    replacement duplicates folios and so turns hapaxes into dis legomena: the bootstrap is invalid for
    hapax fraction and Zipf slope and the jackknife interval is the one to use for those two.
    Reported: percentile 95% interval and bootstrap SE for h2 (raw, no spaces), Zipf
    slope (ranks 1-1000), hapax type fraction, and the a3 'pair-viol frac' (token-weighted share of
    within-word ordered glyph pairs that are out of order under the best linear glyph order; the 0.160 of
    NOTES 4.4) both with the glyph order fixed from the full data and with the order re-derived on each
    resample (a3 best_order heuristic, 2 restarts).  Rigidity uses a3's merge (benches, bench gallows,
    e-groups, i-groups) and a3's letter filter.

(4) A versus B: statistic = value(A) - value(B) for h2 (raw, no spaces), mean word length, -edy rate,
    qo- rate, with folios as units and the folio's page language as its label (lang '?' folios excluded).
    (i) unrestricted: 2,000 random relabellings of the folios; (ii) stratified by hand: labels permuted
    only within a hand.  Because every hand except hand 3 writes one language only, (ii) can only move
    labels among hand-3 folios; the number of movable folios is reported.  p is two sided,
    (1 + #{|perm| >= |obs|}) / (1 + n_perm).

(5) Token predictability (after Rozanova & Temerev 2026, whose exact estimator was not available to
    this session; this is one reasonable reading of 'the information a word carries about the next').
    Word level:  (a) plug-in  I = H(w_i) + H(w_{i+1}) - H(w_i, w_{i+1}) on all consecutive token pairs of
    the stream, with a shuffle baseline (mean of 3 shuffles of the token order; plug-in MI is dominated
    by sample-size bias, and the shuffled value shows how much);  (b) held-out: the stream is split in
    two halves, a model is trained on one and scored on the other, both directions averaged.  Training
    hapaxes and test out-of-vocabulary tokens map to UNK.  Unigram: maximum likelihood.  Bigram:
    Witten-Bell interpolation P(b|a) = (c(a,b) + T(a) P(b)) / (c(a) + T(a)).  Then
    H(w) := CE_uni, H(w_{i+1}|w_i) := CE_bi, I := CE_uni - CE_bi, ratio := CE_bi / CE_uni, plus the same
    on a shuffled stream.  Glyph level: mutual information between the last glyph of a word and the
    first glyph of the next word (plug-in with shuffle baseline; the alphabet is small, so bias is
    small).  For ZL the pairs are also restricted to consecutive words on the same line.  Languages are
    cut to the ZL token count.

(6) The same h2 and predictability numbers on RF1b and GC2a.
"""
import os as _os  # local paths (the September 2026 scripts hard-coded another machine)
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_CORP = _os.path.join(_HERE, 'data', 'corpora')  # corp_<lang>_<gutenberg id>.txt, see fetch_corpora.py
_EXT = _os.path.join(_HERE, 'data', 'external')  # third-party data (Naibbe, Gaskell & Bowern)
_IT = _os.path.join(_CORP, 'corpus_it.txt')  # vatican5 OCR corpus from the September sample's first words (fetch_corpora.py)
import csv, math, json, random, collections, pathlib, re, time, unicodedata, sys

HERE = pathlib.Path(_HERE)
DATA = HERE / "data"
RES = HERE / "results"
RES.mkdir(exist_ok=True)
CORP = pathlib.Path(_CORP)
IT_CORPUS = pathlib.Path(_IT)

N_BOOT = 500
N_PERM = 2000
N_PERM_HAND = 1000
SEED = 2026
T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:6.1f}s]", *a, flush=True)


# ----------------------------------------------------------------------------- tokenisers (from a1)
MERGE1 = ["ckh", "cth", "cph", "cfh", "ch", "sh", "iiin", "iin", "eee", "ee"]
MERGE2 = MERGE1 + ["aiin", "ain", "in", "qo"]


def make_tokenizer(tokens):
    toks = sorted(set(tokens), key=len, reverse=True)
    maxlen = max(len(t) for t in toks)
    tokset = set(toks)

    def tok(word):
        out = []
        i = 0
        n = len(word)
        while i < n:
            for L in range(min(maxlen, n - i), 1, -1):
                if word[i:i + L] in tokset:
                    out.append(word[i:i + L])
                    i += L
                    break
            else:
                out.append(word[i])
                i += 1
        return out
    return tok


tok_raw = lambda w: list(w)
tok_m2 = make_tokenizer(MERGE2)

# a3 merge for rigidity
EVA_OK = set('acdefghiklmnopqrsty')
A3_RULES = [('ckh', 'K'), ('cth', 'T'), ('cph', 'P'), ('cfh', 'F'), ('ch', 'C'), ('sh', 'S'),
            ('eee', 'E'), ('ee', 'E'), ('iiin', 'N'), ('iin', 'N'), ('in', 'N')]
_a3cache = {}


def merge_a3(w):
    m = _a3cache.get(w)
    if m is None:
        m = w
        for a, b in A3_RULES:
            m = m.replace(a, b)
        _a3cache[w] = m
    return m

# ----------------------------------------------------------------------------- entropy helpers


def H(counter):
    n = sum(counter.values())
    if not n:
        return 0.0
    return math.log2(n) - sum(c * math.log2(c) for c in counter.values()) / n


def H_mm(counter):
    n = sum(counter.values())
    if not n:
        return 0.0
    m = sum(1 for c in counter.values() if c)
    return H(counter) + (m - 1) / (2 * n * math.log(2))


def Hd(vec):
    n = sum(vec)
    if not n:
        return 0.0
    return math.log2(n) - sum(c * math.log2(c) for c in vec if c) / n


def ngrams(stream, k):
    if k == 1:
        return collections.Counter(stream)
    return collections.Counter(zip(*[stream[i:] for i in range(k)]))


def cond_entropies(stream, kmax=4):
    """h_k for k=1..kmax, plug-in and Miller-Madow."""
    out = {}
    prev = None
    for k in range(1, kmax + 1):
        ck = ngrams(stream, k)
        if k == 1:
            out[k] = {"plug": H(ck), "mm": H_mm(ck)}
        else:
            ctx = ngrams(stream[:-1], k - 1)
            out[k] = {"plug": H(ck) - H(ctx), "mm": H_mm(ck) - H_mm(ctx), "bins": len(ck)}
        prev = ck
    return out


def streams(words_tok):
    nosp = [s for w in words_tok for s in w]
    sp = []
    for w in words_tok:
        sp.extend(w)
        sp.append(" ")
    if sp:
        sp.pop()
    return sp, nosp


def entropy_block(words_tok, kmax=4):
    """returns {'with_spaces': {...}, 'without_spaces': {...}} with h1..h4 plug, mm, half1, half2."""
    res = {}
    n = len(words_tok)
    halves = [words_tok[:n // 2], words_tok[n // 2:]]
    for name, idx in [("with_spaces", 0), ("without_spaces", 1)]:
        full = cond_entropies(streams(words_tok)[idx], kmax)
        h1 = cond_entropies(streams(halves[0])[idx], kmax)
        h2 = cond_entropies(streams(halves[1])[idx], kmax)
        d = {"n_symbols": len(streams(words_tok)[idx]), "inventory": len(set(streams(words_tok)[idx]))}
        for k in range(1, kmax + 1):
            d[f"h{k}"] = full[k]["plug"]
            d[f"h{k}_mm"] = full[k]["mm"]
            d[f"h{k}_half1"] = h1[k]["plug"]
            d[f"h{k}_half2"] = h2[k]["plug"]
            if k > 1:
                d[f"h{k}_bins"] = full[k]["bins"]
        res[name] = d
    return res

# ----------------------------------------------------------------------------- word stats


def ols_slope(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / sxx if sxx else float("nan")


def zipf_slope_from_freqs(freqs, R=1000):
    r = min(R, len(freqs))
    xs = [math.log10(i + 1) for i in range(r)]
    ys = [math.log10(freqs[i]) for i in range(r)]
    return ols_slope(xs, ys)


def word_stats(tokens):
    c = collections.Counter(tokens)
    freqs = sorted(c.values(), reverse=True)
    hap = sum(1 for v in freqs if v == 1)
    return {"tokens": len(tokens), "types": len(c), "hapax_type_frac": hap / len(c), "hapax_token_frac": hap / len(tokens),
            "zipf_slope_1_1000": zipf_slope_from_freqs(freqs), "ranks_used": min(1000, len(freqs)),
            "H_word_bits": H(c), "mean_word_len": sum(len(t) for t in tokens) / len(tokens),
            "edy_rate": sum(1 for t in tokens if t.endswith("edy")) / len(tokens),
            "qo_rate": sum(1 for t in tokens if t.startswith("qo")) / len(tokens)}

# ----------------------------------------------------------------------------- loading


def load_lines(fname, alphabet="eva"):
    lines = []
    with open(DATA / fname, encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            if row["locus_type"] != "P":
                continue
            ws = []
            for w in row["line_words"].split():
                if "?" in w:
                    continue
                if alphabet == "eva":
                    if not re.fullmatch(r"[a-z]+", w):
                        continue
                else:
                    if "@" in w:
                        continue
                ws.append(w)
            if ws:
                lines.append({"folio": row["folio"], "line_id": row["line_id"], "lang": row["lang"],
                              "hand": row["hand"], "words": ws})
    return lines


def sel(lines, lang=None, hand=None):
    out = []
    for l in lines:
        if lang is not None and lang != "ALL" and l["lang"] != lang:
            continue
        if hand is not None and l["hand"] != hand:
            continue
        out.append(l)
    return out


def flat(lines):
    return [w for l in lines for w in l["words"]]

# ----------------------------------------------------------------------------- corpora


FOLD_MAP = {"ß": "ss", "æ": "ae", "œ": "oe", "ø": "o", "ð": "d", "þ": "th", "ł": "l"}


def fold(word):
    out = []
    for ch in word:
        if ch in FOLD_MAP:
            out.append(FOLD_MAP[ch])
            continue
        d = unicodedata.normalize("NFKD", ch)
        d = "".join(c for c in d if not unicodedata.combining(c))
        out.append(d if d else ch)
    return "".join(out)


def normalise(txt):
    txt = txt.lower()
    out = []
    cur = []
    for ch in txt:
        if ch.isalpha():
            cur.append(ch)
        elif cur:
            out.append("".join(cur))
            cur = []
    if cur:
        out.append("".join(cur))
    return out


def gutenberg(path, strip_sidenotes=False):
    txt = path.read_text(encoding="utf-8", errors="replace")
    i = txt.find("*** START OF")
    if i >= 0:
        txt = txt[txt.find("\n", i) + 1:]
    j = txt.find("*** END OF")
    if j >= 0:
        txt = txt[:j]
    if strip_sidenotes:
        txt = re.sub(r"\[Sidenote:.*?\]", " ", txt, flags=re.S)
    return normalise(txt)


def take_letters(words, n_letters):
    out = []
    n = 0
    for w in words:
        if n >= n_letters:
            break
        out.append(w)
        n += len(w)
    return out


LANG_FILES = {"la": ("corp_la_33849.txt", True), "de": ("corp_de_50285.txt", False), "en": ("corp_en_1342.txt", False),
              "fr": ("corp_fr_62215.txt", False), "da": ("corp_da_36942.txt", False)}


def load_languages():
    out = {}
    for lg, (fn, sn) in LANG_FILES.items():
        out[lg] = gutenberg(CORP / fn, sn)
    out["it"] = normalise(IT_CORPUS.read_text(encoding="utf-8", errors="replace")[:3_000_000])
    return out

# ----------------------------------------------------------------------------- predictability


def plugin_mi(pairs):
    a = collections.Counter(p[0] for p in pairs)
    b = collections.Counter(p[1] for p in pairs)
    ab = collections.Counter(pairs)
    return H(a) + H(b) - H(ab), H(b), H(ab) - H(a)


def word_pairs(seqs):
    """seqs: list of token sequences (one per unit within which adjacency counts). returns list of pairs."""
    pairs = []
    for s in seqs:
        pairs.extend(zip(s, s[1:]))
    return pairs


def heldout_bigram(train, test):
    """UNK-ified Witten-Bell bigram vs ML unigram; returns CE_uni, CE_bi (bits/token) over test positions 1..n-1."""
    c = collections.Counter(train)
    vocab = {w for w, k in c.items() if k >= 2}
    tr = [w if w in vocab else "<unk>" for w in train]
    te = [w if w in vocab else "<unk>" for w in test]
    uni = collections.Counter(tr)
    N = len(tr)
    big = collections.Counter(zip(tr, tr[1:]))
    ctx = collections.Counter(tr[:-1])
    followers = collections.defaultdict(set)
    for (a, b) in big:
        followers[a].add(b)
    T = {a: len(s) for a, s in followers.items()}
    ce_u = 0.0
    ce_b = 0.0
    n = 0
    for a, b in zip(te, te[1:]):
        pu = uni[b] / N
        ca = ctx.get(a, 0)
        ta = T.get(a, 0)
        if ca:
            pb = (big.get((a, b), 0) + ta * pu) / (ca + ta)
        else:
            pb = pu
        ce_u -= math.log2(pu)
        ce_b -= math.log2(pb)
        n += 1
    return ce_u / n, ce_b / n


def word_predictability(tokens, rng, n_shuf=3, line_seqs=None):
    """tokens: flat list in reading order. line_seqs: optional list of per-line sequences (within-line pairs)."""
    res = {"tokens": len(tokens), "types": len(set(tokens))}
    mi, hw, hc = plugin_mi(list(zip(tokens, tokens[1:])))
    res["plugin"] = {"I": mi, "H_w": hw, "H_cond": hc, "ratio": hc / hw}
    sh = []
    for _ in range(n_shuf):
        t = tokens[:]
        rng.shuffle(t)
        m, w, c = plugin_mi(list(zip(t, t[1:])))
        sh.append((m, w, c))
    res["plugin_shuffled"] = {"I": sum(s[0] for s in sh) / n_shuf, "H_cond": sum(s[2] for s in sh) / n_shuf,
                              "ratio": sum(s[2] / s[1] for s in sh) / n_shuf}
    res["plugin_excess_I"] = res["plugin"]["I"] - res["plugin_shuffled"]["I"]
    if line_seqs is not None:
        m, w, c = plugin_mi(word_pairs(line_seqs))
        res["plugin_within_line"] = {"I": m, "H_w": w, "H_cond": c, "ratio": c / w}
    # held-out
    n = len(tokens)
    h = n // 2
    a1, b1 = heldout_bigram(tokens[:h], tokens[h:])
    a2, b2 = heldout_bigram(tokens[h:], tokens[:h])
    ceu, ceb = (a1 + a2) / 2, (b1 + b2) / 2
    res["heldout"] = {"CE_uni": ceu, "CE_bi": ceb, "I": ceu - ceb, "ratio": ceb / ceu}
    sh = []
    for _ in range(n_shuf):
        t = tokens[:]
        rng.shuffle(t)
        a1, b1 = heldout_bigram(t[:h], t[h:])
        a2, b2 = heldout_bigram(t[h:], t[:h])
        sh.append(((a1 + a2) / 2, (b1 + b2) / 2))
    ceu_s = sum(s[0] for s in sh) / n_shuf
    ceb_s = sum(s[1] for s in sh) / n_shuf
    res["heldout_shuffled"] = {"CE_uni": ceu_s, "CE_bi": ceb_s, "I": ceu_s - ceb_s, "ratio": ceb_s / ceu_s}
    res["heldout_excess_I"] = res["heldout"]["I"] - res["heldout_shuffled"]["I"]
    return res


def glyph_boundary_mi(words_tok, rng, n_shuf=3, line_seqs=None):
    """MI between last glyph of word i and first glyph of word i+1."""
    def pairs_of(ws):
        return [(ws[i][-1], ws[i + 1][0]) for i in range(len(ws) - 1)]
    p = pairs_of(words_tok)
    mi, hb, hc = plugin_mi(p)
    ab = collections.Counter(p)
    mm = (len(ab) - 1) / (2 * len(p) * math.log(2)) - (len(set(x for x, _ in p)) - 1) / (2 * len(p) * math.log(2)) \
        - (len(set(y for _, y in p)) - 1) / (2 * len(p) * math.log(2))
    res = {"I": mi, "H_first": hb, "H_first_given_last": hc, "ratio": hc / hb, "I_mm": mi - mm, "pairs": len(p)}
    sh = []
    for _ in range(n_shuf):
        w = words_tok[:]
        rng.shuffle(w)
        sh.append(plugin_mi(pairs_of(w))[0])
    res["I_shuffled"] = sum(sh) / n_shuf
    res["I_excess"] = mi - res["I_shuffled"]
    if line_seqs is not None:
        p2 = []
        for s in line_seqs:
            p2.extend(pairs_of(s))
        m2, hb2, hc2 = plugin_mi(p2)
        res["within_line"] = {"I": m2, "ratio": hc2 / hb2, "pairs": len(p2)}
    return res

# ----------------------------------------------------------------------------- a3 rigidity (order + violations)


def precedence_dense(typec, idx, M):
    W = [0] * (M * M)
    for w, c in typec.items():
        L = len(w)
        for i in range(L):
            x = idx[w[i]]
            for j in range(i + 1, L):
                if w[i] != w[j]:
                    W[x * M + idx[w[j]]] += c
    return W


def best_order_dense(W, M, restarts=2, seed=1, init=None):
    rnd = random.Random(seed)
    n = M
    Wm = [W[i * M:(i + 1) * M] for i in range(M)]

    def cost(order):
        c = 0
        for a in range(n):
            oa = order[a]
            for b in range(a + 1, n):
                c += Wm[order[b]][oa]
        return c

    def local_search(order):
        cur = cost(order)
        improved = True
        while improved:
            improved = False
            for i in range(n):
                s = order[i]
                best = (cur, i)
                rest = order[:i] + order[i + 1:]
                base = cur - sum(Wm[s][rest[p]] for p in range(0, i)) - sum(Wm[rest[p]][s] for p in range(i, n - 1))
                vb = 0
                va = sum(Wm[r][s] for r in rest)
                for p in range(0, n):
                    c = base + vb + va
                    if c < best[0]:
                        best = (c, p)
                    if p < n - 1:
                        vb += Wm[s][rest[p]]
                        va -= Wm[rest[p]][s]
                if best[1] != i and best[0] < cur:
                    order = rest[:best[1]] + [s] + rest[best[1]:]
                    cur = best[0]
                    improved = True
        return order, cur
    if init is None:
        score = {i: sum(Wm[i]) - sum(Wm[j][i] for j in range(n)) for i in range(n)}
        init = sorted(range(n), key=lambda i: -score[i])
    best_o, best_c = local_search(list(init))
    for r in range(restarts):
        o = best_o[:]
        for _ in range(3):
            i, j = rnd.randrange(n), rnd.randrange(n)
            o[i], o[j] = o[j], o[i]
        o, c = local_search(o)
        if c < best_c:
            best_o, best_c = o, c
    return best_o, best_c


def violation_frac(typec, rank):
    vtok = 0
    ntok = 0
    for w, c in typec.items():
        ntok += c
        r = [rank[s] for s in w]
        L = len(r)
        bad = False
        for i in range(L):
            ri = r[i]
            for j in range(i + 1, L):
                if r[j] < ri and w[i] != w[j]:
                    bad = True
                    break
            if bad:
                break
        if bad:
            vtok += c
    return vtok / ntok if ntok else float("nan")

# ----------------------------------------------------------------------------- per-folio dense stats


class FolioUnit:
    __slots__ = ("folio", "lang", "hand", "tokens", "letters", "edy", "qo", "uni", "first", "big", "words",
                 "mtypec", "prec", "viol_fixed", "mtokens")


def build_units(lines, sym_idx, S, m_idx, M, rank_fixed):
    """One unit per (folio, lang). Lines of the folio in order."""
    groups = collections.OrderedDict()
    for l in lines:
        groups.setdefault((l["folio"], l["lang"]), []).append(l)
    units = []
    for (folio, lang), ls in groups.items():
        u = FolioUnit()
        u.folio = folio
        u.lang = lang
        hc = collections.Counter()
        for l in ls:
            hc[l["hand"]] += len(l["words"])
        u.hand = hc.most_common(1)[0][0]
        ws = [w for l in ls for w in l["words"]]
        u.tokens = len(ws)
        u.letters = sum(len(w) for w in ws)
        u.edy = sum(1 for w in ws if w.endswith("edy"))
        u.qo = sum(1 for w in ws if w.startswith("qo"))
        stream = [sym_idx[c] for w in ws for c in w]
        uni = [0] * S
        for s in stream:
            uni[s] += 1
        u.uni = uni
        first = uni[:]
        first[stream[-1]] -= 1
        u.first = first
        big = [0] * (S * S)
        for a, b in zip(stream, stream[1:]):
            big[a * S + b] += 1
        u.big = big
        u.words = collections.Counter(ws)
        mt = collections.Counter()
        for w, c in u.words.items():
            if set(w) <= EVA_OK:
                mt[merge_a3(w)] += c
        u.mtypec = mt
        u.mtokens = sum(mt.values())
        u.prec = precedence_dense(mt, m_idx, M)
        u.viol_fixed = 0.0
        units.append(u)
    return units


def pair_viol_fixed(W, viol_idx):
    tot = sum(W)
    return sum(W[i] for i in viol_idx) / tot if tot else float("nan")


def sum_dense(rows):
    return list(map(sum, zip(*rows)))


def group_h2(units):
    big = sum_dense([u.big for u in units])
    first = sum_dense([u.first for u in units])
    return Hd(big) - Hd(first)


def group_basic(units):
    tok = sum(u.tokens for u in units)
    let = sum(u.letters for u in units)
    return {"h2": group_h2(units), "mean_word_len": let / tok, "edy_rate": sum(u.edy for u in units) / tok,
            "qo_rate": sum(u.qo for u in units) / tok, "tokens": tok}


def group_words(units):
    c = collections.Counter()
    for u in units:
        c.update(u.words)
    return c


def bootstrap(units, rng, M, viol_idx, n_boot=N_BOOT, do_rigidity=True):
    n = len(units)
    keys = ["h2", "zipf_slope", "hapax_type_frac", "viol_fixed_order", "viol_rederived_order", "mean_word_len"]
    vals = {k: [] for k in keys}
    for b in range(n_boot):
        samp = [units[rng.randrange(n)] for _ in range(n)]
        vals["h2"].append(group_h2(samp))
        wc = group_words(samp)
        freqs = sorted(wc.values(), reverse=True)
        vals["zipf_slope"].append(zipf_slope_from_freqs(freqs))
        vals["hapax_type_frac"].append(sum(1 for v in freqs if v == 1) / len(freqs))
        vals["mean_word_len"].append(sum(u.letters for u in samp) / sum(u.tokens for u in samp))
        if do_rigidity:
            W = sum_dense([u.prec for u in samp])
            vals["viol_fixed_order"].append(pair_viol_fixed(W, viol_idx))
            order, c = best_order_dense(W, M, restarts=2, seed=b)
            vals["viol_rederived_order"].append(c / sum(W))
        if b % 100 == 99:
            log(f"  bootstrap {b + 1}/{n_boot}")
    out = {}
    for k, v in vals.items():
        if not v:
            continue
        s = sorted(v)
        mean = sum(s) / len(s)
        se = math.sqrt(sum((x - mean) ** 2 for x in s) / (len(s) - 1))
        out[k] = {"mean": mean, "se": se, "ci95": [s[int(0.025 * len(s))], s[min(len(s) - 1, int(0.975 * len(s)))]]}
    out["n_units"] = n
    out["n_boot"] = n_boot
    return out


def jackknife(units, viol_idx):
    """Delete-one-unit jackknife SE (folios as units) for statistics that resampling-with-duplication distorts."""
    n = len(units)
    total_words = group_words(units)
    total_big = sum_dense([u.big for u in units])
    total_first = sum_dense([u.first for u in units])
    total_prec = sum_dense([u.prec for u in units])
    let = sum(u.letters for u in units)
    tok = sum(u.tokens for u in units)
    vals = collections.defaultdict(list)
    for u in units:
        wc = total_words.copy()
        wc.subtract(u.words)
        freqs = sorted((v for v in wc.values() if v > 0), reverse=True)
        vals["hapax_type_frac"].append(sum(1 for v in freqs if v == 1) / len(freqs))
        vals["zipf_slope"].append(zipf_slope_from_freqs(freqs))
        big = [a - b for a, b in zip(total_big, u.big)]
        first = [a - b for a, b in zip(total_first, u.first)]
        vals["h2"].append(Hd(big) - Hd(first))
        vals["mean_word_len"].append((let - u.letters) / (tok - u.tokens))
        W = [a - b for a, b in zip(total_prec, u.prec)]
        vals["viol_fixed_order"].append(pair_viol_fixed(W, viol_idx))
    out = {}
    for k, v in vals.items():
        m = sum(v) / n
        se = math.sqrt((n - 1) / n * sum((x - m) ** 2 for x in v))
        out[k] = {"se": se, "jack_mean": m}
    return out


def perm_test(units_A, units_B, rng, n_perm, strata=None):
    """Difference A - B for h2, mean word length, edy, qo. strata: function unit -> stratum key, or None."""
    allu = units_A + units_B
    labels = [1] * len(units_A) + [0] * len(units_B)

    def stat(lbl):
        ga = [u for u, l in zip(allu, lbl) if l]
        gb = [u for u, l in zip(allu, lbl) if not l]
        a = group_basic(ga)
        b = group_basic(gb)
        return {k: a[k] - b[k] for k in ["h2", "mean_word_len", "edy_rate", "qo_rate"]}
    obs = stat(labels)
    if strata is None:
        groups = [list(range(len(allu)))]
    else:
        g = collections.defaultdict(list)
        for i, u in enumerate(allu):
            g[strata(u)].append(i)
        groups = list(g.values())
    movable = sum(len(ix) for ix in groups if len({labels[i] for i in ix}) > 1)
    count = {k: 0 for k in obs}
    dist = {k: [] for k in obs}
    for p in range(n_perm):
        lbl = labels[:]
        for ix in groups:
            sub = [lbl[i] for i in ix]
            rng.shuffle(sub)
            for i, v in zip(ix, sub):
                lbl[i] = v
        s = stat(lbl)
        for k in obs:
            dist[k].append(s[k])
            if abs(s[k]) >= abs(obs[k]) - 1e-12:
                count[k] += 1
    out = {"n_A": len(units_A), "n_B": len(units_B), "n_perm": n_perm, "movable_units": movable, "observed_diff": obs,
           "p_two_sided": {k: (1 + count[k]) / (1 + n_perm) for k in obs},
           "perm_sd": {k: math.sqrt(sum((x - sum(dist[k]) / n_perm) ** 2 for x in dist[k]) / (n_perm - 1)) for k in obs},
           "perm_abs_max": {k: max(abs(x) for x in dist[k]) for k in obs}}
    return out

# ----------------------------------------------------------------------------- driver


def run():
    rng = random.Random(SEED)
    R = {"method": __doc__, "seed": SEED}

    ZL = load_lines("ZL3b-n.words.tsv", "eva")
    zl_all = flat(ZL)
    zl_A = flat(sel(ZL, "A"))
    zl_B = flat(sel(ZL, "B"))
    nALL = sum(len(w) for w in zl_all)
    nA = sum(len(w) for w in zl_A)
    R["sizes"] = {"ZL_ALL_tokens": len(zl_all), "ZL_A_tokens": len(zl_A), "ZL_B_tokens": len(zl_B),
                  "ZL_ALL_letters": nALL, "ZL_A_letters": nA, "ZL_B_letters": sum(len(w) for w in zl_B)}
    log("ZL sizes", R["sizes"])

    langs = load_languages()
    R["language_sizes_available_letters"] = {lg: sum(len(w) for w in ws) for lg, ws in langs.items()}
    log("languages loaded", R["language_sizes_available_letters"])

    # ---------------- (1) entropies
    ent = {"voynich": {}, "languages": {}}
    for name, words in [("ZL ALL", zl_all), ("ZL A", zl_A), ("ZL B", zl_B)]:
        ent["voynich"][name] = {"raw": entropy_block([tok_raw(w) for w in words]),
                                "merge2": entropy_block([tok_m2(w) for w in words])}
        log("entropy", name)
    nM2 = ent["voynich"]["ZL ALL"]["merge2"]["without_spaces"]["n_symbols"]
    R["sizes"]["ZL_ALL_merge2_symbols"] = nM2
    for lg, ws in langs.items():
        e = {}
        for tag, n in [("sizeALL", nALL), ("sizeA", nA), ("sizeM2", nM2)]:
            samp = take_letters(ws, n)
            e[tag + "_folded"] = entropy_block([list(fold(w)) for w in samp])
            if tag != "sizeM2":
                e[tag + "_unfolded"] = entropy_block([list(w) for w in samp], kmax=2)
        ent["languages"][lg] = e
        log("entropy", lg)
    R["entropies"] = ent

    # ---------------- (2) per hand
    hands = {}
    cells = collections.OrderedDict()
    for l in ZL:
        cells.setdefault((l["hand"], l["lang"]), []).append(l)
    for (h, lg), ls in sorted(cells.items()):
        ws = flat(ls)
        if len(ws) < 200 or h == "?":
            continue
        toks = [tok_raw(w) for w in ws]
        eb = cond_entropies(streams(toks)[1], 2)
        d = {"tokens": len(ws), "folios": len({l["folio"] for l in ls}), "h1": eb[1]["plug"], "h2": eb[2]["plug"]}
        d.update(word_stats(ws))
        for tag, nn in [("first10k", 10000), ("first750", 750)]:
            if len(ws) >= nn:
                wn = ws[:nn]
                en_ = cond_entropies(streams([tok_raw(w) for w in wn])[1], 2)
                d[tag] = {"h2": en_[2]["plug"]}
                d[tag].update(word_stats(wn))
        hands[f"hand{h}_{lg}"] = d
    # hand 4 all languages (mostly lang '?')
    ws = flat(sel(ZL, None, "4"))
    if len(ws) >= 200:
        eb = cond_entropies(streams([tok_raw(w) for w in ws])[1], 2)
        d = {"tokens": len(ws), "folios": len({l['folio'] for l in sel(ZL, None, '4')}), "h1": eb[1]["plug"], "h2": eb[2]["plug"]}
        d.update(word_stats(ws))
        hands["hand4_anylang"] = d
    R["per_hand"] = hands
    log("per-hand done")

    # ---------------- dense units for bootstrap / permutation
    syms = sorted({c for w in zl_all for c in w})
    sym_idx = {s: i for i, s in enumerate(syms)}
    S = len(syms)
    m_typec_all = collections.Counter(merge_a3(w) for w in zl_all if set(w) <= EVA_OK)
    m_syms = sorted({c for w in m_typec_all for c in w})
    m_idx = {s: i for i, s in enumerate(m_syms)}
    M = len(m_syms)
    W_all = precedence_dense(m_typec_all, m_idx, M)
    order_all, cost_all = best_order_dense(W_all, M, restarts=12, seed=1)
    rank_fixed = {m_syms[i]: r for r, i in enumerate(order_all)}
    rank_i = {i: r for r, i in enumerate(order_all)}
    viol_idx = [a * M + b for a in range(M) for b in range(M) if a != b and rank_i[a] > rank_i[b]]
    R["rigidity_full"] = {"order": [m_syms[i] for i in order_all], "pair_viol_frac": cost_all / sum(W_all),
                          "viol_tokens": violation_frac(m_typec_all, rank_fixed),
                          "n_tokens": sum(m_typec_all.values()), "n_types": len(m_typec_all), "alphabet": M}
    log("full-data glyph order", R["rigidity_full"]["order"], "pair viol", round(R["rigidity_full"]["pair_viol_frac"], 4),
        "viol tokens", round(R["rigidity_full"]["viol_tokens"], 4))
    units = build_units(ZL, sym_idx, S, m_idx, M, rank_fixed)
    uA = [u for u in units if u.lang == "A"]
    uB = [u for u in units if u.lang == "B"]
    mixed = collections.Counter(u.folio for u in units)
    R["units"] = {"n_units": len(units), "n_A": len(uA), "n_B": len(uB), "n_other": len(units) - len(uA) - len(uB),
                  "folios_with_two_language_units": sum(1 for f, c in mixed.items() if c > 1),
                  "hands_of_A_units": dict(collections.Counter(u.hand for u in uA)),
                  "hands_of_B_units": dict(collections.Counter(u.hand for u in uB))}
    log("units", R["units"])

    # ---------------- (3) bootstrap
    boot = {}
    for name, us in [("ZL ALL", units), ("ZL A", uA), ("ZL B", uB)]:
        log("bootstrap", name)
        pt = group_basic(us)
        wc = group_words(us)
        freqs = sorted(wc.values(), reverse=True)
        pt["zipf_slope"] = zipf_slope_from_freqs(freqs)
        pt["hapax_type_frac"] = sum(1 for v in freqs if v == 1) / len(freqs)
        Wg = sum_dense([u.prec for u in us])
        pt["viol_fixed_order"] = pair_viol_fixed(Wg, viol_idx)
        og, cg = best_order_dense(Wg, M, restarts=6, seed=7)
        pt["viol_rederived_order"] = cg / sum(Wg)
        pt["rederived_order"] = [m_syms[i] for i in og]
        jk = jackknife(us, viol_idx)
        for k, d in jk.items():
            d["ci95_normal"] = [pt[k] - 1.96 * d["se"], pt[k] + 1.96 * d["se"]]
        boot[name] = {"point_from_units": pt, "boot": bootstrap(us, rng, M, viol_idx), "jackknife": jk}
    R["bootstrap"] = boot

    # ---------------- (4) permutation A vs B
    log("permutation A vs B")
    perm = {"unrestricted": perm_test(uA, uB, rng, N_PERM),
            "stratified_by_hand": perm_test(uA, uB, rng, N_PERM, strata=lambda u: u.hand)}
    # within-language between-hand: hand 2 vs hand 3 in B
    u2 = [u for u in uB if u.hand == "2"]
    u3 = [u for u in uB if u.hand == "3"]
    perm["B_hand2_vs_hand3"] = perm_test(u2, u3, rng, N_PERM_HAND)
    # within hand 3: A vs B
    a3u = [u for u in uA if u.hand == "3"]
    b3u = [u for u in uB if u.hand == "3"]
    if len(a3u) >= 2:
        perm["hand3_A_vs_B"] = perm_test(a3u, b3u, rng, N_PERM_HAND)
    R["permutation"] = perm
    log("permutation done", {k: v["p_two_sided"] for k, v in perm.items()})

    # ---------------- (5) predictability
    pred = {"voynich": {}, "languages": {}}
    for name, ls in [("ZL ALL", ZL), ("ZL A", sel(ZL, "A")), ("ZL B", sel(ZL, "B"))]:
        ws = flat(ls)
        line_seqs = [l["words"] for l in ls]
        pred["voynich"][name] = {"word": word_predictability(ws, rng, line_seqs=line_seqs),
                                 "glyph_raw": glyph_boundary_mi([tok_raw(w) for w in ws], rng, line_seqs=[[tok_raw(w) for w in s] for s in line_seqs]),
                                 "glyph_merge2": glyph_boundary_mi([tok_m2(w) for w in ws], rng)}
        log("predictability", name)
    for lg, ws in langs.items():
        e = {}
        for tag, n in [("sizeALL", len(zl_all)), ("sizeA", len(zl_A))]:
            samp = [fold(w) for w in ws[:n]]
            e[tag] = {"word": word_predictability(samp, rng), "glyph": glyph_boundary_mi([list(w) for w in samp], rng)}
        pred["languages"][lg] = e
        log("predictability", lg)
    R["predictability"] = pred

    # ---------------- (6) cross-transliteration
    xt = {}
    for fname, alpha, key in [("RF1b-er.words.tsv", "eva", "RF1b"), ("GC2a-n.words.tsv", "v101", "GC2a")]:
        L = load_lines(fname, alpha)
        xt[key] = {}
        for lang in ["ALL", "A", "B"]:
            ls = sel(L, lang)
            ws = flat(ls)
            eb = cond_entropies(streams([list(w) for w in ws])[1], 3)
            xt[key][lang] = {"tokens": len(ws), "letters": sum(len(w) for w in ws), "h1": eb[1]["plug"], "h2": eb[2]["plug"], "h3": eb[3]["plug"],
                             "word": word_predictability(ws, rng, line_seqs=[l["words"] for l in ls]),
                             "glyph": glyph_boundary_mi([list(w) for w in ws], rng)}
        log("cross-translit", key)
    R["cross_transliteration"] = xt
    R["runtime_s"] = time.time() - T0

    with open(RES / "b4.json", "w", encoding="utf-8") as f:
        json.dump(R, f, indent=1, ensure_ascii=False)
    write_md(R)
    return R

# ----------------------------------------------------------------------------- markdown


def f3(x, d=3):
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{d}f}"


def ent_row(label, d):
    return (f"| {label} | {d['n_symbols']} | {d['inventory']} | {f3(d['h1'])} | {f3(d['h2'])} | {f3(d['h3'])} | {f3(d['h4'])} | "
            f"{f3(d['h2_mm'])} | {f3(d['h3_mm'])} | {f3(d['h4_mm'])} | "
            f"{f3(d['h2_half1'])}/{f3(d['h2_half2'])} | {f3(d['h3_half1'])}/{f3(d['h3_half2'])} | {f3(d['h4_half1'])}/{f3(d['h4_half2'])} |")


ENT_HDR = ("| sample | symbols | inv | h1 | h2 | h3 | h4 | h2 MM | h3 MM | h4 MM | h2 halves | h3 halves | h4 halves |\n"
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|")


def write_md(R):
    L = []
    L.append("# b4 -- robustness: higher-order entropies, per-hand statistics, bootstrap intervals, A/B significance, token predictability\n")
    L.append(f"Seed {R['seed']}; runtime {R['runtime_s']:.0f} s. All output unvalidated until reviewed. Method notes are in the script docstring (copied into b4.json under `method`).\n")
    s = R["sizes"]
    L.append(f"Sizes: ZL ALL {s['ZL_ALL_tokens']} tokens / {s['ZL_ALL_letters']} letters; A {s['ZL_A_tokens']} / {s['ZL_A_letters']}; B {s['ZL_B_tokens']} / {s['ZL_B_letters']}. Languages cut to the ALL and A letter counts (entropies) or token counts (predictability).\n")

    L.append("## 1. Conditional entropies h1..h4 (bits; plug-in; MM = Miller-Madow; halves = plug-in on first/second half of the words)\n")
    L.append("h_k is the entropy of a symbol given the k-1 preceding symbols. Where the two half-sample values sit well below the full-sample value the estimator is biased downward at that order (too few n-grams); read h4 with that in mind. Languages: folded alphabet (diacritics removed), first N letters of one book.\n")
    for sp in ["without_spaces", "with_spaces"]:
        L.append(f"### 1.{1 if sp == 'without_spaces' else 2} {sp.replace('_', ' ')}\n")
        L.append(ENT_HDR)
        for name, e in R["entropies"]["voynich"].items():
            for alpha in ["raw", "merge2"]:
                L.append(ent_row(f"{name} {alpha}", e[alpha][sp]))
        for tag in ["sizeALL", "sizeM2", "sizeA"]:
            for lg, e in R["entropies"]["languages"].items():
                L.append(ent_row(f"{lg} {tag} folded", e[tag + '_folded'][sp]))
        L.append("")
    L.append(f"sizeALL = {R['sizes']['ZL_ALL_letters']} letters (ZL ALL raw), sizeM2 = {R['sizes']['ZL_ALL_merge2_symbols']} letters (the symbol count of ZL ALL merge2, for a like-for-like h3/h4 comparison with the merged alphabet), sizeA = {R['sizes']['ZL_A_letters']} letters.\n")
    L.append("Unfolded (accented letters kept as symbols), h1 / h2, no spaces, size ALL: " + "; ".join(
        f"{lg} {f3(e['sizeALL_unfolded']['without_spaces']['h1'])} / {f3(e['sizeALL_unfolded']['without_spaces']['h2'])}"
        for lg, e in R["entropies"]["languages"].items()) + "\n")

    L.append("## 2. Per hand (Davis hands from the IVTFF headers), split by Currier language; raw EVA, no spaces\n")
    L.append("| cell | folios | tokens | h1 | h2 | mean wlen | hapax % types | Zipf slope (ranks) | -edy % | qo- % | first 10k: h2 / hapax % / Zipf | first 750: h2 / hapax % / Zipf (ranks) |\n|---|---|---|---|---|---|---|---|---|---|---|---|")
    for k, d in R["per_hand"].items():
        t = d.get("first10k")
        tt = f"{f3(t['h2'])} / {100 * t['hapax_type_frac']:.1f} / {f3(t['zipf_slope_1_1000'])}" if t else "-"
        s7 = d.get("first750")
        t7 = f"{f3(s7['h2'])} / {100 * s7['hapax_type_frac']:.1f} / {f3(s7['zipf_slope_1_1000'])} ({s7['ranks_used']})" if s7 else "-"
        L.append(f"| {k} | {d['folios']} | {d['tokens']} | {f3(d['h1'])} | {f3(d['h2'])} | {d['mean_word_len']:.2f} | {100 * d['hapax_type_frac']:.1f} | "
                 f"{f3(d['zipf_slope_1_1000'])} ({d['ranks_used']}) | {100 * d['edy_rate']:.2f} | {100 * d['qo_rate']:.2f} | {tt} | {t7} |")
    L.append("\nHapax fraction and Zipf slope fall with sample size, so the size-matched columns are the ones to compare across cells. Hand 4 writes mostly pages of unknown Currier language (lang '?'); 'hand4_anylang' includes its 39 B-page tokens.\n")

    L.append("## 3. Bootstrap over folios (units = folio x page-language; 500 resamples; percentile 95% CI)\n")
    L.append("Point = statistic on the union of units (bigrams within folios only). Rigidity = a3 'pair-viol frac': token-weighted share of within-word ordered glyph pairs that are out of order under the best linear glyph order, a3 merge (NOTES 4.4 quotes 0.160; shuffle null 0.49); 'fixed' keeps the full-data glyph order, 'rederived' re-optimises the order on each resample (2 restarts).\n")
    rf = R["rigidity_full"]
    L.append(f"Full-data glyph order (a3 method, 12 restarts): {' '.join(rf['order'])}; pair-violation fraction {rf['pair_viol_frac']:.4f}; tokens containing a violation {rf['viol_tokens']:.3f}; {rf['n_tokens']} tokens, {rf['alphabet']} symbols. Re-derived orders per subset: " +
             "; ".join(f"{n}: {' '.join(b['point_from_units']['rederived_order'])}" for n, b in R["bootstrap"].items()) + ".\n")
    L.append("| subset | units | statistic | point | boot mean | boot SE | boot 95% CI | jackknife SE | jackknife 95% CI |\n|---|---|---|---|---|---|---|---|---|")
    for name, b in R["bootstrap"].items():
        pt = b["point_from_units"]
        bb = b["boot"]
        for k, lab in [("h2", "h2 raw no-space"), ("zipf_slope", "Zipf slope 1-1000"), ("hapax_type_frac", "hapax type fraction"),
                       ("mean_word_len", "mean word length"), ("viol_fixed_order", "rigidity, fixed order"), ("viol_rederived_order", "rigidity, rederived order")]:
            if k not in bb:
                continue
            p = pt.get(k)
            jk = b["jackknife"].get(k)
            jkc = f"{f3(jk['se'], 4)} | [{f3(jk['ci95_normal'][0], 4)}, {f3(jk['ci95_normal'][1], 4)}]" if jk else "- | -"
            flag = " (bootstrap invalid: folio duplication turns hapaxes into dis legomena; use jackknife)" if k in ("hapax_type_frac", "zipf_slope") else ""
            L.append(f"| {name} | {bb['n_units']} | {lab}{flag} | {f3(p, 4)} | {f3(bb[k]['mean'], 4)} | {f3(bb[k]['se'], 4)} | [{f3(bb[k]['ci95'][0], 4)}, {f3(bb[k]['ci95'][1], 4)}] | {jkc} |")
    L.append("")
    L.append("Jackknife = delete-one-folio SE with a normal 95% interval; it is the interval to quote for hapax fraction and Zipf slope, and it agrees with the bootstrap for h2, word length and rigidity. Both intervals cover sampling of folios only; they say nothing about the choice of transliteration, filter or merge list.\n")

    L.append("## 4. Permutation tests over folios (two sided; difference = first group minus second)\n")
    L.append("| test | n1 / n2 | permutations | movable units | statistic | observed diff | null SD | max |null| | p |\n|---|---|---|---|---|---|---|---|---|")
    for name, p in R["permutation"].items():
        for k, lab in [("h2", "h2"), ("mean_word_len", "mean word length"), ("edy_rate", "-edy rate"), ("qo_rate", "qo- rate")]:
            L.append(f"| {name} | {p['n_A']} / {p['n_B']} | {p['n_perm']} | {p['movable_units']} | {lab} | {f3(p['observed_diff'][k], 4)} | {f3(p['perm_sd'][k], 4)} | {f3(p['perm_abs_max'][k], 4)} | {p['p_two_sided'][k]:.4f} |")
    L.append("")
    u = R["units"]
    L.append(f"Stratified-by-hand permutation can only exchange labels inside hand 3 (all other hands write one language: A units by hand {u['hands_of_A_units']}, B units by hand {u['hands_of_B_units']}), so its p-values test whether hand 3's two A folios differ from hand 3's 28 B folios; with 2 A folios among 30 there are only 435 distinct relabellings, so the smallest attainable two-sided p is about 0.0023. 'hand3_A_vs_B' is the same comparison run directly. 'B_hand2_vs_hand3' asks whether two scribes writing the same language differ.\n")

    L.append("## 5. Token predictability (word level and glyph level across word boundaries)\n")
    L.append("Plug-in I = H(w_i) + H(w_{i+1}) - H(pair) on consecutive tokens; shuffled = same on a shuffled token order (mean of 3); excess = difference. Held-out: two-fold cross-entropy in bits per token, unigram vs Witten-Bell bigram, hapaxes -> UNK; I_ho = CE_uni - CE_bi; ratio = CE_bi / CE_uni; shuffled likewise. Glyph: MI between the last glyph of a word and the first glyph of the next (raw EVA; merge2 also for ZL), shuffle baseline over word order.\n")
    L.append("| sample | tokens | plug-in I | shuffled I | excess | plug-in ratio | held-out H(w) | held-out H(w'|w) | I_ho | ratio_ho | I_ho shuffled | I_ho excess | glyph I | glyph I shuffled | glyph excess | glyph ratio |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")

    def prow(label, w, g):
        return (f"| {label} | {w['tokens']} | {f3(w['plugin']['I'])} | {f3(w['plugin_shuffled']['I'])} | {f3(w['plugin_excess_I'])} | {f3(w['plugin']['ratio'])} | "
                f"{f3(w['heldout']['CE_uni'], 2)} | {f3(w['heldout']['CE_bi'], 2)} | {f3(w['heldout']['I'])} | {f3(w['heldout']['ratio'])} | {f3(w['heldout_shuffled']['I'])} | {f3(w['heldout_excess_I'])} | "
                f"{f3(g['I'])} | {f3(g['I_shuffled'])} | {f3(g['I_excess'])} | {f3(g['ratio'])} |")
    for name, e in R["predictability"]["voynich"].items():
        L.append(prow(name, e["word"], e["glyph_raw"]))
    for tag in ["sizeALL", "sizeA"]:
        for lg, e in R["predictability"]["languages"].items():
            L.append(prow(f"{lg} {tag}", e[tag]["word"], e[tag]["glyph"]))
    for key, e in R["cross_transliteration"].items():
        for lang, d in e.items():
            L.append(prow(f"{key} {lang}", d["word"], d["glyph"]))
    L.append("")
    v = R["predictability"]["voynich"]
    L.append("ZL within-line only (pairs restricted to consecutive words on one line): " + "; ".join(
        f"{n}: word plug-in I {f3(e['word']['plugin_within_line']['I'])} (all pairs {f3(e['word']['plugin']['I'])}), glyph I {f3(e['glyph_raw']['within_line']['I'])} (all pairs {f3(e['glyph_raw']['I'])})"
        for n, e in v.items()) + ".\n")
    L.append("ZL glyph-boundary MI with merge2 glyphs: " + "; ".join(f"{n}: I {f3(e['glyph_merge2']['I'])}, shuffled {f3(e['glyph_merge2']['I_shuffled'])}, ratio {f3(e['glyph_merge2']['ratio'])}" for n, e in v.items()) + ".\n")

    L.append("## 6. Cross-transliteration: h1 / h2 / h3 raw, no spaces\n")
    L.append("| file | subset | tokens | letters | h1 | h2 | h3 |\n|---|---|---|---|---|---|---|")
    for key, e in R["cross_transliteration"].items():
        for lang, d in e.items():
            L.append(f"| {key} | {lang} | {d['tokens']} | {d['letters']} | {f3(d['h1'])} | {f3(d['h2'])} | {f3(d['h3'])} |")
    L.append("")
    L.append(CONCLUSIONS)
    (RES / "b4.md").write_text("\n".join(L) + "\n", encoding="utf-8")


CONCLUSIONS = """## 7. What the intervals and tests change (judgement, marked *)

**Strengthened.** (i) The character-entropy exclusion. Folio-sampling intervals on h2 are about plus or minus 0.03 bits (ALL 2.28-2.34, A 2.31-2.38, B 2.15-2.21, bootstrap and jackknife agreeing) against a raw gap of at least 1.0 bit to the nearest language at equal size; estimator bias is negligible at this order (Miller-Madow at most 0.006, half-sample shift at most 0.03). The gap persists at h3, where the estimate is still well supported (half-sample shift at most 0.07): raw 2.07 against 2.89-3.04. The same h2 and h3 values appear in RF1b and, at the merged level, in GC2a. (ii) The A/B split is a real difference between folio populations, not a large-sample artefact: unrestricted folio permutation gives p = 0.0005 (the minimum for 2,000 permutations) for h2, -edy and qo-, and p = 0.015 for word length; A and B bootstrap intervals for h2 and for rigidity do not overlap. Inside hand 3, the one scribe who writes both languages, the -edy rate still separates the two A folios from the 28 B folios at p = 0.005 (the smallest attainable value is 0.0023), so at least this marker follows the page language and not only the scribe; h2, qo- and word length are not resolvable with two folios. (iii) The a3 rigidity figure: 0.152-0.169 for ALL against 0.278-0.363 for the four languages, and the shuffle null 0.49, whether the glyph order is fixed or re-derived per resample; a new by-product is that Currier A is less rigid (0.199-0.222) than B (0.131-0.145) with non-overlapping intervals. (iv) The Zipf slope interval (-1.065 to -1.015) contains the German and English values and excludes the Latin one; the hapax fraction interval (68.4-71.0%) lies above the Latin (67.0) and German (65.1) single-book values by more than the folio-sampling width.

**Weakened or qualified.** (i) The token-predictability argument, as reproduced here, separates Voynichese from the vernaculars but only marginally from Latin prose. The held-out word bigram model is worse than a unigram model on Voynichese (I_ho about -0.3 bits, ratio 1.05) and the excess over the shuffled stream is 0.10-0.17 bits, against 0.69-1.29 for German, Danish, Italian, English and French, but Latin (Confessiones) at the same token count gives 0.45 (0.33 at the size of A) and a plug-in excess of 0.19 against 0.18 for Voynichese. The measure is therefore not on its own a discriminator against an inflected, free-word-order plaintext; it is robust across ZL, RF1b and GC2a. (ii) The merged-glyph entropy deficit shrinks with context order: at equal symbol count the gap to the nearest language is 0.52 bits at h2, 0.20 at h3 and by h4 the merged text (2.46, MM 2.54) sits inside the language range (2.27-2.51, MM 2.37-2.59), although h4 is bias-limited for every sample. The redundancy is short-range, which is what rigid two- to three-glyph groups predict; merged h2 should not be quoted as if the deficit held at every order. (iii) 'Language nearly a function of scribe' needs the complement: two scribes writing B differ significantly in word length (4.99 against 5.21, p = 0.002) and -edy rate (20.7% against 14.3%, p = 0.006), and at 750 matched tokens hand 5 has an A-like h2 (2.29) with a B-like -edy rate (16.9%). Part of the B continuum in -edy is scribal, but the within-language scribe difference (6 points) is a third of the between-language difference (17 points).

**New observation.** Across word boundaries the last glyph of a word carries more information about the first glyph of the next word in Voynichese (excess MI 0.17 bits ALL, 0.11 A, 0.22 B; 0.19-0.25 with merged glyphs; 0.16-0.28 in RF1b and GC2a) than in any tested language (0.03-0.07, French 0.13 because of elided one-letter words). Word-level dependency is near zero while glyph-level dependency across the space is above language level; the space in Voynichese behaves less like a lexical boundary than it does in the six languages, which bears on the assumption in NOTES section 2 that EVA spaces mark plaintext units.

**Unchanged.** Everything in NOTES 4.3, 4.5 and 4.6 (word-length dispersion, self-citation distances, generator comparison) was not re-tested. The language side of every comparison is still one book per language with no between-book interval, so the hapax and Zipf statements rest on the folio interval only. Hand assignments were taken from the IVTFF headers as before.

## 8. Checked, not checked, user must verify

**Checked.** Point estimates reproduce a1 (h2 2.311 / 2.353 / 2.182, merged 2.870), a2 (Zipf -1.040, hapax 69.7%) and a3 (pair-violation 0.1596, token-violation 0.424, same 27-symbol order) from the same TSV and filters. Bootstrap and jackknife agree for h2, word length and rigidity. The bootstrap failure for hapax and Zipf (folio duplication) was detected and replaced by the jackknife. Runtime under two minutes, so no permutation count was reduced.

**Not checked.** The Rozanova & Temerev estimator itself (their preprint was not read; this is one reading of 'information a word carries about the next'). Whether Witten-Bell is the smoothing they used; a Kneser-Ney or tuned-interpolation model would raise every held-out I by a similar amount and might change the Voynich-Latin ordering. h4 values are bias-limited everywhere. Sensitivity to the merge list and to treating uncertain spaces as breaks. Stratified permutation has almost no power (two A folios in hand 3).

**User must verify before quoting.** The Latin corpus (Confessiones, sidenotes stripped) and the folding of diacritics; the UNK convention (training hapaxes and test OOV to one type) in the held-out estimator; the choice of folio x page-language as the resampling unit; the interpretation of the cross-boundary glyph MI. All output is unvalidated until reviewed.
"""


if __name__ == "__main__":
    R = run()
    log("done; runtime", round(R["runtime_s"], 1))
