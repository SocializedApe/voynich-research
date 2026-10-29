"""v_b4.py -- adversarial verification of b4_robustness.py (pure Python stdlib).

Independently recomputes, with its own code (nothing imported from b4):
  1. h1/h2/h3 (and block-entropy/n for contrast) for ZL raw, no spaces, and for the Latin corpus at the
     same letter count; also h2 at a second Latin offset (mid-book) to see how much 'first N letters' matters.
  2. h2 for hand 2 / B and hand 1 / A (hand and lang from the TSV columns = IVTFF $H and $L).
  3. 200-replicate folio bootstrap (with replacement) of ZL h2 raw, bigrams within folios.
  4. 500-permutation A-vs-B folio test on the token-weighted -edy share.
  5. Held-out word-bigram excess for ZL ALL and Latin with my own smoothing:
       Jelinek-Mercer interpolation P(b|a) = lam * c(a,b)/c(a) + (1-lam) * P1(b), P1 = add-0.5 unigram over
       the training vocabulary (training hapaxes -> UNK, test OOV -> UNK, same convention as b4 so the numbers
       are comparable); lam fixed at 0.5, and also lam tuned on the last 20% of the training half.
     Reported as CE_uni - CE_bi (b4's I_ho), the same on shuffled tokens, the difference (b4's excess), and the
     decomposition of the excess into a unigram term and a bigram term.
  6. Glyph MI across the word boundary (last glyph -> first glyph of next word), ZL ALL and Latin, with shuffle.
Writes results/v_b4.json and results/v_b4.md.  Does not touch b4 files.
"""
import os as _os  # local paths (the September 2026 scripts hard-coded another machine)
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_CORP = _os.path.join(_HERE, 'data', 'corpora')  # corp_<lang>_<gutenberg id>.txt, see fetch_corpora.py
_EXT = _os.path.join(_HERE, 'data', 'external')  # third-party data (Naibbe, Gaskell & Bowern)
_IT = _os.path.join(_CORP, 'corpus_it.txt')  # vatican5 OCR corpus from the September sample's first words (fetch_corpora.py)
import csv, math, json, random, collections, pathlib, re, unicodedata, time

HERE = pathlib.Path(_HERE)
DATA = HERE / "data"
RES = HERE / "results"
CORP = pathlib.Path(_CORP)
LA = CORP / "corp_la_33849.txt"
T0 = time.time()
rng = random.Random(7)


def log(*a):
    print(f"[{time.time()-T0:6.1f}s]", *a, flush=True)

# ---------------------------------------------------------------- data


def load_zl():
    lines = []
    with open(DATA / "ZL3b-n.words.tsv", encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            if row["locus_type"] != "P":
                continue
            ws = [w for w in row["line_words"].split() if "?" not in w and re.fullmatch(r"[a-z]+", w)]
            if ws:
                lines.append((row["folio"], row["lang"], row["hand"], ws))
    return lines


def normalise(txt):
    return re.findall(r"[^\W\d_]+", txt.lower())


def fold(w):
    m = {"ß": "ss", "æ": "ae", "œ": "oe", "ø": "o", "ð": "d", "þ": "th", "ł": "l"}
    out = []
    for ch in w:
        if ch in m:
            out.append(m[ch]); continue
        d = "".join(c for c in unicodedata.normalize("NFKD", ch) if not unicodedata.combining(c))
        out.append(d or ch)
    return "".join(out)


def load_latin():
    txt = LA.read_text(encoding="utf-8", errors="replace")
    i = txt.find("*** START OF"); txt = txt[txt.find("\n", i) + 1:] if i >= 0 else txt
    j = txt.find("*** END OF"); txt = txt[:j] if j >= 0 else txt
    txt = re.sub(r"\[Sidenote:.*?\]", " ", txt, flags=re.S)
    return [fold(w) for w in normalise(txt)]


def take_letters(words, n):
    out, k = [], 0
    for w in words:
        if k >= n:
            break
        out.append(w); k += len(w)
    return out

# ---------------------------------------------------------------- entropy (own code)


def cond_entropy(stream, k):
    """H(X_n | X_{n-k+1}..X_{n-1}) in bits, computed directly as sum_ctx p(ctx) H(next | ctx)."""
    if k == 1:
        c = collections.Counter(stream); n = len(stream)
        return -sum(v / n * math.log2(v / n) for v in c.values())
    table = collections.defaultdict(collections.Counter)
    for i in range(k - 1, len(stream)):
        table[tuple(stream[i - k + 1:i])][stream[i]] += 1
    N = len(stream) - k + 1
    h = 0.0
    for ctx, nxt in table.items():
        m = sum(nxt.values())
        h += m / N * (math.log2(m) - sum(v * math.log2(v) for v in nxt.values()) / m)
    return h


def block_entropy_over_n(stream, k):
    """H(k-gram)/k -- the quantity that is sometimes mislabelled h_k."""
    c = collections.Counter(tuple(stream[i:i + k]) for i in range(len(stream) - k + 1))
    N = sum(c.values())
    return (math.log2(N) - sum(v * math.log2(v) for v in c.values()) / N) / k


def entropies(words):
    s = [ch for w in words for ch in w]
    return {"symbols": len(s), "inventory": len(set(s)),
            "h1": cond_entropy(s, 1), "h2": cond_entropy(s, 2), "h3": cond_entropy(s, 3),
            "H2_over_2": block_entropy_over_n(s, 2), "H3_over_3": block_entropy_over_n(s, 3)}

# ---------------------------------------------------------------- held-out bigram (own smoothing)


def ce_pair(train, test, lam):
    c = collections.Counter(train)
    vocab = {w for w, k in c.items() if k >= 2}
    tr = [w if w in vocab else "<unk>" for w in train]
    te = [w if w in vocab else "<unk>" for w in test]
    uni = collections.Counter(tr); V = len(uni); N = len(tr); a = 0.5
    big = collections.Counter(zip(tr, tr[1:])); ctx = collections.Counter(tr[:-1])
    cu = cb = 0.0; n = 0
    for x, y in zip(te, te[1:]):
        p1 = (uni[y] + a) / (N + a * V)
        cx = ctx.get(x, 0)
        p2 = (lam * big.get((x, y), 0) / cx + (1 - lam) * p1) if cx else p1
        cu -= math.log2(p1); cb -= math.log2(p2); n += 1
    return cu / n, cb / n


def tune_lam(train):
    cut = int(0.8 * len(train))
    grid = [0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    return min(grid, key=lambda l: ce_pair(train[:cut], train[cut:], l)[1])


def heldout(tokens, lam=None):
    h = len(tokens) // 2
    A, B = tokens[:h], tokens[h:]
    if lam is None:
        l1, l2 = tune_lam(A), tune_lam(B)
    else:
        l1 = l2 = lam
    u1, b1 = ce_pair(A, B, l1); u2, b2 = ce_pair(B, A, l2)
    return {"CE_uni": (u1 + u2) / 2, "CE_bi": (b1 + b2) / 2, "I": (u1 + u2 - b1 - b2) / 2, "lam": [l1, l2]}


def heldout_with_shuffle(tokens, lam, n_shuf=3):
    real = heldout(tokens, lam)
    sh = []
    for _ in range(n_shuf):
        t = tokens[:]; rng.shuffle(t); sh.append(heldout(t, lam))
    s = {k: sum(d[k] for d in sh) / n_shuf for k in ("CE_uni", "CE_bi", "I")}
    return {"real": real, "shuffled": s, "excess_I": real["I"] - s["I"],
            "unigram_term_CEuni_minus_shuf": real["CE_uni"] - s["CE_uni"],
            "bigram_gain_CEbi_shuf_minus_real": s["CE_bi"] - real["CE_bi"]}


def plugin_mi(pairs):
    a = collections.Counter(p[0] for p in pairs); b = collections.Counter(p[1] for p in pairs); ab = collections.Counter(pairs)
    n = len(pairs)
    H = lambda c: math.log2(n) - sum(v * math.log2(v) for v in c.values()) / n
    return H(a) + H(b) - H(ab)


def glyph_boundary(words, n_shuf=3):
    pr = lambda ws: [(ws[i][-1], ws[i + 1][0]) for i in range(len(ws) - 1)]
    I = plugin_mi(pr(words)); sh = []
    for _ in range(n_shuf):
        w = words[:]; rng.shuffle(w); sh.append(plugin_mi(pr(w)))
    return {"I": I, "I_shuffled": sum(sh) / n_shuf, "excess": I - sum(sh) / n_shuf}

# ---------------------------------------------------------------- run


def main():
    R = {}
    ZL = load_zl()
    words_all = [w for _, _, _, ws in ZL for w in ws]
    nALL = sum(len(w) for w in words_all)
    R["sizes"] = {"tokens": len(words_all), "letters": nALL}
    log("ZL", R["sizes"])

    # 1. entropies
    la = load_latin()
    la_first = take_letters(la, nALL)
    la_mid = take_letters(la[len(la) // 2:], nALL)
    R["entropy"] = {"ZL_ALL_raw": entropies(words_all), "la_first_N": entropies(la_first), "la_mid_N": entropies(la_mid)}
    for lg in ("A", "B"):
        R["entropy"][f"ZL_{lg}_raw"] = entropies([w for _, l, _, ws in ZL if l == lg for w in ws])
    log("entropies", {k: (round(v["h2"], 3), round(v["h3"], 3)) for k, v in R["entropy"].items()})

    # 2. per hand
    R["per_hand"] = {}
    for h, lg in (("2", "B"), ("1", "A"), ("3", "B"), ("3", "A")):
        ws = [w for _, l, hd, wl in ZL if l == lg and hd == h for w in wl]
        s = [c for w in ws for c in w]
        R["per_hand"][f"hand{h}_{lg}"] = {"tokens": len(ws), "h2": cond_entropy(s, 2)}
    log("per hand", R["per_hand"])

    # 3. folio bootstrap of h2 (200 replicates, folios with replacement, bigrams within folio)
    fol = collections.OrderedDict()
    for f, l, h, ws in ZL:
        fol.setdefault(f, {"lang": l, "words": [], "tokens": 0, "edy": 0})
        fol[f]["words"].extend(ws)
    units = []
    for f, d in fol.items():
        s = [c for w in d["words"] for c in w]
        big = collections.Counter(zip(s, s[1:])); first = collections.Counter(s[:-1])
        units.append({"folio": f, "lang": d["lang"], "big": big, "first": first, "tokens": len(d["words"]),
                      "edy": sum(1 for w in d["words"] if w.endswith("edy"))})

    def h2_of(us):
        big = collections.Counter(); first = collections.Counter()
        for u in us:
            big.update(u["big"]); first.update(u["first"])
        Nb = sum(big.values()); Nf = sum(first.values())
        Hb = math.log2(Nb) - sum(v * math.log2(v) for v in big.values()) / Nb
        Hf = math.log2(Nf) - sum(v * math.log2(v) for v in first.values()) / Nf
        return Hb - Hf
    point = h2_of(units)
    boots = sorted(h2_of([units[rng.randrange(len(units))] for _ in range(len(units))]) for _ in range(200))
    R["bootstrap_h2"] = {"n_folios": len(units), "point_within_folio": point, "n_boot": 200,
                         "ci95": [boots[5], boots[194]], "se": math.sqrt(sum((x - sum(boots) / 200) ** 2 for x in boots) / 199)}
    log("bootstrap", R["bootstrap_h2"])

    # 4. permutation on -edy share, A vs B folios
    ab = [u for u in units if u["lang"] in ("A", "B")]
    lab = [u["lang"] == "A" for u in ab]

    def edy_diff(lbl):
        ea = sum(u["edy"] for u, l in zip(ab, lbl) if l); ta = sum(u["tokens"] for u, l in zip(ab, lbl) if l)
        eb = sum(u["edy"] for u, l in zip(ab, lbl) if not l); tb = sum(u["tokens"] for u, l in zip(ab, lbl) if not l)
        return ea / ta - eb / tb
    obs = edy_diff(lab); cnt = 0; mx = 0.0
    for _ in range(500):
        l = lab[:]; rng.shuffle(l); d = edy_diff(l); mx = max(mx, abs(d))
        if abs(d) >= abs(obs):
            cnt += 1
    R["perm_edy"] = {"n_A": sum(lab), "n_B": len(lab) - sum(lab), "observed_A_minus_B": obs, "n_perm": 500,
                     "p_two_sided": (1 + cnt) / 501, "max_abs_null": mx}
    log("perm", R["perm_edy"])

    # 5. held-out bigram excess, own smoothing
    la_tok = [w for w in la][:len(words_all)]
    R["heldout"] = {}
    for name, toks in (("ZL_ALL", words_all), ("la", la_tok)):
        R["heldout"][name] = {"tokens": len(toks), "types": len(set(toks)),
                              "hapax_type_frac": sum(1 for v in collections.Counter(toks).values() if v == 1) / len(set(toks)),
                              "JM_lam0.5": heldout_with_shuffle(toks, 0.5),
                              "JM_lam_tuned": heldout_with_shuffle(toks, None)}
        log("heldout", name, {k: round(v["excess_I"], 3) for k, v in R["heldout"][name].items() if isinstance(v, dict)})

    # 6. glyph MI across boundary
    R["glyph_boundary"] = {"ZL_ALL": glyph_boundary(words_all), "la": glyph_boundary(la_tok)}
    log("glyph", R["glyph_boundary"])

    R["runtime_s"] = time.time() - T0
    (RES / "v_b4.json").write_text(json.dumps(R, indent=1), encoding="utf-8")
    return R


if __name__ == "__main__":
    main()
