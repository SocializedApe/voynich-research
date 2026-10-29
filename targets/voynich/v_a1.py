"""v_a1.py -- adversarial re-check of a1_charstats.py (independent implementation).

Checks
 1. Recompute ZL raw / merge2 (A, B, ALL) h1, h2 (no-space, with-space, within-word) with a
    direct conditional-entropy formula  H(Y|X) = sum_x p(x) H(Y|X=x)  (not H(XY)-H(X)).
 2. Which books actually make up each language's '150k' sample (a1 claims equal share per book).
 3. Latin per book (Aeneid / Confessions / Phrase-book) at 50k letters each; English contamination
    of the phrase-book measured by English stop-word share.
 4. Italian corpus: stop-word classification of 200-word windows into it / la / de; h2 on the
    Italian-only windows vs the raw mixed stream.
 5. Inventory-independent redundancy (h1 - h2) for Voynich, languages and controls; Miller-Madow
    bias correction for the v101 (70-symbol) case.
 6. Verbose-cipher controls re-encoded from the maps in results/a1.json and re-measured;
    additional verbose control over a 24-symbol alphabet (= EVA inventory) for a fairer match.
 7. Languages with diacritics folded to a-z (does the 40-symbol French inventory matter?).
 8. Voynich data hygiene: characters present in ZL / GC words, dropped-word counts.
Outputs results/v_a1.json and results/v_a1.md
"""
import os as _os  # local paths (the September 2026 scripts hard-coded another machine)
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_CORP = _os.path.join(_HERE, 'data', 'corpora')  # corp_<lang>_<gutenberg id>.txt, see fetch_corpora.py
_EXT = _os.path.join(_HERE, 'data', 'external')  # third-party data (Naibbe, Gaskell & Bowern)
_IT = _os.path.join(_CORP, 'corpus_it.txt')  # vatican5 OCR corpus from the September sample's first words (fetch_corpora.py)
import csv, math, json, collections, pathlib, re, unicodedata, random

HERE = pathlib.Path(_HERE)
DATA = HERE / "data"
RES = HERE / "results"
RES.mkdir(exist_ok=True)
CORP = pathlib.Path(_CORP)
IT_CORPUS = pathlib.Path(_IT)
A1 = json.load(open(RES / "a1.json", encoding="utf-8"))

# ----------------------------------------------------------------- entropy (independent formulas)
def H(counter):
    n = sum(counter.values())
    return -sum(c / n * math.log2(c / n) for c in counter.values()) if n else 0.0

def cond_entropy(pairs):
    """H(Y|X) = sum_x p(x) H(Y|X=x), pairs = iterable of (x,y)."""
    ctx = collections.defaultdict(collections.Counter)
    for x, y in pairs:
        ctx[x][y] += 1
    N = sum(sum(c.values()) for c in ctx.values())
    return sum(sum(c.values()) / N * H(c) for c in ctx.values())

def miller_madow_h2(stream):
    """H(XY)-H(X) with Miller-Madow bias correction (K-1)/(2N ln2) on each term."""
    big = collections.Counter(zip(stream, stream[1:]))
    first = collections.Counter(stream[:-1])
    N = len(stream) - 1
    Hb = H(big) + (len(big) - 1) / (2 * N * math.log(2))
    Hf = H(first) + (len(first) - 1) / (2 * N * math.log(2))
    return Hb - Hf

def stats(words_tok):
    flat = [s for w in words_tok for s in w]
    sp = []
    for w in words_tok:
        sp.extend(w); sp.append(" ")
    sp.pop()
    uni = collections.Counter(flat)
    h1 = H(uni)
    h2 = cond_entropy(zip(flat, flat[1:]))
    h1s = H(collections.Counter(sp))
    h2s = cond_entropy(zip(sp, sp[1:]))
    h2w = cond_entropy((a, b) for w in words_tok for a, b in zip(w, w[1:]))
    wc = collections.Counter("".join(w) for w in words_tok)
    return {"letters": len(flat), "words": len(words_tok), "inv": len(uni), "h0": math.log2(len(uni)),
            "h1": h1, "h2": h2, "h2_over_h1": h2 / h1, "h1_minus_h2": h1 - h2,
            "h1_sp": h1s, "h2_sp": h2s, "h2_sp_over_h1_sp": h2s / h1s,
            "h2_within": h2w, "mean_wlen": len(flat) / len(words_tok),
            "H_word": H(wc), "types": len(wc), "hapax": sum(1 for v in wc.values() if v == 1) / len(wc)}

def r3(d):
    return {k: (round(v, 3) if isinstance(v, float) else v) for k, v in d.items()}

# ----------------------------------------------------------------- tokenisers (own implementation)
MERGE2 = ["ckh", "cth", "cph", "cfh", "ch", "sh", "iiin", "iin", "eee", "ee", "aiin", "ain", "in", "qo"]
_pat = re.compile("|".join(sorted(MERGE2, key=len, reverse=True)) + "|.")
tok_m2 = lambda w: _pat.findall(w)   # regex alternation, longest first = greedy longest match

# ----------------------------------------------------------------- 8. Voynich hygiene + 1. recompute
def load(fname, eva=True):
    rows, dropped = [], collections.Counter()
    chars = collections.Counter()
    with open(DATA / fname, encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            if row["locus_type"] != "P":
                continue
            for w in row["line_words"].split():
                if "?" in w:
                    dropped["?"] += 1; continue
                if eva and not re.fullmatch(r"[a-z]+", w):
                    dropped["non a-z"] += 1; chars.update(set(w) - set("abcdefghijklmnopqrstuvwxyz")); continue
                if (not eva) and "@" in w:
                    dropped["@"] += 1; continue
                rows.append((row["lang"], w))
    return rows, dropped, chars

out = {}
zl, zl_drop, zl_badchars = load("ZL3b-n.words.tsv")
gc, gc_drop, _ = load("GC2a-n.words.tsv", eva=False)
gc_chars = collections.Counter(c for _, w in gc for c in w)
out["hygiene"] = {"ZL_dropped": dict(zl_drop), "ZL_offending_chars": dict(zl_badchars),
                  "ZL_kept_words": len(zl), "GC_dropped": dict(gc_drop), "GC_kept_words": len(gc),
                  "GC_symbol_inventory": "".join(sorted(gc_chars)),
                  "ZL_lang_counts": dict(collections.Counter(l for l, _ in zl))}

voy = {}
for lang in ["A", "B", "ALL"]:
    words = [w for l, w in zl if lang == "ALL" or l == lang]
    voy[f"ZL {lang} raw"] = r3(stats([list(w) for w in words]))
    voy[f"ZL {lang} merge2"] = r3(stats([tok_m2(w) for w in words]))
    if lang == "ALL":
        flat = [c for w in words for c in w]
        voy["ZL ALL raw h2 Miller-Madow"] = round(miller_madow_h2(flat), 3)
gcw = [w for _, w in gc]
voy["GC ALL raw"] = r3(stats([list(w) for w in gcw]))
voy["GC ALL raw h2 Miller-Madow"] = round(miller_madow_h2([c for w in gcw for c in w]), 3)
# compare with a1
a1v = A1["voynich"]["ZL3b"]
voy["a1_reported"] = {f"ZL {l} {t}": {"h1": round(a1v[l][t]["without_spaces"]["h1"], 3),
                                      "h2": round(a1v[l][t]["without_spaces"]["h2"], 3),
                                      "h2_within": round(a1v[l][t]["without_spaces"]["h2_within_word"], 3)}
                      for l in ["A", "B", "ALL"] for t in ["raw", "merge2"]}
out["voynich"] = voy

# ----------------------------------------------------------------- corpora
def normalise(txt):
    return re.findall(r"[^\W\d_]+", txt.lower())   # isalpha runs

def fold(w):
    s = unicodedata.normalize("NFKD", w)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("ß", "ss").replace("æ", "ae").replace("ø", "o").replace("œ", "oe").replace("ð", "d").replace("þ", "th")
    return "".join(c for c in s if "a" <= c <= "z")

def book_words(path):
    t = path.read_text(encoding="utf-8", errors="replace")
    i = t.find("*** START OF")
    if i >= 0:
        t = t[t.find("\n", i) + 1:]
    j = t.find("*** END OF")
    if j >= 0:
        t = t[:j]
    return normalise(t)

def take(words, n):
    o, k = [], 0
    for w in words:
        if k >= n:
            break
        o.append(w); k += len(w)
    return o

def a1_sample(lang, n_big, n_take):
    """replicate a1's procedure exactly and record how many letters each book contributes."""
    files = sorted(CORP.glob(f"corp_{lang}_*.txt"))
    books = [(f.name, book_words(f)) for f in files]
    share = n_big / len(books)
    seq, owner = [], []
    for name, b in books:
        part = take(b, share)
        seq.extend(part); owner.extend([name] * len(part))
    samp = take(seq, n_take)
    contrib = collections.Counter()
    for w, o in zip(samp, owner):
        contrib[o] += len(w)
    return samp, dict(contrib), books

nALL = A1["sizes"]["ZL_ALL_letters"]
big_n = max(150000, nALL) * 3
langs = ["la", "it", "de", "en", "fr", "da", "nl", "sv", "no", "is", "fi"]
lang_out = {}
books_cache = {}
for lg in langs:
    if lg == "it":
        continue
    samp, contrib, books = a1_sample(lg, big_n, 150000)
    books_cache[lg] = books
    st = stats([list(w) for w in samp])
    stf = stats([list(fold(w)) for w in samp if fold(w)])
    lang_out[lg] = {"letters_per_book_in_150k_sample": contrib,
                    "recomputed_150k": r3(st), "folded_to_az_150k": r3(stf),
                    "a1_h2": round(A1["languages"][lg]["150k"]["without_spaces"]["h2"], 3)}
out["languages"] = lang_out

# ----------------------------------------------------------------- 3. Latin per book
EN_STOP = set("the of and to in a is that for it as was with be by on not he this are or his from at which but have an had they you were their one all we can her has there been if more when will would who so no".split())
lat = {}
for name, b in books_cache["la"]:
    s50 = take(b, 50000)
    st = stats([list(w) for w in s50])
    en_share = sum(1 for w in s50 if w in EN_STOP) / len(s50)
    lat[name] = {"en_stopword_share": round(en_share, 3), **r3(st)}
# Latin clean: Aeneid + Confessions 75k each (skip phrase-book)
clean = take(books_cache["la"][0][1], 75000) + take(books_cache["la"][1][1], 75000)
lat["Aeneid+Confessions 150k"] = r3(stats([list(w) for w in clean]))
out["latin_by_book"] = lat

# ----------------------------------------------------------------- 4. Italian contamination
IT_STOP = set("che di la il per non con le del della una un si al lo gli nel della sua suo questo come piu se ma ha sono era anche essere quando alla dal dei delle".split())
LA_STOP = set("et in ad cum quod ut est non ex de per ac atque enim autem sed qui quae quibus esse sunt etiam pro sive vel nec".split())
DE_STOP = set("und der die das den nicht ist sich mit auf dem des ein eine von zu er es an im auch nach wie aus bei war werden hat oder wird".split())
it_all = normalise(IT_CORPUS.read_text(encoding="utf-8", errors="replace")[:4_000_000])
W = 200
win_lab = []
it_words, la_words, de_words = [], [], []
cnt = collections.Counter()
for i in range(0, len(it_all) - W, W):
    win = it_all[i:i + W]
    sc = {"it": sum(w in IT_STOP for w in win), "la": sum(w in LA_STOP for w in win), "de": sum(w in DE_STOP for w in win)}
    lab = max(sc, key=sc.get)
    if sc[lab] < 8:
        lab = "unk"
    cnt[lab] += 1
    {"it": it_words, "la": la_words, "de": de_words}.get(lab, []).extend(win)
it150 = take(it_all, 150000)
ital = {"window_counts_200w_first4MB": dict(cnt),
        "share_of_first_150k_sample_windows": dict(collections.Counter(
            (lambda win: (lambda sc: (max(sc, key=sc.get) if max(sc.values()) >= 8 else "unk"))(
                {"it": sum(w in IT_STOP for w in win), "la": sum(w in LA_STOP for w in win), "de": sum(w in DE_STOP for w in win)}))
            (it150[i:i + W]) for i in range(0, len(it150) - W, W))),
        "a1_it_150k_mixed": r3(stats([list(w) for w in it150])),
        "italian_windows_only_150k": r3(stats([list(w) for w in take(it_words, 150000)])),
        "latin_windows_only_150k": r3(stats([list(w) for w in take(la_words, 150000)])) if sum(map(len, la_words)) > 150000 else None,
        "german_windows_only_150k": r3(stats([list(w) for w in take(de_words, 150000)])) if sum(map(len, de_words)) > 150000 else None}
out["italian"] = ital

# ----------------------------------------------------------------- 6. controls re-encoded + 24-symbol verbose
big_latin, _, _ = a1_sample("la", big_n, big_n)
ctrl = {}
for name, mp in A1["verbose_maps"].items():
    enc = ["".join(mp[c] for c in w) for w in big_latin]
    ctrl[name] = {"recomputed_150k": r3(stats([list(w) for w in take(enc, 150000)])),
                  "a1_h2": round(A1["controls"][name]["150k"]["without_spaces"]["h2"], 3)}
# extra: 24-symbol verbose, frequency ranked, 8 letters 1-symbol, 12 letters 2-symbol, rest 3 (seed 5)
def vmap(words, alpha, n1, n2, seed):
    freq = collections.Counter(c for w in words for c in w)
    rng = random.Random(seed); used = set(); mp = {}
    for idx, (c, _) in enumerate(freq.most_common()):
        L = 1 if idx < n1 else (2 if idx < n1 + n2 else 3)
        while True:
            code = "".join(rng.choice(alpha) for _ in range(L))
            if code not in used:
                used.add(code); mp[c] = code; break
    return mp
for tag, (alpha, n1, n2, seed) in {"LAT-verbose24 (8/12/rest)": ("abcdefghijklmnopqrstuvwx", 8, 12, 5),
                                   "LAT-verbose24 (0/24/rest)": ("abcdefghijklmnopqrstuvwx", 0, 24, 6)}.items():
    mp = vmap(big_latin, alpha, n1, n2, seed)
    enc = ["".join(mp[c] for c in w) for w in big_latin]
    ctrl[tag] = {"recomputed_150k": r3(stats([list(w) for w in take(enc, 150000)]))}
nv = [s for s in ("".join(c for c in w if c not in set("aeiouy")) for w in big_latin) if s]
ctrl["LAT-novowel"] = {"recomputed_150k": r3(stats([list(w) for w in take(nv, 150000)])),
                       "a1_h2": round(A1["controls"]["LAT-novowel"]["150k"]["without_spaces"]["h2"], 3)}
out["controls"] = ctrl

# ----------------------------------------------------------------- 5. redundancy table
red = {}
for k, v in voy.items():
    if isinstance(v, dict) and "h1_minus_h2" in v:
        red[k] = {"h1": v["h1"], "h2": v["h2"], "h1-h2": v["h1_minus_h2"], "h2/h1": v["h2_over_h1"], "inv": v["inv"]}
for lg, v in lang_out.items():
    s = v["recomputed_150k"]
    red[lg] = {"h1": s["h1"], "h2": s["h2"], "h1-h2": s["h1_minus_h2"], "h2/h1": s["h2_over_h1"], "inv": s["inv"]}
s = ital["italian_windows_only_150k"]
red["it (italian windows only)"] = {"h1": s["h1"], "h2": s["h2"], "h1-h2": s["h1_minus_h2"], "h2/h1": s["h2_over_h1"], "inv": s["inv"]}
for k, v in ctrl.items():
    s = v["recomputed_150k"]
    red[k] = {"h1": s["h1"], "h2": s["h2"], "h1-h2": s["h1_minus_h2"], "h2/h1": s["h2_over_h1"], "inv": s["inv"]}
out["redundancy_h1_minus_h2"] = red

json.dump(out, open(RES / "v_a1.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)

# ----------------------------------------------------------------- markdown
L = ["# v_a1 -- adversarial re-check of a1\n", "## Redundancy table (no spaces, 150k letters for languages/controls; Voynich full size)\n",
     "| sample | inv | h1 | h2 | h1-h2 | h2/h1 |", "|---|---|---|---|---|---|"]
for k, v in red.items():
    L.append(f"| {k} | {v['inv']} | {v['h1']:.3f} | {v['h2']:.3f} | {v['h1-h2']:.3f} | {v['h2/h1']:.3f} |")
L.append("\n## Books actually in each 150k sample (letters)\n")
for lg, v in lang_out.items():
    L.append(f"- {lg}: {v['letters_per_book_in_150k_sample']}  a1 h2 {v['a1_h2']} / recomputed {v['recomputed_150k']['h2']} / folded a-z {v['folded_to_az_150k']['h2']} (inv {v['folded_to_az_150k']['inv']})")
L.append("\n## Latin per book (50k letters)\n")
for k, v in lat.items():
    L.append(f"- {k}: h1 {v['h1']} h2 {v['h2']} h1-h2 {v['h1_minus_h2']} H_word {v['H_word']} en_stop {v.get('en_stopword_share')}")
L.append("\n## Italian corpus\n")
L.append(json.dumps({k: v for k, v in ital.items() if not isinstance(v, dict) or 'h2' not in v}, ensure_ascii=False))
for k in ["a1_it_150k_mixed", "italian_windows_only_150k", "latin_windows_only_150k", "german_windows_only_150k"]:
    if ital[k]:
        L.append(f"- {k}: h1 {ital[k]['h1']} h2 {ital[k]['h2']} h1-h2 {ital[k]['h1_minus_h2']} H_word {ital[k]['H_word']} hapax {ital[k]['hapax']}")
L.append("\n## Voynich recomputed vs a1\n")
L.append(json.dumps(voy["a1_reported"]))
for k in ["ZL A raw", "ZL B raw", "ZL ALL raw", "ZL A merge2", "ZL B merge2", "ZL ALL merge2", "GC ALL raw"]:
    v = voy[k]
    L.append(f"- {k}: h1 {v['h1']} h2 {v['h2']} h2_sp {v['h2_sp']} h2_within {v['h2_within']} H_word {v['H_word']} hapax {v['hapax']}")
L.append(f"- Miller-Madow h2: ZL ALL raw {voy['ZL ALL raw h2 Miller-Madow']}, GC ALL {voy['GC ALL raw h2 Miller-Madow']}")
L.append("\n## Hygiene\n" + json.dumps(out["hygiene"], ensure_ascii=False))
(RES / "v_a1.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
