import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import average_precision_score, roc_auc_score
import features as F

GOODWILL = 380.0   # policy §4: goodwill per genuine claim held
CAPACITY_SHARE = 40 / 750  # desk reviews 40 of ~750 claims a month


def month_key(d):
    return d["ts"].dt.to_period("M")


def add_history_oot(d):
    """Partner fraud history for training rows, computed month-by-month from strictly earlier months."""
    d = d.copy()
    parts = []
    mk = month_key(d)
    for m in sorted(mk.unique()):
        cur = d[mk == m]
        past = d[(mk < m) & d["is_fraud"].isin([0, 1])]
        parts.append(F.history_features(cur, past) if len(past) else
                     cur.assign(p_fraud_rate=np.nan, p_fraud_n=0))
    out = pd.concat(parts)
    out["p_fraud_rate"] = out["p_fraud_rate"].fillna(d["is_fraud"].mean())
    return out


def fit_hgb(Xtr, ytr, seed=0):
    m = HistGradientBoostingClassifier(
        max_depth=4, learning_rate=0.05, max_iter=250, min_samples_leaf=30,
        l2_regularization=1.0, categorical_features="from_dtype", random_state=seed)
    m.fit(Xtr, ytr)
    return m


def fit_logit(Xtr, ytr):
    X = pd.get_dummies(Xtr, columns=F.CAT, dtype=float)
    m = make_pipeline(StandardScaler(), LogisticRegression(C=0.3, class_weight="balanced", max_iter=2000))
    m.fit(X, ytr)
    m.cols_ = list(X.columns)
    return m


def predict_logit(m, X):
    Z = pd.get_dummies(X, columns=F.CAT, dtype=float).reindex(columns=m.cols_, fill_value=0.0)
    return m.predict_proba(Z)[:, 1]


def eval_scores(y, s, amount, share=CAPACITY_SHARE):
    y = np.asarray(y); s = np.asarray(s); amount = np.asarray(amount)
    n = len(y); k = max(1, int(round(n * share)))
    top = np.argsort(-s)[:k]
    caught = y[top].sum()
    rs_caught = (amount[top] * y[top]).sum()
    cost = (1 - y[top]).sum() * GOODWILL
    return dict(n=n, frauds=int(y.sum()), pr_auc=average_precision_score(y, s), roc_auc=roc_auc_score(y, s),
                k=k, caught=int(caught), recall_at_k=caught / max(y.sum(), 1), precision_at_k=caught / k,
                rupees_stopped=rs_caught, goodwill_cost=cost, net=rs_caught - cost,
                rupees_per_claim_checked=rs_caught / k,
                base_accuracy=1 - y.mean())
