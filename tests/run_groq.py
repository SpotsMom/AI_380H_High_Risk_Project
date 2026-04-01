#!/usr/bin/env python3
"""
Run Llama‑3 70B via Groq API for the Youth MH evaluation suite.
- Reads the frozen system prompt and scenarios
- Calls Groq's Chat Completions API (OpenAI-compatible)
- Appends results to logs/run_logs.jsonl

Usage:
  GROQ_API_KEY=xxxx python run_groq.py --model llama-3.1-70b-versatile --repetitions 1

Notes:
- This script does NOT install packages and assumes only Python stdlib.
- Network calls require internet connectivity and a valid GROQ_API_KEY.
- Keep temperature, top_p, and max_tokens fixed for reproducibility.
"""

import argparse
import csv
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
from urllib import request, error

ROOT = Path(__file__).resolve().parents[1] if (Path(__file__).parent.name == 'tests') else Path.cwd()
PROMPT_FILE = ROOT / 'prompts' / 'system_prompt_v1.0.txt'
SCENARIOS_FILE = ROOT / 'scenarios' / 'scenarios.csv'
LOGS_FILE = ROOT / 'logs' / 'run_logs.jsonl'

PARAMS = {"temperature": 0.3, "top_p": 0.9, "max_tokens": 280}
GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'
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

def format_messages(system_prompt: str, user_text: str) -> List[Dict[str, str]]:
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_text}]

def detect_crisis(text: str) -> Tuple[bool, List[str]]:
    lowered = f" {text.lower()} "
    matches = sorted({keyword for keyword in CRISIS_KEYWORDS if f" {keyword} " in lowered})
    return bool(matches), matches

def safe_crisis_response(matches: List[str]) -> str:
    matched_text = ", ".join(matches) if matches else "a possible safety concern"
    return (
        "I'm really sorry you're dealing with this. I want to take this seriously. "
        "If there is any immediate danger or you might act on these thoughts, please call emergency services right now or reach out to a trusted adult, parent, school counselor, or another person who can stay with you. "
        "If you can, take one slow breath in and out and move to a safer place while you get support. "
        f"I noticed wording that may indicate {matched_text}."
    )

def call_groq(messages: List[Dict[str, str]], model: str) -> Dict[str, Any]:
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise RuntimeError('GROQ_API_KEY environment variable is not set')
    payload = {"model": model, "messages": messages, "temperature": PARAMS["temperature"],
               "top_p": PARAMS["top_p"], "max_tokens": PARAMS["max_tokens"]}
    data = json.dumps(payload).encode('utf-8')
    req = request.Request(GROQ_API_URL, data=data)
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {api_key}')
    req.add_header('User-Agent', 'python-requests/2.32.3')
    with request.urlopen(req, timeout=120) as resp:
        body = resp.read()
        return json.loads(body.decode('utf-8'))

def call_groq_with_retry(messages: List[Dict[str, str]], model: str, max_retries: int,
                         backoff_base: float, backoff_cap: float) -> Dict[str, Any]:
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return call_groq(messages, model)
        except error.HTTPError as e:
            last_error = e
            is_retryable = e.code == 429 or 500 <= e.code <= 599
            if not is_retryable or attempt == max_retries:
                raise
            sleep_for = min(backoff_cap, backoff_base * (2 ** attempt))
            # Add small jitter to avoid synchronized retries.
            sleep_for += random.uniform(0.0, min(1.0, backoff_base))
            time.sleep(sleep_for)
        except Exception as e:
            last_error = e
            if attempt == max_retries:
                raise
            sleep_for = min(backoff_cap, backoff_base * (2 ** attempt))
            sleep_for += random.uniform(0.0, min(1.0, backoff_base))
            time.sleep(sleep_for)
    if last_error:
        raise last_error
    raise RuntimeError('Unknown Groq call failure')

def extract_text(resp: Dict[str, Any]) -> str:
    try:
        return resp["choices"][0]["message"]["content"].strip()
    except Exception:
        return json.dumps(resp)

def log_result(record: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def main():
    parser = argparse.ArgumentParser(description='Run Llama‑3 70B via Groq for evaluation')
    parser.add_argument('--model', default='llama-3.1-70b-versatile', help='Groq model name')
    parser.add_argument('--repetitions', type=int, default=1, help='Runs per scenario')
    parser.add_argument('--sleep', type=float, default=0.5, help='Seconds to sleep between API calls')
    parser.add_argument('--max-retries', type=int, default=5, help='Max retries for transient API failures')
    parser.add_argument('--backoff-base', type=float, default=1.5, help='Base seconds for exponential backoff')
    parser.add_argument('--backoff-cap', type=float, default=20.0, help='Max seconds per retry wait')
    args = parser.parse_args()

    system_prompt = load_text(PROMPT_FILE)

    for s in iter_scenarios(SCENARIOS_FILE):
        for rep in range(args.repetitions):
            crisis_detected, crisis_matches = detect_crisis(s['scenario_text'])
            messages = format_messages(system_prompt, s['scenario_text'])
            try:
                if crisis_detected:
                    assistant_text = safe_crisis_response(crisis_matches)
                    status = 'flagged_crisis'
                    error = ''
                else:
                    resp = call_groq_with_retry(
                        messages,
                        args.model,
                        max_retries=args.max_retries,
                        backoff_base=args.backoff_base,
                        backoff_cap=args.backoff_cap,
                    )
                    assistant_text = extract_text(resp)
                    status = 'ok'
                    error = ''
            except Exception as e:
                assistant_text = ''
                status = 'error'; error = str(e)
            record = {
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'model': args.model,
                'model_provider': 'groq',
                'model_version': '',
                'scenario_id': s['scenario_id'],
                'scenario_text': s['scenario_text'],
                'risk_tier': s.get('risk_tier', ''),
                'category': s.get('category', ''),
                'system_prompt_version': '1.0',
                'parameters': PARAMS,
                'assistant_response': assistant_text,
                'status': status,
                'error': error,
                'repetition': rep + 1,
                'safety_flag': 'crisis' if crisis_detected else '',
                'safety_matches': crisis_matches,
            }
            log_result(record, LOGS_FILE)
            time.sleep(args.sleep)
    print(f'Completed. Results appended to {LOGS_FILE}')

if __name__ == '__main__':
    for p in (PROMPT_FILE, SCENARIOS_FILE):
        if not p.exists():
            sys.stderr.write(f"Missing required file: {p}\n"); sys.exit(1)
    main()
