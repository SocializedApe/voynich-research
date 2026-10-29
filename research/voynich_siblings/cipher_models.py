"""Can a hand-executable cipher of Latin reproduce the whole Voynich profile? Naibbe and three modifications.

Naibbe (Greshko 2025): plaintext respaced into one- and two-letter units; each unit becomes a token from one of six
glyph tables (alpha, beta1-3, gamma1-2), the table drawn from a card deck. It matches Voynich's low glyph entropy and
start/end independence but fails edge coupling, the open vocabulary, page locality and long-range clustering
(b3.md; code_vs_generator.md). Variants, all using Greshko's own tables (references/naibbe_tables.csv, argv[1]):

  naibbe      the original rule (deck draw), as targets/voynich/b3_bakeoff.Naibbe
  chained     the table of the next token is fixed by the last glyph of the current token (a random but fixed map
              glyph -> table, applied with probability P_CHAIN, otherwise a deck draw): an autokey-like rule
  drift       each page uses only K_PAGE of the six tables (a new random subset per page, weights renormalised)
  chain+drift both

Profile measured on every text, all poured into the ZL line skeleton (fixed parse) so page and line statistics are
comparable: h2 of the glyph stream without spaces (raw EVA), start/end dependence k = 1 (slot_independence), edge
coupling (end of token -> start of next, interior pairs, within-line shuffle null; code_vs_generator), hapax share of
types, share of types on one page, long-range D(256), adjacent identical tokens %.

Run from the repository root: python research/voynich_siblings/cipher_models.py <naibbe_tables.csv>
"""
import collections, csv, math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'targets', 'voynich'))
import slot_independence as si
import code_vs_generator as cg
import a4_selfcitation as a4
from b3_bakeoff import Naibbe

si.TSV = os.path.join(ROOT, 'targets', 'voynich', 'data', 'ZL3b-n.fixed.words.tsv')
a4.ZL = si.TSV
P_CHAIN = 0.9
K_PAGE = 2
TABLES = Naibbe.TABLES


class Variant(Naibbe):
    def __init__(self, csv_path, seed, chain=False, drift=False, p_chain=P_CHAIN, k_page=K_PAGE, noise=0.0, merge=0.0, sandhi=0.0, nulls=0.0, null_set=6, split=False, remap=False, page_nulls=False):
        super().__init__(csv_path, seed=seed)
        self.chain, self.drift, self.p_chain, self.k_page, self.noise, self.merge, self.sandhi = chain, drift, p_chain, k_page, noise, merge, sandhi
        self.nulls, self.split, self.remap, self.page_nulls, self.null_set = nulls, split, remap, page_nulls, null_set
        self.null_words = [self.glyph[c] for c in self.rng.sample(sorted(c for c in self.glyph if c.startswith('unigram_')), null_set)]
        glyph_inventory = sorted({g[-1] for g in self.glyph.values()} | {g[0] for g in self.glyph.values()})
        self.chain_map = {g: self.rng.randrange(6) for g in glyph_inventory}  # index into the page's active tables
        self.active = TABLES
        # sandhi: a fixed rule, last glyph of the previous word -> what is written before the next word
        self.sandhi_map = {g: self.rng.choice(['qo', 'o', 'q', 'y', '', '', 'ch', 'd']) for g in glyph_inventory}

    def new_page(self):
        if self.drift:
            self.active = self.rng.sample(TABLES, self.k_page)
        if self.page_nulls:   # each page has its own small set of null words, drawn from all table outputs
            self.null_words = self.rng.sample(sorted(set(self.glyph.values())), self.null_set)
        if self.remap:   # a new chaining rule (previous ending -> opening table) for every page
            self.chain_map = {g: self.rng.randrange(6) for g in self.chain_map}

    def pick(self, last, role='open'):
        """role 'open' (unigram or prefix table) or 'suffix'. With split=True the opening table is chained over all
        six tables and only the suffix table follows the page's active subset (drift)."""
        pool = TABLES if (self.split and role == 'open') else self.active
        if self.chain and role == 'open' and last is not None and self.rng.random() < self.p_chain:
            i = self.chain_map.get(last[-1])
            if i is not None:
                return pool[i % len(pool)]
        w = [self.WEIGHTS[False][t] for t in pool]
        return self.rng.choices(pool, weights=w)[0]

    def encrypt_units(self, units, last):
        out = []
        for u in units:
            if len(u) == 1:
                t = self.pick(last); g = self.glyph.get(f'unigram_{t}_{u}')
            else:
                for _ in range(50):
                    t = self.pick(last)
                    gp = self.glyph.get(f'prefix_{t}_{u[0]}'); gs = self.glyph.get(f'suffix_{self.pick(None, "suffix")}_{u[1]}')
                    if gp and gs and gp + gs not in self.unigram_glyphs:
                        break
                g = (gp or '') + (gs or '')
            if g and self.noise and self.rng.random() < self.noise:
                g = self.vary(g)
            if g and last is not None and self.sandhi and self.rng.random() < self.sandhi:
                g = self.sandhi_map.get(last[-1], '') + g
            if g:
                out.append(g)
                last = g
        return out, last

    def vary(self, g):
        """one free scribal variation: e <-> ee, k <-> t, ch <-> sh, optional qo- before k/t, o <-> a before i/r/l"""
        r = self.rng.random()
        if r < 0.3 and 'e' in g:
            return g.replace('ee', 'e', 1) if 'ee' in g and self.rng.random() < 0.5 else g.replace('e', 'ee', 1)
        if r < 0.5 and ('k' in g or 't' in g):
            return g.replace('k', '#').replace('t', 'k').replace('#', 't') if self.rng.random() < 0.5 else g
        if r < 0.7 and ('ch' in g or 'sh' in g):
            return g.replace('ch', 'sh', 1) if 'ch' in g else g.replace('sh', 'ch', 1)
        if r < 0.85 and g[:1] in 'kt':
            return 'qo' + g
        return g.replace('o', 'a', 1) if 'o' in g else g


def generate(variant, plaintext_path, skel):
    """Fill the ZL skeleton page by page, line by line (line token counts kept), from the plaintext stream."""
    units = []
    for raw in open(plaintext_path, encoding='utf-8', errors='replace'):
        c = variant.clean_line(raw)
        if c:
            units += variant.respace(c)
        if len(units) > 120000:
            break
    pos, last, pages = 0, None, []
    for pl in skel:
        variant.new_page()
        lines = []
        for (n, _, ps) in pl:
            words = []
            while len(words) < n:
                if variant.nulls and variant.rng.random() < variant.nulls:
                    nw = variant.rng.choice(variant.null_words); words.append(nw); last = nw; continue   # a null word
                ws, last = variant.encrypt_units(units[pos:pos + 1], last); pos += 1
                if words and ws and variant.merge and variant.rng.random() < variant.merge:
                    words[-1] += ws[0]; ws = ws[1:]   # a missed space: two units written as one word
                words += ws
            lines.append({'words': words[:n], 'para_start': ps})
        pages.append({'folio': '', 'lines': lines})
    return pages


def profile(pages, rng):
    L = cg.lines_of(pages)
    toks = [w for ws in L for w in ws]
    unit = si.eva_units
    stream = [[c for w in ws for c in w] for ws in L]
    uni = collections.Counter(); bi = collections.Counter()
    for s in stream:
        uni.update(s); bi.update(zip(s, s[1:]))
    h2 = cg.H(bi) - cg.H(collections.Counter(a for a, _ in bi.elements()))
    se = si.measure([unit(w) for w in toks], 1, rng)[0]
    pairs = lambda lines: [(unit(a)[-1], unit(b)[0]) for ws in lines for a, b in zip(ws[1:-1], ws[2:-1])]
    obs = cg.mi(pairs(L)); base = sum(cg.mi(pairs(cg.shuffled_lines([l[:] for l in L], rng))) for _ in range(5)) / 5
    x1 = (obs - base) / cg.H(collections.Counter(unit(w)[0] for w in toks))
    c = collections.Counter(toks)
    hap = sum(1 for v in c.values() if v == 1) / len(c)
    pages_of = collections.defaultdict(set)
    for i, p in enumerate(pages):
        for ln in p['lines']:
            for w in ln['words']:
                pages_of[w].add(i)
    one_page = sum(1 for s in pages_of.values() if len(s) == 1) / len(pages_of)
    adj = sum(a == b for ws in L for a, b in zip(ws, ws[1:])) / max(1, sum(len(ws) - 1 for ws in L)) * 100
    return dict(h2=h2, se=se, edge=x1, hapax=hap, one_page=one_page, mz=cg.mz(toks, rng), adj=adj, types=len(c))


TARGET = dict(h2=2.280, se=0.039, edge=0.0548, hapax=0.680, one_page=0.683, mz=0.287, adj=0.935)


def distance(p):
    """mean absolute relative deviation from Voynich over the seven profile items"""
    return sum(abs(p[k] - v) / abs(v) for k, v in TARGET.items()) / len(TARGET)


def grid():
    rng = random.Random(59)
    zl = a4.load_zl(); skel = a4.skeleton(zl)
    lat = os.path.join(ROOT, 'lang', 'corpora', 'la-gutenberg.txt')
    res = []
    for kp in (1, 2):
        for nl in (0.1, 0.15):
            for ns in (3, 5):
                for sd in (0.0, 0.1):
                    v = Variant(sys.argv[1], 19, chain=True, drift=True, k_page=kp, p_chain=0.7, merge=0.1, sandhi=sd,
                                nulls=nl, null_set=ns, split=True, page_nulls=True)
                    p = profile(generate(v, lat, skel), rng)
                    res.append((distance(p), kp, nl, ns, sd, p))
                    print(f'global chain 0.7, suffix-tables/page {kp}, page nulls {nl:.2f} x{ns}, sandhi {sd:.1f}: dist {distance(p):.3f}  ' + ' '.join(f'{k} {p[k]:.3f}' for k in TARGET) + f' types {p["types"]}', flush=True)
    res.sort(key=lambda x: x[0])
    print('BEST:', ' | '.join(f'k {r[1]} nulls {r[2]} x{r[3]} sandhi {r[4]} dist {r[0]:.3f}' for r in res[:5]))


def main():
    if '--grid' in sys.argv:
        return grid()
    rng = random.Random(53)
    zl = a4.load_zl(); skel = a4.skeleton(zl)
    lat = os.path.join(ROOT, 'lang', 'corpora', 'la-gutenberg.txt')
    rows = [('Voynich (fixed parse)', zl)]
    for name, ch, dr in [('naibbe', False, False), ('chained', True, False), ('drift', False, True), ('chain+drift', True, True)]:
        for seed in (19, 7):
            rows.append((f'{name} s{seed}', generate(Variant(sys.argv[1], seed, ch, dr), lat, skel)))
    print(f'{"text":24s} {"h2":>6s} {"start/end":>9s} {"edge":>7s} {"hapax":>6s} {"1-page":>7s} {"D256":>6s} {"adj%":>6s} {"types":>6s}')
    for name, pages in rows:
        p = profile(pages, rng)
        print(f'{name:24s} {p["h2"]:6.3f} {p["se"]:9.3f} {p["edge"]:7.4f} {p["hapax"]:6.3f} {p["one_page"]:7.3f} {p["mz"]:6.3f} {p["adj"]:6.3f} {p["types"]:6d}', flush=True)


if __name__ == '__main__':
    main()
