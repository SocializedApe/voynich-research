"""Phase 2 feature library: linguistic concepts as numbers, for any text in any alphabet. (11 Nov 2026)

Input: a list of words, each a Python string whose characters are the symbols of the script (pack() maps
multi-character glyph units to single characters first). Every feature is computed on a chunk of fixed length
(build.py: 4,000 tokens) so that finite-size bias is the same for every text; features that are biased upward on
short samples (mutual information, clustering, repetition) are reported as the excess over the same statistic on
the chunk with its word order shuffled (mean of 3 shuffles; suffix _x). Nothing here knows which symbols are
vowels, what a word means or which language it is.

Concept -> features (prefix):
  graphotactics (c_, p_)  entropies of symbols and their conditionals; Sukhotin's vowel/consonant split and how
                          strictly the two classes alternate; how restricted word-initial and word-final symbols
                          are against word-medial ones; doubled symbols
  word shape (w_)         length mean, spread, skew; lengths of types; Zipf's law of abbreviation (frequent = short)
  lexicon (l_)            type/token, hapax, Zipf slope and curvature, Heaps, word entropy, share of the top words,
                          density of one-edit neighbours among the word types
  morphology (m_)         prefix against suffix diversity (suffixing preference), sharing in the prefix and suffix
                          tries, sizes of stem families and of ending families, successor and predecessor variety
  subword tokens (t_)     byte-pair encoding learnt on the chunk (100 merges): pieces per word, how much of the text
                          the 20 commonest pieces cover, entropy of the pieces, share of merges that touch the start
                          or the end of a word, mean length of the learnt pieces
  syntax (s_)             word-bigram information, irreversibility of word order, burstiness of the commonest
                          words against mid-frequency words (function against content words), adjacent and near
                          repeats, agreement of endings between neighbours, sandhi-like coupling across the space,
                          autocorrelation and long-range (DFA) exponent of word lengths, effective rank of the
                          bigram matrix of the top words (how many distributional classes)
  discourse (d_)          drift of vocabulary between halves, clustering of words in parts of the text, rate of
                          new words late in the text
  compression (z_)        bits per symbol; bits per word of the word-id stream against its shuffle

Use: from features import pack, features; f = features(words, random.Random(1))
     python phase2/features.py <text file>   prints the features of its first 4,000 words
"""
import collections, math, random, zlib
import numpy as np
from scipy.stats import spearmanr

K_SHUF = 3
MERGES = 100


def pack(words_as_symbol_lists):
    """words given as lists of symbols (strings of any length) -> words as strings of single characters"""
    code = {}; out = []
    for w in words_as_symbol_lists:
        out.append(''.join(code.setdefault(s, chr(0xE000 + len(code))) for s in w))
    return out


def H(c):
    n = sum(c.values())
    return -sum(v / n * math.log2(v / n) for v in c.values() if v) if n else 0.0


def _marg(pairs, i):
    c = collections.Counter()
    for k, v in pairs.items():
        c[k[i]] += v
    return c


def mi(pairs):
    return H(_marg(pairs, 0)) + H(_marg(pairs, 1)) - H(pairs)


def jsd(p, q):
    n1, n2 = sum(p.values()), sum(q.values())
    if not n1 or not n2:
        return 0.0
    m = collections.Counter()
    for k, v in p.items():
        m[k] += 0.5 * v / n1
    for k, v in q.items():
        m[k] += 0.5 * v / n2
    return -sum(v * math.log2(v) for v in m.values()) - 0.5 * H(p) - 0.5 * H(q)


def ld1(a, b):
    """edit distance <= 1"""
    if a == b:
        return True
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la > lb:
        a, b, la, lb = b, a, lb, la
    i = 0
    while i < la and a[i] == b[i]:
        i += 1
    return a[i + 1:] == b[i + 1:] if la == lb else a[i:] == b[i + 1:]


def sukhotin(words):
    adj = collections.defaultdict(collections.Counter)
    for w in words:
        for a, b in zip(w, w[1:]):
            if a != b:
                adj[a][b] += 1; adj[b][a] += 1
    s = {c: sum(v.values()) for c, v in adj.items()}; vowels = set()
    while s:
        c = max(s, key=s.get)
        if s[c] <= 0:
            break
        vowels.add(c); del s[c]
        for d in s:
            s[d] -= 2 * adj[c][d]
    return vowels


def dfa(x):
    x = np.asarray(x, float); y = np.cumsum(x - x.mean()); F = []; S = []
    for s in (4, 8, 16, 32, 64, 128, 256):
        n = len(y) // s
        if n < 4:
            break
        seg = y[:n * s].reshape(n, s); t = np.arange(s); r = []
        for row in seg:
            p = np.polyfit(t, row, 1); r.append(np.mean((row - np.polyval(p, t)) ** 2))
        F.append(math.sqrt(np.mean(r))); S.append(s)
    return float(np.polyfit(np.log(S), np.log(F), 1)[0]) if len(S) >= 3 and min(F) > 0 else 0.5


def burst(pos):
    g = np.diff(pos)
    if len(g) < 3:
        return None
    m, s = g.mean(), g.std()
    return float((s - m) / (s + m)) if s + m else None


def bpe(cnt, merges=MERGES):
    """byte-pair encoding on a word-frequency table -> (pieces per word type as lists, list of merged pairs with
    whether the merge ever touched a word start / a word end)"""
    seg = {w: list(w) for w in cnt}; log = []
    for _ in range(merges):
        pc = collections.Counter(); first = collections.Counter(); last = collections.Counter()
        for w, s in seg.items():
            n = cnt[w]
            for i in range(len(s) - 1):
                p = (s[i], s[i + 1]); pc[p] += n
                if i == 0:
                    first[p] += n
                if i == len(s) - 2:
                    last[p] += n
        if not pc:
            break
        p, n = pc.most_common(1)[0]
        if n < 2:
            break
        log.append((p[0] + p[1], first[p] / n, last[p] / n))
        for w, s in seg.items():
            if len(s) > 1:
                out = []; i = 0
                while i < len(s):
                    if i < len(s) - 1 and (s[i], s[i + 1]) == p:
                        out.append(s[i] + s[i + 1]); i += 2
                    else:
                        out.append(s[i]); i += 1
                seg[w] = out
    return seg, log


def order_stats(words, cnt, top):
    """statistics that depend on word order (computed on the chunk and on its shuffles)"""
    N = len(words); o = {}
    big = collections.Counter(zip(words, words[1:]))
    o['bigram_mi'] = mi(big) / max(H(cnt), 1e-9)
    asym = sum(abs(v - big.get((b, a), 0)) for (a, b), v in big.items() if a != b); tot = sum(v for (a, b), v in big.items() if a != b)
    o['irrev'] = asym / tot if tot else 0.0
    o['rep_adj'] = sum(1 for a, b in zip(words, words[1:]) if a == b) / (N - 1)
    o['near_adj'] = sum(1 for a, b in zip(words, words[1:]) if a != b and ld1(a, b)) / (N - 1)
    seen = collections.deque(maxlen=10); hit = 0
    for w in words:
        hit += w in seen; seen.append(w)
    o['w10'] = hit / N
    hl = collections.Counter(b[-1] for b in words[1:]); hf = collections.Counter(b[0] for b in words[1:])
    o['agree_last'] = mi(collections.Counter((a[-1], b[-1]) for a, b in zip(words, words[1:]))) / max(H(hl), 1e-9)
    o['sandhi'] = mi(collections.Counter((a[-1], b[0]) for a, b in zip(words, words[1:]))) / max(H(hf), 1e-9)
    o['first_first'] = mi(collections.Counter((a[0], b[0]) for a, b in zip(words, words[1:]))) / max(H(hf), 1e-9)
    h = N // 2
    o['half_jsd'] = jsd(collections.Counter(words[:h]), collections.Counter(words[h:]))
    part = collections.defaultdict(lambda: [0] * 8)
    for i, w in enumerate(words):
        part[w][min(i * 8 // N, 7)] += 1
    num = den = 0.0
    for w, v in part.items():
        n = cnt[w]
        if n >= 8:
            num += n * (3.0 - H(collections.Counter(dict(enumerate(v))))); den += n
    o['cluster'] = num / den if den else 0.0
    q = 3 * N // 4; early = set(words[:q])
    o['new_late'] = sum(1 for w in words[q:] if w not in early) / (N - q)
    L = np.array([len(w) for w in words], float)
    o['len_ac1'] = float(np.corrcoef(L[:-1], L[1:])[0, 1]) if L.std() > 0 else 0.0
    idx = {w: i for i, w in enumerate(top)}; M = np.zeros((len(top), len(top)))
    for (a, b), v in big.items():
        if a in idx and b in idx:
            M[idx[a], idx[b]] = v
    o['class_rank'] = 0.0
    if M.sum() > 0:
        P = M / M.sum(); r = P.sum(1, keepdims=True); c = P.sum(0, keepdims=True)
        with np.errstate(divide='ignore', invalid='ignore'):
            pmi = np.where(P > 0, np.log2(P / (r @ c)), 0.0)
        sv = np.linalg.svd(np.maximum(pmi, 0), compute_uv=False); sv = sv[sv > 1e-12]
        if len(sv):
            p = sv / sv.sum(); o['class_rank'] = float(np.exp(-(p * np.log(p)).sum()) / len(top))
    ids = {w: i for i, w in enumerate(cnt)}
    o['wordid_bits'] = len(zlib.compress(np.array([ids[w] for w in words], dtype=np.uint16).tobytes(), 9)) * 8 / N
    return o


ORDER = dict(bigram_mi='s_bigram_mi', irrev='s_irrev', rep_adj='s_rep_adj', near_adj='s_near_adj', w10='s_w10', agree_last='s_agree_last', sandhi='s_sandhi',
             first_first='s_first_first', len_ac1='s_len_ac1', class_rank='s_class_rank', half_jsd='d_half_jsd', cluster='d_cluster', new_late='d_new_late',
             wordid_bits='z_wordid')


def features(words, rng):
    words = [w for w in words if w]; N = len(words); f = collections.OrderedDict()
    cnt = collections.Counter(words); types = list(cnt); T = len(types)
    # ---- graphotactics
    text = ' '.join(words); c1 = collections.Counter(text.replace(' ', ''))
    b2 = collections.Counter(zip(text, text[1:])); b3 = collections.Counter(zip(zip(text, text[1:]), text[2:]))
    f['c_h1'] = H(c1); f['c_h2'] = H(b2) - H(_marg(b2, 0)); f['c_h3'] = H(b3) - H(_marg(b3, 0))
    f['c_h2_over_h1'] = f['c_h2'] / max(f['c_h1'], 1e-9); f['c_h3_over_h2'] = f['c_h3'] / max(f['c_h2'], 1e-9); f['c_alpha_eff'] = 2 ** f['c_h1']
    V = sukhotin(words); nch = sum(c1.values()); pv = sum(v for c, v in c1.items() if c in V) / nch
    pairs = [(a in V, b in V) for w in words for a, b in zip(w, w[1:])]
    alt = sum(1 for a, b in pairs if a != b) / len(pairs) if pairs else 0.0
    f['p_vowel_share'] = pv; f['p_cv_alt_excess'] = alt - 2 * pv * (1 - pv)
    ini = collections.Counter(w[0] for w in words); fin = collections.Counter(w[-1] for w in words)
    med = collections.Counter(c for w in words if len(w) >= 3 for c in w[1:-1])
    f['p_h_init'] = H(ini) / max(f['c_h1'], 1e-9); f['p_h_final'] = H(fin) / max(f['c_h1'], 1e-9)
    f['p_jsd_init_med'] = jsd(ini, med); f['p_jsd_final_med'] = jsd(fin, med); f['p_jsd_init_final'] = jsd(ini, fin)
    inw = collections.Counter((a, b) for w in words for a, b in zip('^' + w, w + '$'))
    f['p_double'] = sum(v for (a, b), v in inw.items() if a == b) / max(sum(inw.values()), 1)
    # ---- word shape
    L = np.array([len(w) for w in words], float); TL = np.array([len(w) for w in types], float)
    f['w_len_mean'] = L.mean(); f['w_len_sd'] = L.std(); f['w_len_cv'] = L.std() / L.mean()
    f['w_len_skew'] = float(((L - L.mean()) ** 3).mean() / max(L.std() ** 3, 1e-9)); f['w_len1'] = float((L == 1).mean())
    f['w_type_len_mean'] = TL.mean(); f['w_type_len_var_over_mean'] = TL.var() / TL.mean()
    r = spearmanr([cnt[w] for w in types], TL)[0] if TL.std() > 0 else 0.0; f['w_brevity'] = 0.0 if r != r else float(r)
    # ---- lexicon
    fr = np.array(sorted(cnt.values(), reverse=True), float); lr = np.log(np.arange(1, T + 1)); lf = np.log(fr)
    f['l_ttr'] = T / N; f['l_hapax_types'] = float((fr == 1).mean())
    f['l_zipf_slope'] = float(np.polyfit(lr, lf, 1)[0]); f['l_zipf_curv'] = float(np.polyfit(lr, lf, 2)[0])
    f['l_h_word'] = H(cnt) / math.log2(N); f['l_top1'] = fr[0] / N; f['l_top10'] = fr[:10].sum() / N
    seen = set(); pts = []
    for i, w in enumerate(words, 1):
        seen.add(w)
        if i % (N // 10) == 0:
            pts.append((math.log(i), math.log(len(seen))))
    f['l_heaps'] = float(np.polyfit([a for a, _ in pts], [b for _, b in pts], 1)[0])
    ts = set(types); sub = collections.defaultdict(set); nb = collections.Counter()
    for w in types:
        for i in range(len(w)):
            d = w[:i] + w[i + 1:]
            sub[(i, d)].add(w)
            if d in ts:
                nb[w] += 1; nb[d] += 1
    for g in sub.values():
        if len(g) > 1:
            for w in g:
                nb[w] += len(g) - 1
    f['l_ld1_share'] = sum(1 for w in types if nb[w]) / T; f['l_ld1_mean'] = sum(nb.values()) / T
    # ---- morphology (on types)
    f['m_suffix_pref'] = H(collections.Counter(w[:2] for w in types)) - H(collections.Counter(w[-2:] for w in types))
    tot = sum(len(w) for w in types)
    f['m_prefix_trie'] = len({w[:i] for w in types for i in range(1, len(w) + 1)}) / tot
    f['m_suffix_trie'] = len({w[i:] for w in types for i in range(len(w))}) / tot
    f['m_trie_asym'] = f['m_prefix_trie'] - f['m_suffix_trie']
    long = [w for w in types if len(w) >= 5]
    f['m_stem_family'] = len(long) / max(len({w[:-2] for w in long}), 1); f['m_tail_family'] = len(long) / max(len({w[2:] for w in long}), 1)

    def variety(key, nxt):
        g = collections.defaultdict(collections.Counter)
        for w in types:
            if len(w) >= 4:
                g[key(w)][nxt(w)] += 1
        v = [(sum(c.values()), H(c)) for c in g.values() if sum(c.values()) >= 5]
        return sum(n * h for n, h in v) / sum(n for n, _ in v) if v else 0.0
    f['m_succ_var'] = variety(lambda w: w[:3], lambda w: w[3]); f['m_pred_var'] = variety(lambda w: w[-3:], lambda w: w[-4])
    # ---- subword tokens
    seg, log = bpe(cnt); pc = collections.Counter()
    for w, s in seg.items():
        for p in s:
            pc[p] += cnt[w]
    npieces = sum(pc.values())
    f['t_pieces_per_word'] = npieces / N; f['t_pieces_per_symbol'] = npieces / nch
    f['t_top20_cover'] = sum(v for _, v in pc.most_common(20)) / npieces; f['t_piece_entropy'] = H(pc) / math.log2(max(len(pc), 2))
    f['t_merge_at_start'] = float(np.mean([a for _, a, _ in log])) if log else 0.0; f['t_merge_at_end'] = float(np.mean([b for _, _, b in log])) if log else 0.0
    f['t_merge_len'] = float(np.mean([len(m) for m, _, _ in log])) if log else 0.0
    f['t_whole_words'] = sum(cnt[w] for w, s in seg.items() if len(s) == 1 and len(w) > 1) / N
    # ---- syntax, discourse: excess over shuffled word order
    top = [w for w, _ in cnt.most_common(100)]
    obs = order_stats(words, cnt, top); base = collections.defaultdict(list)
    for _ in range(K_SHUF):
        sh = words[:]; rng.shuffle(sh)
        for k, v in order_stats(sh, cnt, top).items():
            base[k].append(v)
    for k, name in ORDER.items():
        f[name + '_x'] = obs[k] - float(np.mean(base[k]))
    f['s_rep_adj'] = obs['rep_adj']; f['s_len_hurst'] = dfa(L)
    pos = collections.defaultdict(list)
    for i, w in enumerate(words):
        pos[w].append(i)
    bt = [b for b in (burst(np.array(pos[w])) for w in top[:20]) if b is not None]
    bm = [b for b in (burst(np.array(pos[w])) for w in top[20:] if cnt[w] >= 8) if b is not None]
    f['s_burst_top'] = float(np.mean(bt)) if bt else 0.0; f['s_burst_mid'] = float(np.mean(bm)) if bm else 0.0; f['s_burst_diff'] = f['s_burst_mid'] - f['s_burst_top']
    # ---- compression
    code = {c: i for i, c in enumerate(sorted(set(text)))}
    raw = np.array([code[c] for c in text], dtype=np.uint16 if len(code) > 255 else np.uint8).tobytes()
    f['z_bpc'] = len(zlib.compress(raw, 9)) * 8 / len(text)
    return f


if __name__ == '__main__':
    import sys, time
    ws = open(sys.argv[1], encoding='utf-8').read().split()[:4000]; t = time.time()
    for k, v in features(ws, random.Random(1)).items():
        print(f'{k:28s} {v:.4f}')
    print('seconds', round(time.time() - t, 1))
