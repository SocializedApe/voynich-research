"""Abbreviated Latin for the verbose attack: transform, language model, letter reference, gate-4 synthetic cipher.

Medieval Latin scribes wrote frequent pieces as signs. If Voynich enciphers abbreviated Latin, decryptions must be
judged against abbreviated Latin. The transform (fixed before any run, 29 Oct 2026), on each word of Latin normalised
by lang.lm 'latin' (no j v k y w), in this order:
  word et -> '&' (Tironian et)            word est -> '=' (est sign)
  initial con-/com- (word longer than 4) -> '7' (con sign)
  per anywhere -> 'P'                      initial pro- -> 'R'          initial prae- -> 'B'
  final -que (word longer than 3) -> 'Q'   final -rum -> 'M'            final -us (word longer than 2) -> '9'
  final -m after a vowel -> '~' (macron)   n before a consonant -> '~'
Alphabet: the 21 Latin letters plus & = 7 P R B Q M 9 ~ (31 symbols).

Writes into kaggle_pkg/data/: lm/la-abbr.npy/.json/.ref.json (order-5 letter-only model of the abbreviated
la-gutenberg corpus, built with lang.lm.DenseLM) and texts/syn_gate4.json (Pliny abbreviated, 11,000 words, enciphered
as gate3.py: homophones for the 8 commonest symbols, 2-3-glyph codes, a space after each code with probability 0.5;
seed 9; truth = the abbreviated plaintext).

Run from the repository root: python targets/voynich/verbose/abbrev.py
"""
import collections, json, os, random, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, HERE); sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(HERE, 'kaggle_pkg'))
import numpy as np
from lang import lm, corpora

LATIN = lm.alphabet('latin', False)
SIGNS = '&=7PRBQM9~'
ALPHA = LATIN + SIGNS
VOW = set('aeiou')


def abbreviate_word(w):
    if w == 'et': return '&'
    if w == 'est': return '='
    if len(w) > 4 and (w.startswith('con') or w.startswith('com')): w = '7' + w[3:]
    if w.startswith('prae'): w = 'B' + w[4:]
    elif w.startswith('pro'): w = 'R' + w[3:]
    w = w.replace('per', 'P')
    if len(w) > 3 and w.endswith('que'): w = w[:-3] + 'Q'
    elif w.endswith('rum'): w = w[:-3] + 'M'
    elif len(w) > 2 and w.endswith('us'): w = w[:-2] + '9'
    if len(w) > 1 and w.endswith('m') and w[-2] in VOW: w = w[:-1] + '~'
    w = re.sub(r'n(?=[bcdfghlmnpqrstxz])', '~', w)
    return w


def abbreviate(words): return [abbreviate_word(w) for w in words]


def latin_words(text):
    return [w for w in lm.norm(text, 'latin', True).split() if w]


def main():
    out = os.path.join(HERE, 'kaggle_pkg', 'data')
    raw = corpora.text(['la-gutenberg'])
    words = latin_words(raw)
    ab = abbreviate(words)
    plain_len, ab_len = sum(map(len, words)), sum(map(len, ab))
    sym = collections.Counter(c for w in ab for c in w)
    print(f'corpus: {len(words)} words, {plain_len} letters -> {ab_len} symbols ({ab_len / plain_len:.1%}); signs per 1,000 symbols: '
          + ' '.join(f'{s}:{1000 * sym[s] / ab_len:.1f}' for s in SIGNS))
    print('sample:', ' '.join(f'{a}' for a in ab[1000:1030]))
    text = ''.join(ab)
    m = lm.DenseLM.build(text, 5, ALPHA, dict(model='la-abbr', chars=len(text), sources=['la-gutenberg'], transform='abbrev.py'))
    os.makedirs(os.path.join(out, 'lm'), exist_ok=True)
    np.save(os.path.join(out, 'lm', 'la-abbr.npy'), m.lp)
    json.dump(dict(model='la-abbr', order=5, alpha=ALPHA, chars=len(text), engine='dense', transform='verbose/abbrev.py'),
              open(os.path.join(out, 'lm', 'la-abbr.json'), 'w'))
    sample = text[200000:3200000]
    ref = np.bincount(m.encode(sample), minlength=m.A).astype(float) + 1; ref /= ref.sum()
    json.dump(ref.tolist(), open(os.path.join(out, 'lm', 'la-abbr.ref.json'), 'w'))
    import gate, gate3
    plain = abbreviate(gate.plaintext(11000)); truth = ''.join(plain)
    c4, table = gate3.cipher_of(plain, random.Random(9))
    json.dump({'lines': [c4[i:i + 9] for i in range(0, len(c4), 9)], 'truth': truth}, open(os.path.join(out, 'texts', 'syn_gate4.json'), 'w'))
    print(f'syn_gate4: {len(c4)} cipher words, {sum(len(v) for v in table.values())} codes for {len(table)} symbols; plaintext {truth[:70]}')
    import solver
    L = solver.LM(m.lp, 5, ALPHA)
    print(f'self-check: per-char of abbreviated Pliny under la-abbr {L.per_char(truth[:20000]):.3f}; '
          f'incremental-vs-full max relative error {solver.check(list(truth[:6000]), L, ref, random.Random(1)):.2e}')


if __name__ == '__main__':
    main()
