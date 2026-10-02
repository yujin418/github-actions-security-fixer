"""Detection result data model shared across the analyzer.

The ``Finding`` dataclass is the fixed format for a single detected issue;
it is what later stages (fixer, GitHub PR output) consume.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class Finding:
    """A single detected issue in a workflow file.

    Attributes:
        rule_id: Stable rule identifier (e.g. ``"unpinned-actions"``).
        rule_name: Human-readable rule name.
        severity: ``"high"``, ``"medium"`` or ``"low"``.
        file: Path of the analyzed workflow file.
        line: 1-based line number of the evidence (0 if not located).
        evidence: The raw snippet that triggered the rule.
        message: What was found and why it matters.
        remediation: How to fix it.
        autofixable: Whether an automatic fix is supported at this stage.
    """

    rule_id: str
    rule_name: str
    severity: str
    file: str
    line: int
    evidence: str
    message: str
    remediation: str
    autofixable: bool = False

    def to_dict(self) -> dict:
        return asdict(self)
