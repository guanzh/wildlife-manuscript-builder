"""Tests for SKILL.md reference integrity and documentation requirements."""

from __future__ import annotations

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SKILL_MD = HERE / "SKILL.md"


def test_every_local_reference_link_exists() -> None:
    """Every references/*.md link in SKILL.md must resolve to a real file."""
    text = SKILL_MD.read_text(encoding="utf-8")
    missing: list[str] = []
    for m in re.finditer(r'(?:`|\()((?:references|scripts|templates|agents)/[^`)\s]+)', text):
        raw = m.group(1).strip()
        path_part = raw.split("#", 1)[0]
        if path_part and not (HERE / path_part).exists():
            missing.append(raw)
    assert not missing, f"Missing references: {missing}"


def test_skill_md_mentions_required_terms() -> None:
    """SKILL.md must mention .wmb/, Codex, Hermes, Dr. Who, and 生物多样性."""
    text = SKILL_MD.read_text(encoding="utf-8")
    assert ".wmb/" in text, "SKILL.md must mention .wmb/"
    assert "Codex" in text or "codex" in text, "SKILL.md must mention Codex"
    assert "Hermes" in text or "hermes" in text, "SKILL.md must mention Hermes"
    assert "Dr. Who" in text, "SKILL.md must mention Dr. Who"
    assert "生物多样性" in text, "SKILL.md must mention 生物多样性"


def test_literature_fallback_contains_no_key_placeholder() -> None:
    """literature-search-fallback.md must not contain key placeholder or .env path reference."""
    path = HERE / "references" / "literature-search-fallback.md"
    text = path.read_text(encoding="utf-8")
    # Check for .env file path references (not os.environ code references)
    assert "`ELICIT_API_KEY` in Hermes `.env` file" not in text, \
        "must not instruct readers to access Hermes .env path"
    assert "elk_live_" not in text, "literature fallback must not contain key placeholder"
