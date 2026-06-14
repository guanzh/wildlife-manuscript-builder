"""Journal target contract with refresh capability."""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.request import Request, urlopen

DEFAULT_JOURNAL_URL = (
    "https://www.biodiversity-science.net/CN/column/column49.shtml"
)


@dataclass(frozen=True)
class JournalContract:
    journal_name: str = "生物多样性"
    main_language: str = "zh-CN"
    bilingual_elements: tuple[str, ...] = ("title", "abstract", "keywords")
    source_url: str = DEFAULT_JOURNAL_URL
    status: str = "cached"  # cached | fresh | stale


def default_contract() -> JournalContract:
    """Return the canonical default contract."""
    return JournalContract()


class JournalRefresh:
    """Refresh journal contract from the official source.

    Uses an injectable fetcher for tests.
    """

    def __init__(self, project: Any) -> None:
        self._project = project

    @property
    def _wmb(self) -> Path:
        try:
            return self._project.paths.wmb_dir
        except AttributeError:
            return Path.cwd() / ".wmb"

    def refresh_contract(
        self,
        project: Any | None = None,
        fetcher: Callable[[str], bytes] | None = None,
    ) -> JournalContract:
        """Fetch and cache the journal contract.

        Parameters
        ----------
        project:
            Override project (for test isolation).
        fetcher:
            Injectable function that takes a URL and returns bytes.
            Defaults to urllib.request.urlopen.

        Returns
        -------
        JournalContract with status 'fresh' on success, 'stale' on failure.
        """
        f = fetcher or self._default_fetch
        url = DEFAULT_JOURNAL_URL

        try:
            data = f(url)
            content_hash = hashlib.sha256(data).hexdigest()[:16]
            timestamp = datetime.now(timezone.utc).isoformat()

            # Store the cached contract
            self._wmb.mkdir(parents=True, exist_ok=True)
            cache_path = self._wmb / "journal_cache"
            cache_path.mkdir(exist_ok=True)

            import yaml
            cached = {
                "source_url": url,
                "retrieved_at": timestamp,
                "content_hash": content_hash,
                "status": "fresh",
                "journal_name": "生物多样性",
                "main_language": "zh-CN",
                "bilingual_elements": ["title", "abstract", "keywords"],
            }
            (cache_path / "contract.yaml").write_text(
                yaml.safe_dump(cached, default_flow_style=False, sort_keys=False),
                encoding="utf-8",
            )
            return JournalContract(
                status="fresh",
                source_url=url,
            )
        except Exception as exc:
            # Preserve existing cached rules but mark stale
            try:
                existing = self._load_cached()
                if existing:
                    return JournalContract(
                        journal_name=existing.get("journal_name", "生物多样性"),
                        main_language=existing.get("main_language", "zh-CN"),
                        status="stale",
                        source_url=url,
                    )
            except Exception:
                pass
            return JournalContract(status="stale", source_url=url)

    def load_contract(self) -> JournalContract:
        """Load the cached contract or return default."""
        try:
            cached = self._load_cached()
            if cached:
                return JournalContract(
                    journal_name=cached.get("journal_name", "生物多样性"),
                    main_language=cached.get("main_language", "zh-CN"),
                    status=cached.get("status", "stale"),
                    source_url=cached.get("source_url", DEFAULT_JOURNAL_URL),
                )
        except Exception:
            pass
        return default_contract()

    def _load_cached(self) -> dict[str, Any] | None:
        cache_path = self._wmb / "journal_cache" / "contract.yaml"
        if not cache_path.exists():
            return None
        import yaml
        raw = cache_path.read_text(encoding="utf-8")
        return yaml.safe_load(raw) or {}

    @staticmethod
    def _default_fetch(url: str) -> bytes:
        req = Request(url, headers={"User-Agent": "WMB/1.0"})
        with urlopen(req, timeout=15) as resp:
            return resp.read()
