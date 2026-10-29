"""Read the sweep results (results/*.jsonl) and apply the decision rule.

Decision rule, fixed before any sweep result was seen (29 Oct 2026):
  Per (text, lang, variant, K): the seed with the best objective is kept for each part.
  stability = agreement of the h1 and h2 keys: over units used in both halves, the share of unit occurrences
    (weighted by min of the two counts) mapped to the same letter; chance is about the sum of squared letter
    frequencies (0.06-0.08).
  degenerate = letter KL of the full decryption to the language > 0.15 (e.g. the 'iiii' collapse).
  Per (text, lang, variant) the K is chosen blind: the non-degenerate full run with the best per-character score.
  SIGNAL if, for that K: per_char >= -2.2, not degenerate, stability >= 0.5, and per_char exceeds the shuffled
    control by >= 0.3 (if the control is degenerate, that last condition is replaced by stability >= 0.7).
  The rule is only interpreted if the calibration passes: syn_gate2 and syn_gate3 must both give SIGNAL with
    similarity >= 0.8, and no Voynich shuffled control may pass the per-char and stability thresholds.
A SIGNAL never claims a decryption; it marks a setting for a targeted follow-up.

Run: python analyze.py [results_dir]
"""
import collections, glob, json, os, sys


def stability(k1, k2, f1, f2):
    num = den = 0
    for u in set(k1) & set(k2):
        w = min(f1.get(u, 0), f2.get(u, 0)); den += w; num += w * (k1[u] == k2[u])
    return num / den if den else float('nan')


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
    rows = [json.loads(l) for p in glob.glob(os.path.join(d, '*.jsonl')) for l in open(p, encoding='utf-8')]
    best = {}
    for r in rows:
        k = (r['text'], r['lang'], r['variant'], r['K'], r['part'])
        if k not in best or r['objective'] > best[k]['objective']: best[k] = r
    print(f'{len(rows)} job results, {len(best)} cells\n')
    print('| text | lang | variant | chosen K | per-char | KL | stability | shuffled per-char | similarity | verdict |')
    print('|---|---|---|---|---|---|---|---|---|---|')
    groups = collections.defaultdict(list)
    for (t, l, v, K, p) in best: groups[(t, l, v)].append(K)
    for (t, l, v) in sorted(groups):
        cands = []
        for K in sorted(set(groups[(t, l, v)])):
            full = best.get((t, l, v, K, 'full'))
            if full and full['kl'] <= 0.15: cands.append((full['per_char'], K))
        if not cands: print(f'| {t} | {l} | {v} | - | - | - | - | - | - | all degenerate |'); continue
        pc, K = max(cands); full = best[(t, l, v, K, 'full')]
        h1, h2, sh = (best.get((t, l, v, K, p)) for p in ('h1', 'h2', 'shuf'))
        stab = float('nan')
        if h1 and h2:
            stab = stability(h1['key'], h2['key'], h1['unit_counts'], h2['unit_counts'])
        shpc = sh['per_char'] if sh else float('nan'); shdeg = sh and sh['kl'] > 0.15
        ok = pc >= -2.2 and stab == stab and stab >= 0.5 and ((pc - shpc >= 0.3) if (sh and not shdeg) else stab >= 0.7)
        sim = full.get('similarity')
        print(f'| {t} | {l} | {v} | {K} | {pc:.3f} | {full["kl"]:.3f} | {stab:.2f} | {shpc:.3f}{" (degenerate)" if shdeg else ""} | '
              f'{"" if sim is None else f"{sim:.3f}"} | {"SIGNAL" if ok else "no signal"} |')


if __name__ == '__main__':
    main()
