"""Duplicate drawings: does a pharmaceutical page share words with the herbal page whose plant it redraws?

Pairs: `data/voynich_nu/pairs.json`, parsed from René Zandbergen's quire pages (voynich.nu q15, q19, fetched 28 Oct
2026): fragment N on a pharmaceutical page "appears to be the same plant as" (9 pairs) or "shows some similarity with"
(22 pairs) the plant on a herbal folio. The matches are visual, made without reference to the text.

Protocol, fixed before the run (28 Oct 2026):
  Vocabulary of a page = all a-z word types in ZL3b (every locus type: paragraphs and labels).
  For each pair (P, H): s = Jaccard(P, H). Controls = herbal pages (ZL illustration type H) of the same Currier
  language as H, and of the same hand if at least 8 such pages exist, H excluded. Score = percentile of s among
  Jaccard(P, control) (ties half). Statistic = mean score over pairs; null = H replaced by a random control page,
  10,000 times; p = share of null means >= observed. Reported for 'same' pairs, all pairs, and with P reduced to its
  label words (word in H's text counts) as a secondary test.
  If pages that show the same plant share vocabulary beyond scribe and dialect, the mean score sits above 0.5.

Run from the repository root: python targets/voynich/meaning/duplicates.py
"""
import collections, csv, json, os, random, re
HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, '..', 'data', 'ZL3b-n.words.tsv')


def load():
    words, labels, meta = collections.defaultdict(set), collections.defaultdict(set), {}
    for r in csv.DictReader(open(TSV, encoding='utf-8'), delimiter='\t'):
        ws = [w for w in r['line_words'].split() if re.fullmatch(r'[a-z]+', w)]
        words[r['folio']].update(ws)
        if r['locus_type'] == 'L': labels[r['folio']].update(ws)
        meta.setdefault(r['folio'], (r['illus'], r['lang'], r['hand']))
    return words, labels, meta


def jac(a, b): return len(a & b) / len(a | b) if (a | b) else 0.0


def run(pairs, words, labels, meta, use_labels, rng, reps=10000):
    herbal = [f for f, m in meta.items() if m[0] == 'H' and words[f]]
    items = []
    for p in pairs:
        P, H = p['pharma'], p['herbal']
        if P not in words or H not in meta: continue
        lang, hand = meta[H][1], meta[H][2]
        ctl = [f for f in herbal if f != H and meta[f][1] == lang]
        same_hand = [f for f in ctl if meta[f][2] == hand]
        if len(same_hand) >= 8: ctl = same_hand
        vp = labels[P] if use_labels else words[P]
        if not vp: continue
        sim = (lambda f: len(vp & words[f]) / len(vp)) if use_labels else (lambda f: jac(vp, words[f]))
        s = sim(H); cs = [sim(f) for f in ctl]
        items.append((sum(c < s for c in cs) + 0.5 * sum(c == s for c in cs)) / len(cs) if cs else 0.5)
        items[-1] = (items[-1], [ (sum(c < x for c in cs) + 0.5 * sum(c == x for c in cs)) / len(cs) for x in cs ])
    obs = sum(i for i, _ in items) / len(items)
    null = [sum(rng.choice(alt) for _, alt in items) / len(items) for _ in range(reps)]
    p = (1 + sum(x >= obs for x in null)) / (1 + reps)
    return len(items), obs, p, [round(i, 2) for i, _ in items]


def main():
    words, labels, meta = load()
    pairs = json.load(open(os.path.join(HERE, 'data', 'voynich_nu', 'pairs.json')))
    print('pairs:', len(pairs), '| languages of matched herbal pages:', collections.Counter(meta.get(p['herbal'], ('?', '?', '?'))[1] for p in pairs),
          '| pharma pages:', collections.Counter(meta.get(p['pharma'], ('?', '?', '?'))[1] for p in pairs))
    rng = random.Random(5)
    for name, sel in (('same plant', [p for p in pairs if p['strength'] == 'same']), ('all pairs', pairs)):
        for lab in (False, True):
            n, obs, pv, per = run(sel, words, labels, meta, lab, rng)
            print(f'{name:10} {"labels of P in H" if lab else "page vocabulary   "}: n {n:2}, mean percentile {obs:.3f} (null 0.5), p {pv:.4f} | per pair {per}')


if __name__ == '__main__':
    main()
