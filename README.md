# Kestrel warranty-claim fraud scoring

Scores each warranty claim before payout so the investigation desk (40 claims a month) looks at the riskiest ones first.
Runs fully offline. **No paid API, no API key, cost per claim: Rs 0.**

## What is in here
| Path | What |
|---|---|
| `predictions.csv` | Fraud score for every row of `test_unlabelled.csv` (higher = more likely fraud) |
| `app/` | The service (`POST /score`) and the one-page screen |
| `src/` | Cleaning, features, training, validation code |
| `model/` | Trained model and the small reference snapshot the service needs |
| `evidence/validation.json`, `EVIDENCE.md` | How well it works and how often it fails |
| `MEMO.md` | One-page memo to Ritu |
| `DECISIONS.md` | Every judgement call and why |

## Run the service (about 2 minutes, clean machine)
Needs Python 3.10 or newer.
```
git clone https://github.com/NiharikaGupta28/kestrel-warranty-fraud.git
cd kestrel-warranty-fraud
python -m venv .venv
.venv\Scripts\activate          # Windows.   Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000
```
Open http://127.0.0.1:8000 for the screen. The trained model is included, so nothing else is needed.
If you see "Model files missing or unreadable" (for example a different scikit-learn version), rebuild it with the retrain steps below.

### API
```
curl -X POST http://127.0.0.1:8000/score -H "Content-Type: application/json" -d "{\"partner_id\":\"SP3160\",\"sku\":\"KH-AF-02\",\"claim_amount_inr\":1450,\"days_since_purchase\":95,\"partner_inspected\":\"N\"}"
```
Required: `partner_id, sku, claim_amount_inr, days_since_purchase, partner_inspected`.
Optional: `photo_attached, customer_prior_claims, product_serial, submitted_at`.
Returns `score`, `band` (REVIEW / WATCH / PAY), `action`, and plain-English `reasons`. Bad input returns a clear 422 message; missing model files return 503 with the fix.

## Retrain / regenerate predictions
The raw customer data is **not** in this repo (policy section 10). Put the five CSVs in `data/`:
`train.csv, test_unlabelled.csv, partners.csv, products.csv, sample_submission.csv`, then:
```
python src/train.py        # writes predictions.csv, model/model.joblib, model/state.joblib
python src/evaluate.py     # writes evidence/validation.json and prints the results
```

## Known limits (short version, see MEMO.md and DECISIONS.md)
- Only 141 confirmed frauds in the labelled data, 36 of them since the May 2026 rule change. Treat scores as a ranking aid.
- The service uses a snapshot of outlet activity up to 30 Sep 2026. Retrain monthly.
