"""Phase 2, second round: generators with word-order structure, and candidate processes for the word-internal
oddities. (12 Nov 2026)

Round 1 (build.py, model.py) failed its checks because every generator but one drew its words independently, so the
classifiers learnt 'word order has structure = a language underneath'. Added here, same chunk size and features:
  generated, with sequential structure and no message
    wordchain    a word-bigram chain fitted to a language: locally grammatical nonsense
    blockshuffle the words of a language shuffled inside blocks of 200: topics kept, syntax destroyed
    selfcite2    copying generator with other settings than round 1's (window 100, copy 0.8, edit 0.3, a fresh
                 start every 500 words)
    chain        invented word parts (15 openers, 40 middles, 12 endings); the opener depends on the previous
                 word's ending, the middle on the opener, the ending on the middle (sparse random tables)
    topic        the table generator with its column weights re-drawn every 300 words
  cipher (a language underneath), candidates for what round 1 found unlike any language inside the word
    abbrev       scribal abbreviation, language-free version: the 10 commonest words become single signs, the 8
                 commonest word endings (2-3 letters) and the 4 commonest word beginnings (2-3 letters) become
                 single marks
    posverbose   a verbose cipher whose glyph groups differ by position in the word (initial, medial, final)
    taxonomic    a constructed-language codebook: every word type becomes genus syllable + difference consonant +
                 species vowel (assigned in frequency order), plus one of 6 endings chosen by the last letter of
                 the original word
  other (not used in training; for oddities.py only)
    numerals     Roman numerals of numbers drawn with small numbers commoner

Run from targets/voynich: python phase2/build2.py -> phase2/features2.csv (about 10 minutes)
"""
import collections, csv, glob, os, random, sys, time, zlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build
from build import N, sym, invented, syllable, CONS, VOW, read_words
from features import features


def wordchain(ws, rng):
    nxt = collections.defaultdict(list)
    for a, b in zip(ws, ws[1:]):
        nxt[a].append(b)
    out = [rng.choice(ws)]
    while len(out) < N:
        f = nxt.get(out[-1]); out.append(rng.choice(f) if f else rng.choice(ws))
    return out


def blockshuffle(ws, rng):
    out = []
    for i in range(0, len(ws), 200):
        b = ws[i:i + 200]; rng.shuffle(b); out += b
    return out


def selfcite2(rng):
    out = []
    while len(out) < N:
        page = [invented(rng) for _ in range(8)]
        while len(page) < 500:
            if rng.random() < 0.8:
                w = rng.choice(page[-100:])
                if rng.random() < 0.3:
                    i = rng.randrange(len(w)); w = w[:i] + rng.choice(CONS + VOW) + w[i + 1:]
            else:
                w = invented(rng)
            page.append(w)
        out += page
    return out


def chain(rng):
    op = [''] + [rng.choice(CONS) + rng.choice(('', rng.choice(VOW))) for _ in range(14)]; mid = [syllable(rng) for _ in range(40)]
    en = [rng.choice(VOW) + rng.choice(('', 'n', 'r', 's', 'l')) for _ in range(12)]
    def tab(n, m):
        return [[rng.gammavariate(0.3, 1) for _ in range(m)] for _ in range(n)]
    t_op = tab(len(en) + 1, len(op)); t_mid = tab(len(op), len(mid)); t_en = tab(len(mid), len(en)); out = []; prev = len(en)
    while len(out) < N:
        o = rng.choices(range(len(op)), t_op[prev])[0]; m = rng.choices(range(len(mid)), t_mid[o])[0]; e = rng.choices(range(len(en)), t_en[m])[0]
        out.append(op[o] + mid[m] + en[e]); prev = e
    return out


def topic(rng):
    cols = [[invented(rng, 1) if rng.random() < 0.8 else '' for _ in range(n)] for n in (12, 20, 12)]; out = []
    while len(out) < N:
        wts = [[rng.gammavariate(0.5, 1) for _ in c] for c in cols]
        for _ in range(300):
            w = ''.join(rng.choices(c, wt)[0] for c, wt in zip(cols, wts))
            if w:
                out.append(w)
    return out


def abbrev(ws, rng):
    cnt = collections.Counter(ws); whole = {w: sym(500 + i) for i, (w, _) in enumerate(cnt.most_common(10))}
    def common(part, k):
        c = collections.Counter(part(w, n) for w in ws if len(w) >= 5 and w not in whole for n in (2, 3))
        out = []
        for s, _ in c.most_common():
            if not any(s.endswith(x) or x.endswith(s) or s.startswith(x) or x.startswith(s) for x in out):
                out.append(s)
            if len(out) == k:
                break
        return out
    ends = {s: sym(520 + i) for i, s in enumerate(common(lambda w, n: w[-n:], 8))}; begs = {s: sym(540 + i) for i, s in enumerate(common(lambda w, n: w[:n], 4))}
    out = []
    for w in ws:
        if w in whole:
            out.append(whole[w]); continue
        if len(w) >= 5:
            for n in (3, 2):
                if w[-n:] in ends:
                    w = w[:-n] + ends[w[-n:]]; break
            for n in (3, 2):
                if w[:n] in begs:
                    w = begs[w[:n]] + w[n:]; break
        out.append(w)
    return out


def posverbose(ws, rng):
    letters = sorted({c for w in ws for c in w}); m = {}; used = set()
    for pos in range(3):
        for c in letters:
            tries = 0
            while True:
                tries += 1   # longer groups once the short ones run out (scripts with hundreds of characters)
                g = ''.join(sym(pos * 12 + rng.randrange(12)) for _ in range(rng.choices((1, 2), (0.5, 0.5))[0] + tries // 20))
                if g not in used:
                    used.add(g); m[(pos, c)] = g; break
    return [''.join(m[(0 if i == 0 else 2 if i == len(w) - 1 else 1, c)] for i, c in enumerate(w)) for w in ws]


def taxonomic(ws, rng):
    cnt = collections.Counter(ws); gen = [c + v for c in CONS for v in VOW]; rng.shuffle(gen)
    lastc = sorted({w[-1] for w in ws}); endmap = {c: 'aeious'[i % 6] for i, c in enumerate(lastc)}; m = {}
    for r, (w, _) in enumerate(cnt.most_common()):
        g = gen[(r // 60) % len(gen)]; d = 'ptkbdgmnslrf'[(r // 5) % 12]; s = VOW[r % 5]
        m[w] = g + d + s + endmap[w[-1]] + ('' if r < 60 * len(gen) else syllable(rng))
    return [m[w] for w in ws]


def roman(n):
    out = ''
    for v, s in ((1000, 'm'), (900, 'cm'), (500, 'd'), (400, 'cd'), (100, 'c'), (90, 'xc'), (50, 'l'), (40, 'xl'), (10, 'x'), (9, 'ix'), (5, 'v'), (4, 'iv'), (1, 'i')):
        while n >= v:
            out += s; n -= v
    return out


def numerals(rng):
    return [roman(min(3999, int(rng.paretovariate(0.7)))) for _ in range(N)]


LANG_GEN = collections.OrderedDict(wordchain=wordchain, blockshuffle=blockshuffle)
LANG_CIPH = collections.OrderedDict(abbrev=abbrev, posverbose=posverbose, taxonomic=taxonomic)
FREE = collections.OrderedDict(selfcite2=selfcite2, chain=chain, topic=topic)


def main():
    t0 = time.time(); rows = []

    def add(kind, process, source, chunk, ws):
        ws = [w for w in ws if w][:N]
        if len(ws) < N:
            return
        f = features(ws, random.Random(zlib.crc32(f'{process}|{source}|{chunk}'.encode()) % 10 ** 6)); rows.append(dict(kind=kind, process=process, source=source, chunk=chunk, **f))
        print(len(rows), kind, process, source, f'{time.time() - t0:.0f}s', flush=True)

    for li, path in enumerate(sorted(glob.glob(os.path.join(build.VOY, 'data', 'external', 'bible', '*.txt')))):
        lang = os.path.basename(path)[:-4]; ws = read_words(path); ch = [ws[i:i + N] for i in range(0, len(ws) - N + 1, N)]
        print('start', lang, flush=True)
        add('generated', 'wordchain', lang, 0, wordchain(ws, random.Random(9000 + li)))
        add('generated', 'blockshuffle', lang, 0, blockshuffle(ch[(li + 2) % len(ch)][:], random.Random(9500 + li)))
        for j, (name, fn) in enumerate(LANG_CIPH.items()):
            add('cipher', name, lang, 0, fn(ch[(6 + j) % len(ch)], random.Random(12000 + 10 * li + j)))
    for s in range(40):
        for j, (name, fn) in enumerate(FREE.items()):
            add('generated', name, f'{name}{s}', 0, fn(random.Random(20000 + 100 * j + s)))
    for s in range(10):
        add('other', 'numerals', f'numerals{s}', 0, numerals(random.Random(30000 + s)))
    with open(os.path.join(HERE, 'features2.csv'), 'w', encoding='utf-8', newline='') as o:
        w = csv.DictWriter(o, list(rows[0])); w.writeheader(); w.writerows(rows)
    print(len(rows), 'chunks;', dict(collections.Counter((r['kind'], r['process']) for r in rows))); print(f'runtime {time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
