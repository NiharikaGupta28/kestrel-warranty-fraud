"""Score ONE claim and explain it in plain English. No network, no paid API."""
import os, sys, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
import numpy as np, pandas as pd, joblib
import features as F
from serving_state import _h

REQUIRED = ["partner_id", "sku", "claim_amount_inr", "days_since_purchase", "partner_inspected"]
DEFAULTS = {"submitted_at": None, "product_serial": "", "photo_attached": "N",
            "claim_description": "", "inspector_note": None, "customer_prior_claims": 0, "claim_id": "NEW"}

class ScoringError(ValueError):
    pass

_M = _S = None
def _load():
    global _M, _S
    if _M is None:
        try:
            _M = joblib.load(os.path.join(ROOT, "model", "model.joblib"))
            _S = joblib.load(os.path.join(ROOT, "model", "state.joblib"))
        except Exception as e:
            raise RuntimeError("Model files missing or unreadable. Run:  python src/train.py   (then restart). Detail: %s" % e)
    return _M, _S

def _num(rec, key, lo=None):
    try:
        v = float(rec[key])
    except Exception:
        raise ScoringError(f"'{key}' must be a number")
    if lo is not None and v < lo:
        raise ScoringError(f"'{key}' must be >= {lo}")
    return v

def score_claim(rec):
    M, S = _load()
    rec = {**DEFAULTS, **{k: v for k, v in rec.items() if v is not None or k in ("inspector_note",)}}
    miss = [k for k in REQUIRED if rec.get(k) in (None, "")]
    if miss:
        raise ScoringError("Missing required field(s): " + ", ".join(miss))
    if rec["partner_id"] not in S["partners"].index:
        raise ScoringError(f"Unknown partner_id '{rec['partner_id']}' (not in partners.csv)")
    if rec["sku"] not in S["products"].index:
        raise ScoringError(f"Unknown sku '{rec['sku']}' (not in products.csv)")
    amount = _num(rec, "claim_amount_inr", 1); days = _num(rec, "days_since_purchase", 0)
    prior = int(_num(rec, "customer_prior_claims", 0))
    if str(rec["partner_inspected"]).upper() not in ("Y", "N") or str(rec["photo_attached"]).upper() not in ("Y", "N"):
        raise ScoringError("'partner_inspected' and 'photo_attached' must be Y or N")
    ts = rec["submitted_at"] or S["snapshot_end"]
    try:
        pd.Timestamp(ts)
    except Exception:
        raise ScoringError("'submitted_at' must look like 2026-09-30 14:05")
    df = pd.DataFrame([dict(claim_id=rec["claim_id"], submitted_at=str(ts)[:16], partner_id=rec["partner_id"], sku=rec["sku"],
                            product_serial=rec["product_serial"], days_since_purchase=days, claim_amount_inr=amount,
                            photo_attached=str(rec["photo_attached"]).upper(), partner_inspected=str(rec["partner_inspected"]).upper(),
                            claim_description=rec["claim_description"], inspector_note=rec["inspector_note"],
                            customer_prior_claims=prior, source="crm")])
    d = F.base_features(df, S["partners"].reset_index(), S["products"].reset_index())
    pr = S["partner_recent"].reindex([rec["partner_id"]]).fillna(0).iloc[0]
    d["p_cnt30"] = pr.p_cnt30
    d["p_small_share30"] = pr.p_small30 / pr.p_cnt30 if pr.p_cnt30 > 0 else 0
    d["p_uninsp_share30"] = pr.p_uninsp30 / pr.p_cnt30 if pr.p_cnt30 > 0 else 0
    d["serial_seen_before"] = min(S["serial_hashes"].get(_h(d.serial_clean.iloc[0]), 0), 3) if d.serial_clean.iloc[0] else 0
    hist = S["partner_hist"].reindex([rec["partner_id"]])
    d["p_fraud_rate"] = hist.p_fraud_rate.fillna(S["prior_rate"]).values
    d["p_fraud_n"] = hist.p_fraud_n.fillna(0).values
    X = F.design(d)[M["cols"]]
    a = np.mean([m.predict_proba(X)[:, 1] for m in M["m_hist"]])
    Xn = X.drop(columns=["p_fraud_rate", "p_fraud_n"])
    b = np.mean([m.predict_proba(Xn)[:, 1] for m in M["m_nohist"]])
    score = float((a + b) / 2)
    band = "REVIEW" if score >= S["thr_review"] else ("WATCH" if score >= S["thr_watch"] else "PAY")
    return dict(score=round(score, 4), band=band, action={"REVIEW": "Hold and send to the investigation desk",
                "WATCH": "Pay, but flag the outlet for the next review round", "PAY": "Pay as normal"}[band],
                reasons=reasons(d.iloc[0], S, hist), note="Score is a ranking aid, not a probability. Final call is the investigator's.")

def reasons(r, S, hist):
    out = []
    if r.young_partner and r.uninspected and r.small_claim:
        out.append("Small claim (under Rs 2,000) with no inspection, from an outlet onboarded under a year ago. After the 1 May rule change this combination had a 21% fraud rate in past data, against 0.1% for older outlets.")
    elif r.uninspected and r.small_claim and r.post_change:
        out.append("Small claim paid without inspection (auto-approved since 1 May). Low risk on its own for an established outlet.")
    if r.young_partner and not (r.uninspected and r.small_claim):
        out.append("Outlet is under a year old, but this claim was inspected or is not small, which has been low risk in past data.")
    n = float(hist.p_fraud_n.fillna(0).iloc[0])
    if n >= 3:
        out.append(f"This outlet has {int(n)} confirmed fraud cases in the labelled history.")
    if r.p_cnt30 >= 8 and r.young_partner:
        out.append(f"High recent volume from a young outlet ({int(r.p_cnt30)} claims in the last 30 days).")
    if r.ratio >= 0.55:
        out.append(f"Claim is {r.ratio:.0%} of the product's list price (typical claims are 20-40%).")
    if r.prior >= 2:
        out.append(f"Customer already has {int(r.prior)} earlier warranty claims.")
    if r.days_since_purchase < 60 and r.small_claim and r.uninspected:
        out.append(f"Filed only {int(r.days_since_purchase)} days after purchase.")
    if not r.serial_valid:
        out.append("Serial number is not in the standard KH + 9 digits format (check it was typed correctly).")
    if r.serial_seen_before >= 2:
        out.append("This serial number has appeared on earlier claims.")
    return out or ["No unusual pattern found in the claim details."]
