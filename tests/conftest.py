from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from topdrawer_mcp import server


@pytest.fixture(autouse=True)
def clear_manual_cache(monkeypatch: pytest.MonkeyPatch):
    """Keep manual path and cached readers isolated between tests."""
    monkeypatch.delenv("TOPDRAWER_MANUAL_PATH", raising=False)
    server._manual_for_path.cache_clear()
    yield
    server._manual_for_path.cache_clear()


@pytest.fixture
def write_manual(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[[str], Path]:
    """Write a temporary manual file and point the server at it."""

    def _write_manual(text: str):
        path = tmp_path / "manual.txt"
        path.write_text(text, encoding="utf-8")
        monkeypatch.setenv("TOPDRAWER_MANUAL_PATH", str(path))
        server._manual_for_path.cache_clear()
        return path

    return _write_manual


@pytest.fixture
def sample_manual(write_manual):
    return write_manual(
        "\n".join(
            [
                "Intro line",
                "BARGRAPH command",
                "Middle context",
                "bargraph lowercase match",
                "Final line",
            ]
        )
        + "\n"
    )
