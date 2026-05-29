#!/usr/bin/env python3
"""
OCR Text Verification Tool
生成した PNG に対して OCR を実行し、JSON spec に記載されたテキストが
正しくレンダリングされているかを確認する。

Usage:
    python tools/ocr_check.py --image out/xxx.png --spec examples/xxx.json
    python tools/ocr_check.py --image out/xxx.png --expect "START"
"""

import argparse
import json
import sys
from pathlib import Path


def extract_expected_texts(spec_path: Path) -> list[str]:
    """JSON spec からテキストレイヤーの value を全て収集する。"""
    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)
    texts = []
    for layer in spec.get("layers", []):
        text_obj = layer.get("text")
        if text_obj and "value" in text_obj:
            texts.append(text_obj["value"])
    return texts


def run_ocr(image_path: Path) -> list[str]:
    """easyocr で画像からテキストを抽出する。"""
    import easyocr  # 初回はモデルのダウンロードが走る

    reader = easyocr.Reader(["en"], verbose=False)
    results = reader.readtext(str(image_path), detail=0)
    return [r.strip() for r in results if r.strip()]


def normalize(text: str) -> str:
    return text.upper().replace(" ", "")


def check_texts(detected: list[str], expected: list[str]) -> list[dict]:
    results = []
    for exp in expected:
        exp_norm = normalize(exp)
        matched = any(exp_norm in normalize(d) for d in detected)
        results.append({
            "expected": exp,
            "matched": matched,
            "detected_candidates": detected,
        })
    return results


def print_report(checks: list[dict], image_path: Path) -> None:
    print(f"\n{'='*60}")
    print(f"OCR Check Report: {image_path.name}")
    print(f"{'='*60}")
    all_pass = True
    for c in checks:
        icon = "✅" if c["matched"] else "❌"
        print(f"  {icon} Expected: \"{c['expected']}\"")
        if not c["matched"]:
            all_pass = False
            cands = ", ".join(f'"{x}"' for x in c["detected_candidates"]) or "(nothing)"
            print(f"     OCR detected: {cands}")
    print(f"\n{'='*60}")
    verdict = "PASS" if all_pass else "FAIL"
    icon = "✅" if all_pass else "❌"
    print(f"{icon} OCR Verdict: {verdict}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="OCR Text Verification")
    parser.add_argument("--image", required=True, help="Path to PNG image")
    parser.add_argument("--spec", help="Path to JSON spec file")
    parser.add_argument("--expect", help="Comma-separated expected text values")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"ERROR: Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    if args.spec:
        expected = extract_expected_texts(Path(args.spec))
    elif args.expect:
        expected = [t.strip() for t in args.expect.split(",")]
    else:
        print("ERROR: --spec または --expect が必要です", file=sys.stderr)
        sys.exit(1)

    if not expected:
        print("ERROR: spec にテキストレイヤーが見つかりません", file=sys.stderr)
        sys.exit(1)

    print(f"OCR 実行中: {image_path} ...", file=sys.stderr)
    detected = run_ocr(image_path)
    print(f"検出テキスト: {detected}", file=sys.stderr)

    checks = check_texts(detected, expected)
    print_report(checks, image_path)

    all_pass = all(c["matched"] for c in checks)
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
