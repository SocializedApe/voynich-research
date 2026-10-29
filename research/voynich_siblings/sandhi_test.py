"""Where does Voynich's edge coupling live? A test of the 'boundary spelling' (sandhi) model on the real text.

cipher_models.py reproduces the edge coupling with a rule that writes a short prefix (qo, o, q, y, ch, d ...) before
a word according to the last glyph of the previous word. If Voynich works that way, the coupling between the last
glyph of w_t and the opening of w_t+1 should sit in a detachable opening element; once it is stripped, the rest of
w_t+1 should be (nearly) independent of w_t.

For every interior pair on certain spaces (as cross_boundary.py), the opening of w_t+1 is split into
  OPEN = the longest of ('qo', 'q', 'o', 'y', 'd', 's') that leaves at least two glyph units, else ''
  CORE = the first glyph unit after OPEN
and the dependence of each on the last glyph unit of w_t is measured (MI minus within-line-shuffle MI, normalised by
the entropy of the measured element). Same for the sandhi model's own output (positive control: it must show the
coupling in OPEN) and for Latin (negative control).

Run from the repository root: python research/voynich_siblings/sandhi_test.py <ZL3b-n.txt> <naibbe_tables.csv>
"""
import collections, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import slot_independence as si
import cross_boundary as cb
import cipher_models as cm
import code_vs_generator as cg
import a4_selfcitation as a4

OPENERS = ['qo', 'q', 'o', 'y', 'd', 's']


def split(w):
    u = si.eva_units(w)
    for op in OPENERS:
        ou = si.eva_units(op)
        if u[:len(ou)] == ou and len(u) - len(ou) >= 2:
            return op, u[len(ou)]
    return '', u[0]


def measure(lines, rng, reps=10):
    """lines: list of word lists. Returns normalised dependence of OPEN and CORE on the previous last unit."""
    def pairs(L):
        out = []
        for ws in L:
            inner = ws[1:-1]
            for a, b in zip(inner, inner[1:]):
                op, core = split(b)
                out.append((si.eva_units(a)[-1], op, core))
        return out
    def mis(P):
        return cg.mi([(x, o) for x, o, _ in P]), cg.mi([(x, c) for x, _, c in P])
    o_obs, c_obs = mis(pairs(lines))
    o_b = c_b = 0
    for _ in range(reps):
        a, b = mis(pairs(cg.shuffled_lines([l[:] for l in lines], rng))); o_b += a; c_b += b
    P = pairs(lines)
    ho = cg.H(collections.Counter(o for _, o, _ in P)); hc = cg.H(collections.Counter(c for _, _, c in P))
    share = sum(1 for _, o, _ in P if o) / len(P)
    return (o_obs - o_b / reps) / ho, (c_obs - c_b / reps) / hc, share


def main():
    rng = random.Random(61)
    raw = cb.parse(sys.argv[1])
    vl = []
    for lang, ws, ss in raw:   # keep runs of good words joined by certain spaces only
        run = [ws[0]]
        for w, s in zip(ws[1:], ss):
            if s == '.' and cb.good(w) and cb.good(run[-1]):
                run.append(w)
            else:
                if len(run) >= 3: vl.append(run)
                run = [w]
        if len(run) >= 3: vl.append(run)
    zl = a4.load_zl(); skel = a4.skeleton(zl)
    lat = os.path.join(HERE, '..', '..', 'lang', 'corpora', 'la-gutenberg.txt')
    model = cm.generate(cm.Variant(sys.argv[2], 19, drift=True, k_page=2, merge=0.1, sandhi=0.25, nulls=0.1, null_set=8), lat, skel)
    naib = cm.generate(cm.Variant(sys.argv[2], 19), lat, skel)
    latin = cg.lines_of(a4.pour(si.corpus('Latin')[:40000], skel))
    print(f'{"text":34s} {"OPEN dep":>9s} {"CORE dep":>9s} {"share with OPEN":>15s}')
    for name, L in [('Voynich (certain spaces)', vl), ('sandhi model (best fit)', cg.lines_of(model)),
                    ('Naibbe', cg.lines_of(naib)), ('Latin (letters as units)', latin)]:
        o, c, sh = measure(L, rng)
        print(f'{name:34s} {o:9.4f} {c:9.4f} {sh:15.3f}', flush=True)


if __name__ == '__main__':
    main()
