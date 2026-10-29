"""Gate 2 for the verbose-cipher attack: gate.py with units capped at 3 glyphs and the setting chosen blind.

Protocol, fixed before the run (29 Oct 2026):
  Same plaintext, cipher and solver as gate.py (Pliny, verbose24 0/24/rest seed 6, attack_v0.solve with the 5-gram
  Latin model), with two changes from gate 1:
    - SentencePiece pieces at most 3 glyphs long (the cipher's code lengths); gate 1 allowed 4, and at 20,000 words
      pieces swallowed pairs of codes.
    - K in (30, 36, 42, 50, 60); for each text size the K whose decryption has the best per-character LM score is
      chosen WITHOUT the answer, and only that run decides: pass if its similarity >= 0.80.
  Seeds 1 and 2 per point (best objective kept). Reported for every point: similarity, LM score, segmentation exact,
  and the length distribution of the learned pieces actually used.

Run from the repository root: python targets/voynich/verbose/gate2.py
"""
import collections, difflib, os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sentencepiece as spm
import gate
from lang import lm


def learn_units(words, k, tmp):
    path = os.path.join(tmp, 'cipher.txt'); open(path, 'w').write('\n'.join(words))
    pref = os.path.join(tmp, f'u{k}')
    spm.SentencePieceTrainer.train(input=path, model_prefix=pref, vocab_size=k, model_type='unigram',
                                   character_coverage=1.0, add_dummy_prefix=False, split_by_whitespace=True,
                                   bos_id=-1, eos_id=-1, unk_id=0, hard_vocab_limit=False, minloglevel=2,
                                   max_sentencepiece_length=3)
    sp = spm.SentencePieceProcessor(model_file=pref + '.model')
    return [[p for p in sp.encode(w, out_type=str) if p] for w in words]


def main():
    model = lm.load('la', order=5, spaces=False)
    with tempfile.TemporaryDirectory() as tmp:
        for n in (11000, 20000):
            plain = gate.plaintext(n); truth = ''.join(plain)
            mp = gate.a1.verbose_cipher_map(plain, gate.ALPHA24, 0, 24, seed=6)
            cipher = gate.a1.verbose_encode(plain, mp)
            true_split = [[mp[c] for c in w] for w in plain]
            runs = []
            for k in (30, 36, 42, 50, 60):
                pieces = learn_units(cipher, k, tmp)
                seg_ok = sum(p == t for p, t in zip(pieces, true_split)) / len(plain)
                syms = [p for ws in pieces for p in ws]
                used = collections.Counter(len(p) for p in set(syms))
                sc, dec, nsym = gate.solve_best(syms, model, seeds=(1, 2))
                sim = difflib.SequenceMatcher(None, dec[:3000], truth[:3000], autojunk=False).ratio()
                runs.append((sc, k, sim))
                print(f'N {n:6} K {k:3}: units used {nsym:3} (by length {dict(sorted(used.items()))}) | segmentation exact '
                      f'{seg_ok:.1%} | similarity {sim:.3f} | per-char {sc:.3f} | {dec[:60]}', flush=True)
            sc, k, sim = max(runs)
            print(f'GATE N {n}: chosen blind K {k} (per-char {sc:.3f}) -> similarity {sim:.3f} -> {"PASS" if sim >= 0.8 else "FAIL"}', flush=True)
            print(f'   truth: {truth[:60]}', flush=True)


if __name__ == '__main__':
    main()
