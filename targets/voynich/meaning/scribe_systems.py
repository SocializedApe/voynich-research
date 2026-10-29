"""Per-scribe systems: three tests on one set of texts.

Protocol, fixed before any run (28 Oct 2026):

Texts (all generated texts fill the ZL paragraph skeleton page by page, each page by its own Davis hand):
  voynich              ZL paragraph text
  cipher_shared        round-8 (hybrid_model.BASE) with Greshko's tables, each hand enciphering its own stretch of Latin
  cipher_group         round-8 with one table set for Currier-A pages and one for B pages, each built from that group's
                       own Voynich words (unigram codes <- whole words of up to 3 glyph units; prefix/suffix codes <- the
                       two halves of longer words; codes drawn from the 2n commonest of each pool), Latin as above
  cipher_hand          the same with one table set per hand 1, 2, 3 (built from that hand's words); other pages use
                       the group tables
  improv_<sigma_s>_<sigma_p>  template improviser: one glyph-unit trigram word model trained on all Voynich paragraph
                       words (the shared template, so the vocabulary is regenerated, not invented: noted as borrowed);
                       each hand multiplies every transition weight by exp(sigma_s z), each page by exp(sigma_p z),
                       z ~ N(0,1) drawn once per hand (or page), context and next unit; then hybrid_model.hybridize at
                       the repo's scribe setting (q 0.15, w 8, e 0.9, g 0.2). Grid sigma_s 0.3/0.6/1.0, sigma_p 0.2/0.4.
  controls for test 2: Auchinleck scribes 1, 2, 3, 5; Latin vs Italian (letters).

Test 3 (a different cipher system per scribe): scribe_ratio.analyse on hands 1-3 (between scribes and same scribe,
  other document, each over within-document). Passes if both ratios fall inside Voynich's bootstrap intervals.
Test 1 (template improviser): the grid point closest to Voynich's two ratios (sum of squared log ratios) is chosen on
  those ratios alone, then scored on the b3 battery (b3.score with both autocopists, 37 items; 30 held out of the
  hybrid_model tuning). Leads if it matches more held-out items than cipher+scribe and code+scribe (24-25 of 30).
Test 2 (same rules, different habits?): for each ordered pair of scribes X, Y: train a glyph-unit model on 2,000
  words of X (100-word chunks, random), test on 500 other words of X and 500 of Y, 20 draws.
  rules = share of Y's tokens whose unit trigrams (word edges '#') all occur in X's training, over the same share
  for X's own held-out words (1 = the rules carry over); habits = cross-entropy of Y under X's add-0.1 unit-bigram
  model minus X's own (bits/unit). Read: shared script with personal habits = rules near Auchinleck's, habits well
  above; different systems = rules well below.

Run from the repository root: python targets/voynich/meaning/scribe_systems.py <naibbe_tables.csv>
"""
import collections, contextlib, csv, io, itertools, json, math, os, random, statistics, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'research', 'voynich_siblings'))
import scribe_ratio as sr
import a4_selfcitation as a4
import b3_bakeoff as b3
import hybrid_model as hm
import cipher_models as cm
import auchinleck
from variants import UNIT

TSV = os.path.join(HERE, '..', 'data', 'ZL3b-n.fixed.words.tsv')
HANDS = ('1', '2', '3')
SCRIBE = (0.15, 8, 0.9, 0.2)
GRID = [(s, p) for s in (0.3, 0.6, 1.0) for p in (0.2, 0.4)]


def page_hands():
    c = collections.defaultdict(collections.Counter)
    for r in csv.DictReader(open(TSV, encoding='utf-8'), delimiter='\t'):
        if r['locus_type'] == 'P':
            c[r['folio']][r['hand']] += len(r['line_words'].split())
    return {f: v.most_common(1)[0][0] for f, v in c.items()}


def by_hand(pages, hand_of):
    g = collections.defaultdict(list)
    for p in pages:
        g[hand_of[p['folio']]] += [w for ln in p['lines'] for w in ln['words']]
    return {h: g[h] for h in HANDS}


# ------------------------------------------------------------------ cipher tables built from a group's own words
def build_tables(v, words, rng):
    uni, pre, suf = collections.Counter(), collections.Counter(), collections.Counter()
    for w in words:
        u = UNIT.findall(w)
        if len(u) <= 3:
            uni[w] += 1
        else:
            k = len(u) // 2; pre[''.join(u[:k])] += 1; suf[''.join(u[k:])] += 1
    for kind, pool in (('unigram_', uni), ('prefix_', pre), ('suffix_', suf)):
        codes = sorted(c for c in v.glyph if c.startswith(kind))
        cands = [s for s, _ in pool.most_common(2 * len(codes))]
        vals = rng.sample(cands, len(codes)) if len(cands) >= len(codes) else [rng.choice(cands) for _ in codes]
        v.glyph.update(zip(codes, vals))
    v.unigram_glyphs = {g for c, g in v.glyph.items() if c.startswith('unigram_')}
    return v


def cipher_text(zl, hand_of, csv_path, tables_for, plain_paths, table_words=None):
    """tables_for(page) -> name of a table set in table_words (None = Greshko's); each hand enciphers its own plaintext, in page order."""
    out = {}
    for h in sorted({hand_of[p['folio']] for p in zl}):
        pg = [p for p in zl if hand_of[p['folio']] == h]
        groups = collections.OrderedDict()
        for p in pg:
            groups.setdefault(tables_for(p), []).append(p)
        for key, ps in groups.items():
            v = cm.Variant(csv_path, 19 + len(out), merge=0.0, **hm.BASE)
            if key is not None:
                build_tables(v, table_words[key], random.Random(sum(map(ord, key))))
            for p, q in zip(ps, cm.generate(v, plain_paths[h], a4.skeleton(ps))):
                out[p['folio']] = {'folio': p['folio'], 'lang': p['lang'], 'lines': q['lines']}
    return [out[p['folio']] for p in zl]


# ------------------------------------------------------------------ template improviser
class Improviser:
    def __init__(self, words, ss, sp, seed):
        self.t = collections.defaultdict(collections.Counter)
        for w in words:
            u = ['#', '#'] + UNIT.findall(w) + ['#']
            for a, b, c in zip(u, u[1:], u[2:]):
                self.t[(a, b)][c] += 1
        self.opts = {k: (list(v), [float(x) for x in v.values()]) for k, v in self.t.items()}
        self.ss, self.sp, self.rng = ss, sp, random.Random(seed); self.hand_f = {}

    def factors(self, store, key, n, sigma):
        if key not in store:
            store[key] = [math.exp(sigma * self.rng.gauss(0, 1)) for _ in range(n)]
        return store[key]

    def word(self, hf, pf):
        ctx = ('#', '#'); out = []
        while len(out) < 14:
            opts, w = self.opts[ctx]
            f1 = self.factors(hf, ctx, len(opts), self.ss); f2 = self.factors(pf, ctx, len(opts), self.sp)
            nxt = self.rng.choices(opts, weights=[a * b * c for a, b, c in zip(w, f1, f2)])[0]
            if nxt == '#':
                if out:
                    break
                continue
            out.append(nxt); ctx = (ctx[1], nxt)
        return ''.join(out)

    def text(self, zl, hand_of):
        pages = []
        for p in zl:
            hf = self.hand_f.setdefault(hand_of[p['folio']], {}); pf = {}
            lines = [{'words': [self.word(hf, pf) for _ in ln['words']], 'para_start': ln['para_start']} for ln in p['lines']]
            pages.append({'folio': p['folio'], 'lang': p['lang'], 'lines': lines})
        q, w, e, g = SCRIBE
        out = hm.hybridize(pages, random.Random(7), q, w, e, g)
        for a, b in zip(out, pages):
            a['lang'] = b['lang']
        return out


# ------------------------------------------------------------------ test 2
def rules_habits(groups, split, rng, train=2000, test=500, draws=20):
    def chunks(ws):
        return [ws[i:i + 100] for i in range(0, len(ws) - 99, 100)]
    C = {k: chunks(v) for k, v in groups.items()}
    def units(w):
        return ['#', '#'] + split(w) + ['#', '#']
    rule, habit = [], []
    for X, Y in itertools.permutations(groups, 2):
        for _ in range(draws):
            cx = C[X][:]; rng.shuffle(cx)
            tr = [w for c in cx[:train // 100] for w in c]; tx = [w for c in cx[train // 100:(train + test) // 100] for w in c]
            ty = [w for c in rng.sample(C[Y], test // 100) for w in c]
            tri, bi, uv = set(), collections.Counter(), set()
            ctx = collections.Counter()
            for w in tr:
                u = units(w); tri.update(zip(u, u[1:], u[2:])); bi.update(zip(u, u[1:])); ctx.update(u[:-1]); uv.update(u)
            V = len(uv | {x for w in tx + ty for x in units(w)})
            def acc(ws):
                return sum(all(t in tri for t in zip(u, u[1:], u[2:])) for u in map(units, ws)) / len(ws)
            def xent(ws):
                s = n = 0
                for w in ws:
                    u = units(w)[1:-1]
                    for a, b in zip(u, u[1:]):
                        s -= math.log2((bi[(a, b)] + 0.1) / (ctx[a] + 0.1 * V)); n += 1
                return s / n
            ax = acc(tx)
            rule.append(acc(ty) / ax if ax else float('nan')); habit.append(xent(ty) - xent(tx))
    return statistics.mean(rule), statistics.mean(habit)


def main():
    csv_path = sys.argv[1]; rng = random.Random(17)
    zl = b3.load_zl_lang(); hand_of = page_hands()
    vh = by_hand(zl, hand_of)
    # plaintext: a separate stretch of Latin per hand
    la = a4.gutenberg_words(os.path.join(ROOT, 'lang', 'corpora', 'la-gutenberg.txt')); tmp = tempfile.mkdtemp(); plain = {}
    for i, h in enumerate(sorted(set(hand_of.values()))):
        ws = la[i * 12000:(i + 1) * 12000]; plain[h] = os.path.join(tmp, f'{h if h != "?" else "x"}.txt')
        open(plain[h], 'w', encoding='utf-8').write('\n'.join(' '.join(ws[k:k + 12]) for k in range(0, len(ws), 12)))
    grp_words = {g: [w for p in zl if p['lang'] == g for ln in p['lines'] for w in ln['words']] for g in ('A', 'B')}
    TW = {'grpA': grp_words['A'], 'grpB': grp_words['B'], **{'hand' + h: vh[h] for h in HANDS}}
    grp_key = lambda p: 'grpA' if p['lang'] == 'A' else 'grpB'
    T = collections.OrderedDict()
    T['voynich'] = zl
    T['cipher_shared'] = cipher_text(zl, hand_of, csv_path, lambda p: None, plain)
    T['cipher_group'] = cipher_text(zl, hand_of, csv_path, grp_key, plain, TW)
    T['cipher_hand'] = cipher_text(zl, hand_of, csv_path,
                                   lambda p: 'hand' + hand_of[p['folio']] if hand_of[p['folio']] in HANDS else grp_key(p), plain, TW)
    allw = b3.words_of(zl)
    for ss, sp in GRID:
        T[f'improv_{ss}_{sp}'] = Improviser(allw, ss, sp, 23).text(zl, hand_of)
    print('texts built:', list(T), flush=True)

    R = {}
    print('\nTest 1/3, scribe ratios on hands 1-3 (between scribes / within; same scribe other doc / within)')
    for n, p in T.items():
        R[n] = {'ratio': sr.analyse(n, sr.docs_of(by_hand(p, hand_of)), UNIT.findall, rng)}
    v = R['voynich']['ratio']
    def dist(n):
        r = R[n]['ratio']; return math.log(r['between_ratio'] / v['between_ratio']) ** 2 + math.log(r['same_ratio'] / v['same_ratio']) ** 2
    best = min((n for n in T if n.startswith('improv_')), key=dist)
    inside = lambda r: v['ci'][0] <= r['between_ratio'] <= v['ci'][1] and v['same_ci'][0] <= r['same_ratio'] <= v['same_ci'][1]
    for n in T:
        R[n]['inside_voynich_ci'] = inside(R[n]['ratio'])
    print('chosen improviser:', best, flush=True)

    print('\nTest 2, rules carry over / habit gap (bits per unit), mean over ordered scribe pairs')
    au = collections.defaultdict(list)
    for it in json.load(open(os.path.join(auchinleck.RAW, 'items.json'))):
        if it['scribe']:
            au[it['scribe']] += auchinleck.text_of(os.path.join(auchinleck.RAW, os.path.basename(it['page'])))
    it_words = a4.gutenberg_words(a4.IT)
    controls = {'auchinleck': ({k: v for k, v in au.items() if len(v) >= 2500}, list),
                'latin_vs_italian': ({'la': la[200000:206000], 'it': it_words[:6000]}, list)}
    rows = [(n, (by_hand(T[n], hand_of), UNIT.findall)) for n in ('voynich', 'cipher_shared', 'cipher_group', 'cipher_hand', best)]
    rows += list(controls.items())
    for n, (groups, split) in rows:
        r, h = rules_habits(groups, split, rng)
        R.setdefault(n, {})['rules'] = r; R[n]['habits'] = h
        print(f'{n:22s} rules {r:.3f}  habits {h:+.3f}', flush=True)
    vp = by_hand(zl, hand_of)
    for a, b in (('1', '2'), ('2', '3'), ('1', '3')):
        r, h = rules_habits({a: vp[a], b: vp[b]}, UNIT.findall, rng)
        R['voynich'][f'rules_{a}{b}'] = r; R['voynich'][f'habits_{a}{b}'] = h
        print(f'voynich hands {a}-{b}       rules {r:.3f}  habits {h:+.3f}', flush=True)

    print('\nTest 1/3, b3 battery', flush=True)
    skel = a4.skeleton(zl)
    B = collections.OrderedDict(); B['voynich_ZL'] = zl
    B['autocopist_s19'] = a4.Autocopist(19).generate(skel); B['autocopist_s7'] = a4.Autocopist(7).generate(skel)
    for n in ('cipher_shared', 'cipher_group', 'cipher_hand', best):
        B[n] = T[n]
    full = collections.OrderedDict()
    for n, p in B.items():
        with contextlib.redirect_stdout(io.StringIO()):
            full[n] = b3.battery(p, n, {})
    tol, marks = b3.score(full)
    held = [k for k, _ in b3.ITEMS if k not in hm.TUNED_B3]
    print('\n| text | between / within [Voynich CI] | same scribe / within | inside CI | rules | habits | b3 (37) | held-out (30) | held-out misses |')
    print('|---|---|---|---|---|---|---|---|---|')
    for n in ('voynich', 'cipher_shared', 'cipher_group', 'cipher_hand', best):
        r = R[n]['ratio']; m = marks.get(n if n != 'voynich' else 'voynich_ZL', {})
        b3s = f"{sum(m.values())} | {sum(m[k] for k in held)} | " + ', '.join(k for k in held if not m[k]) if n != 'voynich' else ' | | '
        print(f"| {n} | {r['between_ratio']:.2f} [{r['ci'][0]:.2f}-{r['ci'][1]:.2f}] | {r['same_ratio']:.2f} [{r['same_ci'][0]:.2f}-{r['same_ci'][1]:.2f}] | "
              f"{'yes' if R[n]['inside_voynich_ci'] else 'no'} | {R[n]['rules']:.3f} | {R[n]['habits']:+.3f} | {b3s} |")
    for n in ('auchinleck', 'latin_vs_italian'):
        print(f"| {n} | | | | {R[n]['rules']:.3f} | {R[n]['habits']:+.3f} | | | |")
    print('\nimproviser grid:', {n: (round(R[n]['ratio']['between_ratio'], 2), round(R[n]['ratio']['same_ratio'], 2)) for n in T if n.startswith('improv_')})
    json.dump({'R': R, 'best': best, 'b3': full, 'marks': marks, 'held': held}, open(os.path.join(HERE, 'scribe_systems_results.json'), 'w'), indent=1, default=str)


if __name__ == '__main__':
    main()
