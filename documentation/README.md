# Youth Mental Health Evaluation Bundle

This bundle contains a frozen system prompt, 40-scenario robustness suite, evaluation rubric, methods, and scripts.

## Contents
- prompts/system_prompt_v1.0.txt
- scenarios/scenarios.csv
- scenarios/scenario_metadata.csv
- tests/test_suite.yaml
- tests/run_template.py
- logs/run_logs.jsonl (template)
- rubric/evaluation_rubric.pdf
- documentation/Methods_section.md

## Quick Start
1. Review the frozen system prompt in `prompts/`.
2. Inspect scenarios and metadata in `scenarios/`.
3. (Optional) Edit `tests/test_suite.yaml` for subsets.
4. Wire your API into `tests/run_template.py` and run it.
5. Check `logs/run_logs.jsonl` for appended outputs.

## Rebuild Evaluation CSVs
Run this from the workspace root to regenerate the 40-scenario template and append rows from `run_logs.jsonl`:

```powershell
Set-Location .\AI_for_Youth_MH; .\.venv\Scripts\python.exe .\tests\prepare_evaluation_csv.py
```

## Recommended Run Profile (Strong Backoff)
Use this profile to reduce rate-limit failures during full 40-scenario runs:

```powershell
Set-Location .\AI_for_Youth_MH; .\.venv\Scripts\python.exe .\tests\run_groq.py --model llama-3.3-70b-versatile --repetitions 1 --sleep 1.8 --max-retries 8 --backoff-base 2.0 --backoff-cap 30
```

## Versioning
- System prompt version: 1.0
- Test suite version: 1.0
Generated: 2026-03-12 19:18 UTC
