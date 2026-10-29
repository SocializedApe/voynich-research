"""The blind attack (attack_v1 segmentation + attack_v2 annealer) on Voynich, with order-shuffled controls.

Model under test: each Voynich token encodes one or two plaintext letters through head/tail glyph groups with
homophones (a Naibbe-type table cipher, the family still standing in hybrid_model.md), plaintext Latin or Italian.

Danger: with several hundred symbols that may each stand for one or two letters, the annealer can make any token
stream look somewhat like the target language. Control: the same tokens shuffled within each line (order destroyed,
frequencies kept). A real cipher of the language loses its plaintext under the shuffle; overfitting does not care.

Conditions (one process each): --text synth|voynich, --shuffle, --lang la|it. Synthetic = Naibbe on Latin (positive
control for the gap; known plaintext). Voynich = paragraph text of the fixed parse, first N tokens in manuscript order.
Score reported = per-character log-probability of the decryption under the language model (no unigram term).

Decision, fixed before the run (28 Oct 2026, this commit):
  gap_synth = score(synth, real order) - score(synth, shuffled)      (Latin)
  gap_voy(L) = score(Voynich, real order) - score(Voynich, shuffled)  for L = Latin, Italian
  SIGNAL for language L if gap_voy(L) >= 0.5 * gap_synth; NO SIGNAL if gap_voy(L) < 0.25 * gap_synth; between:
  weak / undecided. A decryption is never claimed from this run; a signal would only justify a targeted follow-up.

Run from the repository root:
  python research/voynich_siblings/attack/run_voynich.py <naibbe_tables.csv> --text voynich --lang la [--shuffle] [N]
"""
import collections, csv, os, random, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.join(HERE, '..', '..', '..')
import numpy as np
import attack_v0 as v0, attack_v1 as v1, attack_v2 as v2
from lang import lm

MODELS = {'la': ('la', 'latin', 'la-gutenberg.txt'), 'it': ('it-cinquecento', 'early', None)}


def lines_voynich():
    tsv = os.path.join(ROOT, 'targets', 'voynich', 'data', 'ZL3b-n.fixed.words.tsv')
    out = []
    for r in csv.DictReader(open(tsv, encoding='utf-8'), delimiter='\t'):
        if r['locus_type'] == 'P':
            ws = [w for w in r['line_words'].split() if re.fullmatch(r'[a-z]+', w)]
            if ws: out.append(ws)
    return out


def lines_synth(csv_path, n):
    syms, _ = v0.synth(csv_path, n)
    toks, i = [], 0
    while i < len(syms):
        if syms[i][0] == 'U': toks.append(syms[i][1]); i += 1
        else: toks.append(syms[i][1] + syms[i + 1][1]); i += 2
    return [toks[j:j + 9] for j in range(0, len(toks), 9)]


def main():
    args = sys.argv[1:]
    csv_path = args[0]
    text = args[args.index('--text') + 1]; lang = args[args.index('--lang') + 1]; shuffle = '--shuffle' in args
    nums = [a for a in args[1:] if a.isdigit()]; N = int(nums[0]) if nums else 20000
    rng = random.Random(211)
    mid, scheme, corp = MODELS[lang]
    model = lm.load(mid, order=5, spaces=False)
    if corp is None:   # unigram reference for the Italian model: from its own corpus via the lang cache
        from lang import corpora
        sample = lm.norm(corpora.text(lm.registry()[0][mid]['sources'])[:3000000], scheme, False)
        c = np.bincount(model.encode(sample), minlength=model.A).astype(float) + 1
        v0.latin_unigram = lambda m, c=c: c / c.sum()
    L = lines_voynich() if text == 'voynich' else lines_synth(csv_path, N)
    toks_total = 0; Lc = []
    for ws in L:
        if toks_total >= N: break
        Lc.append(ws[:]); toks_total += len(ws)
    if shuffle:
        for ws in Lc: rng.shuffle(ws)
    toks = [w for ws in Lc for w in ws]
    rd = v1.segment(collections.Counter(toks))
    vis = []
    for t in toks:
        r = rd[t]; vis += [('U', r[0])] if len(r) == 1 else [('P', r[0]), ('S', r[1])]
    t0 = time.time()
    dec = v2.solve(vis, model, rng, log=lambda s: print(s, flush=True))
    out = ''.join(dec(s) for s in vis)
    score = model.per_char(out)
    print(f'RESULT text={text} lang={lang} shuffle={shuffle} tokens={len(toks)} symbols={len(set(vis))} '
          f'split_share={sum(1 for t in toks if len(rd[t]) == 2) / len(toks):.3f} per_char={score:.4f} time={time.time() - t0:.0f}s')
    print('DECRYPTION', out[:600])


if __name__ == '__main__':
    main()
