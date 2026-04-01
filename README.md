# AI for Youth MH

A reproducible evaluation workspace for youth mental well-being assistant behavior.

This project includes:
- a frozen system prompt,
- a curated scenario suite,
- runner scripts to produce model outputs,
- and scripts to build scoring CSVs from logs.

## Project Layout

- `prompts/system_prompt_v1.0.txt`: Frozen assistant instruction set.
- `scenarios/scenarios.csv`: Evaluation scenarios and metadata fields.
- `scenarios/scenario_metadata.csv`: Additional scenario metadata.
- `tests/run_template.py`: Local stub runner template.
- `tests/run_groq.py`: Groq API runner (OpenAI-compatible endpoint).
- `tests/prepare_evaluation_csv.py`: Builds rubric CSV artifacts from logs.
- `logs/run_logs.jsonl`: Appended run outputs.
- `rubric/evaluation_template_full40.csv`: Blank 40-scenario scoring template.
- `rubric/evaluation_runs_from_logs.csv`: Log-derived evaluation rows.

## Prerequisites

- Python 3.13+
- Local virtual environment at `.venv`
- A Groq API key for `run_groq.py`

## Quick Setup (PowerShell)

```powershell
Set-Location .\AI_for_Youth_MH
.\.venv\Scripts\Activate.ps1
```

## Run with Groq

```powershell
Set-Location .\AI_for_Youth_MH
.\.venv\Scripts\python.exe .\tests\run_groq.py --model llama-3.1-70b-versatile --repetitions 1
```

Optional stronger retry profile:

```powershell
Set-Location .\AI_for_Youth_MH
.\.venv\Scripts\python.exe .\tests\run_groq.py --model llama-3.1-70b-versatile --repetitions 1 --sleep 1.8 --max-retries 8 --backoff-base 2.0 --backoff-cap 30
```

## Run the Local Template

```powershell
Set-Location .\AI_for_Youth_MH
.\.venv\Scripts\python.exe .\tests\run_template.py
```

## Build Evaluation CSVs

```powershell
Set-Location .\AI_for_Youth_MH
.\.venv\Scripts\python.exe .\tests\prepare_evaluation_csv.py
```

This writes or updates:
- `rubric/evaluation_template_full40.csv`
- `rubric/evaluation_runs_from_logs.csv`

## Safety Check Behavior in Runners

Current runner behavior includes a lightweight keyword/rule-based crisis detector.

- If a scenario is flagged in `tests/run_groq.py`, the script skips the external API call and writes a supportive fallback response.
- Safety metadata is logged per row with `safety_flag` and `safety_matches` in `logs/run_logs.jsonl`.

This is a simple guardrail and should not be treated as a complete moderation system.

## Notes

- Keep the system prompt version fixed during a benchmark run to preserve comparability.
- Treat generated logs as experimental artifacts and avoid committing sensitive local data.

## Disclaimer

This project is for research and evaluation purposes only.
It is not a mental health service.
