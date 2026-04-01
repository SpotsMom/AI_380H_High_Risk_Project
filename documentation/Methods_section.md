# Methods: Youth Mental Well-Being LLM Evaluation

**System prompt**: `prompts/system_prompt_v1.0.txt` (frozen; Version 1.0).  
**Scenario set**: 40 scenarios across adversarial, crisis (R0–R3), ambiguity, long-conversation stability, and normal youth-support.  
**Models**: Copilot (GPT-4+/GPT-5-chat) for design/stress tests; Llama-3 70B for open, reproducible evaluation.  
**Parameters**: temperature=0.3, top_p=0.9, max_new_tokens=280.

## Study Design
- Each scenario is run once on Copilot and 3× on Llama-3 70B to assess variability.  
- System prompt is identical across models.  
- Conversations are single-turn unless marked `long_convo` (multi-turn stability tests).

## Safety & Ethics
- No PII used; scenarios are synthetic.  
- Safety protocol for R2/R3 includes validation, grounding, and guidance to contact trusted adults/emergency services.  
- All outputs logged to `logs/run_logs.jsonl`.  
- Human raters assess responses using `rubric/evaluation_rubric.pdf`.

## Scoring & IRR
- Six dimensions: Empathy, Emotional Accuracy, Safety Compliance (critical), Clarity, Helpfulness, Agency.  
- Double-rate ≥20% and compute inter-rater reliability (Cohen’s κ).  
- Record critical fails and error taxonomy (missed risk, boundary violation, over-escalation).

## Analysis
- Report dimension means with 95% CIs; compare models; plot failure rates by risk tier.  
- For long-conversation tests, assess tone drift and safety-trigger reliability at specified turns.  
- Provide exemplar sanitized responses in an appendix.

## Reproducibility
- All artifacts versioned in this bundle.  
- Any prompt change triggers new version (e.g., `system_prompt_v1.1.txt`) and update to the change log.
