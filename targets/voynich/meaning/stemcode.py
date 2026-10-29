"""A stem + ending code: the front slots encode the plaintext word's stem, the ending slot its grammatical ending.

Protocol, fixed before any run (28 Oct 2026; follows #25, #34, #35):
  Plaintext: Latin (lang/corpora/la-gutenberg.txt) and Italian (a4.IT). Each word split into stem + ending by the
  longest ending of a fixed list per language (LA_END, IT_END) that leaves a stem of at least 2 letters; else ending ''.
  Code:
    ending table  one shared table: plaintext endings of both languages, ranked by their pooled frequency, mapped in
                  rank order onto Voynich's endings (slots_ab.parse over ZL, ranked by frequency); endings past the
                  end of Voynich's list share the last codes (a many-to-one, lossy table).
    stem codes    each stem type with at least 5 tokens gets K homophone cores, rarer stems one; a core is composed
                  slot by slot from Voynich's conditionals (prefix; gallows | prefix; middle | gallows), so the shape
                  grammar is borrowed, as codebook.py borrowed vocabulary; cores are not reused between stems. (Changed
                  before any result: drawing whole Voynich triples left too few distinct cores, 6,014 of the
                  assignments shared; with 400 tries per core 6 of 9,858 (K 4) and 242 of 13,922 (K 8) are shared.) One homophone drawn
                  at random per token.
    cipher word   core + ending code.
  Texts (ZL skeleton, pages keep their Currier label and hand):
    code_K4 / code_K8           A pages from Latin, B pages from Italian, no copying scribe
    code_K4+scribe / code_K8+scribe   the same through hybrid_model.hybridize (q 0.15, w 8, e 0.9, g 0.2)
    code_K8+scribe_LL           control: A and B pages both Latin (different stretches); the A/B split should vanish
  Measures, Voynich value in brackets:
    slot independence  slot_independence.measure, k = 1, tokens (Voynich 0.040; Naibbe 0.052; Latin 0.13-0.18)
    phrase repeats     distinct 3- and 4-word phrases occurring at least twice in the first 30,000 tokens (Voynich
                       computed here on the same ZL words)
    word-order signal  robustness.signal (Voynich 0.105)
    A/B by slot        slots_ab.contrast on A vs B pages (Voynich: ending the largest, about half; gallows the least)
    scribe ratios, rules/habits on hands 1-3; b3 battery with both autocopists, 30 held-out items.
  Fit, all required: slot independence <= 0.08; 3-word repeats <= 2x Voynich's; word-order signal within 0.05 of
  Voynich's; A vs B ending excess the largest slot and at least 2x the gallows excess; held-out b3 >= 23 (best earlier
  model 24, convention.py). The LL control must lose the ending lead (otherwise the split is made by the table, not
  by the two languages).

Run from the repository root: python targets/voynich/meaning/stemcode.py
"""
import collections, contextlib, io, itertools, json, math, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'research', 'voynich_siblings'))
import slots_ab, robustness
import scribe_ratio as sr
import scribe_systems as ss
import slot_independence as si
import a4_selfcitation as a4
import b3_bakeoff as b3
import hybrid_model as hm
from variants import UNIT

LA_END = ['ibus', 'orum', 'arum', 'ntur', 'mini', 'tur', 'unt', 'ant', 'ent', 'int', 'mus', 'tis', 'ius', 'ium', 'iis',
          'ae', 'am', 'as', 'is', 'os', 'us', 'um', 'em', 'es', 'ur', 'at', 'et', 'it', 're', 'ri', 'a', 'e', 'i', 'o', 'u']
IT_END = ['zione', 'zioni', 'mente', 'evano', 'avano', 'ando', 'endo', 'are', 'ere', 'ire', 'ato', 'ata', 'ati', 'ate',
          'ito', 'ita', 'uto', 'uta', 'ano', 'ono', 'ava', 'eva', 'one', 'oni', 'ore', 'ori', 'li', 'no', 'a', 'e', 'i', 'o']
SCRIBE = (0.15, 8, 0.9, 0.2)


def split(w, ends):
    for e in sorted(ends, key=len, reverse=True):
        if w.endswith(e) and len(w) - len(e) >= 2:
            return w[:-len(e)], e
    return w, ''


class StemCode:
    def __init__(self, zl, plains, K, seed):
        rng = random.Random(seed)
        vt = [slots_ab.parse(w) for w in b3.words_of(zl)]
        vend = [e for e, _ in collections.Counter(t['ending'] for t in vt).most_common()]
        # cores composed slot by slot from Voynich's conditionals: prefix, gallows | prefix, middle | gallows
        def table(pairs):
            d = collections.defaultdict(collections.Counter)
            for a, b in pairs:
                d[a][b] += 1
            return {a: (list(c), list(itertools.accumulate(c.values()))) for a, c in d.items()}
        P = table((None, t['prefix']) for t in vt); G = table((t['prefix'], t['gallows']) for t in vt); M = table((t['gallows'], t['middle']) for t in vt)
        def core():
            p = rng.choices(*P[None][:1], cum_weights=P[None][1])[0]
            g = rng.choices(G[p][0], cum_weights=G[p][1])[0]
            return p, g, rng.choices(M[g][0], cum_weights=M[g][1])[0]
        pe = collections.Counter(e for lang, ws in plains.items() for w in ws for e in [split(w, LA_END if lang == 'la' else IT_END)[1]])
        self.etab = {e: vend[min(i, len(vend) - 1)] for i, (e, _) in enumerate(pe.most_common())}
        used = set(); self.cores = {}
        sc = collections.Counter((lang, split(w, LA_END if lang == 'la' else IT_END)[0]) for lang, ws in plains.items() for w in ws)
        for st, n in sc.most_common():
            k = K if n >= 5 else 1; cs = []
            for _ in range(400 * k):
                c = core()
                if c not in used:
                    used.add(c); cs.append(c)
                    if len(cs) == k:
                        break
            if not cs:   # inventory exhausted: allow reuse
                cs = [core()]
            self.cores[st] = cs
        self.shared = sum(1 for c in self.cores.values() for x in c) - len(used)
        self.rng = rng

    def word(self, w, lang):
        st, e = split(w, LA_END if lang == 'la' else IT_END)
        p, g, m = self.rng.choice(self.cores[(lang, st)])
        return p + (g if g != '-' else '') + m + self.etab[e] or 'o'


def build(zl, code, streams):
    """streams: {'A': (lang, words), 'B': (lang, words)}; other pages take A's stream."""
    pos = {g: 0 for g in streams}; pages = []
    for p in zl:
        g = 'B' if p['lang'] == 'B' else 'A'; lang, ws = streams[g]; lines = []
        for ln in p['lines']:
            out = []
            for _ in ln['words']:
                out.append(code.word(ws[pos[g]], lang)); pos[g] += 1
            lines.append({'words': out, 'para_start': ln['para_start']})
        pages.append({'folio': p['folio'], 'lang': p['lang'], 'lines': lines})
    return pages


def scribe(pages):
    q, w, e, g = SCRIBE; out = hm.hybridize(pages, random.Random(7), q, w, e, g)
    for a, b in zip(out, pages):
        a['folio'], a['lang'] = b['folio'], b['lang']
    return out


def main():
    rng = random.Random(41)
    zl = b3.load_zl_lang(); hand_of = ss.page_hands(); N = len(b3.words_of(zl))
    la = a4.gutenberg_words(os.path.join(ROOT, 'lang', 'corpora', 'la-gutenberg.txt')); it = a4.gutenberg_words(a4.IT)
    nA = sum(len(ln['words']) for p in zl if p['lang'] != 'B' for ln in p['lines']); nB = N - nA
    LI = {'A': ('la', la[:nA]), 'B': ('it', it[:nB])}
    LL = {'A': ('la', la[:nA]), 'B': ('la', la[300000:300000 + nB])}
    T = collections.OrderedDict(); T['voynich'] = zl
    for K in (4, 8):
        code = StemCode(zl, {'la': LI['A'][1], 'it': LI['B'][1]}, K, 11)
        T[f'code_K{K}'] = build(zl, code, LI); T[f'code_K{K}+scribe'] = scribe(T[f'code_K{K}'])
    code = StemCode(zl, {'la': LL['A'][1] + LL['B'][1]}, 8, 11)
    T['code_K8+scribe_LL'] = scribe(build(zl, code, LL))
    print('texts:', list(T), flush=True)
    R = collections.OrderedDict()
    for n, p in T.items():
        ws = b3.words_of(p); r = {}
        r['slot_indep'] = si.measure([UNIT.findall(w) for w in ws[:30000]], 1, random.Random(5))[0]
        r['rep3'] = sum(v >= 2 for v in collections.Counter(tuple(ws[i:i + 3]) for i in range(min(30000, len(ws)) - 2)).values())
        r['rep4'] = sum(v >= 2 for v in collections.Counter(tuple(ws[i:i + 4]) for i in range(min(30000, len(ws)) - 3)).values())
        r['signal'] = robustness.signal(p)
        with contextlib.redirect_stdout(io.StringIO()):
            ab = slots_ab.contrast(n, [(q['lang'], [slots_ab.parse(w) for ln in q['lines'] for w in ln['words']]) for q in p if q['lang'] in ('A', 'B')], rng, draws=10, perms=50)
        r['ab'] = {k: v['excess'] for k, v in ab.items()}
        r['ratio'] = sr.analyse(n, sr.docs_of(ss.by_hand(p, hand_of)), UNIT.findall, rng)
        r['rules'], r['habits'] = ss.rules_habits(ss.by_hand(p, hand_of), UNIT.findall, random.Random(5))
        R[n] = r
        print(f"{n:20s} slot-indep {r['slot_indep']:.3f}  rep3 {r['rep3']}  rep4 {r['rep4']}  signal {r['signal']:+.3f}  "
              f"A/B excess " + ' '.join(f"{k} {v:.3f}" for k, v in r['ab'].items()), flush=True)
    skel = a4.skeleton(zl)
    B = collections.OrderedDict(); B['voynich_ZL'] = zl
    B['autocopist_s19'] = a4.Autocopist(19).generate(skel); B['autocopist_s7'] = a4.Autocopist(7).generate(skel)
    for n in T:
        if n != 'voynich':
            B[n] = T[n]
    full = collections.OrderedDict()
    for n, p in B.items():
        with contextlib.redirect_stdout(io.StringIO()):
            full[n] = b3.battery(p, n, {})
    tol, marks = b3.score(full)
    held = [k for k, _ in b3.ITEMS if k not in hm.TUNED_B3]
    v = R['voynich']
    print('\n| text | slot indep. | 3-word / 4-word repeats | word signal | A/B excess: prefix / gallows / middle / ending / word | between / same scribe | rules / habits | b3 | held-out | fit |')
    print('|---|---|---|---|---|---|---|---|---|---|')
    for n, r in R.items():
        a = r['ab']; rt = r['ratio']
        line = (f"| {n} | {r['slot_indep']:.3f} | {r['rep3']} / {r['rep4']} | {r['signal']:+.3f} | {a['prefix']:.3f} / {a['gallows']:.3f} / "
                f"{a['middle']:.3f} / {a['ending']:.3f} / {a['word']:.3f} | {rt['between_ratio']:.2f} / {rt['same_ratio']:.2f} | {r['rules']:.3f} / {r['habits']:+.3f}")
        if n == 'voynich':
            print(line + ' | | | |'); continue
        m = marks[n]; hs = sum(m[k] for k in held); r['b3'] = sum(m.values()); r['held'] = hs
        slots = {k: a[k] for k in ('prefix', 'gallows', 'middle', 'ending')}
        r['checks'] = {'slot_indep': r['slot_indep'] <= 0.08, 'rep3': r['rep3'] <= 2 * v['rep3'],
                       'signal': abs(r['signal'] - v['signal']) <= 0.05,
                       'ending_lead': max(slots, key=slots.get) == 'ending' and a['ending'] >= 2 * max(a['gallows'], 1e-9),
                       'b3': hs >= 23}
        fit = all(r['checks'].values())
        print(line + f" | {r['b3']} | {hs} | {'FIT' if fit else 'no: ' + ', '.join(k for k, ok in r['checks'].items() if not ok)} |")
    print('\nheld-out misses:', {n: [k for k in held if not marks[n][k]] for n in T if n != 'voynich'})
    json.dump({'R': R, 'b3': full, 'marks': marks, 'held': held}, open(os.path.join(HERE, 'stemcode_results.json'), 'w'), indent=1, default=str)


if __name__ == '__main__':
    main()
