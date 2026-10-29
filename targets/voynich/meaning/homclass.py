"""Test H2 of homophone_plan.md: are there homophone classes in Voynich? (model-free)

Protocol (homophone_plan.md, fixed 29 Oct 2026; the points the plan left open were fixed here before any run):
  Texts, all on the ZL skeleton (page, line and token counts kept; about 34,800 tokens):
    code_<la|it>_K<4|8|16>_<rand|habit>  plaintext Pliny (pliny.STREAM books, Latin) or the Italian control (a4.IT),
                  cut to Voynich length. Each plaintext word with >= 5 tokens gets K code words, rarer words one. Code
                  words: distinct words of the improviser's template (scribe_systems.Improviser, no habits), assigned
                  at random, so homophones of one word are unrelated in spelling. Choice per token:
                    rand   uniform among the word's homophones
                    habit  H1's generator at its default (the middle of H1's grid): per hand a preference
                           Dirichlet(alpha_s = 0.5) over each word's homophones; per quire Dirichlet(alpha_q = 20 x
                           the hand's preference); within a page the last homophone of that word reused with
                           probability rho = 0.5, else a draw from the quire's preference.
                  Every code passes through the copying scribe (hybrid_model.hybridize, scribe_systems.SCRIBE), as H1.
    negative controls  improv_0.6_0.2 (scribe_systems.Improviser s 0.6, p 0.2); cipher_scribe (round-8 + copying
                  scribe, duel.cipher_habit s = p = 0); naibbe (Greshko's Naibbe, cipher_models.Variant seed 19, Latin);
                  voynich_shuffled (ZL tokens shuffled over the whole text).
    voynich       ZL.
  Vectors: every word type with >= 10 tokens. Left and right neighbour counts within the line (line edges as '#'),
    page counts; each block PPMI with context-distribution smoothing (context counts ^ 0.75), L2-normalised, the
    three blocks concatenated with equal weight. Similarity: cosine.
  Clusters: agglomerative, average linkage, cosine distance; number of clusters by the best silhouette over 40
    values spaced geometrically from 5 to n/2.
  ARI (synthetic codes only): pair-counting ARI of clusters against the true homophone sets, over pairs of labelled
    types (types that are code words) at glyph edit distance >= 3.
  No-answer score: S = mean similarity of the top 1% of pairs at glyph edit distance >= 3. Null: tokens shuffled
    within each page (keeps each type's page vector, breaks its neighbours), 200 permutations. Excess E = S - mean(null);
    a text's 95th percentile is E + (95th percentile of null - mean(null)).
  Power check (pass rule of the plan): at K 8 habit, in both languages, ARI >= 0.3 and E above every negative control's
    95th percentile. If it fails, the test cannot decide at Voynich's length; record that and stop.
  Reading, only if it passes: Voynich at or below the controls counts against a homophonic word code; above them, a
    positive (to be followed up on hand 2 B pages).

Run from the repository root: python targets/voynich/meaning/homclass.py <naibbe_tables.csv>
"""
import collections, csv, json, math, os, random, sys, tempfile
import numpy as np
from rapidfuzz.distance import Levenshtein
from rapidfuzz.process import cdist
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.metrics import silhouette_score
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'research', 'voynich_siblings'))
import scribe_systems as ss
import duel
import pliny
import a4_selfcitation as a4
import b3_bakeoff as b3
import hybrid_model as hm
import cipher_models as cm
from variants import UNIT

MIN_TOK, PERMS, TOP = 10, 200, 0.01
HABIT = (0.5, 20.0, 0.5)   # alpha_s, alpha_q, rho


# ------------------------------------------------------------------ texts
def code_words(allw, n, seed):
    imp = ss.Improviser(allw, 0.0, 0.0, seed); out, seen = [], set()
    for _ in range(60 * n):
        w = imp.word({}, {})
        if w and w not in seen:
            seen.add(w); out.append(w)
            if len(out) == n:
                return out
    raise RuntimeError(f'only {len(out)} distinct code words of {n}')


def encode(zl, hand_of, quire_of, plain, K, mode, allw, seed):
    rng = random.Random(seed); nrng = np.random.default_rng(seed)
    freq = collections.Counter(plain)
    ks = {w: (K if n >= 5 else 1) for w, n in freq.items()}
    pool = code_words(allw, sum(ks.values()), seed); rng.shuffle(pool)
    codes, i = {}, 0
    for w in freq:
        codes[w] = pool[i:i + ks[w]]; i += ks[w]
    a_s, a_q, rho = HABIT; hpref, qpref = {}, {}
    def quire_p(w, h, q):
        k = (w, h, q)
        if k not in qpref:
            hp = hpref.setdefault((w, h), nrng.dirichlet([a_s] * ks[w]))
            qpref[k] = nrng.dirichlet(np.maximum(a_q * hp, 1e-3))
        return qpref[k]
    pos, pages = 0, []
    for p in zl:
        h, q = hand_of[p['folio']], quire_of[p['folio']]; last = {}; lines = []
        for ln in p['lines']:
            out = []
            for _ in ln['words']:
                w = plain[pos % len(plain)]; pos += 1
                if ks[w] == 1:
                    j = 0
                elif mode == 'rand':
                    j = rng.randrange(ks[w])
                elif w in last and rng.random() < rho:
                    j = last[w]
                else:
                    pr = quire_p(w, h, q); j = int(nrng.choice(ks[w], p=pr / pr.sum()))
                last[w] = j; out.append(codes[w][j])
            lines.append({'words': out, 'para_start': ln['para_start']})
        pages.append({'folio': p['folio'], 'lang': p['lang'], 'lines': lines})
    label = {c: w for w, cs in codes.items() for c in cs}
    return scribe(pages), label


def scribe(pages):
    q, w, e, g = ss.SCRIBE; out = hm.hybridize(pages, random.Random(7), q, w, e, g)
    for a, b in zip(out, pages):
        a['folio'], a['lang'] = b['folio'], b['lang']
    return out


def pour(zl, words):
    it = iter(words); pages = []
    for p in zl:
        lines = [{'words': [next(it) for _ in ln['words']], 'para_start': ln['para_start']} for ln in p['lines']]
        pages.append({'folio': p['folio'], 'lang': p['lang'], 'lines': lines})
    return pages


# ------------------------------------------------------------------ measures
class Space:
    """token arrays for one text: type id, page id, line id; contexts over all types + '#'"""
    def __init__(self, pages):
        toks, pg, li = [], [], []; L = 0
        for i, p in enumerate(pages):
            for ln in p['lines']:
                for w in ln['words']:
                    toks.append(w); pg.append(i); li.append(L)
                L += 1
        c = collections.Counter(toks)
        self.vocab = ['#'] + sorted(c); idx = {w: i for i, w in enumerate(self.vocab)}
        self.tok = np.array([idx[w] for w in toks]); self.page = np.array(pg); self.line = np.array(li)
        self.npage = len(pages)
        self.targets = np.array([idx[w] for w in sorted(c) if c[w] >= MIN_TOK])
        self.row = -np.ones(len(self.vocab), int); self.row[self.targets] = np.arange(len(self.targets))
        self.words = [self.vocab[i] for i in self.targets]
        u = sorted({g for w in self.words for g in UNIT.findall(w)}); m = {g: chr(0x100 + i) for i, g in enumerate(u)}
        enc = [''.join(m[g] for g in UNIT.findall(w)) for w in self.words]
        self.ed = cdist(enc, enc, scorer=Levenshtein.distance, workers=-1)
        iu = np.triu_indices(len(self.words), 1); keep = self.ed[iu] >= 3
        self.pairs = (iu[0][keep], iu[1][keep])
        page_order = np.argsort(self.page, kind='stable'); self.page_bounds = np.searchsorted(self.page[page_order], np.arange(self.npage + 1))
        self.page_order = page_order

    def vectors(self, tok):
        n, V = len(self.targets), len(self.vocab)
        same = self.line[1:] == self.line[:-1]
        left = np.where(np.r_[False, same], np.r_[0, tok[:-1]], 0)
        right = np.where(np.r_[same, False], np.r_[tok[1:], 0], 0)
        r = self.row[tok]; m = r >= 0
        blocks = []
        for ctx, size in ((left[m], V), (right[m], V), (self.page[m], self.npage)):
            M = np.zeros((n, size)); np.add.at(M, (r[m], ctx), 1)
            pc = M.sum(0) ** 0.75; pc /= pc.sum(); pw = M.sum(1, keepdims=True) / M.sum()
            with np.errstate(divide='ignore', invalid='ignore'):
                P = np.log((M / M.sum()) / (pw * pc))
            P[~np.isfinite(P) | (P < 0)] = 0
            P /= np.maximum(np.linalg.norm(P, axis=1, keepdims=True), 1e-12)
            blocks.append(P)
        X = np.hstack(blocks) / math.sqrt(3)
        return X

    def score(self, X):
        s = (X @ X.T)[self.pairs]; k = max(1, int(round(TOP * len(s))))
        return float(np.partition(s, -k)[-k:].mean())

    def shuffled(self, rng):
        tok = self.tok.copy()
        for a, b in zip(self.page_bounds[:-1], self.page_bounds[1:]):
            ix = self.page_order[a:b]; tok[ix] = tok[rng.permutation(ix)]
        return tok


def cluster(X):
    n = len(X); Z = linkage(X, 'average', metric='cosine')
    ks = sorted({int(round(x)) for x in np.geomspace(5, n / 2, 40)})
    best = None
    for k in ks:
        lab = fcluster(Z, k, 'maxclust')
        if len(set(lab)) < 2:
            continue
        s = silhouette_score(X, lab, metric='cosine')
        if best is None or s > best[0]:
            best = (s, k, lab)
    return best


def pair_ari(sp, lab, label):
    i, j = sp.pairs; w = sp.words
    t = np.array([label.get(x) for x in w], dtype=object); has = np.array([x is not None for x in t])
    m = has[i] & has[j]; i, j = i[m], j[m]
    st = t[i] == t[j]; sc = lab[i] == lab[j]
    tp = float(np.sum(st & sc)); fp = float(np.sum(~st & sc)); fn = float(np.sum(st & ~sc)); tn = float(np.sum(~st & ~sc))
    den = (tp + fn) * (fn + tn) + (tp + fp) * (fp + tn)
    return (2 * (tp * tn - fn * fp) / den if den else float('nan')), int(tp + fn), int(len(i))


def measure(name, pages, label=None):
    sp = Space(pages); X = sp.vectors(sp.tok); S = sp.score(X)
    rng = np.random.default_rng(3); null = np.array([sp.score(sp.vectors(sp.shuffled(rng))) for _ in range(PERMS)])
    r = {'types': len(sp.words), 'pairs_ed3': len(sp.pairs[0]), 'S': S, 'null_mean': float(null.mean()),
         'E': S - float(null.mean()), 'q95': float(np.percentile(null, 95) - null.mean())}
    r['upper95'] = r['E'] + r['q95']
    sil, k, lab = cluster(X); r['clusters'] = k; r['silhouette'] = float(sil)
    if label is not None:
        r['ari'], r['true_pairs'], r['labelled_pairs'] = pair_ari(sp, lab, label)
    print(f"{name:24s} types {r['types']:5d}  S {S:.4f}  null {r['null_mean']:.4f}  E {r['E']:+.4f} (95% +{r['q95']:.4f})  "
          f"k {k} sil {sil:.3f}" + (f"  ARI {r['ari']:.3f} ({r['true_pairs']} true pairs)" if label is not None else ''), flush=True)
    return r


def main():
    csv_path = sys.argv[1]
    zl = b3.load_zl_lang(); hand_of = ss.page_hands(); allw = b3.words_of(zl); N = len(allw)
    quire_of = {}
    for r in csv.DictReader(open(ss.TSV, encoding='utf-8'), delimiter='\t'):
        quire_of.setdefault(r['folio'], r['quire'])
    la = [w for b in pliny.STREAM for c in pliny.chapters(b) for w in pliny.latin_words(c)]
    it = a4.gutenberg_words(a4.IT)
    print(f'Voynich tokens {N}; Pliny {len(la)}; Italian {len(it)}', flush=True)
    plains = {'la': la[:N], 'it': it[:N]}
    R = collections.OrderedDict()

    print('\nsynthetic codes', flush=True)
    for lang, pl in plains.items():
        for K in (4, 8, 16):
            for mode in ('rand', 'habit'):
                n = f'code_{lang}_K{K}_{mode}'
                pages, label = encode(zl, hand_of, quire_of, pl, K, mode, allw, 11 + K)
                R[n] = measure(n, pages, label)

    print('\nnegative controls', flush=True)
    lg = a4.gutenberg_words(os.path.join(ROOT, 'lang', 'corpora', 'la-gutenberg.txt')); tmp = tempfile.mkdtemp(); plain = {}
    for i, h in enumerate(sorted(set(hand_of.values()))):
        ws = lg[i * 12000:(i + 1) * 12000]; plain[h] = os.path.join(tmp, f'{h if h != "?" else "x"}.txt')
        open(plain[h], 'w', encoding='utf-8').write('\n'.join(' '.join(ws[k:k + 12]) for k in range(0, len(ws), 12)))
    nb = os.path.join(tmp, 'naibbe.txt'); ws = lg[:3 * N]
    open(nb, 'w', encoding='utf-8').write('\n'.join(' '.join(ws[k:k + 12]) for k in range(0, len(ws), 12)))
    shuf = list(allw); random.Random(5).shuffle(shuf)
    C = collections.OrderedDict()
    C['improv_0.6_0.2'] = ss.Improviser(allw, 0.6, 0.2, 23).text(zl, hand_of)
    C['cipher_scribe'] = duel.cipher_habit(zl, hand_of, csv_path, plain, 0.0, 0.0)
    C['naibbe'] = [{'folio': a['folio'], 'lang': a['lang'], 'lines': q['lines']}
                   for a, q in zip(zl, cm.generate(cm.Variant(csv_path, 19), nb, a4.skeleton(zl)))]
    C['voynich_shuffled'] = pour(zl, shuf)
    for n, p in C.items():
        R[n] = measure(n, p)

    print('\nVoynich', flush=True)
    R['voynich'] = measure('voynich', zl)

    ctrl = max(R[n]['upper95'] for n in C)
    power = {}
    for lang in plains:
        r = R[f'code_{lang}_K8_habit']; power[lang] = {'ari': r['ari'] >= 0.3, 'score': r['E'] > ctrl}
    passed = all(all(v.values()) for v in power.values())
    print('\n| text | types >= 10 | S (top 1%, ed >= 3) | page-shuffled null | excess E | E + null 95% | clusters (silhouette) | ARI |')
    print('|---|---|---|---|---|---|---|---|')
    for n, r in R.items():
        print(f"| {n} | {r['types']} | {r['S']:.4f} | {r['null_mean']:.4f} | {r['E']:+.4f} | {r['upper95']:+.4f} | {r['clusters']} ({r['silhouette']:.3f}) | "
              f"{r['ari']:.3f} |" if 'ari' in r else f"| {n} | {r['types']} | {r['S']:.4f} | {r['null_mean']:.4f} | {r['E']:+.4f} | {r['upper95']:+.4f} | {r['clusters']} ({r['silhouette']:.3f}) | |")
    print(f'\nhighest negative-control 95th percentile: {ctrl:+.4f}')
    print('power check at K 8 habit:', power, '->', 'PASS' if passed else 'FAIL')
    if passed:
        v = R['voynich']['E']
        reading = ('Voynich above every control: first positive evidence for homophone classes (follow up on hand 2 B pages)'
                   if v > ctrl else 'Voynich at or below the controls: counts against a homophonic word code')
    else:
        reading = 'power check failed: the test cannot decide at Voynich length; stop here'
    print('reading:', reading)
    json.dump({'R': R, 'control_upper95': ctrl, 'power': power, 'passed': passed, 'reading': reading,
               'habit': HABIT, 'perms': PERMS}, open(os.path.join(HERE, 'homclass_results.json'), 'w'), indent=1, default=str)


if __name__ == '__main__':
    main()
