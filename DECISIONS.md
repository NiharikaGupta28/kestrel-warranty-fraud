# Decisions and assumptions (what was unclear, what I chose, why)

1. **KPI.** Ritu asked for accuracy above 97%. I did not use it as the target. Fraud is about 1% to 3% of claims, so "flag nothing" already scores 97% to 99%. I report frauds caught among the ~5% of claims the desk can review, and rupees per claim checked (Farhan's ask). I will still show her an accuracy figure so the board can see why it is not enough.
2. **Review capacity.** 40 claims a month of about 750 = 5.3%. All "top-K" numbers use that share.
3. **Costs.** Fraud paid = full claim amount. A genuine claim held = Rs 380 goodwill (policy section 4). The Rs 260 service-contact cost is used only when comparing with re-inspecting claims; I assumed desk review time is already paid for.
4. **Duplicates.** Same claim_id appearing twice (681 rows) = re-submitted claim. Kept the latest row.
5. **Undecided cases.** 215 blank outcomes (202 unique claims, all from the new CRM) are dropped from training, not treated as 0. Legacy rows that may be hidden undecided cases cannot be identified; flagged as a limitation.
6. **Time.** Validated by date and by outlet, never a random split, because the test set is the most recent three months and rules changed on 1 May 2026.
7. **Regime change.** Post-May fraud (small, uninspected, young outlets) differs from pre-May fraud. Post-May rows are weighted 5x in training. Chosen by comparing 1x and 5x on held-out data.
8. **"New partner".** Defined as onboarded within the last 12 months (about 60 outlets, matches policy section 6). Partner age in days is also a feature.
9. **Partner fraud history.** Computed only from earlier months for each row, to avoid leaking the answer. Final score = average of a model with partner history and one without, because history helps for repeat outlets but hurts for brand-new ones.
10. **Serials.** Cleaned (case, spaces, dashes). About 9% are malformed; kept as a feature, not discarded.
11. **Timestamps.** Policy section 9 says only legacy resolution events were stored in UTC. Claim `submitted_at` is IST, so no conversion was made. Resolution timestamps are not in the data.
12. **Free text.** `claim_description` is reduced to one of 12 fault categories; `inspector_note` is only used as present/absent. Free text typed by partners is not trusted as an input.
13. **No leakage found** in the provided columns: nothing records the investigation outcome or payout, so all columns were allowed except `is_fraud`.
14. **Left out:** deep learning, text models, a paid LLM, outlet-to-customer network analysis. Reason: 141 labelled frauds is too few, and the service must run free and offline.
15. **Form wording.** The form mentions "Vireo, roughly 650 tickets a week". The pack is about Kestrel (about 750 claims a month). I answer for Kestrel and note this.
