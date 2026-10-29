"""First exploratory Voynich run of the verbose pipeline validated by gate2.py (gate 3 not yet passed).

Protocol, fixed before the run (29 Oct 2026):
  Texts, separately (A and B are different systems): Voynich herbal pages of Currier language A, and of language B
  (ZL fixed parse, paragraph text, words as transcribed).
  Pipeline as gate2.py: SentencePiece units (pieces <= 3 glyphs) for K in (36, 42, 50) -> attack_v0.solve, unit ->
  letter, 5-gram model without spaces, seeds 1 and 2; for each text and language the K with the best per-character LM
  score is chosen blind. Languages: Latin ('la') and Italian ('it-cinquecento', with its own unigram reference as in
  research/voynich_siblings/attack/run_voynich.py).
  Control: the chosen K's unit stream shuffled (units kept, order destroyed), solved the same way.
  Rule: SIGNAL for a text and language if the chosen run's per-character score is >= -2.2 (a solved synthetic Latin
  verbose cipher scores -1.95 to -2.0, failed runs -2.5 to -2.9) AND exceeds its shuffled control by >= 0.3;
  otherwise NO SIGNAL. A decryption is never claimed from this run. Because gate 3 (homophones, unaligned spaces) is
  not yet passed, NO SIGNAL does not exclude a verbose cipher.

Run from the repository root: python targets/voynich/verbose/voy1.py
"""
import collections, csv, os, random, re, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import gate, gate2
import attack_v0 as v0
from lang import lm, corpora


def italian_model():
    m = lm.load('it-cinquecento', order=5, spaces=False)
    sample = lm.norm(corpora.text(lm.registry()[0]['it-cinquecento']['sources'])[:3000000], 'early', False)
    c = np.bincount(m.encode(sample), minlength=m.A).astype(float) + 1
    return m, (lambda mm, c=c: c / c.sum())


def main():
    rows = [r for r in csv.DictReader(open(os.path.join(HERE, '..', 'data', 'ZL3b-n.fixed.words.tsv'), encoding='utf-8'), delimiter='\t')
            if r['locus_type'] == 'P' and r['illus'] == 'H']
    texts = {L: [w for r in rows if r['lang'] == L for w in r['line_words'].split() if re.fullmatch(r'[a-z]+', w)] for L in ('A', 'B')}
    print('herbal words:', {k: len(v) for k, v in texts.items()}, flush=True)
    la = lm.load('la', order=5, spaces=False); la_uni = v0.latin_unigram
    it, it_uni = italian_model()
    with tempfile.TemporaryDirectory() as tmp:
        for L, words in texts.items():
            units = {k: [p for ws in gate2.learn_units(words, k, tmp) for p in ws] for k in (36, 42, 50)}
            for lname, model, uni in (('Latin', la, la_uni), ('Italian', it, it_uni)):
                v0.latin_unigram = uni
                runs = []
                for k, syms in units.items():
                    sc, dec, nsym = gate.solve_best(syms, model, seeds=(1, 2))
                    runs.append((sc, k, dec, nsym))
                    print(f'herbal {L} | {lname:7} | K {k}: units {nsym} | per-char {sc:.3f} | {dec[:70]}', flush=True)
                sc, k, dec, nsym = max(runs)
                sh = units[k][:]; random.Random(4).shuffle(sh)
                ssc, sdec, _ = gate.solve_best(sh, model, seeds=(1, 2))
                verdict = 'SIGNAL' if sc >= -2.2 and sc - ssc >= 0.3 else 'NO SIGNAL'
                print(f'RESULT herbal {L} {lname}: chosen K {k}, per-char {sc:.3f}, shuffled {ssc:.3f}, gap {sc - ssc:+.3f} -> {verdict}', flush=True)
                print(f'   decryption: {dec[:200]}', flush=True)
                print(f'   shuffled:   {sdec[:120]}', flush=True)
            v0.latin_unigram = la_uni


if __name__ == '__main__':
    main()
