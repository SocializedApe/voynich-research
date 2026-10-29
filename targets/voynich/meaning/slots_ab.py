"""Which slot of the Voynich word carries the A/B difference? prefix + gallows + middle + ending.

Protocol, fixed before any run (28 Oct 2026):
  Parse (EVA, ZL fixed parse, paragraph text), in this order:
    ending  = the longest of ENDINGS that ends the word (the whole word if it is one of them; '' if none)
    prefix  = qo, q, o, y, d, s (not before h), l or r at the start of the rest ('' if none)
    gallows = cth, ckh, cph, cfh, k, t, p or f at the start of what remains ('-' if none)
    middle  = whatever remains ('' if nothing)
  Measure, per slot: I(slot value; label) in bits, from tokens, with labels balanced by subsampling to the smaller
  class (40 draws). Null: labels permuted between folios (folio clustering kept), 200 permutations. Reported:
  excess = I - mean null, z = excess / sd null, and excess as a share of the slot's entropy. Also I(whole word; label)
  with the same null, for scale.
  Contrasts: Currier A vs B (all hands); hand 2 vs hand 3 (B pages); quire, among hand-2 B pages (quires with >= 500
  tokens). For A vs B, the five values per slot with the largest contribution to I, with their A and B shares.
  Read: a slot whose excess is near zero is shared; a convention layer would show as excess concentrated in one or
  two slots.

Run from the repository root: python targets/voynich/meaning/slots_ab.py
"""
import collections, csv, json, math, os, random, re, statistics
HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, '..', 'data', 'ZL3b-n.fixed.words.tsv')
ENDINGS = ['aiin', 'aiir', 'ain', 'air', 'iin', 'iir', 'in', 'ir', 'eedy', 'edy', 'dy', 'eey', 'ey', 'y', 'ol', 'al',
           'or', 'ar', 'am', 'om', 'an', 'l', 'r', 's', 'm', 'n', 'd', 'o', 'e']
GALLOWS = ['cth', 'ckh', 'cph', 'cfh', 'k', 't', 'p', 'f']
SLOTS = ('prefix', 'gallows', 'middle', 'ending')


def parse(w):
    end = ''
    for e in sorted(ENDINGS, key=len, reverse=True):
        if w.endswith(e):
            end = e; break
    rest = w[:len(w) - len(end)]
    m = re.match(r'(qo|q|o|y|d|s(?!h)|l|r)', rest)
    pre = m.group(1) if m else ''; rest = rest[len(pre):]
    gal = next((g for g in GALLOWS if rest.startswith(g)), '-'); rest = rest[len(gal):] if gal != '-' else rest
    return {'prefix': pre, 'gallows': gal, 'middle': rest, 'ending': end, 'word': w}


def mi(tokens, key):
    """tokens: list of (label, parsed); I(value; label) in bits."""
    j = collections.Counter((l, p[key]) for l, p in tokens); n = len(tokens)
    pl = collections.Counter(l for l, _ in tokens); pv = collections.Counter(p[key] for _, p in tokens)
    return sum(c / n * math.log2(c * n / (pl[l] * pv[v])) for (l, v), c in j.items())


def H(tokens, key):
    c = collections.Counter(p[key] for _, p in tokens); n = len(tokens)
    return -sum(x / n * math.log2(x / n) for x in c.values())


def contrast(name, folios, rng, draws=40, perms=200):
    """folios: list of (label, [parsed tokens]). Balanced by subsampling folios' tokens to the smaller class."""
    by = collections.defaultdict(list)
    for l, toks in folios:
        by[l] += [(l, t) for t in toks]
    m = min(len(v) for v in by.values())
    def balanced(fol):
        pool = collections.defaultdict(list)
        for l, toks in fol:
            pool[l] += [(l, t) for t in toks]
        return [x for l in pool for x in rng.sample(pool[l], min(m, len(pool[l])))]
    out = {}
    for key in SLOTS + ('word',):
        real = statistics.mean(mi(balanced(folios), key) for _ in range(draws))
        labels = [l for l, _ in folios]; null = []
        for _ in range(perms):
            rng.shuffle(labels); null.append(mi(balanced(list(zip(labels, [t for _, t in folios]))), key))
        mu, sd = statistics.mean(null), statistics.pstdev(null)
        h = H([(None, t) for _, ts in folios for t in ts], key)
        out[key] = {'I': real, 'null': mu, 'excess': real - mu, 'z': (real - mu) / sd if sd else float('nan'), 'H': h, 'share': (real - mu) / h if h else 0}
    print(f'\n{name}: classes {dict((l, len(v)) for l, v in by.items())} tokens, balanced to {m} each')
    print('| slot | I (bits) | null | excess | z | excess / H(slot) |'); print('|---|---|---|---|---|---|')
    for key, r in out.items():
        print(f"| {key} | {r['I']:.4f} | {r['null']:.4f} | {r['excess']:.4f} | {r['z']:.1f} | {100 * r['share']:.1f}% |")
    return out


def top_values(folios, key, k=5):
    c = {l: collections.Counter() for l in ('A', 'B')}
    for l, ts in folios:
        c[l].update(t[key] for t in ts)
    nA, nB = sum(c['A'].values()), sum(c['B'].values())
    rows = []
    for v in set(c['A']) | set(c['B']):
        a, b = c['A'][v] / nA, c['B'][v] / nB; m = (a + b) / 2
        contrib = sum(x / 2 * math.log2(x / m) for x in (a, b) if x)
        rows.append((contrib, v, a, b))
    rows.sort(reverse=True)
    return [(v or "''", round(a, 3), round(b, 3)) for _, v, a, b in rows[:k]]


def main():
    rng = random.Random(29)
    fol = collections.OrderedDict(); meta = {}
    for r in csv.DictReader(open(TSV, encoding='utf-8'), delimiter='\t'):
        if r['locus_type'] != 'P':
            continue
        ws = [w for w in r['line_words'].split() if re.fullmatch(r'[a-z]+', w)]
        fol.setdefault(r['folio'], []).extend(parse(w) for w in ws)
        meta.setdefault(r['folio'], collections.Counter())[(r['lang'], r['hand'], r['quire'])] += len(ws)
    lab = {f: m.most_common(1)[0][0] for f, m in meta.items()}
    toks = [t for ts in fol.values() for t in ts]
    print('parse: share of tokens with each slot filled:', {s: round(sum(1 for t in toks if t[s] not in ('', '-')) / len(toks), 3) for s in SLOTS})
    print('commonest middles:', collections.Counter(t['middle'] for t in toks).most_common(12))
    R = {}
    ab = [(lab[f][0], ts) for f, ts in fol.items() if lab[f][0] in ('A', 'B')]
    R['A_vs_B'] = contrast('Currier A vs B', ab, rng)
    R['A_vs_B_top'] = {s: top_values(ab, s) for s in SLOTS}
    for s in SLOTS:
        print(f'  {s:8s} largest A/B shifts (value, share in A, share in B):', R['A_vs_B_top'][s])
    h23 = [(lab[f][1], ts) for f, ts in fol.items() if lab[f][0] == 'B' and lab[f][1] in ('2', '3')]
    R['hand2_vs_hand3_B'] = contrast('Hand 2 vs hand 3, B pages', h23, rng)
    q = collections.Counter()
    for f, ts in fol.items():
        if lab[f][0] == 'B' and lab[f][1] == '2':
            q[lab[f][2]] += len(ts)
    qs = {k for k, v in q.items() if v >= 500}
    qq = [(lab[f][2], ts) for f, ts in fol.items() if lab[f][0] == 'B' and lab[f][1] == '2' and lab[f][2] in qs]
    R['quire_hand2_B'] = contrast(f'Quire among hand-2 B pages ({sorted(qs)})', qq, rng)
    json.dump(R, open(os.path.join(HERE, 'slots_ab_results.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
