"""Taxonomic-language test on Voynich labels: do label words in the same section (or on the same page) share
their beginnings more than labels from other sections written by the same scribe?

A Wilkins-style a priori language builds words from category parts, so names of similar things share prefixes.
Natural-language or enciphered names do not, beyond what the scribe's dialect imposes. Hand is held fixed (pairs
are compared only within one hand), because Currier language follows the hand.

Statistic for a grouping G (section, or folio within section):
    D = P(same prefix | same G, same hand) - P(same prefix | different G, same hand)
Null: G shuffled among the words of each hand, sizes kept (N_PERM permutations). Same statistic on paragraph
words of the same hands as a baseline for general section vocabulary, and a power check with synthetic
category prefixes injected into the real labels.

Run: python -I research/voynich_siblings/label_prefix_test.py [--with-paragraphs]   (from the repository root;
the paragraph baseline takes about 10 minutes)
"""
import collections, csv, os, random, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, '..', '..', 'targets', 'voynich', 'data', 'ZL3b-n.words.tsv')
N_PERM = 2000
SEED = 1
SECTION = {'H': 'herbal', 'P': 'pharma', 'A': 'astro', 'C': 'cosmo', 'Z': 'zodiac', 'B': 'bio', 'T': 'text', 'S': 'stars'}
GLYPHS = ['cth', 'ckh', 'cph', 'cfh', 'ch', 'sh', 'qo']  # multi-letter EVA units counted as one at word start


def glyphs(w):
    out, i = [], 0
    while i < len(w):
        for g in GLYPHS:
            if w.startswith(g, i):
                out.append(g); i += len(g); break
        else:
            out.append(w[i]); i += 1
    return out


def prefix(w, kind):
    if kind == 'eva2':
        return w[:2]
    if kind == 'eva3':
        return w[:3]
    return ''.join(glyphs(w)[:2])  # 'gly2': first two glyph units


def load():
    rows = list(csv.DictReader(open(TSV, encoding='utf-8'), delimiter='\t'))
    lab, par = [], []
    for r in rows:
        for w in r['line_words'].split():
            if '@' in w or '?' in w or len(w) < 3 or not re.fullmatch(r'[a-z]+', w):
                continue
            rec = (w, r['hand'], r['illus'], r['folio'])
            if r['locus_type'] == 'L':
                lab.append(rec)
            elif r['locus_type'] == 'P':
                par.append(rec)
    return lab, par


def stat(words, kind, group_of):
    """D over all same-hand pairs."""
    byhand = collections.defaultdict(list)
    for w in words:
        byhand[w[1]].append(w)
    s_same = n_same = s_diff = n_diff = 0
    for ws in byhand.values():
        # count by (group, prefix) to avoid O(n^2) on paragraph words
        gp = collections.Counter((group_of(w), prefix(w[0], kind)) for w in ws)
        g = collections.Counter(group_of(w) for w in ws)
        p = collections.Counter(prefix(w[0], kind) for w in ws)
        n = len(ws)
        same_pairs = sum(c * (c - 1) for c in g.values())
        same_pre_same_g = sum(c * (c - 1) for c in gp.values())
        all_pre = sum(c * (c - 1) for c in p.values())
        s_same += same_pre_same_g; n_same += same_pairs
        s_diff += all_pre - same_pre_same_g; n_diff += n * (n - 1) - same_pairs
    if not n_same or not n_diff:
        return None
    return s_same / n_same - s_diff / n_diff


def perm_test(words, kind, key):
    """key(w) gives the group; shuffle groups within hand."""
    rng = random.Random(SEED)
    obs = stat(words, kind, key)
    byhand = collections.defaultdict(list)
    for i, w in enumerate(words):
        byhand[w[1]].append(i)
    groups = [key(w) for w in words]
    ge = 0
    null = []
    for _ in range(N_PERM):
        g2 = groups[:]
        for idx in byhand.values():
            vals = [g2[i] for i in idx]
            rng.shuffle(vals)
            for i, v in zip(idx, vals):
                g2[i] = v
        lookup = {id(w): g2[i] for i, w in enumerate(words)}
        d = stat(words, kind, lambda w: lookup[id(w)])
        null.append(d)
        ge += d >= obs
    mu = sum(null) / len(null)
    sd = (sum((x - mu) ** 2 for x in null) / len(null)) ** 0.5
    return obs, mu, sd, (ge + 1) / (N_PERM + 1)


def inject(words, rate, rng):
    """Power check: with probability `rate`, replace a label's first two glyph units by a section-specific pair."""
    tag = {}
    pool = ['qok', 'chol', 'shed', 'oka', 'ota', 'dai', 'ykc', 'olk']
    out = []
    for w, h, s, f in words:
        if s not in tag:
            tag[s] = pool[len(tag) % len(pool)]
        if rng.random() < rate:
            w = tag[s] + ''.join(glyphs(w)[2:])
        out.append((w, h, s, f))
    return out


def main():
    lab, par = load()
    multi = {h for h, n in collections.Counter((w[1], w[2]) for w in lab).items()}
    hands_multi = {h for h in {w[1] for w in lab} if len({s for (hh, s) in multi if hh == h}) > 1}
    print(f'labels kept: {len(lab)} words; paragraph words: {len(par)}')
    print('label words by hand and section:', dict(sorted(collections.Counter((w[1], SECTION.get(w[2], w[2])) for w in lab).items())))
    print('hands with labels in more than one section:', sorted(hands_multi))
    lab_m = [w for w in lab if w[1] in hands_multi]
    par_m = [w for w in par if w[1] in hands_multi]
    print()
    for kind in ['eva2', 'eva3', 'gly2']:
        print(f'== prefix = {kind}')
        sets = [('labels', lab_m)] + ([('paragraph words (same hands)', par_m)] if '--with-paragraphs' in sys.argv else [])
        for name, words in sets:
            obs, mu, sd, p = perm_test(words, kind, lambda w: w[2])
            z = (obs - mu) / sd if sd else float('nan')
            print(f'  section, {name:30s} D = {obs:+.4f}  null {mu:+.4f} +- {sd:.4f}  z = {z:5.1f}  p = {p:.4f}')
        obs, mu, sd, p = perm_test(lab, kind, lambda w: (w[2], w[3]))
        z = (obs - mu) / sd if sd else float('nan')
        print(f'  page (folio), labels, all hands        D = {obs:+.4f}  null {mu:+.4f} +- {sd:.4f}  z = {z:5.1f}  p = {p:.4f}')
    print()
    print('== power check (section prefix injected into a share of the real labels; gly2)')
    rng = random.Random(SEED)
    for rate in [0.1, 0.2, 0.3, 0.5]:
        obs, mu, sd, p = perm_test(inject(lab_m, rate, rng), 'gly2', lambda w: w[2])
        print(f'  injected {rate:.0%}: D = {obs:+.4f}  z = {(obs - mu) / sd:5.1f}  p = {p:.4f}')


if __name__ == '__main__':
    main()
