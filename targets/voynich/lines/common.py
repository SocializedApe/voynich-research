"""Shared loader for the November 2026 line-structure tests.

pages(): ZL3b paragraph text (fixed parse, data/ZL3b-n.fixed.words.tsv) as a4-style pages, each page carrying
folio, hand, lang (Currier), quire, illus; lines carry words (a-z only) and para_start.
controls(skel): texts poured into the same skeleton: Latin / English (Gutenberg via a4.lang_words), the Naibbe
ciphertext of Pliny (Greshko, shipped file), the autocopist (a4.Autocopist, seeds 19 and 7), gibberish volunteers
(Gaskell & Bowern, cycled), plus Voynich with words shuffled within each line (keeps line vocabulary, destroys
positions) and with lines shuffled within each page.
"""
import collections, csv, os, random, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..')
sys.path.insert(0, VOY)
import a4_selfcitation as a4
import b3_bakeoff as b3

TSV = os.path.join(VOY, 'data', 'ZL3b-n.fixed.words.tsv')
UNIT = re.compile(r'cth|ckh|cph|cfh|ch|sh|[a-z]')
AZ = re.compile(r'^[a-z]+$')


def units(w):
    return UNIT.findall(w) or list(w)


def pages():
    out = collections.OrderedDict()
    for r in csv.DictReader(open(TSV, encoding='utf-8'), delimiter='\t'):
        if r['locus_type'] != 'P':
            continue
        ws = [w for w in r['line_words'].split() if AZ.match(w)]
        if not ws:
            continue
        p = out.setdefault(r['folio'], {'folio': r['folio'], 'hand': r['hand'], 'lang': r['lang'], 'quire': r['quire'],
                                        'illus': r['illus'], 'lines': []})
        p['lines'].append({'words': ws, 'para_start': r['para_start'] == '1'})
    return list(out.values())


def with_meta(poured, ref):
    for a, b in zip(poured, ref):
        for k in ('folio', 'hand', 'lang', 'quire', 'illus'):
            a[k] = b[k]
    return poured


def shuffle_within_line(pgs, seed=5):
    rng = random.Random(seed); out = []
    for p in pgs:
        q = dict(p); q['lines'] = []
        for ln in p['lines']:
            ws = ln['words'][:]; rng.shuffle(ws); q['lines'].append({'words': ws, 'para_start': ln['para_start']})
        out.append(q)
    return out


def shuffle_lines_within_page(pgs, seed=6):
    rng = random.Random(seed); out = []
    for p in pgs:
        q = dict(p); lines = [dict(ln) for ln in p['lines']]; rng.shuffle(lines)
        for i, ln in enumerate(lines):
            ln['para_start'] = p['lines'][i]['para_start']
        q['lines'] = lines; out.append(q)
    return out


def controls(ref, which=('latin', 'english', 'naibbe', 'autocopist_s19', 'autocopist_s7', 'gibberish')):
    skel = a4.skeleton(ref); N = sum(len(ln['words']) for p in ref for ln in p['lines'])
    out = collections.OrderedDict()
    for name in which:
        try:
            if name in ('latin', 'english', 'italian'):
                lang = {'latin': 'la', 'english': 'en', 'italian': 'it'}[name]
                out[name] = with_meta(a4.pour(a4.lang_words(lang, N), skel), ref)
            elif name == 'naibbe':
                lines = b3.read_cipher_lines(os.path.join(b3.NAIBBE_DIR, 'encrypted_nathist_output_ciphertext.txt'))
                words = [w for ws, _ in lines for w in ws]
                if len(words) < N:
                    words = (words * (N // len(words) + 1))
                out[name] = with_meta(a4.pour(words[:N], skel), ref)
            elif name.startswith('autocopist'):
                seed = int(name.split('_s')[1])
                out[name] = with_meta(a4.Autocopist(seed).generate(skel), ref)
            elif name == 'gibberish':
                words, _ = b3.load_gibberish()
                words = (words * (N // len(words) + 1))[:N]
                out[name] = with_meta(a4.pour(words, skel), ref)
        except (Exception, SystemExit) as e:
            print(f'control {name} unavailable: {e}', file=sys.stderr)
    return out
