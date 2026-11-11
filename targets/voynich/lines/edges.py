"""What are the first and the last word of a line made of? (10 Nov 2026, second session)

wrapping.py: the first word of a line is longer than interior words by as much as wrapping would give, yet it is
not an overflow word (its length is unrelated to the space left on the line above), and the last word is shorter
than wrapping gives (Currier B). So both edges are made that way. Three measurements on the ZL paragraph text,
lines of 6+ words, interior pool = words at index >= 3 and not among the last two (as boundaries.py).

Part 1 (is the first word an ordinary word with a glyph in front?). For a word w, a = number of interior tokens
equal to w (leave-one-out for interior tokens), b = number of interior tokens equal to w without its first glyph
unit. 'Prefixed-like' = b >= 5 * max(a, 1): stripping the first glyph gives a word at least five times commoner
inside lines. Share per position (first, second, interior, last), for paragraph-first lines and other lines
separately, and by first glyph for line-first words against interior words that begin with the same glyph. If the
first word were an interior word plus one glyph in a share s of lines, the length offset would be about s glyphs.
Control: the same on Voynich with words shuffled within each line (positions destroyed).

Part 2 (which slot is short at the edge?). Word = opener | middle | ending (slots4.split3). Share of words with an
empty opener, an empty middle, an empty ending, and mean slot length in EVA characters, by position, for Currier A
and B. Last word: the same by the space left before it (wrapping.py's width: longest line of the paragraph), in
bins, and the ten endings most over-represented in the last word.

Part 3 (the same for the last word read backwards: is it an ordinary word cut short or with a glyph added?). a as
above; c = number of interior tokens of which w is a proper prefix by exactly one glyph unit (w + one unit), d =
number of interior tokens equal to w without its last unit. 'Cut-like' = c >= 5 * max(a, 1); 'suffixed-like' =
d >= 5 * max(a, 1). Share per position.

Part 4 (does the A/B convention hold at the edges?). JSD between Currier A and B of the opener, middle and ending
distributions, by position; reference = the JSD of interior words subsampled to the same counts (20 draws).

Part 5 (is the short last word an ordinary short word?). For each word length (EVA characters), JSD between the
distribution of last words of that length and interior words of that length, against the floor (interior words of
that length subsampled to the same count, against the rest; 20 draws); the same without words ending in m, and for
first words. If the scribe only picked an ordinary word that fits, the last word would match interior words of its
length.

Run from targets/voynich: python lines/edges.py -> lines/edges_results.json, edges.md
"""
import collections, json, math, os, random, statistics, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..')
sys.path.insert(0, HERE); sys.path.insert(0, VOY); sys.path.insert(0, os.path.join(VOY, 'reinforce')); sys.path.insert(0, os.path.join(VOY, 'meaning'))
sys.path.insert(0, os.path.join(VOY, '..', '..', 'research', 'voynich_siblings'))
import common, wrapping
import slots4
from slots import EMPTY

U = common.units
POS = ('first', 'second', 'interior', 'penult', 'last')


def positions(pgs):
    """yield (position, word, page, line is paragraph-first, space left before the word or None)"""
    for p in pgs:
        for para in wrapping.paragraphs(p):
            W = max(wrapping.llen(ws) for ws in para)
            for li, ws in enumerate(para):
                if len(ws) < 6:
                    continue
                for i, w in enumerate(ws):
                    pos = 'first' if i == 0 else 'second' if i == 1 else 'last' if i == len(ws) - 1 else 'penult' if i == len(ws) - 2 else 'interior' if i >= 2 else None
                    space = W - wrapping.llen(ws[:-1]) - 1 if pos == 'last' and len(para) >= 3 else None
                    yield pos, w, p, li == 0, space


def affix_tests(pgs):
    rows = list(positions(pgs))
    inter = collections.Counter(w for pos, w, *_ in rows if pos == 'interior')
    plus1 = collections.Counter()      # interior tokens counted under their form without the last unit
    for w, c in inter.items():
        u = U(w)
        if len(u) >= 2:
            plus1[''.join(u[:-1])] += c
    out = collections.OrderedDict(); by_glyph = {k: collections.defaultdict(lambda: [0, 0]) for k in ('first', 'interior')}
    for scope in ('all lines', 'paragraph-first lines', 'other lines'):
        for pos in POS:
            n = 0; pre = 0; cut = 0; suf = 0; known = 0; lens = []; stripped_lens = []
            for ps, w, p, pfirst, _ in rows:
                if ps != pos or (scope == 'paragraph-first lines' and not pfirst) or (scope == 'other lines' and pfirst):
                    continue
                u = U(w); a = inter[w] - (1 if pos == 'interior' else 0); n += 1; known += a >= 1
                is_pre = len(u) >= 2 and inter[''.join(u[1:])] >= 5 * max(a, 1)
                pre += is_pre; lens.append(len(w)); stripped_lens.append(len(''.join(u[1:])) if is_pre else len(w))
                cut += plus1[w] - (0) >= 5 * max(a, 1)
                suf += len(u) >= 2 and inter[''.join(u[:-1])] >= 5 * max(a, 1)
                if scope == 'all lines' and pos in by_glyph:
                    g = by_glyph[pos][u[0]]; g[0] += 1; g[1] += is_pre
            if n:
                out[f'{scope} | {pos}'] = dict(n=n, known_interior_word=known / n, prefixed_like=pre / n, cut_like=cut / n, suffixed_like=suf / n,
                                               mean_len=statistics.mean(lens), mean_len_prefix_removed=statistics.mean(stripped_lens))
    glyphs = {}
    for g, (n, k) in sorted(by_glyph['first'].items(), key=lambda x: -x[1][0])[:14]:
        ni, ki = by_glyph['interior'].get(g, [0, 0])
        glyphs[g] = dict(first_n=n, first_prefixed=k / n, interior_n=ni, interior_prefixed=ki / ni if ni else None)
    return out, glyphs


def slot_tests(pgs):
    out = collections.OrderedDict()
    for lang in ('A', 'B'):
        cells = collections.defaultdict(list)
        for pos, w, p, pfirst, space in positions(pgs):
            if p['lang'] != lang or pos is None:
                continue
            o, m, e = (('' if x == EMPTY else x) for x in slots4.split3(w))
            cells[pos].append((o, m, e))
            if pos == 'last' and space is not None:
                cells['last, space ' + ('<= 3' if space <= 3 else '4-5' if space <= 5 else '6-8' if space <= 8 else '9+')].append((o, m, e))
        for k in list(POS) + ['last, space <= 3', 'last, space 4-5', 'last, space 6-8', 'last, space 9+']:
            v = cells.get(k)
            if v:
                out[f'{lang} | {k}'] = dict(n=len(v), no_opener=sum(1 for o, m, e in v if not o) / len(v), no_middle=sum(1 for o, m, e in v if not m) / len(v),
                                            no_ending=sum(1 for o, m, e in v if not e) / len(v), len_opener=statistics.mean(len(o) for o, m, e in v),
                                            len_middle=statistics.mean(len(m) for o, m, e in v), len_ending=statistics.mean(len(e) for o, m, e in v),
                                            len_word=statistics.mean(len(o + m + e) or 1 for o, m, e in v))
        ei = collections.Counter(e for o, m, e in cells['interior']); el = collections.Counter(e for o, m, e in cells['last'])
        ni = sum(ei.values()); nl = sum(el.values())
        ratio = sorted(((el[e] / nl) / ((ei[e] + 0.5) / ni), e, el[e]) for e in el if el[e] >= 15)
        out[f'{lang} | endings over-represented in the last word'] = [dict(ending=e or '(none)', ratio=r, n_last=c, share_last=c / nl) for r, e, c in ratio[::-1][:10]]
        out[f'{lang} | endings under-represented in the last word'] = [dict(ending=e or '(none)', ratio=r, n_last=c, share_last=c / nl) for r, e, c in ratio[:6]]
    return out


def ab_by_position(pgs):
    import boundaries
    def dists(pp, slot):
        d = collections.defaultdict(collections.Counter)
        for pos, w, p, pf, sp in positions(pp):
            if pos:
                d[pos][slots4.split3(w)[slot]] += 1
        return d
    A = [p for p in pgs if p['lang'] == 'A']; B = [p for p in pgs if p['lang'] == 'B']; out = collections.OrderedDict()
    for slot, name in enumerate(('opener', 'middle', 'ending')):
        dA = dists(A, slot); dB = dists(B, slot); ia = list(dA['interior'].elements()); ib = list(dB['interior'].elements()); rng = random.Random(1)
        for pos in POS:
            nA = sum(dA[pos].values()); nB = sum(dB[pos].values())
            fl = [boundaries.common_jsd(collections.Counter(rng.sample(ia, min(nA, len(ia)))), collections.Counter(rng.sample(ib, min(nB, len(ib))))) for _ in range(20)]
            out[f'{name} | {pos}'] = dict(jsd=boundaries.common_jsd(dA[pos], dB[pos]), interior_same_n=statistics.mean(fl), interior_same_n_max=max(fl), nA=nA, nB=nB)
    return out


def length_matched(pgs):
    import boundaries
    out = collections.OrderedDict()
    for lang in ('A', 'B'):
        rows = [r for r in positions([p for p in pgs if p['lang'] == lang]) if r[0]]
        by = {k: [w for pos, w, *_ in rows if pos == k] for k in ('interior', 'last', 'first')}; rng = random.Random(2)
        for n in range(1, 9):
            i = [w for w in by['interior'] if len(w) == n]; ci = collections.Counter(i)
            def cmp(x):
                if len(x) < 40 or len(i) < 2 * len(x):
                    return None
                fl = [boundaries.common_jsd(collections.Counter(rng.sample(i, len(x))), ci) for _ in range(20)]
                return dict(n=len(x), jsd=boundaries.common_jsd(collections.Counter(x), ci), floor=statistics.mean(fl))
            l = [w for w in by['last'] if len(w) == n]
            out[f'{lang} | {n}'] = dict(n_interior=len(i), share_interior=len(i) / len(by['interior']), share_last=len(l) / len(by['last']), last=cmp(l),
                                        last_without_m=cmp([w for w in l if not w.endswith('m')]), first=cmp([w for w in by['first'] if len(w) == n]))
    return out


def main():
    t0 = time.time(); ref = common.pages()
    res = collections.OrderedDict()
    res['affix'], res['first_glyphs'] = affix_tests(ref)
    res['affix_shuffled'], _ = affix_tests(common.shuffle_within_line(ref, seed=5))
    res['slots'] = slot_tests(ref)
    res['ab_by_position'] = ab_by_position(ref)
    res['length_matched'] = length_matched(ref)
    json.dump(res, open(os.path.join(HERE, 'edges_results.json'), 'w'), indent=1)
    L = ['# What the first and the last word of a line are made of (10 Nov 2026)', '', 'Script `edges.py` (protocol in its docstring).', '',
         '## 1 and 3. Affix tests against the interior vocabulary', '',
         '| lines | position | n | is an interior word | prefixed-like | cut-like | suffixed-like | mean length | mean length, prefix removed |', '|---|---|---|---|---|---|---|---|---|']
    for k, r in res['affix'].items():
        sc, pos = k.split(' | ')
        L.append(f"| {sc} | {pos} | {r['n']} | {r['known_interior_word']:.3f} | {r['prefixed_like']:.3f} | {r['cut_like']:.3f} | {r['suffixed_like']:.3f} | {r['mean_len']:.2f} | {r['mean_len_prefix_removed']:.2f} |")
    L += ['', 'Words shuffled within each line (control):', '', '| lines | position | n | is an interior word | prefixed-like | cut-like | suffixed-like | mean length |', '|---|---|---|---|---|---|---|---|']
    for k, r in res['affix_shuffled'].items():
        sc, pos = k.split(' | ')
        if sc == 'all lines':
            L.append(f"| {sc} | {pos} | {r['n']} | {r['known_interior_word']:.3f} | {r['prefixed_like']:.3f} | {r['cut_like']:.3f} | {r['suffixed_like']:.3f} | {r['mean_len']:.2f} |")
    L += ['', 'Line-first words by first glyph: share prefixed-like, against interior words beginning with the same glyph:', '',
          '| first glyph | n first | prefixed-like, first | n interior | prefixed-like, interior |', '|---|---|---|---|---|']
    for g, r in res['first_glyphs'].items():
        L.append(f"| {g} | {r['first_n']} | {r['first_prefixed']:.3f} | {r['interior_n']} | " + ('-' if r['interior_prefixed'] is None else f"{r['interior_prefixed']:.3f}") + ' |')
    L += ['', '## 2. Slots by position', '', '| language | position | n | no opener | no middle | no ending | opener length | middle length | ending length | word length |', '|---|---|---|---|---|---|---|---|---|---|']
    for k, r in res['slots'].items():
        if isinstance(r, dict):
            lang, pos = k.split(' | ')
            L.append(f"| {lang} | {pos} | {r['n']} | {r['no_opener']:.3f} | {r['no_middle']:.3f} | {r['no_ending']:.3f} | {r['len_opener']:.2f} | {r['len_middle']:.2f} | {r['len_ending']:.2f} | {r['len_word']:.2f} |")
    L.append('')
    for k, r in res['slots'].items():
        if isinstance(r, list):
            L.append(f'- {k}: ' + ', '.join(f"{x['ending']} x{x['ratio']:.1f} ({x['share_last']:.3f} of last words)" for x in r))
    L += ['', '## 4. Currier A against B, by slot and position (JSD in bits; in brackets interior words subsampled to the same counts: mean, max of 20)', '',
          '| slot | ' + ' | '.join(POS) + ' |', '|---|' + '---|' * len(POS)]
    for name in ('opener', 'middle', 'ending'):
        L.append(f'| {name} | ' + ' | '.join(f"{res['ab_by_position'][f'{name} | {pos}']['jsd']:.3f} ({res['ab_by_position'][f'{name} | {pos}']['interior_same_n']:.3f}, {res['ab_by_position'][f'{name} | {pos}']['interior_same_n_max']:.3f})" for pos in POS) + ' |')
    L += ['', '## 5. Edge words against interior words of the same length: JSD (floor), n', '',
          '| language | length | interior n | share of interior / of last words | last | last, no -m words | first |', '|---|---|---|---|---|---|---|']
    g = lambda c: '-' if c is None else f"{c['jsd']:.3f} ({c['floor']:.3f}), {c['n']}"
    for k, r in res['length_matched'].items():
        lang, n = k.split(' | ')
        L.append(f"| {lang} | {n} | {r['n_interior']} | {r['share_interior']:.3f} / {r['share_last']:.3f} | {g(r['last'])} | {g(r['last_without_m'])} | {g(r['first'])} |")
    L.append(''); L.append(f'Runtime {time.time() - t0:.0f} s.')
    open(os.path.join(HERE, 'edges.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    main()
