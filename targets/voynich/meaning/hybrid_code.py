"""Code plus copying scribe against cipher plus copying scribe.

Protocol, fixed before any run (28 Oct 2026):
  Bases: (a) the round-8 letter-unit cipher of Latin (research/voynich_siblings/cipher_models.py, BASE settings of
  hybrid_model.py); (b) codebook_vocab_it and codebook_vocab_la of codebook.py (Voynich word types as one-to-one codes
  of the b3 Italian / Latin controls).
  Scribe: hybrid_model.hybridize with the repo's best tuned setting q 0.15, w 8, e 0.9, g 0.2 (merge 0.0), unchanged,
  seeds 19 and 7; plus q 0.30 (same w, e, g), seed 19, as a sensitivity check. Nothing is tuned on the code.
  Scores: b3.battery + b3.score (all 37, and the 30 not used in hybrid_model's tuning), swap.run (page context, the
  d>30 value is the one compared), code_vs_copy.analyse (spread by rank, hapax neighbourhood).
  Expectation written in advance: if code+scribe matches at least as many b3 items as cipher+scribe and keeps page
  context near Voynich (about 0.59) where cipher+scribe falls toward chance, code+scribe becomes the leading model.

Run from the repository root: python targets/voynich/meaning/hybrid_code.py <naibbe_tables.csv>
"""
import collections, contextlib, io, json, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'research', 'voynich_siblings'))
import codebook as cbk
import swap, code_vs_copy
import a4_selfcitation as a4
import b3_bakeoff as b3
import hybrid_model as hm
import cipher_models as cm

SETTINGS = [(0.15, 8, 0.9, 0.2, 19), (0.15, 8, 0.9, 0.2, 7), (0.30, 8, 0.9, 0.2, 19)]


def main():
    csv_path = sys.argv[1]
    zl = b3.load_zl_lang(); skel = a4.skeleton(zl); N = len(b3.words_of(zl))
    lat = os.path.join(ROOT, 'lang', 'corpora', 'la-gutenberg.txt')
    vfreq = collections.Counter(b3.words_of(zl)); vtypes = sorted(vfreq, key=lambda w: -vfreq[w])
    C = collections.OrderedDict()
    C['voynich_ZL'] = zl
    C['autocopist_s19'] = a4.Autocopist(19).generate(skel); C['autocopist_s7'] = a4.Autocopist(7).generate(skel)
    codes = {}
    for lang in ('it', 'la'):
        plain = a4.lang_words(lang, N); rng = random.Random(5)
        extra = [c for c in cbk.template_codes(rng, len(set(plain))) if c not in vfreq]
        codes[lang] = a4.pour(cbk.encode(plain, vtypes + extra)[0], skel)
        C[f'code_{lang}'] = codes[lang]
    C['cipher'] = cm.generate(cm.Variant(csv_path, 19, merge=0.0, **hm.BASE), lat, skel)
    for q, w, e, g, seed in SETTINGS:
        tag = f'q{q:.2f}_s{seed}'
        C[f'cipher+scribe_{tag}'] = hm.build(csv_path, seed, q, w, e, g, 0.0, skel, lat)
        for lang in ('it', 'la'):
            C[f'code_{lang}+scribe_{tag}'] = hm.hybridize(codes[lang], random.Random(seed * 1000 + 7), q, w, e, g)
    print('corpora:', list(C), flush=True)
    full = collections.OrderedDict()
    for n, p in C.items():
        full[n] = b3.battery(p, n, {}); print(f'battery {n} done', flush=True)
    tol, marks = b3.score(full)
    held = [k for k, _ in b3.ITEMS if k not in hm.TUNED_B3]
    rng = random.Random(7); extra = {}
    for n, p in C.items():
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sw = swap.run(n, p, rng); code_vs_copy.analyse(n, p)
        extra[n] = {'swap': sw, 'printed': buf.getvalue()}
    print('\n| corpus | b3 all (37) | held-out (30) | page context d>30 | held-out misses |')
    print('|---|---|---|---|---|')
    for n in C:
        m = marks[n]
        print(f'| {n} | {sum(m.values())} | {sum(m[k] for k in held)} | {extra[n]["swap"][30]:.3f} | '
              + ', '.join(k for k in held if not m[k]) + ' |')
    print()
    for n in C: print(extra[n]['printed'], end='')
    json.dump({'full': full, 'tol': tol, 'marks': marks, 'held': held, 'extra': extra}, open(os.path.join(HERE, 'hybrid_code_results.json'), 'w'), indent=1, default=str)


if __name__ == '__main__':
    main()
