"""followup.py -- exploratory follow-up to run_controls.py (written AFTER its results were seen; not pre-registered).

Mandarin pinyin by word was the closest natural language on the battery (19/37) but missed h2 (2.74 vs 2.11) and was
six times too predictable token to token.  Question: does the slot syllabary of run_controls.py (onset / nucleus /
coda codes from three disjoint glyph sets), applied to pinyin syllables and written one token per word, close h2;
and does homophony (3 codes per slot value) close the word-order predictability?  The same two variants on Latin,
Italian and Turkish (the word-level homophonic case was missing from the planned set).

Pinyin syllable = initial (b p m f d t n l g k h j q x zh ch sh r z c s y w or none) + vowel run + coda (n, ng, r).
"""
import collections, json, os, random, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_controls as rc
a4, b3, c1 = rc.a4, rc.b3, rc.c1

INIT = re.compile(r'^(zh|ch|sh|[bpmfdtnlgkhjqxrzcsyw])?([aeiouv]+)(ng|n|r)?$')


def zh_word_syllables(n_tokens):
    import pypinyin, jieba
    jieba.setLogLevel(60)
    han = re.compile(r'[一-鿿]+'); out = []
    for v in rc_verses():
        for run in han.findall(v):
            for u in jieba.lcut(run):
                syl = []
                for s in pypinyin.lazy_pinyin(u, style=pypinyin.Style.NORMAL):
                    m = INIT.match(s)
                    if m:
                        syl.append((m.group(1) or '', m.group(2), m.group(3) or ''))
                if syl:
                    out.append(syl)
        if len(out) >= n_tokens:
            break
    return out


def rc_verses():
    import build_corpora
    return build_corpora.verses('cmn-cu89s')


def encode_words(per_word, rng, homo):
    tabs = rc.slot_tables([s for sw in per_word for s in sw], homo)
    return [''.join(''.join(rng.choice(tabs[i][s[i]]) for i in range(3)) for s in sw) for sw in per_word]


def main():
    t0 = time.time()
    zl = b3.load_zl_lang(); skel = a4.skeleton(zl); N = len(b3.words_of(zl))
    words = collections.OrderedDict()
    zh = zh_word_syllables(2 * N)
    words['sylword_zh'] = encode_words(zh, random.Random(1), False)[:N]
    words['sylwordhomo_zh'] = encode_words(zh, random.Random(2), True)[:N]
    plain = {'la': [w.replace('j', 'i').replace('v', 'u') for w in a4.lang_words('la', 3 * N)],
             'it': a4.lang_words('it', 3 * N), 'tr': rc.file_words('turkish')[:3 * N]}
    for lg, ws in plain.items():
        per = [rc.syllabify(w, lg) for w in ws]
        words[f'sylwordhomo_{lg}'] = encode_words(per, random.Random(3), True)[:N]
    for n, ws in words.items():
        rc.log(f'{n:18s} sample: {" ".join(ws[100:112])}')
    corpora = collections.OrderedDict(voynich_ZL=zl, autocopist_s19=a4.Autocopist(19).generate(skel),
                                      autocopist_s7=a4.Autocopist(7).generate(skel))
    for n, ws in words.items():
        corpora[n] = a4.pour(ws, skel)
    full = collections.OrderedDict(); xf = {}
    for n, p in corpora.items():
        full[n] = b3.battery(p, n, xf)
    tol, marks = b3.score(full)
    h2 = {n: c1.conventions([list(w) for w in ws]) for n, ws in words.items()}
    out = {'note': 'exploratory, not pre-registered', 'full': full, 'marks': marks, 'h2': h2,
           'matches': {n: sum(m.values()) for n, m in marks.items()}, 'runtime_s': round(time.time() - t0, 1)}
    json.dump(out, open(os.path.join(rc.OUT, 'followup.json'), 'w', encoding='utf-8'), indent=1, default=str)
    for n in words:
        r = full[n]
        print(f"{n:18s} matches {out['matches'][n]:2d}  h2sp {h2[n]['with_space']['h2']:.3f}  len {r['b_len_mean']:.2f}"
              f"  ttr {r['c_ttr']:.3f}  hapax {r['c_hapax_types']:.3f}  tok_acc {r['i_tok_acc']:.3f}  lock {r['f_lock']:.3f}"
              f"  | " + ', '.join(k for k, v in marks[n].items() if v))


if __name__ == '__main__':
    main()
