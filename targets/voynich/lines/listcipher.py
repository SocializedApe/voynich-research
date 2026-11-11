"""Two ways a real text could still give the line structure: a list (one item per line), or a clerk who always
squeezes the last word in. (11 Nov 2026)

wrapping.py: the first word of a Voynich line is not an overflow word, so the lines were not cut from a stream of
ready words. Two escapes for a text with content:
(A) the plaintext is a list and every line is one item. Then line length is item length. Measured: the fill of a
    line (its length in characters over the paragraph's longest line) for Voynich lines that are not the last of
    their paragraph, against item lengths of real itemised text: Latin Vulgate verses (one verse = one item) and
    their clauses (split at , ; : .), each divided by the 95th percentile of its own lengths so that 'fill' means
    the same thing. Coefficient of variation, share of items under half and under 80% of the width. Also the same
    for Voynich paragraphs treated as items (their length in words).
(B) the text is a stream, but the clerk never carries a word over: a word that does not fit is cut down to fit
    (probability q), otherwise it opens the next line. Simulated on Voynich words shuffled within the page, wrapped
    as in wrapping.py with ragged margin J; the cut keeps the ending and drops the middle, then the opener, then
    leading characters (what edges.py found in short last words). Reported with wrapping.profile: first and last
    offsets, early breaks, r(slack, next first), r(space, last), mean slack. Grid q 0, 0.5, 0.8, 1 x J 0, 6, 12.
    A cell 'matches' if r(slack, next first) is inside Voynich's interval (-0.045, +0.020) and early breaks are
    within 0.10 of Voynich's 0.36 and the last-word offset is negative.

Run from targets/voynich: python lines/listcipher.py -> lines/listcipher_results.json, listcipher.md
"""
import collections, json, math, os, random, re, statistics, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..')
sys.path.insert(0, HERE); sys.path.insert(0, VOY); sys.path.insert(0, os.path.join(VOY, 'reinforce')); sys.path.insert(0, os.path.join(VOY, 'meaning'))
sys.path.insert(0, os.path.join(VOY, '..', '..', 'research', 'voynich_siblings'))
import common, wrapping
import slots4
from slots import EMPTY


def spread(fills):
    m = statistics.mean(fills)
    return dict(n=len(fills), mean=m, cv=statistics.pstdev(fills) / m, under_half=sum(1 for x in fills if x < 0.5) / len(fills),
                under_80=sum(1 for x in fills if x < 0.8) / len(fills))


def items_fill(lengths):
    s = sorted(lengths); w = s[int(0.95 * len(s))]
    return spread([min(x / w, 1.5) for x in lengths])


def cut(w, room):
    o, m, e = (('' if x == EMPTY else x) for x in slots4.split3(w))
    for cand in (o + e, e):
        if cand and len(cand) <= room:
            return cand
    return w[-room:]


def squeeze_wrap(paras, stream, J, q, rng):
    out = []; k = 0; cuts = 0; n = 0
    for para in paras:
        W = max(wrapping.llen(ws) for ws in para); cnt = sum(len(ws) for ws in para)
        words = stream[k:k + cnt]; k += cnt; n += cnt
        lines = []; cur = []; cap = W - rng.randint(0, J)
        for w in words:
            if cur and wrapping.llen(cur + [w]) > cap:
                room = cap - wrapping.llen(cur) - 1
                if room >= 1 and rng.random() < q:
                    cur.append(cut(w, room)); cuts += 1; lines.append(cur); cur = []; cap = W - rng.randint(0, J); continue
                lines.append(cur); cur = []; cap = W - rng.randint(0, J)
            cur.append(w)
        if cur:
            lines.append(cur)
        out.append(lines)
    return out, cuts / n


def main():
    t0 = time.time(); ref = common.pages(); rng = random.Random(12)
    real = [para for p in ref for para in wrapping.paragraphs(p)]
    res = collections.OrderedDict(); A = collections.OrderedDict()
    fills = []; wfill = []
    for para in real:
        if len(para) >= 3:
            W = max(wrapping.llen(ws) for ws in para); Ww = max(len(ws) for ws in para)
            fills += [wrapping.llen(ws) / W for ws in para[:-1]]; wfill += [len(ws) / Ww for ws in para[:-1]]
    A['Voynich lines (not paragraph-final), characters / longest line'] = spread(fills)
    A['Voynich lines (not paragraph-final), words / most words'] = spread(wfill)
    A['Voynich paragraphs as items (words)'] = items_fill([sum(len(ws) for ws in para) for para in real])
    bible = os.path.join(VOY, 'data', 'corpora', 'bible_lat.txt')
    if os.path.exists(bible):
        verses = [re.sub(r'\s+', ' ', l).strip() for l in open(bible, encoding='utf-8', errors='replace') if len(l.split()) >= 3]
        A['Latin Vulgate verses (characters)'] = items_fill([len(v) for v in verses])
        clauses = [c.strip() for v in verses for c in re.split(r'[,;:.]', v) if len(c.split()) >= 2]
        A['Latin Vulgate clauses (characters)'] = items_fill([len(c) for c in clauses])
        A['Latin Vulgate clauses (words)'] = items_fill([len(c.split()) for c in clauses])
    res['A'] = A
    shuf = []
    for p in ref:
        ws = [w for ln in p['lines'] for w in ln['words']]; rng.shuffle(ws); shuf += ws
    B = collections.OrderedDict(); B['Voynich'] = wrapping.profile(real); brng = random.Random(3)
    B['Voynich']['r_ci'] = wrapping.overflow(real, brng, B=300)['ci']
    for q in (0.0, 0.5, 0.8, 1.0):
        for J in (0, 6, 12):
            runs = []; cs = []
            for s in range(3):
                w, c = squeeze_wrap(real, shuf, J, q, random.Random(100 * s + J)); runs.append(wrapping.profile(w)); cs.append(c)
            r = {k: statistics.mean(x[k] for x in runs) for k in runs[0] if runs[0][k] is not None}; r['cut_share'] = statistics.mean(cs)
            r['match'] = bool(-0.045 <= r['r_slack_next'] <= 0.020 and abs(r['early_break'] - B['Voynich']['early_break']) <= 0.10 and r['last_offset'] < 0)
            B[f'q {q}, J {J}'] = r
    res['B'] = B
    json.dump(res, open(os.path.join(HERE, 'listcipher_results.json'), 'w'), indent=1)
    L = ['# A list, or a clerk who squeezes the last word in? (11 Nov 2026)', '', 'Script `listcipher.py` (protocol in its docstring).', '',
         '## A. Are lines items? Fill of a line against the length of real items', '', '| text | n | mean fill | CV | under half | under 80% |', '|---|---|---|---|---|---|']
    for k, r in A.items():
        L.append(f"| {k} | {r['n']} | {r['mean']:.2f} | {r['cv']:.2f} | {r['under_half']:.3f} | {r['under_80']:.3f} |")
    cols = [('first_offset', 'first - int.'), ('last_offset', 'last - int.'), ('early_break', 'early breaks'), ('mean_slack', 'mean slack'), ('r_slack_next', 'r slack, next first'),
            ('r_space_last', 'r space, last'), ('jsd_last', 'JSD last'), ('cut_share', 'words cut'), ('match', 'match')]
    L += ['', '## B. Stream wrapped with the overflow word cut to fit with probability q', '', '| text | ' + ' | '.join(c for _, c in cols) + ' |', '|---|' + '---|' * len(cols)]
    for k, r in B.items():
        L.append(f'| {k} | ' + ' | '.join(('-' if r.get(c) is None else str(r[c]) if c == 'match' else f'{r[c]:.3f}') for c, _ in cols) + ' |')
    L.append(''); L.append(f'Runtime {time.time() - t0:.0f} s.')
    open(os.path.join(HERE, 'listcipher.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    main()
