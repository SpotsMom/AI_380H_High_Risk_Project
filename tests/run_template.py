#!/usr/bin/env python3
"""
Run template for Youth MH LLM Evaluation (no network calls included).
- Loads scenarios and system prompt
- Demonstrates payload formation and logging
- You must plug in your actual model call (e.g., Hugging Face Inference API)
"""
import csv, json, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPT_FILE = ROOT / 'prompts' / 'system_prompt_v1.0.txt'
SCENARIOS_FILE = ROOT / 'scenarios' / 'scenarios.csv'
LOGS_FILE = ROOT / 'logs' / 'run_logs.jsonl'

PARAMS = {"temperature": 0.3, "top_p": 0.9, "max_tokens": 280}
CRISIS_KEYWORDS = {
    "kill myself",
    "end my life",
    "suicide",
    "want to die",
    "self harm",
    "self-harm",
    "hurt myself",
    "cut myself",
    "overdose",
    "kill him",
    "kill her",
    "kill them",
    "hurt someone",
    "abuse",
    "molest",
}


def load_text(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def iter_scenarios(path: Path):
    with path.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


def format_messages(system_prompt: str, user_text: str):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text},
    ]


def detect_crisis(text: str):
    lowered = f" {text.lower()} "
    matches = sorted({keyword for keyword in CRISIS_KEYWORDS if f" {keyword} " in lowered})
    return bool(matches), matches


def safe_crisis_response(matches):
    matched_text = ", ".join(matches) if matches else "a possible safety concern"
    return (
        "I'm really sorry you're dealing with this. I want to take this seriously. "
        "If there is any immediate danger or you might act on these thoughts, please call emergency services right now or reach out to a trusted adult, parent, school counselor, or another person who can stay with you. "
        "If you can, take one slow breath in and out and move to a safer place while you get support. "
        f"I noticed wording that may indicate {matched_text}."
    )


def call_model_stub(messages, model_name: str):
    """Placeholder for your real model call.
    Replace this with your API logic (e.g., Hugging Face Inference).
    Return a dict with a 'text' field.
    """
    return {"text": "[stubbed] This is where the model response would appear."}


def log_result(record: dict, path: Path):
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    system_prompt = load_text(PROMPT_FILE)
    model_name = 'meta-llama/Meta-Llama-3-70B-Instruct'  # example

    for s in iter_scenarios(SCENARIOS_FILE):
        crisis_detected, crisis_matches = detect_crisis(s['scenario_text'])
        messages = format_messages(system_prompt, s['scenario_text'])
        response = call_model_stub(messages, model_name)
        if crisis_detected:
            response = {"text": safe_crisis_response(crisis_matches)}
        record = {
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'model': model_name,
            'model_version': '',
            'scenario_id': s['scenario_id'],
            'scenario_text': s['scenario_text'],
            'system_prompt_version': '1.0',
            'assistant_response': response['text'],
            'parameters': PARAMS,
            'safety_flag': 'crisis' if crisis_detected else '',
            'safety_matches': crisis_matches,
        }
        log_result(record, LOGS_FILE)

    print('Run completed. Results appended to logs/run_logs.jsonl')


if __name__ == '__main__':
    main()
