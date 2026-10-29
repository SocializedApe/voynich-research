"""Build the early-modern Dutch prose corpus for the nl-1600 model.

DBNL full texts (dbnl.org/nieuws/text.php?id=...) carry modern editorial introductions and notes, so only paragraphs
whose spelling is clearly early-modern are kept: at least 6 markers (ck, gh, ae, uy, ey, ooc, sy, ende) per 100
words, and no modern-only spellings (oo/ee before final consonant clusters are not tested; the marker rate does the
work). Output: lang/corpora/nl-1600-prose.txt.  Run: python -m lang.build_nl1600
"""
import os, re, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'corpora', 'nl-1600-prose.txt')
DBNL = {
    'marn001bien01': 'Marnix, Biënkorf der H. Roomsche Kercke (1569)',
    'coor001zede01': 'Coornhert, Zedekunst dat is Wellevenskunste (1586)',
    'mand001schi01': 'Van Mander, Het Schilder-boeck (1604)',
    'bred001spaa01': 'Bredero, Spaanschen Brabander (1617)',
    'hoof001nede01': 'Hooft, Nederlandsche Historien (1642)',
}
MARK = re.compile(r'ck|gh|ae|uy|ey|\booc\b|\bsy\b|\bende\b', re.I)


def get(i):
    req = urllib.request.Request(f'https://www.dbnl.org/nieuws/text.php?id={i}', headers={'User-Agent': 'Mozilla/5.0'})
    return urllib.request.urlopen(req, timeout=120).read().decode('utf-8', 'replace')


def keep(par):
    words = par.split()
    if len(words) < 12:
        return False
    return len(MARK.findall(par)) * 100 / len(words) >= 6


def main():
    out = []
    for i, title in DBNL.items():
        t = re.sub(r'\{==[^}]*==\}|\{>>[^}]*<<\}', ' ', get(i))
        pars = [re.sub(r'\s+', ' ', p).strip() for p in re.split(r'\n\s*\n', t)]
        kept = [p for p in pars if keep(p)]
        print(i, title, len(pars), 'paragraphs,', len(kept), 'kept,', sum(len(p) for p in kept), 'chars')
        out += kept
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'w', encoding='utf-8').write('\n\n'.join(out))
    print('wrote', OUT, sum(len(p) for p in out), 'chars')


if __name__ == '__main__':
    main()
