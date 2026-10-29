"""run_controls.py -- checks 1-3 of 29 Oct 2026, through the unchanged b3 battery (37 items) and h2 conventions.

Check 1. Languages not yet run through the battery (build_corpora.py): Turkish, Hungarian, Vietnamese (as written
         and with diacritics folded), Mandarin in toneless pinyin (one token per syllable / per jieba word), Arabic
         transliterated (vocalised / consonantal).  All Bible text, so the genre matches c1's Bible controls.
Check 2. Ciphers a 1420s writer could have known from the Arabic manuals (Ibn al-Durayhim, d. 1361, as reported in
         al-Qalqashandi's Subh al-a'sha, Cairo 1412) or from Italian chanceries.  Plaintext: Latin (a4.lang_words
         'la') and the Italian control (a4.lang_words 'it'); word spaces kept unless stated.
           homo     homophonic substitution: 40 cipher signs shared out by letter frequency (max(1, round(40 p))
                    signs per letter, the manuals' rule of more signs for frequent letters), one drawn at random per
                    occurrence
           homonull homo plus 4 null signs, one inserted after any sign with probability 0.15
           letword  each plaintext letter replaced by a whole word ('letters as names'): 3 code words per letter,
                    random strings of 3-6 signs over a 20-sign alphabet, chosen at random per occurrence; one
                    cipher token per plaintext letter, plaintext word spaces dropped
           polyb    two-sign groups: each letter becomes row sign + column sign of a 5x5 (Latin, Italian) square
                    with disjoint row and column alphabets; plaintext words kept as tokens
Check 3. Syllable ciphers: plaintext cut into syllables (rule syllabifier below), each syllable written as
         onset code + nucleus code + coda code from three disjoint glyph sets (onset b c d f g h, nucleus a e i o,
         coda l m n r y), codes assigned by frequency rank (all 1-glyph codes, then 2-glyph codes); an empty onset
         and an empty coda are written as nothing.  Plaintexts: Latin, Italian, Turkish.
           syl      one cipher token per syllable
           sylword  one cipher token per plaintext word (its syllable codes written together)
           sylhomo  as syl, but every slot value has 3 codes (consumed 3 at a time down the same code list),
                    one chosen at random per occurrence
         Syllabifier: nucleus = a maximal vowel run (Latin, Italian; 'qu' counts as one consonant) or a single vowel
         (Turkish: no diphthongs); between two nuclei one consonant goes to the next onset, two or more give the
         last one (or a stop + l/r pair, Latin and Italian) to the next onset and the rest to the coda.

All design choices above were written down before any battery number was computed.  Match rule: b3.score
(tolerance max(10% of the Voynich value, autocopist s19-s7 spread)), on the fixed parse (parse_ivtff.py --fixed,
data/ZL3b-n.fixed.words.tsv, 34,834 tokens), so counts compare with results/fixed_parse/b3.json and c1.json.
Reference counts there: Latin 11, Italian 14, Vulgate 16, Swahili 17, Esperanto 18, Naibbe 21-23, Markov-3 on
Voynich 27 (a fit, not a hypothesis).

Writes results/controls2.json and results/controls2.md.  Seeded and deterministic.
"""
import collections, itertools, json, math, os, random, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
VOY = os.path.dirname(HERE)
sys.path.insert(0, VOY)
import a4_selfcitation as a4
a4.ZL = os.path.join(VOY, 'data', 'ZL3b-n.fixed.words.tsv')
import b3_bakeoff as b3
import c1_comparators as c1

D = os.path.join(HERE, 'data')
OUT = os.path.join(HERE, 'results')
SEED = 20261029


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def file_words(name):
    return c1.text_words(name, os.path.join(D, name + '.txt'))


# ----------------------------------------------------------------------------------------------- check 2
def letters_of(words, alphabet):
    return [[c for c in w if c in alphabet] for w in words]


def homophonic(words, rng, n_signs=40, nulls=False):
    cnt = collections.Counter(c for w in words for c in w); tot = sum(cnt.values())
    signs = [chr(c) for c in range(ord('a'), ord('z') + 1)] + [chr(c) for c in range(ord('A'), ord('Z') + 1)]
    share = {c: max(1, round(n_signs * v / tot)) for c, v in cnt.items()}
    it = iter(signs + [f'{i}' for i in range(10)] * 9)
    table = {c: [next(it) for _ in range(k)] for c, k in sorted(share.items(), key=lambda x: -x[1])}
    null_signs = [next(it) for _ in range(4)] if nulls else []
    out = []
    for w in words:
        s = []
        for c in w:
            s.append(rng.choice(table[c]))
            if nulls and rng.random() < 0.15:
                s.append(rng.choice(null_signs))
        out.append(''.join(s))
    return out


def letter_words(words, rng):
    alpha = 'abcdefghiklmnopqrstu'
    letters = sorted(set(c for w in words for c in w))
    used = set(); table = {}
    for c in letters:
        table[c] = []
        while len(table[c]) < 3:
            cw = ''.join(rng.choice(alpha) for _ in range(rng.randint(3, 6)))
            if cw not in used:
                used.add(cw); table[c].append(cw)
    return [rng.choice(table[c]) for w in words for c in w]


def polybius(words, rng):
    letters = [c for c, _ in collections.Counter(c for w in words for c in w).most_common()]
    rows, cols = 'abcdef', 'klmnop'
    size = 5 if len(letters) <= 25 else 6
    cells = [r + k for r in rows[:size] for k in cols[:size]]
    order = rng.sample(cells, len(cells))
    table = {c: order[i % len(order)] for i, c in enumerate(letters)}
    return [''.join(table[c] for c in w) for w in words]


# ----------------------------------------------------------------------------------------------- check 3
VOWELS = {'la': set('aeiouy'), 'it': set('aeiouàèéìíòóùú'), 'tr': set('aeıioöuü')}
STOPS = set('pbtdcgf'); LIQ = set('lr')


def syllabify(w, lang):
    V = VOWELS[lang]
    if lang == 'la':
        w = w.replace('qu', 'Q')
    nuclei = []  # (start, end) of each nucleus
    i = 0
    while i < len(w):
        if w[i] in V:
            j = i + 1
            if lang != 'tr':
                while j < len(w) and w[j] in V:
                    j += 1
            nuclei.append((i, j)); i = j
        else:
            i += 1
    if not nuclei:
        return [(w, '', '')]
    syl = []
    onset = w[:nuclei[0][0]]
    for k, (s, e) in enumerate(nuclei):
        nuc = w[s:e]
        if k + 1 < len(nuclei):
            cl = w[e:nuclei[k + 1][0]]
            if len(cl) <= 1:
                coda, nxt = '', cl
            elif lang != 'tr' and cl[-2] in STOPS and cl[-1] in LIQ:
                coda, nxt = cl[:-2], cl[-2:]
            else:
                coda, nxt = cl[:-1], cl[-1]
        else:
            coda, nxt = w[e:], ''
        syl.append((onset, nuc, coda)); onset = nxt
    return syl


def codes(alpha):
    for c in alpha:
        yield c
    n = 2
    while True:  # rare slot values (long clusters, odd vowel runs) get ever longer codes
        for t in itertools.product(alpha, repeat=n):
            yield ''.join(t)
        n += 1


def slot_tables(sylls, homo):
    k = 3 if homo else 1
    tabs = []
    for slot, alpha in ((0, 'bcdfgh'), (1, 'aeio'), (2, 'lmnry')):
        cnt = collections.Counter(s[slot] for s in sylls)
        gen = codes(alpha); t = {}
        for val, _ in cnt.most_common():
            if val == '' and slot != 1:
                t[val] = ['']
            else:
                t[val] = [next(gen) for _ in range(k)]
        tabs.append(t)
    return tabs


def syllable_cipher(words, lang, rng, mode):
    per_word = [syllabify(w, lang) for w in words]
    tabs = slot_tables([s for sw in per_word for s in sw], mode == 'sylhomo')
    enc = lambda s: ''.join(rng.choice(tabs[i][s[i]]) for i in range(3))
    if mode == 'sylword':
        return [''.join(enc(s) for s in sw) for sw in per_word]
    return [enc(s) for sw in per_word for s in sw]


# ----------------------------------------------------------------------------------------------- main
CHECK1 = ['turkish', 'hungarian', 'vietnamese', 'vietnamese_fold', 'chinese_pinyin_syl', 'chinese_pinyin_word',
          'arabic_voc', 'arabic_cons']


def main():
    t0 = time.time(); os.makedirs(OUT, exist_ok=True)
    zl = b3.load_zl_lang(); skel = a4.skeleton(zl); vw = b3.words_of(zl); N = len(vw)
    log(f'ZL fixed parse: {N} tokens, {len(zl)} pages')
    words = collections.OrderedDict(); meta = {}
    for name in CHECK1:
        ws = file_words(name)
        meta[name] = {'check': 1, 'available_tokens': len(ws), 'alphabet': ''.join(sorted(set(''.join(ws))))}
        words[name] = ws[:N]
    big = 8 * N
    plain = {'la': a4.lang_words('la', 250000), 'it': a4.lang_words('it', big)}
    plain['tr'] = file_words('turkish')
    for lg in ('la', 'it'):
        abc = set('abcdefghiklmnopqrstuvxyz') if lg == 'la' else set('abcdefghilmnopqrstuvz')
        pw = [w for w in letters_of(plain[lg], abc) if w]
        pw = [''.join(w) for w in pw]
        for i, (mode, fn) in enumerate([('homo', lambda ws, r: homophonic(ws, r)),
                                        ('homonull', lambda ws, r: homophonic(ws, r, nulls=True)),
                                        ('letword', letter_words), ('polyb', polybius)]):
            name = f'{mode}_{lg}'
            src = pw[:N] if mode != 'letword' else pw[:N]
            out = fn(src, random.Random(SEED + i))
            meta[name] = {'check': 2, 'available_tokens': len(out)}
            words[name] = out[:N]
    for lg in ('la', 'it', 'tr'):
        pw = plain[lg] if lg != 'la' else [w.replace('j', 'i').replace('v', 'u') for w in plain['la']]
        for i, mode in enumerate(('syl', 'sylword', 'sylhomo')):
            name = f'{mode}_{lg}'
            out = syllable_cipher(pw[:3 * N], lg, random.Random(SEED + 10 + i), mode)
            meta[name] = {'check': 3, 'available_tokens': len(out)}
            words[name] = out[:N]
    for n, ws in words.items():
        log(f'{n:22s} {len(ws):6d} tokens   sample: {" ".join(ws[100:112])}')

    h2 = collections.OrderedDict()
    h2['voynich_ZL_raw'] = c1.conventions([list(w) for w in vw])
    h2['voynich_ZL_merged'] = c1.conventions([c1.tok_merge2(w) for w in vw])
    for n, ws in words.items():
        h2[n] = c1.conventions([list(w) for w in ws])

    corpora = collections.OrderedDict()
    corpora['voynich_ZL'] = zl
    corpora['autocopist_s19'] = a4.Autocopist(19).generate(skel)
    corpora['autocopist_s7'] = a4.Autocopist(7).generate(skel)
    for n, ws in words.items():
        if len(ws) >= N:
            corpora[n] = a4.pour(ws, skel)
        else:
            log(f'SKIP {n}: only {len(ws)} tokens')
    full = collections.OrderedDict(); xf = {}
    for n, p in corpora.items():
        t1 = time.time(); full[n] = b3.battery(p, n, xf); log(f'{n}: battery {time.time() - t1:.1f}s')
    tol, marks = b3.score(full)
    out = {'meta': {'N': N, 'seed': SEED, 'corpora': meta, 'items': b3.ITEMS, 'runtime_s': round(time.time() - t0, 1)},
           'h2': h2, 'full': full, 'tol': tol, 'marks': marks, 'matches': {n: sum(m.values()) for n, m in marks.items()}}
    json.dump(out, open(os.path.join(OUT, 'controls2.json'), 'w', encoding='utf-8'), indent=1, default=str)
    write_md(out)
    log('done', out['meta']['runtime_s'], 's')


SHOW = ['a_h2_raw', 'b_len_mean', 'b_len_sd', 'c_zipf', 'c_ttr', 'c_hapax_types', 'd_adj_exact', 'e_w10', 'f_irrev', 'f_lock']


def write_md(R):
    keys = [k for k, _ in R['meta']['items']]
    show = [k for k in SHOW if k in keys]
    L = ['# controls2: checks 1-3 (29 Oct 2026): more languages, Arabic-manual ciphers, syllable ciphers', '',
         'Script `controls2/run_controls.py`; design and match rule in its docstring (fixed before any score).', '',
         '| corpus | check | b3 matches /37 | h2 with space | h2 no space | ' + ' | '.join(show) + ' |',
         '|---|---|---|---|---|' + '---|' * len(show)]
    for n, res in R['full'].items():
        ck = R['meta']['corpora'].get(n, {}).get('check', '')
        h = R['h2'].get(n) or (R['h2']['voynich_ZL_raw'] if n == 'voynich_ZL' else None)
        hs = f"{h['with_space']['h2']:.3f} | {h['no_space']['h2']:.3f}" if h else ' | '
        vals = ' | '.join(b3.fmt(res.get(k)) for k in show)
        L.append(f"| {n} | {ck} | {R['matches'][n]} | {hs} | {vals} |")
    L += ['', 'Voynich merged-glyph h2: with space %.3f, no space %.3f.' % (
        R['h2']['voynich_ZL_merged']['with_space']['h2'], R['h2']['voynich_ZL_merged']['no_space']['h2']), '',
          '## Items matched, per corpus', '']
    for n, m in R['marks'].items():
        L.append(f"- **{n}** ({sum(m.values())}): " + ', '.join(k for k, v in m.items() if v))
    open(os.path.join(OUT, 'controls2.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')


if __name__ == '__main__':
    main()
