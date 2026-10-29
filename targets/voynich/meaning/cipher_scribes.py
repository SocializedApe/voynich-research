"""Can a cipher make scribes look as different as gibberish volunteers (#22)? scribe_ratio.py's measure on enciphered text.

Protocol, fixed before any run (28 Oct 2026):
  Five 'scribes', each enciphering a different stretch of Latin (lang/corpora/la-gutenberg.txt, consecutive chunks)
  into 15 pages of 120 words (12 lines of 10), so each scribe gives 9 documents of 200 words as in scribe_ratio.py.
  Systems:
    naibbe_shared     Greshko's Naibbe, the same tables for every scribe
    round8_shared     the round-8 cipher (hybrid_model.BASE: page-level table subsets, chaining, nulls), shared tables
    naibbe_own        each scribe has his own tables: the glyph strings permuted among the codes of each kind
                      (unigram, prefix, suffix), i.e. the same system learned with a different table
    round8_own        the same for round-8
    round8_lang       shared round-8 tables, scribes 1-2 Latin and 3-5 Italian (a change of plaintext language)
  Measure: scribe_ratio.analyse unchanged (glyph-unit pairs, 100-word halves, bootstrap over scribes and documents).
  Compared with scribe_ratio_results.json: Voynich 2.97 [2.29-3.46], same scribe other document 2.00; gibberish 3.16;
  Auchinleck 1.42, same scribe 1.32.

Run from the repository root: python targets/voynich/meaning/cipher_scribes.py <naibbe_tables.csv>
"""
import json, os, random, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'research', 'voynich_siblings'))
import scribe_ratio as sr
import a4_selfcitation as a4
import hybrid_model as hm
import cipher_models as cm
from variants import UNIT

SCRIBES, PAGES, LINES, PER_LINE = 5, 15, 12, 10
SKEL = [[(PER_LINE, 0, li == 0) for li in range(LINES)] for _ in range(PAGES)]


def own_tables(v, seed):
    rng = random.Random(seed)
    for kind in ('unigram_', 'prefix_', 'suffix_'):
        codes = sorted(c for c in v.glyph if c.startswith(kind)); vals = [v.glyph[c] for c in codes]; rng.shuffle(vals)
        v.glyph.update(zip(codes, vals))
    v.unigram_glyphs = {g for c, g in v.glyph.items() if c.startswith('unigram_')}
    return v


def main():
    csv_path = sys.argv[1]; tmp = tempfile.mkdtemp()
    need = PAGES * LINES * PER_LINE * 2   # plaintext words per scribe, with room (one cipher word is 1-2 letters)
    src = {'la': a4.gutenberg_words(os.path.join(ROOT, 'lang', 'corpora', 'la-gutenberg.txt')), 'it': a4.gutenberg_words(a4.IT)}
    def plain(s, lang):
        ws = src[lang][s * need:(s + 1) * need]; p = os.path.join(tmp, f'{lang}{s}.txt')
        open(p, 'w', encoding='utf-8').write('\n'.join(' '.join(ws[i:i + 12]) for i in range(0, len(ws), 12))); return p
    systems = {
        'naibbe_shared': lambda s: (cm.Variant(csv_path, 19 + s), 'la'),
        'round8_shared': lambda s: (cm.Variant(csv_path, 19 + s, merge=0.0, **hm.BASE), 'la'),
        'naibbe_own': lambda s: (own_tables(cm.Variant(csv_path, 19 + s), 100 + s), 'la'),
        'round8_own': lambda s: (own_tables(cm.Variant(csv_path, 19 + s, merge=0.0, **hm.BASE), 100 + s), 'la'),
        'round8_lang': lambda s: (cm.Variant(csv_path, 19 + s, merge=0.0, **hm.BASE), 'la' if s < 2 else 'it'),
    }
    rng = random.Random(17); out = {}
    for name, make in systems.items():
        groups = {}
        for s in range(SCRIBES):
            v, lang = make(s)
            pages = cm.generate(v, plain(s, lang), SKEL)
            groups[str(s)] = [w for p in pages for ln in p['lines'] for w in ln['words']]
        out[name] = sr.analyse(name, sr.docs_of(groups), UNIT.findall, rng)
    json.dump(out, open(os.path.join(HERE, 'cipher_scribes_results.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
