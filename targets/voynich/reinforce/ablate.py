"""Which levels of the hierarchy carry Voynich's word re-use? Held-out likelihood with level ablations. (10 Nov 2026)

The HPY of hpy.py is fitted with some levels removed (the tree collapses past them) and scored on held-out pages:
every fifth page (by manuscript order) is held out; the model is fitted on the rest (Gibbs sweeps as hpy.fit);
then each held-out page is predicted token by token in order (its page and line nodes start empty, so what helps
is what the quire, section and hand nodes know, plus the re-use inside the page as it is read), log2 probabilities
summed, the page removed again. Base distribution G0 uniform over the training types, unseen words get 1/(V+1).

Variants: full (book > hand > section > quire > page > line); -line; -page; -quire; -section; -hand; flat (book
only); and 'book+page+line' (no scribe or codicological levels at all). A level's contribution = gain in bits per
token when it is present. Texts: Voynich and the controls poured into the same skeleton, so the only thing that
differs is which words sit where.

Run from targets/voynich: python reinforce/ablate.py [text ...] -> reinforce/ablate_results.json, ablate.md
"""
import collections, json, math, os, random, statistics, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'lines'))
import hpy, common

ALL = ['book', 'hand', 'section', 'quire', 'page', 'line']
VARIANTS = collections.OrderedDict([
    ('full', ALL), ('-line', ['book', 'hand', 'section', 'quire', 'page']), ('-page', ['book', 'hand', 'section', 'quire', 'line']),
    ('-quire', ['book', 'hand', 'section', 'page', 'line']), ('-section', ['book', 'hand', 'quire', 'page', 'line']),
    ('-hand', ['book', 'section', 'quire', 'page', 'line']), ('book+page+line', ['book', 'page', 'line']), ('flat', ['book'])])
SWEEPS = int(os.environ.get('HPY_SWEEPS', '60'))
ONLY = os.environ.get('ABLATE_VARIANTS')  # comma-separated subset of variants, for the controls


def paths(pgs, levels):
    data = []
    for pi, p in enumerate(pgs):
        full = {'book': 'book', 'hand': 'h' + p['hand'], 'section': 's' + p['illus'], 'quire': 'q' + p['quire'], 'page': p['folio']}
        for li, ln in enumerate(p['lines']):
            full['line'] = f'l{li}'
            path = tuple(full[l] for l in levels)
            for w in ln['words']:
                data.append((path, w))
    return data


class G0:
    def __init__(self, types):
        self.p = 1.0 / len(types); self.pu = 1.0 / (len(types) + 1); self.types = set(types)

    def __getitem__(self, w):
        return self.p if w in self.types else self.pu


def fit_eval(train, test, levels, rng, sweeps):
    tr = paths(train, levels); te = paths(test, levels)
    types = sorted({w for _, w in tr})
    m = hpy.HPY([0.5] * len(levels), [1.0] * len(levels), G0(types))
    for path, w in tr:
        m.add(m.node(path), w, rng)
    order = list(range(len(tr)))
    for s in range(sweeps):
        rng.shuffle(order)
        for i in order:
            path, w = tr[i]; n = m.nodes[path]; m.remove(n, w, rng); m.add(n, w, rng)
        m.resample_hyper(rng)
    # held-out: page by page, sequential prediction then removal
    tot = 0.0; n = 0
    by_page = collections.OrderedDict()
    for path, w in te:
        by_page.setdefault(path[:len(levels) - 1] if 'line' in levels else path, []).append((path, w))
    # group by page: the page key is the path without the line component (or the full path if no line level)
    for key, toks in by_page.items():
        added = []
        for path, w in toks:
            node = m.node(path); tot += math.log2(max(m.prob(node, w), 1e-300)); n += 1
            m.add(node, w, rng); added.append((node, w))
        for node, w in added:
            m.remove(node, w, rng)
    return dict(bits_per_token=-tot / n, test_tokens=n, train_tokens=len(tr), d=m.d, theta=m.theta)


def main():
    t0 = time.time()
    ref = common.pages()
    want = sys.argv[1:] or ['voynich', 'latin', 'english', 'naibbe', 'autocopist_s19', 'gibberish']
    texts = collections.OrderedDict()
    if 'voynich' in want:
        texts['voynich'] = ref
    texts.update(common.controls(ref, which=tuple(w for w in want if w != 'voynich')))
    out_path = os.path.join(HERE, 'ablate_results.json')
    res = json.load(open(out_path)) if os.path.exists(out_path) else {}
    for name, pgs in texts.items():
        test = [p for i, p in enumerate(pgs) if i % 5 == 2]; train = [p for i, p in enumerate(pgs) if i % 5 != 2]
        res.setdefault(name, {})
        for vname, levels in VARIANTS.items():
            if vname in res[name] or (ONLY and vname not in ONLY.split(',')):
                continue
            r = fit_eval(train, test, levels, random.Random(3), SWEEPS)
            res[name][vname] = r
            print(f'{name:16s} {vname:16s} held-out bits/token {r["bits_per_token"]:.3f}  ({time.time() - t0:.0f}s)', flush=True)
            json.dump(res, open(out_path, 'w'), indent=1)
    L = ['# Held-out bits per token of the hierarchical Pitman-Yor model, by hierarchy variant (10 Nov 2026)', '',
         f'Script `ablate.py` ({SWEEPS} sweeps; every fifth page held out and predicted token by token). Lower is better; the gain of a level = bits saved when it is present.', '']
    L.append('| text | ' + ' | '.join(VARIANTS) + ' | gain line | gain page | gain quire | gain section | gain hand | hierarchy vs flat |')
    L.append('|---|' + '---|' * (len(VARIANTS) + 6))
    for name, R in res.items():
        b = {v: R[v]['bits_per_token'] for v in VARIANTS if v in R}
        g = lambda a, c: f"{b[a] - b[c]:+.3f}" if a in b and c in b else '-'
        gains = [g('-line', 'full'), g('-page', 'full'), g('-quire', 'full'), g('-section', 'full'), g('-hand', 'full'), g('flat', 'full')]
        L.append(f'| {name} | ' + ' | '.join(f'{b[v]:.3f}' if v in b else '-' for v in VARIANTS) + ' | ' + ' | '.join(gains) + ' |')
    L.append(''); L.append(f'Runtime {time.time() - t0:.0f} s.')
    open(os.path.join(HERE, 'ablate.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    main()
