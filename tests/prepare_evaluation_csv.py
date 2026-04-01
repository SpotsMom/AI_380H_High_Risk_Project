#!/usr/bin/env python3
"""
Build evaluation CSV artifacts for the Youth MH suite.

What this script does:
1) Creates a full 40-scenario scoring template.
2) Appends evaluation rows from logs/run_logs.jsonl.
3) Recomputes total_score_5to25 from the 5 rubric dimensions when present.

Usage:
  python tests/prepare_evaluation_csv.py

Optional paths:
  python tests/prepare_evaluation_csv.py \
    --scenarios AI_for_Youth_MH/scenarios/scenarios.csv \
    --logs AI_for_Youth_MH/logs/run_logs.jsonl \
    --template-out AI_for_Youth_MH/rubric/evaluation_template_full40.csv \
    --evaluation-out AI_for_Youth_MH/rubric/evaluation_runs_from_logs.csv
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


TEMPLATE_COLUMNS = [
    "run_id",
    "date_utc",
    "model_id",
    "provider",
    "temperature",
    "max_new_tokens",
    "system_prompt_version",
    "scenario_id",
    "scenario_label",
    "scenario_text",
    "category",
    "risk_tier",
    "repetition",
    "response_text",
    "empathy_score_1to5",
    "helpfulness_score_1to5",
    "safety_score_1to5",
    "clarity_score_1to5",
    "boundaries_score_1to5",
    "total_score_5to25",
    "status",
    "error",
    "evaluator_id",
    "notes",
]

SCORE_COLUMNS = [
    "empathy_score_1to5",
    "helpfulness_score_1to5",
    "safety_score_1to5",
    "clarity_score_1to5",
    "boundaries_score_1to5",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare evaluation CSV files")
    parser.add_argument(
        "--scenarios",
        default="AI_for_Youth_MH/scenarios/scenarios.csv",
        help="Path to scenarios CSV",
    )
    parser.add_argument(
        "--logs",
        default="AI_for_Youth_MH/logs/run_logs.jsonl",
        help="Path to run logs JSONL",
    )
    parser.add_argument(
        "--template-out",
        default="AI_for_Youth_MH/rubric/evaluation_template_full40.csv",
        help="Output path for the full scenario template CSV",
    )
    parser.add_argument(
        "--evaluation-out",
        default="AI_for_Youth_MH/rubric/evaluation_runs_from_logs.csv",
        help="Output path for evaluation rows built from log entries",
    )
    return parser.parse_args()


def to_root(path_str: str) -> Path:
    # Script is in AI_for_Youth_MH/tests. Move to workspace root for relative defaults.
    root = Path(__file__).resolve().parents[2]
    path = Path(path_str)
    return path if path.is_absolute() else root / path


def safe_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        number = int(float(text))
    except ValueError:
        return None
    return number


def compute_total(row: Dict[str, Any]) -> str:
    values: List[int] = []
    for key in SCORE_COLUMNS:
        parsed = safe_int(row.get(key, ""))
        if parsed is None:
            return ""
        if parsed < 1 or parsed > 5:
            return ""
        values.append(parsed)
    return str(sum(values))


def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    normalized = {col: row.get(col, "") for col in TEMPLATE_COLUMNS}
    normalized["total_score_5to25"] = compute_total(normalized)
    return normalized


def read_scenarios(path: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            rows.append(row)
    return rows


def write_template(scenarios: List[Dict[str, str]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=TEMPLATE_COLUMNS)
        writer.writeheader()
        for idx, scenario in enumerate(scenarios, start=1):
            row = {
                "run_id": str(idx),
                "date_utc": "",
                "model_id": "",
                "provider": "",
                "temperature": "",
                "max_new_tokens": "",
                "system_prompt_version": "",
                "scenario_id": scenario.get("scenario_id", ""),
                "scenario_label": f"Scenario {scenario.get('scenario_id', '').strip()}",
                "scenario_text": scenario.get("scenario_text", ""),
                "category": scenario.get("category", ""),
                "risk_tier": scenario.get("risk_tier", ""),
                "repetition": "",
                "response_text": "",
                "empathy_score_1to5": "",
                "helpfulness_score_1to5": "",
                "safety_score_1to5": "",
                "clarity_score_1to5": "",
                "boundaries_score_1to5": "",
                "total_score_5to25": "",
                "status": "",
                "error": "",
                "evaluator_id": "",
                "notes": "",
            }
            writer.writerow(normalize_row(row))


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    if not path.exists():
        return records

    with path.open("r", encoding="utf-8") as file:
        for line_no, line in enumerate(file, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                records.append(json.loads(text))
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON at line {line_no} in {path}")
    return records


def read_existing_rows(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        return [dict(row) for row in reader]


def row_key(row: Dict[str, Any]) -> str:
    return "|".join(
        [
            str(row.get("date_utc", "")),
            str(row.get("model_id", "")),
            str(row.get("scenario_id", "")),
            str(row.get("repetition", "")),
            str(row.get("response_text", "")),
        ]
    )


def log_to_row(record: Dict[str, Any], run_id: int) -> Dict[str, Any]:
    params = record.get("parameters") or {}
    return normalize_row(
        {
            "run_id": str(run_id),
            "date_utc": record.get("timestamp", ""),
            "model_id": record.get("model", ""),
            "provider": record.get("model_provider", ""),
            "temperature": str(params.get("temperature", "")),
            "max_new_tokens": str(params.get("max_tokens", "")),
            "system_prompt_version": record.get("system_prompt_version", ""),
            "scenario_id": str(record.get("scenario_id", "")),
            "scenario_label": f"Scenario {record.get('scenario_id', '')}",
            "scenario_text": record.get("scenario_text", ""),
            "category": record.get("category", ""),
            "risk_tier": record.get("risk_tier", ""),
            "repetition": str(record.get("repetition", "")),
            "response_text": record.get("assistant_response", ""),
            "empathy_score_1to5": "",
            "helpfulness_score_1to5": "",
            "safety_score_1to5": "",
            "clarity_score_1to5": "",
            "boundaries_score_1to5": "",
            "total_score_5to25": "",
            "status": record.get("status", ""),
            "error": record.get("error", ""),
            "evaluator_id": "",
            "notes": "",
        }
    )


def append_from_logs(logs: List[Dict[str, Any]], out_path: Path) -> int:
    existing_rows = [normalize_row(r) for r in read_existing_rows(out_path)]
    seen = {row_key(r) for r in existing_rows}

    next_run_id = 1
    if existing_rows:
        run_ids = [safe_int(r.get("run_id", "")) for r in existing_rows]
        valid_ids = [r for r in run_ids if r is not None]
        if valid_ids:
            next_run_id = max(valid_ids) + 1

    appended = 0
    for record in logs:
        new_row = log_to_row(record, next_run_id)
        key = row_key(new_row)
        if key in seen:
            continue
        existing_rows.append(new_row)
        seen.add(key)
        next_run_id += 1
        appended += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=TEMPLATE_COLUMNS)
        writer.writeheader()
        for row in existing_rows:
            writer.writerow(normalize_row(row))

    return appended


def main() -> None:
    args = parse_args()

    scenarios_path = to_root(args.scenarios)
    logs_path = to_root(args.logs)
    template_out_path = to_root(args.template_out)
    evaluation_out_path = to_root(args.evaluation_out)

    if not scenarios_path.exists():
        raise FileNotFoundError(f"Missing scenarios file: {scenarios_path}")

    scenarios = read_scenarios(scenarios_path)
    write_template(scenarios, template_out_path)

    log_records = load_jsonl(logs_path)
    appended = append_from_logs(log_records, evaluation_out_path)

    print(f"Wrote template: {template_out_path}")
    print(f"Appended {appended} rows from logs to: {evaluation_out_path}")


if __name__ == "__main__":
    main()
