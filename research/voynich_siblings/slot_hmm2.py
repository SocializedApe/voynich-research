"""Slot-HMM round 2: is Voynich's state-to-state dependence (0.54 bits at K = 24, slot_hmm.py) more than line
position, section drift and edge coupling?

  interior   tokens shuffled inside each line, first and last token kept (keeps line position, page and section)
  noP        prefix slot blanked (edge coupling end -> next opener cannot act through it)
  E only     only the ending slot kept (does one ending predict the next ending?)
Three seeds each at K = 24. Run from the repository root: python research/voynich_siblings/slot_hmm2.py
"""
import os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slot_hmm as s

K = 24
SEEDS = [11, 12, 13]


def interior(lines, rng):
    out = []
    for l in lines:
        mid = l[1:-1]; rng.shuffle(mid)
        out.append([l[0]] + mid + [l[-1]] if len(l) > 2 else list(l))
    return out


def keep(lines, idx):
    return [[tuple(x[j] if j in idx else '-' for j in range(4)) for x in l] for l in lines]


def main():
    V = [[s.slots(w) for w in ln] for ln in s.voynich_lines()]
    for seed in SEEDS:
        rng = random.Random(seed)
        I = interior(V, rng)
        for name, data in [('voynich', V), ('interior', I),
                           ('voynich noP', keep(V, {1, 2, 3})), ('interior noP', keep(I, {1, 2, 3})),
                           ('voynich E', keep(V, {3})), ('interior E', keep(I, {3}))]:
            s.run(f'{name} s{seed}', data, ks=[K], seed=seed)


if __name__ == '__main__':
    main()
