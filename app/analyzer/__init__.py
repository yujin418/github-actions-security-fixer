"""Workflow analyzer: parse a workflow file and run the detection rules.

Public API:
    analyze_text(text, file) -> list[Finding]
    analyze_file(path)       -> list[Finding]
    load_rules()             -> dict[str, RuleMeta]
"""

from __future__ import annotations

from pathlib import Path

import yaml

from .detectors import DETECTORS
from .models import Finding
from .rules import RuleMeta, load_rules

__all__ = ["analyze_text", "analyze_file", "load_rules", "Finding", "RuleMeta"]


def analyze_text(
    text: str,
    file: str = "<memory>",
    rules: dict[str, RuleMeta] | None = None,
) -> list[Finding]:
    """Analyze workflow YAML given as a string.

    Invalid YAML yields an empty result rather than raising, so a single
    malformed file does not stop a batch scan.
    """
    if rules is None:
        rules = load_rules()
    try:
        workflow = yaml.safe_load(text)
    except yaml.YAMLError:
        return []
    if not isinstance(workflow, dict):
        return []

    lines = text.splitlines()
    used: set[int] = set()
    findings: list[Finding] = []
    for rule_id, detector in DETECTORS.items():
        meta = rules.get(rule_id)
        if meta is None:
            continue
        findings.extend(detector(workflow, lines, file, meta, used))

    findings.sort(key=lambda f: (f.line, f.rule_id))
    return findings


def analyze_file(
    path: str | Path,
    rules: dict[str, RuleMeta] | None = None,
) -> list[Finding]:
    """Analyze a workflow file on disk."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    return analyze_text(text, file=str(path), rules=rules)
