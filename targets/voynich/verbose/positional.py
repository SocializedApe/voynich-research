"""Gate 5: a positional verbose cipher of Latin, where the same glyph group stands for different letters by position.

Cipher (fixed before any run, 29 Oct 2026; seed 10): plaintext Pliny, 11,000 words (gate.plaintext), letters only.
  A pool of 30 codes (2 glyphs, or 3 with probability 1/3) over the 24-glyph alphabet. Four position classes: start,
  mid and end of a cipher word of two or more codes, and 'only' (a one-code word). Each class has its own one-to-one
  table letter -> code, drawn independently from the same pool, so a code string means different letters in different
  classes (one-to-many), the case the earlier sweeps could not represent.
  Cipher words: the letter stream is cut into words of 1, 2, 3, ... codes (after every code a break with probability
  0.5, as gate3.py), and each letter is written with the table of its position in its word.
Writes kaggle_pkg/data/texts/syn_gate5.json ({'lines', 'truth'}); the sweep's positional variants ('rawpos',
'nogalpos') tag every unit with its class before solving (sweep.select).

Run from the repository root: python targets/voynich/verbose/positional.py
"""
import collections, json, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import gate

CLASSES = ('start', 'mid', 'end', 'only')


def cipher_of(plain, rng):
    letters = sorted(set(''.join(plain)))
    pool = set()
    while len(pool) < 30:
        pool.add(''.join(rng.choice(gate.ALPHA24) for _ in range(3 if rng.random() < 1 / 3 else 2)))
    pool = sorted(pool)
    tables = {c: dict(zip(letters, rng.sample(pool, len(letters)))) for c in CLASSES}
    stream = ''.join(plain); words, cur = [], []
    for ch in stream:
        cur.append(ch)
        if rng.random() < 0.5: words.append(cur); cur = []
    if cur: words.append(cur)
    out = []
    for w in words:
        if len(w) == 1: out.append(tables['only'][w[0]]); continue
        out.append(''.join(tables['start' if i == 0 else 'end' if i == len(w) - 1 else 'mid'][ch] for i, ch in enumerate(w)))
    return out, tables, pool


def main():
    plain = gate.plaintext(11000); truth = ''.join(plain)
    words, tables, pool = cipher_of(plain, random.Random(10))
    shared = collections.Counter(code for t in tables.values() for code in t.values())
    multi = sum(1 for c in pool if len({tables[k][l] for k in CLASSES for l in tables[k] if tables[k][l] == c}) and
                len({l for k in CLASSES for l, cc in tables[k].items() if cc == c}) > 1)
    print(f'gate 5: {len(words)} cipher words, pool {len(pool)} codes, {multi} codes stand for 2+ letters by position; '
          f'sample: {" ".join(words[:10])}')
    out = os.path.join(HERE, 'kaggle_pkg', 'data', 'texts', 'syn_gate5.json')
    json.dump({'lines': [words[i:i + 9] for i in range(0, len(words), 9)], 'truth': truth}, open(out, 'w'))
    print('written', out)


if __name__ == '__main__':
    main()
