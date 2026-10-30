# Validation report

Validation performed locally on 30 October 2026.

- Dataset rows: 2,018 raw; 2,017 resolved outcomes retained after status normalisation; 1 unresolved/in-transit row excluded.
- Resolved outcomes: 1,444 delivered and 573 RTO (28.41%).
- RTO cost assumption: ₹169.40 per RTO.
- Automated tests: 14 passed.
- Chronological scoring: verified sorted evaluation and a regression test showing the first order's own outcome does not affect its risk score.
- Pincode validation: six digits, first digit 1–9; shared by decision engine and address review.
- Founder memo: regenerated from the current dataset and policy; 2 pages.

## Not validated

- Live LLM request and address interpretation accuracy.
- Real WhatsApp delivery, consent/template approval, payment link or payment webhook.
- Causal reduction in RTO, actual prepaid conversion, or actual net profit uplift.
- Model calibration/generalisation on a separate future-period holdout.

The risk score remains a transparent heuristic. The dashboard's financial output is scenario analysis based on editable assumptions, not a claim of realised savings.
