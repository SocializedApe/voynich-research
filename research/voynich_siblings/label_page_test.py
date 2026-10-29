"""Does a Voynich label word turn up in the paragraph text of its own page?

Names hypothesis: a label names something the page's text discusses, so the *exact* label word should be enriched
in its own page's paragraphs. Copy-and-modify hypothesis (Timm & Schinner): words echo nearby words with small
edits, so *near* matches (edit distance 1, not exact) should be enriched on the same page, exact ones need not be.

For every label token on a folio that has paragraph text: E = 1 if the label word occurs in that folio's paragraphs,
N = 1 if a word at edit distance 1 (but no exact match) occurs there. Null: labels shuffled among folios of the same
section and hand (paragraph text stays put), N_PERM times. Baseline: the same statistics for paragraph words, each
tested against the rest of its folio's paragraphs with its own line removed, null = folio shuffled likewise.

Run from the repository root: python -I research/voynich_siblings/label_page_test.py
"""
import collections, csv, os, random, re

HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, '..', '..', 'targets', 'voynich', 'data', 'ZL3b-n.words.tsv')
N_PERM = 2000
SEED = 2
ALPHA = 'abcdefghijklmnopqrstuvwxyz'


def ok(w):
    return '@' not in w and '?' not in w and len(w) >= 3 and re.fullmatch(r'[a-z]+', w)


def neighbours(w):
    out = set()
    for i in range(len(w) + 1):
        for c in ALPHA:
            out.add(w[:i] + c + w[i:])
    for i in range(len(w)):
        out.add(w[:i] + w[i + 1:])
        for c in ALPHA:
            out.add(w[:i] + c + w[i + 1:])
    out.discard(w)
    return out


def load():
    rows = list(csv.DictReader(open(TSV, encoding='utf-8'), delimiter='\t'))
    par = collections.defaultdict(collections.Counter)      # folio -> word counts
    par_lines = collections.defaultdict(list)                # folio -> [(line_id, words)]
    meta = {}
    labels = []
    for r in rows:
        f = r['folio']
        meta.setdefault(f, (r['illus'], r['hand']))
        ws = [w for w in r['line_words'].split() if ok(w)]
        if r['locus_type'] == 'P':
            par[f].update(ws)
            par_lines[f].append((r['line_id'], ws))
        elif r['locus_type'] == 'L':
            labels += [(w, f) for w in ws]
    return par, par_lines, meta, labels


def hits(word, vocab, nb):
    e = vocab.get(word, 0) > 0
    n = (not e) and any(vocab.get(x, 0) > 0 for x in nb)
    return e, n


def test(items, vocab_of, strata, nbcache):
    """items: list of (word, folio); vocab_of(word, folio, item_index) -> Counter for that folio."""
    def total(assign):
        E = N = 0
        for k, (w, f0) in enumerate(items):
            e, n = hits(w, vocab_of(w, assign[k], k), nbcache[w])
            E += e; N += n
        return E, N
    obs = total([f for _, f in items])
    rng = random.Random(SEED)
    groups = collections.defaultdict(list)
    for k, (w, f) in enumerate(items):
        groups[strata[f]].append(k)
    nullE, nullN = [], []
    for _ in range(N_PERM):
        assign = [f for _, f in items]
        for idx in groups.values():
            fs = [assign[k] for k in idx]
            rng.shuffle(fs)
            for k, f in zip(idx, fs):
                assign[k] = f
        e, n = total(assign)
        nullE.append(e); nullN.append(n)
    def summ(o, null):
        mu = sum(null) / len(null); sd = (sum((x - mu) ** 2 for x in null) / len(null)) ** 0.5
        p = (sum(x >= o for x in null) + 1) / (len(null) + 1)
        return o, mu, sd, (o - mu) / sd if sd else float('nan'), p
    return summ(obs[0], nullE), summ(obs[1], nullN), len(items)


def main():
    par, par_lines, meta, labels = load()
    strata = {f: meta[f] for f in meta}
    items = [(w, f) for w, f in labels if sum(par[f].values()) > 0]
    print(f'label tokens on folios with paragraph text: {len(items)} of {len(labels)}')
    print('by section:', dict(collections.Counter(meta[f][0] for _, f in items)))
    nb = {}
    for w, _ in items:
        nb.setdefault(w, neighbours(w))
    E, N, n = test(items, lambda w, f, k: par[f], strata, nb)
    print('\nLABELS vs own page paragraphs (null: labels shuffled among folios of same section+hand)')
    print(f'  exact match : obs {E[0]}  null {E[1]:.1f} +- {E[2]:.1f}  ratio {E[0] / E[1]:.2f}  z {E[3]:.1f}  p {E[4]:.4f}')
    print(f'  near match  : obs {N[0]}  null {N[1]:.1f} +- {N[2]:.1f}  ratio {N[0] / N[1]:.2f}  z {N[3]:.1f}  p {N[4]:.4f}')
    # baseline: one paragraph word per line (the middle word), against the rest of its folio minus its own line
    rng = random.Random(SEED)
    base, own = [], []
    for f, lines in par_lines.items():
        if len(lines) < 3:
            continue
        for lid, ws in lines:
            if ws:
                base.append((ws[len(ws) // 2], f)); own.append(collections.Counter(ws))
    rng.shuffle(base)
    keep = list(range(len(base)))[:600]
    base = [base[i] for i in keep]
    for w, _ in base:
        nb.setdefault(w, neighbours(w))
    # the item's own line is removed only when testing against its own folio
    owncnt = {}
    for (w, f), k in zip(base, range(len(base))):
        owncnt[k] = None
    lines_of = {f: [collections.Counter(ws) for _, ws in par_lines[f]] for f in par_lines}
    src_line = {}
    for k, (w, f) in enumerate(base):
        for c in lines_of[f]:
            if c.get(w):
                src_line[k] = c; break
    def vocab_base(w, f, k):
        v = par[f]
        if f == base[k][1] and k in src_line:
            v = v - src_line[k]
        return v
    E, N, n = test(base, vocab_base, strata, nb)
    print(f'\nBASELINE: {n} paragraph words (one per line) vs rest of own page (own line removed)')
    print(f'  exact match : obs {E[0]}  null {E[1]:.1f} +- {E[2]:.1f}  ratio {E[0] / E[1]:.2f}  z {E[3]:.1f}  p {E[4]:.4f}')
    print(f'  near match  : obs {N[0]}  null {N[1]:.1f} +- {N[2]:.1f}  ratio {N[0] / N[1]:.2f}  z {N[3]:.1f}  p {N[4]:.4f}')


if __name__ == '__main__':
    main()
