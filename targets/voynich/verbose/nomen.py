"""Nomenclator layer for the verbose attack: whole-word codes for the commonest words, a verbose letter cipher elsewhere.

Fixed before any run (29 Oct 2026):
  Plaintext model: the 12 commonest words of the language become single symbols (upper-case A-L, in frequency order),
  every other word stays in letters; order-5 letter-only model of that stream (lang DenseLM). Latin ('la-nom': the
  la-gutenberg corpus, 'latin' normalisation) and Italian ('it-nom': it-cinquecento corpora, 'early').
  Gate 7 (calibration): Pliny, 11,000 words, the same 12-word Latin codebook; each code word is one cipher word, an
  invented Voynich-like glyph string of 4-6 glyphs; every other word is enciphered letter by letter as gate3.py
  (homophones, 2-3-glyph codes, a space after each code with probability 0.5); code words stand between spaces (seed 11).
  Codebook words: English stop words excluded (the Gutenberg Latin texts carry English introductions; 'in' and 'a'
  kept), and single letters other than the vowel words a, e, o (page references and numerals in the corpus).
  Cipher side (sweep variant 'nom'): the 16 commonest cipher words of at least 4 glyphs become single units ('W:' +
  word) (amended before any solver run: by frequency alone the one-code words of the letter cipher crowd them out, and
  16 rather than 12 so that rarer code words are not cut into letter units);
  all other words are cut into SentencePiece units as before. The solver maps every unit to one symbol of the extended
  alphabet, so a unit may turn out to be a letter or one of the 12 word codes.
Writes kaggle_pkg/data/lm/{la-nom,it-nom}.npy/.json/.ref.json and kaggle_pkg/data/texts/syn_gate7.json.

Run from the repository root: python targets/voynich/verbose/nomen.py
"""
import collections, json, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, HERE); sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(HERE, 'kaggle_pkg'))
import numpy as np
from lang import lm, corpora

NCODE = 12
TOKENS = 'ABCDEFGHIJKL'
MODELS = {'la-nom': (['la-gutenberg'], 'latin'), 'it-nom': (['it-renaissance', 'it-nunziature'], 'early')}


ENGLISH = set('the of and to is that it was he for with as his i be by on this which not or are from at but have had her'.split())   # not in, a: Latin too
NCAND = 16   # cipher side: candidate code words (more than NCODE, so that rarer code words are not cut into letter units)
MINLEN = 4   # cipher side: candidate code words are the NCODE commonest cipher words of at least MINLEN glyphs


def codebook(words):
    """the NCODE commonest words, English stop words excluded (the Gutenberg Latin texts carry English matter)"""
    top = [w for w, _ in collections.Counter(words).most_common(NCODE + 50)
           if w not in ENGLISH and (len(w) > 1 or w in 'aeo')][:NCODE]
    return {w: TOKENS[i] for i, w in enumerate(top)}


def code_candidates(cipher_words):
    return [w for w, _ in collections.Counter(w for w in cipher_words if len(w) >= MINLEN).most_common(NCAND)]


def nomen_stream(words, book):
    return ''.join(book.get(w, w) for w in words)


def main():
    out = os.path.join(HERE, 'kaggle_pkg', 'data')
    books = {}
    for mid, (src, scheme) in MODELS.items():
        words = [w for w in lm.norm(corpora.text(src), scheme, True).split() if w]
        book = codebook(words); books[mid] = book
        meta_p = os.path.join(out, 'lm', mid + '.json')
        if os.path.exists(meta_p) and json.load(open(meta_p)).get('codebook') == book and '--rebuild' not in sys.argv:
            print(f'{mid}: model exists with this codebook {book}', flush=True); continue
        text = nomen_stream(words, book)
        alpha = lm.alphabet(scheme, False) + TOKENS
        cover = sum(1 for w in words if w in book) / len(words)
        print(f'{mid}: {len(words)} words; codebook {book}; code words are {cover:.1%} of tokens; alphabet {len(alpha)}', flush=True)
        m = lm.DenseLM.build(text, 5, alpha, dict(model=mid))
        np.save(os.path.join(out, 'lm', mid + '.npy'), m.lp)
        json.dump(dict(model=mid, order=5, alpha=alpha, chars=len(text), engine='dense', codebook=book, transform='verbose/nomen.py'),
                  open(os.path.join(out, 'lm', mid + '.json'), 'w'))
        ref = np.bincount(m.encode(text[200000:3200000]), minlength=m.A).astype(float) + 1; ref /= ref.sum()
        json.dump(ref.tolist(), open(os.path.join(out, 'lm', mid + '.ref.json'), 'w'))
    import gate, gate3
    rng = random.Random(11)
    plain = gate.plaintext(11000); book = books['la-nom']
    truth = nomen_stream(plain, book)
    gl = gate.ALPHA24; codes = {}
    while len(codes) < NCODE:
        c = ''.join(rng.choice(gl) for _ in range(rng.randint(4, 6)))
        if c not in codes.values(): codes[len(codes)] = c
    wordcode = {w: codes[TOKENS.index(t)] for w, t in book.items()}
    # letter cipher for everything else (gate-3 tables), code words as whole cipher words
    letters_plain = [w for w in plain if w not in book]
    _, table = gate3.cipher_of(letters_plain, random.Random(12))
    cipher, cur = [], ''
    for w in plain:
        if w in wordcode:
            if cur: cipher.append(cur); cur = ''
            cipher.append(wordcode[w]); continue
        for ch in w:
            cur += rng.choice(table[ch])
            if rng.random() < 0.5: cipher.append(cur); cur = ''
    if cur: cipher.append(cur)
    json.dump({'lines': [cipher[i:i + 9] for i in range(0, len(cipher), 9)], 'truth': truth}, open(os.path.join(out, 'texts', 'syn_gate7.json'), 'w'))
    cand = code_candidates(cipher)
    print(f'syn_gate7: {len(cipher)} cipher words; of the {NCAND} code candidates (commonest words of >= {MINLEN} glyphs), '
          f'{sum(1 for w in cand if w in wordcode.values())} are code words; truth {truth[:60]}')


if __name__ == '__main__':
    main()
