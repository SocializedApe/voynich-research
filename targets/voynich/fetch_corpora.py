"""Fetch the comparison corpora the Voynich scripts read, into data/corpora (git-ignored).

The September 2026 session kept them in a scratchpad that no longer exists; the Gutenberg ids below
are the ones its result files name (corp_<lang>_<id>.txt).  Run once:  python fetch_corpora.py
Files that are already present are skipped.  Every file is plain text, read as data only.
"""
import bz2, os, sys, time, urllib.request, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
CORP = os.path.join(HERE, 'data', 'corpora')

GUTENBERG = {
    'da': [24747, 36942, 41072, 44967, 66058],
    'de': [35312, 50285, 56156, 66452],
    'en': [1342, 2554, 2701],
    'fi': [75789, 78071],
    'fr': [18143, 19919, 62215, 78027],
    'is': [15178, 16696, 16846, 17025, 19960],
    'la': [227, 33849, 50280],
    'nl': [76186, 76280, 76761, 76765],
    'no': [30027, 43724, 59635, 77368],
    'sv': [48961, 59341, 62635, 62806],
}

# c1_comparators.py (October 2026): low-h2 languages and constructed languages.
# eBible.org "readaloud" texts (one plain-text file per chapter): bible_<code>.txt
EBIBLE = {
    'haw': 'haw1868',   # Hawaiian, Baibala Hemolele 1868 revision, public domain
    'ton': 'ton',       # Tongan, Revised West Version, public domain
    'mri': 'mri',       # Maori New Testament (Bible Society NZ, redistributable)
    'tsn': 'tsn',       # Setswana New Testament (Biblica Open, redistributable)
    'swh': 'swh1850',   # Swahili New Testament 1850, public domain
    'epo': 'epo',       # Esperanto, Zamenhof's Bible, public domain
    'lat': 'latVUC',    # Latin Vulgate (Clementine), public domain: same-genre Latin control
}
# Tatoeba per-language sentence exports (CC BY 2.0 FR): tatoeba_<code>.txt, one sentence per line
TATOEBA = ['tok', 'jbo', 'vol']   # Toki Pona, Lojban, Volapuk

# Voynich transliterations: raw IVTFF into data/<name>.txt (b1 reads the raw ZL for its uncertain spaces),
# parsed by parse_ivtff.py into data/<name>.words.tsv.  voynich.nu refuses requests without browser headers.
IVTFF = ['RF1b-er', 'GC2a-n', 'CD2a-n', 'IT2a-n', 'ZL3b-n']
BROWSER = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/126.0 Safari/537.36', 'Accept': 'text/html,text/plain,*/*', 'Accept-Language': 'en-US,en;q=0.9'}

UA = 'Mozilla/5.0 (cyphersolver corpus fetch; research use)'


def get(url, dest, headers=None):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return False
    req = urllib.request.Request(url, headers=headers or {'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    with open(dest, 'wb') as f:
        f.write(data)
    return True


IT_SOURCE = os.path.join(HERE, '..', 'vatican5', 'corpus_it.txt')  # git-ignored; built by vatican5/build_it_lm.py
IT_ANCHOR = 'cumque predictus fcrdiuandu s rex nuper in romanorum regem'  # first words of the September 2026 sample


def freeze_italian():
    """The Italian control is the vatican5 Nuntiaturberichte OCR corpus, which build_it_lm.py rebuilds with its
    documents in a different order.  The September scripts took 'the first N tokens'; that sample begins at these
    words (results/v_a4.md), so the frozen copy starts there and every Italian figure reproduces."""
    dest = os.path.join(CORP, 'corpus_it.txt')
    if os.path.exists(dest):
        return
    if not os.path.exists(IT_SOURCE):
        print('MISSING', IT_SOURCE, '(build it with targets/vatican5/build_it_lm.py)', file=sys.stderr); return
    text = open(IT_SOURCE, encoding='utf-8', errors='replace').read()
    i = text.find(IT_ANCHOR)
    if i < 0:
        print('Italian anchor not found; the September sample cannot be rebuilt from this corpus build', file=sys.stderr); return
    with open(dest, 'w', encoding='utf-8') as f:
        f.write(text[i:])
    print('froze corpus_it.txt from offset', i)


def main():
    os.makedirs(CORP, exist_ok=True)
    freeze_italian()
    sys.path.insert(0, HERE)
    import parse_ivtff
    for name in IVTFF:
        raw = os.path.join(HERE, 'data', name + '.txt')
        if get(f'https://www.voynich.nu/data/{name}.txt', raw, BROWSER):
            print('fetched', name, os.path.getsize(raw))
        tsv = os.path.join(HERE, 'data', name + '.words.tsv')
        if name == 'ZL3b-n' or os.path.exists(tsv):
            continue  # the committed ZL TSV (version of 13 May 2025) is the reference text; the raw file is kept to compare
        with open(tsv, 'w', encoding='utf-8') as f:
            f.write('\t'.join(['folio', 'line_id', 'locus_type', 'lang', 'hand', 'illus', 'quire',
                               'para_start', 'para_end', 'line_words']) + '\n')
            for r in parse_ivtff.parse(raw):
                f.write('\t'.join(map(str, r)) + '\n')
        print('parsed', name)
    for lang, ids in GUTENBERG.items():
        for i in ids:
            dest = os.path.join(CORP, f'corp_{lang}_{i}.txt')
            for host in ('gutenberg.pglaf.org', 'www.gutenberg.org'):  # www often answers 503 to scripts
                try:
                    if get(f'https://{host}/cache/epub/{i}/pg{i}.txt', dest):
                        print('fetched', os.path.basename(dest), os.path.getsize(dest))
                        time.sleep(2)
                    break
                except Exception as e:
                    print('FAILED', host, lang, i, e, file=sys.stderr)
    for code, tid in EBIBLE.items():
        dest = os.path.join(CORP, f'bible_{code}.txt')
        if os.path.exists(dest):
            continue
        zpath = os.path.join(CORP, f'_ebible_{tid}.zip')
        try:
            get(f'https://ebible.org/Scriptures/{tid}_readaloud.zip', zpath)
        except Exception as e:
            print('FAILED ebible', tid, e, file=sys.stderr); continue
        with zipfile.ZipFile(zpath) as z:
            names = sorted(n for n in z.namelist() if n.endswith('_read.txt') and '_000_000_000_' not in n)
            text = '\n'.join(z.read(n).decode('utf-8-sig', 'replace') for n in names)
        with open(dest, 'w', encoding='utf-8') as f:
            f.write(text)
        os.remove(zpath)
        print('fetched', os.path.basename(dest), len(names), 'chapters')
        time.sleep(1)
    for code in TATOEBA:
        dest = os.path.join(CORP, f'tatoeba_{code}.txt')
        if os.path.exists(dest):
            continue
        bz = os.path.join(CORP, f'_tatoeba_{code}.tsv.bz2')
        try:
            get(f'https://downloads.tatoeba.org/exports/per_language/{code}/{code}_sentences.tsv.bz2', bz)
        except Exception as e:
            print('FAILED tatoeba', code, e, file=sys.stderr); continue
        rows = bz2.decompress(open(bz, 'rb').read()).decode('utf-8', 'replace').splitlines()
        sents = [r.split('\t')[2] for r in rows if r.count('\t') >= 2]
        with open(dest, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sents) + '\n')
        os.remove(bz)
        print('fetched', os.path.basename(dest), len(sents), 'sentences')


if __name__ == '__main__':
    main()
