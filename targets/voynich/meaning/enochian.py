"""Enochian (Dee and Kelley, 1584): extract Dee's text of the Calls and compare its statistics with Voynich and the
gibberish volunteers.

Source: Christeos Pir, 'An Essay on Enochian Pronunciation' (sacred-texts.com/pag/pr_calls.txt, fetched 28 Oct 2026
into data/enochian), which prints every line of the Calls three times: Aurum Solis, Geoffrey James, and Dee's original
as printed in Casaubon's True and Faithful Relation (1659). Dee's version is the last on each line, in lower case or
capitalised words (Aurum Solis words carry ^ # or inner capitals, James's are all capitals). Extraction: from the end
of each line, the run of words of Dee's form; syllable hyphens joined; bracketed variants dropped.

Statistics on 1,000-word samples (Voynich: herbal A and herbal B paragraph text; gibberish: the 30 volunteers with at
least 200 words pooled; Latin and Italian controls): h1 and h2 of letters/glyph units (bits, word-internal plus word
edges), type-token ratio, hapax share, mean word length, share of adjacent identical words, and Zipf slope over the
top 50 ranks. Enochian has one 'scribe' (Kelley's dictation, Dee's notes), so no scribe test.

Run from the repository root: python targets/voynich/meaning/enochian.py
"""
import collections, csv, html, math, os, random, re, statistics, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'glyphs')); sys.path.insert(0, os.path.join(HERE, '..'))
from variants import UNIT
import pliny
import a4_selfcitation as a4

SRC = os.path.join(HERE, 'data', 'enochian', 'pr_calls.txt')
DEE_WORD = re.compile(r"^(?:[a-z][a-z\-]*|[A-Z][a-z\-]*|I)$")


def dee_text():
    t = open(SRC, encoding='utf-8', errors='replace').read()
    s = html.unescape(re.sub(r'<[^>]+>', '\n', t))
    s = s[s.find('First Call'):]
    calls, cur, name = {}, [], None
    for line in s.split('\n'):
        line = line.strip()
        m = re.match(r'^(\w+(?:-\w+)?) Call$', line)
        if m:
            if name: calls[name] = cur
            name, cur = m.group(1), []; continue
        if not line or name is None: continue
        line = re.sub(r'\([^)]*\)', '', line)
        toks = [re.sub(r'[,.:;!?]', '', x) for x in line.split()]
        run = []
        for tk in reversed(toks):
            if not tk: continue
            if DEE_WORD.match(tk): run.append(tk)
            else: break
        cur += [w.replace('-', '').lower() for w in reversed(run) if w.replace('-', '')]
    if name: calls[name] = cur
    return calls


def units_voy(w): return UNIT.findall(w)


def stats(words, split):
    c1 = collections.Counter(); c2 = collections.Counter(); ctx = collections.Counter()
    for w in words:
        u = ['#'] + split(w) + ['#']
        c1.update(u[1:-1]); c2.update(zip(u, u[1:])); ctx.update(u[:-1])
    n1 = sum(c1.values()); h1 = -sum(v / n1 * math.log2(v / n1) for v in c1.values())
    n2 = sum(c2.values()); h2 = -sum(v / n2 * math.log2(v / ctx[a]) for (a, b), v in c2.items())
    f = collections.Counter(words); ranks = [v for _, v in f.most_common(50)]
    xs = [math.log(i + 1) for i in range(len(ranks))]; ys = [math.log(v) for v in ranks]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return {'h1': h1, 'h2': h2, 'ttr': len(f) / len(words), 'hapax': sum(1 for v in f.values() if v == 1) / len(f),
            'len': statistics.mean(map(len, words)), 'adj_rep': sum(a == b for a, b in zip(words, words[1:])) / (len(words) - 1),
            'zipf50': slope}


def main():
    calls = dee_text()
    eno = [w for k, ws in calls.items() for w in ws]
    print(f'Enochian (Dee): {len(calls)} calls, {len(eno)} words, {len(set(eno))} types; first call: {" ".join(calls.get("First", [])[:20])}')
    rng = random.Random(5); N = min(1000, len(eno))
    rows = [r for r in csv.DictReader(open(os.path.join(HERE, '..', 'data', 'ZL3b-n.fixed.words.tsv'), encoding='utf-8'), delimiter='\t')
            if r['locus_type'] == 'P' and r['illus'] == 'H']
    W = lambda lang: [w for r in rows if r['lang'] == lang for w in r['line_words'].split() if re.fullmatch(r'[a-z]+', w)]
    z = zipfile.ZipFile(os.path.join(HERE, 'data', 'gaskell_bowern', 'gibberish_transcriptions.zip'))
    gib = [w for n in z.namelist() if not n.endswith('/') for w in re.findall(r'[a-z]+', z.read(n).decode('utf-8', 'replace').lower())]
    lat = [w for b in pliny.STREAM for c in pliny.chapters(b) for w in pliny.latin_words(c)]
    ita = a4.lang_words('it', 5000)
    def cont(ws):
        k = rng.randrange(0, len(ws) - N); return ws[k:k + N]
    texts = [('Enochian (Dee 1584)', eno[:N], list), ('Voynich herbal A', cont(W('A')), units_voy), ('Voynich herbal B', cont(W('B')), units_voy),
             ('Gibberish volunteers (pooled)', cont(gib), list), ('Latin (Pliny)', cont(lat), list), ('Italian', cont(ita), list)]
    print(f'\n{N}-word samples | ' + ' | '.join(['h1', 'h2', 'h1-h2', 'TTR', 'hapax/types', 'mean len', 'adjacent repeats', 'Zipf slope (top 50)']))
    for name, ws, sp in texts:
        s = stats(ws, sp)
        print(f'{name:30} {s["h1"]:.2f} | {s["h2"]:.2f} | {s["h1"] - s["h2"]:.2f} | {s["ttr"]:.2f} | {s["hapax"]:.2f} | {s["len"]:.2f} | {s["adj_rep"]:.3f} | {s["zipf50"]:.2f}')


if __name__ == '__main__':
    main()
