"""Power check: does word order in a real language survive the candidate ciphers well enough to be measured?

Protocol, fixed before any run (28 Oct 2026):
  Texts, each poured into the ZL paragraph skeleton (same pages, lines and word count as Voynich):
    plain Latin (lang/corpora/la-gutenberg.txt) and plain Italian (a4.IT);
    for both: a one-to-one word code (sanity: must keep the plaintext's signal), a homophonic word code (each type
    gets 1-4 code words by frequency, one drawn at random per token), Naibbe (Greshko's rule, cipher_models.Variant
    defaults) and the round-8 letter cipher (cipher_models.Variant with hybrid_model.BASE, merge 0.0);
    Voynich (ZL) itself.
  Split by page: page index mod 5 == 0 test, == 1 validation, the rest training.
  Models, bits per word on the test pages, interpolation weights chosen on the validation pages:
    U  = unigram (training hapaxes stand for unseen words) mixed with a cache of the previous 200 words;
    Bw = absolute-discounted bigram on the previous word (d 0.75) over that unigram, mixed with the same cache;
    Bs = the same bigram with the previous word cut to its last two letters (a sub-word context, for ciphers whose
         words are pieces of plaintext words).
  Order gain = U - B (bits/word). Null: the same text with words shuffled within each line (3 seeds), which keeps
  the cache and the line vocabulary but destroys order. Signal = gain(text) - mean gain(shuffled).
  Added after the first run: each text is also built from the same plaintext words in random order (scr), because
  the round-8 chaining rule makes its own sub-word signal (+0.45 for Latin and Italian alike). Read-out: survival =
  (signal(cipher) - signal(cipher of scrambled plaintext)) / (signal(plaintext) - signal(scrambled plaintext)). A cipher with survival near 0 hides word order from
  this test, so a null on Voynich says nothing about meaning under that cipher.

Run from the repository root: python targets/voynich/meaning/wordpredict.py <naibbe_tables.csv>
"""
import collections, json, math, os, random, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'research', 'voynich_siblings'))
import codebook as cbk
import a4_selfcitation as a4
import b3_bakeoff as b3
import hybrid_model as hm
import cipher_models as cm

CACHE, D, UNK = 200, 0.75, '<unk>'
LAMBDAS = (0.0, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4)


def split(pages):
    tr, va, te = [], [], []
    for i, p in enumerate(pages):
        ws = [w for ln in p['lines'] for w in ln['words']]
        (te if i % 5 == 0 else va if i % 5 == 1 else tr).append(ws)
    return tr, va, te


class LM:
    def __init__(self, train_pages, ctx):
        self.ctx = ctx
        c = collections.Counter(w for p in train_pages for w in p)
        self.vocab = {w for w, n in c.items() if n > 1}
        self.uni = collections.Counter(self.m(w) for p in train_pages for w in p)
        self.tot = sum(self.uni.values()); self.V = len(self.uni) + 1
        self.big = collections.defaultdict(collections.Counter)
        for p in train_pages:
            for a, b in zip(p, p[1:]):
                self.big[ctx(a)][self.m(b)] += 1
        self.ctot = {k: sum(v.values()) for k, v in self.big.items()}

    def m(self, w):
        return w if w in self.vocab else UNK

    def pu(self, w):
        return (self.uni[w] + 0.1) / (self.tot + 0.1 * self.V)

    def pb(self, prev, w):
        row = self.big.get(self.ctx(prev)) if prev is not None else None
        if not row:
            return self.pu(w)
        n = self.ctot[self.ctx(prev)]
        return max(row[w] - D, 0) / n + D * len(row) / n * self.pu(w)

    def bits(self, pages, lam, order):
        s = n = 0
        for p in pages:
            hist = collections.deque(maxlen=CACHE); cc = collections.Counter(); prev = None
            for raw in p:
                w = self.m(raw)
                base = self.pb(prev, w) if order else self.pu(w)
                pc = cc[raw] / len(hist) if hist else 0.0   # raw words: a recurring unseen word is caught by the cache
                prob = (1 - lam) * base + lam * pc
                s -= math.log2(max(prob, 1e-12)); n += 1
                if len(hist) == CACHE:
                    cc[hist[0]] -= 1
                hist.append(raw); cc[raw] += 1; prev = raw
        return s / n


def measure(pages):
    tr, va, te = split(pages)
    out = {}
    for name, ctx, order in (('U', lambda w: w, False), ('Bw', lambda w: w, True), ('Bs', lambda w: w[-2:], True)):
        lm = LM(tr, ctx)
        lam = min(LAMBDAS, key=lambda l: lm.bits(va, l, order))
        out[name] = lm.bits(te, lam, order); out[name + '_lam'] = lam
    out['gain_w'] = out['U'] - out['Bw']; out['gain_s'] = out['U'] - out['Bs']
    return out


def shuffle_lines(pages, seed):
    rng = random.Random(seed); new = []
    for p in pages:
        lines = []
        for ln in p['lines']:
            ws = list(ln['words']); rng.shuffle(ws); lines.append({'words': ws, 'para_start': ln['para_start']})
        new.append({'folio': p.get('folio', ''), 'lines': lines})
    return new


def homophonic(plain, rng):
    freq = collections.Counter(plain); codes = {}
    for i, (w, n) in enumerate(freq.most_common()):
        k = 1 if n < 5 else 2 if n < 30 else 3 if n < 150 else 4
        codes[w] = [f'c{i}_{j}' for j in range(k)]
    return [rng.choice(codes[w]) for w in plain]


def main():
    csv_path = sys.argv[1]
    zl = b3.load_zl_lang(); skel = a4.skeleton(zl); N = len(b3.words_of(zl))
    paths = {'la': os.path.join(ROOT, 'lang', 'corpora', 'la-gutenberg.txt'), 'it': a4.IT}
    C = collections.OrderedDict(); C['voynich_ZL'] = zl
    tmp = tempfile.mkdtemp()
    for lang, path in paths.items():
        words = [w for w in a4.gutenberg_words(path)][:N]
        if len(words) < N:
            raise SystemExit(f'{lang}: only {len(words)} words')
        scr = list(words); random.Random(11).shuffle(scr)
        for tag, plain in (('', words), ('scr', scr)):   # scr: the same words in random order, so a cipher's own structure shows alone
            pf = os.path.join(tmp, f'{lang}{tag}.txt')
            with open(pf, 'w', encoding='utf-8') as f:
                f.write('\n'.join(' '.join(plain[i:i + 12]) for i in range(0, len(plain), 12)))
            C[f'{lang}{tag}_plain'] = a4.pour(plain, skel)
            C[f'{lang}{tag}_code1to1'] = a4.pour(cbk.encode(plain, [f'k{i}' for i in range(len(set(plain)))])[0], skel)
            C[f'{lang}{tag}_homophonic'] = a4.pour(homophonic(plain, random.Random(5)), skel)
            C[f'{lang}{tag}_naibbe'] = cm.generate(cm.Variant(csv_path, 19), pf, skel)
            C[f'{lang}{tag}_round8'] = cm.generate(cm.Variant(csv_path, 19, merge=0.0, **hm.BASE), pf, skel)
    R = {}
    for n, p in C.items():
        real = measure(p); null = [measure(shuffle_lines(p, s)) for s in (1, 2, 3)]
        r = {'real': real, 'null': null}
        for g in ('gain_w', 'gain_s'):
            vals = [x[g] for x in null]; mu = sum(vals) / 3
            r['sig' + g[4:]] = real[g] - mu; r['nullsd' + g[4:]] = (sum((v - mu) ** 2 for v in vals) / 2) ** 0.5
        R[n] = r
        print(f"{n:18s} U {real['U']:.3f}  Bw {real['Bw']:.3f}  Bs {real['Bs']:.3f}  signal word {r['sig_w']:+.3f} (null sd {r['nullsd_w']:.3f})"
              f"  sub-word {r['sig_s']:+.3f} (null sd {r['nullsd_s']:.3f})", flush=True)
    print('\n| text | signal, previous word: real / scrambled plaintext | survival | last 2 letters: real / scrambled | survival |')
    print('|---|---|---|---|---|')
    for n, r in R.items():
        if 'scr_' in n:
            continue
        if n == 'voynich_ZL':
            print(f"| {n} | {r['sig_w']:+.3f} | | {r['sig_s']:+.3f} | |"); continue
        lang, kind = n.split('_', 1); s = R[f'{lang}scr_{kind}']; pr, ps = R[f'{lang}_plain'], R[f'{lang}scr_plain']
        r['surv_w'] = (r['sig_w'] - s['sig_w']) / (pr['sig_w'] - ps['sig_w'])
        r['surv_s'] = (r['sig_s'] - s['sig_s']) / (pr['sig_s'] - ps['sig_s'])
        print(f"| {n} | {r['sig_w']:+.3f} / {s['sig_w']:+.3f} | {r['surv_w']:.2f} | {r['sig_s']:+.3f} / {s['sig_s']:+.3f} | {r['surv_s']:.2f} |")
    json.dump(R, open(os.path.join(HERE, 'wordpredict_results.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
