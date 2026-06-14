"""Tests for JournalRefresh."""

from __future__ import annotations

from pathlib import Path

from wmb.core.journal import default_contract, JournalRefresh


class _MockProject:
    def __init__(self, tmp_path: Path) -> None:
        (tmp_path / ".wmb").mkdir(parents=True, exist_ok=True)
        self.paths = type("Paths", (), {"wmb_dir": tmp_path / ".wmb"})()


def test_default_contract() -> None:
    c = default_contract()
    assert c.journal_name == "生物多样性"
    assert c.main_language == "zh-CN"
    assert "title" in c.bilingual_elements


def test_successful_refresh_marks_fresh(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    jr = JournalRefresh(proj)

    def _fake_fetch(url: str) -> bytes:
        return b"<html>dummy instructions</html>"

    contract = jr.refresh_contract(fetcher=_fake_fetch)
    assert contract.status == "fresh"


def test_failed_refresh_marks_stale_without_losing_cache(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    jr = JournalRefresh(proj)

    # First: successful refresh
    def _good(url: str) -> bytes:
        return b"<html>ok</html>"

    jr.refresh_contract(fetcher=_good)

    # Second: failed refresh
    def _bad(url: str) -> bytes:
        raise RuntimeError("network error")

    contract = jr.refresh_contract(fetcher=_bad)
    assert contract.status == "stale"

    # Cache should still be readable
    loaded = jr.load_contract()
    assert loaded.journal_name == "生物多样性"


def test_content_hash_stored(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    jr = JournalRefresh(proj)

    def _fake(url: str) -> bytes:
        return b"content"

    jr.refresh_contract(fetcher=_fake)
    cached = jr._load_cached()
    assert cached is not None
    assert len(cached.get("content_hash", "")) == 16


def test_load_contract_returns_default_when_no_cache(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    jr = JournalRefresh(proj)
    c = jr.load_contract()
    assert c.status == "cached"  # default status
