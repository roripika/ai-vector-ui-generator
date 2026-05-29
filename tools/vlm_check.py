#!/usr/bin/env python3
"""
VLM Visual Check Tool
Ollama 上のビジョンモデルを使って生成した UI 画像をチェックする。

Usage:
    python tools/vlm_check.py --image out/ui_title_primary_button_001/ui_title_primary_button_001.png
    python tools/vlm_check.py --image out/xxx.png --host http://gx10-5cfb.tailba17ab.ts.net:11434 --model qwen3-vl:30b
"""

import argparse
import base64
import json
import sys
from pathlib import Path

import requests


DEFAULT_HOST = "http://gx10-5cfb.tailba17ab.ts.net:11434"
DEFAULT_MODEL = "qwen3-vl:30b"

CHECK_PROMPT = """You are a strict UI quality inspector. Analyze this UI image and answer each question with PASS, FAIL, or SKIP(intentional).

If FAIL or SKIP, briefly explain why (1 line max).

--- TEXT PLACEMENT ---
T-01: Is the TOP edge of any text element clipped or cut off?  (Expected: NO → PASS if not clipped)
T-02: Is the BOTTOM edge of any text element clipped or cut off?  (Expected: NO → PASS if not clipped)
T-03: Is the LEFT edge of any text element clipped or cut off?  (Expected: NO → PASS if not clipped)
T-04: Is the RIGHT edge of any text element clipped or cut off?  (Expected: NO → PASS if not clipped)
T-05: Is the text located INSIDE the button/component boundary?  (Expected: YES → PASS)

--- READABILITY ---
V-01: Is the contrast between text and background sufficient to read clearly?  (Expected: YES → PASS)
V-02: Is the text buried under or blended into another layer (e.g. highlight gradient)?  (Expected: NO → PASS)
V-03: Are the text characters clearly identifiable at the current font size?  (Expected: YES → PASS)

--- LAYOUT ---
L-01: Does any element extend OUTSIDE the canvas/viewBox boundary?  (Expected: NO → PASS)
L-02: Are there unexpected large blank or transparent areas?  (Expected: NO → PASS)
L-03: Does the overall layout match a typical game UI button purpose?  (Expected: YES → PASS)

--- PURPOSE FIT ---
U-01: Does this button visually stand out enough to be a PRIMARY action button?  (Expected: YES → PASS)
U-02: Is the text bold/large enough that it would remain identifiable even if the button is displayed at half its current rendered size?  (Expected: YES → PASS)

Respond in this exact format (JSON only, no markdown):
{
  "checks": {
    "T-01": {"result": "PASS|FAIL|SKIP", "note": "..."},
    "T-02": {"result": "PASS|FAIL|SKIP", "note": "..."},
    "T-03": {"result": "PASS|FAIL|SKIP", "note": "..."},
    "T-04": {"result": "PASS|FAIL|SKIP", "note": "..."},
    "T-05": {"result": "PASS|FAIL|SKIP", "note": "..."},
    "V-01": {"result": "PASS|FAIL|SKIP", "note": "..."},
    "V-02": {"result": "PASS|FAIL|SKIP", "note": "..."},
    "V-03": {"result": "PASS|FAIL|SKIP", "note": "..."},
    "L-01": {"result": "PASS|FAIL|SKIP", "note": "..."},
    "L-02": {"result": "PASS|FAIL|SKIP", "note": "..."},
    "L-03": {"result": "PASS|FAIL|SKIP", "note": "..."},
    "U-01": {"result": "PASS|FAIL|SKIP", "note": "..."},
    "U-02": {"result": "PASS|FAIL|SKIP", "note": "..."}
  },
  "verdict": "PASS|REWORK|STOP",
  "fail_items": ["T-01", ...],
  "summary": "one sentence overall assessment"
}
"""


def encode_image(image_path: Path) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def run_check(image_path: Path, host: str, model: str) -> dict:
    image_b64 = encode_image(image_path)

    payload = {
        "model": model,
        "prompt": CHECK_PROMPT,
        "images": [image_b64],
        "stream": False,
        "options": {"temperature": 0.0},
    }

    resp = requests.post(f"{host}/api/generate", json=payload, timeout=120)
    resp.raise_for_status()

    raw = resp.json()["response"].strip()

    # JSON 部分だけ抽出（モデルが余分なテキストを返す場合があるため）
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"JSON not found in response:\n{raw}")

    return json.loads(raw[start:end])


def print_report(result: dict, image_path: Path) -> None:
    checks = result.get("checks", {})
    verdict = result.get("verdict", "UNKNOWN")
    fail_items = result.get("fail_items", [])
    summary = result.get("summary", "")

    print(f"\n{'='*60}")
    print(f"VLM Check Report: {image_path.name}")
    print(f"{'='*60}")

    sections = {
        "TEXT PLACEMENT": ["T-01", "T-02", "T-03", "T-04", "T-05"],
        "READABILITY":    ["V-01", "V-02", "V-03"],
        "LAYOUT":         ["L-01", "L-02", "L-03"],
        "PURPOSE FIT":    ["U-01", "U-02"],
    }

    for section, keys in sections.items():
        print(f"\n[{section}]")
        for k in keys:
            item = checks.get(k, {})
            r = item.get("result", "?")
            note = item.get("note", "")
            icon = "✅" if r == "PASS" else ("⚠️" if r == "SKIP" else "❌")
            note_str = f"  → {note}" if note else ""
            print(f"  {icon} {k}: {r}{note_str}")

    print(f"\n{'='*60}")
    verdict_icon = "✅" if verdict == "PASS" else ("❌" if verdict == "REWORK" else "🛑")
    print(f"{verdict_icon} Final Verdict: {verdict}")
    if fail_items:
        print(f"   FAIL items: {', '.join(fail_items)}")
    if summary:
        print(f"   Summary: {summary}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="VLM Visual Check Tool")
    parser.add_argument("--image", required=True, help="Path to PNG image")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Ollama host URL")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model name")
    parser.add_argument("--json", action="store_true", help="Output raw JSON only")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"ERROR: Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Checking: {image_path} with {args.model} @ {args.host} ...", file=sys.stderr)

    result = run_check(image_path, args.host, args.model)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_report(result, image_path)

    # REWORK / STOP のときは exit code 1
    verdict = result.get("verdict", "STOP")
    sys.exit(0 if verdict == "PASS" else 1)


if __name__ == "__main__":
    main()
