"""Detection logic for the three initial rule types.

Each detector receives the parsed workflow (a dict from ``yaml.safe_load``),
the original source split into lines (for line-number lookup), the file path
and the loaded rule metadata, and returns a list of :class:`Finding`.
"""

from __future__ import annotations

import re

from .models import Finding
from .rules import RuleMeta

# --- Script injection: contexts an attacker can influence -------------------
# See the GitHub security-hardening guide. Matched against the normalized
# (whitespace-stripped) text inside a ${{ ... }} expression.
_UNTRUSTED_PATTERNS = [
    r"github\.event\.issue\.title",
    r"github\.event\.issue\.body",
    r"github\.event\.pull_request\.title",
    r"github\.event\.pull_request\.body",
    r"github\.event\.pull_request\.head\.ref",
    r"github\.event\.pull_request\.head\.label",
    r"github\.event\.pull_request\.head\.repo\.default_branch",
    r"github\.event\.comment\.body",
    r"github\.event\.review\.body",
    r"github\.event\.review_comment\.body",
    r"github\.event\.discussion\.title",
    r"github\.event\.discussion\.body",
    r"github\.event\.pages[\.\[]\d+[\]]?\.page_name",
    r"github\.event\.commits[\.\[]\d+[\]]?\.message",
    r"github\.event\.commits[\.\[]\d+[\]]?\.author\.(?:name|email)",
    r"github\.event\.head_commit\.message",
    r"github\.event\.head_commit\.author\.(?:name|email)",
    r"github\.head_ref",
]
_UNTRUSTED_RE = re.compile("|".join(_UNTRUSTED_PATTERNS))
_EXPR_RE = re.compile(r"\$\{\{(.*?)\}\}", re.DOTALL)
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _code_part(raw: str) -> str:
    """Return the line with a trailing ``# ...`` comment removed.

    Full-line comments become empty so they are never matched. A ``#`` that
    begins a comment is preceded by whitespace (or starts the line) in YAML.
    """
    if raw.lstrip().startswith("#"):
        return ""
    idx = raw.find(" #")
    return raw[:idx] if idx != -1 else raw


def _locate(lines: list[str], needle: str, used: set[int]) -> int:
    """Return the 1-based line number of ``needle``, skipping claimed lines.

    Comments are ignored so a snippet mentioned in a comment is not mistaken
    for the real occurrence. Claiming lines lets repeated identical snippets
    (e.g. the same action referenced twice) map to distinct lines. Returns 0
    when not found.
    """
    if not needle:
        return 0
    for idx, raw in enumerate(lines):
        line_no = idx + 1
        if line_no in used:
            continue
        if needle in _code_part(raw):
            used.add(line_no)
            return line_no
    return 0


def _iter_jobs(workflow: dict):
    jobs = workflow.get("jobs")
    if not isinstance(jobs, dict):
        return
    for name, job in jobs.items():
        if isinstance(job, dict):
            yield name, job


def _iter_steps(job: dict):
    steps = job.get("steps")
    if not isinstance(steps, list):
        return
    for step in steps:
        if isinstance(step, dict):
            yield step


def detect_script_injection(
    workflow: dict, lines: list[str], file: str, meta: RuleMeta, used: set[int]
) -> list[Finding]:
    findings: list[Finding] = []
    for _name, job in _iter_jobs(workflow):
        for step in _iter_steps(job):
            run = step.get("run")
            if not isinstance(run, str):
                continue
            for match in _EXPR_RE.finditer(run):
                expr = match.group(1)
                normalized = re.sub(r"\s+", "", expr)
                if not _UNTRUSTED_RE.search(normalized):
                    continue
                snippet = match.group(0)
                findings.append(
                    Finding(
                        rule_id=meta.id,
                        rule_name=meta.name,
                        severity=meta.severity,
                        file=file,
                        line=_locate(lines, snippet, used),
                        evidence=snippet,
                        message=(
                            "신뢰할 수 없는 입력 "
                            f"{normalized} 이(가) run 스크립트에 직접 삽입되어 "
                            "임의 명령 실행으로 이어질 수 있습니다."
                        ),
                        remediation=meta.remediation,
                        autofixable=meta.autofixable,
                    )
                )
    return findings


def detect_excessive_permissions(
    workflow: dict, lines: list[str], file: str, meta: RuleMeta, used: set[int]
) -> list[Finding]:
    findings: list[Finding] = []

    def check(scope_perms, label: str) -> None:
        if isinstance(scope_perms, str) and scope_perms.strip() == "write-all":
            findings.append(
                Finding(
                    rule_id=meta.id,
                    rule_name=meta.name,
                    severity=meta.severity,
                    file=file,
                    line=_locate(lines, "write-all", used),
                    evidence="permissions: write-all",
                    message=(
                        f"{label}에 permissions: write-all 이 설정되어 "
                        "GITHUB_TOKEN 이 모든 스코프에 write 권한을 가집니다."
                    ),
                    remediation=meta.remediation,
                    autofixable=meta.autofixable,
                )
            )

    workflow_perms = workflow.get("permissions")
    check(workflow_perms, "워크플로우")

    jobs = list(_iter_jobs(workflow))
    job_perms_present = False
    for _name, job in jobs:
        job_perms = job.get("permissions")
        if job_perms is not None:
            job_perms_present = True
        check(job_perms, f"잡 '{_name}'")

    # No permissions block anywhere -> repository default applies (may be broad).
    if workflow_perms is None and not job_perms_present:
        line = _locate(lines, "jobs:", used) or 1
        findings.append(
            Finding(
                rule_id=meta.id,
                rule_name=meta.name,
                severity="low",
                file=file,
                line=line,
                evidence="(no permissions block)",
                message=(
                    "워크플로우와 잡 어디에도 permissions 가 명시되지 않아 "
                    "저장소 기본 권한(넓을 수 있음)이 적용됩니다."
                ),
                remediation=meta.remediation,
                autofixable=False,
            )
        )
    return findings


def detect_unpinned_actions(
    workflow: dict, lines: list[str], file: str, meta: RuleMeta, used: set[int]
) -> list[Finding]:
    findings: list[Finding] = []

    def check_uses(value, source: str) -> None:
        if not isinstance(value, str):
            return
        ref = value.strip()
        if ref.startswith("./") or ref.startswith(".\\") or ref.startswith("docker://"):
            return  # local action or docker reference: out of scope
        if "@" not in ref:
            return
        pinned = ref.rsplit("@", 1)[1]
        if _SHA_RE.match(pinned):
            return  # already pinned to a full commit SHA
        findings.append(
            Finding(
                rule_id=meta.id,
                rule_name=meta.name,
                severity=meta.severity,
                file=file,
                line=_locate(lines, ref, used),
                evidence=f"uses: {ref}",
                message=(
                    f"{source} 의 외부 참조 '{ref}' 가 커밋 SHA 로 고정되지 않아 "
                    "참조 대상이 변경될 수 있습니다."
                ),
                remediation=meta.remediation,
                autofixable=meta.autofixable,
            )
        )

    for name, job in _iter_jobs(workflow):
        check_uses(job.get("uses"), f"잡 '{name}'")  # reusable workflow
        for step in _iter_steps(job):
            check_uses(step.get("uses"), f"잡 '{name}' 스텝")
    return findings


DETECTORS = {
    "script-injection": detect_script_injection,
    "excessive-permissions": detect_excessive_permissions,
    "unpinned-actions": detect_unpinned_actions,
}
