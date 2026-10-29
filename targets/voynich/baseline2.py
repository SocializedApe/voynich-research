"""baseline2.py -- word-level anchors: Zipf slope (ranks 1-1000), hapax fraction, type count at 34k tokens,
word-length mean/sd, adjacent exact and edit-1 repeats; Voynich ZL (P text) vs Latin, German, English, Italian."""
import os as _os  # local paths (the September 2026 scripts hard-coded another machine)
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_CORP = _os.path.join(_HERE, 'data', 'corpora')  # corp_<lang>_<gutenberg id>.txt, see fetch_corpora.py
_EXT = _os.path.join(_HERE, 'data', 'external')  # third-party data (Naibbe, Gaskell & Bowern)
_IT = _os.path.join(_CORP, 'corpus_it.txt')  # vatican5 OCR corpus from the September sample's first words (fetch_corpora.py)
import math, collections, re, pathlib, glob, sys, random
sys.stdout.reconfigure(encoding='utf-8')
HERE = pathlib.Path(__file__).parent
CORP = _CORP
rows = [l.rstrip('\n').split('\t') for l in open(HERE / 'data/ZL3b-n.words.tsv', encoding='utf-8')][1:]
voy = [w for r in rows if r[2] == 'P' for w in r[9].split() if '?' not in w and re.fullmatch(r'[a-z]+', w)]
def corpus(lang):
    text = ''
    for f in sorted(glob.glob(f'{CORP}/corp_{lang}_*.txt')):
        raw = open(f, encoding='utf-8', errors='ignore').read()
        m = re.search(r'\*\*\* ?START OF.*?\*\*\*', raw); raw = raw[m.end():] if m else raw
        m = re.search(r'\*\*\* ?END OF', raw); raw = raw[:m.start()] if m else raw
        text += raw.lower() + ' '
    return re.sub(r'[^a-zäöüßæøå]+', ' ', text).split()
def ed1(a, b):
    if a == b: return False
    if abs(len(a) - len(b)) > 1: return False
    if len(a) == len(b): return sum(x != y for x, y in zip(a, b)) == 1
    if len(a) > len(b): a, b = b, a
    for i in range(len(b)):
        if b[:i] + b[i+1:] == a: return True
    return False
def stats(name, toks, n=34116):
    toks = toks[:n]; c = collections.Counter(toks); freqs = sorted(c.values(), reverse=True)
    xs = [math.log(r) for r in range(1, 1001)]; ys = [math.log(f) for f in freqs[:1000]]
    mx = sum(xs)/len(xs); my = sum(ys)/len(ys); slope = sum((x-mx)*(y-my) for x, y in zip(xs, ys)) / sum((x-mx)**2 for x in xs)
    hapax = sum(1 for v in c.values() if v == 1) / len(c)
    L = [len(w) for w in toks]; mean = sum(L)/len(L); sd = (sum((l-mean)**2 for l in L)/len(L))**0.5
    adj = sum(1 for a, b in zip(toks, toks[1:]) if a == b) / (len(toks)-1)
    adj1 = sum(1 for a, b in zip(toks, toks[1:]) if ed1(a, b)) / (len(toks)-1)
    print(f'{name:22} types {len(c):5d}  zipf {slope:.2f}  hapax {hapax:.2f}  len {mean:.2f}+-{sd:.2f}  adj= {adj*100:.2f}%  adj_ed1 {adj1*100:.2f}%')
stats('Voynich ZL', voy)
for lang in ['la', 'de', 'en', 'da']: stats(lang, corpus(lang))
stats('it', open(pathlib.Path(_IT), encoding='utf-8').read().split())
