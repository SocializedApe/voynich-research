"""GPU version of sweep.py: all annealing chains of one (text, variant, lang) run as one batch.

Same objective and moves as solver.py (order-5 letter model log-probability minus LAMBDA * n * letter KL;
frequency-matched start; single re-assignments and P_SWAP swaps; linear cooling from T0 = 2 n / 20000), but every
chain is rescored in full at every step, in parallel. One batch = every K x part x seed x restart of one text,
variant and language (3 x 4 x 2 x 4 = 96 chains); a job's result is the best of its restart chains. Writes the same
JSON lines as sweep.py (plus 'engine': 'gpu'), so analyze.py reads both.

Run: python gpu_sweep.py --tier 2 [--shard 0 --nshards 1] [--out DIR] [--iters 60000] [--deadline SECONDS]
"""
import argparse, collections, difflib, itertools, json, os, random, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import torch
import solver, sweep

RESTARTS = 4


def freq_init(freq, ref, letters, rng):
    order = np.argsort(-freq); need = {l: ref[l] * freq.sum() for l in letters}
    key = np.zeros(len(freq), dtype=np.int64)
    for s in order:
        l = max(letters, key=lambda L: need[L] + rng.random() * 1e-6); key[s] = l; need[l] -= freq[s]
    return key


def run_batch(text, variant, lang, jobs_here, iters, dev, log=print):
    m, ref = sweep.load_lm(lang); A, k = m.A, m.order
    lp = torch.tensor(m.lp, device=dev); refT = torch.tensor(ref, device=dev, dtype=torch.float32)
    letters = [i for i, c in enumerate(m.alpha) if c != ' ']
    chains = []   # (job, restart, types, seq)
    for j in jobs_here:
        pieces, truth = sweep.units_for(text, variant, j['K'])
        syms = sweep.select(pieces, j['part'], j['variant'].endswith('pos'))
        types = sorted(set(syms)); tid = {t: i for i, t in enumerate(types)}
        seq = np.array([tid[s] for s in syms], dtype=np.int64)
        for r in range(RESTARTS): chains.append((j, r, types, seq, syms, truth))
    C = len(chains); N = max(len(c[3]) for c in chains); Tm = max(len(c[2]) for c in chains)
    seqT = torch.zeros((C, N), dtype=torch.long, device=dev); lens = torch.tensor([len(c[3]) for c in chains], device=dev)
    for i, c in enumerate(chains): seqT[i, :len(c[3])] = torch.tensor(c[3], device=dev)
    nw = N - k + 1
    wmask = (torch.arange(nw, device=dev)[None, :] < (lens - k + 1)[:, None]).float()
    freq = torch.zeros((C, Tm), device=dev)
    for i, c in enumerate(chains): freq[i, :len(c[2])] = torch.tensor(np.bincount(c[3], minlength=len(c[2])), device=dev, dtype=torch.float32)
    valid = (freq > 0).float()
    key = torch.zeros((C, Tm), dtype=torch.long, device=dev)
    for i, c in enumerate(chains):
        rng = random.Random(hash((c[0]['id'], c[1])) & 0xffffffff)
        key[i, :len(c[2])] = torch.tensor(freq_init(np.bincount(c[3], minlength=len(c[2])), ref, letters, rng), device=dev)
    lettersT = torch.tensor(letters, device=dev); powers = torch.tensor([A ** (k - 1 - j) for j in range(k)], device=dev)
    nT = lens.float()
    def objective(kk):
        x = torch.gather(kk, 1, seqT)
        ctx = sum(x[:, j:j + nw] * powers[j] for j in range(k))
        lmv = (lp[ctx] * wmask).sum(1)
        cnt = torch.zeros((C, A), device=dev).scatter_add_(1, kk, freq) + 1e-9
        q = cnt / cnt.sum(1, keepdim=True)
        klv = (q * torch.log(q / refT[None, :])).sum(1)
        return lmv - solver.LAMBDA * nT * klv
    g = torch.Generator(device=dev); g.manual_seed(12345)
    cur = objective(key); best = cur.clone(); bestkey = key.clone()
    T0 = 2.0 * nT / 20000
    ar = torch.arange(C, device=dev)
    pw = freq / freq.sum(1, keepdim=True); pu = valid / valid.sum(1, keepdim=True)
    t0 = time.time()
    for it in range(iters):
        new = key.clone()
        swap = torch.rand(C, device=dev, generator=g) < solver.P_SWAP
        pick = torch.where((torch.rand(C, device=dev, generator=g) < 0.5)[:, None], pw, pu)
        s = torch.multinomial(pick, 1, generator=g)[:, 0]
        s2 = torch.multinomial(pw, 1, generator=g)[:, 0]
        newl = lettersT[torch.randint(len(letters), (C,), device=dev, generator=g)]
        a_l = new[ar, s].clone(); b_l = new[ar, s2].clone()
        new[ar, s] = torch.where(swap, b_l, newl)
        new[ar, s2] = torch.where(swap, a_l, new[ar, s2])
        sc = objective(new)
        Tt = T0 * (1 - it / iters) + 1e-3
        acc = (sc > cur) | (torch.rand(C, device=dev, generator=g) < torch.exp(((sc - cur) / Tt).clamp(max=0)))
        key = torch.where(acc[:, None], new, key); cur = torch.where(acc, sc, cur)
        imp = cur > best; best = torch.where(imp, cur, best); bestkey = torch.where(imp[:, None], key, bestkey)
        if it % 10000 == 0: log(f'  {text}|{lang}|{variant}: step {it}/{iters}, {C} chains, {time.time() - t0:.0f}s')
    out = []
    byjob = collections.defaultdict(list)
    for i, c in enumerate(chains): byjob[c[0]['id']].append(i)
    for jid, idx in byjob.items():
        i = max(idx, key=lambda q: float(best[q])); j, _, types, seq, syms, truth = chains[i]
        kk = bestkey[i, :len(types)].cpu().numpy()
        dec = ''.join(m.alpha[kk[t]] for t in seq)
        cnt = np.bincount(m.encode(dec), minlength=A).astype(float) + 1e-9
        r = dict(j, objective=float(best[i]), per_char=m.per_char(dec), kl=solver.kl(cnt, ref), units=len(types),
                 unit_counts=dict(collections.Counter(syms)), symbols=len(seq), key={t: m.alpha[kk[q]] for q, t in enumerate(types)},
                 decryption=dec[:400], engine='gpu', seconds=round(time.time() - t0, 1))
        if truth and j['part'] == 'full':
            r['similarity'] = difflib.SequenceMatcher(None, dec[:3000], truth[:3000], autojunk=False).ratio()
        out.append(r)
    return out


def main():
    a = argparse.ArgumentParser(); a.add_argument('--tier', type=int, default=2); a.add_argument('--shard', type=int, default=0)
    a.add_argument('--nshards', type=int, default=1); a.add_argument('--out', default=os.path.join(HERE, 'results'))
    a.add_argument('--iters', type=int, default=60000); a.add_argument('--deadline', type=float, default=0)
    a.add_argument('--only', default='', help='comma list of texts to restrict to (testing)')
    args = a.parse_args()
    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    js = sweep.jobs(args.tier)
    if args.only: js = [j for j in js if j['text'] in args.only.split(',')]
    groups = collections.defaultdict(list)
    for j in js: groups[(j['text'], j['variant'], j['lang'])].append(j)
    keys = sorted(groups)[args.shard::args.nshards]
    os.makedirs(args.out, exist_ok=True); path = os.path.join(args.out, f'gpu_shard{args.shard}.jsonl')
    done = {json.loads(l)['id'] for l in open(path, encoding='utf-8')} if os.path.exists(path) else set()
    print(f'{dev}: {len(keys)} batches, {sum(len(groups[k]) for k in keys)} jobs ({len(done)} done)', flush=True)
    t0 = time.time()
    with open(path, 'a', encoding='utf-8') as f:
        for b, kk in enumerate(keys):
            todo = [j for j in groups[kk] if j['id'] not in done]
            if not todo: continue
            for r in run_batch(*kk, todo, args.iters, dev):
                f.write(json.dumps(r) + '\n')
                print(f'[{b + 1}/{len(keys)} {time.time() - t0:.0f}s] {r["id"]}: per-char {r["per_char"]:.3f} kl {r["kl"]:.3f}'
                      + (f' sim {r["similarity"]:.3f}' if 'similarity' in r else ''), flush=True)
            f.flush()
            if args.deadline and time.time() - t0 > args.deadline: print('deadline reached; stopping', flush=True); break


if __name__ == '__main__':
    main()
