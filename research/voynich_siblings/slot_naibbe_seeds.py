"""Naibbe ciphertext regenerated from Latin (repository port of Greshko's naibbe.py in targets/voynich/b3_bakeoff.py,
tables = references/naibbe_tables.csv from github.com/greshko/naibbe-cipher, path argv[1]) with several seeds, scored
with the start/end dependence measure of slot_independence.py. Run from the repository root."""
import os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'targets', 'voynich'))
import slot_independence as si
from b3_bakeoff import Naibbe

csv_path = sys.argv[1]
lat = os.path.join(HERE, '..', '..', 'lang', 'corpora', 'la-gutenberg.txt')
rng = random.Random(11)
for seed in (19, 7, 3, 101, 2026):
    nb = Naibbe(csv_path, seed=seed)
    words = [w for ws, _ in nb.generate(lat, si.N_TOK + 5000) for w in ws][:si.N_TOK]
    for k in (1, 2):
        v, _, n = si.measure([si.eva_units(w) for w in words], k, rng)
        print(f'naibbe Latin seed {seed:5d} k={k} tokens(4-8) {n:6d} norm {v:.3f}')
