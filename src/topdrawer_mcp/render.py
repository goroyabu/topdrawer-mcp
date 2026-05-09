from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import TypedDict


TD_EXECUTABLE_ENV = "TD_EXECUTABLE_PATH"
TD_PS_FILENAME = "render.ps"
TD_WRAPPER_FILENAME = "render.top"
TD_ERROR_MARKERS = ("*** ERROR ***", "ERROR FOUND BY THE UNIFIED GRAPHICS SYSTEM")


class RenderResult(TypedDict):
    """Structured success result returned by the render MCP tool."""

    output_path: str
    td_executable: str
    success: bool
    message: str


def resolve_td_executable() -> Path:
    """Resolve the `td` executable from the environment or PATH."""
    configured = os.environ.get(TD_EXECUTABLE_ENV)
    if configured:
        candidate = Path(configured).expanduser()
        if not candidate.is_file():
            raise FileNotFoundError(
                f"{TD_EXECUTABLE_ENV} points to a missing file: {candidate}"
            )
        if not os.access(candidate, os.X_OK):
            raise PermissionError(
                f"{TD_EXECUTABLE_ENV} points to a non-executable file: {candidate}"
            )
        return candidate.resolve()

    resolved = shutil.which("td")
    if resolved is None:
        raise FileNotFoundError(
            "Unable to find `td` on PATH. Set TD_EXECUTABLE_PATH or install td."
        )
    return Path(resolved).resolve()


def resolve_gs_executable() -> Path:
    """Resolve the Ghostscript executable from PATH."""
    resolved = shutil.which("gs")
    if resolved is None:
        raise FileNotFoundError(
            "Unable to find `gs` on PATH. Install Ghostscript to convert PostScript to PNG."
        )
    return Path(resolved).resolve()


def resolve_input_path(input_path: str) -> Path:
    """Resolve and validate the Topdrawer input file path."""
    candidate = Path(input_path).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    resolved = candidate.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Input file does not exist: {resolved}")
    if not resolved.is_file():
        raise IsADirectoryError(f"Input path is not a file: {resolved}")
    return resolved


def resolve_output_path(output_path: str | None) -> Path:
    """Resolve the final PNG output path."""
    if output_path is None:
        directory = Path(tempfile.mkdtemp(prefix="topdrawer-mcp-render-out-"))
        return (directory / "render.png").resolve()

    candidate = Path(output_path).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    return candidate.resolve()


def build_wrapper_text(source_text: str, ps_filename: str = TD_PS_FILENAME) -> str:
    """Prepend a PostScript output directive to the original Topdrawer input."""
    normalized = source_text
    if normalized and not normalized.endswith("\n"):
        normalized += "\n"
    return f"SET DEVICE POSTSCR FILE='{ps_filename}'\n{normalized}"


def render_topdrawer_input(
    input_path: str,
    output_path: str | None = None,
    overwrite: bool = False,
) -> RenderResult:
    """Render an existing Topdrawer input file into a PNG image."""
    resolved_input = resolve_input_path(input_path)
    resolved_output = resolve_output_path(output_path)
    td_executable = resolve_td_executable()
    gs_executable = resolve_gs_executable()

    if resolved_output.exists() and not overwrite:
        raise FileExistsError(
            f"Output file already exists: {resolved_output}. Pass overwrite=True to replace it."
        )

    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    source_text = resolved_input.read_text(encoding="utf-8", errors="replace")

    with tempfile.TemporaryDirectory(prefix="topdrawer-mcp-render-work-") as workdir_text:
        workdir = Path(workdir_text)
        wrapper_path = workdir / TD_WRAPPER_FILENAME
        ps_path = workdir / TD_PS_FILENAME
        wrapper_path.write_text(build_wrapper_text(source_text), encoding="utf-8")

        td_result = subprocess.run(
            [str(td_executable), str(wrapper_path)],
            cwd=workdir,
            capture_output=True,
            text=True,
            check=False,
        )
        td_output = f"{td_result.stdout}{td_result.stderr}"
        if td_result.returncode != 0:
            raise RuntimeError(
                f"`td` exited with code {td_result.returncode}: {_summarize_output(td_output)}"
            )
        if any(marker in td_output for marker in TD_ERROR_MARKERS):
            raise RuntimeError(f"`td` reported an execution error: {_summarize_output(td_output)}")
        if not ps_path.exists():
            raise FileNotFoundError(
                f"`td` did not produce the expected PostScript output: {ps_path}"
            )

        gs_result = subprocess.run(
            [
                str(gs_executable),
                "-dSAFER",
                "-dBATCH",
                "-dNOPAUSE",
                "-sDEVICE=pngalpha",
                "-r144",
                f"-sOutputFile={resolved_output}",
                str(ps_path),
            ],
            cwd=workdir,
            capture_output=True,
            text=True,
            check=False,
        )
        gs_output = f"{gs_result.stdout}{gs_result.stderr}"
        if gs_result.returncode != 0:
            raise RuntimeError(
                f"`gs` exited with code {gs_result.returncode}: {_summarize_output(gs_output)}"
            )
        if not resolved_output.exists():
            raise FileNotFoundError(
                f"`gs` did not produce the expected PNG output: {resolved_output}"
            )

    summary = _summarize_output(td_result.stdout)
    message = "Rendered PNG successfully."
    if summary:
        message = f"{message} {summary}"

    return RenderResult(
        output_path=str(resolved_output),
        td_executable=str(td_executable),
        success=True,
        message=message,
    )


def _summarize_output(output: str) -> str:
    """Return the first non-empty line from process output."""
    for line in output.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""
