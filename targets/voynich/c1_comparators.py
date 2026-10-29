"""c1_comparators.py -- the comparators asked for after RBA's post (goflaw.substack.com, 22 Sept 2026) and
Ilya A.'s note (11 Oct 2026), run through the b3 battery and the Lindemann & Bowern entropy convention.

Part 1. Conditional character entropy h2 under both conventions, with alphabet size:
        (a) with the space as a character, as Lindemann & Bowern 2021 (arXiv 2010.14697) compute it;
        (b) without spaces, as a1/b4 and the site page quote it.
        Every corpus is cut to the Voynich token count (34,116 tokens) before measuring.  Voynich points: ZL raw
        EVA, ZL merged (a1 merge2: benches, i-groups, ee, aiin/ain/in, qo; close to L&B's 'Minimal'), RF1b-er,
        IT2a-n (Takahashi), CD2a-n (Currier), GC2a-n (v101).  Paragraph text only, words with '?' dropped, EVA
        files a-z only, the others drop words containing '@' (a1's rule).
Part 2. The b3 battery (37 items, b3.battery / b3.score unchanged, autocopist spread as tolerance) on:
        low-h2 natural languages from public-domain or redistributable Bibles (Hawaiian 1868, Tongan, Maori NT,
        Setswana NT, Swahili NT 1850) and the Latin Vulgate as a same-genre Latin control; constructed languages
        (Esperanto Bible; Toki Pona, Lojban and Volapuk sentences from Tatoeba); character Markov chains of order
        1, 2 and 3 trained on the ZL token stream and of order 1 and 3 trained on Latin; i.i.d. 'random glyphs'
        drawn from the Voynich glyph frequencies.  All poured into the ZL page/line skeleton, as in b3.
Part 3. Curves for the site charts: rank-frequency, vocabulary growth, word-length histograms.

Normalisation of the comparator texts: lower case; a word is a maximal run of letters (str.isalpha, plus the
apostrophe for Lojban, where it is a letter); Toki Pona and Lojban keep only words in their fixed alphabets;
for the others, words containing a letter rarer than 0.01% of all letters are dropped (L&B's rare-character
cut, applied to words).  Bible chapter headings stay in; verse numbers are digits and drop out.

Caveats fixed in advance: a Markov chain of order k >= 1 trained on Voynichese reproduces its h2 by
construction, so its h2 says nothing about Voynichese; what matters is which battery items it does NOT
reproduce.  Tatoeba texts are independent sentences in contribution order, so their page-level and long-range
items (e, h, j, k) are not meaningful.  The 1868 Hawaiian Bible spells without the okina and macrons, the
simplification Stallings (1998) objected to in Bennett's Hawaiian comparison.

Writes results/c1.json and results/c1.md.  Seeded and deterministic.  Needs fetch_corpora.py to have run.
"""
import collections, json, math, os, random, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a4_selfcitation as a4
import b3_bakeoff as b3

DATA = os.path.join(HERE, 'data')
CORP = os.path.join(DATA, 'corpora')
OUT = os.path.join(HERE, 'results')

COMPARATORS = [  # name, file, group, label
    ('hawaiian', 'bible_haw.txt', 'low-h2 language', 'Hawaiian (Bible 1868)'),
    ('tongan', 'bible_ton.txt', 'low-h2 language', 'Tongan (Bible)'),
    ('maori', 'bible_mri.txt', 'low-h2 language', 'Maori (New Testament)'),
    ('setswana', 'bible_tsn.txt', 'low-h2 language', 'Setswana (New Testament)'),
    ('swahili', 'bible_swh.txt', 'low-h2 language', 'Swahili (New Testament 1850)'),
    ('latin_vulgate', 'bible_lat.txt', 'language', 'Latin (Vulgate)'),
    ('esperanto', 'bible_epo.txt', 'constructed language', 'Esperanto (Bible)'),
    ('toki_pona', 'tatoeba_tok.txt', 'constructed language', 'Toki Pona (Tatoeba)'),
    ('lojban', 'tatoeba_jbo.txt', 'constructed language', 'Lojban (Tatoeba)'),
    ('volapuk', 'tatoeba_vol.txt', 'constructed language', 'Volapuk (Tatoeba)'),
]
FIXED_ALPHABET = {'toki_pona': set('aeijklmnopstuw'), 'lojban': set("abcdefgijklmnoprstuvxyz'")}
GUTENBERG_LANGS = ['la', 'it', 'de', 'en', 'fr', 'da', 'nl', 'sv', 'no', 'is', 'fi']
SEED = 20261011

MERGE2 = ["ckh", "cth", "cph", "cfh", "ch", "sh", "iiin", "iin", "eee", "ee", "aiin", "ain", "in", "qo"]  # a1


def log(*a):
    print(*a, flush=True)


# ----------------------------------------------------------------------------------------------- loading
def text_words(name, path):
    t = open(path, encoding='utf-8', errors='replace').read().lower()
    pat = r"(?:[^\W\d_]|')+" if name == 'lojban' else r"[^\W\d_]+"
    words = re.findall(pat, t)
    if name == 'lojban':
        words = [w.strip("'") for w in words]
        words = [w for w in words if w]
    if name in FIXED_ALPHABET:
        ok = FIXED_ALPHABET[name]
        return [w for w in words if set(w) <= ok]
    letters = collections.Counter(c for w in words for c in w)
    total = sum(letters.values())
    rare = {c for c, v in letters.items() if v / total < 1e-4}
    return [w for w in words if not (set(w) & rare)]


def voynich_words(fname, alphabet):
    """a1.load_voynich: paragraph text, '?' words dropped; EVA a-z only, other alphabets drop '@' words."""
    out = []
    with open(os.path.join(DATA, fname), encoding='utf-8') as f:
        head = next(f).rstrip('\n').split('\t')
        for line in f:
            row = dict(zip(head, line.rstrip('\n').split('\t')))
            if row['locus_type'] != 'P':
                continue
            for w in row['line_words'].split():
                if '?' in w:
                    continue
                if alphabet == 'eva' and not re.fullmatch(r'[a-z]+', w):
                    continue
                if alphabet != 'eva' and '@' in w:
                    continue
                out.append(w)
    return out


def tok_merge2(w):
    out = []; i = 0
    while i < len(w):
        for s in sorted(MERGE2, key=len, reverse=True):
            if w.startswith(s, i):
                out.append(s); i += len(s); break
        else:
            out.append(w[i]); i += 1
    return out


def lang_words_upto(lang, n):
    """a4.lang_words, but returns what there is when the books hold fewer than n words (fi, is)."""
    try:
        return a4.lang_words(lang, n)
    except SystemExit:
        files = sorted(fn for fn in os.listdir(CORP) if fn.startswith(f'corp_{lang}_') and fn.endswith('.txt'))
        return [w for fn in files for w in a4.gutenberg_words(os.path.join(CORP, fn))][:n]


# ----------------------------------------------------------------------------------------------- entropy
def H(counts):
    n = sum(counts); return -sum(c / n * math.log2(c / n) for c in counts if c)


def h12(symbols):
    """h1 and h2 = H(X_n | X_{n-1}) of one symbol stream; alphabet size."""
    pairs = collections.Counter(zip(symbols, symbols[1:]))
    first = collections.Counter()
    for (x, _), v in pairs.items():
        first[x] += v
    return H(collections.Counter(symbols).values()), H(pairs.values()) - H(first.values()), len(set(symbols))


def conventions(word_symbols):
    """word_symbols: list of words, each a list of symbols.  Returns both conventions."""
    with_sp = []
    for ws in word_symbols:
        with_sp.extend(ws); with_sp.append(' ')
    no_sp = [s for ws in word_symbols for s in ws]
    h1s, h2s, ns = h12(with_sp); h1n, h2n, nn = h12(no_sp)
    return {'with_space': {'h1': h1s, 'h2': h2s, 'alphabet': ns}, 'no_space': {'h1': h1n, 'h2': h2n, 'alphabet': nn},
            'tokens': len(word_symbols), 'symbols': len(no_sp)}


# ----------------------------------------------------------------------------------------------- generators
def markov_words(train_words, k, n_tokens, seed):
    s = ' ' + ' '.join(train_words) + ' '
    table = collections.defaultdict(collections.Counter)
    for i in range(k, len(s)):
        table[s[i - k:i]][s[i]] += 1
    dist = {ctx: (list(c.keys()), list(itertools_accumulate(c.values()))) for ctx, c in table.items()}
    starts = [s[i - k:i] for i in range(k, len(s)) if s[i - 1] == ' ']
    rng = random.Random(seed); ctx = rng.choice(starts); out = []; ntok = 0
    while ntok < n_tokens + 1:
        if ctx not in dist:
            ctx = rng.choice(starts)
        chars, cum = dist[ctx]
        c = rng.choices(chars, cum_weights=cum)[0]
        if c == ' ' and out and out[-1] != ' ':
            ntok += 1
        out.append(c); ctx = (ctx + c)[-k:]
    return ''.join(out).split()[:n_tokens]


def itertools_accumulate(vals):
    tot = 0
    for v in vals:
        tot += v; yield tot


def random_glyph_words(train_words, n_tokens, seed):
    s = ' '.join(train_words) + ' '
    c = collections.Counter(s); chars = list(c); cum = list(itertools_accumulate(c.values()))
    rng = random.Random(seed); out = []; ntok = 0
    while ntok < n_tokens + 1:
        ch = rng.choices(chars, cum_weights=cum)[0]
        if ch == ' ' and out and out[-1] != ' ':
            ntok += 1
        out.append(ch)
    return ''.join(out).split()[:n_tokens]


# ----------------------------------------------------------------------------------------------- curves
def curves(words):
    cnt = collections.Counter(words)
    rf = [v for _, v in cnt.most_common(2000)]
    n = len(words); pts = sorted({int(round(math.exp(math.log(100) + i * (math.log(n) - math.log(100)) / 29))) for i in range(30)})
    seen = set(); heaps = []; j = 0
    for i, w in enumerate(words, 1):
        seen.add(w)
        if j < len(pts) and i == pts[j]:
            heaps.append([i, len(seen)]); j += 1
    lens = collections.Counter(min(len(w), 15) for w in words)
    return {'rank_freq': rf, 'heaps': heaps, 'len_hist': {str(k): lens.get(k, 0) / n for k in range(1, 16)},
            'tokens': n, 'types': len(cnt), 'hapax_types': sum(1 for v in cnt.values() if v == 1) / len(cnt)}


# ----------------------------------------------------------------------------------------------- main
def main():
    t0 = time.time()
    zl = b3.load_zl_lang(); skel = a4.skeleton(zl); vw = b3.words_of(zl); N = len(vw)
    log(f'ZL {N} tokens, {len(zl)} pages')

    # word lists
    words = collections.OrderedDict(); meta = {}
    for name, fn, group, label in COMPARATORS:
        ws = text_words(name, os.path.join(CORP, fn))
        meta[name] = {'file': fn, 'group': group, 'label': label, 'available_tokens': len(ws),
                      'alphabet': ''.join(sorted(set(''.join(ws))))}
        words[name] = ws[:N]
        log(f'{name}: {len(ws)} tokens available, alphabet {meta[name]["alphabet"]}')
    latin = a4.lang_words('la', N)
    gens = [('markov1_voynich', vw, 1, 'Markov order 1, trained on Voynich'), ('markov2_voynich', vw, 2, 'Markov order 2, trained on Voynich'),
            ('markov3_voynich', vw, 3, 'Markov order 3, trained on Voynich'), ('markov1_latin', latin, 1, 'Markov order 1, trained on Latin'),
            ('markov3_latin', latin, 3, 'Markov order 3, trained on Latin')]
    for i, (name, train, k, label) in enumerate(gens):
        words[name] = markov_words(train, k, N, SEED + i)
        meta[name] = {'group': 'generator', 'label': label, 'available_tokens': len(words[name])}
    words['random_glyphs'] = random_glyph_words(vw, N, SEED + 9)
    meta['random_glyphs'] = {'group': 'generator', 'label': 'Random glyphs (Voynich glyph frequencies, i.i.d.)', 'available_tokens': N}

    # ---------------- part 1: h2 conventions
    part1 = collections.OrderedDict()
    for fname, alpha, key, label in [('ZL3b-n.words.tsv', 'eva', 'voynich_ZL_raw', 'Voynich ZL, EVA'),
                                     ('ZL3b-n.words.tsv', 'eva_m2', 'voynich_ZL_merged', 'Voynich ZL, merged glyphs'),
                                     ('RF1b-er.words.tsv', 'eva', 'voynich_RF1b', 'Voynich RF1b-er, EVA'),
                                     ('IT2a-n.words.tsv', 'eva', 'voynich_IT2a', 'Voynich Takahashi IT2a, EVA'),
                                     ('CD2a-n.words.tsv', 'currier', 'voynich_CD2a', 'Voynich Currier CD2a'),
                                     ('GC2a-n.words.tsv', 'v101', 'voynich_GC2a', 'Voynich v101 GC2a')]:
        ws = voynich_words(fname, 'eva' if alpha.startswith('eva') else alpha)
        sym = [tok_merge2(w) for w in ws] if alpha == 'eva_m2' else [list(w) for w in ws]
        part1[key] = dict(conventions(sym), group='Voynich', label=label)
    for lg in GUTENBERG_LANGS:
        ws = lang_words_upto(lg, N)
        part1['gutenberg_' + lg] = dict(conventions([list(w) for w in ws]), group='language', label=f'{lg} (Nuntiaturberichte OCR)' if lg == 'it' else f'{lg} (Gutenberg)')
    for name, ws in words.items():
        part1[name] = dict(conventions([list(w) for w in ws]), group=meta[name]['group'], label=meta[name]['label'])
    for k, v in part1.items():
        log(f'{k:22s} with space h2 {v["with_space"]["h2"]:.3f} (n={v["with_space"]["alphabet"]})   no space h2 {v["no_space"]["h2"]:.3f}')

    # ---------------- part 2: b3 battery
    corpora = collections.OrderedDict()
    corpora['voynich_ZL'] = zl
    corpora['autocopist_s19'] = a4.Autocopist(19).generate(skel)
    corpora['autocopist_s7'] = a4.Autocopist(7).generate(skel)
    for name, ws in words.items():
        if len(ws) >= N:
            corpora[name] = a4.pour(ws, skel)
    N_short = 10053
    short_only = {name: ws[:N_short] for name, ws in words.items() if N_short <= len(ws) < N}
    full = collections.OrderedDict(); short = collections.OrderedDict(); xf = {}; xs = {}
    for n, p in corpora.items():
        t1 = time.time()
        full[n] = b3.battery(p, n, xf)
        short[n] = b3.battery(b3.truncate_pages(p, N_short), n, xs)
        log(f'{n}: battery {time.time() - t1:.1f}s')
    for n, ws in short_only.items():
        short[n] = b3.battery(b3.truncate_pages(a4.pour(ws + [''] * (N - len(ws)), skel), N_short), n, xs)
        log(f'{n}: short battery only ({len(words[n])} tokens)')
    tol_f, marks_f = b3.score(full); tol_s, marks_s = b3.score(short)

    # ---------------- part 3: curves
    curv = collections.OrderedDict()
    curv['voynich_ZL'] = curves(vw)
    curv['voynich_ZL_merged'] = {'len_hist': curves([''.join(tok_merge2(w)) for w in vw])['len_hist']}
    m2len = collections.Counter(min(len(tok_merge2(w)), 15) for w in vw)
    curv['voynich_ZL_merged']['len_hist'] = {str(k): m2len.get(k, 0) / N for k in range(1, 16)}
    for lg in ('la', 'it', 'en'):
        curv['gutenberg_' + lg] = curves(a4.lang_words(lg, N))
    for name, ws in words.items():
        curv[name] = curves(ws)
    gib, _ = b3.load_gibberish()
    curv['gaskell_gibberish_10k'] = curves(gib)
    curv['voynich_ZL_10k'] = curves(vw[:len(gib)])
    shipped = b3.read_cipher_lines(os.path.join(b3.NAIBBE_DIR, 'encrypted_nathist_output_ciphertext.txt'))
    curv['naibbe_pliny'] = curves([w for ws, _ in shipped for w in ws][:N])
    curv['autocopist_s19'] = curves(b3.words_of(corpora['autocopist_s19']))
    mz = {n: xf[n]['mz_curve'] for n in full}

    out = {'meta': {'N': N, 'N_short': N_short, 'seed': SEED, 'corpora': meta, 'items': b3.ITEMS,
                    'short_only': sorted(short_only), 'runtime_s': round(time.time() - t0, 1)},
           'h2_conventions': part1, 'full': full, 'short': short, 'extra_full': xf, 'extra_short': xs,
           'tol_full': tol_f, 'tol_short': tol_s, 'marks_full': marks_f, 'marks_short': marks_s,
           'matches_full': {n: sum(m.values()) for n, m in marks_f.items()},
           'matches_short': {n: sum(m.values()) for n, m in marks_s.items()},
           'curves': curv, 'mz_curves': mz}
    json.dump(out, open(os.path.join(OUT, 'c1.json'), 'w', encoding='utf-8'), indent=1, default=str)
    write_md(out)
    log(f'done in {out["meta"]["runtime_s"]}s')


def write_md(R):
    L = ['# c1: comparators after RBA (Sept 2026) and Ilya A. (Oct 2026): conlangs, low-h2 languages, Markov chains', '',
         'Script `c1_comparators.py`; method and caveats in its docstring.  All output unvalidated until reviewed.', '',
         '## 1. h2 under both conventions (every corpus cut to %d tokens)' % R['meta']['N'], '',
         '| corpus | group | h2 with space (L&B) | alphabet incl. space | h2 no space | alphabet | h1 no space |', '|---|---|---|---|---|---|---|']
    for k, v in R['h2_conventions'].items():
        L.append(f"| {v['label']} | {v['group']} | {v['with_space']['h2']:.3f} | {v['with_space']['alphabet']} | "
                 f"{v['no_space']['h2']:.3f} | {v['no_space']['alphabet']} | {v['no_space']['h1']:.3f} |")
    L += ['', 'Lindemann & Bowern 2021 Appendix B (data/lb2021_wikipedia_h2.tsv) give, with the space: Hawaiian 2.765, '
          'Maori 2.875, Tswana 2.816, lowest of 306 Wikipedia samples; their Voynich Full Maximal 2.114, Minimal 2.475.', '',
          '## 2. b3 battery: matches to voynich_ZL under b3\'s tolerance rule (37 items)', '',
          '| corpus | full | short |', '|---|---|---|']
    for n in R['short']:
        L.append(f"| {n} | {R['matches_full'].get(n, '-')} | {R['matches_short'][n]} |")
    keys = ['a_h2_raw', 'a_h2_mrg', 'b_len_mean', 'b_len_sd', 'c_zipf', 'c_hapax_types', 'c_ttr', 'd_adj_exact', 'e_ratio',
            'f_lock', 'h_peak_R', 'i_tok_acc']
    L += ['', '## 3. Selected items, full length (short battery for the Tatoeba corpora that are shorter)', '',
          '| corpus | ' + ' | '.join(keys) + ' |', '|---|' + '---|' * len(keys)]
    for n in R['short']:
        src = R['full'].get(n) or R['short'][n]
        L.append(f'| {n} | ' + ' | '.join(b3.fmt(src[k]) for k in keys) + ' |')
    L += ['', 'Short-only corpora (fewer than %d tokens): %s.' % (R['meta']['N'], ', '.join(R['meta']['short_only']) or 'none'), '']
    open(os.path.join(OUT, 'c1.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')


if __name__ == '__main__':
    main()
