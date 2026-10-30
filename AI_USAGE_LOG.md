# AI usage log

## Tools and use

- **ChatGPT:** used to review the assignment requirements, inspect the project structure, identify potential data leakage and financial-accounting ambiguities, and help revise code, tests, documentation and the founder memo.
- **Local Python/pandas:** used to inspect the supplied CSV, reproduce counts, run chronological replay, calculate scenario outputs and execute automated tests.
- **Optional address LLM adapter:** an OpenAI-compatible chat-completions call exists in `llm_review.py`. It is not called by default and was not live-tested as part of this offline package. No LLM accuracy or business uplift is claimed.

## Examples of weak or incorrect AI/code assumptions caught and corrected

1. **Potential target leakage:** the earlier risk calculation could use cohort outcomes from the same time period as the order being scored. The replay was changed to sort orders by timestamp and score each row only from previously resolved rows. The order's own outcome cannot affect its score.
2. **Inconsistent pincode validation:** the engine and address-review helper previously differed on whether a pincode beginning with zero was accepted. Both now require exactly six digits with a first digit from 1 to 9.
3. **Incomplete financial comparison:** the earlier dashboard mixed estimated avoided RTO costs and cancellation downside without explicitly including incremental delivered contribution from assumed successful interventions. The revised model displays avoided RTO costs, incremental delivered contribution, contribution at risk under assumed cancellation, discounts and the net formula separately. Assumptions and excluded costs are shown.

## Verification boundary

The offline unit tests validate core logic and state transitions. They do not validate live WhatsApp delivery, real payment processing, production API reliability, LLM accuracy, causal savings or model calibration. Those require external integration tests and a controlled operational pilot.
