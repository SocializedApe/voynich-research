"""Robustness of the start/end result (slot_independence.md):
  1. a second transliteration, Takahashi IT2a (parsed with parse_ivtff.py --fixed; path argv[1]);
  2. human gibberish, Gaskell & Bowern 2022 volunteer files (folder argv[2]; shipped in github.com/greshko/naibbe-cipher
     figure_utils/gaskell_bowern_2022/data/gibberish_transcriptions);
  3. verbose ciphers of Latin, fixed and 3-homophone, 5 random tables each, with LENGTH MATCHING: plaintext words are
     taken only if their ciphertext falls in 4-8 glyph units, so the measured tokens span the same length window as
     Voynich's and come from all plaintext word lengths that fit.
Run from the repository root."""
import glob, os, random, re, sys, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import slot_independence as si

rng = random.Random(41)
N = si.N_TOK


def report(name, toks, unit):
    a = si.measure([unit(w) for w in toks], 1, rng)
    b = si.measure([unit(w) for w in toks], 2, rng)
    print(f'{name:48s} tokens(4-8) {a[2]:6d}  k1 {a[0]:.3f}  k2 {b[0]:.3f}', flush=True)


si.TSV = os.path.join(HERE, '..', '..', 'targets', 'voynich', 'data', 'ZL3b-n.fixed.words.tsv')
v = si.voynich(); rng.shuffle(v); report('Voynich ZL3b (fixed parse)', v[:N], si.eva_units)
si.TSV = sys.argv[1]
for lang in (None, 'A', 'B'):
    v = si.voynich(lang); rng.shuffle(v); report(f'Voynich IT2a {lang or "all"} (fixed parse)', v[:N], si.eva_units)

gib = []
for f in sorted(glob.glob(os.path.join(sys.argv[2], '*.txt'))):
    t = unicodedata.normalize('NFKD', open(f, encoding='utf-8', errors='replace').read().lower())
    gib += re.findall(r'[a-z]+', t.encode('ascii', 'ignore').decode())
report(f'Gaskell & Bowern gibberish ({len(gib)} tokens)', gib, list)

lat = si.corpus('Latin')
pairs = ['qo', 'ok', 'ol', 'ch', 'sh', 'ed', 'dy', 'ai', 'in', 'ar', 'or', 'al', 'ee', 'ot', 'ke', 'te',
         'da', 'yk', 'od', 'ey', 'cth', 'lk', 'sa', 'ro', 'am', 'ir', 'ck', 'op', 'ty', 'ol', 'ky', 'oe']
for hom in (1, 3):
    vals1, vals2 = [], []
    for t in range(5):
        r = random.Random(100 + t)
        pool = pairs[:]; r.shuffle(pool)
        pool += [a + b for a in 'oyda' for b in ['l', 'r', 'n', 'm', 'dy', 'ky']]
        table = {c: [pool[(i * hom + j) % len(pool)] for j in range(hom)] for i, c in enumerate('abcdefghijklmnopqrstuvwxyz')}
        out = []
        for w in lat:
            ct = ''.join(r.choice(table[c]) for c in w)
            if 4 <= len(si.eva_units(ct)) <= 8:
                out.append(ct)
            if len(out) >= N:
                break
        toks = [si.eva_units(w) for w in out]
        vals1.append(si.measure(toks, 1, rng)[0]); vals2.append(si.measure(toks, 2, rng)[0])
    print(f'{"verbose Latin, length-matched, " + str(hom) + " homophone(s)/letter":48s} 5 tables  k1 {min(vals1):.3f}-{max(vals1):.3f}  k2 {min(vals2):.3f}-{max(vals2):.3f}', flush=True)
