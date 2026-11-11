"""Do the main November results depend on the ZL transliteration? (11 Nov 2026)

Every test of November 2026 reads the Zandbergen-Landini text (ZL3b, fixed parse). Where a word ends and what a
glyph is are judgments of the transcriber. The same measures, with the same functions, on three transliterations in
EVA: ZL (data/ZL3b-n.fixed.words.tsv), Takahashi (IT2a-n.words.tsv) and the RF reference text (RF1b-er.words.tsv),
paragraph loci only. Paragraph starts are taken from the ZL fixed parse by line id for all three (the IT and RF
word files were written by the earlier parse, which lost the paragraph markers; found when RF first gave r = +0.10
with every page one paragraph). GC (v101 alphabet) is left out: the glyph units and the word recipe are defined on EVA.
  line      wrapping.profile / wrapping.overflow: first-word and last-word length offsets, early breaks,
            r(slack of a line, length of the next first word) with its paragraph-bootstrap interval
  coupling  slots.coupling: edge coupling X between adjacent words within a line and across a line break
  budget    lengths.measure: within-context correlations of slot lengths and the variance ratio;
            recipe_free.chain_sd: variance ratio of word length against an order-2 unit chain
  A/B       hpy.drift: JSD of glyph bigrams A vs B; slots8.moments: share of endings switched by language and the
            size of a switch; recipe_free.part_c: per-language unit chain against the tilt, order 1, pseudocount 10

Run from targets/voynich: python lines/translit.py -> lines/translit_results.json, translit.md
"""
import collections, csv, json, os, random, statistics, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); VOY = os.path.join(HERE, '..')
sys.path.insert(0, HERE); sys.path.insert(0, VOY); sys.path.insert(0, os.path.join(VOY, 'reinforce')); sys.path.insert(0, os.path.join(VOY, 'meaning'))
sys.path.insert(0, os.path.join(VOY, '..', '..', 'research', 'voynich_siblings'))
import common, wrapping
import hpy, lengths, slots4, slots6, slots8, recipe_free
from slots import coupling

TEXTS = collections.OrderedDict([('ZL (Zandbergen-Landini)', 'ZL3b-n.fixed.words.tsv'), ('IT (Takahashi)', 'IT2a-n.words.tsv'), ('RF (reference)', 'RF1b-er.words.tsv')])
ROWS = [('pages', 'pages', '{:.0f}'), ('tokens', 'tokens', '{:.0f}'), ('first_offset', 'first word - interior (chars)', '{:+.2f}'), ('last_offset', 'last word - interior', '{:+.2f}'),
        ('early_break', 'early breaks', '{:.2f}'), ('r_slack_next', 'r(slack, next first word)', '{:+.3f}'), ('r_ci', '95% interval', '{}'),
        ('x_within', 'edge coupling within line', '{:.4f}'), ('x_break', 'edge coupling across line break', '{:.4f}'),
        ('r_om', 'r opener, middle lengths within context', '{:+.3f}'), ('r_se', 'r stem, ending lengths within context', '{:+.3f}'), ('var_ratio', 'variance ratio of slot lengths', '{:.3f}'),
        ('var_chain2', 'variance ratio vs order-2 unit chain', '{:.2f}'), ('ab', 'JSD A vs B (glyph bigrams)', '{:.3f}'),
        ('pi_lang', 'share of endings switched by language', '{:.2f}'), ('s_lang', 'size of a switch (log)', '{:.2f}'), ('chain_ab', 'per-language unit chain - tilt (bits/unit)', '{:+.4f}'), ('chain_ci', '95% interval', '{}')]


def pages_with_zl_paragraphs():
    zl = os.path.join(VOY, 'data', TEXTS['ZL (Zandbergen-Landini)'])
    start = {r['line_id']: r['para_start'] == '1' for r in csv.DictReader(open(zl, encoding='utf-8'), delimiter='	')}
    out = collections.OrderedDict()
    for r in csv.DictReader(open(common.TSV, encoding='utf-8'), delimiter='	'):
        ws = [w for w in r['line_words'].split() if common.AZ.match(w)]
        if r['locus_type'] != 'P' or not ws:
            continue
        p = out.setdefault(r['folio'], {k: r[k] for k in ('folio', 'hand', 'lang', 'quire', 'illus')}); p.setdefault('lines', [])
        p['lines'].append({'words': ws, 'para_start': start.get(r['line_id'], False)})
    return list(out.values())


def main():
    t0 = time.time(); res = collections.OrderedDict()
    for name, f in TEXTS.items():
        common.TSV = os.path.join(VOY, 'data', f); ref = pages_with_zl_paragraphs(); rng = random.Random(4)
        paras = [para for p in ref for para in wrapping.paragraphs(p)]; pr = wrapping.profile(paras); ov = wrapping.overflow(paras, rng, B=300)
        toks = [w for p in ref for ln in p['lines'] for w in ln['words']]
        m = lengths.measure([tuple(lengths.S(x) for x in slots4.split3(w)) for w in toks]); c = coupling(ref)
        seqs = [common.units(w) for w in toks]; sd2, _ = recipe_free.chain_sd(seqs, 2, rng)
        mom = slots8.moments(slots6.data_for(ref, edge=True)['ending'], slots8.LV)[0]
        pc = recipe_free.part_c(ref, rng)['order 1, pseudocount 10']
        res[name] = dict(pages=len(ref), tokens=len(toks), first_offset=pr['first_offset'], last_offset=pr['last_offset'], early_break=pr['early_break'],
                         r_slack_next=ov['r'], r_ci='[{:+.3f}, {:+.3f}]'.format(*ov['ci']), x_within=c['within'], x_break=c['line_break'],
                         r_om=m['r_opener_middle_within_ctx'], r_se=m['r_stem_ending_within_ctx'], var_ratio=m['var_ratio'],
                         var_chain2=(statistics.pstdev([len(u) for u in seqs]) / sd2) ** 2, ab=hpy.drift(ref)['A_vs_B'], pi_lang=mom['pi'], s_lang=mom['s'],
                         chain_ab=pc['lang_minus_tilt'], chain_ci='[{:+.4f}, {:+.4f}]'.format(*pc['ci']))
        print(name, f'{time.time() - t0:.0f}s', flush=True)
    json.dump(res, open(os.path.join(HERE, 'translit_results.json'), 'w'), indent=1)
    L = ['# The main results on three transliterations (11 Nov 2026)', '', 'Script `translit.py` (protocol in its docstring). Reproduce: `python lines/translit.py` from `targets/voynich`.', '',
         '| measure | ' + ' | '.join(res) + ' |', '|---|' + '---|' * len(res)]
    for key, label, f in ROWS:
        L.append(f'| {label} | ' + ' | '.join(f.format(r[key]) for r in res.values()) + ' |')
    L.append(''); L.append(f'Runtime {time.time() - t0:.0f} s.')
    open(os.path.join(HERE, 'translit.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    main()
