"""Lightweight lint for ui-templates catalog consistency."""
from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "ui-templates" / "_catalog" / "index.yaml"

ROLE_RE = re.compile(r"^role:\s*([A-Za-z0-9_:-]+)\s*$")


def parse_index(text: str) -> list[dict[str, str | list[str]]]:
    entries: list[dict[str, str | list[str]]] = []
    current: dict[str, str | list[str]] = {}

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- id:"):
            if current:
                entries.append(current)
            current = {"id": stripped.split(":", 1)[1].strip().strip('"')}
        elif stripped.startswith("path:"):
            current["path"] = stripped.split(":", 1)[1].strip().strip('"')
        elif stripped.startswith("tags:"):
            tags_text = stripped.split(":", 1)[1].strip()
            tags: list[str] = []
            if tags_text.startswith("[") and tags_text.endswith("]"):
                inner = tags_text[1:-1].strip()
                if inner:
                    tags = [tag.strip() for tag in inner.split(",") if tag.strip()]
            current["tags"] = tags

    if current:
        entries.append(current)

    return entries


def read_role(path: Path) -> str | None:
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        match = ROLE_RE.match(line.strip())
        if match:
            return match.group(1)
    return None


def main() -> int:
    if not INDEX_PATH.exists():
        print("WARN: index.yaml not found")
        return 0

    entries = parse_index(INDEX_PATH.read_text(encoding="utf-8"))
    warnings: list[str] = []

    for entry in entries:
        path_text = entry.get("path")
        if not isinstance(path_text, str):
            continue
        tags = entry.get("tags")
        tag_list = tags if isinstance(tags, list) else []
        template_path = (ROOT / path_text).resolve()
        role = read_role(template_path)

        if "decoration" in tag_list and role != "decoration":
            warnings.append(
                f"decoration tag requires role=decoration: {path_text} (role={role})"
            )

    if warnings:
        print("Template lint warnings:")
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("Template lint OK")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
