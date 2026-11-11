"""Do the length budget, the switched convention and the A/B chaining difference survive without the word recipe?
(11 Nov 2026)

lengths.py, slots8.py and its lang8 control all rest on the split opener | middle | ending (slots4.split3), which is
this repository's own. Three re-statements that use only glyph units (common.units) or whole words:
A. Length. A Markov chain over the units of a word (orders 1, 2, 3, with word start and end as symbols), fitted on
   the tokens, is sampled (200,000 words) and the sd of its word length is compared with that of the text. A chain
   knows what the last one to three units were and not how long the word already is; if the lengths of the text are
   narrower than those of the chain, there is a length budget beyond the local rule. Same for the Naibbe ciphertext
   and Latin (letters as units) poured into the Voynich skeleton.
B. Convention. slots8.moments (share of values switched pi, switch size s, per level lang, hand, section, quire,
   page) on the first unit of the word, on its last unit, and on whole words.
C. Chaining rule of A and B. Next-unit models (context = previous one or two units, word start padded), trained on
   odd pages and tested on even pages and the reverse, bits per unit on the test pages:
     book    P(u | context) from all training pages
     tilt    P(u | context) x P_lang(u) / P(u), renormalised: the language changes unit frequencies only
     lang    P_lang(u | context), smoothed towards tilt (pseudocount 1)
   lang - tilt < 0 means the two languages differ in how units follow one another beyond their frequencies. 95%
   interval from a bootstrap over test pages (500). Pseudocounts 10 and 100 for lang were added after the first run
   (pseudocount 1 gave -0.035 at order 1 and +0.012 at order 2, where a context-by-language cell is thin).

Run from targets/voynich: python reinforce/recipe_free.py -> reinforce/recipe_free_results.json, recipe_free.md
"""
import collections, json, math, os, random, statistics, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..')
sys.path.insert(0, HERE); sys.path.insert(0, VOY); sys.path.insert(0, os.path.join(VOY, 'lines')); sys.path.insert(0, os.path.join(VOY, 'meaning'))
sys.path.insert(0, os.path.join(VOY, '..', '..', 'research', 'voynich_siblings'))
import common, slots6, slots8


def toks(pgs):
    return [w for p in pgs for ln in p['lines'] for w in ln['words']]


def chain_sd(seqs, order, rng, n=200000):
    cnt = collections.defaultdict(collections.Counter)
    for u in seqs:
        s = ['^'] * order + u + ['$']
        for i in range(order, len(s)):
            cnt[tuple(s[i - order:i])][s[i]] += 1
    tab = {c: (list(x), list(x.values())) for c, x in cnt.items()}
    L = []
    for _ in range(n):
        c = ('^',) * order; k = 0
        while True:
            vals, wts = tab[c]; v = rng.choices(vals, wts)[0]
            if v == '$':
                break
            k += 1; c = (c + (v,))[1:]
        L.append(k)
    return statistics.pstdev(L), statistics.mean(L)


def part_a(texts, rng):
    out = collections.OrderedDict()
    for name, (pgs, unit) in texts.items():
        seqs = [unit(w) for w in toks(pgs)]; L = [len(u) for u in seqs]
        r = dict(tokens=len(seqs), mean=statistics.mean(L), sd=statistics.pstdev(L))
        for k in (1, 2, 3):
            sd, mean = chain_sd(seqs, k, rng); r[f'chain{k}_sd'] = sd; r[f'chain{k}_mean'] = mean; r[f'var_ratio{k}'] = (r['sd'] / sd) ** 2
        out[name] = r
    return out


def part_b(ref):
    out = collections.OrderedDict(); lv = slots8.LV + ['page']
    for name, f in (('first unit', lambda w: common.units(w)[0]), ('last unit', lambda w: common.units(w)[-1]), ('whole word', lambda w: w)):
        data = [(slots6.loc_of(p, 0), f(w)) for p in ref for ln in p['lines'] for w in ln['words']]
        out[name] = slots8.moments(data, lv)
    return out


def rows(pgs, order):
    out = []
    for pi, p in enumerate(pgs):
        for ln in p['lines']:
            for w in ln['words']:
                s = ['^'] * order + common.units(w) + ['$']
                for i in range(order, len(s)):
                    out.append((pi, p['lang'], tuple(s[i - order:i]), s[i]))
    return out


def part_c(ref, rng):
    out = collections.OrderedDict()
    for order, K in ((1, 1), (1, 10), (1, 100), (2, 1), (2, 10), (2, 100)):
        per_page = collections.defaultdict(lambda: [0.0, 0.0, 0.0, 0])
        for d, (tr, te) in enumerate(((ref[0::2], ref[1::2]), (ref[1::2], ref[0::2]))):
            R = rows(tr, order); uni = collections.Counter(u for _, _, _, u in R); V = sorted(uni); n = len(R)
            lu = collections.defaultdict(collections.Counter); cb = collections.defaultdict(collections.Counter); cl = collections.defaultdict(collections.Counter)
            for _, l, c, u in R:
                lu[l][u] += 1; cb[c][u] += 1; cl[(l, c)][u] += 1
            cache = {}

            def models(l, c):
                if (l, c) not in cache:
                    x = cb.get(c, {}); t0 = sum(x.values()) if x else 0
                    b = {u: (x.get(u, 0) + uni[u] / n) / (t0 + 1) for u in V}; nl = sum(lu[l].values())
                    t = {u: b[u] * ((lu[l][u] + 0.5) / (nl + 0.5 * len(V))) / (uni[u] / n) for u in V}; z = sum(t.values()); t = {u: v / z for u, v in t.items()}
                    y = cl.get((l, c), {}); tt = sum(y.values()) if y else 0
                    cache[(l, c)] = (b, t, {u: (y.get(u, 0) + K * t[u]) / (tt + K) for u in V})
                return cache[(l, c)]
            for pi, l, c, u in rows(te, order):
                if u not in uni:
                    continue
                b, t, g = models(l, c); a = per_page[(d, pi)]
                a[0] -= math.log2(b[u]); a[1] -= math.log2(t[u]); a[2] -= math.log2(g[u]); a[3] += 1
        pp = list(per_page.values()); N = sum(a[3] for a in pp)
        r = dict(units=N, book=sum(a[0] for a in pp) / N, tilt=sum(a[1] for a in pp) / N, lang=sum(a[2] for a in pp) / N)
        bs = []
        for _ in range(500):
            s = [rng.choice(pp) for _ in pp]; nn = sum(a[3] for a in s); bs.append(sum(a[2] - a[1] for a in s) / nn)
        bs.sort(); r['lang_minus_tilt'] = r['lang'] - r['tilt']; r['ci'] = [bs[12], bs[487]]
        out[f'order {order}, pseudocount {K}'] = r
    return out


def main():
    t0 = time.time(); rng = random.Random(21); ref = common.pages()
    texts = collections.OrderedDict(voynich=(ref, common.units))
    for name, pgs in common.controls(ref, which=('naibbe', 'latin')).items():
        texts[name] = (pgs, common.units if name == 'naibbe' else list)
    res = dict(A=part_a(texts, rng), B=part_b(ref), C=part_c(ref, rng))
    json.dump(res, open(os.path.join(HERE, 'recipe_free_results.json'), 'w'), indent=1)
    L = ['# Without the word recipe (11 Nov 2026)', '', 'Script `recipe_free.py` (protocol in its docstring). Reproduce: `python reinforce/recipe_free.py` from `targets/voynich`.', '',
         '## A. Word length against unit chains', '', '| text | mean units | sd | chain 1 sd | chain 2 sd | chain 3 sd | variance ratio vs chain 1 | 2 | 3 |', '|---|---|---|---|---|---|---|---|---|']
    for k, r in res['A'].items():
        L.append(f"| {k} | {r['mean']:.2f} | {r['sd']:.2f} | {r['chain1_sd']:.2f} | {r['chain2_sd']:.2f} | {r['chain3_sd']:.2f} | {r['var_ratio1']:.2f} | {r['var_ratio2']:.2f} | {r['var_ratio3']:.2f} |")
    L += ['', '## B. Switched convention on recipe-free values (levels lang, hand, section, quire, page)', '', '| value | sd | pi | s |', '|---|---|---|---|']
    for k, m in res['B'].items():
        L.append(f'| {k} | ' + ' | '.join(', '.join(f'{x[key]:.2f}' for x in m) for key in ('sd', 'pi', 's')) + ' |')
    L += ['', '## C. Next-unit models, bits per unit on held-out pages', '', '| context | units | book | tilt | lang | lang - tilt [95%] |', '|---|---|---|---|---|---|']
    for k, r in res['C'].items():
        L.append(f"| {k} | {r['units']} | {r['book']:.4f} | {r['tilt']:.4f} | {r['lang']:.4f} | {r['lang_minus_tilt']:+.4f} [{r['ci'][0]:+.4f}, {r['ci'][1]:+.4f}] |")
    L.append(''); L.append(f'Runtime {time.time() - t0:.0f} s.')
    open(os.path.join(HERE, 'recipe_free.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    main()
