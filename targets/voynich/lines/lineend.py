"""The line-final -m words: padding, abbreviation mark, or ordinary words? (11 Nov 2026)

edges.py: -am is 41 times commoner in the last word of a line than inside it in Currier B (16% of last words), -om
53 times; in A 9 and 5 times. Three readings: (a) padding written to fill the line; (b) a line-end form of ordinary
words (the ending swapped at the margin); (c) ordinary words that happen to be short.

ZL paragraph text; lines that are not the last of their paragraph, paragraphs of 3+ lines, lines of 3+ words; width
W = longest line of the paragraph (wrapping.py). 'm word' = a word ending in the glyph m.

1. Where m words sit: share of all m words that are line-final; share of last words that are m words by the space
   left before the last word, and by the slack left after the line.
2. Padding: at the same space before the last word (bins), mean length of an m last word against other last words,
   and the slack left after it. Padding fills: an m word would leave less slack than other last words.
3. Chain: coupling X (boundaries.coupling) between the last unit of the penultimate word and the first unit of the
   last word, for m last words, other last words and interior pairs. Padding stuck on at the margin would not follow
   the chain.
4. Stems: stem = the word without its ending slot (slots4.split3: opener + middle). Stem distribution of line-final
   -am words against the stems of interior words with each common ending (JSD; floor = interior words of that
   ending subsampled to the same count against the rest). The ending whose stems they share is the one -am
   stands in for, if any; if none is near the floor, the m words are not ordinary words with a swapped ending.
5. What follows: first-unit distribution of the next line's first word after an m last word against after other
   last words (JSD, floor by label shuffle).

Run from targets/voynich: python lines/lineend.py -> lines/lineend_results.json, lineend.md
"""
import collections, json, math, os, random, statistics, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..')
sys.path.insert(0, HERE); sys.path.insert(0, VOY); sys.path.insert(0, os.path.join(VOY, 'reinforce')); sys.path.insert(0, os.path.join(VOY, 'meaning'))
sys.path.insert(0, os.path.join(VOY, '..', '..', 'research', 'voynich_siblings'))
import common, wrapping, boundaries
import slots4
from slots import EMPTY

BB = ((0, 3, '<= 3'), (4, 5, '4-5'), (6, 8, '6-8'), (9, 999, '9+'))
AB = ((0, 1, '0-1'), (2, 4, '2-4'), (5, 9, '5-9'), (10, 999, '10+'))


def binof(x, bins):
    for lo, hi, lab in bins:
        if lo <= x <= hi:
            return lab


def stem(w):
    o, m, e = slots4.split3(w)
    return ('' if o == EMPTY else o) + ('' if m == EMPTY else m), ('' if e == EMPTY else e)


def analyse(pgs, rng):
    lines = []; inter_words = []; all_m = 0; final_m = 0; inter_pairs = []
    for p in pgs:
        for para in wrapping.paragraphs(p):
            W = max(wrapping.llen(ws) for ws in para)
            for i, ws in enumerate(para):
                all_m += sum(1 for w in ws if w.endswith('m')); final_m += ws[-1].endswith('m')
                if len(ws) >= 6:
                    inter_words += ws[2:-2]; inter_pairs += list(zip(ws[2:-3], ws[3:-2]))
                if len(para) >= 3 and i < len(para) - 1 and len(ws) >= 3:
                    lines.append(dict(last=ws[-1], prev=ws[-2], before=W - wrapping.llen(ws[:-1]) - 1, after=W - wrapping.llen(ws), nxt=para[i + 1][0]))
    out = dict(lines=len(lines), m_words=all_m, share_of_m_words_line_final=final_m / all_m if all_m else None)
    ism = lambda l: l['last'].endswith('m')
    out['m_share_by_space_before'] = {lab: dict(n=len(v), m=sum(map(ism, v)) / len(v)) for lo, hi, lab in BB for v in [[l for l in lines if lo <= l['before'] <= hi]] if v}
    out['m_share_by_slack_after'] = {lab: dict(n=len(v), m=sum(map(ism, v)) / len(v)) for lo, hi, lab in AB for v in [[l for l in lines if lo <= l['after'] <= hi]] if v}
    pad = {}
    for lo, hi, lab in BB:
        a = [l for l in lines if lo <= l['before'] <= hi and ism(l)]; b = [l for l in lines if lo <= l['before'] <= hi and not ism(l)]
        if len(a) >= 15 and len(b) >= 15:
            pad[lab] = dict(n_m=len(a), n_other=len(b), len_m=statistics.mean(len(l['last']) for l in a), len_other=statistics.mean(len(l['last']) for l in b),
                            slack_m=statistics.mean(l['after'] for l in a), slack_other=statistics.mean(l['after'] for l in b))
    out['padding'] = pad
    cp = lambda pairs: (boundaries.coupling(pairs, rng) or {}).get('X')
    out['chain'] = dict(m_last=cp([(l['prev'], l['last']) for l in lines if ism(l)]), other_last=cp([(l['prev'], l['last']) for l in lines if not ism(l)]),
                        interior=cp(inter_pairs), n_m=sum(map(ism, lines)))
    # stems
    by_end = collections.defaultdict(list)
    for w in inter_words:
        s, e = stem(w); by_end[e].append(s)
    target = [stem(l['last'])[0] for l in lines if stem(l['last'])[1] == 'am']
    st = {}
    if len(target) >= 40:
        for e, v in by_end.items():
            if len(v) >= 4 * len(target):
                cv = collections.Counter(v)
                fl = [boundaries.common_jsd(collections.Counter(rng.sample(v, len(target))), cv) for _ in range(20)]
                st[e or '(none)'] = dict(n_interior=len(v), jsd=boundaries.common_jsd(collections.Counter(target), cv), floor=statistics.mean(fl))
    out['stems_of_final_am'] = dict(n=len(target), top=collections.Counter(target).most_common(8), against=st)
    # what follows
    fa = collections.Counter(common.units(l['nxt'])[0] for l in lines if ism(l)); fb = collections.Counter(common.units(l['nxt'])[0] for l in lines if not ism(l))
    labs = [ism(l) for l in lines]; firsts = [common.units(l['nxt'])[0] for l in lines]; fl = []
    for _ in range(50):
        rng.shuffle(labs)
        fl.append(boundaries.common_jsd(collections.Counter(f for f, x in zip(firsts, labs) if x), collections.Counter(f for f, x in zip(firsts, labs) if not x)))
    out['next_first'] = dict(jsd=boundaries.common_jsd(fa, fb), floor=statistics.mean(fl), floor_max=max(fl))
    return out


def main():
    t0 = time.time(); ref = common.pages(); rng = random.Random(8)
    res = collections.OrderedDict((lab, analyse([p for p in ref if key is None or p['lang'] == key], rng)) for lab, key in (('Voynich', None), ('Currier A', 'A'), ('Currier B', 'B')))
    json.dump(res, open(os.path.join(HERE, 'lineend_results.json'), 'w'), indent=1)
    L = ['# The line-final m words (11 Nov 2026)', '', 'Script `lineend.py` (protocol in its docstring).', '']
    for lab, r in res.items():
        L += [f'## {lab}', '', f"{r['lines']} lines; {r['m_words']} m words in the text, {r['share_of_m_words_line_final']:.3f} of them line-final.", '',
              'Share of last words that are m words, by space before the last word: ' + ', '.join(f"{k} {v['m']:.3f} (n {v['n']})" for k, v in r['m_share_by_space_before'].items()),
              '', 'by slack after the line: ' + ', '.join(f"{k} {v['m']:.3f} (n {v['n']})" for k, v in r['m_share_by_slack_after'].items()), '',
              '| space before | n m / other | length m / other | slack after m / other |', '|---|---|---|---|']
        for k, v in r['padding'].items():
            L.append(f"| {k} | {v['n_m']} / {v['n_other']} | {v['len_m']:.2f} / {v['len_other']:.2f} | {v['slack_m']:.2f} / {v['slack_other']:.2f} |")
        c = r['chain']; f = lambda x: '-' if x is None else f'{x:.3f}'
        L += ['', f"Chain X, penultimate -> last: m last words {f(c['m_last'])} (n {c['n_m']}), other last words {f(c['other_last'])}, interior pairs {f(c['interior'])}.", '']
        s = r['stems_of_final_am']
        L.append(f"Stems of line-final -am words (n {s['n']}; commonest: " + ', '.join(f"{a or '(none)'} {b}" for a, b in s['top']) + '), JSD against the stems of interior words by ending (floor): '
                 + ', '.join(f"-{e} {v['jsd']:.3f} ({v['floor']:.3f})" for e, v in sorted(s['against'].items(), key=lambda x: x[1]['jsd'] - x[1]['floor'])))
        n = r['next_first']
        L += ['', f"First unit of the next line after an m word against after other words: JSD {n['jsd']:.4f} (label-shuffle floor {n['floor']:.4f}, max {n['floor_max']:.4f}).", '']
    L.append(f'Runtime {time.time() - t0:.0f} s.')
    open(os.path.join(HERE, 'lineend.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    main()
