"""Fetch line-by-line transcriptions of real medieval manuscripts (ground truth for handwriting recognition) and keep
the text of their main-text lines. (11 Nov 2026)

Sources: HTR-United / CREMMA Medieval (Old French, 12th-15th c.; Pinche et al.) and CREMMA Medii Aevi (Latin,
9th-15th c.; Clerice et al.), both CC BY 4.0, ALTO XML with one TextLine per manuscript line,
transcribed graphically (abbreviations, word separation and line breaks as in the manuscript).
  https://github.com/HTR-United/cremma-medieval      https://github.com/HTR-United/cremma-medieval-lat
Only the text is kept (no XML, no images): data/external/cremma/<repo>__<manuscript>.tsv with columns page file,
block index, block type, line type, line width in pixels, text. data/external/ is git-ignored.

Run from targets/voynich: python lines/fetch_mss.py   (about 400 files, 20 MB of traffic)
"""
import csv, json, os, re, sys, time, urllib.request
import xml.etree.ElementTree as ET
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'data', 'external', 'cremma')
REPOS = ('cremma-medieval', 'cremma-medieval-lat')


def get(url, tries=4):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'voynich-research'}), timeout=60).read()
        except Exception as e:
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))


def lines_of(xml):
    root = ET.fromstring(xml); ns = {'a': root.tag.split('}')[0].strip('{')}
    tags = {t.get('ID'): t.get('LABEL') for t in root.iter() if t.tag.endswith('OtherTag')}
    out = []
    for bi, blk in enumerate(root.iterfind('.//a:TextBlock', ns)):
        bt = tags.get((blk.get('TAGREFS') or '').split(' ')[0], '')
        for ln in blk.iterfind('a:TextLine', ns):
            lt = tags.get((ln.get('TAGREFS') or '').split(' ')[0], '')
            text = ' '.join(s.get('CONTENT') or '' for s in ln.iterfind('a:String', ns)).strip()
            if text:
                out.append((bi, bt, lt, ln.get('WIDTH') or '', text))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    for repo in REPOS:
        tree = json.loads(get(f'https://api.github.com/repos/HTR-United/{repo}/git/trees/HEAD?recursive=1'))['tree']
        files = sorted(e['path'] for e in tree if e['path'].startswith('data/') and e['path'].endswith('.xml') and '.chocomufin.' not in e['path'])
        by = {}
        for f in files:
            by.setdefault(f.split('/')[1], []).append(f)
        for ms, fs in by.items():
            dest = os.path.join(OUT, f'{repo}__{ms}.tsv')
            if os.path.exists(dest):
                continue
            rows = []
            for f in fs:
                for r in lines_of(get(f'https://raw.githubusercontent.com/HTR-United/{repo}/HEAD/' + urllib.request.quote(f))):
                    rows.append((os.path.basename(f),) + r)
            with open(dest, 'w', encoding='utf-8', newline='') as o:
                w = csv.writer(o, delimiter='\t'); w.writerow(['page', 'block', 'block_type', 'line_type', 'width_px', 'text']); w.writerows(rows)
            print(repo, ms, len(fs), 'pages', len(rows), 'lines', flush=True)


if __name__ == '__main__':
    main()
