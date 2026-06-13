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


class _FakeArtifact:
    def __init__(self, artifact_id: str, resource_uri: str):
        self.artifact_id = artifact_id
        self.resource_uri = resource_uri


class _FakeArtifactManager:
    def __init__(self):
        self.created = []

    def create_artifact(self, **kwargs):
        self.created.append(kwargs)
        return _FakeArtifact("tdart_test", "resource://artifacts/tdart_test")


def test_resolve_td_executable_prefers_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    configured = tmp_path / "custom-td"
    fallback = tmp_path / "td"
    _make_executable(configured)
    _make_executable(fallback)
    monkeypatch.setenv(render.TD_EXECUTABLE_ENV, str(configured))
    monkeypatch.setenv("PATH", str(tmp_path))

    assert render.resolve_td_executable() == configured.resolve()


def test_resolve_gs_executable_prefers_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    configured = tmp_path / "custom-gs"
    fallback = tmp_path / "gs"
    _make_executable(configured)
    _make_executable(fallback)
    monkeypatch.setenv(render.GS_EXECUTABLE_ENV, str(configured))
    monkeypatch.setenv("PATH", str(tmp_path))

    assert render.resolve_gs_executable() == configured.resolve()


def test_resolve_gs_executable_raises_when_missing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PATH", "")

    with pytest.raises(FileNotFoundError, match="get_server_runtime_info"):
        render.resolve_gs_executable()


def test_resolve_input_path_rejects_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="Input file does not exist"):
        render.resolve_input_path(str(tmp_path / "missing.top"))


def test_resolve_output_path_defaults_to_named_temp_file():
    resolved = render.resolve_output_path(None, default_filename="render.ps")

    assert resolved.is_absolute()
    assert resolved.name == "render.ps"
    assert resolved.parent.parent == Path(tempfile.gettempdir()).resolve()
    assert resolved.parent.name.startswith("topdrawer-mcp-render-out-")


def test_build_wrapper_text_prepends_postscript_device():
    wrapped = render.build_wrapper_text("TITLE TOP 'smoke'\nPLOT\n")

    assert wrapped.startswith("SET DEVICE POSTSCR FILE='render.ps'\n")
    assert "TITLE TOP 'smoke'" in wrapped


def test_parse_set_device_line_accepts_postscr_abbreviation():
    parsed = render.parse_set_device_line("SET DEVICE POSTSCR ORIENT=3 FILE='plot.ps'")

    assert parsed.device == "POSTSCRIPT"
    assert parsed.orientation == 3
    assert parsed.output_key == "FILE"
    assert parsed.output_value == "plot.ps"


def test_parse_set_device_line_preserves_unknown_trailing_tokens_for_policy_rejection():
    parsed = render.parse_set_device_line("SET DEVICE POSTSCRIPT FOO BAR")

    assert parsed.device == "POSTSCRIPT"
    assert parsed.option_tokens == ["FOO", "BAR"]


def test_parse_set_device_line_preserves_unknown_key_value_for_policy_rejection():
    parsed = render.parse_set_device_line("SET DEVICE POSTSCRIPT BAZ=1")

    assert parsed.device == "POSTSCRIPT"
    assert parsed.unknown_options == {"BAZ": "1"}


def test_parse_set_device_line_rejects_invalid_orientation():
    with pytest.raises(ValueError, match="ORIENTATION must be 0..3"):
        render.parse_set_device_line("SET DEVICE POSTSCRIPT ORIENTATION=9")


def test_normalize_execution_device_config_overrides_script_side_file():
    parsed, overridden = render.normalize_execution_device_config(
        "SET DEVICE POSTSCRIPT FILE='user.ps'\nplot\n",
        output_format="png",
        execution_output_path=Path("/tmp/server.ps"),
    )

    assert overridden is True
    assert parsed.output_key == "FILE"
    assert parsed.output_value == "/tmp/server.ps"


def test_normalize_execution_device_config_rejects_unsupported_device():
    with pytest.raises(render.PolicyError, match="unsupported device error"):
        render.normalize_execution_device_config(
            "SET DEVICE XWINDOW\nplot\n",
            output_format="png",
            execution_output_path=Path("/tmp/server.ps"),
        )


def test_normalize_execution_device_config_rejects_unknown_trailing_tokens_as_policy_error():
    with pytest.raises(render.PolicyError, match="unsupported option or mode error"):
        render.normalize_execution_device_config(
            "SET DEVICE POSTSCRIPT FOO BAR\nplot\n",
            output_format="png",
            execution_output_path=Path("/tmp/server.ps"),
        )


def test_normalized_device_config_metadata_uses_parsed_values():
    parsed = render.ParsedSetDevice(
        original_line="SET DEVICE POSTSCRIPT ORIENTATION=3 COLOR=ON FILE='out.ps'",
        device="POSTSCRIPT",
        orientation=3,
        orientation_keyword="ORIENTATION",
        color=True,
        output_key="FILE",
        output_value="/tmp/server.ps",
        width="10",
        height="20",
        reverse=True,
        sequential=True,
    )

    metadata = render._normalized_device_config_metadata(parsed)

    assert metadata == {
        "device": "POSTSCRIPT",
        "output_key": "FILE",
        "output_value": "/tmp/server.ps",
        "orientation": 3,
        "orientation_keyword": "ORIENTATION",
        "color": True,
        "width": "10",
        "height": "20",
        "reverse": True,
        "sequential": True,
    }


def test_normalize_execution_device_config_rejects_multiple_set_device_commands():
    with pytest.raises(render.PolicyError, match="multiple SET DEVICE commands"):
        render.normalize_execution_device_config(
            "SET DEVICE POSTSCRIPT\nplot\nSET DEVICE POSTSCRIPT\n",
            output_format="png",
            execution_output_path=Path("/tmp/server.ps"),
        )


def test_build_execution_source_text_replaces_existing_set_device():
    parsed = render.ParsedSetDevice(
        original_line="SET DEVICE POSTSCRIPT FILE='user.ps'",
        device="POSTSCRIPT",
        output_key="FILE",
        output_value="/tmp/server.ps",
        orientation=3,
        orientation_keyword="ORIENTATION",
    )

    rebuilt = render.build_execution_source_text(
        "SET DEVICE POSTSCRIPT FILE='user.ps'\nTITLE TOP 't'\nPLOT\n",
        parsed,
    )

    assert rebuilt.startswith("SET DEVICE POSTSCRIPT ORIENTATION=3 FILE='/tmp/server.ps'\n")
    assert "TITLE TOP 't'" in rebuilt
    assert "user.ps" not in rebuilt


def test_read_postscript_bbox_parses_bounding_box(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    ps_path = tmp_path / "input.ps"
    ps_path.write_text("%!PS-Adobe-1.0\n", encoding="utf-8")

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args[0],
            0,
            stdout="",
            stderr="%%BoundingBox: 99 234 543 564\n",
        )

    monkeypatch.setattr(render.subprocess, "run", fake_run)

    assert render.read_postscript_bbox(ps_path, Path("/bin/gs")) == (99, 234, 543, 564)


def test_read_postscript_bbox_reports_ghostscript_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    ps_path = tmp_path / "input.ps"
    ps_path.write_text("%!PS-Adobe-1.0\n", encoding="utf-8")

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 1, stdout="", stderr="gs failed\n")

    monkeypatch.setattr(render.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="Ghostscript bounding-box read failure"):
        render.read_postscript_bbox(ps_path, Path("/bin/gs"))


def test_build_gs_png_command_uses_white_background_and_trim_defaults(tmp_path: Path):
    command = render.build_gs_png_command(
        Path("/bin/gs"),
        tmp_path / "input.ps",
        tmp_path / "output.png",
        background="white",
        crop=True,
        bbox=(99, 234, 543, 564),
    )

    assert "-sDEVICE=png16m" in command
    assert f"-r{render.GS_RENDER_DPI}" in command
    assert "-dFIXEDMEDIA" in command
    assert "-c" in command
    assert "-87 -222 translate" in command
    assert "-dDEVICEWIDTHPOINTS=468" in command
    assert "-dDEVICEHEIGHTPOINTS=354" in command


def test_build_gs_png_command_uses_transparent_device(tmp_path: Path):
    command = render.build_gs_png_command(
        Path("/bin/gs"),
        tmp_path / "input.ps",
        tmp_path / "output.png",
        background="transparent",
        crop=False,
    )

    assert "-sDEVICE=png16malpha" in command
    assert "-dFIXEDMEDIA" not in command
    assert "-c" not in command


def test_generate_topdrawer_png_rejects_invalid_input_combination():
    with pytest.raises(ValueError, match="exactly one of input_path or script"):
        render.generate_topdrawer_png()


def test_generate_topdrawer_png_rejects_unknown_background():
    with pytest.raises(ValueError, match="background must be one of"):
        render.generate_topdrawer_png(script="plot\n", background="blue")


def test_generate_topdrawer_postscript_uses_temp_output_by_default(
    monkeypatch: pytest.MonkeyPatch,
):
    captured: dict[str, object] = {}
    fake_manager = _FakeArtifactManager()

    def fake_run_td(source_text: str, *, base_dir: Path, output_path: Path, output_format: str):
        captured["output_path"] = output_path
        output_path.write_text("%!PS-Adobe-1.0\n", encoding="utf-8")
        return (
            output_path,
            "/bin/td",
            False,
            "SET DEVICE POSTSCRIPT FILE='/tmp/server.ps'\nplot\n",
            render.ParsedSetDevice(
                original_line="",
                device="POSTSCRIPT",
                output_key="FILE",
                output_value="/tmp/server.ps",
            ),
        )

    monkeypatch.setattr(render, "_run_td_to_postscript", fake_run_td)
    monkeypatch.setattr(render, "get_artifact_manager", lambda: fake_manager)

    result = render.generate_topdrawer_postscript(script="plot\n")

    assert result["success"] is True
    assert result["format"] == "postscript"
    assert result["artifact_id"] == "tdart_test"
    assert result["resource_uri"] == "resource://artifacts/tdart_test"
    assert Path(fake_manager.created[0]["output_file"]).name == "render.ps"
    assert captured["output_path"] == Path(fake_manager.created[0]["output_file"])
    assert fake_manager.created[0]["source_text"].startswith("SET DEVICE POSTSCRIPT FILE=")
    assert result["metadata"]["normalized_device_config"]["device"] == "POSTSCRIPT"


def test_generate_topdrawer_png_returns_metadata_and_uses_crop_setting(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    output_path = tmp_path / "render.png"
    fake_manager = _FakeArtifactManager()

    def fake_run_td(source_text: str, *, base_dir: Path, output_path: Path, output_format: str):
        output_path.write_text("%!PS-Adobe-1.0\n", encoding="utf-8")
        return (
            output_path,
            "/bin/td",
            True,
            "SET DEVICE POSTSCRIPT ORIENTATION=3 FILE='/tmp/server.ps'\nplot\n",
            render.ParsedSetDevice(
                original_line="SET DEVICE POSTSCRIPT ORIENTATION=3 FILE='user.ps'",
                device="POSTSCRIPT",
                orientation=3,
                orientation_keyword="ORIENTATION",
                output_key="FILE",
                output_value="/tmp/server.ps",
            ),
        )

    monkeypatch.setattr(render, "_run_td_to_postscript", fake_run_td)
    monkeypatch.setattr(render, "get_artifact_manager", lambda: fake_manager)
    monkeypatch.setattr(render, "resolve_gs_executable", lambda: Path("/bin/gs"))
    monkeypatch.setattr(render, "read_postscript_bbox", lambda *args, **kwargs: (0, 0, 100, 100))

    def fake_run(*args, **kwargs):
        output_file = next(
            arg.split("=", 1)[1] for arg in args[0] if arg.startswith("-sOutputFile=")
        )
        Path(output_file).write_bytes(b"\x89PNG\r\n\x1a\n")
        return subprocess.CompletedProcess(args[0], 0, stdout="", stderr="")

    monkeypatch.setattr(render.subprocess, "run", fake_run)

    result = render.generate_topdrawer_png(
        script="plot\n",
        output_path=str(output_path),
        crop=False,
        background="transparent",
    )

    assert result["success"] is True
    assert result["format"] == "png"
    assert result["artifact_id"] == "tdart_test"
    assert result["resource_uri"] == "resource://artifacts/tdart_test"
    assert result["metadata"]["background"] == "transparent"
    assert result["metadata"]["crop_applied"] is False
    assert result["metadata"]["output_path_overridden"] is True
    assert result["metadata"]["output_path"] == str(output_path)
    assert result["metadata"]["normalized_device_config"]["orientation"] == 3
    assert fake_manager.created[0]["source_text"].startswith("SET DEVICE POSTSCRIPT ORIENTATION=3")


def test_generate_topdrawer_png_reports_ghostscript_raster_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    output_path = tmp_path / "render.png"
    fake_manager = _FakeArtifactManager()

    def fake_run_td(source_text: str, *, base_dir: Path, output_path: Path, output_format: str):
        output_path.write_text("%!PS-Adobe-1.0\n", encoding="utf-8")
        return (
            output_path,
            "/bin/td",
            False,
            "SET DEVICE POSTSCRIPT FILE='/tmp/server.ps'\nplot\n",
            render.ParsedSetDevice(
                original_line="",
                device="POSTSCRIPT",
                output_key="FILE",
                output_value="/tmp/server.ps",
            ),
        )

    monkeypatch.setattr(render, "_run_td_to_postscript", fake_run_td)
    monkeypatch.setattr(render, "get_artifact_manager", lambda: fake_manager)
    monkeypatch.setattr(render, "resolve_gs_executable", lambda: Path("/bin/gs"))
    monkeypatch.setattr(render, "read_postscript_bbox", lambda *args, **kwargs: (0, 0, 100, 100))

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 1, stdout="", stderr="gs failed\n")

    monkeypatch.setattr(render.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="Ghostscript raster render failure"):
        render.generate_topdrawer_png(script="plot\n", output_path=str(output_path))


def test_render_topdrawer_source_text_delegates_to_generate_topdrawer_png(
    monkeypatch: pytest.MonkeyPatch,
):
    captured = {}

    def fake_generate(**kwargs):
        captured["kwargs"] = kwargs
        return {
            "success": True,
            "format": "png",
            "message": "ok",
            "artifact_id": "tdart_test",
            "resource_uri": "resource://artifacts/tdart_test",
            "metadata": {},
        }

    monkeypatch.setattr(render, "generate_topdrawer_png", fake_generate)

    result = render.render_topdrawer_source_text(
        "plot\n",
        base_dir="samples",
        output_path="out.png",
        overwrite=True,
    )

    assert captured["kwargs"] == {
        "script": "plot\n",
        "base_dir": "samples",
        "output_path": "out.png",
        "overwrite": True,
    }
    assert result["success"] is True


def test_render_topdrawer_input_delegates_to_generate_topdrawer_png(
    monkeypatch: pytest.MonkeyPatch,
):
    captured = {}

    def fake_generate(**kwargs):
        captured["kwargs"] = kwargs
        return {
            "success": True,
            "format": "png",
            "message": "ok",
            "artifact_id": "tdart_test",
            "resource_uri": "resource://artifacts/tdart_test",
            "metadata": {},
        }

    monkeypatch.setattr(render, "generate_topdrawer_png", fake_generate)

    result = render.render_topdrawer_input(
        "sample.top",
        output_path="out.png",
        overwrite=True,
    )

    assert captured["kwargs"] == {
        "input_path": "sample.top",
        "output_path": "out.png",
        "overwrite": True,
    }
    assert result["success"] is True
