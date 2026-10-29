"""Comparable texts for the transformer study: same length (N characters), lines broken as in Voynich.

Each text is a string of lowercase letters, ' ' and '\\n' (line break). Voynich lines keep their manuscript breaks;
other texts are cut into lines whose lengths cycle through the Voynich line lengths, at word boundaries.
Names: voynich, voynich_shufline (words shuffled within each line), voynich_shufpage (words shuffled within each
page), latin, italian, naibbe (Greshko's cipher of Latin), rugg (Rugg sorted grille), autocopist (Timm & Schinner).

Run from the repository root: python targets/voynich/tfm/texts.py   (writes targets/voynich/tfm/data/<name>.txt)
"""
import os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'research', 'voynich_siblings', 'attack'))
N = 180000
NAIBBE_CSV = os.environ.get('NAIBBE_CSV', '')


def voy_pages():
    import a4_selfcitation as a4
    return a4, a4.load_zl()


def join_pages(pages):
    return '\n'.join(' '.join(ln['words']) for p in pages for ln in p['lines'])


def line_lengths():
    a4, pages = voy_pages()
    return [len(' '.join(ln['words'])) for p in pages for ln in p['lines']]


def into_lines(words, lens):
    out, cur, k = [], [], 0
    for w in words:
        cur.append(w)
        if len(' '.join(cur)) >= lens[k % len(lens)]:
            out.append(' '.join(cur)); cur = []; k += 1
    return '\n'.join(out)


def lang_words(src):
    from lang import lm, corpora
    t = lm.norm(corpora.text([src])[:3000000], 'early', True).split()
    return t[len(t) // 5:]


def build(name):
    a4, pages = voy_pages(); rng = random.Random(11)
    if name == 'voynich':
        s = join_pages(pages)
    elif name in ('voynich_shufline', 'voynich_shufpage'):
        pp = []
        for p in pages:
            lines = [ln['words'][:] for ln in p['lines']]
            if name == 'voynich_shufline':
                for ws in lines: rng.shuffle(ws)
            else:
                flat = [w for ws in lines for w in ws]; rng.shuffle(flat); it = iter(flat)
                lines = [[next(it) for _ in ws] for ws in lines]
            pp.append({'lines': [{'words': ws} for ws in lines]})
        s = join_pages(pp)
    elif name == 'latin':
        s = into_lines(lang_words('la-gutenberg'), line_lengths())
    elif name == 'italian':
        s = into_lines(lang_words('it-renaissance'), line_lengths())
    elif name == 'naibbe':
        import run_merged as rm
        toks, _ = rm.synth_tokens(NAIBBE_CSV, 1)
        s = into_lines(toks, line_lengths())
    elif name in ('rugg', 'autocopist'):
        gen = a4.RuggSorted(19) if name == 'rugg' else a4.Autocopist(19)
        s = join_pages(gen.generate(a4.skeleton(pages)))
    else:
        raise SystemExit(f'unknown text {name}')
    s = s[:N]
    assert len(s) == N, (name, len(s))
    return s


def main():
    os.makedirs(os.path.join(HERE, 'data'), exist_ok=True)
    for name in sys.argv[1:] or ['voynich', 'voynich_shufline', 'voynich_shufpage', 'latin', 'italian', 'naibbe', 'rugg', 'autocopist']:
        s = build(name)
        open(os.path.join(HERE, 'data', name + '.txt'), 'w', encoding='utf-8').write(s)
        print(f'{name:18} {len(s)} chars, {len(set(s))} symbols, {s.count(chr(10)) + 1} lines, {len(s.split())} words')


if __name__ == '__main__':
    main()
