"""Submission package verifier against journal requirements."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from wmb.core.journal import JournalRefresh


@dataclass(frozen=True)
class Finding:
    code: str
    kind: str  # deterministic | heuristic
    blocking: bool
    message: str
    artifact: str | None = None


@dataclass
class VerificationReport:
    maximum_level: int = 0  # 0-4
    findings: list[Finding] = field(default_factory=list)

    @property
    def blocking(self) -> bool:
        return any(f.blocking for f in self.findings)


class PackageVerifier:
    """Verify a manuscript package against submission requirements.

    Deterministic findings block; heuristic findings never block.
    """

    def __init__(self, project: Any) -> None:
        self._project = project

    @property
    def _wmb(self) -> Path:
        try:
            return self._project.paths.wmb_dir
        except AttributeError:
            return Path.cwd() / ".wmb"

    def verify(
        self,
        author: dict[str, Any] | None = None,
        package: dict[str, Any] | None = None,
    ) -> VerificationReport:
        """Run all checks against the project state."""
        report = VerificationReport()
        pkg = package or {}
        author_data = author or {}

        # 1. Default journal contract
        journal = JournalRefresh(self._project).load_contract()

        # 2. Check placeholder author (Dr. Who)
        author_name = author_data.get("name") or pkg.get("author_name", "")
        if not author_name or author_name == "Dr. Who":
            report.findings.append(Finding(
                code="PLACEHOLDER_AUTHOR",
                kind="deterministic",
                blocking=True,
                message="Author is Dr. Who or not set — caps maximum at Level 3",
                artifact="author",
            ))
            report.maximum_level = min(report.maximum_level, 3)

        # 3. Check missing authorship / declarations
        if not author_data.get("affiliations"):
            report.findings.append(Finding(
                code="MISSING_AFFILIATIONS",
                kind="deterministic",
                blocking=True,
                message="No affiliations set",
            ))

        # 4. Missing bilingual elements (生物多样性要求)
        if journal.journal_name == "生物多样性":
            if not pkg.get("bilingual_title"):
                report.findings.append(Finding(
                    code="MISSING_BILINGUAL_TITLE",
                    kind="deterministic",
                    blocking=True,
                    message="Missing bilingual title (生物多样性 requirement)",
                ))
            if not pkg.get("bilingual_abstract"):
                report.findings.append(Finding(
                    code="MISSING_BILINGUAL_ABSTRACT",
                    kind="deterministic",
                    blocking=True,
                    message="Missing bilingual abstract",
                ))

        # 5. Citation/reference set mismatch
        refs = pkg.get("references", [])
        citations = pkg.get("citations", [])
        if refs and citations:
            ref_set = set(refs)
            cite_set = set(citations)
            missing_in_refs = cite_set - ref_set
            if missing_in_refs:
                report.findings.append(Finding(
                    code="CITATION_REF_MISMATCH",
                    kind="deterministic",
                    blocking=True,
                    message=f"{len(missing_in_refs)} cited papers not in reference list",
                ))

        # 6. Failed sensitive-data check
        if pkg.get("sensitive_data_check_failed", False):
            report.findings.append(Finding(
                code="SENSITIVE_DATA_FAILED",
                kind="deterministic",
                blocking=True,
                message="Sensitive-data check failed",
            ))

        # 7. Missing central claim trace
        claims_dir = self._wmb / "artifacts" / "claims"
        if not claims_dir.is_dir() or not any(claims_dir.iterdir()):
            report.findings.append(Finding(
                code="MISSING_CLAIM_TRACE",
                kind="deterministic",
                blocking=True,
                message="No central claim traces found — run provenance tracking",
            ))

        # 8. Failed analysis cited as support
        analysis_dir = self._wmb / "artifacts" / "analysis"
        if analysis_dir.is_dir():
            for fpath in analysis_dir.iterdir():
                if fpath.suffix not in (".yaml", ".yml"):
                    continue
                import yaml
                try:
                    data = yaml.safe_load(fpath.read_text(encoding="utf-8"))
                    if isinstance(data, dict) and data.get("status") == "failed":
                        report.findings.append(Finding(
                            code="FAILED_ANALYSIS_CITED",
                            kind="deterministic",
                            blocking=True,
                            message=f"Analysis {data.get('analysis_id', fpath.stem)} "
                                    "has status 'failed' and is cited as support",
                            artifact=fpath.stem,
                        ))
                except Exception:
                    pass

        # 9. Compute level
        if not report.blocking:
            if author_name and author_name != "Dr. Who" and author_data.get("affiliations"):
                report.maximum_level = max(report.maximum_level, 4)
            else:
                report.maximum_level = max(report.maximum_level, 1)

        return report
