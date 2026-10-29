"""c3_period.py -- real 14th-15th-century ciphertexts from this repository's own targets against Voynichese.

Question: does any cipher system actually in use when the Voynich vellum was prepared (1404-1438) produce the
low conditional character entropy of Voynichese?  RBA (Sept 2026) argued that period cryptography (Alberti 1467,
nomenclators) raises h2; this measures it on real ciphertexts instead of arguing it.

Data: data/period/<target>.json, extracted by data/period/_extract.py from the targets' own transcriptions
(sign tokens per line; '|' = word divider written by the cipherer, 'N:' = nomenclator/code sign, '0:' = null).

Measures, all without spaces (most of these ciphers write no word division):
  h1, h2 of the sign stream as written (dividers removed), inventory size;
  the same for the plaintext reading of the same passages, where one exists (letters only);
  size-matched references, because plug-in h2 falls with sample length and rises with inventory: for each target's
  length n, 300 random contiguous windows of n symbols from Voynich ZL (raw EVA and merged glyphs), Latin and Italian,
  giving mean and 5-95% range.  The estimator is the same everywhere, so the comparison at equal n is fair; the
  bias is larger for bigger inventories, which makes the ciphers look lower, not higher.
Writes results/c3.json and results/c3.md, and provides chart() for c2_charts.py.
"""
import collections, glob, json, math, os, random, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a4_selfcitation as a4

OUT = os.path.join(HERE, 'results')
PERIOD = os.path.join(HERE, 'data', 'period')
MERGE2 = ["ckh", "cth", "cph", "cfh", "ch", "sh", "iiin", "iin", "eee", "ee", "aiin", "ain", "in", "qo"]
SEED = 1421
CHART_MIN = 250  # shorter texts stay in the table; at a few dozen signs every h2 is dominated by sample size
NICE = {'siena1421_no14': 'Siena no. 14', 'siena1421_no07': 'Siena no. 7', 'siena1421_no11': 'Siena no. 11',
        'siena1421_no25': 'Siena no. 25', 'siena1421_no06_24': 'Siena nos. 6, 24', 'siena1421_no20_23': 'Siena nos. 20-23',
        'r1854_p1': 'Mantua R1854 p. 1', 'r1854_p2': 'Mantua R1854 p. 2', 'r1854_p3': 'Mantua R1854 p. 3',
        'r1854_p4p5': 'Mantua R1854 pp. 4-5', 'it1583_f68': 'Sforza, BnF it. 1583 f. 68', 'it1583_f70': 'Sforza, BnF it. 1583 f. 70',
        'buda1489': 'Buda, to Milan'}


def H(c):
    n = sum(c); return -sum(v / n * math.log2(v / n) for v in c if v)


def h12(sym):
    pairs = collections.Counter(zip(sym, sym[1:])); first = collections.Counter()
    for (x, _), v in pairs.items():
        first[x] += v
    return H(collections.Counter(sym).values()), H(pairs.values()) - H(first.values()), len(set(sym))


def tok_merge2(w):
    out = []; i = 0
    while i < len(w):
        for s in sorted(MERGE2, key=len, reverse=True):
            if w.startswith(s, i):
                out.append(s); i += len(s); break
        else:
            out.append(w[i]); i += 1
    return out


def windows(stream, n, rng, k=300):
    if n >= len(stream):
        return [h12(stream)[1]]
    vals = []
    for _ in range(k):
        i = rng.randrange(0, len(stream) - n); vals.append(h12(stream[i:i + n])[1])
    return vals


def summary(vals):
    v = sorted(vals); q = lambda p: v[min(len(v) - 1, int(p * len(v)))]
    return {'mean': sum(v) / len(v), 'p05': q(0.05), 'p95': q(0.95)}


def main():
    zl = a4.load_zl(); words = [w for p in zl for ln in p['lines'] for w in ln['words']]
    refs = {'voynich_raw': [c for w in words for c in w],
            'voynich_merged': [s for w in words for s in tok_merge2(w)],
            'latin': [c for w in a4.lang_words('la', 34116) for c in w],
            'italian': [c for w in a4.lang_words('it', 34116) for c in w]}
    rng = random.Random(SEED); rows = []
    for path in sorted(glob.glob(os.path.join(PERIOD, '*.json'))):
        d = json.load(open(path, encoding='utf-8'))
        sym = [t for line in d['lines'] for t in line if t != '|']
        if len(sym) < 40:
            continue
        h1, h2, inv = h12(sym)
        cav = ' '.join(d.get('caveats') or []) if isinstance(d.get('caveats'), list) else str(d.get('caveats') or '')
        row = {'target': d.get('dataset') or os.path.basename(path)[:-5], 'folder': d['target'], 'date': d.get('date'),
               'year': d.get('year'), 'reconstructed': 'RECONSTRUCTED' in cav.upper() or 'reconstructed' in str(d.get('date_basis', '')), 'system': d.get('system'), 'n': len(sym), 'inventory': inv,
               'h1': h1, 'h2': h2, 'h2_over_log2inv': h2 / math.log2(inv) if inv > 1 else None,
               'codes': sum(1 for t in sym if t.startswith('N:')), 'nulls': sum(1 for t in sym if t.startswith('0:'))}
        letters = [t for t in sym if not t.startswith(('N:', '0:'))]
        if len(letters) >= 40 and len(letters) < len(sym):
            row['letters_only'] = dict(zip(('h1', 'h2', 'inventory'), h12(letters)), n=len(letters))
        pt = re.sub(r'[^a-z]', '', (d.get('plaintext') or '').lower())
        if len(pt) >= 40:
            p1, p2, pinv = h12(list(pt)); row['plaintext'] = {'n': len(pt), 'h1': p1, 'h2': p2, 'inventory': pinv}
        row['refs'] = {k: summary(windows(s, len(sym), rng)) for k, s in refs.items()}
        rows.append(row)
        print(f"{d['target']:16s} n={len(sym):5d} inv={inv:3d} h2={h2:.3f}  voynich raw {row['refs']['voynich_raw']['mean']:.3f} "
              f"merged {row['refs']['voynich_merged']['mean']:.3f} latin {row['refs']['latin']['mean']:.3f}"
              + (f"  plaintext {row['plaintext']['h2']:.3f}" if 'plaintext' in row else ''))
    rows.sort(key=lambda r: (r['year'] is None, r['year'] or 0, r['target']))
    json.dump({'seed': SEED, 'rows': rows}, open(os.path.join(OUT, 'c3.json'), 'w', encoding='utf-8'), indent=1)
    L = ['# c3: real 14th-15th-century ciphertexts against Voynichese (no spaces, size-matched)', '',
         'Script `c3_period.py`; data `data/period/` (README there).  Reference columns: mean (5-95%) of 300 random windows '
         'of the same length.  All output unvalidated until reviewed.', '',
         '| target | date | signs | inventory | cipher h2 | plaintext h2 | Voynich EVA h2 | Voynich merged h2 | Latin h2 | Italian h2 |',
         '|---|---|---|---|---|---|---|---|---|---|']
    f = lambda s: f"{s['mean']:.2f} ({s['p05']:.2f}-{s['p95']:.2f})"
    for r in rows:
        L.append(f"| {r['target']} | {r['date']} | {r['n']} | {r['inventory']} | {r['h2']:.2f} | "
                 f"{r['plaintext']['h2']:.2f} | " if 'plaintext' in r else f"| {r['target']} | {r['date']} | {r['n']} | {r['inventory']} | {r['h2']:.2f} | - | ")
        L[-1] += f"{f(r['refs']['voynich_raw'])} | {f(r['refs']['voynich_merged'])} | {f(r['refs']['latin'])} | {f(r['refs']['italian'])} |"
    L += ['', f'The chart on the site shows rows with at least {CHART_MIN} signs that were transcribed from the manuscript '
          '(benedict1399 is re-enciphered from the printed plaintext with a rebuilt key, so it is left out).', '', 'Systems:', ''] + [f"- {r['target']}: {r['system']}" for r in rows]
    open(os.path.join(OUT, 'c3.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')


def chart(c3):
    """Dot plot for c2_charts.py: one row per ciphertext; Voynich and Latin windows of the same length as ranges."""
    import c2_charts as c2
    rows = [r for r in c3['rows'] if r['n'] >= CHART_MIN and not r['reconstructed']]; W, L, R, T, rh = 760, 210, 20, 44, 30
    H = T + rh * len(rows) + 46
    X = c2.lin(0.5, 5.5, L, W - R)
    o = c2.svg_open(W, H, 'Real 15th-century ciphertexts have conditional entropy far above Voynichese at the same length')
    for v in range(1, 6):
        o.append(f'<line class="grid" x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{T - 10}" y2="{H - 40}"/>'
                 f'<text x="{X(v):.1f}" y="{H - 26}" text-anchor="middle">{v}</text>')
    o.append(f'<text x="{(L + W - R) / 2:.0f}" y="{H - 8}" text-anchor="middle">h2 without spaces, bits per sign, at each text&#8217;s own length</text>')
    for i, r in enumerate(rows):
        y = T + i * rh + 10
        when = (('c. ' if 'c.' in str(r['date']) else '') + str(r['year'])) if r['year'] else 'undated'
        name = NICE.get(r['target'], r['target'].replace('_', ' '))
        o.append(f'<text class="lab" x="{L - 12}" y="{y + 4}" text-anchor="end">{c2.esc(name)} ({when})</text>'
                 f'<text x="{L - 12}" y="{y + 16}" text-anchor="end">{r["n"]} signs, {r["inventory"]} kinds</text>')
        for key, cls in (('voynich_raw', 's1'), ('latin', 's2')):
            s = r['refs'][key]
            o.append(f'<line class="{cls} line" x1="{X(s["p05"]):.1f}" x2="{X(s["p95"]):.1f}" y1="{y}" y2="{y}" stroke-opacity=".55"/>')
            o.append(c2.marker('circle', X(s['mean']), y, cls, r=3.5, tip=f"{key.replace('_', ' ')} windows of {r['n']}: mean {s['mean']:.2f}, 5-95% {s['p05']:.2f}-{s['p95']:.2f}"))
        if 'plaintext' in r:
            o.append(c2.marker('square', X(r['plaintext']['h2']), y, 's4', r=4, tip=f"plaintext reading: h2 {r['plaintext']['h2']:.2f} ({r['plaintext']['n']} letters)"))
        o.append(c2.marker('diamond', X(r['h2']), y, 's3', r=5, tip=f"ciphertext: h2 {r['h2']:.2f}, {r['n']} signs, {r['inventory']} kinds"))
    o += c2.legend([('diamond', 's3', 'ciphertext'), ('square', 's4', 'its plaintext'), ('circle', 's1', 'Voynich, same length'),
                    ('circle', 's2', 'Latin, same length')], L, 20)
    o.append('</svg>')
    return '\n'.join(o)


if __name__ == '__main__':
    main()
