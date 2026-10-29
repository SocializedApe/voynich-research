"""Write every input of the verbose sweep into kaggle_pkg/data/, so the package runs without the repository.

  texts/<name>.json   {'lines': [[word, ...], ...], 'truth': str or None}
    Voynich groups from the ZL fixed parse (paragraph text, a-z words): A herbal, B herbal, A all, B all, hand 1
    pharmaceutical, hand 2 biological, hand 3 stars. Synthetic calibration ciphers with their plaintext: syn_gate2
    (gate2.py: verbose24 Latin, 11,000 words, seed 6; lines of 9 words) and syn_gate3 (gate3.py: homophones, mixed
    code lengths, spaces not at plaintext word boundaries; seed 8).
  lm/<model>.npy/.json  the lang/ order-5 letter-only tables (la, it-cinquecento, de-1500s, ca-modern)
  lm/<model>.ref.json   the language's letter frequencies (from its corpora; the solver's KL reference)
Also checks the incremental solver against a full recomputation on each language.

Run from the repository root: python targets/voynich/verbose/prepare.py
"""
import csv, json, os, random, re, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'kaggle_pkg'))
import numpy as np
import gate, gate3
import solver
from lang import lm, corpora

PKG = os.path.join(HERE, 'kaggle_pkg', 'data')
MODELS = ['la', 'it-cinquecento', 'de-1500s', 'ca-modern']


def main():
    os.makedirs(os.path.join(PKG, 'texts'), exist_ok=True); os.makedirs(os.path.join(PKG, 'lm'), exist_ok=True)
    rows = [r for r in csv.DictReader(open(os.path.join(HERE, '..', 'data', 'ZL3b-n.fixed.words.tsv'), encoding='utf-8'), delimiter='\t')
            if r['locus_type'] == 'P']
    groups = {'voy_A_herbal': lambda r: r['lang'] == 'A' and r['illus'] == 'H', 'voy_B_herbal': lambda r: r['lang'] == 'B' and r['illus'] == 'H',
              'voy_A_all': lambda r: r['lang'] == 'A', 'voy_B_all': lambda r: r['lang'] == 'B',
              'voy_h1_pharma': lambda r: r['hand'] == '1' and r['illus'] == 'P', 'voy_h2_bio': lambda r: r['hand'] == '2' and r['illus'] == 'B',
              'voy_h3_stars': lambda r: r['hand'] == '3' and r['illus'] == 'S'}
    for name, f in groups.items():
        lines = [[w for w in r['line_words'].split() if re.fullmatch(r'[a-z]+', w)] for r in rows if f(r)]
        lines = [l for l in lines if l]
        json.dump({'lines': lines, 'truth': None}, open(os.path.join(PKG, 'texts', name + '.json'), 'w'))
        print(f'{name}: {len(lines)} lines, {sum(map(len, lines))} words')
    plain = gate.plaintext(11000); truth = ''.join(plain)
    mp = gate.a1.verbose_cipher_map(plain, gate.ALPHA24, 0, 24, seed=6); c2 = gate.a1.verbose_encode(plain, mp)
    json.dump({'lines': [c2[i:i + 9] for i in range(0, len(c2), 9)], 'truth': truth}, open(os.path.join(PKG, 'texts', 'syn_gate2.json'), 'w'))
    c3, _ = gate3.cipher_of(plain, random.Random(8))
    json.dump({'lines': [c3[i:i + 9] for i in range(0, len(c3), 9)], 'truth': truth}, open(os.path.join(PKG, 'texts', 'syn_gate3.json'), 'w'))
    print(f'syn_gate2: {len(c2)} words; syn_gate3: {len(c3)} words')
    models, _ = lm.registry()
    for mid in MODELS:
        m = lm.load(mid, order=5, spaces=False)
        src = os.path.join(ROOT, 'lang', 'cache', f'{mid}.o5.ns')
        shutil.copy(src + '.npy', os.path.join(PKG, 'lm', mid + '.npy'))
        meta = json.load(open(src + '.json')); meta['alpha'] = m.alpha
        json.dump(meta, open(os.path.join(PKG, 'lm', mid + '.json'), 'w'))
        sample = lm.norm(corpora.text(models[mid]['sources'])[200000:3200000], models[mid]['norm'], False)
        ref = np.bincount(m.encode(sample), minlength=m.A).astype(float) + 1; ref /= ref.sum()
        json.dump(ref.tolist(), open(os.path.join(PKG, 'lm', mid + '.ref.json'), 'w'))
        L = solver.LM(np.load(src + '.npy'), meta['order'], m.alpha)
        syms = [p for w in c2[:3000] for p in (w[i:i + 2] for i in range(0, len(w), 2))]
        err = solver.check(syms, L, ref, random.Random(1))
        print(f'{mid}: alphabet {m.alpha} ({m.A}), incremental-vs-full max relative error {err:.2e}')


if __name__ == '__main__':
    main()
