"""Gate for a verbose-cipher attack: can the pipeline break a synthetic verbose cipher of Latin blind?

Protocol, fixed before the run (28 Oct 2026):
  Plaintext: Pliny, Naturalis Historia (meaning/pliny.py stream), Latin normalisation ('latin'), N words.
  Cipher: a1_charstats.verbose_cipher_map over a 24-glyph alphabet, 0 one-glyph / 24 two-glyph / rest three-glyph codes
    (the 'LAT-verbose24 (0/24/rest)' control whose h1/h2 match Voynich), seed 6; word spaces kept.
  Pipeline, blind (the code table is not used):
    1. units: SentencePiece unigram model with vocabulary K learned on the cipher words (one word per line, no dummy
       prefix, character coverage 1); every word is cut into pieces.
    2. solve: research/voynich_siblings/attack/attack_v0.solve, piece -> letter, 5-gram Latin model without spaces
       ('la'), 3 seeds, the run with the best objective kept.
  Pass: difflib similarity of the first 3,000 decrypted letters to the plaintext >= 0.80.
  Also reported: segmentation accuracy (share of cipher words cut exactly at the true code boundaries).
  Grid: N in (11,000, 20,000) x K in (30, 40, 60).

Run from the repository root: python targets/voynich/verbose/gate.py
"""
import collections, difflib, os, random, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..', '..')
for p in (ROOT, os.path.join(HERE, '..'), os.path.join(HERE, '..', 'meaning'), os.path.join(ROOT, 'research', 'voynich_siblings', 'attack')):
    sys.path.insert(0, p)
import numpy as np
import sentencepiece as spm
from lang import lm
import a1_charstats as a1
import attack_v0 as v0
import pliny

ALPHA24 = 'abcdefghijklmnopqrstuvwx'


def plaintext(n):
    ws = [w for b in pliny.STREAM for c in pliny.chapters(b) for w in pliny.latin_words(c)]
    ws = [lm.norm(w, 'latin', False) for w in ws]
    return [w for w in ws if w][:n]


def learn_units(words, k, tmp):
    path = os.path.join(tmp, 'cipher.txt'); open(path, 'w').write('\n'.join(words))
    pref = os.path.join(tmp, f'u{k}')
    spm.SentencePieceTrainer.train(input=path, model_prefix=pref, vocab_size=k, model_type='unigram',
                                   character_coverage=1.0, add_dummy_prefix=False, split_by_whitespace=True,
                                   bos_id=-1, eos_id=-1, unk_id=0, hard_vocab_limit=False, minloglevel=2,
                                   max_sentencepiece_length=4)
    sp = spm.SentencePieceProcessor(model_file=pref + '.model')
    return [[p for p in sp.encode(w, out_type=str) if p] for w in words]


def solve_best(syms, model, seeds=(1, 2, 3)):
    best = None
    for s in seeds:
        rng = random.Random(s); np.random.seed(s)
        types, key = v0.solve(syms, model, rng)
        dec = ''.join(model.alpha[key[types.index(x)]] for x in syms)
        sc = model.per_char(dec)
        if best is None or sc > best[0]: best = (sc, dec, len(types))
    return best


def main():
    model = lm.load('la', order=5, spaces=False)
    with tempfile.TemporaryDirectory() as tmp:
        for n in (11000, 20000):
            plain = plaintext(n); truth = ''.join(plain)
            mp = a1.verbose_cipher_map(plain, ALPHA24, 0, 24, seed=6)
            cipher = a1.verbose_encode(plain, mp)
            true_split = [[mp[c] for c in w] for w in plain]
            for k in (30, 40, 60):
                pieces = learn_units(cipher, k, tmp)
                seg_ok = sum(p == t for p, t in zip(pieces, true_split)) / len(plain)
                syms = [p for ws in pieces for p in ws]
                sc, dec, nsym = solve_best(syms, model)
                sim = difflib.SequenceMatcher(None, dec[:3000], truth[:3000], autojunk=False).ratio()
                print(f'N {n:6} K {k:3}: units used {nsym:3} | segmentation exact {seg_ok:.1%} | similarity {sim:.3f} '
                      f'{"PASS" if sim >= 0.8 else "fail"} | per-char {sc:.3f} | {dec[:70]}', flush=True)
            print(f'   truth: {truth[:70]}', flush=True)


if __name__ == '__main__':
    main()
