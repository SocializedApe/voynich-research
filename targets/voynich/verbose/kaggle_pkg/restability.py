"""Re-reading of every sweep tier by key stability alone. (12 Nov 2026; after tier 6, so post hoc for tiers 3-5)

Tier 6 showed that the per-character threshold of the tier rules fails at 2% miscopied glyphs, while the agreement of
the keys solved independently on the two halves of a text stays above its shuffled null up to 10% glyph noise
(normalised stability 0.50-0.84 for noisy ciphers, 0.87 clean). This script reads all saved results with that one
criterion: for every cell (text, language, variant, K), stability(h1, h2), the null stability(s1, s2) from halves of
the shuffled stream, normalised = (s - null) / (1 - null). A cell 'agrees' if normalised >= 0.5, the lowest value of a
solvable noisy cipher in tier 6 and the stability bound already in the tier rules. Tiers 1-2 (tier1_cpu, gpufull,
gpucal) have no shuffled halves; for them the raw stability is listed against the raw stability of the synthetic
ciphers of the same tier and of the Voynich nulls of tiers 3-5 (0.26-0.86).
Amended after the first run: four Voynich cells of tier 4 (German, positional units) passed 0.5. Their keys are
degenerate: the letter distribution of the decryption is far from German (KL 0.32-0.37 against the tier rules' limit
0.15) and the decryption is en / er / de repeated; both halves collapse the same way and the shuffled stream does not.
Stability alone is therefore not enough, and the last column counts cells with normalised stability >= 0.5 AND letter
KL <= 0.15 on the full text (the tier rules without their per-character threshold).

Run from targets/voynich: python verbose/kaggle_pkg/restability.py -> verbose/kaggle_results/restability.md
"""
import collections, glob, json, os, statistics, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from analyze import stability
RES = os.path.join(HERE, '..', 'kaggle_results')


def main():
    L = ['# Every sweep tier read by key stability alone (12 Nov 2026)', '', 'Script `kaggle_pkg/restability.py` (criterion in its docstring; post hoc for tiers 3-5). Reproduce: `python verbose/kaggle_pkg/restability.py` from `targets/voynich`.', '',
         '| tier | texts | cells | normalised stability: min / median / max | cells >= 0.5 | raw stability: min / median / max | cells >= 0.5 with KL <= 0.15 |', '|---|---|---|---|---|---|---|']
    leads = []
    for tier in ('tier1_cpu', 'gpucal', 'gpufull', 'tier3', 'tier4', 'tier5', 'tier6'):
        best = {}
        for p in glob.glob(os.path.join(RES, tier, '*.jsonl')):
            for l in open(p, encoding='utf-8'):
                r = json.loads(l); k = (r['text'], r['lang'], r['variant'], r['K'], r['part'])
                if k not in best or r['objective'] > best[k]['objective']:
                    best[k] = r
        groups = collections.defaultdict(list)
        for (t, l, v, K) in sorted({k[:4] for k in best}):
            def st(a, b):
                x, y = best.get((t, l, v, K, a)), best.get((t, l, v, K, b))
                return stability(x['key'], y['key'], x['unit_counts'], y['unit_counts']) if x and y else None
            s, n = st('h1', 'h2'), st('s1', 's2')
            if s is None or s != s:
                continue
            nm = (s - n) / (1 - n) if n is not None and n == n and n < 1 else None
            f = best.get((t, l, v, K, 'full')); groups['Voynich' if t.startswith('voy') else 'synthetic ciphers'].append((s, nm, (tier, t, l, v, K), f['kl'] if f else 9, f.get('similarity') if f else None))
        for g, cells in groups.items():
            raw = [c[0] for c in cells]; nm = [c[1] for c in cells if c[1] is not None]
            f3 = lambda x: f'{min(x):.2f} / {statistics.median(x):.2f} / {max(x):.2f}' if x else '-'
            hits = [c for c in cells if c[1] is not None and c[1] >= 0.5]
            L.append(f"| {tier} | {g} | {len(cells)} | {f3(nm)} | {len(hits) if nm else '-'} | {f3(raw)} | {sum(1 for c in hits if c[3] <= 0.15) if nm else '-'} |")
            if g == 'Voynich':
                leads += hits
            elif tier == 'tier6':
                t6 = sorted((c[2][1], c[2][4], c[1], c[3], c[4]) for c in cells if c[1] is not None)
    L += ['', f'Voynich cells with normalised stability >= 0.5: {len(leads)}.'] + [f'- {c[2]}: raw {c[0]:.2f}, normalised {c[1]:.2f}, letter KL {c[3]:.2f}' for c in leads]
    L += ['', 'Tier 6 (noisy calibration ciphers) under stability >= 0.5 and KL <= 0.15, per noise level and K:', '', '| text | K | normalised stability | KL | similarity to plaintext | passes |', '|---|---|---|---|---|---|']
    L += [f"| {t} | {K} | {nm:.2f} | {kl:.3f} | {sim:.2f} | {'yes' if nm >= 0.5 and kl <= 0.15 else 'no'} |" for t, K, nm, kl, sim in t6]
    open(os.path.join(RES, 'restability.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    main()
