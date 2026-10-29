"""Is Voynichese a slot-built CODE of a real language (each Voynich word = one plaintext word, the codeword built from
independent slots, as a nomenclator would), a letter-fragment cipher (Naibbe), or generated text (self-citation)?

The b3 bake-off (targets/voynich/results/b3.md) shows Naibbe lacks Voynich's page and long-range clustering, while the
start/end test (slot_independence.md) rules out whole-word letter ciphers. A code keeps the plaintext's word-level
structure (topic clustering, Zipf, word-to-word dependence) while its codewords can be slot-built (start/end
independence). This script builds such a code from Latin and Italian and puts it beside Voynich and the generators on
measures that separate the families:

  W1  word-to-word dependence: I(w_t; w_t+1), plug-in, minus the same after shuffling tokens within each line
      (interior tokens only; the first and last token of every line are excluded so line-position effects drop out),
      divided by H(w); computed on the 2,000 most frequent types (others pooled as one symbol).
  X1  cross-boundary glyph dependence: I(last unit of w_t; first unit of w_t+1), same shuffle, normalised.
  SE  start/end dependence inside the word (slot_independence.measure, k = 1).
  REP adjacent identical tokens (%), and near-copy excess: share of tokens with an edit-distance-1 (not identical)
      token among the previous 10 on the same line, observed / within-line shuffled.
  MZ  long-range clustering: D(s) for blocks of s = 256 tokens, real minus token-shuffled (bits), as b3 item h.

Texts: Voynich (fixed parse), autocopist s19 and s7, Naibbe (Latin, seed 19), Latin, Italian (Gutenberg), and
CODE-Latin / CODE-Italian: every distinct plaintext word gets its own codeword drawn from Voynich-like slots
(prefix x core x suffix lists from a4.Rugg, re-drawn until unused), so the code is one-to-one and slot-built.
All texts cut to the same token count and poured into the ZL line skeleton.

Run from the repository root: python research/voynich_siblings/code_vs_generator.py <naibbe_tables.csv>
"""
import collections, math, os, random, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'targets', 'voynich'))
import slot_independence as si
import a4_selfcitation as a4
from b3_bakeoff import Naibbe

si.TSV = os.path.join(ROOT, 'targets', 'voynich', 'data', 'ZL3b-n.fixed.words.tsv')
a4.ZL = si.TSV
SEED = 23
TOP = 2000
GUT_IT = os.path.join(ROOT, 'lang', 'corpora', 'it-gutenberg.txt')


def H(c):
    n = sum(c.values())
    return -sum(v / n * math.log2(v / n) for v in c.values() if v)


def mi(pairs):
    a = collections.Counter(x for x, _ in pairs); b = collections.Counter(y for _, y in pairs)
    return H(a) + H(b) - H(collections.Counter(pairs))


def lines_of(pages):
    return [ln['words'] for p in pages for ln in p['lines'] if ln['words']]


def interior_pairs(lines, f):
    out = []
    for ws in lines:
        inner = ws[1:-1]
        out += [(f(a), f(b)) for a, b in zip(inner, inner[1:])]
    return out


def shuffled_lines(lines, rng):
    out = []
    for ws in lines:
        inner = ws[1:-1]; rng.shuffle(inner)
        out.append(ws[:1] + inner + ws[-1:] if len(ws) > 1 else ws)
    return out


def dep(lines, f, rng, reps=5):
    obs = mi(interior_pairs(lines, f))
    base = sum(mi(interior_pairs(shuffled_lines([l[:] for l in lines], rng), f)) for _ in range(reps)) / reps
    h = H(collections.Counter(f(w) for ws in lines for w in ws))
    return (obs - base) / h


def ld1(a, b):
    if a == b or abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    s, l = (a, b) if len(a) < len(b) else (b, a)
    return any(l[:i] + l[i + 1:] == s for i in range(len(l)))


def nearcopy(lines):
    hit = n = 0
    for ws in lines:
        for i, w in enumerate(ws):
            n += 1; hit += any(ld1(w, v) for v in ws[max(0, i - 10):i])
    return hit / n


def mz(tokens, rng, s=256):
    def D(t):
        allh = H(collections.Counter(t[: (len(t) // s) * s]))
        blocks = [t[i:i + s] for i in range(0, (len(t) // s) * s, s)]
        return allh - sum(H(collections.Counter(b)) for b in blocks) / len(blocks)
    sh = tokens[:]; base = 0
    for _ in range(3):
        rng.shuffle(sh); base += D(sh)
    return D(tokens) - base / 3


def make_code(words, rng):
    pre = [p for p in a4.Rugg.PRE if p] + ['']; mid = [m for m in a4.Rugg.MID if m] + ['']; suf = [x for x in a4.Rugg.SUF if x]
    code, used = {}, set()
    for w in sorted(set(words), key=lambda x: (-words.count(x) if False else 0, x)):
        for _ in range(1000):
            c = rng.choice(pre) + rng.choice(mid) + rng.choice(suf)
            if c not in used:
                break
        else:
            c = c + 'y' * rng.randint(1, 3)
        used.add(c); code[w] = c
    return [code[w] for w in words]


def italian_words(n):
    if not os.path.exists(GUT_IT):
        return None
    t = open(GUT_IT, encoding='utf-8', errors='replace').read().lower()
    return re.findall(r'[a-z]+', t)[20000:20000 + n]


def main():
    rng = random.Random(SEED)
    zl = a4.load_zl(); skel = a4.skeleton(zl); N = sum(n for pl in skel for n, _, _ in pl)
    flat = lambda pages: [w for p in pages for ln in p['lines'] for w in ln['words']]
    texts = {'Voynich (fixed parse)': zl}
    texts['autocopist s19'] = a4.Autocopist(19).generate(skel)
    texts['autocopist s7'] = a4.Autocopist(7).generate(skel)
    nb = Naibbe(sys.argv[1], seed=19)
    lat_path = os.path.join(ROOT, 'lang', 'corpora', 'la-gutenberg.txt')
    texts['Naibbe (Latin)'] = a4.pour([w for ws, _ in nb.generate(lat_path, N + 2000) for w in ws][:N], skel)
    lat = si.corpus('Latin'); s0 = rng.randrange(0, len(lat) - N); lat = lat[s0:s0 + N]
    texts['Latin'] = a4.pour(lat, skel)
    texts['CODE-Latin (slot-built codewords)'] = a4.pour(make_code(lat, rng), skel)
    it = italian_words(N)
    if it and len(it) == N:
        texts['Italian'] = a4.pour(it, skel)
        texts['CODE-Italian'] = a4.pour(make_code(it, rng), skel)
    print(f'{"text":36s} {"W1 word dep":>11s} {"X1 cross":>9s} {"SE start/end":>12s} {"adj ident %":>11s} {"nearcopy x":>10s} {"MZ256":>7s} {"hapax%":>7s}')
    for name, pages in texts.items():
        L = lines_of(pages); toks = flat(pages)
        top = {w for w, _ in collections.Counter(toks).most_common(TOP)}
        unit = list if name in ('Latin', 'Italian') else si.eva_units
        w1 = dep(L, lambda w: w if w in top else '#', rng)
        x1 = dep(L, lambda w: (unit(w)[-1], unit(w)[0]), rng) if False else None
        # cross-boundary: last unit of w_t vs first unit of w_t+1
        pairs = []
        for ws in L:
            inner = ws[1:-1]; pairs += [(unit(a)[-1], unit(b)[0]) for a, b in zip(inner, inner[1:])]
        obs = mi(pairs); base = 0
        for _ in range(5):
            pp = []
            for ws in shuffled_lines([l[:] for l in L], rng):
                inner = ws[1:-1]; pp += [(unit(a)[-1], unit(b)[0]) for a, b in zip(inner, inner[1:])]
            base += mi(pp)
        hu = H(collections.Counter(unit(w)[0] for w in toks))
        x1 = (obs - base / 5) / hu
        se = si.measure([unit(w) for w in toks], 1, rng)[0]
        adj = sum(a == b for ws in L for a, b in zip(ws, ws[1:])) / max(1, sum(len(ws) - 1 for ws in L)) * 100
        nc = nearcopy(L) / max(1e-9, nearcopy(shuffled_lines([l[:] for l in L], rng)))
        hap = sum(1 for v in collections.Counter(toks).values() if v == 1) / len(set(toks)) * 100
        print(f'{name:36s} {w1:11.4f} {x1:9.4f} {se:12.3f} {adj:11.3f} {nc:10.2f} {mz(toks, rng):7.3f} {hap:7.1f}', flush=True)


if __name__ == '__main__':
    main()
