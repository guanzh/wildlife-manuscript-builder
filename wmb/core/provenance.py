"""Analysis provenance and claim trace for manuscript evidence."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass
class ClaimValidationReport:
    valid: bool = True
    issues: list[str] = field(default_factory=list)


class ProvenanceStore:
    """Persistent store for analysis provenance and claim traces.

    Analyses go to .wmb/artifacts/analysis/ANALYSIS_ID.yaml
    Claims go to .wmb/artifacts/claims/CLAIM_ID.yaml

    Persistence is no-clobber and idempotent for identical records.
    """

    def __init__(self, project: Any) -> None:
        self._project = project

    @property
    def analysis_dir(self) -> Path:
        return self._wmb / "artifacts" / "analysis"

    @property
    def claims_dir(self) -> Path:
        return self._wmb / "artifacts" / "claims"

    @property
    def _wmb(self) -> Path:
        try:
            return self._project.paths.wmb_dir
        except AttributeError:
            return Path.cwd() / ".wmb"

    # ---- analysis ----

    def record_analysis(self, payload: dict[str, Any]) -> str:
        """Persist an analysis record. Idempotent ONLY for identical payload.
        Different content with same analysis_id blocks (no-clobber).
        """
        analysis_id = payload.get("analysis_id", f"analysis_{uuid4().hex[:8]}")

        dest = self.analysis_dir
        dest.mkdir(parents=True, exist_ok=True)
        path = dest / f"{analysis_id}.yaml"

        if path.exists():
            existing = self._load_yaml(path)
            if existing == payload:
                return analysis_id  # idempotent: identical
            raise ValueError(
                f"Analysis {analysis_id} already exists with different content. "
                "Use a new analysis_id or delete the existing record."
            )

        import yaml
        with open(str(path), "w", encoding="utf-8", newline="\n") as fh:
            yaml.safe_dump(payload, fh, default_flow_style=False, sort_keys=False)

        return analysis_id

    def get_analysis(self, analysis_id: str) -> dict[str, Any] | None:
        path = self.analysis_dir / f"{analysis_id}.yaml"
        if not path.exists():
            return None
        return self._load_yaml(path)

    # ---- claim trace ----

    def record_claim_trace(
        self,
        claim_id: str | None = None,
        *,
        analysis_id: str | None = None,
        result_card: str | None = None,
        manuscript_claim: str | None = None,
        figure_or_table_caption: str | None = None,
        central: bool = False,
        evidence_source: str | None = None,
        status: str = "draft",
    ) -> str:
        """Record a claim trace."""
        cid = claim_id or f"claim_{uuid4().hex[:8]}"

        entry = {
            "claim_id": cid,
            "analysis_id": analysis_id,
            "result_card": result_card,
            "manuscript_claim": manuscript_claim,
            "figure_or_table_caption": figure_or_table_caption,
            "central": central,
            "evidence_source": evidence_source,
            "status": status,
        }

        self.claims_dir.mkdir(parents=True, exist_ok=True)
        path = self.claims_dir / f"{cid}.yaml"

        if path.exists():
            existing = self._load_yaml(path)
            if existing == entry:
                return cid  # idempotent

        import yaml
        with open(str(path), "w", encoding="utf-8", newline="\n") as fh:
            yaml.safe_dump(entry, fh, default_flow_style=False, sort_keys=False)

        return cid

    def get_claim_trace(self, claim_id: str) -> dict[str, Any] | None:
        path = self.claims_dir / f"{claim_id}.yaml"
        if not path.exists():
            return None
        return self._load_yaml(path)

    # ---- validation ----

    def validate_claim_trace(self, claim_id: str) -> ClaimValidationReport:
        """Validate a single claim trace against provenance rules."""
        report = ClaimValidationReport()
        trace = self.get_claim_trace(claim_id)
        if trace is None:
            report.valid = False
            report.issues.append(f"Claim trace {claim_id} not found")
            return report

        analysis_id = trace.get("analysis_id") or trace.get("evidence_source")
        central = trace.get("central", False)
        result_card = trace.get("result_card")
        manuscript_claim = trace.get("manuscript_claim")
        caption = trace.get("figure_or_table_caption")

        if central:
            if not result_card:
                report.issues.append("Central claim missing result_card")
            if not manuscript_claim:
                report.issues.append("Central claim missing manuscript_claim")
            if caption and not analysis_id:
                report.issues.append(
                    "Central figure/table caption requires an analysis trace"
                )

        if analysis_id:
            analysis = self.get_analysis(analysis_id)
            if analysis is None:
                report.issues.append(f"Analysis {analysis_id} not found")
            else:
                if analysis.get("status") == "failed":
                    report.issues.append(
                        f"Analysis {analysis_id} has status 'failed' — "
                        "cannot support a claim"
                    )
                allowed = {"successful", "usable_with_caveat"}
                if analysis.get("status") not in allowed:
                    report.issues.append(
                        f"Analysis {analysis_id} status {analysis.get('status')!r} "
                        f"not in allowed set {allowed}"
                    )

                # Check referenced file exists
                file_path = analysis.get("file_path")
                if file_path:
                    resolved = Path(file_path)
                    if not resolved.is_absolute():
                        resolved = self._wmb.parent / resolved
                    if not resolved.exists():
                        report.issues.append(
                            f"Referenced file {file_path} does not exist"
                        )

                # Check hash matches
                declared_hash = analysis.get("content_hash")
                if file_path and declared_hash:
                    resolved = Path(file_path)
                    if not resolved.is_absolute():
                        resolved = self._wmb.parent / resolved
                    if resolved.exists():
                        actual = self._hash_file(resolved)
                        if actual != declared_hash:
                            report.issues.append(
                                f"Hash mismatch for {file_path}: "
                                f"declared {declared_hash}, actual {actual}"
                            )
        else:
            if not central and not manuscript_claim:
                report.issues.append("Claim has no manuscript_claim text")

        report.valid = len(report.issues) == 0
        return report

    def validate_all_central_claims(self) -> list[ClaimValidationReport]:
        """Validate every central claim in the store."""
        results: list[ClaimValidationReport] = []
        if not self.claims_dir.is_dir():
            return results
        for fpath in sorted(self.claims_dir.iterdir()):
            if fpath.suffix not in (".yaml", ".yml"):
                continue
            trace = self._load_yaml(fpath)
            if not isinstance(trace, dict):
                continue
            if trace.get("central"):
                results.append(self.validate_claim_trace(trace["claim_id"]))
        return results

    # ---- helpers ----

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        import yaml
        raw = path.read_text(encoding="utf-8")
        return yaml.safe_load(raw) or {}

    def _hash_file(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
