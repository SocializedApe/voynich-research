"""c2_charts.py -- the inline SVG charts on docs/voynich.html, drawn from results/*.json.

Each chart replaces the text between <!-- vchart:NAME --> and <!-- /vchart:NAME --> in the page.  Colours are
CSS classes (.vchart .s1 ... in docs/style.css): the reference data-viz palette, slots 1-5, validated against
both site surfaces (scripts/validate_palette.js: adjacent pairs pass in dark and light; the scatter uses only
slots 1-3, which pass all-pairs).  Every mark has a <title> tooltip; the tables on the page carry the numbers.
Run after c1_comparators.py and c3_period.py:  python c2_charts.py
"""
import html, json, math, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results')
PAGE = os.path.join(HERE, '..', '..', 'docs', 'voynich.html')


def load(name):
    p = os.path.join(RES, name)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None


def esc(s):
    return html.escape(str(s), quote=True)


def svg_open(w, h, label):
    return [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" class="vchart" role="img" aria-label="{esc(label)}">']


def lin(d0, d1, r0, r1):
    return lambda v: r0 + (v - d0) * (r1 - r0) / (d1 - d0)


def marker(shape, x, y, cls, r=4.5, tip=None, hollow=False):
    k = f'{cls} hollow' if hollow else cls
    if shape == 'square':
        m = f'<rect class="{k}" x="{x - r:.1f}" y="{y - r:.1f}" width="{2 * r:.1f}" height="{2 * r:.1f}" rx="1"/>'
    elif shape == 'triangle':
        m = f'<path class="{k}" d="M{x:.1f} {y - r * 1.15:.1f}L{x + r * 1.1:.1f} {y + r * .8:.1f}L{x - r * 1.1:.1f} {y + r * .8:.1f}Z"/>'
    elif shape == 'diamond':
        m = f'<path class="{k}" d="M{x:.1f} {y - r * 1.2:.1f}L{x + r * 1.2:.1f} {y:.1f}L{x:.1f} {y + r * 1.2:.1f}L{x - r * 1.2:.1f} {y:.1f}Z"/>'
    else:
        m = f'<circle class="{k}" cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}"/>'
    if tip:
        return f'<g class="pt"><title>{esc(tip)}</title>{m}<circle class="hit" cx="{x:.1f}" cy="{y:.1f}" r="8"/></g>'
    return m


def legend(items, x, y, gap=22):
    out = []
    for shape, cls, text in items:
        hollow = shape.endswith('-o')
        out.append(marker(shape[:-2] if hollow else shape, x + 5, y - 4, cls, r=4.5, hollow=hollow))
        out.append(f'<text class="lab" x="{x + 14}" y="{y}">{esc(text)}</text>')
        x += 14 + 6.6 * len(text) + gap
    return out


# ------------------------------------------------------------------------------------- A: h2 against alphabet
def chart_h2(c1):
    W, H, L, R, T, B = 760, 440, 58, 18, 46, 50
    X = lin(10, 80, L, W - R); Y = lin(1.9, 4.3, H - B, T)
    o = svg_open(W, H, 'Conditional character entropy against alphabet size: Voynich transliterations sit below every '
                       'natural language, but merged-glyph transliterations come close to Hawaiian and are matched by Toki Pona')
    for v in [2.0, 2.5, 3.0, 3.5, 4.0]:
        o.append(f'<line class="grid" x1="{L}" x2="{W - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/>'
                 f'<text x="{L - 8}" y="{Y(v) + 4:.1f}" text-anchor="end">{v:.1f}</text>')
    for v in range(10, 81, 10):
        o.append(f'<line class="grid" y1="{T}" y2="{H - B}" x1="{X(v):.1f}" x2="{X(v):.1f}"/>'
                 f'<text x="{X(v):.1f}" y="{H - B + 16}" text-anchor="middle">{v}</text>')
    o.append(f'<line class="axis" x1="{L}" x2="{W - R}" y1="{H - B}" y2="{H - B}"/>')
    o.append(f'<text x="{(L + W - R) / 2:.0f}" y="{H - 12}" text-anchor="middle">alphabet size, space included</text>')
    o.append(f'<text x="14" y="{(T + H - B) / 2:.0f}" text-anchor="middle" transform="rotate(-90 14 {(T + H - B) / 2:.0f})">'
             f'h2, bits per character (space counted)</text>')
    lb = [l.rstrip('\n').split('\t') for l in open(os.path.join(HERE, 'data', 'lb2021_wikipedia_h2.tsv'), encoding='utf-8')
          if not l.startswith('#')][1:]
    shown = 0
    for r in lb:
        n, h2 = int(r[5]), float(r[8])
        if n <= 80 and h2 <= 4.3:
            shown += 1
            o.append(f'<circle class="bg" cx="{X(n):.1f}" cy="{Y(h2):.1f}" r="2.6"><title>{esc(r[0])} ({esc(r[3])} script), '
                     f'Wikipedia: h2 {h2:.3f}, {n} characters (Lindemann &amp; Bowern 2021)</title></circle>')
    fam = {'Voynich': ('circle', 's1'), 'language': ('square', 's2'), 'low-h2 language': ('square', 's2'),
           'constructed language': ('triangle', 's3')}
    for k, v in c1['h2_conventions'].items():
        if v['group'] not in fam:
            continue
        shape, cls = fam[v['group']]; ws = v['with_space']
        o.append(marker(shape, X(ws['alphabet']), Y(ws['h2']), cls, r=5,
                        tip=f"{v['label']}: h2 {ws['h2']:.3f} with space, {v['no_space']['h2']:.3f} without; {ws['alphabet']} characters"))
    labels = [  # key, dx, dy, anchor, text
        ('voynich_ZL_raw', 10, 16, 'start', 'Voynich, EVA (ZL, RF1b, Takahashi)'),
        ('voynich_CD2a', 10, 14, 'start', 'Voynich, Currier'),
        ('voynich_ZL_merged', 10, -2, 'start', 'Voynich, merged glyphs'),
        ('voynich_GC2a', -8, 18, 'end', 'Voynich, v101'),
        ('toki_pona', 0, 20, 'middle', 'Toki Pona'),
        ('hawaiian', -9, 4, 'end', 'Hawaiian 1868'),
        ('gutenberg_la', -9, 4, 'end', 'Latin'),
    ]
    for key, dx, dy, anc, text in labels:
        v = c1['h2_conventions'][key]['with_space']
        o.append(f'<text class="lab" x="{X(v["alphabet"]) + dx:.1f}" y="{Y(v["h2"]) + dy:.1f}" text-anchor="{anc}">{esc(text)}</text>')
    haw = next(r for r in lb if r[1] == 'haw')
    o.append(f'<circle class="ring" cx="{X(int(haw[5])):.1f}" cy="{Y(float(haw[8])):.1f}" r="6"/>')
    o.append(f'<text class="lab" x="{X(int(haw[5])) + 8:.1f}" y="{Y(float(haw[8])) + 4:.1f}">Hawaiian, modern spelling</text>')
    o += legend([('circle', 's1', 'Voynich'), ('square', 's2', 'natural language, this study'),
                 ('triangle', 's3', 'constructed language'), ('circle', 'bg', 'Wikipedia, Lindemann & Bowern')], L, 22)
    o.append('</svg>')
    return '\n'.join(o), shown


# ------------------------------------------------------------------------------------- B: Zipf and hapax
def chart_zipf(c1, b3):
    rows = [  # (group, key, source, label)
        ('Voynich', 'voynich_ZL', 'c1', 'Voynich, all'), ('Voynich', 'voynich_A', 'b3', 'Voynich, Currier A'),
        ('Voynich', 'voynich_B', 'b3', 'Voynich, Currier B'),
        ('languages', 'latin', 'b3', 'Latin (Gutenberg)'), ('languages', 'italian', 'b3', 'Italian'),
        ('languages', 'english', 'b3', 'English'), ('languages', 'hawaiian', 'c1', 'Hawaiian 1868'),
        ('languages', 'maori', 'c1', 'Maori'), ('languages', 'swahili', 'c1', 'Swahili'),
        ('constructed', 'esperanto', 'c1', 'Esperanto'), ('constructed', 'toki_pona', 'c1', 'Toki Pona'),
        ('constructed', 'lojban', 'c1', 'Lojban'), ('constructed', 'volapuk', 'c1', 'Volapuk'),
        ('generators', 'random_glyphs', 'c1', 'random glyphs'), ('generators', 'markov1_latin', 'c1', 'Markov 1, Latin-trained'),
        ('generators', 'markov1_voynich', 'c1', 'Markov 1, Voynich-trained'), ('generators', 'markov3_voynich', 'c1', 'Markov 3, Voynich-trained'),
        ('generators', 'autocopist_s19', 'c1', 'autocopist (Timm-Schinner)'), ('generators', 'rugg_grille', 'b3', 'Rugg grille'),
        ('cipher', 'naibbe_pliny', 'b3', 'Naibbe cipher (Pliny)'), ('human gibberish', 'gaskell_gibberish', 'b3', 'Gaskell & Bowern'),
    ]
    src = {'c1': c1['short'], 'b3': b3['short']}
    real = c1['short']['voynich_ZL']; tol = c1['tol_short']
    W, L, R, T, rh = 760, 196, 16, 52, 17
    groups = []
    for g, *_ in rows:
        if g not in groups:
            groups.append(g)
    H = T + rh * len(rows) + 14 * len(groups) + 40
    panels = [('c_zipf', 'Zipf slope, ranks 1-1000', -2.4, -0.4, [-2.0, -1.5, -1.0, -0.5]),
              ('c_hapax_types', 'hapax share of word types', 0.0, 1.0, [0.0, 0.25, 0.5, 0.75, 1.0])]
    gap = 64; pw = (W - L - R - gap) / 2
    o = svg_open(W, H, 'Zipf slope and hapax share at 10,053 tokens: languages, constructed languages, Markov chains and '
                       'random glyphs all land near Voynichese on Zipf; human gibberish does not')
    for i, (key, title, d0, d1, ticks) in enumerate(panels):
        x0 = L + i * (pw + gap); X = lin(d0, d1, x0, x0 + pw)
        if i:
            o.append(f'<line class="axis" x1="{x0 - gap / 2:.1f}" x2="{x0 - gap / 2:.1f}" y1="{T - 24}" y2="{H - 40}"/>')
        lo, hi = real[key] - tol[key], real[key] + tol[key]
        o.append(f'<rect class="band" x="{X(lo):.1f}" y="{T - 6}" width="{X(hi) - X(lo):.1f}" height="{H - T - 34}"/>')
        o.append(f'<text class="ttl" x="{x0}" y="{T - 16}">{esc(title)}</text>')
        for t in ticks:
            o.append(f'<line class="grid" x1="{X(t):.1f}" x2="{X(t):.1f}" y1="{T - 6}" y2="{H - 40}"/>'
                     f'<text x="{X(t):.1f}" y="{H - 26}" text-anchor="middle">{t:g}</text>')
        y = T; last = None
        for g, k, s, lab in rows:
            if g != last:
                y += 14; last = g
            v = src[s][k][key]; inside = abs(v - real[key]) <= tol[key]
            cls = 's1' if g == 'Voynich' else 'ink'
            o.append(marker('circle', X(max(d0, min(d1, v))), y, cls, r=4.5, hollow=not inside,
                            tip=f'{lab}: {v:.3f} ({"inside" if inside else "outside"} the Voynich tolerance {lo:.3f} to {hi:.3f})'))
            y += rh
    y = T; last = None
    for g, k, s, lab in rows:
        if g != last:
            y += 14; last = g
            o.append(f'<text class="grp" x="8" y="{y - 9}">{esc(g)}</text>')
        o.append(f'<text class="lab" x="{L - 12}" y="{y + 4}" text-anchor="end">{esc(lab)}</text>')
        y += rh
    o += legend([('circle', 'ink', 'within the bake-off tolerance of Voynichese (shaded band)'),
                 ('circle-o', 'ink', 'outside it')], L, H - 6)
    o.append('</svg>')
    return '\n'.join(o)


# ------------------------------------------------------------------------------------- C: word length
def chart_wordlen(c1):
    series = [('voynich_ZL', 's1', 'Voynich'), ('markov1_voynich', 's2', 'Markov 1, Voynich-trained'),
              ('markov3_voynich', 's3', 'Markov 3, Voynich-trained'), ('gutenberg_la', 's4', 'Latin')]
    W, H, L, R, T, B = 760, 330, 52, 150, 30, 46
    X = lin(1, 15, L, W - R); Y = lin(0, 0.30, H - B, T)
    o = svg_open(W, H, 'Word-length distributions: an order-1 Markov chain gives geometric lengths, an order-3 chain trained '
                       'on Voynichese reproduces its peaked distribution, Latin is broader')
    for v in [0, 0.1, 0.2, 0.3]:
        o.append(f'<line class="grid" x1="{L}" x2="{W - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/>'
                 f'<text x="{L - 8}" y="{Y(v) + 4:.1f}" text-anchor="end">{int(v * 100)}%</text>')
    for v in range(1, 16, 2):
        o.append(f'<text x="{X(v):.1f}" y="{H - B + 16}" text-anchor="middle">{v}{"+" if v == 15 else ""}</text>')
    o.append(f'<line class="axis" x1="{L}" x2="{W - R}" y1="{H - B}" y2="{H - B}"/>')
    o.append(f'<text x="{(L + W - R) / 2:.0f}" y="{H - 10}" text-anchor="middle">word length in letters (15 = 15 or more)</text>')
    for key, cls, lab in series:
        h = c1['curves'][key]['len_hist']; pts = [(X(int(k)), Y(v)) for k, v in h.items()]
        o.append(f'<polyline class="{cls} line" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}"/>')
        for (k, v), (x, y) in zip(h.items(), pts):
            o.append(marker('circle', x, y, cls, r=3, tip=f'{lab}: length {k}, {v * 100:.1f}% of tokens'))
    ly = T + 10  # legend at the right, two lines per entry
    for key, cls, lab in series:
        o.append(f'<line class="{cls} line" x1="{W - R + 12}" x2="{W - R + 30}" y1="{ly - 4}" y2="{ly - 4}"/>'
                 f'<text class="lab" x="{W - R + 36}" y="{ly}">{esc(lab.split(",")[0])}</text>')
        if ',' in lab:
            ly += 13; o.append(f'<text class="lab" x="{W - R + 36}" y="{ly}">{esc(lab.split(",")[1].strip())}</text>')
        ly += 22
    o.append('</svg>')
    return '\n'.join(o)


# ------------------------------------------------------------------------------------- D: long-range
def chart_mz(c1, b3):
    series = [('voynich_ZL', c1['mz_curves']['voynich_ZL'], 's1', 'Voynich'),
              ('latin', b3['extra_full']['latin']['mz_curve'], 's2', 'Latin'),
              ('autocopist_s19', c1['mz_curves']['autocopist_s19'], 's3', 'autocopist'),
              ('naibbe_pliny', b3['extra_full']['naibbe_pliny']['mz_curve'], 's4', 'Naibbe cipher'),
              ('markov3_voynich', c1['mz_curves']['markov3_voynich'], 's5', 'Markov 3')]
    W, H, L, R, T, B = 760, 320, 52, 120, 24, 46
    X = lin(4, 11, L, W - R); Y = lin(-0.02, 0.62, H - B, T)
    o = svg_open(W, H, 'Long-range word clustering: Voynichese has more of it than Latin; the Naibbe cipher and a Markov chain have none')
    for v in [0, 0.2, 0.4, 0.6]:
        o.append(f'<line class="grid" x1="{L}" x2="{W - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/>'
                 f'<text x="{L - 8}" y="{Y(v) + 4:.1f}" text-anchor="end">{v:.1f}</text>')
    for e in range(4, 12):
        o.append(f'<text x="{X(e):.1f}" y="{H - B + 16}" text-anchor="middle">{2 ** e}</text>')
    o.append(f'<line class="axis" x1="{L}" x2="{W - R}" y1="{Y(0):.1f}" y2="{Y(0):.1f}"/>')
    o.append(f'<text x="{(L + W - R) / 2:.0f}" y="{H - 10}" text-anchor="middle">block size in tokens</text>')
    o.append(f'<text x="14" y="{(T + H - B) / 2:.0f}" text-anchor="middle" transform="rotate(-90 14 {(T + H - B) / 2:.0f})">bits, real minus shuffled</text>')
    ends = []
    for key, curve, cls, lab in series:
        pts = sorted((math.log2(int(s)), d['R']) for s, d in curve.items())
        o.append(f'<polyline class="{cls} line" points="{" ".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in pts)}"/>')
        for a, b in pts:
            o.append(marker('circle', X(a), Y(b), cls, r=3, tip=f'{lab}: block {2 ** int(a)} tokens, {b:.3f} bits'))
        ends.append([Y(pts[-1][1]) + 4, lab, X(pts[-1][0]) + 8])
    ends.sort(reverse=True)  # bottom first; push each label at least 13 px above the one below
    for i in range(1, len(ends)):
        ends[i][0] = min(ends[i][0], ends[i - 1][0] - 13)
    for y, lab, x in ends:
        o.append(f'<text class="lab" x="{x:.1f}" y="{y:.1f}">{esc(lab)}</text>')
    o.append('</svg>')
    return '\n'.join(o)


# ------------------------------------------------------------------------------------- E: bake-off grid
def chart_grid(c1, b3):
    items = b3['meta']['items']; groups = 'abcdefghijk'
    rows = [(n, b3['marks_full'][n], 'b3') for n in b3['marks_full']]
    rows += [(n, c1['marks_full'][n], 'c1') for n in c1['marks_full'] if n not in b3['marks_full']]
    names = {'voynich_ZL': 'Voynich, all', 'voynich_A': 'Voynich, Currier A', 'voynich_B': 'Voynich, Currier B',
             'latin': 'Latin (Gutenberg)', 'italian': 'Italian letters (OCR)', 'english': 'English',
             'autocopist_s19': 'autocopist, seed 19', 'autocopist_s7': 'autocopist, seed 7', 'rugg_grille': 'Rugg grille',
             'rugg_sorted': 'Rugg sorted table', 'naibbe_pliny': 'Naibbe, Pliny', 'naibbe_pliny_lines': 'Naibbe, Pliny, own lines',
             'naibbe_divcom': 'Naibbe, Dante', 'gaskell_gibberish': 'human gibberish (cycled)', 'hawaiian': 'Hawaiian 1868',
             'tongan': 'Tongan', 'maori': 'Maori', 'setswana': 'Setswana', 'swahili': 'Swahili', 'latin_vulgate': 'Latin Vulgate',
             'esperanto': 'Esperanto', 'toki_pona': 'Toki Pona', 'lojban': 'Lojban',
             'markov1_voynich': 'Markov 1, Voynich-trained', 'markov2_voynich': 'Markov 2, Voynich-trained',
             'markov3_voynich': 'Markov 3, Voynich-trained', 'markov1_latin': 'Markov 1, Latin-trained',
             'markov3_latin': 'Markov 3, Latin-trained', 'random_glyphs': 'random glyphs'}
    W, L, T, cw, rh = 760, 190, 40, 13, 15
    H = T + rh * len(rows) + 24
    o = svg_open(W, H, 'Bake-off grid: which of the 37 battery items each corpus matches within tolerance of Voynichese')
    x = L; last = None
    for key, lab in items:
        g = key[0]
        if g != last:
            if last:
                x += 4
            o.append(f'<text class="ttl" x="{x + 2}" y="{T - 10}">{g}</text>'); last = g
        o.append(f'<g><title>{esc(key)}: {esc(lab)}</title><rect class="hit" x="{x}" y="{T - 22}" width="{cw}" height="16"/></g>')
        x += cw
    for i, (n, marks, s) in enumerate(rows):
        y = T + i * rh; x = L; last = None
        lab = names.get(n, n.replace('_', ' '))
        o.append(f'<text class="lab" x="{L - 8}" y="{y + 11}" text-anchor="end">{esc(lab)}</text>'
                 f'<text x="{L + 37 * cw + 40 + 6:.0f}" y="{y + 11}">{sum(marks.values())}/37</text>')
        for key, ilab in items:
            if key[0] != last:
                if last:
                    x += 4
                last = key[0]
            ok = marks[key]
            o.append(f'<rect class="{"cell on" if ok else "cell"}" x="{x + 1}" y="{y + 1}" width="{cw - 2}" height="{rh - 2}" rx="2">'
                     f'<title>{esc(lab)} - {esc(ilab)}: {"matches" if ok else "does not match"}</title></rect>')
            x += cw
    o.append('</svg>')
    return '\n'.join(o)


def put(page, name, svg):
    pat = re.compile(r'(<!-- vchart:%s -->)(.*?)(<!-- /vchart:%s -->)' % (name, name), re.S)
    if not pat.search(page):
        print('marker missing:', name); return page
    return pat.sub(lambda m: m.group(1) + '\n' + svg + '\n' + m.group(3), page)


def main():
    c1 = load('c1.json'); b3 = load('b3.json'); c3 = load('c3.json')
    page = open(PAGE, encoding='utf-8').read()
    svg, shown = chart_h2(c1); page = put(page, 'h2', svg); print('h2 scatter: Wikipedia points shown', shown)
    page = put(page, 'zipf', chart_zipf(c1, b3))
    page = put(page, 'wordlen', chart_wordlen(c1))
    page = put(page, 'mz', chart_mz(c1, b3))
    page = put(page, 'grid', chart_grid(c1, b3))
    if c3:
        import c3_period
        page = put(page, 'period', c3_period.chart(c3))
    open(PAGE, 'w', encoding='utf-8').write(page)


if __name__ == '__main__':
    main()
