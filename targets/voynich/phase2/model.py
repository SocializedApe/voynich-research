"""Phase 2 models: learn 'a language underneath' against 'generated' from features, test whether that carries to
kinds of text never seen in training, and only then look at Voynich. (11 Nov 2026)

Protocol, written before any Voynich or mimic row of features.csv was looked at.
Training rows: kinds natural, cipher, generated (build.py). Features: all columns of features.py.
Tasks: T1 meaningful (natural or cipher) against generated; T3 natural / cipher / generated.
Models: logistic regression on standardised features (C 1), random forest (500 trees), gradient boosting
(HistGradientBoosting, defaults). Primary model: gradient boosting.
Checks on the models (all from training rows or the held-out mimics, none from Voynich):
  C1 leave-source-out: 10 folds grouped by source (a language with all its ciphers and chains, or one generator
     seed); AUC and accuracy of T1.
  C2 leave-process-out: for every cipher and every generator, a model trained without that process classifies its
     chunks; recall = share put on the right side of T1. This is the check that matters: Voynich, if it is anything,
     is a process not in the training set.
  C3 genre: trained on the Bible texts only, natural chunks of other genres (Gutenberg, manuscripts) must be called
     meaningful.
  C4 mimics (never in training): the autocopist, Rugg's table text, the volunteers' gibberish and this repository's
     lang8 generator must get a mean P(meaningful) below 0.5, the Naibbe cipher of Pliny above 0.5.
  C5 novelty: features standardised on the training rows; distance of a chunk = mean distance to its 5 nearest
     training chunks from other sources; reference = that distance for every training chunk. A chunk is 'in
     distribution' if its distance is at or below the 95th percentile of the reference.
Rule for a verdict on Voynich (ZL glyph units; the other two encodings are reported beside it):
  a verdict is issued only if C1 AUC >= 0.95, C2 mean recall >= 0.8 with no process under 0.5, C3 recall >= 0.9, all
  five C4 families on the right side, and at least 6 of the 8 Voynich chunks are in distribution (C5). Then:
  'language underneath' if the mean P(meaningful) is >= 0.8 under all three models, 'generated' if <= 0.2 under all
  three, otherwise undecided. If a condition fails the output is 'no verdict' with the failed condition named, and
  the descriptive part (nearest sources, features where Voynich leaves each kind) is reported as description only.

Run from targets/voynich: python phase2/model.py -> phase2/model_results.json, phase2/phase2.md
                          python phase2/model.py features.csv features2.csv -> model_resultsb.json, phase2b.md (second
                          round: same protocol and rule, training rows of build2.py added; 12 Nov 2026)
"""
import collections, json, os, sys, time, warnings
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__))
META = ['kind', 'process', 'source', 'chunk']
MODELS = collections.OrderedDict([
    ('logistic', lambda: make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000))),
    ('forest', lambda: RandomForestClassifier(n_estimators=500, random_state=0, n_jobs=3)),
    ('boosting', lambda: HistGradientBoostingClassifier(random_state=0))])
PRIMARY = 'boosting'


def main():
    files = sys.argv[1:] or ['features.csv']; tag = '' if len(files) == 1 else 'b'
    t0 = time.time(); df = pd.concat([pd.read_csv(os.path.join(HERE, f)) for f in files], ignore_index=True); F = [c for c in df.columns if c not in META]
    tr = df[df.kind.isin(['natural', 'cipher', 'generated'])].reset_index(drop=True)
    X = tr[F].values; y = (tr.kind != 'generated').astype(int).values; g = tr.source.values
    res = collections.OrderedDict(n_train=len(tr), n_features=len(F), counts=tr.groupby(['kind', 'process']).size().to_dict().__repr__())
    # ---- C1
    c1 = {}
    for name, mk in MODELS.items():
        p = np.zeros(len(tr))
        for a, b in GroupKFold(10).split(X, y, g):
            p[b] = mk().fit(X[a], y[a]).predict_proba(X[b])[:, 1]
        c1[name] = dict(auc=float(roc_auc_score(y, p)), acc=float(((p >= 0.5) == y).mean()))
    res['C1'] = c1
    # ---- C2
    c2 = collections.OrderedDict()
    for proc in sorted(set(tr.process[tr.kind != 'natural'])):
        m = (tr.process == proc).values; row = {}
        for name, mk in MODELS.items():
            p = mk().fit(X[~m], y[~m]).predict_proba(X[m])[:, 1]
            row[name] = float(((p >= 0.5) == y[m]).mean())
        row['truth'] = 'meaningful' if y[m][0] else 'generated'; row['n'] = int(m.sum()); c2[proc] = row
    res['C2'] = c2
    # ---- C3
    bible = ~tr.source.str.contains(':').values; other = (~bible) & (tr.kind == 'natural').values
    res['C3'] = {name: float((mk().fit(X[bible], y[bible]).predict_proba(X[other])[:, 1] >= 0.5).mean()) for name, mk in MODELS.items()}; res['C3']['n'] = int(other.sum())
    # ---- full models
    full = {name: mk().fit(X, y) for name, mk in MODELS.items()}
    y3 = tr.kind.values; full3 = HistGradientBoostingClassifier(random_state=0).fit(X, y3)
    te = df[df.kind.isin(['mimic', 'voynich'])].reset_index(drop=True); Xt = te[F].values
    for name, m in full.items():
        te['p_' + name] = m.predict_proba(Xt)[:, 1]
    p3 = full3.predict_proba(Xt)
    for i, c in enumerate(full3.classes_):
        te['p3_' + c] = p3[:, i]
    # ---- C5 novelty
    mu = X.mean(0); sd = X.std(0) + 1e-9; Z = (X - mu) / sd; Zt = (Xt - mu) / sd
    def knn(z, mask):
        d = np.sqrt(((Z[mask] - z) ** 2).sum(1)); return float(np.sort(d)[:5].mean())
    refd = np.array([knn(Z[i], g != g[i]) for i in range(len(tr))]); thr = float(np.percentile(refd, 95))
    te['dist'] = [knn(z, np.ones(len(tr), bool)) for z in Zt]; te['in_dist'] = te.dist <= thr
    te['dist_pct'] = [float((refd <= d).mean()) for d in te.dist]
    res['C5'] = dict(threshold=thr, median_reference=float(np.median(refd)))
    # ---- C4 and Voynich
    grp = te.groupby(['kind', 'process']).agg(n=('dist', 'size'), **{c: (c, 'mean') for c in ['p_logistic', 'p_forest', 'p_boosting', 'p3_natural', 'p3_cipher', 'p3_generated', 'dist', 'dist_pct']}, in_dist=('in_dist', 'sum'))
    res['held_out'] = {f'{k}|{p}': {c: float(v) for c, v in r.items()} for (k, p), r in grp.iterrows()}
    want = dict(autocopist=0, rugg=0, volunteers=0, lang8=0, naibbe=1)
    c4 = {p: bool((res['held_out'][f'mimic|{p}']['p_' + PRIMARY] >= 0.5) == bool(w)) for p, w in want.items() if f'mimic|{p}' in res['held_out']}
    res['C4'] = c4
    rec = [c2[p][PRIMARY] for p in c2]; v = res['held_out'].get('voynich|ZL units')
    conds = collections.OrderedDict([
        ('C1 leave-source-out AUC >= 0.95', c1[PRIMARY]['auc'] >= 0.95),
        ('C2 leave-process-out mean recall >= 0.8, none under 0.5', float(np.mean(rec)) >= 0.8 and min(rec) >= 0.5),
        ('C3 other genres recall >= 0.9', res['C3'][PRIMARY] >= 0.9),
        ('C4 all mimic families on the right side', all(c4.values()) and len(c4) == 5),
        ('C5 at least 6 of 8 Voynich chunks in distribution', bool(v and v['in_dist'] >= 6))])
    res['conditions'] = {k: bool(x) for k, x in conds.items()}
    if all(conds.values()):
        ps = [v['p_' + m] for m in MODELS]
        res['verdict'] = 'language underneath' if min(ps) >= 0.8 else 'generated' if max(ps) <= 0.2 else 'undecided'
    else:
        res['verdict'] = 'no verdict (failed: ' + '; '.join(k for k, x in conds.items() if not x) + ')'
    # ---- description: nearest sources, features where Voynich leaves each kind
    vz = Zt[(te.kind == 'voynich').values & (te.process == 'ZL units').values]
    near = collections.Counter()
    for z in vz:
        d = np.sqrt(((Z - z) ** 2).sum(1))
        for i in np.argsort(d)[:10]:
            near[f"{tr.kind[i]} / {tr.process[i]} / {tr.source[i]}"] += 1
    res['nearest'] = near.most_common(15)
    kinds = collections.OrderedDict()
    for k in ('natural', 'cipher', 'generated'):
        A = Z[(tr.kind == k).values]; kinds[k] = (A.mean(0), A.std(0) + 1e-9)
    vm = vz.mean(0); feat = []
    for j, name in enumerate(F):
        A = X[(tr.kind == 'natural').values][:, j]; val = float(te[F].values[(te.kind == 'voynich').values & (te.process == 'ZL units').values][:, j].mean())
        feat.append(dict(feature=name, voynich=val, natural_median=float(np.median(A)), pct_in_natural=float((A <= val).mean()),
                         **{f'z_{k}': float((vm[j] - m[j]) / s[j]) for k, (m, s) in kinds.items()}))
    res['features'] = feat
    imp = full['forest'].feature_importances_; res['importance'] = sorted(((F[j], float(imp[j])) for j in range(len(F))), key=lambda x: -x[1])[:15]
    json.dump(res, open(os.path.join(HERE, f'model_results{tag}.json'), 'w'), indent=1)
    # ---- report
    L = ['# Phase 2: linguistic features and classifiers' + (' (11 Nov 2026)' if not tag else ', second round with structured generators (12 Nov 2026); training rows from ' + ' + '.join(files)), '',
         'Scripts `features.py`, `build.py`, `model.py` (protocol and the rule for a verdict in the docstring of `model.py`, written before the Voynich rows were looked at). '
         'Reproduce from `targets/voynich`: `python phase2/corpora2.py`, `python lines/fetch_mss.py`, `python phase2/build.py`, `python phase2/model.py`.', '',
         f"Training chunks {len(tr)} (natural {(tr.kind == 'natural').sum()}, cipher {(tr.kind == 'cipher').sum()}, generated {(tr.kind == 'generated').sum()}), {len(F)} features, 4,000 tokens a chunk.", '',
         '## Checks on the models', '', '| check | logistic | forest | boosting |', '|---|---|---|---|',
         '| C1 leave-source-out AUC | ' + ' | '.join(f"{c1[m]['auc']:.3f}" for m in MODELS) + ' |', '| C1 leave-source-out accuracy | ' + ' | '.join(f"{c1[m]['acc']:.3f}" for m in MODELS) + ' |',
         f"| C3 other genres called meaningful (n {res['C3']['n']}) | " + ' | '.join(f"{res['C3'][m]:.2f}" for m in MODELS) + ' |', '',
         'C2, a process left out of training, share of its chunks put on the right side:', '', '| process (truth) | n | logistic | forest | boosting |', '|---|---|---|---|---|']
    for p, r in c2.items():
        L.append(f"| {p} ({r['truth']}) | {r['n']} | " + ' | '.join(f'{r[m]:.2f}' for m in MODELS) + ' |')
    L += ['', '## Held-out texts: mimics (truth known) and Voynich', '', '| text | chunks | P(meaningful) logistic | forest | boosting | 3-class: natural / cipher / generated | distance (percentile of training) | chunks in distribution |', '|---|---|---|---|---|---|---|---|']
    for k, r in res['held_out'].items():
        L.append(f"| {k.replace('|', ': ')} | {r['n']:.0f} | {r['p_logistic']:.2f} | {r['p_forest']:.2f} | {r['p_boosting']:.2f} | {r['p3_natural']:.2f} / {r['p3_cipher']:.2f} / {r['p3_generated']:.2f} | {r['dist']:.1f} ({r['dist_pct']:.2f}) | {r['in_dist']:.0f} |")
    L += ['', f"Novelty threshold (95th percentile of training distances) {thr:.1f}; median {res['C5']['median_reference']:.1f}.", '', '## Conditions and verdict', '']
    L += [f"- {k}: {'met' if x else 'NOT met'}" for k, x in conds.items()] + ['', f"**Verdict: {res['verdict']}**", '',
          '## Description: nearest training chunks to the Voynich chunks (ZL units; count among the 10 nearest of each of 8 chunks)', '']
    L += [f'- {n}: {c}' for n, c in res['nearest']]
    L += ['', '## Description: where Voynich sits, feature by feature', '', 'z = (Voynich mean - kind mean) / kind sd on standardised features; the 25 features furthest from natural language first.', '',
          '| feature | Voynich | natural median | percentile in natural | z natural | z cipher | z generated |', '|---|---|---|---|---|---|---|']
    for r in sorted(feat, key=lambda r: -abs(r['z_natural']))[:25]:
        L.append(f"| {r['feature']} | {r['voynich']:.3f} | {r['natural_median']:.3f} | {r['pct_in_natural']:.2f} | {r['z_natural']:+.1f} | {r['z_cipher']:+.1f} | {r['z_generated']:+.1f} |")
    inside = [r['feature'] for r in feat if 0.05 <= r['pct_in_natural'] <= 0.95]
    L += ['', f"Features where Voynich is inside the middle 90% of natural languages ({len(inside)} of {len(F)}): " + ', '.join(inside) + '.', '',
          'Most used features (random forest importance): ' + ', '.join(f'{n} {v:.3f}' for n, v in res['importance']) + '.', '', f'Runtime {time.time() - t0:.0f} s.']
    open(os.path.join(HERE, f'phase2{tag}.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    main()
