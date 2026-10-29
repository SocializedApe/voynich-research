"""baseline.py -- independent anchor numbers: h0/h1/h2 of the ZL letter stream (EVA raw and merged glyphs,
with and without word spaces) against Latin, Italian, German, English of the same size."""
import os as _os  # local paths (the September 2026 scripts hard-coded another machine)
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_CORP = _os.path.join(_HERE, 'data', 'corpora')  # corp_<lang>_<gutenberg id>.txt, see fetch_corpora.py
_EXT = _os.path.join(_HERE, 'data', 'external')  # third-party data (Naibbe, Gaskell & Bowern)
_IT = _os.path.join(_CORP, 'corpus_it.txt')  # vatican5 OCR corpus from the September sample's first words (fetch_corpora.py)
import math, collections, re, pathlib, glob, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = pathlib.Path(__file__).parent
CORP = _CORP
rows = [l.rstrip('\n').split('\t') for l in open(HERE / 'data/ZL3b-n.words.tsv', encoding='utf-8')][1:]
words = [w for r in rows if r[2] == 'P' for w in r[9].split() if '?' not in w and re.fullmatch(r'[a-z]+', w)]
MERGE = ['ckh', 'cth', 'cph', 'cfh', 'iiin', 'iin', 'sh', 'ch', 'ee', 'qo']
def merge(w):
    out = []; i = 0
    while i < len(w):
        for m in MERGE:
            if w.startswith(m, i): out.append(m); i += len(m); break
        else: out.append(w[i]); i += 1
    return out
def entropies(seq):
    n = len(seq); c1 = collections.Counter(seq); c2 = collections.Counter(zip(seq, seq[1:]))
    h0 = math.log2(len(c1)); h1 = -sum(v/n*math.log2(v/n) for v in c1.values())
    h12 = -sum(v/(n-1)*math.log2(v/(n-1)) for v in c2.values()); h2 = h12 - (-sum(v/(n-1)*math.log2(v/(n-1)) for v in collections.Counter(seq[:-1]).values()))
    return len(c1), h0, h1, h2
def report(name, tokens_of_words, nletters=150000):
    seq_sp = []; seq_ns = []
    for w in tokens_of_words:
        seq_sp += list(w) + [' ']; seq_ns += list(w)
        if len(seq_ns) >= nletters: break
    a = entropies(seq_sp); b = entropies(seq_ns)
    print(f'{name:28} with spaces: n={a[0]:2d} h1={a[2]:.3f} h2={a[3]:.3f} | no spaces: n={b[0]:2d} h1={b[2]:.3f} h2={b[3]:.3f}  (letters {len(seq_ns)})')
report('Voynich ZL EVA raw', [list(w) for w in words])
report('Voynich ZL EVA merged', [merge(w) for w in words])
A = [w for r in rows if r[2] == 'P' and r[3] == 'A' for w in r[9].split() if '?' not in w and re.fullmatch(r'[a-z]+', w)]
B = [w for r in rows if r[2] == 'P' and r[3] == 'B' for w in r[9].split() if '?' not in w and re.fullmatch(r'[a-z]+', w)]
report('Voynich A merged', [merge(w) for w in A]); report('Voynich B merged', [merge(w) for w in B])
def corpus(lang):
    text = ''
    for f in sorted(glob.glob(f'{CORP}/corp_{lang}_*.txt')):
        raw = open(f, encoding='utf-8', errors='ignore').read()
        m = re.search(r'\*\*\* ?START OF.*?\*\*\*', raw); raw = raw[m.end():] if m else raw
        m = re.search(r'\*\*\* ?END OF', raw); raw = raw[:m.start()] if m else raw
        text += raw.lower() + ' '
    text = re.sub(r'[^a-zäöüßæøå]+', ' ', text)
    return [list(w) for w in text.split()]
for lang in ['la', 'de', 'en', 'fr', 'da']: report(f'{lang} (Gutenberg)', corpus(lang))
it = open(pathlib.Path(_IT), encoding='utf-8').read().split()
report('it (Nuntiaturberichte)', [list(w) for w in it])
# Latin without vowels
lat = corpus('la'); report('la without vowels', [[c for c in w if c not in 'aeiouy'] or ['x'] for w in lat])
print('word tokens', len(words), 'types', len(set(words)), 'mean word length', sum(len(w) for w in words)/len(words), 'merged mean', sum(len(merge(w)) for w in words)/len(words))
