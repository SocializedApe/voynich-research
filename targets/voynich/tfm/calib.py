"""Calibration: does a model learn Latin well enough (below the 5-gram's 1.95 bits/char on the test blocks) to be
worth running on all texts? One LSTM (1 layer, 384 units) against the train.py transformer.

Run from the repository root: python targets/voynich/tfm/calib.py lstm|tfm [steps] [threads]
"""
import math, os, sys, time
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import train as T


class LSTM(nn.Module):
    def __init__(self, V):
        super().__init__(); self.e = nn.Embedding(V, 64); self.r = nn.LSTM(64, 384, 1, batch_first=True); self.h = nn.Linear(384, V)

    def forward(self, x, need=False):
        o, _ = self.r(self.e(x)); return self.h(o), [o], None


def main():
    kind = sys.argv[1]; steps = int(sys.argv[2]) if len(sys.argv) > 2 else 1500
    torch.set_num_threads(int(sys.argv[3]) if len(sys.argv) > 3 else 3)
    vocab, tr, va, te = T.load('latin'); V = len(vocab)
    torch.manual_seed(0); rng = np.random.default_rng(0)
    m = LSTM(V) if kind == 'lstm' else T.GPT(V)
    if kind != 'lstm': T.DROP = 0.1
    opt = torch.optim.AdamW(m.parameters(), lr=3e-3, weight_decay=0.01 if kind == 'lstm' else 0.1); t0 = time.time()
    for step in range(1, steps + 1):
        lr = 3e-3 * min(1, step / 100) * 0.5 * (1 + math.cos(math.pi * step / steps))
        for g in opt.param_groups: g['lr'] = lr
        x, y = T.batch(tr, 32 if kind == 'lstm' else 16, rng)
        loss = F.cross_entropy(m(x)[0].transpose(1, 2), y)
        opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(m.parameters(), 1.0); opt.step()
        if step % 250 == 0:
            c = np.array(T.curve(m, va, stride=128))
            print(f'{kind} step {step} train {loss.item() / math.log(2):.3f} val {c.mean():.3f} | pos0 {c[0]:.2f} '
                  f'8-15 {c[8:16].mean():.2f} 32-63 {c[32:64].mean():.2f} 128-255 {c[128:].mean():.2f} | {time.time() - t0:.0f}s', flush=True)


if __name__ == '__main__':
    main()
