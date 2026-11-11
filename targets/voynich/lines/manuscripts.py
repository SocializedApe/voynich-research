"""Does a real copied manuscript show the overflow signal that Voynich lacks? (11 Nov 2026)

wrapping.py compared Voynich with text wrapped by a simulation: a wrapped line breaks because the next word did not
fit, so the first word of a line is longer when the line above had little room left, r(slack, next first word) =
+0.09 to +0.38, and Voynich has -0.01. The simulation is not a manuscript. Here the same functions
(wrapping.profile, wrapping.overflow) run on line-by-line graphic transcriptions of real manuscripts (CREMMA
Medieval and CREMMA Medieval LAT, fetched by fetch_mss.py): main-text zones, default lines, one column (text block)
of a page taken as the unit that a paragraph is for Voynich; words = runs of characters between spaces or
punctuation, as the scribe separated them. A word broken at the line end counts as two words, as it would in a
transliteration.
Genre is set by hand from the catalogue contents before any result: prose, verse (one verse a line, the list case
of listcipher.py), other (song book, unknown layout). Manuscripts with fewer than 150 usable lines are pooled only.
Reported per pool and per manuscript: lines, fill of a line (characters over the longest line of its column; mean
and CV), first-word and last-word length offsets, early breaks (the next first word would have fitted),
r(slack, next first word) with a column-bootstrap interval, and the same r with the slack measured in pixels
(right edge of the widest line of the column less the width of the line, from the ALTO coordinates).
Added after the first run (prose gave r = -0.009): the other two line results on the same manuscripts. r(space left
before the last word, length of the last word) from wrapping.profile; and the coupling between adjacent words
(normalised excess mutual information of the last character of a word and the first character of the next, as
boundaries.coupling but on characters) for interior pairs of a line and for the pair across a line break.
Control for the simulation: the prose pool re-wrapped by wrapping.wrap from its own word stream (ragged margin J 0, 4,
8), which says what the simulation predicts for these very words.
Reading fixed before the run: if real prose gives r clearly above 0 like the simulation, the Voynich result stands
as a difference from copied text; if real prose gives r near 0, the missing overflow signal is what scribes do
(breaking words, filling lines) and section 5 of the README has to be withdrawn as evidence against copying.

Run from targets/voynich: python lines/fetch_mss.py; python lines/manuscripts.py -> lines/manuscripts_results.json, manuscripts.md
"""
import collections, csv, glob, json, os, random, re, statistics, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..')
sys.path.insert(0, HERE); sys.path.insert(0, VOY); sys.path.insert(0, os.path.join(VOY, 'reinforce')); sys.path.insert(0, os.path.join(VOY, 'meaning'))
sys.path.insert(0, os.path.join(VOY, '..', '..', 'research', 'voynich_siblings'))
import common, wrapping, boundaries

DIR = os.path.join(VOY, 'data', 'external', 'cremma')
VERSE = {'vaticane_reg_lat_1616-otinel', 'bodmer_168-otinel', 'pennsylvania_codex_909-eneide', 'bnf_fr_24428-bestiaire', 'bnf_arsenal_3516-imageDuMonde',
         'CCCC-MSS-236', 'LaurentianusPluteus33.31', 'LaurentianusPluteus39.34', 'Latin6395', 'Latin8236'}
OTHER = {'bnf_fr_844-manuscritDuRoi', 'bnf_fr_1728', 'pennsylvania_660-pelerinageMademoiselleSapience', 'SBB_PK_Hdschr25', 'BGO-511'}
PUNCT = re.compile(r'[\s.,:;!?·•¶/()\[\]"\'‸⸫⸵]+')


def load(f):
    """-> list of columns, each a list of (words, width_px)"""
    cols = collections.OrderedDict()
    for r in csv.DictReader(open(f, encoding='utf-8'), delimiter='\t'):
        if not r['block_type'].startswith('MainZone') or r['line_type'] != 'DefaultLine':
            continue
        ws = [w for w in PUNCT.split(r['text']) if w]
        if ws:
            cols.setdefault((r['page'], r['block']), []).append((ws, float(r['width_px']) if r['width_px'] else None))
    return list(cols.values())


def char_coupling(pairs, rng, reps=10):
    if len(pairs) < 50:
        return None
    ab = [(a[-1].lower(), b[0].lower()) for a, b in pairs]; xs = [x for x, _ in ab]; ys = [y for _, y in ab]; base = []
    obs = boundaries.mi(ab)
    for _ in range(reps):
        rng.shuffle(ys); base.append(boundaries.mi(list(zip(xs, ys))))
    return (obs - statistics.mean(base)) / boundaries.H(collections.Counter(ys))


def measure(cols, rng):
    paras = [[ws for ws, _ in c] for c in cols]; pr = wrapping.profile(paras); ov = wrapping.overflow(paras, rng, B=300)
    fills = []; sp = []; nx = []
    for c in cols:
        if len(c) >= 3:
            W = max(wrapping.llen(ws) for ws, _ in c); fills += [wrapping.llen(ws) / W for ws, _ in c[:-1]]
            if all(px for _, px in c):
                P = max(px for _, px in c)
                for (a, pa), (b, _) in zip(c, c[1:]):
                    sp.append(P - pa); nx.append(len(b[0]))
    m = statistics.mean(fills) if fills else None
    K = boundaries.pair_kinds([{'lines': [{'words': ws, 'para_start': False} for ws, _ in c]} for c in cols])
    xw = char_coupling(K['within'], rng); xb = char_coupling(K['line_break'], rng)
    return dict(lines=sum(len(c) for c in cols), words=sum(len(ws) for c in cols for ws, _ in c), fill_mean=m, fill_cv=statistics.pstdev(fills) / m if fills else None,
                first_offset=pr.get('first_offset'), last_offset=pr.get('last_offset'), early_break=pr['early_break'], r=ov['r'], ci=ov['ci'],
                r_px=wrapping.pearson(sp, nx), r_space_last=pr.get('r_space_last'), x_within=xw, x_break=xb)


def main():
    t0 = time.time(); rng = random.Random(8); res = collections.OrderedDict(); pools = collections.defaultdict(list); per = []
    for f in sorted(glob.glob(os.path.join(DIR, '*.tsv'))):
        repo, ms = os.path.basename(f)[:-4].split('__'); cols = load(f)
        genre = 'verse' if ms in VERSE else 'other' if ms in OTHER else 'prose'
        key = f"{genre}, {'Latin' if repo.endswith('lat') else 'French'}"; pools[key] += cols
        if sum(len(c) for c in cols) >= 150:
            per.append((f'{ms} ({key})', cols))
    ref = common.pages(); voy = [[(ws, None) for ws in para] for p in ref for para in wrapping.paragraphs(p)]
    res['Voynich (paragraphs)'] = measure(voy, rng)
    for key in sorted(pools):
        res['pool: ' + key] = measure(pools[key], rng)
    prose = pools['prose, French'] + pools['prose, Latin']; res['pool: prose, both'] = measure(prose, rng)
    paras = [[ws for ws, _ in c] for c in prose]; stream = [w for para in paras for ws in para for w in ws]
    for J in (0, 4, 8):
        w = wrapping.wrap(paras, stream, J, random.Random(J)); res[f'prose pool re-wrapped by the simulation, J {J}'] = measure([[(ws, None) for ws in para] for para in w], rng)
    for name, cols in per:
        res[name] = measure(cols, rng)
    json.dump(res, open(os.path.join(HERE, 'manuscripts_results.json'), 'w'), indent=1)
    def f(x, fmt):
        return '-' if x is None else fmt.format(x)
    L = ['# Real manuscripts, line by line: is there an overflow signal? (11 Nov 2026)', '',
         'Script `manuscripts.py` (protocol and the reading fixed in advance in its docstring). Reproduce: `python lines/fetch_mss.py`, then `python lines/manuscripts.py`, from `targets/voynich`.', '',
         '| text | lines | fill mean | fill CV | first - interior | last - interior | early breaks | r(slack, next first) [95%] | r with slack in pixels | r(space, last word) | coupling within line | coupling across line break |', '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for k, r in res.items():
        ci = '-' if not r['ci'] else f"[{r['ci'][0]:+.3f}, {r['ci'][1]:+.3f}]"
        L.append(f"| {k} | {r['lines']} | {f(r['fill_mean'], '{:.2f}')} | {f(r['fill_cv'], '{:.2f}')} | {f(r['first_offset'], '{:+.2f}')} | {f(r['last_offset'], '{:+.2f}')} | {f(r['early_break'], '{:.2f}')} | {f(r['r'], '{:+.3f}')} {ci} | {f(r['r_px'], '{:+.3f}')} | {f(r['r_space_last'], '{:+.3f}')} | {f(r['x_within'], '{:.4f}')} | {f(r['x_break'], '{:.4f}')} |")
    L.append(''); L.append(f'Runtime {time.time() - t0:.0f} s.')
    open(os.path.join(HERE, 'manuscripts.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    main()
