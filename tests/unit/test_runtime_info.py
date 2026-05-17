from __future__ import annotations

from pathlib import Path

import pytest

from topdrawer_mcp import runtime_info


pytestmark = pytest.mark.unit


def test_get_runtime_info_reports_default_manual_and_missing_render_deps(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv(runtime_info.TOPDRAWER_MANUAL_ENV, raising=False)
    monkeypatch.delenv(runtime_info.TD_EXECUTABLE_ENV, raising=False)
    monkeypatch.delenv(runtime_info.GS_EXECUTABLE_ENV, raising=False)
    monkeypatch.setenv("PATH", "")

    result = runtime_info.get_runtime_info()

    assert result["manual"]["source"] == "default"
    assert result["manual"]["exists"] is True
    assert result["manual"]["user_action"] == []
    assert result["render"]["available"] is False
    assert result["render"]["td"]["available"] is False
    assert result["render"]["gs"]["available"] is False
    assert result["render"]["missing_requirements"] == ["td", "gs"]
    assert len(result["render"]["user_action"]) == 3


def test_get_runtime_info_reports_configured_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    manual = tmp_path / "manual.txt"
    td = tmp_path / "td"
    gs = tmp_path / "gs"
    manual.write_text("manual\n", encoding="utf-8")
    td.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    gs.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    td.chmod(0o755)
    gs.chmod(0o755)
    monkeypatch.setenv(runtime_info.TOPDRAWER_MANUAL_ENV, str(manual))
    monkeypatch.setenv(runtime_info.TD_EXECUTABLE_ENV, str(td))
    monkeypatch.setenv(runtime_info.GS_EXECUTABLE_ENV, str(gs))

    result = runtime_info.get_runtime_info()

    assert result["manual"]["source"] == "env"
    assert result["manual"]["configured_path"] == str(manual)
    assert result["manual"]["exists"] is True
    assert result["manual"]["user_action"] == []
    assert result["render"]["available"] is True
    assert result["render"]["td"]["resolved_path"] == str(td.resolve())
    assert result["render"]["gs"]["resolved_path"] == str(gs.resolve())
    assert result["render"]["missing_requirements"] == []
    assert result["render"]["user_action"] == []


def test_get_runtime_info_lists_lookup_sources():
    result = runtime_info.get_runtime_info()

    names = {entry["name"] for entry in result["command_lookup_sources"]}
    assert names == {"manual", "targets", "reviewed"}


def test_get_runtime_info_reports_missing_manual_action(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    manual = tmp_path / "missing-manual.txt"
    monkeypatch.setenv(runtime_info.TOPDRAWER_MANUAL_ENV, str(manual))

    result = runtime_info.get_runtime_info()

    assert result["manual"]["exists"] is False
    assert result["manual"]["error"] is not None
    assert any(runtime_info.TOPDRAWER_MANUAL_ENV in step for step in result["manual"]["user_action"])
