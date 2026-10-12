"""Train final model on all labelled claims, score test, write predictions.csv + artifacts.
Run from repo root:  python src/train.py"""
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd, joblib
import features as F, modeling as M

POST_WEIGHT = 5.0
SEEDS = range(5)

def build(data_dir="data"):
    tr, te, pa, pr = F.load_raw(data_dir)
    tr = F.dedupe_train(tr)
    al = F.behaviour_features(F.base_features(pd.concat([tr, te], ignore_index=True), pa, pr))
    return al, pa, pr

def fit_all(lab):
    ft = M.add_history_oot(lab)                      # partner history from strictly earlier months
    X_hist = F.design(ft)
    X_nohist = X_hist.drop(columns=["p_fraud_rate", "p_fraud_n"])
    w = np.where(ft.post_change == 1, POST_WEIGHT, 1.0)
    from model_utils import hgb
    m_hist = [hgb(X_hist, ft.is_fraud, w, s) for s in SEEDS]
    m_nohist = [hgb(X_nohist, ft.is_fraud, w, s) for s in SEEDS]
    return m_hist, m_nohist, X_hist.columns.tolist()

def predict(m_hist, m_nohist, X_hist):
    a = np.mean([m.predict_proba(X_hist)[:, 1] for m in m_hist], axis=0)
    X_n = X_hist.drop(columns=["p_fraud_rate", "p_fraud_n"])
    b = np.mean([m.predict_proba(X_n)[:, 1] for m in m_nohist], axis=0)
    return (a + b) / 2

if __name__ == "__main__":
    al, pa, pr = build()
    lab = al[al.is_fraud.isin([0, 1])].copy()
    test = al[al.is_fraud.isna() & (al.ts >= "2026-07-01")].copy()
    m_hist, m_nohist, cols = fit_all(lab)
    test_h = F.history_features(test, lab)
    score = predict(m_hist, m_nohist, F.design(test_h))
    sub = pd.read_csv("data/sample_submission.csv")
    out = pd.DataFrame({"claim_id": test_h.claim_id.values, "score": np.round(score, 6)})
    out = sub[["claim_id"]].merge(out, on="claim_id", how="left")
    assert len(out) == len(sub) and out.score.notna().all() and out.claim_id.is_unique
    out.to_csv("predictions.csv", index=False)
    joblib.dump(dict(m_hist=m_hist, m_nohist=m_nohist, cols=cols), "model/model.joblib")
    from serving_state import build_state
    joblib.dump(build_state(al, lab, pa, pr, test_h.assign(score=score)), "model/state.joblib")
    print("wrote model/model.joblib and model/state.joblib")
    print("wrote predictions.csv", out.shape, "score range", out.score.min(), out.score.max())
    print("top-120 (3 months x 40) share of test:", round(120 / len(out), 3))
