"""Verbose-cipher sweep: one job = units -> solver on one text part, for one language and setting.

Self-contained (numpy, sentencepiece, and the files written by prepare.py in data/). Jobs are generated
deterministically; shard i of n takes jobs[i::n] and runs them on all CPU cores; each finished job appends one JSON
line to results/shard<i>.jsonl, and a restart skips jobs already done.

Job grid:
  text     Voynich groups (Currier A herbal, B herbal, A all, B all, hand 1 pharmaceutical, hand 2 biological, hand 3
           stars; ZL fixed parse, paragraph text) and two synthetic calibration ciphers with known plaintext
           (syn_gate2: gate2's verbose24 Latin; syn_gate3: gate3's homophonic cipher with unaligned spaces)
  lang     la, it (it-cinquecento), de (de-1500s), ca (ca-modern); synthetic texts with la only
  variant  raw, or nogal (the first glyph of a line is dropped when it is a gallows k t p f: line-initial gallows as
           decoration); synthetic texts raw only
  K        SentencePiece vocabulary 36, 42, 50 (pieces <= 3 glyphs, learned on the whole text of that variant)
  part     full; h1 and h2 (first and second half of the words, same unit model): key stability;
           shuf (the full unit stream shuffled, seed 4): control
  seed     1, 2
Solver: solver.solve (60,000 iterations x 4 restarts). Recorded per job: objective, per-character LM score, letter KL to
the language, the key (unit -> letter), first 400 decrypted letters, similarity to the plaintext where known.

Tier 6 = how much copying noise the tier-5 solver survives: syn_gate7 with glyphs miscopied (2, 5, 10, 20%), word breaks
moved (5, 15%) or both (5% + 5%), variant nom against la-nom, K 42, 50, 60 (252 jobs; 11 Nov 2026).
Tier 5 = nomenclator layer (variant nom: the 16 commonest cipher words of 4+ glyphs are whole-word units; plaintext
models la-nom / it-nom with 12 word symbols; verbose/nomen.py) on every Voynich text and syn_gate7; run 11 Nov 2026.
Tier 4 = positional units (variant rawpos: every unit tagged start/mid/end/only) on every Voynich text in la, it,
de, lab with K 42/50, and syn_gate5 (verbose/positional.py) with K 36-60. Tier 3 = abbreviated Latin ('lab', verbose/abbrev.py) on every Voynich text and syn_gate4, K 42/50/60, parts with
shuffled halves s1/s2. Tiers: 1 = A/B herbal and all, Latin and Italian, K 42 and 50, plus the calibration ciphers (288 jobs); 2 = the rest;
0 = all.
Run: python sweep.py --tier 1 --shard 0 --nshards 4 [--procs 4] [--list] [--out DIR]
"""
import argparse, difflib, hashlib, itertools, json, multiprocessing as mp, os, random, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import solver

DATA = os.path.join(HERE, 'data')
VOY = ['voy_A_herbal', 'voy_B_herbal', 'voy_A_all', 'voy_B_all', 'voy_h1_pharma', 'voy_h2_bio', 'voy_h3_stars']
SYN = ['syn_gate2', 'syn_gate3']
SYN3 = ['syn_gate4']   # tier 3: abbreviated Latin (verbose/abbrev.py)
SYN4 = ['syn_gate5']   # tier 4: positional cipher (verbose/positional.py)
LANGS4 = ('la', 'it', 'de', 'lab')
KS4_VOY, KS4_SYN = (42, 50), (36, 42, 50, 60)
LANGS = {'la': 'la', 'it': 'it-cinquecento', 'de': 'de-1500s', 'ca': 'ca-modern', 'lab': 'la-abbr', 'lan': 'la-nom', 'itn': 'it-nom'}
SYN5 = ['syn_gate7']   # tier 5: nomenclator layer (verbose/nomen.py)
# tier 6: the calibration cipher with copying noise (see noisy()); g = glyphs miscopied, w = word breaks moved, in %
SYN6 = ['syn_gate7~g02', 'syn_gate7~g05', 'syn_gate7~g10', 'syn_gate7~g20', 'syn_gate7~w05', 'syn_gate7~w15', 'syn_gate7~g05w05']
KS6 = (42, 50, 60)
NCAND, MINLEN = 16, 4   # tier 5 cipher side, as fixed in nomen.py
LANGS_012 = ('la', 'it', 'de', 'ca')
KS3 = (42, 50, 60)
PARTS3 = ('full', 'h1', 'h2', 'shuf', 's1', 's2')   # s1, s2: halves of the shuffled stream (stability null)
KS = (36, 42, 50)
PARTS = ('full', 'h1', 'h2', 'shuf')
SEEDS = (1, 2)
GALLOWS = set('ktpf')


TIER1 = dict(text={'voy_A_herbal', 'voy_B_herbal', 'voy_A_all', 'voy_B_all', 'syn_gate2', 'syn_gate3'}, lang={'la', 'it'}, K={42, 50})


def jobs(tier=0):
    out = []
    if tier == 6:
        for text, k, part, seed in itertools.product(SYN6, KS6, PARTS3, SEEDS):
            out.append(dict(text=text, lang='lan', variant='nom', K=k, part=part, seed=seed))
        for j in out: j['id'] = '|'.join(str(j[x]) for x in ('text', 'lang', 'variant', 'K', 'part', 'seed'))
        return out
    if tier == 5:
        for text in VOY + SYN5:
            langs = ('lan', 'itn') if text in VOY else ('lan',)
            for lang, k, part, seed in itertools.product(langs, KS4_VOY if text in VOY else KS4_SYN, PARTS3, SEEDS):
                out.append(dict(text=text, lang=lang, variant='nom', K=k, part=part, seed=seed))
        for j in out: j['id'] = '|'.join(str(j[x]) for x in ('text', 'lang', 'variant', 'K', 'part', 'seed'))
        return out
    if tier == 4:
        for text in VOY + SYN4:
            langs = LANGS4 if text in VOY else ('la',)
            for lang, k, part, seed in itertools.product(langs, KS4_VOY if text in VOY else KS4_SYN, PARTS3, SEEDS):
                out.append(dict(text=text, lang=lang, variant='rawpos', K=k, part=part, seed=seed))
        for j in out: j['id'] = '|'.join(str(j[x]) for x in ('text', 'lang', 'variant', 'K', 'part', 'seed'))
        return out
    if tier == 3:
        for text in VOY + SYN3:
            variants = ('raw', 'nogal') if text in VOY else ('raw',)
            for variant, k, part, seed in itertools.product(variants, KS3, PARTS3, SEEDS):
                out.append(dict(text=text, lang='lab', variant=variant, K=k, part=part, seed=seed))
        for j in out: j['id'] = '|'.join(str(j[x]) for x in ('text', 'lang', 'variant', 'K', 'part', 'seed'))
        return out
    for text in VOY + SYN:
        langs = LANGS_012 if text in VOY else ('la',)
        variants = ('raw', 'nogal') if text in VOY else ('raw',)
        for lang, variant, k, part, seed in itertools.product(langs, variants, KS, PARTS, SEEDS):
            out.append(dict(text=text, lang=lang, variant=variant, K=k, part=part, seed=seed))
    for j in out: j['id'] = '|'.join(str(j[x]) for x in ('text', 'lang', 'variant', 'K', 'part', 'seed'))
    if tier == 1: out = [j for j in out if all(j[k] in v for k, v in TIER1.items())]
    elif tier == 2: out = [j for j in out if not all(j[k] in v for k, v in TIER1.items())]
    return out


_cache = {}


def load_lm(lang):
    if lang not in _cache:
        mid = LANGS[lang]; meta = json.load(open(os.path.join(DATA, 'lm', mid + '.json'), encoding='utf-8'))
        m = solver.LM(np.load(os.path.join(DATA, 'lm', mid + '.npy')), meta['order'], meta['alpha'])
        ref = np.array(json.load(open(os.path.join(DATA, 'lm', mid + '.ref.json'))))
        _cache[lang] = (m, ref)
    return _cache[lang]


def noisy(lines, spec):
    """copying noise on a cipher text (tier 6). spec 'g05': every glyph is replaced with probability 0.05 by a glyph
    drawn from the glyph frequencies of the text; 'w15': every word break is dropped with probability 0.15 and every
    word of 4+ glyphs is split in two at a random point with probability 0.15; 'g05w05': both. Seed fixed."""
    import re
    rng = random.Random(31); g = re.search(r'g(\d+)', spec); w = re.search(r'w(\d+)', spec)
    pool = [c for ln in lines for x in ln for c in x]
    if g:
        e = int(g.group(1)) / 100
        lines = [[''.join(rng.choice(pool) if rng.random() < e else c for c in x) for x in ln] for ln in lines]
    if w:
        e = int(w.group(1)) / 100; out = []
        for ln in lines:
            cur = []; glue = False
            for x in ln:
                parts = [x]
                if len(x) >= 4 and rng.random() < e:
                    i = rng.randint(1, len(x) - 1); parts = [x[:i], x[i:]]
                if glue and cur: cur[-1] += parts[0]; parts = parts[1:]
                cur += parts; glue = rng.random() < e
            out.append(cur)
        lines = out
    return lines


def text_words(text, variant):
    base, _, spec = text.partition('~')
    t = json.load(open(os.path.join(DATA, 'texts', base + '.json'), encoding='utf-8'))
    lines = noisy(t['lines'], spec) if spec else t['lines']
    if variant.startswith('nogal'):
        lines = [[ln[0][1:] if ln and ln[0][:1] in GALLOWS and len(ln[0]) > 1 else ln[0]] + ln[1:] for ln in lines if ln]
    return [w for ln in lines for w in ln if w], t.get('truth')


def units_for(text, variant, k):
    import sentencepiece as spm
    variant = variant[:-3] if variant.endswith('pos') else variant   # positional variants share the unit model
    if variant == 'nom':   # tier 5: the NCAND commonest words of MINLEN+ glyphs are whole-word units, the rest as raw
        if (text, 'nom', k) not in _cache:
            import collections
            pieces, truth = units_for(text, 'raw', k); words, _ = text_words(text, 'raw')
            cand = {w for w, _ in collections.Counter(w for w in words if len(w) >= MINLEN).most_common(NCAND)}
            _cache[(text, 'nom', k)] = ([['W:' + w] if w in cand else ps for w, ps in zip(words, pieces)], truth)
        return _cache[(text, 'nom', k)]
    key = (text, variant, k)
    if key not in _cache:
        words, truth = text_words(text, variant)
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, 'c.txt'); open(p, 'w').write('\n'.join(words))
            spm.SentencePieceTrainer.train(input=p, model_prefix=os.path.join(tmp, 'u'), vocab_size=k, model_type='unigram',
                                           character_coverage=1.0, add_dummy_prefix=False, split_by_whitespace=True,
                                           bos_id=-1, eos_id=-1, unk_id=0, hard_vocab_limit=False, minloglevel=2,
                                           max_sentencepiece_length=3, input_sentence_size=0, seed_sentencepiece_size=1000000)
            sp = spm.SentencePieceProcessor(model_file=os.path.join(tmp, 'u.model'))
            pieces = [[x for x in sp.encode(w, out_type=str) if x] for w in words]
        _cache[key] = (pieces, truth)
    return _cache[key]


def tag(ws):
    """positional tags of one word's units: start / mid / end, or only for a one-unit word"""
    if len(ws) == 1: return [ws[0] + '@only']
    return [u + ('@start' if i == 0 else '@end' if i == len(ws) - 1 else '@mid') for i, u in enumerate(ws)]


def select(pieces, part, positional=False):
    """the unit stream of one job part: full, halves h1/h2, shuffled full stream, or halves s1/s2 of the shuffled stream;
    positional: every unit tagged with its position in its word before any shuffling or halving"""
    if positional: pieces = [tag(ws) for ws in pieces]
    h = len(pieces) // 2
    if part in ('full', 'shuf', 's1', 's2'):
        syms = [p for ws in pieces for p in ws]
        if part != 'full': random.Random(4).shuffle(syms)
        if part in ('s1', 's2'): syms = syms[:len(syms) // 2] if part == 's1' else syms[len(syms) // 2:]
        return syms
    return [p for ws in (pieces[:h] if part == 'h1' else pieces[h:]) for p in ws]


def run_job(j):
    t0 = time.time()
    m, ref = load_lm(j['lang'])
    pieces, truth = units_for(j['text'], j['variant'], j['K'])
    h = len(pieces) // 2
    syms = select(pieces, j['part'], j['variant'].endswith('pos'))
    seed = int(hashlib.md5(j['id'].encode()).hexdigest()[:8], 16)
    rng = random.Random(seed); np.random.seed(seed % 2 ** 32)
    r = solver.solve(syms, m, ref, rng)
    cnt = np.bincount(m.encode(r['decryption']), minlength=m.A).astype(float) + 1e-9
    import collections
    out = dict(j, objective=r['objective'], per_char=r['per_char'], kl=solver.kl(cnt, ref), units=r['units'], unit_counts=dict(collections.Counter(syms)),
               symbols=len(syms), key=r['key'], decryption=r['decryption'][:400], seconds=round(time.time() - t0, 1))
    if truth and j['part'] == 'full':
        out['similarity'] = difflib.SequenceMatcher(None, r['decryption'][:3000], truth[:3000], autojunk=False).ratio()
    return out


def main():
    a = argparse.ArgumentParser(); a.add_argument('--shard', type=int, default=0); a.add_argument('--nshards', type=int, default=1)
    a.add_argument('--procs', type=int, default=os.cpu_count() or 1); a.add_argument('--list', action='store_true')
    a.add_argument('--out', default=os.path.join(HERE, 'results')); a.add_argument('--tier', type=int, default=0)
    a.add_argument('--deadline', type=float, default=0, help='stop starting new jobs after this many seconds')
    args = a.parse_args()
    js = jobs(args.tier)
    if args.list:
        print(len(js), 'jobs;', len(js[args.shard::args.nshards]), 'in this shard'); return
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, f'shard{args.shard}.jsonl')
    done = {json.loads(l)['id'] for l in open(path, encoding='utf-8')} if os.path.exists(path) else set()
    todo = [j for j in js[args.shard::args.nshards] if j['id'] not in done]
    # group by text/variant/K so each worker reuses its unit model
    todo.sort(key=lambda j: (j['text'], j['variant'], j['K'], j['lang']))
    print(f'shard {args.shard}/{args.nshards}: {len(todo)} jobs to do ({len(done)} done), {args.procs} processes', flush=True)
    t0 = time.time()
    with mp.Pool(args.procs) as pool, open(path, 'a', encoding='utf-8') as f:
        for i, r in enumerate(pool.imap_unordered(run_job, todo, chunksize=1)):
            f.write(json.dumps(r) + '\n'); f.flush()
            print(f'[{i + 1}/{len(todo)} {time.time() - t0:.0f}s] {r["id"]}: per-char {r["per_char"]:.3f} kl {r["kl"]:.3f}'
                  + (f' sim {r["similarity"]:.3f}' if 'similarity' in r else ''), flush=True)
            if args.deadline and time.time() - t0 > args.deadline:
                print(f'deadline reached after {i + 1} jobs; stopping', flush=True); pool.terminate(); break


if __name__ == '__main__':
    main()
