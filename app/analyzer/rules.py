"""Load declarative rule metadata from the top-level ``rules/`` directory.

Detection logic lives in :mod:`app.analyzer.detectors`; the human-readable
metadata (name, severity, remediation, references) is kept in ``rules/*.yml``
so the two can be reviewed separately.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

# repo_root/rules  (this file is at repo_root/app/analyzer/rules.py)
_DEFAULT_RULES_DIR = Path(__file__).resolve().parents[2] / "rules"


@dataclass
class RuleMeta:
    id: str
    name: str
    severity: str
    autofixable: bool = False
    description: str = ""
    remediation: str = ""
    references: list[str] = field(default_factory=list)


def load_rules(rules_dir: Path | str | None = None) -> dict[str, RuleMeta]:
    """Read every ``*.yml`` rule definition and return them keyed by id."""
    directory = Path(rules_dir) if rules_dir is not None else _DEFAULT_RULES_DIR
    rules: dict[str, RuleMeta] = {}
    for path in sorted(directory.glob("*.yml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        rule_id = data.get("id")
        if not rule_id:
            continue
        rules[rule_id] = RuleMeta(
            id=rule_id,
            name=data.get("name", rule_id),
            severity=data.get("severity", "medium"),
            autofixable=bool(data.get("autofixable", False)),
            description=str(data.get("description", "")).strip(),
            remediation=str(data.get("remediation", "")).strip(),
            references=list(data.get("references", []) or []),
        )
    return rules
