"""What did the Voynich model pick up? Linear probes on hidden states, and attention reach for every model.

Probes (Voynich model only): the text of texts.py 'voynich' is rebuilt line by line with its ZL metadata (Currier
language, Davis hand, illustration type = section, paragraph-first line). For the character at the end of every
word (the space after it), hidden states of each layer are taken with up to 255 characters of context; a logistic
regression (5-fold, grouped by folio so no page is in train and test) predicts each label. Baselines: the same probe
on the untrained (random-init) model, and the majority class. A label the trained model decodes well above the
untrained one is something the model learned to track from context.

Attention reach (every trained model): per layer and head, the mean distance (characters) its attention looks back,
and the share of attention landing in the previous line, averaged over test windows. Copying from the previous line
(the autocopist's mechanism) shows as heads with high previous-line share.

Run from the repository root after train.py: python targets/voynich/tfm/probe.py [--model voynich_s0]
"""
import collections, csv, json, os, sys
import numpy as np
import torch
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import train as T
from texts import N

DATA = os.path.join(HERE, '..', 'data', 'ZL3b-n.words.tsv')
QUICK = '--quick' in sys.argv   # smoke test: one position in 30


def voynich_meta():
    """characters of the 'voynich' text with a per-character metadata row (same build as texts.py)"""
    chars, meta = [], []
    for r in csv.DictReader(open(DATA, encoding='utf-8'), delimiter='\t'):
        if r['locus_type'] != 'P': continue
        ws = [w for w in r['line_words'].split() if w.isalpha() and w.islower() and w.isascii()]
        if not ws: continue
        line = ' '.join(ws)
        if chars: chars.append('\n'); meta.append(meta[-1])
        m = {'lang': r['lang'], 'hand': r['hand'], 'section': r['illus'], 'pfl': r['para_start'], 'folio': r['folio']}
        chars += list(line); meta += [m] * len(line)
    return ''.join(chars)[:N], meta[:N]


@torch.no_grad()
def states(model, ids, positions):
    """hidden state (all layers) at each position, context = up to CTX-1 previous characters"""
    out = []
    for p in positions:
        s = max(0, p - T.CTX + 1); x = torch.tensor(ids[s:p + 1])[None]
        _, hs, _ = model(x); out.append(torch.stack([h[0, -1] for h in hs]).numpy())
    return np.stack(out)   # (n, L, D)


def probes(model_tag='voynich'):
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import GroupKFold, cross_val_score
    text, meta = voynich_meta()
    ck = open(os.path.join(HERE, 'data', 'voynich.txt'), encoding='utf-8').read()
    assert text == ck, 'metadata rebuild does not match texts.py voynich'
    sd = torch.load(os.path.join(HERE, 'models', model_tag + '.pt'), map_location='cpu'); T.D, T.L = sd.get('d', T.D), sd.get('layers', T.L)
    stoi = {c: i for i, c in enumerate(sd['vocab'])}; ids = [stoi[c] for c in text]
    trained = T.GPT(len(sd['vocab'])); trained.load_state_dict(sd['state']); trained.eval()
    torch.manual_seed(1); rand = T.GPT(len(sd['vocab'])); rand.eval()
    pos = [i for i in range(300, len(text)) if text[i] == ' '][::(30 if QUICK else 3)]
    groups = [meta[i]['folio'] for i in pos]
    H_tr, H_rd = states(trained, ids, pos), states(rand, ids, pos)
    res = {}
    for lab in ('lang', 'hand', 'section', 'pfl'):
        y = np.array([meta[i][lab] for i in pos]); keep = np.array([v not in ('', '?', 'X', 'Y') for v in y])
        cnt = collections.Counter(y[keep]); keep &= np.array([cnt[v] >= 30 for v in y])
        yk, gk = y[keep], np.array(groups)[keep]; maj = max(collections.Counter(yk).values()) / len(yk)
        row = {'n': int(keep.sum()), 'classes': len(set(yk)), 'majority': maj}
        for nm, Hs in (('trained', H_tr), ('untrained', H_rd)):
            row[nm] = []
            for layer in range(T.L):
                clf = LogisticRegression(max_iter=2000, C=0.5)
                sc = cross_val_score(clf, Hs[keep, layer], yk, cv=GroupKFold(5), groups=gk)
                row[nm].append(float(sc.mean()))
        res[lab] = row
        print(f'{lab:8} n={row["n"]:5} classes={row["classes"]} majority {maj:.3f} | trained by layer ' +
              ' '.join(f'{v:.3f}' for v in row['trained']) + ' | untrained ' + ' '.join(f'{v:.3f}' for v in row['untrained']), flush=True)
    return res


@torch.no_grad()
def reach(name):
    sd = torch.load(os.path.join(HERE, 'models', name + '.pt'), map_location='cpu'); vocab = sd['vocab']; T.D, T.L = sd.get('d', T.D), sd.get('layers', T.L)
    m = T.GPT(len(vocab)); m.load_state_dict(sd['state']); m.eval()
    _, _, _, test = T.load(sd.get('name', name)); nl = vocab.index('\n')
    dist = np.zeros((T.L, T.NH)); prev = np.zeros((T.L, T.NH)); n = 0
    idx = torch.arange(T.CTX)
    for p in test:
        for s in range(0, len(p) - T.CTX, 512):
            x = torch.tensor(p[s:s + T.CTX])[None]
            _, _, ws = m(x, need=True)
            line = torch.cumsum((x[0] == nl).long(), 0)          # line number of each position
            q = torch.arange(128, T.CTX)                         # queries with at least 128 chars of context
            d = (q[:, None] - idx[None, :]).clamp(min=0).float()
            pl = (line[idx][None, :] == (line[q] - 1)[:, None]).float()
            for l, w in enumerate(ws):
                w = w[0][:, q]                                   # (heads, q, keys)
                dist[l] += (w * d).sum(-1).mean(-1).numpy(); prev[l] += (w * pl).sum(-1).mean(-1).numpy()
            n += 1
    return (dist / n).tolist(), (prev / n).tolist()


def main():
    tag = sys.argv[sys.argv.index('--model') + 1] if '--model' in sys.argv else 'voynich'
    out = {'probes': probes(tag), 'reach': {}}
    for name in sorted(f[:-3] for f in os.listdir(os.path.join(HERE, 'models')) if f.endswith('.pt')):
        d, pl = reach(name); out['reach'][name] = {'mean_distance': d, 'prev_line_share': pl}
        print(f'{name:18} mean look-back by layer (max head): ' + ' '.join(f'{max(r):5.1f}' for r in d) +
              ' | previous-line share (max head): ' + ' '.join(f'{max(r):.2f}' for r in pl), flush=True)
    json.dump(out, open(os.path.join(HERE, 'results', 'probe.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
