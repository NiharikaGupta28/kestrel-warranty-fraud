"""Small reference snapshot the API needs to score ONE claim (no customer-level rows, serials are hashed)."""
import hashlib
import numpy as np, pandas as pd

def _h(s): return hashlib.sha1(s.encode()).hexdigest()[:16]

def build_state(al, lab, pa, pr, scored_test):
    end = al.ts.max()
    recent = al[al.ts > end - pd.Timedelta(days=30)]
    g = recent.groupby("partner_id").agg(p_cnt30=("claim_id", "size"), p_small30=("small_claim", "sum"),
                                         p_uninsp30=("uninspected", "sum"))
    k = 20; prior = lab.is_fraud.mean()
    h = lab.groupby("partner_id").is_fraud.agg(["sum", "count"])
    h["p_fraud_rate"] = (h["sum"] + k * prior) / (h["count"] + k)
    h["p_fraud_n"] = h["sum"]
    serial_counts = al.groupby("serial_clean").size()
    # review thresholds: top 5.3% of scored recent claims = desk capacity (40 of ~750 a month)
    s = scored_test["score"].values
    return dict(
        partners=pa.set_index("partner_id"), products=pr.set_index("sku"),
        partner_recent=g, partner_hist=h[["p_fraud_rate", "p_fraud_n"]], prior_rate=float(prior),
        serial_hashes={_h(x): int(c) for x, c in serial_counts.items()},
        snapshot_end=str(end),
        thr_review=float(np.quantile(s, 1 - 40 / 750)), thr_watch=float(np.quantile(s, 1 - 0.12)),
    )
