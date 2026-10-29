"""Cross-boundary dependence in Voynichese: does the end of one word predict the start of the next, and is that an
artefact of doubtful word breaks?

Reads the raw IVTFF file (ZL3b-n.txt, path argv[1]) and keeps, for every pair of adjacent words inside a paragraph
line, the kind of separator between them: '.' (certain space), ',' (uncertain space) or '<->' (drawing gap). Inline
comments are removed, alternatives [a:b] read as a, ligature braces opened (as parse_ivtff --fixed). Words with '?',
'@' or non-letters are dropped together with the pairs they belong to. The first and last word of each line are
excluded (line-position effects); the null shuffles the interior words of each line.

X1 = [I(last unit of w_t; first unit of w_t+1) - mean over 10 shuffles] / H(first unit), for:
  all pairs; certain-space pairs only; uncertain-space pairs only; and by Currier language.
Also the same for a few unit definitions (raw last/first EVA letter; glyph units) and a lag-2 control (w_t, w_t+2).

Run from the repository root: python research/voynich_siblings/cross_boundary.py <ZL3b-n.txt>
"""
import collections, math, os, random, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import slot_independence as si

SEED = 31


def H(c):
    n = sum(c.values())
    return -sum(v / n * math.log2(v / n) for v in c.values() if v)


def mi(pairs):
    return H(collections.Counter(a for a, _ in pairs)) + H(collections.Counter(b for _, b in pairs)) - H(collections.Counter(pairs))


def parse(path):
    meta, lines = {}, []
    for raw in open(path, encoding='utf-8', errors='replace'):
        raw = raw.rstrip('\n')
        if raw.startswith('#') or not raw.strip():
            continue
        m = re.match(r'<(f\d+[rv]\d?|[a-z]\w*)>\s*<!([^>]*)>', raw)
        if m and '.' not in m.group(1):
            meta[m.group(1)] = dict(re.findall(r'\$(\w)=(\w+)', m.group(2))); continue
        m = re.match(r'<(f\d+[rv]\d?|\w+)\.(\d+),([@+*=])([A-Za-z])(\w*)>\s*(.*)$', raw)
        if not m or m.group(4) != 'P':
            continue
        folio, text = m.group(1), m.group(6)
        t = re.sub(r'<![^>]*>', '', text).replace('<->', '|')
        t = re.sub(r'<[^>]*>', '', t)
        t = re.sub(r'\{([^}]*)\}', lambda x: x.group(1).replace("'", ''), t)
        t = re.sub(r'\[([^\]:]*):[^\]]*\]', r'\1', t)
        toks = re.split(r'([.,|])', t)
        words, seps = [], []
        for i, x in enumerate(toks):
            if x in '.,|' and x:
                seps.append(x)
            elif x:
                words.append(x)
        # seps[i] lies between words[i] and words[i+1] when the string alternates word/sep
        ok = len(seps) == len(words) - 1
        if not ok:
            continue
        lines.append((meta.get(folio, {}).get('L', '?'), words, seps))
    return lines


def good(w):
    return re.fullmatch(r'[a-z]+', w) is not None


def pairs_of(lines, unit, kinds, lag=1):
    out = []
    for lang, ws, ss in lines:
        n = len(ws)
        for i in range(1, n - 1 - lag):
            j = i + lag
            if j > n - 2:
                break
            if lag == 1 and ss[i] not in kinds:
                continue
            a, b = ws[i], ws[j]
            if good(a) and good(b):
                out.append((unit(a)[-1], unit(b)[0]))
    return out


def shuffle_lines(lines, rng):
    out = []
    for lang, ws, ss in lines:
        inner = ws[1:-1]; rng.shuffle(inner)
        out.append((lang, ws[:1] + inner + ws[-1:] if len(ws) > 1 else ws, ss))
    return out


def x1(lines, unit, kinds, rng, lag=1, reps=10):
    obs = mi(pairs_of(lines, unit, kinds, lag))
    base = sum(mi(pairs_of(shuffle_lines(lines, rng), unit, kinds, lag)) for _ in range(reps)) / reps
    firsts = collections.Counter(unit(w)[0] for _, ws, _ in lines for w in ws if good(w))
    return (obs - base) / H(firsts), len(pairs_of(lines, unit, kinds, lag))


def main():
    rng = random.Random(SEED)
    lines = parse(sys.argv[1])
    sepc = collections.Counter(s for _, _, ss in lines for s in ss)
    print(f'paragraph lines {len(lines)}; separators: {dict(sepc)}')
    units = {'glyph units': si.eva_units, 'raw EVA letters': list}
    for uname, u in units.items():
        for label, kinds in [('all separators', '.,|'), ('certain spaces only (.)', '.'), ('uncertain spaces only (,)', ','), ('drawing gaps only (<->)', '|')]:
            v, n = x1(lines, u, kinds, rng)
            print(f'{uname:16s} {label:28s} X1 = {v:.4f}  ({n} pairs)')
        for lang in 'AB':
            sub = [l for l in lines if l[0] == lang]
            v, n = x1(sub, u, '.', rng)
            print(f'{uname:16s} Currier {lang}, certain spaces      X1 = {v:.4f}  ({n} pairs)')
        v, n = x1(lines, u, '.,|', rng, lag=2)
        print(f'{uname:16s} lag 2 (w_t, w_t+2)            X1 = {v:.4f}  ({n} pairs)')


if __name__ == '__main__':
    main()
