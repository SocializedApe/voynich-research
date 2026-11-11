"""Near-copy geometry: where on the page does a word's near-copy sit? (10 Nov 2026)

Timm & Schinner's self-citation account has the scribe copying and modifying words he sees above or just before the
one he is writing. If so, a word's near-copy (another word on the same page at Levenshtein distance <= 1) should
sit preferentially in the line directly above, and at about the same horizontal position (the scribe's eye goes up,
not sideways). A cipher or a copy of running text has no reason to align words vertically: lines are arbitrary cuts.
The repository's autocopist (a4) copies from the same position in a previous line 28% of the time, so it is a
positive control for alignment; Latin, English, the Naibbe cipher and the gibberish volunteers (poured into the ZL
skeleton, so their original lines are lost) are negative controls.

For every page and every pair of lines (n - k, n), k = 1, 2, 3: every pair of tokens (a in line n - k, b in line n)
with ld1(a, b) <= 1 (a4.ld1; exact repeats also separately) gives one event with word positions (pa, pb).
  align1 = share of events with |pb - pa| <= 1;  same = share with pb == pa;  left = share with pa < pb.
Scopes: all positions; interior only (both words at index >= 2 and not the last word of their line, lines of >= 6
words), which removes the known line-initial and line-final vocabulary effects.
Two nulls, 20 draws each: A = words shuffled within each line (keeps every line's vocabulary and the event count,
destroys positions, including position-specific vocabulary); B = column shuffle, words at the same index swapped
among the lines of the page (keeps each position's page vocabulary and every line's length, destroys which line a
word is in). An excess over A that vanishes over B is position vocabulary (line-initial words resemble line-initial
words); an excess over B at k = 1 that is absent at k = 2, 3 is copying from the line directly above.
Also reported: where the nearest earlier near-copy (a4 definition) sits (same line / line above / 2 above / 3+),
observed against the within-page shuffle.

Run from targets/voynich: python lines/copy_geometry.py  -> lines/copy_geometry_results.json, lines/copy_geometry.md
"""
import collections, json, math, os, random, statistics, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import common, a4_selfcitation as a4

NULLS = 20


def shuffle_columns(pgs, seed):
    rng = random.Random(seed); out = []
    for p in pgs:
        q = dict(p); L = [ln['words'][:] for ln in p['lines']]
        maxlen = max((len(ws) for ws in L), default=0)
        for i in range(maxlen):
            idx = [n for n, ws in enumerate(L) if len(ws) > i]
            col = [L[n][i] for n in idx]; rng.shuffle(col)
            for n, w in zip(idx, col):
                L[n][i] = w
        q['lines'] = [{'words': ws, 'para_start': ln['para_start']} for ws, ln in zip(L, p['lines'])]
        out.append(q)
    return out


def events(pgs, k, exact=None, interior=False):
    """list of (pa, La, pb, Lb) for token pairs at LD<=1 (exact=None) or LD==0 (exact=True), lines n-k and n"""
    out = []
    for p in pgs:
        L = p['lines']
        for n in range(k, len(L)):
            A, B = L[n - k]['words'], L[n]['words']
            if len(A) < 2 or len(B) < 2 or (interior and (len(A) < 6 or len(B) < 6)):
                continue
            la = [len(w) for w in A]; lb = [len(w) for w in B]
            ra = range(2, len(A) - 1) if interior else range(len(A))
            rb = range(2, len(B) - 1) if interior else range(len(B))
            for j in rb:
                b = B[j]
                for i in ra:
                    if -1 <= la[i] - lb[j] <= 1:
                        d = a4.ld1(A[i], b)
                        if d <= 1 and (exact is None or d == 0):
                            out.append((i, len(A), j, len(B)))
    return out


def summarise(ev):
    n = len(ev)
    if n == 0:
        return dict(n=0, align1=None, same=None, left=None)
    return dict(n=n, align1=sum(1 for i, La, j, Lb in ev if abs(i - j) <= 1) / n,
                same=sum(1 for i, La, j, Lb in ev if i == j) / n, left=sum(1 for i, La, j, Lb in ev if i < j) / n)


def nearest_above(pgs):
    tot = 0; c = collections.Counter()
    for p in pgs:
        toks, lines = [], []
        for li, ln in enumerate(p['lines']):
            for w in ln['words']:
                toks.append(w); lines.append(li)
        lens = [len(t) for t in toks]
        for i, w in enumerate(toks):
            tot += 1
            j = i - 1
            while j >= 0:
                if -1 <= lens[j] - lens[i] <= 1 and a4.ld1(toks[j], w) <= 1:
                    d = lines[i] - lines[j]
                    c['same' if d == 0 else 'above1' if d == 1 else 'above2' if d == 2 else 'above3+'] += 1
                    break
                j -= 1
    return {k: v / tot for k, v in c.items()}, tot


def analyse(name, pgs):
    R = {}
    nullsA = [common.shuffle_within_line(pgs, seed=1000 * s + 17) for s in range(NULLS)]
    nullsB = [shuffle_columns(pgs, seed=1000 * s + 29) for s in range(NULLS)]
    for scope in ('all', 'interior'):
        for k in (1, 2, 3):
            for lab, ex in (('ld<=1', None), ('exact', True)):
                obs = summarise(events(pgs, k, ex, scope == 'interior'))
                row = dict(n=obs['n'])
                for nl, nulls in (('A', nullsA), ('B', nullsB)):
                    acc = collections.defaultdict(list)
                    for sh in nulls:
                        for key, v in summarise(events(sh, k, ex, scope == 'interior')).items():
                            if key != 'n' and v is not None:
                                acc[key].append(v)
                    for key in ('align1', 'same', 'left'):
                        if obs[key] is None or not acc[key]:
                            row[f'{key}_{nl}'] = None; continue
                        mu = statistics.mean(acc[key]); sd = statistics.pstdev(acc[key]) or 1e-9
                        row[f'{key}_{nl}'] = dict(obs=obs[key], null=mu, ratio=obs[key] / mu if mu else None, z=(obs[key] - mu) / sd)
                R[f'{scope}_k{k}_{lab}'] = row
    na, tot = nearest_above(pgs)
    nas, _ = nearest_above(a4.shuffle_within_page(pgs))
    R['nearest'] = dict(tokens=tot, obs=na, within_page_shuffle=nas)
    return R


def fmt(c):
    return '-' if c is None else f"{c['obs']:.3f} / {c['null']:.3f} / {c['ratio']:.2f} / {c['z']:+.1f}"


def main():
    t0 = time.time()
    voy = common.pages()
    texts = collections.OrderedDict(voynich=voy)
    texts['voynich_A'] = [p for p in voy if p['lang'] == 'A']
    texts['voynich_B'] = [p for p in voy if p['lang'] == 'B']
    for h in ('1', '2', '3'):
        texts[f'voynich_hand{h}'] = [p for p in voy if p['hand'] == h]
    texts.update(common.controls(voy))
    results = collections.OrderedDict()
    for name, pgs in texts.items():
        results[name] = analyse(name, pgs); print(name, 'done', f'{time.time() - t0:.0f}s', flush=True)
    json.dump(results, open(os.path.join(HERE, 'copy_geometry_results.json'), 'w'), indent=1)
    L = ['# Near-copy geometry: is the near-copy in the line above, at the same position? (10 Nov 2026)', '',
         'Script `copy_geometry.py` (docstring has the definitions). Cells: observed / null mean (20) / ratio / z.',
         'Null A = words shuffled within each line; null B = column shuffle (same index swapped among the lines of the page).',
         'align1 = |position difference| <= 1; same = identical word index; left = source left of target.', '']
    for scope in ('all', 'interior'):
        for lab in ('ld<=1', 'exact'):
            L.append(f'## {scope} positions, token pairs at {lab} between a line and the line k above'); L.append('')
            L.append('| text | k | events | align1 vs A | align1 vs B | same vs A | same vs B | left vs A |'); L.append('|---|---|---|---|---|---|---|---|')
            for name, R in results.items():
                for k in (1, 2, 3):
                    r = R[f'{scope}_k{k}_{lab}']
                    L.append(f"| {name} | {k} | {r['n']} | {fmt(r['align1_A'])} | {fmt(r['align1_B'])} | {fmt(r['same_A'])} | {fmt(r['same_B'])} | {fmt(r['left_A'])} |")
            L.append('')
    L.append('## Where the nearest earlier near-copy (a4 definition) sits, share of all tokens, observed (within-page shuffle)'); L.append('')
    L.append('| text | tokens | same line | line above | 2 above | 3+ above |'); L.append('|---|---|---|---|---|---|')
    for name, R in results.items():
        o, s = R['nearest']['obs'], R['nearest']['within_page_shuffle']
        cells = [f"{o.get(k, 0):.3f} ({s.get(k, 0):.3f})" for k in ('same', 'above1', 'above2', 'above3+')]
        L.append(f"| {name} | {R['nearest']['tokens']} | " + ' | '.join(cells) + ' |')
    L.append(''); L.append(f'Runtime {time.time() - t0:.0f} s.')
    open(os.path.join(HERE, 'copy_geometry.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
