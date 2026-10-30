# Decision log

- **Four actions instead of a binary block:** selected Ship as-is, Ship after confirmation, Nudge to prepaid, and Hold / cancel to balance Operations loss control with Marketing's first-order conversion concern.
- **Hold means human review:** rejected blanket automatic cancellation because a high-risk segment still contains delivered orders and historical cohort rates are uncertain.
- **Use simple code for deterministic work:** Python handles pincode/name format checks, cohort counts, thresholds, state transitions and rupee calculations. These are auditable and more reliable than an LLM.
- **Limit LLM use to ambiguous language:** optional LLM adapter may interpret Hinglish address completeness. It is off by default, advisory only, unbenchmarked and never decides whether to ship or cancel.
- **Use chronological history:** corrected the evaluation so each historical order is scored only from earlier resolved orders. The order's own status and future statuses cannot influence its score. The assignment's approximate 28% RTO rate is used only as a cold-start prior until prior outcomes exist.
- **Smooth small cohorts:** cohort RTO rates are shrunk toward the baseline with 30 prior-equivalent observations to avoid extreme rates from tiny groups. This is a heuristic, not a trained model.
- **Keep thresholds outside code:** policy cut-offs live in `config.json`; sidebar edits support quick scenario exploration.
- **Conservative timeout:** no response after 24 hours goes to manual review, not silent dispatch or cancellation.
- **Payment claims are not payment proof:** a chat reply such as “paid” leaves the flow awaiting a verified payment webhook.
- **Scenario financials are explicitly labelled:** confirmation/prepaid response and post-intervention rates are assumptions because the supplied dataset has no intervention outcomes. Non-responders remain at baseline risk; held orders are treated as cancelled only for downside illustration.
- **No production integrations claimed:** WhatsApp is a local simulator; optional LLM requires a separately supplied API key; neither real messages nor payment processing occur.
