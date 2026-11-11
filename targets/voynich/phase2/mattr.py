"""Moving-average type-token ratio (MATTR; Covington & McFall 2010) of Voynich against 50 languages. (12 Nov 2026)

MATTR(w) = mean, over every window of w consecutive words, of distinct words / w: vocabulary variety that does not
depend on text length. Windows 50, 200, 500, 2000 on the first 30,000 words of each Bible-corpus language
(phase2/corpora2.py), on Voynich (ZL paragraph text, all, Currier A, Currier B) and on the held-out Voynich-like
texts. For each window: Voynich's value, its rank among the languages, and the five nearest languages.

Run from targets/voynich: python phase2/mattr.py -> phase2/mattr.md
"""
import collections, glob, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..')
sys.path.insert(0, HERE); sys.path.insert(0, VOY); sys.path.insert(0, os.path.join(VOY, 'lines'))
import build, common
WINS = (50, 200, 500, 2000); N = 30000


def mattr(ws, w):
    if len(ws) < w:
        return None
    c = collections.Counter(ws[:w]); tot = len(c); n = 1
    for i in range(w, len(ws)):
        a = ws[i - w]; c[a] -= 1
        if not c[a]:
            del c[a]
        c[ws[i]] += 1; tot += len(c); n += 1
    return tot / n / w


def main():
    langs = {os.path.basename(p)[:-4]: build.read_words(p)[:N] for p in sorted(glob.glob(os.path.join(VOY, 'data', 'external', 'bible', '*.txt')))}
    ref = common.pages(); flat = lambda pp: [w for p in pp for ln in p['lines'] for w in ln['words']]
    own = collections.OrderedDict([('Voynich (all)', flat(ref)[:N]), ('Voynich A', flat([p for p in ref if p['lang'] == 'A'])), ('Voynich B', flat([p for p in ref if p['lang'] == 'B'])[:N])])
    for name, f in (('Naibbe cipher of Pliny', 'naibbe.txt'), ('Rugg table text', 'rugg.txt'), ('autocopist', 'autocopist.txt')):
        own[name] = open(os.path.join(VOY, 'tfm', 'data', f), encoding='utf-8').read().split()[:N]
    L = ['# MATTR of Voynich against 50 languages (12 Nov 2026)', '', 'Script `mattr.py` (definition in its docstring). Reproduce: `python phase2/corpora2.py`, `python phase2/mattr.py` from `targets/voynich`.', '',
         '| text | ' + ' | '.join(f'MATTR {w}' for w in WINS) + ' |', '|---|' + '---|' * len(WINS)]
    val = {k: {w: mattr(ws, w) for w in WINS} for k, ws in list(own.items()) + list(langs.items())}
    for k in own:
        L.append(f'| {k} | ' + ' | '.join(f'{val[k][w]:.3f}' for w in WINS) + ' |')
    for k in ('Latin', 'Italian', 'German', 'English', 'Hebrew', 'Turkish', 'Finnish', 'Vietnamese-tok', 'Chinese-tok'):
        L.append(f'| {k} | ' + ' | '.join(f'{val[k][w]:.3f}' for w in WINS) + ' |')
    L += ['', '| window | languages: min / median / max | Voynich (all): rank from the lowest of 51 | five nearest languages |', '|---|---|---|---|']
    for w in WINS:
        xs = sorted((val[k][w], k) for k in langs); v = val['Voynich (all)'][w]
        near = sorted(langs, key=lambda k: abs(val[k][w] - v))[:5]
        L.append(f"| {w} | {xs[0][0]:.3f} / {xs[len(xs) // 2][0]:.3f} / {xs[-1][0]:.3f} | {1 + sum(1 for x, _ in xs if x < v)} | " + ', '.join(f'{k} {val[k][w]:.3f}' for k in near) + ' |')
    open(os.path.join(HERE, 'mattr.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    main()
