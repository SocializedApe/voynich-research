"""Train one small character-level transformer on one text and measure loss as a function of context length.

Model: GPT-style decoder, 4 layers, d_model 96, 4 heads, window 256 characters, dropout on residual and MLP outputs, none on attention weights (about 0.45M parameters).
Training: AdamW, batch 24, cosine schedule, validation every 100 steps, stop after 5 without improvement.
Split: the text is cut into 20 equal blocks; blocks 4 and 14 are validation (early stopping), 9 and 19 test, the
rest training (80%). Training windows are drawn at random inside training blocks.
Curve: every test window (stride 32) is scored; the loss at position t in a window uses exactly t characters of
context, so averaging by t gives loss (bits/char) against context length from one model. Also the unigram entropy of
the text's test blocks, so curves can be compared as gains: H1 - loss(t).

Writes targets/voynich/tfm/results/<name>.json and models/<name>.pt.
Run from the repository root: python targets/voynich/tfm/train.py <name> [--steps 1500] [--lr 1e-3] [--drop 0.2] [--batch 24] [--d 96] [--layers 4] [--seed 0] [--tag NAME] [--threads 4]
Uses a CUDA GPU when one is available.
"""
import json, math, os, sys, time
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

HERE = os.path.dirname(os.path.abspath(__file__))
CTX, D, L, NH, DROP = 256, 96, 4, 4, 0.2


class Block(nn.Module):
    def __init__(self):
        super().__init__()
        self.ln1, self.ln2 = nn.LayerNorm(D), nn.LayerNorm(D)
        self.qkv, self.proj = nn.Linear(D, 3 * D), nn.Linear(D, D)
        self.mlp = nn.Sequential(nn.Linear(D, 4 * D), nn.GELU(), nn.Linear(4 * D, D), nn.Dropout(DROP))
        self.drop = nn.Dropout(DROP)

    def forward(self, x, mask, need=False):
        B, T, _ = x.shape
        q, k, v = self.qkv(self.ln1(x)).view(B, T, 3, NH, D // NH).permute(2, 0, 3, 1, 4)
        w = None
        if need:   # explicit weights for analysis
            att = (q @ k.transpose(-1, -2)) / math.sqrt(D // NH)
            w = att.masked_fill(mask, float('-inf')).softmax(-1); a = w @ v
        else:
            a = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        x = x + self.drop(self.proj(a.transpose(1, 2).reshape(B, T, D)))
        return x + self.mlp(self.ln2(x)), w


class GPT(nn.Module):
    def __init__(self, V):
        super().__init__()
        self.tok, self.pos = nn.Embedding(V, D), nn.Embedding(CTX, D)
        self.blocks = nn.ModuleList(Block() for _ in range(L))
        self.ln, self.head = nn.LayerNorm(D), nn.Linear(D, V)
        self.drop = nn.Dropout(DROP)
        self.register_buffer('mask', torch.triu(torch.ones(CTX, CTX, dtype=torch.bool), 1))

    def forward(self, idx, need=False):
        T = idx.shape[1]
        x = self.drop(self.tok(idx) + self.pos(torch.arange(T, device=idx.device)))
        hs, ws = [], []
        for b in self.blocks:
            x, w = b(x, self.mask[:T, :T], need); hs.append(x); ws.append(w)
        return self.head(self.ln(x)), hs, ws


def load(name):
    s = open(os.path.join(HERE, 'data', name + '.txt'), encoding='utf-8').read()
    vocab = sorted(set(s)); stoi = {c: i for i, c in enumerate(vocab)}
    a = np.array([stoi[c] for c in s], dtype=np.int64)
    B = len(a) // 20
    blocks = [a[i * B:(i + 1) * B] for i in range(20)]
    val = [blocks[4], blocks[14]]; test = [blocks[9], blocks[19]]
    train = [b for i, b in enumerate(blocks) if i not in (4, 9, 14, 19)]
    return vocab, train, val, test


def batch(parts, n, rng):
    xs = []
    for _ in range(n):
        p = parts[rng.integers(len(parts))]; i = rng.integers(len(p) - CTX - 1); xs.append(p[i:i + CTX + 1])
    x = torch.tensor(np.stack(xs)); return x[:, :-1], x[:, 1:]


@torch.no_grad()
def curve(model, parts, stride=32):
    model.eval(); tot = torch.zeros(CTX); cnt = 0; dev = next(model.parameters()).device
    for p in parts:
        starts = list(range(0, len(p) - CTX - 1, stride))
        for j in range(0, len(starts), 64):
            x = torch.tensor(np.stack([p[i:i + CTX + 1] for i in starts[j:j + 64]])).to(dev)
            logits, _, _ = model(x[:, :-1])
            l = F.cross_entropy(logits.transpose(1, 2), x[:, 1:], reduction='none')   # (b, T) nats
            tot += l.sum(0).cpu(); cnt += l.shape[0]
    model.train(); return (tot / cnt / math.log(2)).tolist()


def main():
    global DROP, D, L
    a = sys.argv[1:]; name = a[0]
    opt_ = lambda k, d, f=float: f(a[a.index(k) + 1]) if k in a else d
    steps = opt_('--steps', 1500, int); LR = opt_('--lr', 1e-3); DROP = opt_('--drop', DROP); BS = opt_('--batch', 24, int)
    D = opt_('--d', D, int); L = opt_('--layers', L, int); seed = opt_('--seed', 0, int); tag = a[a.index('--tag') + 1] if '--tag' in a else name
    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    torch.set_num_threads(int(a[a.index('--threads') + 1]) if '--threads' in a else 4)
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    vocab, train, val, test = load(name)
    model = GPT(len(vocab)).to(dev); opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.1)
    nparams = sum(p.numel() for p in model.parameters())
    best, best_state, bad, t0, log = 1e9, None, 0, time.time(), []
    for step in range(1, steps + 1):
        lr = LR * min(1, step / 100) * (0.5 * (1 + math.cos(math.pi * step / steps)))
        for g in opt.param_groups: g['lr'] = lr
        x, y = batch(train, BS, rng); x, y = x.to(dev), y.to(dev)
        logits, _, _ = model(x); loss = F.cross_entropy(logits.transpose(1, 2), y)
        opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step()
        if step % 100 == 0:
            v = float(np.mean(curve(model, val, stride=128)))
            log.append((step, float(loss) / math.log(2), v)); print(f'{name} step {step} train {float(loss) / math.log(2):.3f} val {v:.3f} bits/char {time.time() - t0:.0f}s', flush=True)
            if v < best - 1e-3: best, best_state, bad = v, {k: t.detach().cpu().clone() for k, t in model.state_dict().items()}, 0
            else:
                bad += 1
                if bad >= 5: break
    if best_state is not None: model.load_state_dict(best_state)
    c = curve(model, test)
    allt = np.concatenate(test); f = np.bincount(allt, minlength=len(vocab)) / len(allt)
    h1 = float(-(f[f > 0] * np.log2(f[f > 0])).sum())
    out = {'name': name, 'tag': tag, 'seed': seed, 'd': D, 'layers': L, 'device': dev, 'params': nparams, 'lr': LR, 'drop': DROP, 'batch': BS, 'vocab': vocab, 'best_val': best, 'h1_test': h1, 'curve': c, 'log': log,
           'time_s': time.time() - t0}
    os.makedirs(os.path.join(HERE, 'results'), exist_ok=True); os.makedirs(os.path.join(HERE, 'models'), exist_ok=True)
    json.dump(out, open(os.path.join(HERE, 'results', tag + '.json'), 'w'))
    torch.save({'state': {k: t.cpu() for k, t in model.state_dict().items()}, 'vocab': vocab, 'd': D, 'layers': L, 'name': name}, os.path.join(HERE, 'models', tag + '.pt'))
    bins = [(0, 1), (1, 2), (2, 4), (4, 8), (8, 16), (16, 32), (32, 64), (64, 128), (128, 256)]
    print(f'RESULT {name} params {nparams} H1 {h1:.3f} | ' + ' '.join(f'ctx{a_}-{b_ - 1}: {np.mean(c[a_:b_]):.3f}' for a_, b_ in bins) + f' | {time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
