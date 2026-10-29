"""How solid is the between-scribe ratio of gibberish.py? Matched documents and bootstrap intervals.

gibberish.py drew a gibberish volunteer's 'within' samples from one short text but Voynich's from a scribe's whole
output (several sections and pages), which inflates Voynich's within-scribe spread. Here every text is cut into
documents of 200 consecutive words (gibberish: each volunteer's first 200 words; Voynich: each Davis hand's paragraph
text in manuscript order; Auchinleck: each scribe's text in manuscript order). For each document: within = JSD of its
two 100-word halves (random split). Between documents: JSD of 100 random words of one against 100 of the other,
for pairs of the same scribe and of different scribes. Ratios = mean between / mean within.
Uncertainty: bootstrap over documents (1,000 resamples; for between-scribe pairs, resampling scribes as well, since
Voynich has only three) gives 95% intervals.

Run from the repository root: python targets/voynich/meaning/scribe_ratio.py
"""
import collections, csv, itertools, json, os, random, re, statistics, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'glyphs'))
from variants import UNIT
from variance import jsd
import auchinleck

DOC, HALF, BOOT = 200, 100, 1000


def pairs(words, split):
    c = collections.Counter()
    for w in words:
        u = ['#'] + split(w) + ['#']; c.update(zip(u, u[1:]))
    return c


def docs_of(groups):
    return [(s, ws[k:k + DOC]) for s, ws in groups.items() for k in range(0, len(ws) - DOC + 1, DOC)]


def analyse(name, docs, split, rng, max_pairs=3000):
    within = []
    for s, d in docs:
        w = d[:]; rng.shuffle(w); within.append(jsd(pairs(w[:HALF], split), pairs(w[HALF:], split)))
    idx = list(range(len(docs)))
    allp = list(itertools.combinations(idx, 2)); rng.shuffle(allp)
    same = [(i, j) for i, j in allp if docs[i][0] == docs[j][0]][:max_pairs]
    diff = [(i, j) for i, j in allp if docs[i][0] != docs[j][0]][:max_pairs]
    def pj(i, j): return jsd(pairs(rng.sample(docs[i][1], HALF), split), pairs(rng.sample(docs[j][1], HALF), split))
    S = {p: pj(*p) for p in same}; D = {p: pj(*p) for p in diff}
    scribes = sorted({s for s, _ in docs})
    def stat(doc_set, scr_set):
        ds = set(doc_set); W = [within[i] for i in doc_set]
        sv = [v for (i, j), v in S.items() if i in ds and j in ds]
        dv = [v for (i, j), v in D.items() if i in ds and j in ds and docs[i][0] in scr_set and docs[j][0] in scr_set]
        w = statistics.mean(W)
        return (statistics.mean(dv) / w if dv else float('nan')), (statistics.mean(sv) / w if sv else float('nan'))
    obs_d, obs_s = stat(idx, set(scribes))
    bd, bs = [], []
    for _ in range(BOOT):
        scr = set(rng.choices(scribes, k=len(scribes)))
        pool = [i for i in idx if docs[i][0] in scr]
        if len(pool) < 4: continue
        ds = rng.choices(pool, k=len(pool))
        d, s = stat(sorted(set(ds)), scr)
        if d == d: bd.append(d)
        if s == s: bs.append(s)
    ci = lambda v: (sorted(v)[int(0.025 * len(v))], sorted(v)[int(0.975 * len(v)) - 1]) if v else (float('nan'),) * 2
    lo, hi = ci(bd); slo, shi = ci(bs)
    print(f'{name:36} scribes {len(scribes):2}, docs {len(docs):4} | within {statistics.mean(within):.4f} | '
          f'between scribes / within {obs_d:.2f} [{lo:.2f}-{hi:.2f}] | same scribe, other doc / within '
          + (f'{obs_s:.2f} [{slo:.2f}-{shi:.2f}]' if obs_s == obs_s else 'n/a (one doc per scribe)'), flush=True)
    return {'between_ratio': obs_d, 'ci': (lo, hi), 'same_ratio': obs_s, 'same_ci': (slo, shi), 'docs': len(docs), 'scribes': len(scribes)}


def main():
    rng = random.Random(17)
    z = zipfile.ZipFile(os.path.join(HERE, 'data', 'gaskell_bowern', 'gibberish_transcriptions.zip'))
    gib = {n: re.findall(r'[a-z]+', z.read(n).decode('utf-8', 'replace').lower())[:DOC] for n in z.namelist() if not n.endswith('/')}
    gib = {k: v for k, v in gib.items() if len(v) == DOC}
    voy = collections.defaultdict(list)
    for r in csv.DictReader(open(os.path.join(HERE, '..', 'data', 'ZL3b-n.fixed.words.tsv'), encoding='utf-8'), delimiter='\t'):
        if r['locus_type'] == 'P' and r['hand'] in ('1', '2', '3', '4', '5'):
            voy[r['hand']] += [w for w in r['line_words'].split() if re.fullmatch(r'[a-z]+', w)]
    au = collections.defaultdict(list)
    for it in json.load(open(os.path.join(auchinleck.RAW, 'items.json'))):
        if it['scribe']: au[it['scribe']] += auchinleck.text_of(os.path.join(auchinleck.RAW, os.path.basename(it['page'])))
    out = {'voynich': analyse('Voynich, Davis hands 1-5', docs_of(voy), UNIT.findall, rng),
           'auchinleck': analyse('Auchinleck, scribes 1, 2, 3, 5', docs_of(au), list, rng),
           'gibberish': analyse('Gibberish volunteers (200 words each)', docs_of(gib), list, rng)}
    json.dump(out, open(os.path.join(HERE, 'scribe_ratio_results.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
