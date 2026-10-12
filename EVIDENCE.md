# Evidence: does it work, and how often does it not?

**Data used:** 11,146 labelled claims (Apr 2025 to Jun 2026) with 141 confirmed frauds, after removing 681 repeated claim rows (partners re-submit bounced claims) and 202 claims still under investigation. Raw counts: 12,029 rows, 11,348 unique claims.

## Why accuracy is the wrong yardstick
Fraud is about 1% of claims overall and 2.5% to 3% since May 2026. A model that says "nobody is fraud" is 97% to 99% accurate and stops nothing. I therefore report how many frauds are caught among the claims the desk can actually review (about 5% of claims: 40 of roughly 750 a month), and the rupees.

## How I checked (always on claims the model had not seen, by date or by outlet)
| Check | Claims | Frauds | Model reviews top | Frauds caught | Wrong holds | Rs fraud stopped | Rs goodwill lost | Net Rs | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|---|---|---|
| 1. Train to May 2026, test June 2026 | 720 | 22 | 38 | 11 (50%) | 27 | 17,356 | 10,260 | 7,096 | 0.32 | 0.88 |
| 2. Whole outlets held out (post-May data) | 1,431 | 36 | 76 | 22 (61%) | 54 | 31,556 | 20,520 | 11,036 | 0.28 | 0.93 |
| 3. Later 40% of post-May period | 573 | 16 | 31 | 10 (63%) | 21 | 14,356 | 7,980 | 6,376 | 0.45 | 0.91 |

Checks 1 to 3 overlap in the post-May data, so they are three views of the same two months, not three independent proofs.
Goodwill is Rs 380 per genuine claim held (policy section 4). Net = fraud stopped minus goodwill lost.

**Per claim checked:** Rs 415 to 463 of fraud stopped, Rs 145 to 206 net after goodwill.

## Against simpler rules (same checks)
| | Check 1 caught | Check 2 caught | Check 3 caught |
|---|---|---|---|
| Model | 11 | 22 | 10 |
| Rule: young outlet + no inspection + small claim | 12 | 15 | 8 |
| "Flag new partners" (Ritu's idea) | 9 | 11 | 5 |

The model clearly beats the new-partner flag. It beats the three-part rule in two of three checks and ties in one, so the rule is a strong fallback.

## How often it is wrong
- About 7 in 10 claims it sends for review are genuine (precision about 30%). Each costs about Rs 380 of goodwill.
- It misses roughly 4 to 5 in 10 frauds even when reviewing the full desk capacity. The misses are mostly: first-time fraud at outlets with no history, and fraud on ordinary-looking claims from established outlets.
- Frauds before May 2026 looked different (large claims at 7 older franchises, repeat customers). A model trained only on those scored worse than random on the post-May claims, which is why post-May claims are weighted 5x.

## Known weak spots
1. Only 36 frauds since the May rule change. Every number above is noisy; a single outlet moves it.
2. Outlets onboarded after June 2026 have no history; they are scored from claim details only.
3. About 200 undecided claims were excluded, and Tanmay's note says old open cases were stored as 0 in the legacy system. Some "not fraud" labels in legacy data may be wrong. Cannot be fixed from the data.
4. The model ranks; it was not tuned to be a probability.
