"""Phase 2 data set: chunks of 4,000 words of known kinds of text, each turned into the features of features.py.
(11 Nov 2026)

Kinds and processes (every chunk is 4,000 tokens; 'source' is the language or generator a chunk comes from and is
the unit held out in cross-validation):
  natural    plain        50 languages of the Bible corpus (corpora2.py), 4 chunks each; other genres: the Latin
                          Gutenberg corpus and the Gutenberg texts in lang/corpora (1-4 chunks); real manuscripts in
                          graphic transcription (CREMMA, lines/fetch_mss.py) with 4,000+ words
  cipher     (a language underneath, 1 chunk per language and process)
             verbose      every letter -> a fixed group of 1-3 glyphs over 18 glyphs
             homophonic   every letter -> one of 1-4 symbols (more for frequent letters), drawn at random
             abjad        the vowels found by Sukhotin's algorithm are deleted
             digraphic    pairs of letters inside a word -> one symbol
             anagram      the letters of every word sorted
             respace      spaces removed and put back at the same word lengths in shuffled order
             nulls        one of 3 null symbols inserted after a letter with probability 0.2
             codebook     every word type -> an invented pronounceable word (frequent words shorter)
  generated  (no message)
             markov1/2/3  words drawn independently from a symbol chain of that order fitted to a language
             bag          the words of a language in random order
             table        three columns of invented syllables, one cell of each per word (table and grille)
             selfcite     60% of words copy one of the previous 30 words, half of those with one edit; the rest
                          are new invented words
  Held out of all training (kind 'mimic'): texts made to look like Voynich or from the Voynich literature: the
  autocopist (6 seeds), Rugg's table text, the Naibbe ciphertext of Pliny, the gibberish of Gaskell & Bowern's
  volunteers, this repository's generator lang8 (slots8.py, 2 seeds).
  Voynich (kind 'voynich'): ZL paragraph text in reading order, 8 chunks, with glyph units as symbols; the same with
  EVA characters as symbols; the Takahashi transliteration with glyph units.

Run from targets/voynich: python phase2/build.py -> phase2/features.csv (about 25 minutes)
"""
import collections, csv, glob, os, random, re, sys, time, zlib
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..')
sys.path.insert(0, HERE); sys.path.insert(0, VOY); sys.path.insert(0, os.path.join(VOY, 'lines')); sys.path.insert(0, os.path.join(VOY, 'reinforce')); sys.path.insert(0, os.path.join(VOY, 'meaning'))
sys.path.insert(0, os.path.join(VOY, '..', '..', 'research', 'voynich_siblings'))
from features import features, pack, sukhotin

N = 4000
WORD = re.compile(r'[^\W\d_]+', re.UNICODE)
CONS = 'ptkbdgmnslrfvzhc'; VOW = 'aeiou'


def sym(i):
    return chr(0xE100 + i)


def syllable(rng):
    return rng.choice(CONS) + rng.choice(VOW) + (rng.choice('nrsl') if rng.random() < 0.25 else '')


def invented(rng, n=None):
    return ''.join(syllable(rng) for _ in range(n or rng.choice((1, 2, 2, 3, 3, 4))))


# ------------------------------------------------------------------------------------------- ciphers
def verbose(ws, rng):
    letters = sorted({c for w in ws for c in w}); codes = set(); m = {}
    for c in letters:
        while True:
            g = ''.join(sym(rng.randrange(18)) for _ in range(rng.choices((1, 2, 3), (0.2, 0.5, 0.3))[0]))
            if g not in codes:
                codes.add(g); m[c] = g; break
    return [''.join(m[c] for c in w) for w in ws]


def homophonic(ws, rng):
    cnt = collections.Counter(c for w in ws for c in w); tot = sum(cnt.values()); m = {}; k = 0
    for c, v in cnt.items():
        n = 1 + min(3, int(v / tot / 0.03)); m[c] = [sym(k + i) for i in range(n)]; k += n
    return [''.join(rng.choice(m[c]) for c in w) for w in ws]


def abjad(ws, rng):
    V = sukhotin(ws)
    return [x for x in (''.join(c for c in w if c not in V) for w in ws) if x]


def digraphic(ws, rng):
    m = {}
    return [''.join(m.setdefault(w[i:i + 2], sym(len(m))) for i in range(0, len(w), 2)) for w in ws]


def anagram(ws, rng):
    return [''.join(sorted(w)) for w in ws]


def respace(ws, rng):
    s = ''.join(ws); L = [len(w) for w in ws]; rng.shuffle(L); out = []; i = 0
    for n in L:
        out.append(s[i:i + n]); i += n
    return out


def nulls(ws, rng):
    nl = [sym(900 + i) for i in range(3)]
    return [''.join(c + (rng.choice(nl) if rng.random() < 0.2 else '') for c in w) for w in ws]


def codebook(ws, rng):
    cnt = collections.Counter(ws); m = {}; used = set()
    for r, (w, _) in enumerate(cnt.most_common()):
        while True:
            x = invented(rng, 1 if r < 15 else 2 if r < 150 else None)
            if x not in used:
                used.add(x); m[w] = x; break
    return [m[w] for w in ws]


# ------------------------------------------------------------------------------------------- generators
def markov(order):
    def gen(ws, rng):
        t = collections.defaultdict(collections.Counter)
        for w in ws:
            s = '^' * order + w + '$'
            for i in range(order, len(s)):
                t[s[i - order:i]][s[i]] += 1
        tab = {k: (list(v), list(v.values())) for k, v in t.items()}; out = []
        while len(out) < N:
            c = '^' * order; w = ''
            while True:
                x = rng.choices(*tab[c])[0]
                if x == '$' or len(w) > 30:
                    break
                w += x; c = (c + x)[1:]
            if w:
                out.append(w)
        return out
    return gen


def bag(ws, rng):
    ws = ws[:]; rng.shuffle(ws); return ws


def table(rng):
    cols = [[invented(rng, 1) if rng.random() < 0.8 else '' for _ in range(n)] for n in (12, 20, 12)]
    wts = [[1.0 / (i + 1) for i in range(len(c))] for c in cols]; out = []
    while len(out) < N:
        w = ''.join(rng.choices(c, wt)[0] for c, wt in zip(cols, wts))
        if w:
            out.append(w)
    return out


def selfcite(rng):
    out = [invented(rng) for _ in range(10)]
    while len(out) < N:
        if rng.random() < 0.6:
            w = rng.choice(out[-30:])
            if rng.random() < 0.5:
                i = rng.randrange(len(w)); k = rng.random()
                w = w[:i] + (rng.choice(CONS + VOW) + w[i + 1:] if k < 0.5 else w[i + 1:] if k < 0.75 and len(w) > 1 else rng.choice(CONS + VOW) + w[i:])
        else:
            w = invented(rng)
        out.append(w)
    return out


CIPHERS = collections.OrderedDict(verbose=verbose, homophonic=homophonic, abjad=abjad, digraphic=digraphic, anagram=anagram, respace=respace, nulls=nulls, codebook=codebook)
GENS = collections.OrderedDict(markov1=markov(1), markov2=markov(2), markov3=markov(3), bag=bag)


def read_words(path):
    return WORD.findall(open(path, encoding='utf-8', errors='replace').read().lower())


def main():
    t0 = time.time(); rows = []; rng = random.Random(2026)

    def add(kind, process, source, chunk, ws):
        ws = [w for w in ws if w][:N]
        if len(ws) < N:
            return
        f = features(ws, random.Random(zlib.crc32(f"{process}|{source}|{chunk}".encode()) % 10 ** 6)); rows.append(dict(kind=kind, process=process, source=source, chunk=chunk, **f))
        if len(rows) % 50 == 0:
            print(len(rows), kind, process, source, f'{time.time() - t0:.0f}s', flush=True)

    for li, path in enumerate(sorted(glob.glob(os.path.join(VOY, 'data', 'external', 'bible', '*.txt')))):
        lang = os.path.basename(path)[:-4]; ws = read_words(path); ch = [ws[i:i + N] for i in range(0, len(ws) - N + 1, N)]
        for i in range(min(4, len(ch))):
            add('natural', 'plain', lang, i, ch[i])
        for j, (name, fn) in enumerate(CIPHERS.items()):
            add('cipher', name, lang, 0, fn(ch[(4 + j) % len(ch)] + ch[(5 + j) % len(ch)], random.Random(1000 * li + j)))
        for j, (name, fn) in enumerate(GENS.items()):
            add('generated', name, lang, 0, fn(ch[(j + li) % len(ch)], random.Random(5000 * li + j)))
    extra = sorted(glob.glob(os.path.join(VOY, '..', '..', 'lang', 'corpora', '*.txt')))
    for path in extra:
        name = os.path.basename(path)[:-4]; ws = read_words(path)[2000:]
        for i in range(4 if name == 'la-gutenberg' else 1):
            add('natural', 'plain', 'gutenberg:' + name, i, ws[i * 5 * N:i * 5 * N + N])
    for path in sorted(glob.glob(os.path.join(VOY, 'data', 'external', 'cremma', '*.tsv'))):
        ws = [w for r in csv.DictReader(open(path, encoding='utf-8'), delimiter='\t') if r['block_type'].startswith('MainZone') and r['line_type'] == 'DefaultLine'
              for w in WORD.findall(r['text'].lower())]
        for i in range(min(2, len(ws) // N)):
            add('natural', 'plain', 'manuscript:' + os.path.basename(path)[:-4].split('__')[1], i, ws[i * N:(i + 1) * N])
    for s in range(40):
        add('generated', 'table', f'table{s}', 0, table(random.Random(70 + s)))
        add('generated', 'selfcite', f'selfcite{s}', 0, selfcite(random.Random(170 + s)))
    # ---- held out: Voynich-like texts and Voynich
    import common, a4_selfcitation as a4, b3_bakeoff as b3
    ref = common.pages(); flat = [w for p in ref for ln in p['lines'] for w in ln['words']]
    def units(ws):
        return pack([common.units(w) for w in ws])
    for s in (19, 7, 3, 11, 23, 5):
        ac = [w for p in a4.Autocopist(s).generate(a4.skeleton(ref)) for ln in p['lines'] for w in ln['words']]
        add('mimic', 'autocopist', f'autocopist_s{s}', 0, units(ac))
    for name, path in (('rugg', 'rugg.txt'), ('naibbe', 'naibbe.txt')):
        ws = open(os.path.join(VOY, 'tfm', 'data', path), encoding='utf-8').read().split()
        for i in range(min(4, len(ws) // N)):
            add('mimic', name, name, i, units(ws[i * N:(i + 1) * N]))
    gib, _ = b3.load_gibberish()
    for i in range(min(4, len(gib) // N)):
        add('mimic', 'volunteers', 'volunteers', i, gib[i * N:(i + 1) * N])
    try:
        import slots8
        for s in (19, 7):
            g = [w for p in slots8.generate('lang8', ref, s)[0] for ln in p['lines'] for w in ln['words']]
            for i in range(2):
                add('mimic', 'lang8', f'lang8_s{s}', i, units(g[i * 3 * N:i * 3 * N + N]))
    except Exception as e:
        print('lang8 skipped:', e, flush=True)
    for i in range(len(flat) // N):
        add('voynich', 'ZL units', 'voynich', i, units(flat[i * N:(i + 1) * N]))
        add('voynich', 'ZL EVA characters', 'voynich', i, flat[i * N:(i + 1) * N])
    common.TSV = os.path.join(VOY, 'data', 'IT2a-n.words.tsv')
    if os.path.exists(common.TSV):
        it = [w for p in common.pages() for ln in p['lines'] for w in ln['words']]
        for i in range(len(it) // N):
            add('voynich', 'IT units', 'voynich', i, units(it[i * N:(i + 1) * N]))
    keys = list(rows[0])
    with open(os.path.join(HERE, 'features.csv'), 'w', encoding='utf-8', newline='') as o:
        w = csv.DictWriter(o, keys); w.writeheader(); w.writerows(rows)
    c = collections.Counter((r['kind'], r['process']) for r in rows)
    print(len(rows), 'chunks;', dict(c)); print(f'runtime {time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
