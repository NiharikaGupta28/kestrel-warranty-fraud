# Memo: Warranty fraud flag

**To:** Ritu Deshpande, Head of D2C Operations  **Cc:** Farhan Sheikh, Meenal Joshi, Tanmay Kulkarni

## The decision
Use the model to **rank claims for the investigation desk**, not to reject claims automatically. Each month, send the top 40 for review and pay the rest as normal. Do not report accuracy to the board as the success measure.

## Why not accuracy
Only about 1 in 40 claims is fraud lately. A "model" that flags nothing would score 97% accuracy and stop no fraud. We should report instead: **how many frauds we catch in the 40 claims we can review, and the rupees stopped per claim checked.**

## The numbers (tested on recent claims the model had not seen)
- It finds about **half to six in ten of the frauds** among the claims the desk can review (11 of 22, 22 of 36, 10 of 16 in three checks).
- Per claim checked: about **Rs 415 to 460 of fraud stopped**, against **Rs 380 goodwill** lost when a genuine claim is held. After goodwill that is roughly **Rs 150 to 200 net per claim checked**.
- At 40 reviews a month: about **Rs 17,000 of fraud stopped, about Rs 6,000 to 8,000 net** each month (roughly Rs 70,000 to 1 lakh a year). Seven in ten claims it flags will still turn out genuine.
- Context: confirmed fraud since May runs about **18 claims and Rs 34,000 a month**. This is a small money problem; the number of cases has more than doubled, but each is small.

## What the data says about new partners
You were partly right. Since the 1 May change, **small claims paid without inspection, from outlets onboarded in the last year, were fraud 21% of the time. The same kind of claim from older outlets was fraud 0.1% of the time.** But the problem sits in **about 10 outlets**, not the roughly 60 new ones. Flagging every new partner would hold many honest claims (Meenal's point) and catches fewer frauds than the model.

## One thing that may matter more than the model
The May rule (auto-approve claims under Rs 2,000) is what opened the gap. Re-inspecting small claims from new outlets would cost about Rs 21,000 to 28,000 a month in contact costs, about what it would save, so it is **not an obvious win**. Reviewing a short list of outlets is cheaper.

## What to do next week
1. Agree that the desk works from the ranked list (top 40 a month) and records every outcome, including cases still open.
2. Ask Meenal's team to look at the outlets the model names most often (starting with SP3160, SP3232, SP3318, SP3129, SP3319).
3. Have Tanmay fix the legacy export so open cases are blank, not 0, and keep a clean claim number per claim.
4. Pilot for one month, then retrain with the new outcomes. Treat the numbers above as estimates; they rest on only 36 confirmed frauds since May.
