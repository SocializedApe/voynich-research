"""Leaf-wise topical plaintext: does real subject structure produce Voynich's leaf and section vocabulary?

Protocol, fixed before the run (28 Oct 2026):
  Source: Pliny, Naturalis Historia (Latin Wikisource, raw wikitext in data/pliny_raw, fetched 28 Oct 2026), one author
  with changing subjects. Section of each ZL page = ZL illustration type; sources by section:
    H herbal <- books XX-XXIII (plants); P pharmaceutical <- XXIV-XXV; S, T recipes/text <- XXVI-XXVII (remedies by
    disease); A, C, Z astronomical/cosmological/zodiac <- II (the heavens); B balneological <- XXXI (waters; no chapter
    marks, so groups of 3 numbered paragraphs count as chapters).
  sectioned: leaves (f<n>, all its pages) in manuscript order; every leaf starts a new chapter of its section's queue
    (chapters in book order, cycled if exhausted) and takes whole chapters until its pages are filled; leftovers dropped.
  stream (control): the same books concatenated in book order (II, XX-XXVII, XXXI) as one text, poured page after
    page with no regard to leaves or sections.
  Versions: plain Latin words (lang.lm.norm 'latin'); code + scribe (Voynich word types as codes, rank to rank, template
    codes for the extra Latin types, as codebook.py); cipher + scribe (round-8 letter cipher of cipher_models, run leaf by
    leaf for 'sectioned'). Scribe = hybrid_model setting q 0.15, w 8, e 0.9, g 0.2 (drift.scribe, carry 0, habit 0).
  Scores: order.items (j_jacc_excess, leaf_excess, k_jsd_halves, h_peak_R) in the current order, k_jsd_halves under 10
  within-section page shuffles, swap.run page context (d>30), b3.battery + b3.score (37 items).
  Expectation: if missing topic structure is what the models lack, sectioned versions move toward Voynich on
  leaf_excess and the section-shuffled drift, and stream versions do not.

Run from the repository root: python targets/voynich/meaning/pliny.py <naibbe_tables.csv>
"""
import collections, contextlib, csv, glob, io, json, os, random, re, statistics, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'research', 'voynich_siblings'))
import codebook as cbk, drift, order, swap
import a4_selfcitation as a4
import b3_bakeoff as b3
import hybrid_model as hm
import cipher_models as cm
from lang import lm

RAW = os.path.join(HERE, 'data', 'pliny_raw')
SRC = {'H': ['XX', 'XXI', 'XXII', 'XXIII'], 'P': ['XXIV', 'XXV'], 'S': ['XXVI', 'XXVII'], 'T': ['XXVI', 'XXVII'],
       'A': ['II'], 'C': ['II'], 'Z': ['II'], 'B': ['XXXI']}
STREAM = ['II', 'XX', 'XXI', 'XXII', 'XXIII', 'XXIV', 'XXV', 'XXVI', 'XXVII', 'XXXI']


def clean(s):
    s = re.sub(r'\{\{[^}]*\}\}', ' ', s); s = re.sub(r'<[^>]+>', ' ', s); s = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', s)
    s = re.sub(r'^\s*\d+\s+', ' ', s, flags=re.M)
    s = re.sub(r'(?<![A-Za-z])([A-Z]) ([a-z])', r'\1\2', s)   # decorated initial written apart ('M undum')
    return re.sub(r'\s+', ' ', s).strip()


def chapters(book):
    t = open(os.path.join(RAW, f'liber_{book}.txt'), encoding='utf-8').read()
    parts = re.split(r'^==[^=\n]+==\s*$', t, flags=re.M)
    if len(parts) > 2:
        out = [clean(p) for p in parts[1:]]
    else:   # no chapter marks: groups of three numbered paragraphs
        paras = [clean(p) for p in re.split(r'\n\s*\n', t) if re.match(r'\s*\d+\s', p)]
        out = [' '.join(paras[i:i + 3]) for i in range(0, len(paras), 3)]
    return [c for c in out if len(c.split()) >= 5]


def leaves_of(zl):
    sec = {}
    for r in csv.DictReader(open(os.path.join(HERE, '..', 'data', 'ZL3b-n.words.tsv'), encoding='utf-8'), delimiter='\t'):
        sec.setdefault(r['folio'], r['illus'])
    groups = collections.OrderedDict()
    for i, p in enumerate(zl):
        m = re.match(r'f(\d+)', p['folio']); groups.setdefault(m.group(1) if m else p['folio'], []).append(i)
    return groups, [sec.get(p['folio'], 'T') for p in zl]


def queue(books):
    q = [c for b in books for c in chapters(b)]
    while True:
        for c in q: yield c


def latin_words(c): return lm.norm(c, 'latin', True).split()


def sectioned_words(zl, skel, groups, sections):
    """per page: list of Latin words, leaf-aligned"""
    queues = {s: queue(b) for s, b in SRC.items()}
    out = [None] * len(zl)
    for leaf, idx in groups.items():
        need = sum(n for i in idx for n, _, _ in skel[i]); ws = []
        q = queues.get(sections[idx[0]], queues['T'])
        while len(ws) < need: ws += latin_words(next(q))
        k = 0
        for i in idx:
            n = sum(x for x, _, _ in skel[i]); out[i] = ws[k:k + n]; k += n
    return out


def pour_pages(page_words, skel):
    pages = []
    for words, pl in zip(page_words, skel):
        it = iter(words); lines = []
        for (n, _, ps) in pl: lines.append({'words': [next(it) for _ in range(n)], 'para_start': ps})
        pages.append({'folio': '', 'lines': lines})
    return pages


def cipher_pages(csv_path, texts_by_page_group, skel, seed=19):
    """round-8 cipher, units drawn from a separate text per page group (leaf); cipher_models.generate's loop"""
    v = cm.Variant(csv_path, seed, merge=0.0, **hm.BASE)
    pages = [None] * len(skel); last = None
    for idx, text in texts_by_page_group:
        units = []
        for raw in text:
            c = v.clean_line(raw)
            if c: units += v.respace(c)
        pos = 0
        for i in idx:
            v.new_page(); lines = []
            for (n, _, ps) in skel[i]:
                words = []
                while len(words) < n:
                    if v.nulls and v.rng.random() < v.nulls:
                        nw = v.rng.choice(v.null_words); words.append(nw); last = nw; continue
                    ws, last = v.encrypt_units(units[pos % len(units):pos % len(units) + 1], last); pos += 1
                    words += ws
                lines.append({'words': words[:n], 'para_start': ps})
            pages[i] = {'folio': '', 'lines': lines}
    return pages


def main():
    csv_path = sys.argv[1]
    zl = b3.load_zl_lang(); skel = a4.skeleton(zl); langs = [p['lang'] for p in zl]
    groups, sections = leaves_of(zl)
    print('sections:', collections.Counter(sections), '| leaves:', len(groups), '| chapters:',
          {b: len(chapters(b)) for b in STREAM}, flush=True)
    sec_words = sectioned_words(zl, skel, groups, sections)
    stream_all = [w for b in STREAM for c in chapters(b) for w in latin_words(c)]
    N = sum(map(len, sec_words)); st = (stream_all * 3)[:N]; k = 0; stream_words = []
    for pw in sec_words: stream_words.append(st[k:k + len(pw)]); k += len(pw)
    vfreq = collections.Counter(b3.words_of(zl)); vtypes = sorted(vfreq, key=lambda w: -vfreq[w])
    def code_of(page_words):
        flat = [w for pw in page_words for w in pw]
        extra = [c for c in cbk.template_codes(random.Random(5), len(set(flat))) if c not in vfreq]
        codes, table = cbk.encode(flat, vtypes + extra); it = iter(codes)
        return pour_pages([[next(it) for _ in pw] for pw in page_words], skel)
    # cipher texts: per leaf, a fresh chapter run of its section (enough letters), or one continuous stream
    queues = {s: queue(b) for s, b in SRC.items()}
    sec_texts = []
    for leaf, idx in groups.items():
        need = sum(n for i in idx for n, _, _ in skel[i]) * 2; q = queues.get(sections[idx[0]], queues['T']); txt = []
        while sum(len(t.split()) for t in txt) < need: txt.append(next(q))
        sec_texts.append((idx, txt))
    stream_text = [(list(range(len(zl))), [c for b in STREAM for c in chapters(b)])]
    C = collections.OrderedDict()
    C['voynich_ZL'] = zl
    C['autocopist_s19'] = a4.Autocopist(19).generate(skel); C['autocopist_s7'] = a4.Autocopist(7).generate(skel)
    C['plain_sectioned'] = pour_pages(sec_words, skel)
    C['plain_stream'] = pour_pages(stream_words, skel)
    C['code_sectioned+scribe'] = drift.scribe(code_of(sec_words), langs, random.Random(19007), 0.0, 0.0)
    C['code_stream+scribe'] = drift.scribe(code_of(stream_words), langs, random.Random(19007), 0.0, 0.0)
    C['cipher_sectioned+scribe'] = drift.scribe(cipher_pages(csv_path, sec_texts, skel), langs, random.Random(19007), 0.0, 0.0)
    C['cipher_stream+scribe'] = drift.scribe(cipher_pages(csv_path, stream_text, skel), langs, random.Random(19007), 0.0, 0.0)
    # order-free leaf pairs (same as order.py)
    leafpos = collections.defaultdict(dict)
    for i, p in enumerate(zl):
        m = re.match(r'f(\d+)([rv])', p['folio'])
        if m: leafpos[m.group(1)].setdefault(m.group(2), i)
    pairs = [(d['r'], d['v']) for d in leafpos.values() if 'r' in d and 'v' in d]
    res = {}
    full = collections.OrderedDict()
    for n, p in C.items():
        it = order.items(p, pairs)
        rng = random.Random(11); ks = []
        for _ in range(10):
            new = list(range(len(p))); byS = collections.defaultdict(list)
            for i, s in enumerate(sections): byS[s].append(i)
            for s, idx in byS.items():
                perm = idx[:]; rng.shuffle(perm)
                for a, b_ in zip(idx, perm): new[a] = b_
            q = [p[i] for i in new]; ms = b3.page_strings(q, merged=True); h = len(ms) // 2
            ks.append(b3.jsd(b3.bigram_dist(ms[:h]), b3.bigram_dist(ms[h:])))
        it['k_jsd_shuffled'] = statistics.mean(ks)
        with contextlib.redirect_stdout(io.StringIO()):
            it['swap_d30'] = swap.run(n, p, random.Random(7))[30]
        full[n] = b3.battery(p, n, {})
        res[n] = it
        print(f'{n:26} ' + ' '.join(f'{k} {v:.4f}' for k, v in it.items()), flush=True)
    tol, marks = b3.score(full)
    print('\n| corpus | leaf_excess | j_jacc_excess | k_jsd_halves | k_jsd within-section shuffled | h_peak_R | page context d>30 | b3 (37) |')
    print('|---|---|---|---|---|---|---|---|')
    for n in C:
        r = res[n]
        print(f'| {n} | {r["leaf_excess"]:.3f} | {r["j_jacc_excess"]:.3f} | {r["k_jsd_halves"]:.4f} | {r["k_jsd_shuffled"]:.4f} | '
              f'{r["h_peak_R"]:.3f} | {r["swap_d30"]:.3f} | {sum(marks[n].values())} |')
    json.dump({'items': res, 'full': full, 'marks': marks, 'tol': tol}, open(os.path.join(HERE, 'pliny_results.json'), 'w'), indent=1, default=str)


if __name__ == '__main__':
    main()
