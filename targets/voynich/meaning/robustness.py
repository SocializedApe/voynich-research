"""Robustness of #25, #27, #28 and #33 before the write-up.

Protocol, fixed before any run (28 Oct 2026):
  A. Homophony sweep (#25): wordpredict.measure on Latin and Italian word codes where every type with at least 5
     tokens gets K code words (K = 1, 2, 4, 8, 16), one drawn at random per token; signal against the within-line
     shuffle (3 seeds) as in wordpredict.py. Reported: the K at which the previous-word signal falls to Voynich's.
  B. Generator seeds (#27, #33): the per-hand cipher (scribe_systems cipher_hand) and the strongest habit setting
     (duel cipher_habit s 2.0, p 1.0) rebuilt with generator seeds 0, 1, 2; scribe ratios on hands 1-3.
  C. Spread of rules/habits (#28): scribe_systems.rules_habits repeated 5 times (20 draws each, new sampling seed)
     on Voynich, Auchinleck and the per-hand cipher (seed 0); mean and range.

Run from the repository root: python targets/voynich/meaning/robustness.py <naibbe_tables.csv>
"""
import collections, json, os, random, statistics, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'research', 'voynich_siblings'))
import wordpredict as wp
import scribe_systems as ss
import scribe_ratio as sr
import duel
import a4_selfcitation as a4
import b3_bakeoff as b3
import hybrid_model as hm
import cipher_models as cm
import auchinleck
from variants import UNIT


def signal(pages):
    real = wp.measure(pages); null = [wp.measure(wp.shuffle_lines(pages, s)) for s in (1, 2, 3)]
    return real['gain_w'] - statistics.mean(x['gain_w'] for x in null)


def homophonic_k(plain, K, rng):
    freq = collections.Counter(plain)
    codes = {w: [f'c{i}_{j}' for j in range(K if n >= 5 else 1)] for i, (w, n) in enumerate(freq.most_common())}
    return [rng.choice(codes[w]) for w in plain]


def cipher_hand(zl, hand_of, csv_path, plain, TW, seed):
    out = {}
    for i, h in enumerate(sorted({hand_of[p['folio']] for p in zl})):
        pg = [p for p in zl if hand_of[p['folio']] == h]
        key = 'hand' + h if h in ss.HANDS else None
        groups = collections.OrderedDict()
        for p in pg:
            groups.setdefault(key or ('grpA' if p['lang'] == 'A' else 'grpB'), []).append(p)
        for j, (k, ps) in enumerate(groups.items()):
            v = cm.Variant(csv_path, 100 * seed + 10 * i + j, merge=0.0, **hm.BASE)
            ss.build_tables(v, TW[k], random.Random(sum(map(ord, k)) + 1000 * seed))
            for p, q in zip(ps, cm.generate(v, plain[h], a4.skeleton(ps))):
                out[p['folio']] = {'folio': p['folio'], 'lang': p['lang'], 'lines': q['lines']}
    return [out[p['folio']] for p in zl]


def main():
    csv_path = sys.argv[1]; R = {}
    zl = b3.load_zl_lang(); skel = a4.skeleton(zl); N = len(b3.words_of(zl)); hand_of = ss.page_hands()

    print('A. homophony sweep (previous-word signal, bits/word)', flush=True)
    R['A'] = {'voynich': signal(zl)}; print(f"voynich {R['A']['voynich']:+.3f}", flush=True)
    for lang, path in (('la', os.path.join(ROOT, 'lang', 'corpora', 'la-gutenberg.txt')), ('it', a4.IT)):
        plain = a4.gutenberg_words(path)[:N]
        for K in (1, 2, 4, 8, 16):
            R['A'][f'{lang}_K{K}'] = signal(a4.pour(homophonic_k(plain, K, random.Random(5)), skel))
            print(f"{lang} K {K:2d} {R['A'][f'{lang}_K{K}']:+.3f}", flush=True)

    la = a4.gutenberg_words(os.path.join(ROOT, 'lang', 'corpora', 'la-gutenberg.txt')); tmp = tempfile.mkdtemp(); plain = {}
    for i, h in enumerate(sorted(set(hand_of.values()))):
        ws = la[i * 12000:(i + 1) * 12000]; plain[h] = os.path.join(tmp, f'{h if h != "?" else "x"}.txt')
        open(plain[h], 'w', encoding='utf-8').write('\n'.join(' '.join(ws[k:k + 12]) for k in range(0, len(ws), 12)))
    vh = ss.by_hand(zl, hand_of)
    grp = {g: [w for p in zl if p['lang'] == g for ln in p['lines'] for w in ln['words']] for g in ('A', 'B')}
    TW = {'grpA': grp['A'], 'grpB': grp['B'], **{'hand' + h: vh[h] for h in ss.HANDS}}

    print('\nB. generator seeds, scribe ratios on hands 1-3 (Voynich 2.96 [2.18-3.59], 2.00 [1.87-2.15])', flush=True)
    rng = random.Random(17); R['B'] = {}; hand0 = None
    for seed in (0, 1, 2):
        t = cipher_hand(zl, hand_of, csv_path, plain, TW, seed); hand0 = hand0 or t
        R['B'][f'cipher_hand_s{seed}'] = sr.analyse(f'cipher_hand seed {seed}', sr.docs_of(ss.by_hand(t, hand_of)), UNIT.findall, rng)
        orig = duel.HabitVariant.__init__
        def init(self, c, sd, s, p, _o=orig, _seed=seed):
            _o(self, c, sd + 1000 * _seed, s, p)
        duel.HabitVariant.__init__ = init
        t = duel.cipher_habit(zl, hand_of, csv_path, plain, 2.0, 1.0)
        duel.HabitVariant.__init__ = orig
        R['B'][f'cipher_habit_2.0_1.0_s{seed}'] = sr.analyse(f'cipher_habit 2.0/1.0 seed {seed}', sr.docs_of(ss.by_hand(t, hand_of)), UNIT.findall, rng)

    print('\nC. rules / habits, 5 repeats of 20 draws', flush=True)
    au = collections.defaultdict(list)
    for it in json.load(open(os.path.join(auchinleck.RAW, 'items.json'))):
        if it['scribe']:
            au[it['scribe']] += auchinleck.text_of(os.path.join(auchinleck.RAW, os.path.basename(it['page'])))
    sets = {'voynich': (vh, UNIT.findall), 'auchinleck': ({k: v for k, v in au.items() if len(v) >= 2500}, list),
            'cipher_hand_s0': (ss.by_hand(hand0, hand_of), UNIT.findall)}
    R['C'] = {}
    for n, (g, split) in sets.items():
        rs = [ss.rules_habits(g, split, random.Random(100 + k)) for k in range(5)]
        R['C'][n] = rs
        r = [x[0] for x in rs]; h = [x[1] for x in rs]
        print(f'{n:16s} rules {statistics.mean(r):.3f} [{min(r):.3f}-{max(r):.3f}]  habits {statistics.mean(h):+.3f} [{min(h):+.3f}-{max(h):+.3f}]', flush=True)
    json.dump(R, open(os.path.join(HERE, 'robustness_results.json'), 'w'), indent=1, default=str)


if __name__ == '__main__':
    main()
