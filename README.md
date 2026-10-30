# COD Decision Studio — Associate Software Engineer Take-Home

A local, explainable COD order triage demo with a chronological historical replay, editable policy thresholds, an offline WhatsApp conversation simulator, and a founder dashboard.

## Run locally (Python 3.10+)

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit. Run the analysis and tests from the project folder:

```bash
python analysis.py
python make_memo.py
python -m unittest discover -v
```

`Founder_Memo.pdf` is included and can be regenerated with `python make_memo.py`.

## What is included

- **Decision engine (`engine.py`)**: four actions — Ship as-is, Ship after confirmation, Nudge to prepaid, and Hold / cancel. Each decision includes a plain-English reason and estimated risk.
- **Leakage-safe replay**: historical orders are sorted chronologically. Each order is scored only with outcomes from earlier resolved orders. A 28% cold-start prior comes from the assignment's approximate business baseline. Cohort rates are smoothed toward the prior. This is a transparent heuristic, not a trained or validated predictive model.
- **Editable thresholds (`config.json`)**: ship, confirmation, prepaid-nudge and hold thresholds; no Python edits required. Sidebar changes are session-only; edit JSON to persist defaults.
- **Address checks (`address_review.py`)**: deterministic fake-name, six-digit pincode (first digit 1–9), and incomplete-address flags. LLMs are not used for arithmetic, thresholds, or cancellation decisions.
- **Optional LLM adapter (`llm_review.py`)**: when explicitly invoked with `OPENAI_API_KEY`, it may interpret ambiguous Indian/Hinglish address text and returns advisory structured output. No API call is made by default. It is unbenchmarked and must never make the dispatch decision. Do not send real customer personal data without approval, consent and privacy safeguards.
- **WhatsApp mock (`whatsapp.py`)**: offline YES/NO, PAY/COD, unclear reply, reminder and 24-hour timeout paths. It sends no real message and verifies no payment. A customer saying “paid” is not proof of payment.
- **Founder dashboard (`app.py`)**: four decision buckets, historical outcomes, estimated RTO costs avoided, genuine contribution at risk under a cancellation scenario, incremental delivered contribution and net scenario value.
- **Business memo, decision log and AI usage log**: included as standalone files.

## Financial model and limitations

The assignment's estimated cost per RTO is:

`₹65 forward + ₹65 return + ₹25 packaging/handling + (8% × ₹180 damage cost) = ₹169.40`.

A delivered order's gross contribution is estimated as `order value × 62%`. `finance.py` compares the policy scenario with shipping every order as COD:

`Net = avoided RTO costs + incremental delivered contribution − genuine contribution at risk from assumed cancellations − prepaid discounts`.

The model applies the configured confirmation success and prepaid conversion assumptions only to the relevant share of orders. Non-responders remain at baseline risk and are sent to manual review after 24 hours. Held orders are assumed cancelled only to show the downside; the real operating recommendation is human review, not automatic cancellation. Gateway fees, messaging costs, staff review costs and tax effects are excluded.

The dataset contains no observed WhatsApp response outcomes or prepaid experiment. Therefore confirmation success, prepaid conversion and post-intervention RTO rates are scenario assumptions, not measured effects. Dashboard rupee figures are estimates, not achieved savings or causal impact. The heuristic risk score is not a calibrated probability and must be evaluated on a larger, later time period before production use.

## LLM boundary

Use an LLM only for ambiguous language interpretation, such as whether a Hinglish address appears to contain a usable landmark. Use ordinary Python for name/pincode format checks, cohort maths, thresholds, financial calculations and state transitions. The LLM output is advisory; deterministic checks and a human reviewer retain control. The optional integration has not been benchmarked for accuracy.

To enable the optional live adapter in PowerShell (API usage may incur charges):

```powershell
$env:OPENAI_API_KEY="YOUR_OWN_KEY"
streamlit run app.py
```

Optional: `OPENAI_MODEL` (default `gpt-4o-mini`) and `OPENAI_API_URL` (default OpenAI-compatible chat-completions endpoint). Never commit keys or use real customer details in this demo.

## Suggested production safeguards

Obtain customer messaging consent; use approved WhatsApp templates and opt-out handling; log idempotent message events; use secure expiring payment links; release prepaid orders only after a verified payment webhook; provide a human appeal/review path; monitor false positives, segment sample sizes and drift; run a controlled holdout experiment before claiming savings.
