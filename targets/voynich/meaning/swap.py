"""Does a word belong on its page, judged only from pages far away? (word-swap test)

For each test item: a word w on page i, and a decoy v of the same frequency band (whole-text count, log2 bins) and
length (+-1) that does not occur on page i. Each candidate is scored by its page co-occurrence with the other word
types of page i, counted only on training pages j with |i - j| > d (page order = manuscript order), as mean smoothed
PMI over the page's types. Accuracy = share of items where w outscores v (ties 0.5); 0.5 = no page context.

Expectations: meaningful text keeps topics across the book, so accuracy stays above 0.5 at large d; a copy-and-modify
generator spreads words only to nearby pages, so accuracy falls toward 0.5 as d grows; a cipher with no topic
structure (Naibbe) sits near 0.5 at every d; Voynich with words shuffled across the whole text is the floor.

--far: context words within edit distance 2 of either candidate are ignored, so a word cannot win by sitting
among its own spelling variants (the copy-and-modify cue); what is left is co-occurrence with different words.

Texts poured into the ZL paragraph skeleton (a4_selfcitation), so every text has Voynich's pages and lines.
Run from the repository root: python targets/voynich/meaning/swap.py [--far]
"""
import collections, math, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'research', 'voynich_siblings', 'attack'))
import a4_selfcitation as a4

DS = (0, 2, 10, 30)
FAR = '--far' in sys.argv   # ignore context words within edit distance 2 of either candidate (spelling variants)
PER_PAGE = 25
NAIBBE_CSV = os.environ.get('NAIBBE_CSV', '')


def texts():
    pages = a4.load_zl(); skel = a4.skeleton(pages); need = sum(len(ln['words']) for p in pages for ln in p['lines'])
    flat = [w for p in pages for ln in p['lines'] for w in ln['words']]
    out = {'voynich': pages}
    rng = random.Random(4); sh = flat[:]; rng.shuffle(sh); out['voynich_shuffled_all'] = a4.pour(sh, skel)
    for lang, src in (('latin', 'la-gutenberg'), ('italian', 'it-renaissance')):
        from lang import lm, corpora
        ws = lm.norm(corpora.text([src])[:4000000], 'early', True).split()
        ws = ws[len(ws) // 5: len(ws) // 5 + need]
        out[lang] = a4.pour(ws, skel)
    if NAIBBE_CSV:
        import run_merged as rm
        toks, _ = rm.synth_tokens(NAIBBE_CSV, 1)
        while len(toks) < need: toks += toks
        out['naibbe'] = a4.pour(toks[:need], skel)
    out['autocopist'] = a4.Autocopist(19).generate(skel)
    out['rugg_sorted'] = a4.RuggSorted(19).generate(skel)
    return out


def ed2(a, b):
    """edit distance <= 2 (banded DP)"""
    if abs(len(a) - len(b)) > 2: return False
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, y in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y))
        if min(cur) > 2: return False
        prev = cur
    return prev[-1] <= 2


def run(name, pages, rng):
    P = [set(w for ln in p['lines'] for w in ln['words']) for p in pages]
    tok = [[w for ln in p['lines'] for w in ln['words']] for p in pages]
    freq = collections.Counter(w for t in tok for w in t)
    band = lambda w: (int(math.log2(freq[w])), len(w))
    byband = collections.defaultdict(list)
    for w in freq:
        if freq[w] >= 3: byband[band(w)].append(w)
    where = collections.defaultdict(set)
    for i, s in enumerate(P):
        for w in s: where[w].add(i)
    items = []
    for i, t in enumerate(tok):
        cands = [w for w in set(t) if freq[w] >= 3 and freq[w] - t.count(w) >= 2]
        rng.shuffle(cands)
        for w in cands[:PER_PAGE]:
            pool = [v for b in ((int(math.log2(freq[w])), len(w) + k) for k in (0, -1, 1)) for v in byband.get(b, []) if i not in where[v]]
            if pool: items.append((i, w, rng.choice(pool)))
    res = {}
    for d in DS:
        ok = 0.0
        for i, w, v in items:
            train = lambda S: {j for j in S if abs(j - i) > d}
            ctx = [c for c in P[i] if c != w and not (FAR and (ed2(c, w) or ed2(c, v)))]
            Ntr = len(P) - sum(1 for j in range(len(P)) if abs(j - i) <= d)
            def score(x):
                wx = train(where[x]); s = 0.0
                for c in ctx:
                    wc = train(where[c]); co = len(wx & wc)
                    s += math.log((co + 0.1) * Ntr / ((len(wx) + 0.1) * (len(wc) + 0.1)))
                return s / max(len(ctx), 1)
            a, b = score(w), score(v)
            ok += 1.0 if a > b else 0.5 if a == b else 0.0
        res[d] = ok / len(items)
    print(f'{name:22} items {len(items):5} | ' + ' | '.join(f'd>{d}: {res[d]:.3f}' for d in DS), flush=True)
    return res


def main():
    rng = random.Random(7)
    for name, pages in texts().items():
        run(name, pages, rng)


if __name__ == '__main__':
    main()
