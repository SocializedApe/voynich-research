"""Tier 6: how much copying noise does the tier-5 solver survive? Rule written before any tier-6 result (11 Nov 2026).

The calibration cipher of tier 5 (syn_gate7: Pliny under a verbose letter cipher with a 12-word nomenclator) is
re-run with copying noise (sweep.noisy): glyphs miscopied at 2, 5, 10, 20%, word breaks moved at 5, 15%, both at 5%.
A noise level is 'detected' if the noisy cipher would have been reported as SIGNAL by the tier-5 rule, with the
tier-5 threshold unchanged: at the chosen K (best per-char among K with letter KL <= 0.15), per-char >= PC* (the
clean calibration per-char - 0.25, from the tier-5 results), KL <= 0.15 and normalised half-to-half stability >= 0.5.
Similarity to the true plaintext is reported beside it (it cannot reach 1 once glyphs are miscopied).
The 'no signal' of tier 5 on Voynich then reads: no such cipher with copying noise up to the highest detected level.

Run: python analyze6.py <tier-6 results dir> <tier-5 results dir>
"""
import glob, json, os, sys
from analyze import stability


def load(d):
    rows = [json.loads(l) for p in glob.glob(os.path.join(d, '*.jsonl')) for l in open(p, encoding='utf-8')]
    best = {}
    for r in rows:
        if r['variant'] != 'nom': continue
        k = (r['text'], r['lang'], r['K'], r['part'])
        if k not in best or r['objective'] > best[k]['objective']: best[k] = r
    return best


def main():
    best = load(sys.argv[1]); cal = load(sys.argv[2])
    def cell(b, t, K):
        def st(a, c):
            x, y = b.get((t, 'lan', K, a)), b.get((t, 'lan', K, c))
            return stability(x['key'], y['key'], x['unit_counts'], y['unit_counts']) if x and y else float('nan')
        s, n = st('h1', 'h2'), st('s1', 's2')
        return b.get((t, 'lan', K, 'full')), s, n, ((s - n) / (1 - n) if n == n and n < 1 else float('nan'))
    def chosen(b, t):
        c = [(b[k]['per_char'], k[2]) for k in b if k[0] == t and k[3] == 'full' and b[k]['kl'] <= 0.15]
        return max(c)[1] if c else None
    K0 = chosen(cal, 'syn_gate7'); f0 = cal[('syn_gate7', 'lan', K0, 'full')]; pcs = f0['per_char'] - 0.25
    print(f'clean calibration (tier 5): K {K0}, per-char {f0["per_char"]:.3f}, similarity {f0["similarity"]:.3f}; threshold PC* = {pcs:.3f}')
    print(f'{len(best)} tier-6 cells\n\n| text | chosen K | per-char | KL | similarity | stability | null | normalised | detected |\n|---|---|---|---|---|---|---|---|---|')
    for t in sorted({k[0] for k in best}):
        K = chosen(best, t)
        if K is None:
            Ks = sorted({k[2] for k in best if k[0] == t}); f, s, n, nm = cell(best, t, Ks[-1])
            print(f'| {t} | none (all degenerate; K {Ks[-1]} shown) | {f["per_char"]:.3f} | {f["kl"]:.3f} | {f.get("similarity", 0):.3f} | {s:.2f} | {n:.2f} | {nm:.2f} | no |')
            continue
        f, s, n, nm = cell(best, t, K)
        ok = f['per_char'] >= pcs and f['kl'] <= 0.15 and nm >= 0.5
        print(f'| {t} | {K} | {f["per_char"]:.3f} | {f["kl"]:.3f} | {f.get("similarity", 0):.3f} | {s:.2f} | {n:.2f} | {nm:.2f} | {"yes" if ok else "no"} |')


if __name__ == '__main__':
    main()
