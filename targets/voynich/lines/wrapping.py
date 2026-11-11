"""How much of the line structure does plain line-wrapping produce? (10 Nov 2026, second session)

lines/boundaries.py found a longer first word (+0.43 glyphs against interior words) and a shorter last word (-0.36)
and read them as a shaped line. But wrapping any stream of words into lines of limited width selects by length: the
word that did not fit opens the next line (long words overflow more often) and the last word is one that fitted.
The controls of boundaries.py were poured into the Voynich skeleton by word count, so they could not show this.

Part 1 (wrap simulation). For every paragraph of the ZL text, width W = its longest line in EVA characters (words
+ one per space). A stream of words is wrapped greedily into the paragraph (a word goes on the line if it fits,
else it opens the next line), the paragraph getting the same number of words as in Voynich. Streams: Voynich words
shuffled within each page (no position information left), Voynich in its own order, Latin, English. Ragged margin:
each line's capacity is W - j, j uniform on 0..J, for J = 0, 2, 4, 6, 8, 12. Reported, with the estimators applied
identically to the real lines and to the simulated ones: mean length of the first, second, interior, penultimate
and last word (lines of 6+ words, as boundaries.py), JSD of the first glyph unit of the first and of the last word
against interior words.

Part 2 (are the real lines wrapped?). For every line that is not the last of its paragraph (paragraphs of 3+
lines), slack = W - line length and next = length of the first word of the following line + 1. 'Early break' = the
next word would have fitted (next <= slack). Under exact wrapping this never happens; a ragged margin gives some.
Also the correlation between slack and the length of the next line's first word, and of the space left before the
last word with the last word's length. Voynich by section, the wrap simulations at each J, and the Gaskell-Bowern
volunteers' own handwritten lines (people wrapping invented text on a page).

Part 3 (added after the first run showed r = -0.01 for Voynich): the same correlation with a paragraph-bootstrap
interval and the mean first-word length by slack bin, for Voynich by language and section, the volunteers and the
wrap simulations up to J = 20.

Reading rule fixed before the run: if wrapped shuffled Voynich reproduces at least two thirds of both length offsets
at a J whose early-break share is no larger than Voynich's, the length offsets of boundaries.py s2 are a wrapping
effect and are withdrawn as evidence of a shaped line (the vocabulary effects stand or fall on the JSD columns).

Run from targets/voynich: python lines/wrapping.py -> lines/wrapping_results.json, wrapping.md
"""
import collections, json, math, os, random, statistics, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..')
sys.path.insert(0, HERE); sys.path.insert(0, VOY); sys.path.insert(0, os.path.join(VOY, 'reinforce'))
import common, boundaries
import a4_selfcitation as a4

JS = (0, 2, 4, 6, 8, 12)


def llen(ws):
    return sum(len(w) for w in ws) + len(ws) - 1


def paragraphs(p):
    out = []
    for ln in p['lines']:
        if ln['para_start'] or not out:
            out.append([])
        out[-1].append(ln['words'])
    return out


def pearson(xs, ys):
    n = len(xs)
    if n < 10:
        return None
    mx = sum(xs) / n; my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs); syy = sum((y - my) ** 2 for y in ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(sxx * syy) if sxx and syy else None


def profile(paras):
    """paras: list of paragraphs, each a list of lines (word lists)"""
    L = collections.defaultdict(list); F = collections.defaultdict(collections.Counter)
    early = 0; pairs = 0; slack = []; nxt = []; before = []; last = []
    for para in paras:
        for ws in para:
            if len(ws) >= 6:
                for key, i in (('first', 0), ('second', 1), ('penult', -2), ('last', -1)):
                    L[key].append(len(ws[i])); F[key][common.units(ws[i])[0]] += 1
                for w in ws[2:-2]:
                    L['interior'].append(len(w)); F['interior'][common.units(w)[0]] += 1
        if len(para) >= 3:
            W = max(llen(ws) for ws in para)
            for a, b in zip(para, para[1:]):
                s = W - llen(a); n = len(b[0]) + 1
                pairs += 1; early += n <= s; slack.append(s); nxt.append(len(b[0]))
                if len(a) >= 2:
                    before.append(W - llen(a[:-1])); last.append(len(a[-1]))
    out = {k: statistics.mean(v) for k, v in L.items()}
    out.update(n_lines=len(L['first']), first_offset=out['first'] - out['interior'], last_offset=out['last'] - out['interior'],
               jsd_first=boundaries.common_jsd(F['first'], F['interior']), jsd_last=boundaries.common_jsd(F['last'], F['interior']),
               pairs=pairs, early_break=early / pairs if pairs else None, mean_slack=statistics.mean(slack) if slack else None,
               r_slack_next=pearson(slack, nxt), r_space_last=pearson(before, last))
    return out


BINS = ((0, 1), (2, 3), (4, 6), (7, 10), (11, 999))


def overflow(paras, rng, B=1000):
    """Part 3: is the first word of a line the word that did not fit on the line above? Per paragraph of 3+ lines,
    (slack of line i, length of the first word of line i + 1); r with a paragraph-bootstrap interval, and the mean
    first-word length by slack bin. Under wrapping the first word is longer than the slack by construction."""
    per = []
    for para in paras:
        if len(para) >= 3:
            W = max(llen(ws) for ws in para)
            per.append([(W - llen(a), len(b[0])) for a, b in zip(para, para[1:])])
    flat = [x for q in per for x in q]
    r = pearson([a for a, _ in flat], [b for _, b in flat]); bs = []
    for _ in range(B):
        sm = [x for _ in per for x in per[rng.randrange(len(per))]]
        v = pearson([a for a, _ in sm], [b for _, b in sm])
        if v is not None:
            bs.append(v)
    bs.sort()
    bins = {}
    for lo, hi in BINS:
        v = [b for a, b in flat if lo <= a <= hi]
        bins[f'{lo}-{hi}' if hi < 999 else f'{lo}+'] = dict(n=len(v), mean_first=statistics.mean(v) if v else None)
    return dict(pairs=len(flat), r=r, ci=[bs[int(0.025 * len(bs))], bs[int(0.975 * len(bs))]] if bs else None, bins=bins)


def wrap(paras, stream, J, rng):
    """re-wrap: each paragraph gets as many words as it has, from the stream, into lines of capacity W - j"""
    out = []; k = 0
    for para in paras:
        W = max(llen(ws) for ws in para); n = sum(len(ws) for ws in para)
        words = stream[k:k + n]; k += n
        lines = []; cur = []; cap = W - rng.randint(0, J)
        for w in words:
            if cur and llen(cur + [w]) > cap:
                lines.append(cur); cur = []; cap = W - rng.randint(0, J)
            cur.append(w)
        if cur:
            lines.append(cur)
        out.append(lines)
    return out


def main():
    t0 = time.time(); ref = common.pages(); rng = random.Random(4)
    real = [para for p in ref for para in paragraphs(p)]
    N = sum(len(ws) for para in real for ws in para)
    res = collections.OrderedDict(); res['real'] = collections.OrderedDict(); res['wrapped'] = collections.OrderedDict()
    res['real']['Voynich'] = profile(real)
    for lab, key in (('Currier A', 'A'), ('Currier B', 'B')):
        res['real'][lab] = profile([para for p in ref if p['lang'] == key for para in paragraphs(p)])
    for sec in sorted({p['illus'] for p in ref}):
        pp = [para for p in ref if p['illus'] == sec for para in paragraphs(p)]
        if sum(len(x) for x in pp) >= 150:
            res['real'][f'Voynich section {sec}'] = profile(pp)
    try:
        import volunteers
        gib = volunteers.gib_pages(); res['real']['volunteers, own lines'] = profile([para for p in gib for para in paragraphs(p)])
    except Exception as e:
        print('volunteers unavailable:', e, file=sys.stderr)
    shuf = []
    for p in ref:
        ws = [w for ln in p['lines'] for w in ln['words']]; rng.shuffle(ws); shuf += ws
    streams = collections.OrderedDict([('Voynich shuffled within page', shuf), ('Voynich in its own order', [w for para in real for ws in para for w in ws])])
    for name, lang in (('Latin', 'la'), ('English', 'en')):
        try:
            streams[name] = a4.lang_words(lang, N)
        except (Exception, SystemExit) as e:
            print(f'{name} unavailable: {e}', file=sys.stderr)
    for name, st in streams.items():
        for J in JS:
            runs = [profile(wrap(real, st, J, random.Random(100 * s + J))) for s in range(5 if name.startswith('Voynich shuffled') else 2)]
            res['wrapped'][f'{name}, J {J}'] = {k: statistics.mean(r[k] for r in runs) for k in runs[0] if runs[0][k] is not None}
        print(name, 'done', f'{time.time() - t0:.0f}s', flush=True)
    res['overflow'] = collections.OrderedDict(); brng = random.Random(9)
    res['overflow']['Voynich'] = overflow(real, brng)
    for lab, key in (('Currier A', 'A'), ('Currier B', 'B')):
        res['overflow'][lab] = overflow([para for p in ref if p['lang'] == key for para in paragraphs(p)], brng)
    for sec in sorted({p['illus'] for p in ref}):
        pp = [para for p in ref if p['illus'] == sec for para in paragraphs(p)]
        if sum(len(x) for x in pp) >= 150:
            res['overflow'][f'Voynich section {sec}'] = overflow(pp, brng)
    if 'volunteers, own lines' in res['real']:
        res['overflow']['volunteers, own lines'] = overflow([para for p in gib for para in paragraphs(p)], brng)
    for name in ('Voynich shuffled within page', 'Voynich in its own order', 'Latin'):
        for J in (0, 6, 12, 20):
            res['overflow'][f'wrapped: {name}, J {J}'] = overflow(wrap(real, streams[name], J, random.Random(7 + J)), brng)
    json.dump(res, open(os.path.join(HERE, 'wrapping_results.json'), 'w'), indent=1)
    cols = [('n_lines', 'lines 6+'), ('first', 'first'), ('second', 'second'), ('interior', 'interior'), ('penult', 'penult.'), ('last', 'last'), ('first_offset', 'first - int.'),
            ('last_offset', 'last - int.'), ('jsd_first', 'JSD first'), ('jsd_last', 'JSD last'), ('early_break', 'early breaks'), ('mean_slack', 'mean slack'),
            ('r_slack_next', 'r slack, next first'), ('r_space_last', 'r space, last')]
    f = lambda k, v: '-' if v is None else (f'{v:.0f}' if k == 'n_lines' else f'{v:.3f}' if k.startswith(('jsd', 'early', 'r_')) else f'{v:.2f}')
    L = ['# What line-wrapping alone does to the first and last word (10 Nov 2026)', '', 'Script `wrapping.py` (protocol in its docstring). Lengths in EVA characters.', '',
         '## Real lines', '', '| text | ' + ' | '.join(c for _, c in cols) + ' |', '|---|' + '---|' * len(cols)]
    for name, r in res['real'].items():
        L.append(f'| {name} | ' + ' | '.join(f(k, r.get(k)) for k, _ in cols) + ' |')
    L += ['', '## Streams wrapped greedily into the Voynich paragraphs (width = longest line of the paragraph, minus 0..J per line)', '',
          '| text | ' + ' | '.join(c for _, c in cols) + ' |', '|---|' + '---|' * len(cols)]
    for name, r in res['wrapped'].items():
        L.append(f'| {name} | ' + ' | '.join(f(k, r.get(k)) for k, _ in cols) + ' |')
    L += ['', '## Is the first word the word that did not fit? Slack of a line against the length of the first word of the next line', '',
          '| text | pairs | r [95%, paragraph bootstrap] | ' + ' | '.join(f'slack {k}: mean first (n)' for k in res['overflow']['Voynich']['bins']) + ' |', '|---|---|---|' + '---|' * len(BINS)]
    for name, o in res['overflow'].items():
        L.append(f"| {name} | {o['pairs']} | {o['r']:+.3f} [{o['ci'][0]:+.3f}, {o['ci'][1]:+.3f}] | "
                 + ' | '.join((f"{b['mean_first']:.2f} ({b['n']})" if b['n'] else '-') for b in o['bins'].values()) + ' |')
    L.append(''); L.append(f'Runtime {time.time() - t0:.0f} s.')
    open(os.path.join(HERE, 'wrapping.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    main()
