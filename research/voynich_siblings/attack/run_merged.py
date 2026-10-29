"""The blind attack on a role-merged parse (inventory.py, point 3): one job = one solver run.

Parse: attack_v1 segmentation -> the K = 450 pieces used most -> every token spelled by the fewest pieces (at most 3,
ties broken by piece frequency). A piece is one symbol wherever it stands in the word (roles merged) and decrypts to
one letter; a token that no 1-3 pieces spell stays whole (symbol 'U', one or two letters, as in attack_v2).
Solver: validate.solve (swap moves, randomised start, 200,000 iterations), objective as before.

Texts (--text): synth = Naibbe on Latin (Greshko's tables); forms3 = the same with every table entry written in one of
3 forms (itself + 2 scribal variants, hybrid_model.edit), chosen at random at each use; expanded = 4 forms (as
validate.synth_tokens); voynich = paragraph text of the fixed parse. 20,000 tokens in
lines (synthetic: 9 tokens per line). --shuffle shuffles tokens within lines. --lang la|it.

Decision, fixed before any run (28 Oct 2026):
  Symbol counts under this parse, measured before any solver run: Voynich 625, synth 402, forms3 587, expanded about
  1,100. The yardstick is the synthetic within 10% of Voynich's count: forms3.
  Validation. synth, forms3 and expanded, 4 seeds each (1-4). Solved = similarity of the first 3,000 letters >= 0.80.
  The solver counts as able to handle Voynich's size only if forms3 is solved in >= 2 of 4 seeds (expanded is
  reported, not required). If it fails, no Voynich run is interpreted.
  Comparison, only if validation passes. Voynich, la and it, real and shuffled, 4 seeds each; per condition the run
  with the best objective is kept (best-of-4, as validated). gap = per-char(real) - per-char(shuffled).
  gap_synth = the same on the validated synthetic (real and shuffled, best-of-4).
  SIGNAL for L if gap_voy(L) >= 0.5 * gap_synth; NO SIGNAL if < 0.25 * gap_synth; else weak / undecided.
  A decryption is never claimed from this run; a signal only justifies a targeted follow-up.

Run from the repository root:
  python research/voynich_siblings/attack/run_merged.py <naibbe_tables.csv> --text synth --lang la --seed 1 [--shuffle]
"""
import collections, difflib, math, os, random, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import attack_v0 as v0, attack_v1 as v1, run_voynich as rv, validate as va
from lang import lm

K = 450; MAXP = 3; N = 20000


def parse(toks):
    """role-merged parse: list of symbols ('G', piece) or ('U', whole token)"""
    rd = v1.segment(collections.Counter(toks)); by = collections.Counter()
    for t in toks:
        for g in rd[t]: by[g] += 1
    inv = dict(by.most_common(K)); lp = {g: math.log(v) for g, v in inv.items()}
    cache = {}
    def spell(t):
        if t not in cache:
            L = len(t); dp = [None] * (L + 1); dp[0] = (0, 0.0, [])
            for i in range(1, L + 1):
                for j in range(i):
                    if dp[j] and t[j:i] in inv:
                        c = (dp[j][0] + 1, dp[j][1] - lp[t[j:i]], dp[j][2] + [t[j:i]])
                        if dp[i] is None or c[:2] < dp[i][:2]: dp[i] = c
            cache[t] = [('G', g) for g in dp[L][2]] if dp[L] and dp[L][0] <= MAXP else [('U', t)]
        return cache[t]
    return [s for t in toks for s in spell(t)]


def synth_tokens(csv_path, nforms, seed=19):
    """Naibbe tokens of Latin, every table entry written in one of `nforms` forms (validate.synth_tokens generalised)"""
    sys.path.insert(0, os.path.join(HERE, '..')); import hybrid_model as h1
    syms, truth = v0.synth(csv_path, N + 8000, seed=seed); rng = random.Random(seed + 5); variants = {}
    def form(g):
        if g not in variants:
            vs = {g}
            while len(vs) < nforms: vs.add(h1.edit(rng.choice(sorted(vs)), rng))
            variants[g] = sorted(vs)
        return rng.choice(variants[g])
    toks, i = [], 0
    while i < len(syms):
        if syms[i][0] == 'U': toks.append(form(syms[i][1])); i += 1
        else: toks.append(form(syms[i][1]) + form(syms[i + 1][1])); i += 2
    return toks, lm.norm(''.join(truth), 'latin', False)


def main():
    a = sys.argv[1:]
    text = a[a.index('--text') + 1]; lang = a[a.index('--lang') + 1]; seed = int(a[a.index('--seed') + 1])
    shuffle = '--shuffle' in a
    rng = random.Random(seed); np.random.seed(seed)
    mid, scheme, corp = rv.MODELS[lang]
    model = lm.load(mid, order=5, spaces=False)
    if corp is None:   # Italian unigram reference, as in run_voynich
        from lang import corpora
        sample = lm.norm(corpora.text(lm.registry()[0][mid]['sources'])[:3000000], scheme, False)
        c = np.bincount(model.encode(sample), minlength=model.A).astype(float) + 1
        v0.latin_unigram = lambda m, c=c: c / c.sum()
    truth = None
    if text == 'voynich':
        lines = rv.lines_voynich()
    else:
        toks, truth = synth_tokens(a[0], {'synth': 1, 'forms3': 3, 'expanded': 4}[text])
        lines = [toks[j:j + 9] for j in range(0, len(toks), 9)]
    Lc, n = [], 0
    for ws in lines:
        if n >= N: break
        Lc.append(ws[:]); n += len(ws)
    if shuffle:
        srng = random.Random(211)
        for ws in Lc: srng.shuffle(ws)
    toks = [w for ws in Lc for w in ws]
    vis = parse(toks)
    t0 = time.time()
    dec, score = va.solve(vis, model, rng)
    out = ''.join(dec(s) for s in vis)
    sim = difflib.SequenceMatcher(None, out[:3000], truth[:3000], autojunk=False).ratio() if truth and not shuffle else float('nan')
    print(f'JOB text={text} lang={lang} shuffle={shuffle} seed={seed} tokens={len(toks)} symbols={len(set(vis))} '
          f'whole={sum(1 for s in set(vis) if s[0] == "U")} similarity={sim:.3f} objective={score:.0f} '
          f'per_char={model.per_char(out):.4f} time={time.time() - t0:.0f}s', flush=True)
    print('DEC', out[:300], flush=True)


if __name__ == '__main__':
    main()
