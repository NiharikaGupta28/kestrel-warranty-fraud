"""Cleaning + feature engineering for Kestrel warranty-claim fraud scoring."""
import re
import numpy as np
import pandas as pd

FAULTS = ["blade jammed", "burning smell", "display not working", "filter indicator stuck",
          "loud noise while running", "motor not running", "not charging",
          "power button not working", "remote not working", "tripping mcb",
          "unit not heating", "water leaking"]
POLICY_CHANGE = pd.Timestamp("2026-05-01")
NEW_PARTNER_CUTOFF = pd.Timestamp("2025-07-01")  # ~12 months before the end of the data


def clean_serial(s):
    return re.sub(r"[^A-Z0-9]", "", str(s).strip().upper())


def fault_category(text):
    """Free text is reduced to a fixed category; anything else is 'other'.
    The model never reads raw free text (it is partner-typed and untrusted)."""
    t = str(text).lower()
    for f in FAULTS:
        if t.startswith(f):
            return f
    return "other"


def load_raw(data_dir="data"):
    tr = pd.read_csv(f"{data_dir}/train.csv")
    te = pd.read_csv(f"{data_dir}/test_unlabelled.csv")
    pa = pd.read_csv(f"{data_dir}/partners.csv")
    pr = pd.read_csv(f"{data_dir}/products.csv")
    return tr, te, pa, pr


def dedupe_train(tr):
    """Partners re-submit bounced claims: same claim_id twice. Keep the latest."""
    tr = tr.sort_values(["claim_id", "submitted_at"]).drop_duplicates("claim_id", keep="last")
    return tr.reset_index(drop=True)


def base_features(df, pa, pr):
    d = df.copy()
    d["ts"] = pd.to_datetime(d["submitted_at"])
    d = d.merge(pr, on="sku", how="left").merge(pa, on="partner_id", how="left")
    d["serial_clean"] = d["product_serial"].map(clean_serial)
    d["serial_valid"] = d["serial_clean"].str.fullmatch(r"KH\d{9}").astype(int)
    d["serial_messy"] = (d["product_serial"].astype(str) != d["serial_clean"]).astype(int)
    d["ratio"] = d["claim_amount_inr"] / d["list_price_inr"]
    d["small_claim"] = (d["claim_amount_inr"] < 2000).astype(int)
    d["post_change"] = (d["ts"] >= POLICY_CHANGE).astype(int)
    d["auto_approved_zone"] = d["small_claim"] * d["post_change"]
    d["photo"] = (d["photo_attached"] == "Y").astype(int)
    d["inspected"] = (d["partner_inspected"] == "Y").astype(int)
    d["has_note"] = d["inspector_note"].notna().astype(int)
    d["onb"] = pd.to_datetime(d["onboarded_date"])
    d["partner_age_days"] = (d["ts"] - d["onb"]).dt.days
    d["new_partner"] = (d["onb"] >= NEW_PARTNER_CUTOFF).astype(int)
    d["warranty_days"] = d["warranty_months"] * 30.4
    d["warranty_used"] = d["days_since_purchase"] / d["warranty_days"]
    d["fault"] = d["claim_description"].map(fault_category)
    d["hour"] = d["ts"].dt.hour
    d["prior"] = d["customer_prior_claims"]
    d["uninspected"] = 1 - d["inspected"]
    d["young_partner"] = (d["partner_age_days"] < 365).astype(int)
    d["young_uninsp_small"] = d["young_partner"] * d["uninspected"] * d["small_claim"]
    d["ratio_hi"] = (d["ratio"] > 0.55).astype(int)
    return d


def behaviour_features(d, window_days=30):
    """Label-free partner behaviour from the PAST only (trailing window), computed on
    all claims (labelled + unlabelled) sorted by time. No future leakage."""
    d = d.sort_values("ts").copy()
    out = []
    for pid, g in d.groupby("partner_id"):
        g = g.set_index("ts")
        roll = g["small_claim"].rolling(f"{window_days}D", closed="left")
        cnt = g["small_claim"].rolling(f"{window_days}D", closed="left").count()
        small_cnt = roll.sum()
        uninsp = (1 - g["inspected"]).rolling(f"{window_days}D", closed="left").sum()
        out.append(pd.DataFrame({"claim_id": g["claim_id"].values,
                                 "p_cnt30": cnt.values,
                                 "p_small30": small_cnt.values,
                                 "p_uninsp30": uninsp.values}))
    b = pd.concat(out)
    d = d.merge(b, on="claim_id", how="left")
    d["p_cnt30"] = d["p_cnt30"].fillna(0)
    d["p_small30"] = d["p_small30"].fillna(0)
    d["p_uninsp30"] = d["p_uninsp30"].fillna(0)
    d["p_uninsp_share30"] = np.where(d["p_cnt30"] > 0, d["p_uninsp30"] / d["p_cnt30"].clip(lower=1), 0)
    d["p_small_share30"] = np.where(d["p_cnt30"] > 0, d["p_small30"] / d["p_cnt30"].clip(lower=1), 0)
    # serial seen before (any earlier claim with same cleaned serial)
    d = d.sort_values("ts")
    d["serial_seen_before"] = d.groupby("serial_clean").cumcount().clip(upper=3)
    return d


def history_features(d, hist):
    """Partner fraud history from LABELLED rows strictly older than the scoring window.
    hist: labelled dataframe (is_fraud in 0/1) known at scoring time."""
    h = hist[hist["is_fraud"].isin([0, 1])]
    g = h.groupby("partner_id")["is_fraud"].agg(["sum", "count"])
    prior_rate = h["is_fraud"].mean()
    k = 20  # smoothing
    g["p_fraud_rate"] = (g["sum"] + k * prior_rate) / (g["count"] + k)
    g["p_fraud_n"] = g["sum"]
    d = d.merge(g[["p_fraud_rate", "p_fraud_n"]], left_on="partner_id", right_index=True, how="left")
    d["p_fraud_rate"] = d["p_fraud_rate"].fillna(prior_rate)
    d["p_fraud_n"] = d["p_fraud_n"].fillna(0)
    return d


NUM = ["days_since_purchase", "claim_amount_inr", "list_price_inr", "ratio", "small_claim",
       "post_change", "auto_approved_zone", "photo", "inspected", "has_note", "partner_age_days",
       "new_partner", "warranty_used", "prior", "serial_valid", "serial_messy",
       "p_cnt30", "p_small_share30", "p_uninsp_share30", "uninspected", "young_partner", "young_uninsp_small", "ratio_hi", "serial_seen_before", "p_fraud_rate", "p_fraud_n", "hour"]
CAT = ["fault", "partner_type", "family"]


def design(d):
    X = d[NUM].copy()
    for c in CAT:
        X[c] = d[c].astype("category")
    return X
