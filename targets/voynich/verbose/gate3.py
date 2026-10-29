"""Gate 3: a harder, more Voynich-like verbose cipher of Latin. Same blind pipeline as gate2.py.

Protocol, fixed before the run (29 Oct 2026):
  Plaintext: Pliny, 11,000 words (gate.plaintext), letters only (word spaces dropped).
  Cipher (seed 8): letters ranked by frequency; the 8 commonest get two codes each (homophones, chosen at random at
    each use), the rest one; every code is 2 glyphs long, or 3 with probability 1/3, drawn without repeats from the
    24-glyph alphabet. Cipher 'words': after every code a space with probability 0.5 (about two codes per word), so
    spaces carry no plaintext word boundaries.
  Pipeline: SentencePiece units (pieces <= 3 glyphs) for K in (36, 42, 50, 60, 72) -> attack_v0.solve (5-gram Latin
    model, no spaces), seeds 1 and 2; the K with the best per-character LM score is chosen blind and alone decides.
  Pass: similarity of the first 3,000 decrypted letters to the plaintext >= 0.80.

Run from the repository root: python targets/voynich/verbose/gate3.py
"""
import collections, difflib, os, random, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import gate, gate2
from lang import lm


def cipher_of(plain, rng):
    letters = [c for c, _ in collections.Counter(''.join(plain)).most_common()]
    used, table = set(), {}
    for i, c in enumerate(letters):
        table[c] = []
        for _ in range(2 if i < 8 else 1):
            while True:
                code = ''.join(rng.choice(gate.ALPHA24) for _ in range(3 if rng.random() < 1 / 3 else 2))
                if code not in used: used.add(code); table[c].append(code); break
    words, cur = [], ''
    for c in ''.join(plain):
        cur += rng.choice(table[c])
        if rng.random() < 0.5: words.append(cur); cur = ''
    if cur: words.append(cur)
    return words, table


def main():
    model = lm.load('la', order=5, spaces=False)
    plain = gate.plaintext(11000); truth = ''.join(plain)
    words, table = cipher_of(plain, random.Random(8))
    lens = collections.Counter(len(c) for cs in table.values() for c in cs)
    print(f'cipher: {len(words)} words, {sum(len(v) for v in table.values())} codes (by length {dict(lens)}), '
          f'mean {sum(map(len, words)) / len(words):.1f} glyphs per word; sample: {" ".join(words[:12])}', flush=True)
    runs = []
    with tempfile.TemporaryDirectory() as tmp:
        for k in (36, 42, 50, 60, 72):
            pieces = gate2.learn_units(words, k, tmp)
            syms = [p for ws in pieces for p in ws]
            used = collections.Counter(len(p) for p in set(syms))
            sc, dec, nsym = gate.solve_best(syms, model, seeds=(1, 2))
            sim = difflib.SequenceMatcher(None, dec[:3000], truth[:3000], autojunk=False).ratio()
            runs.append((sc, k, sim))
            print(f'K {k:3}: units used {nsym:3} (by length {dict(sorted(used.items()))}) | similarity {sim:.3f} | per-char {sc:.3f} | {dec[:60]}', flush=True)
    sc, k, sim = max(runs)
    print(f'GATE 3: chosen blind K {k} (per-char {sc:.3f}) -> similarity {sim:.3f} -> {"PASS" if sim >= 0.8 else "FAIL"}', flush=True)
    print(f'   truth: {truth[:60]}', flush=True)


if __name__ == '__main__':
    main()
