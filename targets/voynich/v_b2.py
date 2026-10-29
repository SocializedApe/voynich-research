"""v_b2.py -- adversarial verification of b2_longrange.py (pure Python stdlib, seeded, deterministic).

Independently recomputes, with its own code (nothing imported from b2 or a4):
  1. Montemurro-Zanette information I(s) = sum_w p(w) [E_shuffle H_w(s) - H_w(s)], with the shuffled expectation
     computed ANALYTICALLY (hypergeometric occupancy of P = N'/s blocks, text truncated to N' = P*s tokens first), as
     MZ 2010/2013 do; plus a 20-shuffle Monte-Carlo cross-check of the analytic term and a b2-style variant
     (shuffle the whole text, then drop the tail) to locate any difference.  Voynich, Currier A, Currier B, one
     shuffled Voynich, Latin, English, Italian (September slice); length-matched Latin/English windows at the A and
     B lengths; full-length Confessiones and Pride and Prejudice (MZ 2013 used whole books); coverage of the
     frequency >= 20 words.
  2. Adjacent-page JSD ratio raw / within hand / within hand+section, with extra controls: page order shuffled
     within hand; and, for every text, tokens shuffled globally and re-poured (page-length-only effect) and tokens
     shuffled within each hand x section stratum and re-poured ('each page an independent draw from its section').
  3. MI(section; word | hand): 500 within-hand label permutations, 500 within-hand rotations, per hand, per
     hand x quire stratum; and a crossed test on hand 1 that separates the drawing from the gathering
     (herbal drawings in the pharma quires O/Q/S against herbal drawings in the herbal quires and pharma pages).
  4. Spherical k-means on TF-IDF (words ranked 21-520), 10 seeds x 10 restarts; ARI, NMI and homogeneity
     against section, hand and Currier language.
  5. A stronger positive control than b2's: a 'compilation' book whose Voynich sections are filled from different
     works (English: three novels; German: four), poured into the Voynich skeleton with the real hand/quire labels.
Writes results/v_b2.json.  Does not touch b2 files.
"""
import os as _os  # local paths (the September 2026 scripts hard-coded another machine)
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_CORP = _os.path.join(_HERE, 'data', 'corpora')  # corp_<lang>_<gutenberg id>.txt, see fetch_corpora.py
_EXT = _os.path.join(_HERE, 'data', 'external')  # third-party data (Naibbe, Gaskell & Bowern)
_IT = _os.path.join(_CORP, 'corpus_it.txt')  # vatican5 OCR corpus from the September sample's first words (fetch_corpora.py)
_IT_V5 = _os.path.join(_HERE, '..', 'vatican5', 'corpus_it.txt')  # today's rebuilt vatican5 corpus (only to show the drift)
import csv, math, json, random, collections, re, time

DATA = _os.path.join(_HERE, 'data', 'ZL3b-n.words.tsv')
RES = _os.path.join(_HERE, 'results')
IT_SEPT_MARK = 'cumque predictus fcrdiuandu'   # first words of the September corpus_it.txt (v_a4.md, v_a6.md)
WORD = re.compile(r"[^\W\d_]+")
T0 = time.time()
LN2 = math.log(2)


def log(*a):
    print(f"[{time.time() - T0:6.1f}s]", *a, flush=True)


def ent(counts):
    """Shannon entropy in bits of an iterable of non-negative counts."""
    counts = [c for c in counts if c > 0]
    n = sum(counts)
    if n == 0:
        return 0.0
    return math.log2(n) - sum(c * math.log2(c) for c in counts) / n

# ------------------------------------------------------------------------------------------------ data


def load_pages():
    pages = collections.OrderedDict()
    raw = q = other = 0
    with open(DATA, encoding='utf-8') as fh:
        for row in csv.DictReader(fh, delimiter='\t'):
            if row['locus_type'] != 'P':
                continue
            lab = {'lang': row['lang'], 'hand': row['hand'], 'sec': row['illus'], 'quire': row['quire']}
            p = pages.get(row['folio'])
            if p is None:
                p = pages[row['folio']] = dict(lab, page=row['folio'], toks=[])
            elif any(p[k] != v for k, v in lab.items()):
                raise SystemExit('page variables change inside page %s' % row['folio'])
            for w in row['line_words'].split():
                raw += 1
                if '?' in w:
                    q += 1
                elif not re.fullmatch(r'[a-z]+', w):
                    other += 1
                else:
                    p['toks'].append(w)
    return [p for p in pages.values() if p['toks']], {'raw_P_words': raw, 'dropped_qmark': q, 'dropped_other': other}


def gutenberg(path):
    t = open(path, encoding='utf-8', errors='replace').read()
    a = t.find('*** START OF')
    if a >= 0:
        t = t[t.find('\n', a) + 1:]
    b = t.find('*** END OF')
    if b >= 0:
        t = t[:b]
    return re.sub(r'\[(?:Sidenote|Illustration)[^\]]*\]', ' ', t)


def corpus(name):
    """Full token list of a control text (no truncation)."""
    if name in ('la', 'la_body'):
        t = gutenberg(_os.path.join(_CORP, 'corp_la_33849.txt'))
        if name == 'la_body':   # the thirteen books only: cut before the Annales, notes, index and errata
            t = t[:t.find('AUGUSTINIANI ANNALES')]
        return [w for w in WORD.findall(t.lower()) if w != 'sidenote']
    if name == 'en':
        t = gutenberg(_os.path.join(_CORP, 'corp_en_1342.txt'))
        i = t.find('It is a truth universally acknowledged')
        t = t[i:] if i >= 0 else t
        t = re.sub(r'(?m)^[ \t]*CHAPTER[ \t]+[IVXLC]+\.?[ \t]*$', ' ', t)
        return WORD.findall(t.lower())
    if name in ('it_sept', 'it_file'):
        src = _IT if name == 'it_sept' or not _os.path.exists(_IT_V5) else _IT_V5
        t = open(src, encoding='utf-8', errors='replace').read()
        if name == 'it_sept':
            i = t.find(IT_SEPT_MARK)
            t = t[i:i + 2_000_000] if i >= 0 else t[:2_000_000]
        else:
            t = t[:2_000_000]
        return WORD.findall(t.lower())
    lang, gid = name.split('_')
    return WORD.findall(gutenberg(_os.path.join(_CORP, 'corp_%s_%s.txt' % (lang, gid))).lower())


def pour(tokens, pages):
    out, k = [], 0
    for p in pages:
        n = len(p['toks'])
        e = dict(p)
        e['toks'] = tokens[k:k + n]
        k += n
        out.append(e)
    assert k <= len(tokens)
    return out

# ------------------------------------------------------------------------------------------------ 1. MZ


def lchoose(a, b):
    return math.lgamma(a + 1) - math.lgamma(b + 1) - math.lgamma(a - b + 1)


_EH = {}


def expected_shuffled_H(n, s, Np):
    """E[entropy (bits) of the distribution over P = Np/s equal blocks of n tokens dropped at random positions].
    Each block's count is hypergeometric(Np, s, n); E[H] = -P * sum_k Pr(k) (k/n) log2(k/n)."""
    key = (n, s, Np)
    if key in _EH:
        return _EH[key]
    P = Np // s
    base = lchoose(Np, n)
    acc = 0.0
    for k in range(max(1, n - (Np - s)), min(n, s) + 1):
        lp = lchoose(s, k) + lchoose(Np - s, n - k) - base
        if lp < -60:
            continue
        x = k / n
        acc += math.exp(lp) * x * math.log2(x)
    _EH[key] = -P * acc
    return _EH[key]


def block_H(seq_ids, nw, s, P):
    counts = [collections.Counter() for _ in range(nw)]
    for j in range(P):
        for i in seq_ids[j * s:(j + 1) * s]:
            if i >= 0:
                counts[i][j] += 1
    return [ent(c.values()) for c in counts], [sum(c.values()) for c in counts]


def mz(tokens, scales, minfreq=20, mc=0, mc_b2style=0, rng=None, top=0):
    """Analytic MZ curve.  mc: also a Monte-Carlo shuffle estimate of the same (truncated) quantity;
    mc_b2style: shuffle the full text and drop the tail afterwards, weights n_full/N (b2's estimator)."""
    N = len(tokens)
    f = collections.Counter(tokens)
    words = sorted((w for w, c in f.items() if c >= minfreq), key=lambda w: (-f[w], w))
    wid = {w: i for i, w in enumerate(words)}
    ids = [wid.get(w, -1) for w in tokens]
    out = {'N': N, 'n_types_ge_minfreq': len(words), 'coverage': sum(f[w] for w in words) / N, 'curve': {}}
    for s in scales:
        P = N // s
        if P < 2:
            continue
        Np = P * s
        H, n = block_H(ids, len(words), s, P)
        terms = []
        for i, w in enumerate(words):
            if n[i] == 0:
                terms.append(0.0)
                continue
            terms.append(n[i] / Np * (expected_shuffled_H(n[i], s, Np) - H[i]))
        rec = {'I': sum(terms)}
        if mc:
            acc = [0.0] * len(words)
            for _ in range(mc):
                sh = ids[:Np]
                rng.shuffle(sh)
                hh, _n = block_H(sh, len(words), s, P)
                for i in range(len(words)):
                    acc[i] += hh[i]
            rec['I_mc'] = sum(n[i] / Np * (acc[i] / mc - H[i]) for i in range(len(words)) if n[i])
        if mc_b2style:
            acc = [0.0] * len(words)
            for _ in range(mc_b2style):
                sh = ids[:]
                rng.shuffle(sh)
                hh, _n = block_H(sh, len(words), s, P)
                for i in range(len(words)):
                    acc[i] += hh[i]
            rec['I_b2style'] = sum(f[w] / N * (acc[i] / mc_b2style - H[i]) for i, w in enumerate(words))
        out['curve'][s] = rec
        if top:
            rec['top'] = [(words[i], f[words[i]], round(terms[i], 5)) for i in sorted(range(len(words)), key=lambda i: -terms[i])[:top]]
    pk = max(out['curve'], key=lambda s: out['curve'][s]['I'])
    out['peak_scale'], out['peak_I'] = pk, out['curve'][pk]['I']
    return out

# ------------------------------------------------------------------------------------------------ 2. adjacency


def page_dists(pages, topk=300):
    f = collections.Counter()
    first = {}
    for p in pages:
        for w in p['toks']:
            f[w] += 1
            first.setdefault(w, len(first))
    top = set(sorted(f, key=lambda w: (-f[w], first[w]))[:topk])
    D = []
    for p in pages:
        c = collections.Counter(w for w in p['toks'] if w in top)
        n = sum(c.values())
        D.append({w: v / n for w, v in c.items()})
    return D


def jsd_matrix(D):
    Hs = [-sum(x * math.log2(x) for x in d.values()) for d in D]
    M = {}
    for i in range(len(D)):
        for j in range(i + 1, len(D)):
            a, b = D[i], D[j]
            m = 0.0
            for k in set(a) | set(b):
                x = 0.5 * (a.get(k, 0.0) + b.get(k, 0.0))
                m -= x * math.log2(x)
            M[(i, j)] = m - 0.5 * (Hs[i] + Hs[j])
    return M


def adjacency(M, pages, order, strata, rng, n_draw=2000):
    adj = {(min(a, b), max(a, b)) for a, b in zip(order, order[1:])}
    res = {}
    for name, pred in strata.items():
        A = [M[p] for p in adj if pred(pages[p[0]], pages[p[1]])]
        R = [v for p, v in M.items() if p not in adj and pred(pages[p[0]], pages[p[1]])]
        if len(A) < 3 or len(R) < 10:
            res[name] = {'n_adj': len(A), 'n_rand': len(R)}
            continue
        ma, mr = sum(A) / len(A), sum(R) / len(R)
        med = sorted(R)[len(R) // 2]
        r = {'n_adj': len(A), 'n_rand': len(R), 'mean_adj': ma, 'mean_rand': mr, 'ratio': ma / mr,
             'frac_below_median': sum(x < med for x in A) / len(A)}
        if n_draw:
            k = len(A)
            r['p'] = (1 + sum(sum(rng.sample(R, k)) / k <= ma for _ in range(n_draw))) / (n_draw + 1)
        res[name] = r
    return res


STRATA = {
    'all': lambda a, b: True,
    'same_hand': lambda a, b: a['hand'] == b['hand'] != '?',
    'same_hand_section': lambda a, b: a['hand'] == b['hand'] != '?' and a['sec'] == b['sec'],
    'same_hand_section_quire': lambda a, b: a['hand'] == b['hand'] != '?' and a['sec'] == b['sec'] and a['quire'] == b['quire'],
    'different_hand': lambda a, b: a['hand'] != b['hand'] and '?' not in (a['hand'], b['hand']),
}

# ------------------------------------------------------------------------------------------------ 3. MI


class MI:
    """MI(label; word) over frequent words, computed inside strata and pooled with token weights."""

    def __init__(self, pages, minfreq=20):
        f = collections.Counter(w for p in pages for w in p['toks'])
        vocab = sorted(w for w, c in f.items() if c >= minfreq)
        vid = {w: i for i, w in enumerate(vocab)}
        self.V = len(vocab)
        self.pc = [collections.Counter(vid[w] for w in p['toks'] if w in vid) for p in pages]
        self.pn = [sum(c.values()) for c in self.pc]
        self.total = sum(self.pn)

    def stratum(self, members, labels):
        n = sum(self.pn[i] for i in members)
        if n == 0 or len({labels[i] for i in members}) < 2:
            return 0.0, n
        sw = collections.defaultdict(collections.Counter)
        ns = collections.Counter()
        nw = collections.Counter()
        for i in members:
            sw[labels[i]].update(self.pc[i])
            ns[labels[i]] += self.pn[i]
            nw.update(self.pc[i])
        hsw = ent(v for c in sw.values() for v in c.values())
        return ent(ns.values()) + ent(nw.values()) - hsw, n

    def pooled(self, groups, labels):
        return sum(m * n for m, n in (self.stratum(g, labels) for g in groups)) / self.total


def groups_of(keys):
    g = collections.OrderedDict()
    for i, k in enumerate(keys):
        g.setdefault(k, []).append(i)
    return list(g.values())


def permute_within(labels, groups, rng):
    lab = labels[:]
    for g in groups:
        v = [labels[i] for i in g]
        rng.shuffle(v)
        for i, x in zip(g, v):
            lab[i] = x
    return lab


def rotate_within(labels, groups, rng):
    lab = labels[:]
    for g in groups:
        if len(g) > 1:
            r = rng.randrange(1, len(g))
            v = [labels[i] for i in g]
            v = v[r:] + v[:r]
            for i, x in zip(g, v):
                lab[i] = x
    return lab


def null_summary(obs, null):
    m = sum(null) / len(null)
    sd = (sum((x - m) ** 2 for x in null) / (len(null) - 1)) ** 0.5
    return {'obs': obs, 'null_mean': m, 'null_sd': sd, 'excess': obs - m, 'z': (obs - m) / sd if sd else None,
            'p': (1 + sum(x >= obs for x in null)) / (1 + len(null))}


def mi_given_hand(pages, labels, rng, n_perm=500, rotate=True):
    mi = MI(pages)
    hands = [p['hand'] for p in pages]
    G = groups_of(hands)
    obs = mi.pooled(G, labels)
    res = {'given_hand_perm': null_summary(obs, [mi.pooled(G, permute_within(labels, G, rng)) for _ in range(n_perm)])}
    if rotate:
        res['given_hand_rot'] = null_summary(obs, [mi.pooled(G, rotate_within(labels, G, rng)) for _ in range(n_perm)])
    obs_m = mi.pooled([list(range(len(pages)))], labels)
    res['marginal_perm_within_hand'] = null_summary(obs_m, [mi.pooled([list(range(len(pages)))], permute_within(labels, G, rng)) for _ in range(n_perm // 2)])
    per = {}
    for g in G:
        h = hands[g[0]]
        if len({labels[i] for i in g}) < 2:
            continue
        o = mi.stratum(g, labels)[0]
        per[h] = null_summary(o, [mi.stratum(g, permute_within(labels, [g], rng))[0] for _ in range(n_perm)])
        per[h]['n_pages'] = len(g)
    res['per_hand'] = per
    HQ = groups_of([p['hand'] + '/' + p['quire'] for p in pages])
    o = mi.pooled(HQ, labels)
    res['given_hand_quire_perm'] = null_summary(o, [mi.pooled(HQ, permute_within(labels, HQ, rng)) for _ in range(n_perm // 2)])
    strata = {}
    for g in HQ:
        if len({labels[i] for i in g}) < 2:
            continue
        key = pages[g[0]]['hand'] + '/' + pages[g[0]]['quire']
        o = mi.stratum(g, labels)[0]
        r = null_summary(o, [mi.stratum(g, permute_within(labels, [g], rng))[0] for _ in range(1000)])
        r['labels'] = dict(collections.Counter(labels[i] for i in g))
        r['tokens'] = sum(mi.pn[i] for i in g)
        strata[key] = r
    res['hand_quire_strata'] = strata
    return res


def unigram_llr(pages, A, B, test, alpha=0.5, minfreq=5):
    """Per-token log2 likelihood ratio log P_B(page)/P_A(page) under add-alpha unigram models of page sets A and
    B (pages in A or B are left out of their own model).  Positive = closer to B."""
    f = collections.Counter(w for p in pages for w in p['toks'])
    vocab = {w for w, c in f.items() if c >= minfreq}
    pc = [collections.Counter(w if w in vocab else '<unk>' for w in p['toks']) for p in pages]
    V = len(vocab) + 1
    cA = collections.Counter()
    cB = collections.Counter()
    for i in A:
        cA.update(pc[i])
    for i in B:
        cB.update(pc[i])
    nA, nB = sum(cA.values()), sum(cB.values())
    out = {}
    for i in test:
        a, b, na, nb = cA, cB, nA, nB
        if i in A:
            a = cA - pc[i]; na = nA - len(pages[i]['toks'])
        if i in B:
            b = cB - pc[i]; nb = nB - len(pages[i]['toks'])
        s = sum(v * (math.log2((b[w] + alpha) / (nb + alpha * V)) - math.log2((a[w] + alpha) / (na + alpha * V)))
                for w, v in pc[i].items())
        out[pages[i]['page']] = s / len(pages[i]['toks'])
    return out


def crossed_hand1(pages, rng):
    """Hand 1 draws herbal pages both in the herbal quires (A-G) and inside the pharma quires (O, Q, S).
    If the text follows the drawing, the herbal pages in the pharma quires read like herbal pages; if it follows
    the gathering (time of writing), they read like the pharma pages around them."""
    pharmaQ = {'O', 'Q', 'S'}
    g1 = [i for i, p in enumerate(pages) if p['hand'] == '1' and p['sec'] == 'H' and p['quire'] not in pharmaQ]
    g2 = [i for i, p in enumerate(pages) if p['hand'] == '1' and p['sec'] == 'H' and p['quire'] in pharmaQ]
    g3 = [i for i, p in enumerate(pages) if p['hand'] == '1' and p['sec'] == 'P']
    mi = MI(pages)
    res = {'n_pages': {'H_in_herbal_quires': len(g1), 'H_in_pharma_quires': len(g2), 'P': len(g3)},
           'pages_H_in_pharma_quires': [pages[i]['page'] + '/' + pages[i]['quire'] for i in g2]}
    lab_draw = {i: ('H' if i in g2 else 'P') for i in g2 + g3}
    lab_quire = {i: ('herbalQ' if i in g1 else 'pharmaQ') for i in g1 + g2}
    lab_3 = {i: ('H_herbQ' if i in g1 else 'H_pharmQ' if i in g2 else 'P') for i in g1 + g2 + g3}
    for name, lab, mem in (('drawing_within_pharma_quires_(H_vs_P)', lab_draw, g2 + g3),
                           ('gathering_within_herbal_drawings_(herbalQ_vs_pharmaQ)', lab_quire, g1 + g2)):
        labels = [lab.get(i) for i in range(len(pages))]
        o = mi.stratum(mem, labels)[0]
        null = []
        for _ in range(2000):
            v = [labels[i] for i in mem]
            rng.shuffle(v)
            l2 = labels[:]
            for i, x in zip(mem, v):
                l2[i] = x
            null.append(mi.stratum(mem, l2)[0])
        res[name] = null_summary(o, null)
        res[name]['tokens'] = sum(mi.pn[i] for i in mem)
    # likelihood-ratio placement of every hand-1 page between the herbal-quire herbal model and the pharma model
    llr = unigram_llr(pages, g1, g3, g1 + g2 + g3)
    def summ(g):
        v = sorted(llr[pages[i]['page']] for i in g)
        return {'mean': sum(v) / len(v), 'median': v[len(v) // 2], 'frac_pharma_like': sum(x > 0 for x in v) / len(v)}
    res['llr_bits_per_token_(+ = pharma-like)'] = {'H_in_herbal_quires_LOO': summ(g1), 'H_in_pharma_quires': summ(g2),
                                                    'P_LOO': summ(g3),
                                                    'per_page_H_in_pharma_quires': {pages[i]['page']: round(llr[pages[i]['page']], 3) for i in g2}}
    # the same three-way split as one MI table: does 'H in pharma quires' group with H or with P?
    labels3 = [lab_3.get(i) for i in range(len(pages))]
    sub = g1 + g2 + g3
    def mi_pair(x, y):
        mem = [i for i in sub if labels3[i] in (x, y)]
        return mi.stratum(mem, labels3)[0]
    res['pairwise_MI_bits'] = {'H_herbQ_vs_H_pharmQ': mi_pair('H_herbQ', 'H_pharmQ'), 'H_pharmQ_vs_P': mi_pair('H_pharmQ', 'P'),
                               'H_herbQ_vs_P': mi_pair('H_herbQ', 'P')}
    return res

# ------------------------------------------------------------------------------------------------ 4. k-means


def tfidf(pages, skip=20, keep=500):
    f = collections.Counter()
    first = {}
    for p in pages:
        for w in p['toks']:
            f[w] += 1
            first.setdefault(w, len(first))
    vocab = sorted(f, key=lambda w: (-f[w], first[w]))[skip:skip + keep]
    vid = {w: i for i, w in enumerate(vocab)}
    df = collections.Counter(w for p in pages for w in set(p['toks']) if w in vid)
    n = len(pages)
    vecs = []
    for p in pages:
        c = collections.Counter(w for w in p['toks'] if w in vid)
        v = [(vid[w], k / len(p['toks']) * math.log(n / df[w])) for w, k in c.items()]
        norm = math.sqrt(sum(x * x for _, x in v)) or 1.0
        vecs.append([(i, x / norm) for i, x in v])
    return vecs, len(vocab)


def skmeans(vecs, dim, k, rng, restarts=10, iters=100):
    n = len(vecs)
    def dot(v, c):
        return sum(x * c[i] for i, x in v)
    def dense(v):
        c = [0.0] * dim
        for i, x in v:
            c[i] = x
        return c
    best = None
    for _ in range(restarts):
        C = [dense(vecs[rng.randrange(n)])]
        while len(C) < k:
            d = [min(1.0 - dot(v, c) for c in C) for v in vecs]
            d = [max(0.0, x) ** 2 for x in d]
            r = rng.random() * sum(d)
            acc = 0.0
            pick = n - 1
            for i, x in enumerate(d):
                acc += x
                if acc >= r:
                    pick = i
                    break
            C.append(dense(vecs[pick]))
        assign = None
        for _it in range(iters):
            sims = [[dot(v, c) for c in C] for v in vecs]
            new = [max(range(k), key=lambda j: s[j]) for s in sims]
            if new == assign:
                break
            assign = new
            C = []
            for j in range(k):
                c = [0.0] * dim
                for i in range(n):
                    if assign[i] == j:
                        for a, x in vecs[i]:
                            c[a] += x
                nm = math.sqrt(sum(x * x for x in c))
                if nm == 0:   # empty cluster: the worst-fitting point
                    w = min(range(n), key=lambda i: sims[i][assign[i]])
                    c = dense(vecs[w]); nm = 1.0
                C.append([x / nm for x in c])
        inertia = sum(1.0 - dot(vecs[i], C[assign[i]]) for i in range(n))
        if best is None or inertia < best[0]:
            best = (inertia, assign)
    return best[1]


def comb2(x):
    return x * (x - 1) / 2


def ari(a, b):
    n = len(a)
    s_ab = sum(comb2(v) for v in collections.Counter(zip(a, b)).values())
    s_a = sum(comb2(v) for v in collections.Counter(a).values())
    s_b = sum(comb2(v) for v in collections.Counter(b).values())
    e = s_a * s_b / comb2(n)
    mx = (s_a + s_b) / 2
    return (s_ab - e) / (mx - e) if mx != e else 0.0


def nmi_h(clusters, labels):
    Hc, Hl = ent(collections.Counter(clusters).values()), ent(collections.Counter(labels).values())
    I = Hc + Hl - ent(collections.Counter(zip(clusters, labels)).values())
    return (I / math.sqrt(Hc * Hl) if Hc and Hl else 0.0), (I / Hl if Hl else None)


def cluster_runs(pages, label_key, seeds, tag):
    vecs, dim = tfidf(pages)
    k = len({p[label_key] for p in pages})
    out = collections.defaultdict(list)
    for sd in seeds:
        cl = skmeans(vecs, dim, k, random.Random(sd))
        for lk in ('sec', 'hand', 'lang'):
            lab = [p[lk] for p in pages]
            out['ARI_' + lk].append(ari(cl, lab))
            nm, hom = nmi_h(cl, lab)
            out['NMI_' + lk].append(nm)
            out['homog_' + lk].append(hom)
    def st(v):
        v = sorted(x for x in v if x is not None)
        return {'median': v[len(v) // 2], 'min': v[0], 'max': v[-1]} if v else None
    return dict({'tag': tag, 'n_pages': len(pages), 'k': k, 'seeds': len(seeds)}, **{m: st(v) for m, v in out.items()})


def subset_big_sections(pages, pred):
    sub = [p for p in pages if pred(p)]
    c = collections.Counter(p['sec'] for p in sub)
    return [p for p in sub if c[p['sec']] >= 3]

# ------------------------------------------------------------------------------------------------ 5. compilation control


def compilation(pages, works, section_to_work, skip_front=3000):
    streams = {}
    for w in works:
        streams[w] = corpus('en') if w == 'en_1342' else corpus(w)[skip_front:]   # P&P from its first sentence
    pos = collections.Counter()
    out = []
    for p in pages:
        w = works[section_to_work[p['sec']]]
        n = len(p['toks'])
        e = dict(p)
        e['toks'] = streams[w][pos[w]:pos[w] + n]
        assert len(e['toks']) == n, (w, pos[w], n)
        pos[w] += n
        out.append(e)
    return out, dict(pos)

# ------------------------------------------------------------------------------------------------ run


def main():
    R = {}
    rng = random.Random(20261011)
    pages, drop = load_pages()
    toks = [w for p in pages for w in p['toks']]
    N = len(toks)
    R['data'] = dict(drop, pages=len(pages), tokens=N, types=len(set(toks)),
                     sections=dict(collections.Counter(p['sec'] for p in pages)),
                     hands=dict(collections.Counter(p['hand'] for p in pages)))
    log('Voynich', R['data'])
    full = {'la': corpus('la'), 'en': corpus('en'), 'it_sept': corpus('it_sept'), 'it_file': corpus('it_file'),
            'la_body': corpus('la_body')}
    ctrl = {k: v[:N] for k, v in full.items()}
    R['controls'] = {k: {'tokens_loaded': len(full[k]), 'types_at_N': len(set(ctrl[k])), 'first_words': ' '.join(ctrl[k][:8])} for k in full}
    log('controls', R['controls'])

    # ---- 1. MZ
    SC = [50, 100, 200, 400, 800, 1600, 3200, 6400]
    SCF = [50, 100, 200, 300, 400, 600, 800, 1200, 1600, 2400, 3200, 6400]
    shuf = toks[:]
    rng.shuffle(shuf)
    A = [w for p in pages if p['lang'] == 'A' for w in p['toks']]
    B = [w for p in pages if p['lang'] == 'B' for w in p['toks']]
    mzr = {}
    mzr['voynich'] = mz(toks, SC, mc=20, mc_b2style=20, rng=rng, top=10)
    for name, t in (('voynich_shuffled', shuf), ('voynich_A', A), ('voynich_B', B), ('latin', ctrl['la']),
                    ('english', ctrl['en']), ('italian_sept', ctrl['it_sept']), ('italian_file_now', ctrl['it_file'])):
        mzr[name] = mz(t, SC, top=6 if name in ('latin', 'english') else 0)
    for name in ('latin', 'english'):
        mzr[name + '_b2style'] = mz(ctrl[name[:2]], [200, 400, 3200, 6400], mc_b2style=20, rng=rng)
    mzr['voynich_fine'] = mz(toks, SCF)
    mzr['latin_full_file'] = mz(full['la'], SCF)
    mzr['latin_full_length'] = mz(full['la_body'], SCF)
    # a real book at the Voynich length whose window straddles a change of genre (end of book XIII -> Annales/notes)
    off = len(full['la_body']) - N // 2
    mzr['latin_window_straddling_text_and_apparatus'] = dict(mz(full['la'][off:off + N], SC), offset=off,
                                                             first_words=' '.join(full['la'][off:off + 8]))
    mzr['english_full_length'] = mz(full['en'], SCF)
    # length-matched windows at the A and B lengths
    for L, nm in ((len(A), 'A'), (len(B), 'B')):
        for lg in ('la_body', 'en'):
            pk = []
            for off in range(0, len(full[lg]) - L + 1, L):
                m = mz(full[lg][off:off + L], SC)
                pk.append((off, m['peak_scale'], m['peak_I']))
            mzr['%s_windows_len_%s' % (lg, nm)] = {'n_tokens': L, 'windows': pk,
                                                    'mean_peak_I': sum(x[2] for x in pk) / len(pk),
                                                    'min_peak_I': min(x[2] for x in pk), 'max_peak_I': max(x[2] for x in pk)}
    R['mz'] = mzr
    log('MZ', {k: (v.get('peak_scale'), round(v.get('peak_I', v.get('mean_peak_I', 0)), 4)) for k, v in mzr.items()})

    # ---- 2. adjacency
    keep = [p for p in pages if len(p['toks']) >= 30]
    order = list(range(len(keep)))
    adj = {}
    texts = {'voynich': keep}
    for nm in ('la', 'en', 'it_sept'):
        texts[nm] = pour(ctrl[nm], keep)
    Ms = {}
    for nm, pg in texts.items():
        Ms[nm] = jsd_matrix(page_dists(pg))
        adj[nm] = adjacency(Ms[nm], pg, order, STRATA, rng)
    # Voynich with the page order shuffled within hand, and everywhere
    for tag, within in (('voynich_order_shuffled_within_hand', True), ('voynich_order_shuffled', False)):
        acc = collections.defaultdict(list)
        for _ in range(50):
            o = order[:]
            if within:
                byh = collections.defaultdict(list)
                for pos_, i in enumerate(order):
                    byh[keep[i]['hand']].append(pos_)
                for ps in byh.values():
                    v = [order[x] for x in ps]
                    rng.shuffle(v)
                    for x, y in zip(ps, v):
                        o[x] = y
            else:
                rng.shuffle(o)
            r = adjacency(Ms['voynich'], keep, o, STRATA, rng, n_draw=0)
            for st, v in r.items():
                if 'ratio' in v:
                    acc[st].append(v['ratio'])
        adj[tag] = {st: {'mean_ratio': sum(v) / len(v), 'n_shuffles': len(v)} for st, v in acc.items()}
    # token-level baselines for every text: tokens shuffled globally (only the page lengths survive) and tokens
    # shuffled inside each hand x section stratum ('each page an independent draw from its stratum'; keeps page
    # lengths and the stratum composition, which the pooled adjacent/random comparison also picks up)
    for (nm, src), (tg, keyf) in [((a, b), c) for a, b in texts.items()
                                  for c in (('tokens_shuffled_globally', lambda p: 0),
                                            ('tokens_shuffled_within_hand_section', lambda p: (p['hand'], p['sec'])))]:
        tag = nm + '_' + tg
        acc = collections.defaultdict(list)
        for _ in range(3):
            pools = collections.defaultdict(list)
            for p in src:
                pools[keyf(p)].extend(p['toks'])
            for v in pools.values():
                rng.shuffle(v)
            ptr = collections.Counter()
            pg = []
            for p in src:
                k_ = keyf(p)
                e = dict(p)
                e['toks'] = pools[k_][ptr[k_]:ptr[k_] + len(p['toks'])]
                ptr[k_] += len(p['toks'])
                pg.append(e)
            r = adjacency(jsd_matrix(page_dists(pg)), pg, order, STRATA, rng, n_draw=0)
            for st, v in r.items():
                if 'ratio' in v:
                    acc[st].append(v['ratio'])
        adj[tag] = {st: {'mean_ratio': sum(v) / len(v), 'min': min(v), 'max': max(v)} for st, v in acc.items()}
    R['adjacency'] = adj
    log('adjacency', {k: round(v['all'].get('ratio', v['all'].get('mean_ratio', 0)), 3) for k, v in adj.items()})

    # ---- 3. MI
    sec = [p['sec'] for p in pages]
    contig = []
    seen = []
    for s in sec:
        if s not in seen:
            seen.append(s)
    sz = collections.Counter(sec)
    for s in seen:
        contig += [s] * sz[s]
    mir = {'voynich': mi_given_hand(pages, sec, rng)}
    for nm in ('la', 'en', 'it_sept'):
        pg = pour(ctrl[nm], pages)
        mir[nm + '_contiguous'] = mi_given_hand(pg, contig, rng, n_perm=200)
        mir[nm + '_voynich_labels'] = mi_given_hand(pg, sec, rng, n_perm=200)
    mir['hand1_crossed_drawing_vs_gathering'] = crossed_hand1(pages, rng)
    R['mi'] = mir
    log('MI given hand', {k: (round(v['given_hand_perm']['excess'], 4), round(v['given_hand_perm']['z'], 1)) for k, v in mir.items() if 'given_hand_perm' in v})
    log('crossed', json.dumps(mir['hand1_crossed_drawing_vs_gathering'], default=str)[:1500])

    # ---- 4. k-means
    seeds = list(range(10))
    km = {'voynich_all': cluster_runs(keep, 'sec', seeds, 'Voynich, all pages >= 30 tokens')}
    for h in ('1', '2', '3'):
        km['voynich_hand_' + h] = cluster_runs(subset_big_sections(keep, lambda p: p['hand'] == h), 'sec', seeds, 'hand ' + h)
    for L in ('A', 'B'):
        km['voynich_currier_' + L] = cluster_runs(subset_big_sections(keep, lambda p: p['lang'] == L), 'sec', seeds, 'Currier ' + L)
    kc = [c for c, p in zip(contig, pages) if len(p['toks']) >= 30]
    for nm in ('la', 'en', 'it_sept'):
        pg = [dict(e, sec=c) for e, c in zip(pour(ctrl[nm], keep), kc)]
        km[nm + '_contiguous'] = cluster_runs(pg, 'sec', seeds[:10], nm + ' pour, contiguous sections')
    R['kmeans'] = km
    log('kmeans ARI_sec', {k: round(v['ARI_sec']['median'], 3) for k, v in km.items()})

    # ---- 5. compilation control (different works per section, real Voynich labels)
    comp = {}
    for lang, works, s2w in (('english', ['en_1342', 'en_2701', 'en_2554'], {'H': 0, 'B': 1, 'S': 2, 'P': 2, 'T': 2, 'C': 2, 'A': 2}),
                             ('german', ['de_35312', 'de_50285', 'de_56156', 'de_66452'], {'H': 0, 'B': 1, 'S': 2, 'P': 3, 'T': 3, 'C': 3, 'A': 3})):
        pg, used = compilation(pages, works, s2w)
        ct = [w for p in pg for w in p['toks']]
        r = {'works': works, 'section_to_work': s2w, 'tokens_used': used}
        r['mz'] = {k: v for k, v in mz(ct, SC).items() if k != 'curve'}
        r['mi'] = mi_given_hand(pg, sec, rng, n_perm=200)
        kp = [p for p in pg if len(p['toks']) >= 30]
        r['adjacency'] = adjacency(jsd_matrix(page_dists(kp)), kp, list(range(len(kp))), STRATA, rng, n_draw=500)
        r['kmeans_all'] = cluster_runs(kp, 'sec', seeds[:10], lang + ' compilation, all pages')
        r['kmeans_hand_2'] = cluster_runs(subset_big_sections(kp, lambda p: p['hand'] == '2'), 'sec', seeds[:10], lang + ' compilation, hand 2')
        comp[lang] = r
        log('compilation', lang, r['mz']['peak_I'], round(r['mi']['given_hand_perm']['excess'], 4), round(r['kmeans_all']['ARI_sec']['median'], 3))
    R['compilation_control'] = comp
    R['claims'] = claims(R)
    R['runtime_s'] = time.time() - T0
    with open(_os.path.join(RES, 'v_b2.json'), 'w', encoding='utf-8') as fh:
        json.dump(R, fh, indent=1, ensure_ascii=False, default=str)
    log('done')
    return R


def claims(R):
    """The b2.md claims checked, with the independent value computed above and the verifier's verdict
    (verdict strings are the verifier's judgement; the numbers are live)."""
    mzr, A, M, K, C = R['mz'], R['adjacency'], R['mi'], R['kmeans'], R['compilation_control']
    f = lambda x, d=4: round(x, d)
    pk = lambda k: '%s / %.4f' % (mzr[k]['peak_scale'], mzr[k]['peak_I'])
    adj = lambda t, st: '%.3f / %.2f' % (A[t][st]['ratio'], A[t][st]['frac_below_median'])
    base = lambda t, st: f(A[t + '_tokens_shuffled_within_hand_section'][st]['mean_ratio'], 3)
    gh = lambda k: M[k]['given_hand_perm']
    ari = lambda k, lab='sec': '%.3f (%.3f..%.3f)' % (K[k]['ARI_' + lab]['median'], K[k]['ARI_' + lab]['min'], K[k]['ARI_' + lab]['max'])
    x = M['hand1_crossed_drawing_vs_gathering']
    llr = x['llr_bits_per_token_(+ = pharma-like)']
    return [
        {'claim': 'MZ Voynich peak 400 tokens, 0.268 bits/token', 'b2': '400 / 0.2677',
         'independent': pk('voynich') + '; fine grid ' + pk('voynich_fine'), 'verdict': 'confirmed (flat top 400-800)'},
        {'claim': 'MZ Latin 0.107 (200), English 0.110 (200)', 'b2': '200 / 0.1071; 200 / 0.1099',
         'independent': pk('latin') + '; ' + pk('english'), 'verdict': 'confirmed'},
        {'claim': 'MZ Italian OCR 0.056 (800)', 'b2': '800 / 0.0560',
         'independent': 'September sample (data/corpora/corpus_it.txt) ' + pk('italian_sept') + '; rebuilt vatican5/corpus_it.txt ' + pk('italian_file_now'),
         'verdict': 'confirmed; reproduced exactly by the b2 re-run on the frozen copy (the rebuilt vatican5 file starts with other OCR volumes)'},
        {'claim': 'MZ shuffled Voynich 0.0013', 'b2': '1600 / 0.0013', 'independent': pk('voynich_shuffled'), 'verdict': 'confirmed (noise floor)'},
        {'claim': 'Currier A 0.111 (Latin-like), B 0.195', 'b2': '200 / 0.1106; 400 / 0.1953',
         'independent': '%s; %s; Latin windows at A length %.3f..%.3f, English %.3f..%.3f; at B length Latin %.3f..%.3f, English %.3f..%.3f' % (
             pk('voynich_A'), pk('voynich_B'), mzr['la_body_windows_len_A']['min_peak_I'], mzr['la_body_windows_len_A']['max_peak_I'],
             mzr['en_windows_len_A']['min_peak_I'], mzr['en_windows_len_A']['max_peak_I'], mzr['la_body_windows_len_B']['min_peak_I'],
             mzr['la_body_windows_len_B']['max_peak_I'], mzr['en_windows_len_B']['min_peak_I'], mzr['en_windows_len_B']['max_peak_I']),
         'verdict': 'confirmed'},
        {'claim': 'top MZ carriers shedy qokain qokeedy qokedy daiin chedy', 'b2': 'same',
         'independent': ' '.join(t[0] for t in mzr['voynich']['curve']['400']['top'][:6]) if '400' in mzr['voynich']['curve'] else
         ' '.join(t[0] for t in mzr['voynich']['curve'][400]['top'][:6]), 'verdict': 'confirmed'},
        {'claim': 'adjacent ratio all 0.81 / 80%', 'b2': '0.81 / 0.80', 'independent': adj('voynich', 'all') + '; no-continuity baseline %.3f' % base('voynich', 'all'),
         'verdict': 'number confirmed; mostly page-length x stratum composition'},
        {'claim': 'same hand+section 0.83 / 78%, books 0.82 / 0.81 / 0.87', 'b2': '0.83; 0.82 0.81 0.87',
         'independent': '%s; %s %s %s; baselines %s %s %s %s' % (adj('voynich', 'same_hand_section'), adj('la', 'same_hand_section'), adj('en', 'same_hand_section'),
                                                             adj('it_sept', 'same_hand_section'), base('voynich', 'same_hand_section'), base('la', 'same_hand_section'),
                                                             base('en', 'same_hand_section'), base('it_sept', 'same_hand_section')),
         'verdict': 'confirmed (residual over baseline in the books range)'},
        {'claim': 'no adjacency effect within a quire', 'b2': '1.00 0.97 1.00',
         'independent': '%s %s %s; baselines %s %s %s' % (adj('voynich', 'same_hand_section_quire'), adj('la', 'same_hand_section_quire'), adj('en', 'same_hand_section_quire'),
                                                       base('voynich', 'same_hand_section_quire'), base('la', 'same_hand_section_quire'), base('en', 'same_hand_section_quire')),
         'verdict': 'corrected'},
        {'claim': 'MI given hand 0.171 vs null 0.083, excess 0.088, z 14.5', 'b2': '0.1709 / 0.0828 / 0.0881 / 14.5',
         'independent': '%.4f / %.4f / %.4f / %.1f' % (gh('voynich')['obs'], gh('voynich')['null_mean'], gh('voynich')['excess'], gh('voynich')['z']),
         'verdict': 'confirmed'},
        {'claim': '5-6x the excess of contiguous cuts of a real book (0.017, 0.025, 0.015, all z 4-5)', 'b2': '0.0167 0.0246 0.0136',
         'independent': 'contiguous %.4f (z %.1f) %.4f (z %.1f) %.4f (z %.1f); compilation of different works %.4f / %.4f' % (
             gh('la_contiguous')['excess'], gh('la_contiguous')['z'], gh('en_contiguous')['excess'], gh('en_contiguous')['z'],
             gh('it_sept_contiguous')['excess'], gh('it_sept_contiguous')['z'], C['english']['mi']['given_hand_perm']['excess'], C['german']['mi']['given_hand_perm']['excess']),
         'verdict': 'corrected (3.4-6x one book; 1.3-1.5x a compilation)'},
        {'claim': 'per hand: 1 = 0.126 z 20.8; 2 = 0.146 z 13.2; 3 = 0.000', 'b2': 'as stated',
         'independent': '; '.join('%s = %.4f z %.1f' % (h, M['voynich']['per_hand'][h]['excess'], M['voynich']['per_hand'][h]['z']) for h in ('1', '2', '3')),
         'verdict': 'confirmed'},
        {'claim': 'conditioning on quire leaves almost nothing because quires are section-pure', 'b2': '0.0027 z 0.8',
         'independent': 'Voynich hand x quire %.4f z %.2f; stratum 1/O z %.2f; compilation hand x quire z %.1f / %.1f, 1/O z %.1f / %.1f' % (
             M['voynich']['given_hand_quire_perm']['excess'], M['voynich']['given_hand_quire_perm']['z'], M['voynich']['hand_quire_strata']['1/O']['z'],
             C['english']['mi']['given_hand_quire_perm']['z'], C['german']['mi']['given_hand_quire_perm']['z'],
             C['english']['mi']['hand_quire_strata']['1/O']['z'], C['german']['mi']['hand_quire_strata']['1/O']['z']),
         'verdict': 'corrected'},
        {'claim': 'drawings predict the words within a scribe; positive evidence of section-conditioned production', 'b2': '-',
         'independent': 'hand-1 herbal pages in pharma quires: LLR %.2f bits/token, %.0f%% pharma-like (herbal quires %.2f, pharma %.2f)' % (
             llr['H_in_pharma_quires']['mean'], 100 * llr['H_in_pharma_quires']['frac_pharma_like'], llr['H_in_herbal_quires_LOO']['mean'], llr['P_LOO']['mean']),
         'verdict': 'corrected (follows the gathering, not the drawing)'},
        {'claim': 'k-means all: ARI section 0.13, hand 0.21, language 0.27', 'b2': '0.134 0.206 0.267',
         'independent': '%s %s %s' % (ari('voynich_all'), ari('voynich_all', 'hand'), ari('voynich_all', 'lang')), 'verdict': 'confirmed within seed range'},
        {'claim': 'hand 2 ARI 0.61; hand 1 0.33; hand 3 -0.03', 'b2': '0.606 0.328 -0.029',
         'independent': '%s %s %s' % (ari('voynich_hand_2'), ari('voynich_hand_1'), ari('voynich_hand_3')), 'verdict': 'confirmed within seed range'},
        {'claim': 'pours ARI about 0; Voynich far sharper than topic structure in real prose', 'b2': '-0.039 -0.001 -0.064',
         'independent': 'pours %s %s %s; compilation %s / %s' % (ari('la_contiguous'), ari('en_contiguous'), ari('it_sept_contiguous'),
                                                               '%.3f' % C['english']['kmeans_all']['ARI_sec']['median'], '%.3f' % C['german']['kmeans_all']['ARI_sec']['median']),
         'verdict': 'numbers confirmed; comparison corrected'},
    ]


if __name__ == '__main__':
    main()
