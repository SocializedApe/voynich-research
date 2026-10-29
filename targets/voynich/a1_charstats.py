"""a1_charstats.py -- character-level statistics of Voynichese vs natural languages and controls.

Pure Python 3.12, no third-party packages.

METHOD (every choice is explicit; see also results/a1.md)
---------------------------------------------------------
Voynich text
  * Files: data/ZL3b-n.words.tsv (main), data/RF1b-er.words.tsv, data/GC2a-n.words.tsv.
  * Only locus_type == 'P' (paragraph text). Words containing '?' (unread glyph) are dropped.
  * EVA files (ZL, RF): words containing any character outside a-z are dropped as well
    (extended-EVA codes '@nnn;', digits, apostrophes: 96 of 34212 ZL paragraph words, 0 RF words).
  * GC (v101): every character is a symbol (v101 uses digits, capitals and punctuation as glyphs);
    words containing '@' (extended codes '@nnn;') are dropped.
  * Subsets: Currier A ($L=A), Currier B ($L=B), ALL (A + B + pages with unknown language '?').
  * Alphabets:
      raw     : one EVA character = one symbol.
      merge1  : greedy longest-match tokenisation with the token list
                ckh cth cph cfh ch sh iiin iin eee ee   (benches, bench-gallows, i-groups, e-groups)
      merge2  : merge1 tokens plus  aiin ain in qo   (a+i-groups, and the qo digraph)
                Greedy longest match is applied left to right; e.g. 'daiin' -> d,aiin (merge2) or d,a,iin (merge1);
                'cheey' -> ch,ee,y ; 'qokeedy' -> qo,k,ee,d,y (merge2).
    Merging is applied to EVA files only; GC v101 already encodes most of these composites as single glyphs.

Natural languages
  * Gutenberg texts: header stripped up to the line containing '*** START OF', footer from '*** END OF'.
  * Normalisation for ALL texts (identical to Voynich treatment): lower-case; a character is a letter iff
    str.isalpha() (so accented letters such as ae/oe/aa/ss are kept as distinct symbols); every other
    character (digits, punctuation, apostrophe, whitespace) is a word break.
  * Sample: for each language, an equal share of the target letter budget is taken from the START of each
    book (whole words), so that a 150k-letter sample of e.g. Danish mixes all five Danish books.
  * Italian: targets/vatican5/corpus_it.txt (already lower-cased, no punctuation); first N letters.

Controls (built from the Latin sample)
  * LAT-novowel : a e i o u y removed from every Latin word, empty words dropped ("abjad-like").
  * LAT-verbose12 : each Latin letter -> fixed group of 1-3 symbols over a 12-symbol output alphabet;
                    the 4 most frequent letters get 1-symbol codes, the next 8 get 2-symbol codes, the rest
                    3-symbol codes; codes drawn with random.Random(1) (prefix-free is not required).
  * LAT-verbose6  : same idea over a 6-symbol alphabet; all letters get 2- or 3-symbol codes.
  * LAT-verbose20 : 20-symbol output alphabet (inventory comparable to EVA); 6 letters -> 1 symbol,
                    10 letters -> 2 symbols, rest -> 3 symbols (random.Random(3)).
    Word boundaries are kept in both, so the 'with spaces' statistics are meaningful.

Statistics (all logs base 2)
  * with spaces  : the symbol stream is words joined by a single space symbol (line ends count as a space).
  * without spaces: words concatenated with nothing between them; bigrams span word boundaries.
  * h0 = log2(number of distinct symbols in the sample).
  * h1 = -sum p(x) log2 p(x)  over unigrams.
  * h2 = H(X_n | X_{n-1}) = H(bigram) - H(unigram over first positions), plug-in (maximum-likelihood) estimate.
  * h2_within: conditional entropy using only bigrams inside words (no-space stream) -- extra diagnostic.
  * word entropy H_w = -sum p(w) log2 p(w) over word types, plus type/token counts. Because H_w depends
    strongly on sample size, each language is also evaluated at exactly the token counts of the
    Voynich A, B and ALL subsets.
  * Sample sizes: Voynich subsets are reported at full size (and ALL additionally truncated to 150k letters);
    languages/controls are reported at 150,000 letters (spaces excluded from the count) and at the letter
    count of Voynich ZL Currier A, so that A can be compared like with like.
"""
import os as _os  # local paths (the September 2026 scripts hard-coded another machine)
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_CORP = _os.path.join(_HERE, 'data', 'corpora')  # corp_<lang>_<gutenberg id>.txt, see fetch_corpora.py
_EXT = _os.path.join(_HERE, 'data', 'external')  # third-party data (Naibbe, Gaskell & Bowern)
_IT = _os.path.join(_CORP, 'corpus_it.txt')  # vatican5 OCR corpus from the September sample's first words (fetch_corpora.py)
import csv, math, json, os, sys, random, collections, pathlib, re

HERE = pathlib.Path(_HERE)
DATA = HERE / "data"
RES = HERE / "results"
RES.mkdir(exist_ok=True)
CORP = pathlib.Path(_CORP)
IT_CORPUS = pathlib.Path(_IT)

TARGET = 150_000

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
tok_m1 = make_tokenizer(MERGE1)
tok_m2 = make_tokenizer(MERGE2)

# ----------------------------------------------------------------------------- entropy helpers

def H(counter):
    n = sum(counter.values())
    return -sum(c / n * math.log2(c / n) for c in counter.values()) if n else 0.0


def stream_stats(stream):
    """stream: list of symbols. returns dict h0,h1,h2,n,inventory."""
    uni = collections.Counter(stream)
    big = collections.Counter(zip(stream, stream[1:]))
    first = collections.Counter(stream[:-1])
    h1 = H(uni)
    h2 = H(big) - H(first)
    return {"n_symbols": len(stream), "inventory": len(uni), "h0": math.log2(len(uni)), "h1": h1, "h2": h2,
            "h2_over_h1": h2 / h1 if h1 else None, "h1_minus_h2": h1 - h2}


def within_word_h2(words_tok):
    uni = collections.Counter()
    big = collections.Counter()
    first = collections.Counter()
    for w in words_tok:
        uni.update(w)
        for a, b in zip(w, w[1:]):
            big[(a, b)] += 1
            first[a] += 1
    return H(big) - H(first)


def word_entropy(words):
    c = collections.Counter(words)
    return {"tokens": len(words), "types": len(c), "H_word_bits": H(c), "TTR": len(c) / len(words) if words else None,
            "hapax_frac": sum(1 for v in c.values() if v == 1) / len(c) if c else None}


def full_stats(words_tok, label, top=12):
    """words_tok: list of token-lists (one per word)."""
    flat_nospace = [s for w in words_tok for s in w]
    flat_space = []
    for w in words_tok:
        flat_space.extend(w)
        flat_space.append(" ")
    flat_space.pop()
    ws = stream_stats(flat_space)
    ns = stream_stats(flat_nospace)
    ns["h2_within_word"] = within_word_h2(words_tok)
    uni = collections.Counter(flat_nospace)
    n = sum(uni.values())
    return {"label": label, "n_words": len(words_tok), "n_letters": len(flat_nospace),
            "mean_word_len": len(flat_nospace) / len(words_tok) if words_tok else None,
            "with_spaces": ws, "without_spaces": ns,
            "word_entropy": word_entropy(["".join(w) for w in words_tok]),
            "top_symbols": [(s, round(c / n, 4)) for s, c in uni.most_common(top)]}

# ----------------------------------------------------------------------------- Voynich loading

def load_voynich(fname, alphabet="eva"):
    rows = []
    with open(DATA / fname, encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            if row["locus_type"] != "P":
                continue
            for w in row["line_words"].split():
                if "?" in w:
                    continue
                if alphabet == "eva":
                    if not re.fullmatch(r"[a-z]+", w):
                        continue
                else:
                    if "@" in w:
                        continue
                rows.append((row["lang"], w))
    return rows


def subset(rows, lang):
    if lang == "ALL":
        return [w for _, w in rows]
    return [w for l, w in rows if l == lang]

# ----------------------------------------------------------------------------- corpora

def gutenberg_words(path):
    txt = path.read_text(encoding="utf-8", errors="replace")
    i = txt.find("*** START OF")
    if i >= 0:
        txt = txt[txt.find("\n", i) + 1:]
    j = txt.find("*** END OF")
    if j >= 0:
        txt = txt[:j]
    return normalise(txt)


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


def take_letters(words, n_letters):
    out = []
    n = 0
    for w in words:
        if n >= n_letters:
            break
        out.append(w)
        n += len(w)
    return out


def language_sample(lang, n_letters):
    files = sorted(CORP.glob(f"corp_{lang}_*.txt"))
    books = [gutenberg_words(f) for f in files]
    share = n_letters / len(books)
    sample = []
    for b in books:
        sample.extend(take_letters(b, share))
    return sample, [f.name for f in files]


_it_cache = None

def italian_sample(n_letters):
    global _it_cache
    if _it_cache is None:
        _it_cache = normalise(IT_CORPUS.read_text(encoding="utf-8", errors="replace")[:4_000_000])
    return take_letters(_it_cache, n_letters), ["targets/vatican5/corpus_it.txt"]

# ----------------------------------------------------------------------------- controls

VOWELS = set("aeiouy")

def no_vowels(words):
    out = []
    for w in words:
        s = "".join(c for c in w if c not in VOWELS)
        if s:
            out.append(s)
    return out


def verbose_cipher_map(latin_words, out_alpha, n1, n2, seed=1):
    """Frequency-ranked letter -> code-group map. n1 letters get 1-symbol codes, n2 get 2-symbol, rest 3."""
    freq = collections.Counter(c for w in latin_words for c in w)
    letters = [c for c, _ in freq.most_common()]
    rng = random.Random(seed)
    used = set()
    mapping = {}
    for idx, c in enumerate(letters):
        L = 1 if idx < n1 else (2 if idx < n1 + n2 else 3)
        while True:
            code = "".join(rng.choice(out_alpha) for _ in range(L))
            if code not in used:
                used.add(code)
                mapping[c] = code
                break
    return mapping


def verbose_encode(words, mapping):
    return ["".join(mapping[c] for c in w) for w in words]

# ----------------------------------------------------------------------------- driver

def run():
    results = {"method": __doc__, "voynich": {}, "languages": {}, "controls": {}, "verbose_maps": {}}

    # ---- Voynich
    voy_sets = {}
    for fname, alpha in [("ZL3b-n.words.tsv", "eva"), ("RF1b-er.words.tsv", "eva"), ("GC2a-n.words.tsv", "v101")]:
        rows = load_voynich(fname, alpha)
        key = fname.split("-")[0].split(".")[0]
        results["voynich"][key] = {}
        for lang in ["A", "B", "ALL"]:
            words = subset(rows, lang)
            voy_sets[(key, lang)] = words
            entry = {}
            toks = {"raw": tok_raw} if alpha == "v101" else {"raw": tok_raw, "merge1": tok_m1, "merge2": tok_m2}
            for tname, tk in toks.items():
                entry[tname] = full_stats([tk(w) for w in words], f"{key} {lang} {tname}")
                if lang == "ALL":
                    trunc = take_letters(words, TARGET)
                    entry[tname + "_150k"] = full_stats([tk(w) for w in trunc], f"{key} ALL {tname} 150k")
            results["voynich"][key][lang] = entry
    nA = results["voynich"]["ZL3b"]["A"]["raw"]["n_letters"]
    nB = results["voynich"]["ZL3b"]["B"]["raw"]["n_letters"]
    nALL = results["voynich"]["ZL3b"]["ALL"]["raw"]["n_letters"]
    wA = results["voynich"]["ZL3b"]["A"]["raw"]["n_words"]
    wB = results["voynich"]["ZL3b"]["B"]["raw"]["n_words"]
    wALL = results["voynich"]["ZL3b"]["ALL"]["raw"]["n_words"]
    results["sizes"] = {"ZL_A_letters": nA, "ZL_B_letters": nB, "ZL_ALL_letters": nALL,
                        "ZL_A_words": wA, "ZL_B_words": wB, "ZL_ALL_words": wALL, "target_letters": TARGET}

    # ---- languages
    langs = ["la", "it", "de", "en", "fr", "da", "nl", "sv", "no", "is", "fi"]
    big_latin = None
    for lg in langs:
        big_n = max(TARGET, nALL) * 3
        if lg == "it":
            words, files = italian_sample(big_n)
        else:
            words, files = language_sample(lg, big_n)
        if lg == "la":
            big_latin = words
        entry = {"files": files}
        for tag, n in [("150k", TARGET), ("sizeA", nA)]:
            entry[tag] = full_stats([list(w) for w in take_letters(words, n)], f"{lg} {tag}")
        # word entropy at Voynich token counts
        entry["word_entropy_at"] = {f"{k}_words": word_entropy(words[:v]) for k, v in [("A", wA), ("B", wB), ("ALL", wALL)]}
        results["languages"][lg] = entry

    # ---- controls
    nv = no_vowels(big_latin)
    ctrl = {"LAT-novowel": nv}
    m12 = verbose_cipher_map(big_latin, "abcdefghijkl", 4, 8, seed=1)
    m6 = verbose_cipher_map(big_latin, "abcdef", 0, 6, seed=2)
    m20 = verbose_cipher_map(big_latin, "abcdefghijklmnopqrst", 6, 10, seed=3)
    results["verbose_maps"] = {"LAT-verbose12": m12, "LAT-verbose6": m6, "LAT-verbose20": m20}
    ctrl["LAT-verbose12"] = verbose_encode(big_latin, m12)
    ctrl["LAT-verbose6"] = verbose_encode(big_latin, m6)
    ctrl["LAT-verbose20"] = verbose_encode(big_latin, m20)
    for name, words in ctrl.items():
        entry = {}
        for tag, n in [("150k", TARGET), ("sizeA", nA)]:
            entry[tag] = full_stats([list(w) for w in take_letters(words, n)], f"{name} {tag}")
        entry["word_entropy_at"] = {f"{k}_words": word_entropy(words[:v]) for k, v in [("A", wA), ("B", wB), ("ALL", wALL)]}
        results["controls"][name] = entry

    with open(RES / "a1.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1, ensure_ascii=False)
    write_md(results)
    return results


def fmt(x, d=3):
    return "-" if x is None else f"{x:.{d}f}"


def row(label, st):
    ws, ns, we = st["with_spaces"], st["without_spaces"], st["word_entropy"]
    return (f"| {label} | {st['n_letters']} | {st['n_words']} | {fmt(st['mean_word_len'],2)} | "
            f"{ws['inventory']} | {fmt(ws['h0'])} | {fmt(ws['h1'])} | {fmt(ws['h2'])} | {fmt(ws['h2_over_h1'])} | "
            f"{ns['inventory']} | {fmt(ns['h0'])} | {fmt(ns['h1'])} | {fmt(ns['h2'])} | {fmt(ns['h2_over_h1'])} | {fmt(ns['h2_within_word'])} | "
            f"{fmt(we['H_word_bits'],2)} | {we['types']} |")


HDR = ("| sample | letters | words | mean wlen | inv(sp) | h0(sp) | h1(sp) | h2(sp) | h2/h1(sp) | inv | h0 | h1 | h2 | h2/h1 | h2 within-word | H_word | word types |\n"
       "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")


def write_md(R):
    L = []
    L.append("# a1 -- character-level statistics: Voynichese vs natural languages and controls\n")
    L.append("All entropies in bits per symbol; plug-in estimates; log base 2. `(sp)` = word space included as a symbol; otherwise words concatenated with no separator (bigrams cross word boundaries). `h2 within-word` = conditional entropy using only bigrams inside words. `H_word` = entropy of the word-type distribution in bits per word (sample-size dependent, see the dedicated table).\n")
    L.append("## 1. Voynich (paragraph text only, words with '?' dropped)\n")
    L.append(HDR)
    for key in ["ZL3b", "RF1b", "GC2a"]:
        for lang in ["A", "B", "ALL"]:
            for tname, st in R["voynich"][key][lang].items():
                L.append(row(f"{key} {lang} {tname}", st))
    L.append("\n## 2. Natural languages, 150,000 letters (equal share from the start of each book)\n")
    L.append(HDR)
    for lg, e in R["languages"].items():
        L.append(row(f"{lg} 150k", e["150k"]))
    L.append("\n## 3. Controls built from Latin, 150,000 letters\n")
    L.append(HDR)
    for name, e in R["controls"].items():
        L.append(row(f"{name} 150k", e["150k"]))
    L.append(f"\nVerbose cipher maps: {json.dumps(R['verbose_maps'])}\n")
    nA = R["sizes"]["ZL_A_letters"]
    L.append(f"\n## 4. Languages and controls at the size of ZL Currier A ({nA} letters)\n")
    L.append(HDR)
    for lg, e in R["languages"].items():
        L.append(row(f"{lg} sizeA", e["sizeA"]))
    for name, e in R["controls"].items():
        L.append(row(f"{name} sizeA", e["sizeA"]))
    L.append("\n## 5. Word-distribution entropy at matched token counts (bits per word; types; hapax fraction)\n")
    s = R["sizes"]
    L.append(f"| sample | @{s['ZL_A_words']} words (A) | @{s['ZL_B_words']} words (B) | @{s['ZL_ALL_words']} words (ALL) |\n|---|---|---|---|")
    for key in ["ZL3b", "RF1b", "GC2a"]:
        cells = []
        for lang in ["A", "B", "ALL"]:
            we = R["voynich"][key][lang]["raw"]["word_entropy"]
            cells.append(f"{we['H_word_bits']:.2f} / {we['types']} / {we['hapax_frac']:.2f}")
        L.append(f"| {key} (own A / B / ALL) | " + " | ".join(cells) + " |")
    for grp in ["languages", "controls"]:
        for lg, e in R[grp].items():
            cells = []
            for k in ["A_words", "B_words", "ALL_words"]:
                we = e["word_entropy_at"][k]
                cells.append(f"{we['H_word_bits']:.2f} / {we['types']} / {we['hapax_frac']:.2f}")
            L.append(f"| {lg} | " + " | ".join(cells) + " |")
    L.append("\n## 6. Top symbols (relative frequency, no spaces)\n")
    for key in ["ZL3b"]:
        for lang in ["A", "B"]:
            for tname in ["raw", "merge2"]:
                L.append(f"- {key} {lang} {tname}: {R['voynich'][key][lang][tname]['top_symbols']}")
    for lg in ["la", "it", "de", "en"]:
        L.append(f"- {lg}: {R['languages'][lg]['150k']['top_symbols']}")
    for name, e in R["controls"].items():
        L.append(f"- {name}: {e['150k']['top_symbols']}")
    (RES / "a1.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    R = run()
    print("sizes", R["sizes"])
    for key in ["ZL3b"]:
        for lang in ["A", "B", "ALL"]:
            for tname, st in R["voynich"][key][lang].items():
                print(row(f"{key} {lang} {tname}", st))
    for lg, e in R["languages"].items():
        print(row(f"{lg} 150k", e["150k"]))
    for name, e in R["controls"].items():
        print(row(f"{name} 150k", e["150k"]))
