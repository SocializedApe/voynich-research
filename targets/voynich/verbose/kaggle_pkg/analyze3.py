"""Decision rule for tier 3 (abbreviated Latin), fixed before any tier-3 result (29 Oct 2026).

Per (text, variant, K) and part, the seed with the best objective is kept.
  stability      = agreement of the keys solved on the two halves h1, h2 (weighted by unit counts, as analyze.py)
  null stability = the same for the two halves s1, s2 of the shuffled stream: the chance level, measured
  degenerate     = letter KL of the full decryption to abbreviated Latin > 0.15
K chosen blind per (text, variant): the non-degenerate full run with the best per-character score.
Calibration (syn_gate4, abbreviated Pliny under a gate-3 cipher) must pass: similarity >= 0.8 and stability - null
  >= 0.3 at its chosen K. Its per-character score sets the threshold: PC* = calibration per-char - 0.25 (abbreviated
  text has its own score scale, so the -2.2 of the earlier rule does not carry over).
SIGNAL for a Voynich (text, variant) if, at its chosen K: per-char >= PC*, not degenerate, stability >= 0.5 and
  stability - null >= 0.3. If the calibration fails, no Voynich cell is interpreted.
Also printed: diagnostics for every cell, whatever the verdict.

Run: python analyze3.py [results_dir]
"""
import collections, glob, json, os, sys
from analyze import stability


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
    rows = [json.loads(l) for p in glob.glob(os.path.join(d, '*.jsonl')) for l in open(p, encoding='utf-8')]
    rows = [r for r in rows if r['lang'] == 'lab']
    best = {}
    for r in rows:
        k = (r['text'], r['variant'], r['K'], r['part'])
        if k not in best or r['objective'] > best[k]['objective']: best[k] = r
    def cell(t, v, K):
        f = best.get((t, v, K, 'full')); g = lambda p: best.get((t, v, K, p))
        st = stability(g('h1')['key'], g('h2')['key'], g('h1')['unit_counts'], g('h2')['unit_counts']) if g('h1') and g('h2') else float('nan')
        nu = stability(g('s1')['key'], g('s2')['key'], g('s1')['unit_counts'], g('s2')['unit_counts']) if g('s1') and g('s2') else float('nan')
        return f, st, nu
    def chosen(t, v):
        Ks = sorted({k[2] for k in best if k[0] == t and k[1] == v})
        c = [(best[(t, v, K, 'full')]['per_char'], K) for K in Ks if (t, v, K, 'full') in best and best[(t, v, K, 'full')]['kl'] <= 0.15]
        return max(c)[1] if c else None
    print(f'{len(rows)} tier-3 results')
    K = chosen('syn_gate4', 'raw')
    if K is None: print('CALIBRATION FAILS: every syn_gate4 run degenerate'); cal_ok = False; pcs = float('nan')
    else:
        f, st, nu = cell('syn_gate4', 'raw', K)
        cal_ok = f.get('similarity', 0) >= 0.8 and st - nu >= 0.3; pcs = f['per_char'] - 0.25
        print(f'calibration syn_gate4: K {K}, per-char {f["per_char"]:.3f}, KL {f["kl"]:.3f}, similarity {f.get("similarity", 0):.3f}, '
              f'stability {st:.2f} (null {nu:.2f}) -> {"PASS" if cal_ok else "FAIL"}; threshold PC* = {pcs:.3f}')
    print('\n| text | variant | K | per-char | KL | stability | null | verdict (chosen K only) |\n|---|---|---|---|---|---|---|---|')
    for t, v in sorted({(k[0], k[1]) for k in best}):
        ck = chosen(t, v)
        for K in sorted({k[2] for k in best if k[0] == t and k[1] == v}):
            f, st, nu = cell(t, v, K)
            if not f: continue
            verdict = ''
            if K == ck and t != 'syn_gate4':
                ok = cal_ok and f['per_char'] >= pcs and f['kl'] <= 0.15 and st >= 0.5 and st - nu >= 0.3
                verdict = 'SIGNAL' if ok else 'no signal'
            elif ck is None and t != 'syn_gate4' and K == max(k[2] for k in best if k[0] == t and k[1] == v): verdict = 'all degenerate'
            print(f'| {t} | {v} | {K} | {f["per_char"]:.3f} | {f["kl"]:.3f} | {st:.2f} | {nu:.2f} | {verdict} |')


if __name__ == '__main__':
    main()
