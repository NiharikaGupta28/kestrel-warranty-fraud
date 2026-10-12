"""Honest out-of-time validation. Writes evidence/validation.json + prints a table.
Run from repo root:  python src/evaluate.py"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
import features as F, modeling as M
from model_utils import hgb
from train import build, POST_WEIGHT

al, pa, pr = build()
lab = al[al.is_fraud.isin([0, 1])].copy()
post = lab[lab.post_change == 1]; pre = lab[lab.post_change == 0]

def fit_score(f, v, seeds=3):
    ft = M.add_history_oot(f); vt = F.history_features(v, f)
    Xh, Xvh = F.design(ft), F.design(vt)
    drop = ["p_fraud_rate", "p_fraud_n"]
    w = np.where(ft.post_change == 1, POST_WEIGHT, 1.0)
    a = np.mean([hgb(Xh, ft.is_fraud, w, s).predict_proba(Xvh)[:, 1] for s in range(seeds)], axis=0)
    b = np.mean([hgb(Xh.drop(columns=drop), ft.is_fraud, w, s).predict_proba(Xvh.drop(columns=drop))[:, 1] for s in range(seeds)], axis=0)
    return (a + b) / 2

def baselines(v):
    rng = np.random.RandomState(0); jit = 1e-6 * rng.rand(len(v))
    rule = (v.young_partner * v.uninspected * v.small_claim).values + jit
    newp = v.new_partner.values + jit
    return {"rule: young partner + uninspected + small": rule, "new-partner flag only (Ritu's view)": newp}

res = {}
def record(name, v, s):
    r = {"model": M.eval_scores(v.is_fraud, s, v.claim_amount_inr)}
    for k, b in baselines(v).items():
        r[k] = M.eval_scores(v.is_fraud, b, v.claim_amount_inr)
    r["accuracy_always_not_fraud"] = float(1 - v.is_fraud.mean())
    res[name] = r

# 1) train through May -> validate June (strict out-of-time, post-change regime)
f = lab[lab.ts < "2026-06-01"]; v = lab[(lab.ts >= "2026-06-01") & (lab.ts < "2026-07-01")]
record("1_out_of_time_June", v, fit_score(f, v))
# 2) unseen outlets: partner-grouped 5-fold inside post-change months (all pre-change data always in train)
rng = np.random.RandomState(1); parts = post.partner_id.unique(); fold = dict(zip(parts, rng.randint(0, 5, len(parts))))
S, V = [], []
for i in range(5):
    v = post[post.partner_id.map(fold) == i]; f = pd.concat([pre, post[post.partner_id.map(fold) != i]])
    S.append(fit_score(f, v)); V.append(v)
record("2_unseen_outlets_grouped_cv", pd.concat(V), np.concatenate(S))
# 3) later 40% of post-change period, outlets already seen (closest to how the test period behaves)
cut = post.ts.quantile(0.6); f = pd.concat([pre, post[post.ts < cut]]); v = post[post.ts >= cut]
record("3_later_post_change_period", v, fit_score(f, v))

os.makedirs("evidence", exist_ok=True)
json.dump(res, open("evidence/validation.json", "w"), indent=1, default=float)
for k, r in res.items():
    print("\n", k, "| claims", r["model"]["n"], "| frauds", r["model"]["frauds"], "| accuracy of 'nobody is fraud':", round(r["accuracy_always_not_fraud"], 3))
    for name in ["model"] + list(baselines(v).keys()):
        m = r[name]
        print(f"  {name:48s} PR-AUC {m['pr_auc']:.2f}  ROC {m['roc_auc']:.2f}  caught {m['caught']}/{m['frauds']} in top {m['k']}  "
              f"Rs stopped {m['rupees_stopped']:,.0f}  goodwill {m['goodwill_cost']:,.0f}  net {m['net']:,.0f}  Rs/claim checked {m['rupees_per_claim_checked']:,.0f}")
