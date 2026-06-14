"""Submission package verifier with real claim trace validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from wmb.core.journal import JournalRefresh
from wmb.core.provenance import ProvenanceStore


@dataclass(frozen=True)
class Finding:
    code: str
    kind: str  # deterministic | heuristic
    blocking: bool
    message: str
    artifact: str | None = None


@dataclass
class VerificationReport:
    maximum_level: int = 0
    findings: list[Finding] = field(default_factory=list)

    @property
    def blocking(self) -> bool:
        return any(f.blocking for f in self.findings)


class PackageVerifier:
    """Verify manuscript package. Level 4 requires validated central claims."""

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
        report = VerificationReport()
        pkg = package or {}
        auth = author or {}

        journal = JournalRefresh(self._project).load_contract()
        store = ProvenanceStore(self._project)

        # Placeholder author → caps at Level 3
        author_name = auth.get("name") or pkg.get("author_name", "")
        if not author_name or author_name == "Dr. Who":
            report.findings.append(Finding(
                code="PLACEHOLDER_AUTHOR",
                kind="deterministic", blocking=True,
                message="Author is Dr. Who or not set — caps maximum at Level 3",
                artifact="author",
            ))

        if not auth.get("affiliations"):
            report.findings.append(Finding(
                code="MISSING_AFFILIATIONS",
                kind="deterministic", blocking=True,
                message="No affiliations set",
            ))

        if journal.journal_name == "生物多样性":
            if not pkg.get("bilingual_title"):
                report.findings.append(Finding(
                    code="MISSING_BILINGUAL_TITLE",
                    kind="deterministic", blocking=True,
                    message="Missing bilingual title (生物多样性 requirement)",
                ))
            if not pkg.get("bilingual_abstract"):
                report.findings.append(Finding(
                    code="MISSING_BILINGUAL_ABSTRACT",
                    kind="deterministic", blocking=True,
                    message="Missing bilingual abstract",
                ))

        # Citation/reference set mismatch
        refs = pkg.get("references", [])
        citations = pkg.get("citations", [])
        if refs and citations:
            missing = set(citations) - set(refs)
            if missing:
                report.findings.append(Finding(
                    code="CITATION_REF_MISMATCH",
                    kind="deterministic", blocking=True,
                    message=f"{len(missing)} cited papers not in reference list",
                ))

        # Sensitive-data check
        if pkg.get("sensitive_data_check_failed", False):
            report.findings.append(Finding(
                code="SENSITIVE_DATA_FAILED",
                kind="deterministic", blocking=True,
                message="Sensitive-data check failed",
            ))

        # LEVEL 4 requires validated central claims (not just files existing)
        claims_dir = self._wmb / "artifacts" / "claims"
        if not claims_dir.is_dir():
            report.findings.append(Finding(
                code="MISSING_CLAIM_TRACE",
                kind="deterministic", blocking=True,
                message="No claim traces directory found",
            ))
        else:
            central_claims = []
            for fpath in sorted(claims_dir.iterdir()):
                if fpath.suffix not in (".yaml", ".yml"):
                    continue
                import yaml
                try:
                    trace = yaml.safe_load(fpath.read_text(encoding="utf-8"))
                    if isinstance(trace, dict) and trace.get("central"):
                        central_claims.append(trace.get("claim_id", ""))
                except Exception:
                    continue

            if not central_claims:
                report.findings.append(Finding(
                    code="NO_CENTRAL_CLAIMS",
                    kind="deterministic", blocking=True,
                    message="No central claims found in trace directory. Level 4 requires validated claims.",
                ))
            else:
                # Validate each central claim through ProvenanceStore
                validated_count = 0
                for cid in central_claims:
                    v = store.validate_claim_trace(cid)
                    if v.valid:
                        validated_count += 1
                    else:
                        for issue in v.issues:
                            report.findings.append(Finding(
                                code="CLAIM_TRACE_FAILED",
                                kind="deterministic", blocking=True,
                                message=f"Claim {cid}: {issue}",
                                artifact=cid,
                            ))

                if validated_count == len(central_claims):
                    # All claims pass — can reach Level 4
                    pass
                else:
                    report.findings.append(Finding(
                        code="CLAIM_TRACE_FAILED",
                        kind="deterministic", blocking=True,
                        message=f"{len(central_claims) - validated_count}/{len(central_claims)} central claims failed validation",
                    ))

        # Failed analysis cited as support
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
                            kind="deterministic", blocking=True,
                            message=f"Analysis {data.get('analysis_id', fpath.stem)} "
                                    "has status 'failed' and is cited as support",
                            artifact=fpath.stem,
                        ))
                except Exception:
                    pass

        # Compute level
        if len(report.findings) == 0:
            report.maximum_level = 4
        elif not any(f.blocking for f in report.findings):
            report.maximum_level = max(1, report.maximum_level)

        return report
