"""Synthetic codebook (whole-word code) texts against the b3 battery and today's tests.

Design, fixed before any run (28 Oct 2026):
  Plaintext: the b3 language controls, a4.lang_words('la' | 'it', N), N = ZL paragraph tokens; one code word per
  plaintext word, poured into the ZL skeleton (a4.pour), as b3 does for its language controls.
  codebook_vocab: the code words are Voynich's own word types. Plaintext types sorted by frequency are assigned
    one-to-one to Voynich types sorted by frequency (rank to rank, ties in corpus order). If the plaintext has more
    types than Voynich, the extra code words come from the template below (never an existing Voynich word).
  codebook_template: code words built from Rugg's prefix / middle / suffix lists (a4.Rugg.PRE, MID, SUF), every
    distinct non-empty combination; shortest codes to the most frequent plaintext words (ties random, seed 5); if
    there are not enough, a second middle slot is added.
  No homophones, no nulls, no letter spelling of rare words in this round.
Scoring: b3.battery on every corpus and b3.score (tolerance from the two autocopist seeds, real = voynich_ZL);
  plus spaces.score (word-space predictability), swap.run (page context from pages > d away), code_vs_copy.analyse
  (spread by rank, hapax neighbourhood).

Run from the repository root: python targets/voynich/meaning/codebook.py   (writes meaning/codebook_results.json)
"""
import collections, io, itertools, json, os, random, sys, contextlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, os.path.join(HERE, '..', 'glyphs'))
import a4_selfcitation as a4
import b3_bakeoff as b3
import swap, code_vs_copy
from spaces import score as space_score
from variants import UNIT


def template_codes(rng, need):
    combos = {p + m + s for p in a4.Rugg.PRE for m in a4.Rugg.MID for s in a4.Rugg.SUF} - {''}
    if len(combos) < need:
        combos |= {p + m + m2 + s for p in a4.Rugg.PRE for m in a4.Rugg.MID for m2 in a4.Rugg.MID for s in a4.Rugg.SUF} - {''}
    codes = sorted(combos); rng.shuffle(codes); codes.sort(key=len)
    return codes


def encode(plain, codes_by_rank):
    freq = collections.Counter(plain)
    order = sorted(freq, key=lambda w: -freq[w])          # stable: ties keep first-seen order
    table = dict(zip(order, codes_by_rank))
    assert len(table) == len(order) and len(set(table.values())) == len(table), 'codebook not one-to-one'
    return [table[w] for w in plain], table


def main():
    zl = b3.load_zl_lang(); skel = a4.skeleton(zl); N = len(b3.words_of(zl))
    vfreq = collections.Counter(b3.words_of(zl)); vtypes = sorted(vfreq, key=lambda w: -vfreq[w])
    C = collections.OrderedDict()
    C['voynich_ZL'] = zl
    C['voynich_B'] = [p for p in zl if p['lang'] == 'B']
    plains = {}
    for lang, name in (('la', 'latin'), ('it', 'italian')):
        plains[lang] = a4.lang_words(lang, N); C[name] = a4.pour(plains[lang], skel)
    C['autocopist_s19'] = a4.Autocopist(19).generate(skel); C['autocopist_s7'] = a4.Autocopist(7).generate(skel)
    C['rugg_sorted'] = a4.RuggSorted(19).generate(skel)
    meta = {}
    for lang, plain in plains.items():
        ntypes = len(set(plain))
        rng = random.Random(5)
        extra = [c for c in template_codes(rng, ntypes) if c not in vfreq]
        codes, table = encode(plain, vtypes + extra)
        C[f'codebook_vocab_{lang}'] = a4.pour(codes, skel)
        meta[f'codebook_vocab_{lang}'] = {'plain_types': ntypes, 'voynich_types': len(vtypes), 'template_extra_used': max(0, ntypes - len(vtypes)),
                                          'top10': [(w, table[w]) for w, _ in collections.Counter(plain).most_common(10)]}
        rng = random.Random(5)
        codes, table = encode(plain, template_codes(rng, ntypes))
        C[f'codebook_template_{lang}'] = a4.pour(codes, skel)
        meta[f'codebook_template_{lang}'] = {'plain_types': ntypes, 'top10': [(w, table[w]) for w, _ in collections.Counter(plain).most_common(10)]}
    print('built:', {k: len(b3.words_of(v)) for k, v in C.items()}, flush=True)
    for k, v in meta.items(): print(k, v, flush=True)
    full, xf = collections.OrderedDict(), {}
    for n, p in C.items():
        full[n] = b3.battery(p, n, xf); print(f'battery {n} done', flush=True)
    tol, marks = b3.score(full)
    extra = {}
    rng = random.Random(7)
    for n, p in C.items():
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            space_score(n, [[UNIT.findall(w) for w in ln['words']] for q in p for ln in q['lines']])
            sw = swap.run(n, p, rng)
            code_vs_copy.analyse(n, p)
        extra[n] = {'printed': buf.getvalue(), 'swap': sw}
        print(buf.getvalue(), end='', flush=True)
    out = {'meta': meta, 'full': full, 'tol': tol, 'marks': marks,
           'matches': {n: sum(m.values()) for n, m in marks.items()}, 'items': len(next(iter(marks.values()))), 'extra': extra}
    json.dump(out, open(os.path.join(HERE, 'codebook_results.json'), 'w'), indent=1, default=str)
    print('\nb3 items matched (of %d):' % out['items'])
    for n, k in out['matches'].items(): print(f'  {n:24} {k}')


if __name__ == '__main__':
    main()
