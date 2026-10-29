"""a3_supplement.py -- one-edit neighbour density with the type count held fixed (6897 = Voynich merged type count),
plus token-weighted one-edit share.  Appends to results/a3.json and results/a3.md."""
import json, collections, random
import a3_wordgrammar as A
d = json.load(open(A.RES/'a3.json', encoding='utf-8'))
voy = A.load_voynich(merged=True); N = len(voy)
corp = {'voy_merged': voy, 'voy_raw': A.load_voynich(merged=False), 'voy_merged_shuf': A.shuffle_within(voy),
        'la': A.load_gutenberg('la', N)[0], 'de': A.load_gutenberg('de', N)[0], 'en': A.load_gutenberg('en', N)[0], 'it': A.load_italian(N)}
alpha = d['corpora']['voy_merged']['order_raw']; freq = d['corpora']['voy_merged']['symbol_freq']; w = [freq[A.symname(s)] for s in alpha]
rnd = random.Random(5); corp['voy_unigram'] = [''.join(rnd.choices(alpha, w, k=len(x))) for x in voy]
seeds = d['seeds_selfcite']
corp['selfcite_t'] = A.selfcite_generator(seeds, alpha, w, N, seed=13, p_edits=(0.75, 0.20, 0.05), maxlen=9)
corp['selfcite_f'] = A.selfcite_generator(seeds, alpha, w, N, seed=12)
_, _, typec = A.precedence_counts(voy); ng, parse = A.ngram_grammar(typec)
corp['rugg'] = A.rugg_generator(typec, parse, N)[0]
supp = {}
for k, t in corp.items():
    tc = collections.Counter(t)
    f6897, n6897 = A.one_edit_fraction(tc, topk=6897)
    top = [x for x, _ in tc.most_common(6897)]
    ml = sum(len(x) for x in top)/len(top)
    types = list(tc); tset = set(types)
    wild = collections.Counter(); dele = collections.Counter()
    for x in types:
        for i in range(len(x)): wild[x[:i]+'\0'+x[i+1:]] += 1; dele[x[:i]+x[i+1:]] += 1
    tok_has = 0
    for x, c in tc.items():
        ok = any(wild[x[:i]+'\0'+x[i+1:]] > 1 or (x[:i]+x[i+1:]) in tset for i in range(len(x))) or dele[x] > 0
        if ok: tok_has += c
    supp[k] = {'one_edit_frac_top6897_types': round(f6897, 3), 'n_types_used': n6897, 'mean_len_top6897_types': round(ml, 2), 'one_edit_frac_tokens': round(tok_has/N, 3)}
    print(k, supp[k], flush=True)
d['supplement_one_edit'] = supp
d['supplement_note'] = ('one_edit_frac_top6897_types: neighbour density among the 6897 most frequent types (= Voynich type count) '
                        'to reduce the type-count confound; one_edit_frac_tokens: share of tokens whose type has a distance-1 neighbour among all types.')
json.dump(d, open(A.RES/'a3.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
with open(A.RES/'a3.md', 'a', encoding='utf-8') as f:
    f.write('\n\n## Supplement: one-edit neighbour density with type count held at 6897 (Voynich type count)\n\n'
            '| corpus | 1-edit frac among top-6897 types | types used | mean len of those types | tokens whose type has a 1-edit neighbour |\n|---|---|---|---|---|\n')
    for k, v in supp.items():
        f.write(f"| {k} | {v['one_edit_frac_top6897_types']} | {v['n_types_used']} | {v['mean_len_top6897_types']} | {v['one_edit_frac_tokens']} |\n")
print('done')
