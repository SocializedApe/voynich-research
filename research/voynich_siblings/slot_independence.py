"""How much does the beginning of a word predict its end? Voynich against Latin, German and English.

A wheel/volvelle word-maker (Fontana's *Speculum*, c. 1430: five alphabet wheels turned independently) sets each
slot separately, so a word's opening and ending should be close to independent once word length is fixed. Natural
language and copy-and-modify text tie them together.

Statistic: I(prefix; suffix | length), prefix and suffix = first and last k units (k = 1, 2), for word *tokens* of
4-8 units. Bias removed by subtracting the same quantity with suffixes shuffled among words of equal length (the
"independent" value). Reported normalised by min(H(prefix|L), H(suffix|L)). Units: letters for the languages; for
Voynich both raw EVA letters and glyph units (ch, sh, cth, ckh, cph, cfh, qo, ee, ii, aiin/ain/iin as one).
Samples cut to the same number of tokens.

Run from the repository root: python -I research/voynich_siblings/slot_independence.py
"""
import collections, csv, math, os, random, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..')
TSV = os.path.join(ROOT, 'targets', 'voynich', 'data', 'ZL3b-n.words.tsv')
CORP = {'Latin': 'la-gutenberg.txt', 'German 1470-1610': 'de-dta-1470-1610.txt', 'English': 'en-gutenberg.txt'}
N_TOK = 30000
SEED = 5
UNITS = ['aiin', 'ain', 'iin', 'cth', 'ckh', 'cph', 'cfh', 'ch', 'sh', 'qo', 'ee', 'ii']


def eva_units(w):
    out, i = [], 0
    while i < len(w):
        for u in UNITS:
            if w.startswith(u, i):
                out.append(u); i += len(u); break
        else:
            out.append(w[i]); i += 1
    return out


def voynich(lang=None):
    toks = []
    for r in csv.DictReader(open(TSV, encoding='utf-8'), delimiter='\t'):
        if r['locus_type'] != 'P' or (lang and r['lang'] != lang):
            continue
        toks += [w for w in r['line_words'].split() if re.fullmatch(r'[a-z]+', w)]
    return toks


def corpus(name):
    t = open(os.path.join(ROOT, 'lang', 'corpora', CORP[name]), encoding='utf-8', errors='replace').read().lower()
    t = t[len(t) // 10: len(t) // 10 + 3_000_000]  # skip front matter
    return re.findall(r'[a-z]+', t.replace('ſ', 's'))


def H(counter):
    n = sum(counter.values())
    return -sum(c / n * math.log2(c / n) for c in counter.values() if c)


def cond_mi(pairs):
    """pairs: list of (L, pre, suf). Returns I(pre;suf|L), H(pre|L), H(suf|L)."""
    byL = collections.defaultdict(list)
    for L, p, s in pairs:
        byL[L].append((p, s))
    n = len(pairs); I = hp = hs = 0.0
    for L, ps in byL.items():
        w = len(ps) / n
        cp = collections.Counter(p for p, _ in ps); cs = collections.Counter(s for _, s in ps)
        cj = collections.Counter(ps)
        I += w * (H(cp) + H(cs) - H(cj)); hp += w * H(cp); hs += w * H(cs)
    return I, hp, hs


def measure(units_list, k, rng, reps=20):
    pairs = [(len(u), tuple(u[:k]), tuple(u[-k:])) for u in units_list if 4 <= len(u) <= 8]
    I, hp, hs = cond_mi(pairs)
    shuf = []
    for _ in range(reps):
        byL = collections.defaultdict(list)
        for i, (L, p, s) in enumerate(pairs):
            byL[L].append(i)
        sufs = [s for _, _, s in pairs]
        for idx in byL.values():
            v = [sufs[i] for i in idx]; rng.shuffle(v)
            for i, x in zip(idx, v):
                sufs[i] = x
        shuf.append(cond_mi([(L, p, sufs[i]) for i, (L, p, _) in enumerate(pairs)])[0])
    base = sum(shuf) / len(shuf)
    return (I - base) / min(hp, hs), I - base, len(pairs)


def main():
    rng = random.Random(SEED)
    sets = []
    v = voynich(); rng.shuffle(v)
    sets.append(('Voynich all, EVA letters', [list(w) for w in v[:N_TOK]]))
    sets.append(('Voynich all, glyph units', [eva_units(w) for w in v[:N_TOK]]))
    for lang in 'AB':
        vv = voynich(lang); rng.shuffle(vv)
        sets.append((f'Voynich Currier {lang}, glyph units', [eva_units(w) for w in vv[:N_TOK]]))
    for name in CORP:
        c = corpus(name)
        start = rng.randrange(0, max(1, len(c) - N_TOK))
        sets.append((name, [list(w) for w in c[start:start + N_TOK]]))
    print(f'{"text":36s} {"k":>2s} {"tokens 4-8":>10s} {"I - I_indep (bits)":>18s} {"normalised":>10s}')
    for k in (1, 2):
        for name, ul in sets:
            nmi, d, n = measure(ul, k, rng)
            print(f'{name:36s} {k:2d} {n:10d} {d:18.4f} {nmi:10.4f}')


if __name__ == '__main__':
    main()
