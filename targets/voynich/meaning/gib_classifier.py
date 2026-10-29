"""Does each Voynich scribe look like meaningful text or like gibberish? A word-level classifier.

Training (Gaskell & Bowern 2022 data, github.com/danielgaskell/voynich): meaningful = 71 texts of data/meaningful.zip
(many languages and conlangs), up to 10 documents each; gibberish = the 38 volunteer texts, 1-2 documents each.
Document = 200 consecutive words (lower case, letters only). Features are word-level only, so that an alphabet's
letter statistics do not decide: type-token ratio, hapax share of types, share of the commonest word, Zipf slope over
the top 20 ranks, adjacent identical words, repeated word pairs, mean and coefficient of variation of word length,
and the share of types with a one-edit neighbour among the document's types. Logistic regression (standardised),
validated with GroupKFold over sources (no text or volunteer in both training and test).
Scored: 200-word documents of each Voynich hand (paragraph text), Enochian (enochian.py), Auchinleck (scribes 1-5)
and Pliny (sanity: should score meaningful).

Run from the repository root: python targets/voynich/meaning/gib_classifier.py
"""
import collections, csv, json, math, os, random, re, statistics, sys, zipfile
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import auchinleck, enochian, pliny

DOC = 200
WORD = re.compile(r'[^\W\d_]+')


def ed1(a, b):
    if a == b or abs(len(a) - len(b)) > 1: return False
    if len(a) == len(b): return sum(x != y for x, y in zip(a, b)) == 1
    if len(a) > len(b): a, b = b, a
    return any(b[:i] + b[i + 1:] == a for i in range(len(b)))


def feats(ws):
    f = collections.Counter(ws); types = list(f)
    top = [v for _, v in f.most_common(20)]
    xs = [math.log(i + 1) for i in range(len(top))]; ys = [math.log(v) for v in top]
    mx, my = statistics.mean(xs), statistics.mean(ys); den = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else 0.0
    bg = collections.Counter(zip(ws, ws[1:]))
    L = [len(w) for w in ws]
    byl = collections.defaultdict(list)
    for t in types: byl[len(t)].append(t)
    near = sum(1 for t in types if any(ed1(t, u) for k in (len(t) - 1, len(t), len(t) + 1) for u in byl.get(k, ())))
    return [len(types) / len(ws), sum(1 for v in f.values() if v == 1) / len(types), top[0] / len(ws), slope,
            sum(a == b for a, b in zip(ws, ws[1:])) / (len(ws) - 1), sum(v for v in bg.values() if v > 1) / (len(ws) - 1),
            statistics.mean(L), statistics.pstdev(L) / statistics.mean(L), near / len(types)]


def docs(ws, k=None):
    out = [ws[i:i + DOC] for i in range(0, len(ws) - DOC + 1, DOC)]
    return out[:k] if k else out


def main():
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    from sklearn.model_selection import GroupKFold, cross_val_predict
    from sklearn.metrics import roc_auc_score
    D = os.path.join(HERE, 'data', 'gaskell_bowern')
    X, y, g = [], [], []
    zm = zipfile.ZipFile(os.path.join(D, 'meaningful.zip'))
    for n in zm.namelist():
        if not n.startswith('texts/') or n.endswith('/'): continue
        ws = WORD.findall(zm.read(n).decode('utf-8', 'replace').lower())
        for d in docs(ws, 10): X.append(feats(d)); y.append(0); g.append(n)
    zg = zipfile.ZipFile(os.path.join(D, 'gibberish_transcriptions.zip'))
    for n in zg.namelist():
        if n.endswith('/'): continue
        ws = WORD.findall(zg.read(n).decode('utf-8', 'replace').lower())
        for d in docs(ws, 2): X.append(feats(d)); y.append(1); g.append(n)
    X, y = np.array(X), np.array(y)
    clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, class_weight='balanced'))
    p = cross_val_predict(clf, X, y, groups=g, cv=GroupKFold(5), method='predict_proba')[:, 1]
    print(f'training documents: meaningful {int((y == 0).sum())} from {len({x for x, t in zip(g, y) if t == 0})} texts, '
          f'gibberish {int(y.sum())} from {len({x for x, t in zip(g, y) if t == 1})} volunteers')
    print(f'cross-validated by source: AUC {roc_auc_score(y, p):.3f}; accuracy {((p > 0.5) == y).mean():.3f}; '
          f'mean P(gibberish): meaningful {p[y == 0].mean():.2f}, gibberish {p[y == 1].mean():.2f}')
    clf.fit(X, y)
    names = ['TTR', 'hapax', 'top word', 'Zipf20', 'adj repeat', 'repeated pairs', 'mean len', 'len CV', 'ED1 density']
    coef = clf[-1].coef_[0]
    print('weights (+ = gibberish-like): ' + ', '.join(f'{n} {c:+.2f}' for n, c in sorted(zip(names, coef), key=lambda x: -abs(x[1]))))
    sets = collections.OrderedDict()
    hands = collections.defaultdict(list)
    for r in csv.DictReader(open(os.path.join(HERE, '..', 'data', 'ZL3b-n.fixed.words.tsv'), encoding='utf-8'), delimiter='\t'):
        if r['locus_type'] == 'P': hands[r['hand']] += [w for w in r['line_words'].split() if re.fullmatch(r'[a-z]+', w)]
    for h in sorted(hands):
        if h in '12345' and len(hands[h]) >= DOC: sets[f'Voynich hand {h}'] = docs(hands[h])
    sets['Enochian (Dee)'] = docs([w for ws in enochian.dee_text().values() for w in ws])
    au = collections.defaultdict(list)
    for it in json.load(open(os.path.join(auchinleck.RAW, 'items.json'))):
        if it['scribe']: au[it['scribe']] += auchinleck.text_of(os.path.join(auchinleck.RAW, os.path.basename(it['page'])))
    for s in sorted(au): sets[f'Auchinleck scribe {s}'] = docs(au[s], 60)
    sets['Pliny (Latin)'] = docs([w for b in pliny.STREAM for c in pliny.chapters(b) for w in pliny.latin_words(c)], 60)
    out = {}
    print('\nscored documents: mean P(gibberish) [share > 0.5]')
    for name, ds in sets.items():
        q = clf.predict_proba(np.array([feats(d) for d in ds]))[:, 1]
        out[name] = (float(q.mean()), float((q > 0.5).mean()), len(ds))
        print(f'  {name:24} {len(ds):4} docs | {q.mean():.2f} [{(q > 0.5).mean():.0%}]')
    json.dump(out, open(os.path.join(HERE, 'gib_classifier_results.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
