"""Decision rule for tier 5 (nomenclator layer): the tier-4 rule unchanged, with syn_gate7 as the calibration
(written 11 Nov 2026 before any tier-5 result). Text of the tier-4 rule follows.

Decision rule for tier 4 (positional units), fixed before any tier-4 result (29 Oct 2026).

Changes from analyze3.py, both motivated by the tier-3 calibration:
  - Key stability is judged as its excess over the measured chance level, normalised:
      norm = (stability - null) / (1 - null), with null = stability of the two halves of the shuffled stream.
    Tier 3 showed a null of 0.72-0.89, so the raw margin of 0.3 asked for more than a perfect solution can give.
    (On the tier-3 numbers: gate 4 0.96; every Voynich cell negative.)
  - The per-character threshold comes from the Latin calibration (syn_gate7) and applies to every language:
      PC* = calibration per-char - 0.25 (Latin, Italian and German letter models score solved text in a similar range,
      -1.9 to -2.1; abbreviated Latin solved -2.08 in tier 3).
Per (text, lang, K) and part, the seed with the best objective is kept. K is chosen blind per (text, lang): the
non-degenerate (letter KL <= 0.15) full run with the best per-character score.
Calibration passes if syn_gate7 at its chosen K reaches similarity >= 0.8 and norm >= 0.5; otherwise no Voynich cell
is interpreted. A Voynich (text, lang) is SIGNAL if at its chosen K: per-char >= PC*, KL <= 0.15, norm >= 0.5.
Diagnostics for every cell are printed whatever the verdict.

Run: python analyze5.py [results_dir]
"""
import glob, json, os, sys
from analyze import stability


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
    rows = [json.loads(l) for p in glob.glob(os.path.join(d, '*.jsonl')) for l in open(p, encoding='utf-8')]
    rows = [r for r in rows if r['variant'] == 'nom']
    best = {}
    for r in rows:
        k = (r['text'], r['lang'], r['K'], r['part'])
        if k not in best or r['objective'] > best[k]['objective']: best[k] = r
    def st(t, l, K, a, b):
        x, y = best.get((t, l, K, a)), best.get((t, l, K, b))
        return stability(x['key'], y['key'], x['unit_counts'], y['unit_counts']) if x and y else float('nan')
    def cell(t, l, K):
        s, n = st(t, l, K, 'h1', 'h2'), st(t, l, K, 's1', 's2')
        return best.get((t, l, K, 'full')), s, n, ((s - n) / (1 - n) if n == n and n < 1 else float('nan'))
    def chosen(t, l):
        c = [(best[(t, l, K, 'full')]['per_char'], K) for K in sorted({k[2] for k in best if k[:2] == (t, l)})
             if (t, l, K, 'full') in best and best[(t, l, K, 'full')]['kl'] <= 0.15]
        return max(c)[1] if c else None
    print(f'{len(rows)} tier-5 results')
    K = chosen('syn_gate7', 'lan'); cal_ok = False; pcs = float('nan')
    if K is None: print('CALIBRATION FAILS: every syn_gate7 run degenerate')
    else:
        f, s, n, nm = cell('syn_gate7', 'lan', K)
        cal_ok = f.get('similarity', 0) >= 0.8 and nm >= 0.5; pcs = f['per_char'] - 0.25
        print(f'calibration syn_gate7: K {K}, per-char {f["per_char"]:.3f}, KL {f["kl"]:.3f}, similarity {f.get("similarity", 0):.3f}, '
              f'stability {s:.2f}, null {n:.2f}, normalised {nm:.2f} -> {"PASS" if cal_ok else "FAIL"}; threshold PC* = {pcs:.3f}')
    print('\n| text | lang | K | per-char | KL | stability | null | normalised | verdict (chosen K) |\n|---|---|---|---|---|---|---|---|---|')
    for t, l in sorted({k[:2] for k in best}):
        ck = chosen(t, l)
        Ks = sorted({k[2] for k in best if k[:2] == (t, l)})
        for K in Ks:
            f, s, n, nm = cell(t, l, K)
            if not f: continue
            v = ''
            if t != 'syn_gate7':
                if K == ck: v = 'SIGNAL' if (cal_ok and f['per_char'] >= pcs and f['kl'] <= 0.15 and nm >= 0.5) else 'no signal'
                elif ck is None and K == Ks[-1]: v = 'all degenerate'
            sim = f' (sim {f["similarity"]:.3f})' if 'similarity' in f else ''
            print(f'| {t} | {l} | {K} | {f["per_char"]:.3f}{sim} | {f["kl"]:.3f} | {s:.2f} | {n:.2f} | {nm:.2f} | {v} |')


if __name__ == '__main__':
    main()
