"""Repeated word phrases: does any text or generator lack them the way Voynich does?

Count of distinct word n-grams (n 2-5) that occur at least twice, at matched length (first 30,000 tokens; language
corpora from token 5,000 to skip front matter), and per 250-word document (200 random windows; Gaskell & Bowern
gibberish volunteers with at least 250 words, first 250 each). Texts: tfm/data (ZL Voynich, Naibbe, autocopist, Rugg
as generated there), the repo's corpora. Finnish corpora excluded: they are mostly Project Gutenberg licence text.

Run from the repository root: python targets/voynich/meaning/phrase_repeats.py
"""
import collections, json, os, random, re, statistics, zipfile
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, '..', 'data')
N, DOC = 30000, 250


def toks(p, skip):
    return re.findall(r'[a-zà-ÿþðæ]+', open(p, encoding='utf-8', errors='ignore').read().lower())[skip:]


def rep(w, n):
    return sum(v >= 2 for v in collections.Counter(tuple(w[i:i + n]) for i in range(len(w) - n + 1)).values())


def main():
    T = {'Voynich (ZL)': toks(os.path.join(HERE, '..', 'tfm', 'data', 'voynich.txt'), 0)}
    for nm, f in (('Latin (Vulgate)', 'bible_lat.txt'), ('Italian', 'corpus_it.txt'), ('English', 'corp_en_1342.txt'),
                  ('German', 'corp_de_35312.txt'), ('Icelandic', 'corp_is_15178.txt')):
        T[nm] = toks(os.path.join(D, 'corpora', f), 5000)
    for g in ('naibbe', 'autocopist', 'rugg'):
        T[g + ' (generator)'] = toks(os.path.join(HERE, '..', 'tfm', 'data', g + '.txt'), 0)
    out = {'matched': {}, 'documents': {}}
    print(f'{"text":24} tokens  types | repeated n-gram types: 2 3 4 5')
    for nm, w in T.items():
        w = w[:N]; r = [rep(w, n) for n in (2, 3, 4, 5)]
        out['matched'][nm] = {'tokens': len(w), 'types': len(set(w)), 'rep': r}
        print(f'{nm:24} {len(w):6} {len(set(w)):6} | {r}')
    z = zipfile.ZipFile(os.path.join(HERE, 'data', 'gaskell_bowern', 'gibberish_transcriptions.zip'))
    G = [re.findall(r'[a-z]+', z.read(n).decode('utf-8', 'ignore').lower()) for n in z.namelist() if n.endswith('.txt')]
    docs = {f'gibberish volunteers ({sum(len(g) >= DOC for g in G)})': [g[:DOC] for g in G if len(g) >= DOC]}
    rng = random.Random(1)
    for nm in ('Voynich (ZL)', 'Latin (Vulgate)', 'Italian', 'Icelandic', 'naibbe (generator)'):
        w = T[nm][:N]; docs[nm] = [w[s:s + DOC] for s in (rng.randrange(len(w) - DOC) for _ in range(200))]
    print(f'\nper {DOC}-word document, mean repeated n-gram types (2, 3, 4)')
    for nm, ds in docs.items():
        r = [statistics.mean(rep(d, n) for d in ds) for n in (2, 3, 4)]
        out['documents'][nm] = r
        print(f'  {nm:28} ' + ' '.join(f'{x:5.2f}' for x in r))
    json.dump(out, open(os.path.join(HERE, 'phrase_repeats_results.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
