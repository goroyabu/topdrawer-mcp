from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest

from topdrawer_mcp import render


pytestmark = pytest.mark.unit


def _make_executable(path: Path):
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o755)


def test_resolve_td_executable_prefers_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    configured = tmp_path / "custom-td"
    fallback = tmp_path / "td"
    _make_executable(configured)
    _make_executable(fallback)
    monkeypatch.setenv(render.TD_EXECUTABLE_ENV, str(configured))
    monkeypatch.setenv("PATH", str(tmp_path))

    resolved = render.resolve_td_executable()

    assert resolved == configured.resolve()


def test_resolve_td_executable_falls_back_to_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    fallback = tmp_path / "td"
    _make_executable(fallback)
    monkeypatch.delenv(render.TD_EXECUTABLE_ENV, raising=False)
    monkeypatch.setenv("PATH", str(tmp_path))

    resolved = render.resolve_td_executable()

    assert resolved == fallback.resolve()


def test_resolve_td_executable_rejects_non_executable_env_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    configured = tmp_path / "custom-td"
    configured.write_text("not executable\n", encoding="utf-8")
    monkeypatch.setenv(render.TD_EXECUTABLE_ENV, str(configured))

    with pytest.raises(PermissionError, match="non-executable file"):
        render.resolve_td_executable()


def test_resolve_gs_executable_raises_when_missing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PATH", "")

    with pytest.raises(FileNotFoundError, match="Unable to find `gs` on PATH"):
        render.resolve_gs_executable()


def test_resolve_input_path_rejects_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="Input file does not exist"):
        render.resolve_input_path(str(tmp_path / "missing.top"))


def test_resolve_input_path_rejects_directory(tmp_path: Path):
    with pytest.raises(IsADirectoryError, match="Input path is not a file"):
        render.resolve_input_path(str(tmp_path))


def test_resolve_output_path_defaults_to_system_temp():
    resolved = render.resolve_output_path(None)

    assert resolved.is_absolute()
    assert resolved.name == "render.png"
    assert resolved.parent.parent == Path(tempfile.gettempdir()).resolve()
    assert resolved.parent.name.startswith("topdrawer-mcp-render-out-")


def test_resolve_output_path_uses_current_working_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    monkeypatch.chdir(tmp_path)

    resolved = render.resolve_output_path("nested/output.png")

    assert resolved == (tmp_path / "nested" / "output.png").resolve()


def test_build_wrapper_text_prepends_postscript_device():
    wrapped = render.build_wrapper_text("TITLE TOP 'smoke'\nPLOT\n")

    assert wrapped.startswith("SET DEVICE POSTSCR FILE='render.ps'\n")
    assert "TITLE TOP 'smoke'" in wrapped


def test_render_topdrawer_input_rejects_existing_output_without_overwrite(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    input_path = tmp_path / "input.top"
    output_path = tmp_path / "render.png"
    input_path.write_text("TITLE TOP 'smoke'\nPLOT\n", encoding="utf-8")
    output_path.write_text("existing", encoding="utf-8")

    td = tmp_path / "td"
    _make_executable(td)
    monkeypatch.setenv(render.TD_EXECUTABLE_ENV, str(td))
    monkeypatch.setattr(render, "resolve_gs_executable", lambda: Path("/bin/gs"))

    with pytest.raises(FileExistsError, match="Output file already exists"):
        render.render_topdrawer_input(str(input_path), output_path=str(output_path))


def test_render_topdrawer_input_reports_td_nonzero_exit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    input_path = tmp_path / "input.top"
    output_path = tmp_path / "render.png"
    input_path.write_text("plot\n", encoding="utf-8")
    monkeypatch.setattr(render, "resolve_td_executable", lambda: Path("/bin/td"))
    monkeypatch.setattr(render, "resolve_gs_executable", lambda: Path("/bin/gs"))

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 2, stdout="", stderr="td failed\n")

    monkeypatch.setattr(render.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="`td` exited with code 2"):
        render.render_topdrawer_input(str(input_path), output_path=str(output_path))


def test_render_topdrawer_input_reports_td_error_marker(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    input_path = tmp_path / "input.top"
    output_path = tmp_path / "render.png"
    input_path.write_text("plot\n", encoding="utf-8")
    monkeypatch.setattr(render, "resolve_td_executable", lambda: Path("/bin/td"))
    monkeypatch.setattr(render, "resolve_gs_executable", lambda: Path("/bin/gs"))

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args[0],
            0,
            stdout="*** ERROR *** bad plot\n",
            stderr="",
        )

    monkeypatch.setattr(render.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="`td` reported an execution error"):
        render.render_topdrawer_input(str(input_path), output_path=str(output_path))


def test_render_topdrawer_input_reports_missing_postscript_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    input_path = tmp_path / "input.top"
    output_path = tmp_path / "render.png"
    input_path.write_text("plot\n", encoding="utf-8")
    monkeypatch.setattr(render, "resolve_td_executable", lambda: Path("/bin/td"))
    monkeypatch.setattr(render, "resolve_gs_executable", lambda: Path("/bin/gs"))

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 0, stdout="Plot  1 Done.\n", stderr="")

    monkeypatch.setattr(render.subprocess, "run", fake_run)

    with pytest.raises(FileNotFoundError, match="did not produce the expected PostScript output"):
        render.render_topdrawer_input(str(input_path), output_path=str(output_path))


def test_render_topdrawer_input_reports_gs_nonzero_exit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    input_path = tmp_path / "input.top"
    output_path = tmp_path / "render.png"
    input_path.write_text("plot\n", encoding="utf-8")
    monkeypatch.setattr(render, "resolve_td_executable", lambda: Path("/bin/td"))
    monkeypatch.setattr(render, "resolve_gs_executable", lambda: Path("/bin/gs"))

    calls = {"count": 0}

    def fake_run(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            workdir = Path(kwargs["cwd"])
            (workdir / render.TD_PS_FILENAME).write_text("%!PS-Adobe-1.0\n", encoding="utf-8")
            return subprocess.CompletedProcess(args[0], 0, stdout="Plot  1 Done.\n", stderr="")
        return subprocess.CompletedProcess(args[0], 1, stdout="", stderr="gs failed\n")

    monkeypatch.setattr(render.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="`gs` exited with code 1"):
        render.render_topdrawer_input(str(input_path), output_path=str(output_path))
