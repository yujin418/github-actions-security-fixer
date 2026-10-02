"""Tests for the week-3 detection rules.

Run from the repository root:  python -m pytest
"""

from __future__ import annotations

from pathlib import Path

from app.analyzer import analyze_file, analyze_text

REPO_ROOT = Path(__file__).resolve().parents[1]
VULN = REPO_ROOT / "tests" / "workflows" / "vulnerable"
SAFE = REPO_ROOT / "tests" / "workflows" / "safe"


def _rule_ids(findings) -> set[str]:
    return {f.rule_id for f in findings}


# --- vulnerable examples are detected ---------------------------------------

def test_script_injection_detected():
    findings = analyze_file(VULN / "script-injection.yml")
    assert "script-injection" in _rule_ids(findings)
    hit = next(f for f in findings if f.rule_id == "script-injection")
    assert hit.severity == "high"
    assert hit.line > 0
    assert "github.event.issue.title" in hit.evidence.replace(" ", "")


def test_excessive_permissions_detected():
    findings = analyze_file(VULN / "excessive-permissions.yml")
    assert "excessive-permissions" in _rule_ids(findings)
    hit = next(f for f in findings if f.rule_id == "excessive-permissions")
    assert "write-all" in hit.evidence


def test_unpinned_actions_detected():
    findings = analyze_file(VULN / "unpinned-actions.yml")
    unpinned = [f for f in findings if f.rule_id == "unpinned-actions"]
    # both the tag ref and the branch ref should be reported, on distinct lines
    assert len(unpinned) == 2
    assert len({f.line for f in unpinned}) == 2


# --- safe examples produce no findings --------------------------------------

def test_safe_script_injection_clean():
    findings = analyze_file(SAFE / "script-injection.yml")
    assert findings == []


def test_safe_least_privilege_clean():
    findings = analyze_file(SAFE / "least-privilege.yml")
    assert findings == []


# --- behavioral details -----------------------------------------------------

def test_sha_pinned_action_is_not_flagged():
    text = """
name: t
on: [push]
permissions:
  contents: read
jobs:
  j:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
"""
    assert analyze_text(text) == []


def test_local_action_is_not_flagged():
    text = """
name: t
on: [push]
permissions:
  contents: read
jobs:
  j:
    runs-on: ubuntu-latest
    steps:
      - uses: ./.github/actions/local
"""
    assert analyze_text(text) == []


def test_missing_permissions_is_low_severity():
    text = """
name: t
on: [push]
jobs:
  j:
    runs-on: ubuntu-latest
    steps:
      - run: echo hi
"""
    findings = analyze_text(text)
    perms = [f for f in findings if f.rule_id == "excessive-permissions"]
    assert len(perms) == 1
    assert perms[0].severity == "low"


def test_trusted_context_in_run_is_not_injection():
    text = """
name: t
on: [push]
permissions:
  contents: read
jobs:
  j:
    runs-on: ubuntu-latest
    steps:
      - run: echo "${{ github.sha }}"
"""
    findings = analyze_text(text)
    assert all(f.rule_id != "script-injection" for f in findings)


def test_invalid_yaml_returns_empty():
    assert analyze_text("::: not valid yaml :::\n  - [") == []
