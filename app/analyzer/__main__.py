"""Command-line entry point: scan workflow files and print findings.

Usage:
    python -m app.analyzer <file-or-dir> [<file-or-dir> ...]

With no arguments it scans ``.github/workflows`` under the current directory.
Exits non-zero when any finding is reported.
"""

from __future__ import annotations

import sys
from pathlib import Path

from . import analyze_file, load_rules


def _collect(targets: list[str]) -> list[Path]:
    paths: list[Path] = []
    for target in targets:
        p = Path(target)
        if p.is_dir():
            paths.extend(sorted(p.rglob("*.yml")))
            paths.extend(sorted(p.rglob("*.yaml")))
        elif p.is_file():
            paths.append(p)
    return paths


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    targets = argv or [".github/workflows"]
    paths = _collect(targets)
    if not paths:
        print("분석할 워크플로우 파일을 찾지 못했습니다.", file=sys.stderr)
        return 2

    rules = load_rules()
    total = 0
    for path in paths:
        findings = analyze_file(path, rules=rules)
        if not findings:
            continue
        print(f"\n{path}")
        for f in findings:
            total += 1
            print(f"  [{f.severity.upper():6}] L{f.line} {f.rule_id}: {f.message}")
            print(f"           근거: {f.evidence}")

    print(f"\n총 {total}건 탐지 ({len(paths)}개 파일 검사)")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
