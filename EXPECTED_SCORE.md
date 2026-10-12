# What I expect predictions.csv to score, and why
(Written before submitting. Scoring method is not disclosed, so I give my expectation for the likely measures.)

| Measure | Expected | Range I would not be surprised by |
|---|---|---|
| PR-AUC (average precision) | about 0.30 | 0.15 to 0.45 |
| ROC-AUC | about 0.90 | 0.83 to 0.95 |
| Frauds caught in the top 5% of scores | about 50% | 35% to 60% |
| Precision in the top 5% | about 30% | 18% to 40% |

**Why.** I scored claims I had held back by date and by outlet. Three checks gave PR-AUC 0.28 to 0.45, ROC-AUC 0.88 to 0.93, and 10 of 16, 11 of 22 and 22 of 36 frauds in the top ~5% of scores.
**Why I lean to the lower half of the range:** the test period (Jul-Sep 2026) is later than anything I validated on, outlets onboarded after June are unseen, and each check had only 16 to 36 frauds, so the numbers are noisy.
**Why not higher:** fraud is about 1 to 3% of claims and much of it hides among ordinary-looking small claims.
Accuracy would be about 97 to 98% for a model that flags nothing, so I do not expect accuracy to say anything useful.
