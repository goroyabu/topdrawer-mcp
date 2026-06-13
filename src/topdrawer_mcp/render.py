from __future__ import annotations

import os
import re
import shutil
import shlex
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Literal
from typing import TypedDict

from topdrawer_mcp.artifacts import get_artifact_manager


TD_EXECUTABLE_ENV = "TD_EXECUTABLE_PATH"
GS_EXECUTABLE_ENV = "GS_EXECUTABLE_PATH"
TD_PS_FILENAME = "render.ps"
TD_WRAPPER_FILENAME = "render.top"
TD_ERROR_MARKERS = ("*** ERROR ***", "ERROR FOUND BY THE UNIFIED GRAPHICS SYSTEM")
GS_RENDER_DPI = 160
GS_PADDING_POINTS = 12
SET_DEVICE_PATTERN = re.compile(r"^\s*set\s+device\b", re.IGNORECASE)

SUPPORTED_POSTSCRIPT_DEVICES = {"POSTSCRIPT"}
DEVICE_NAMES = (
    "TEST",
    "CALCOMP",
    "PRINTRONIX",
    "QMS-1200",
    "EXCL",
    "REGIS",
    "SIXEL",
    "SIXELS",
    "TEKTRONIX",
    "VERSATEK",
    "VERSATEC",
    "TEKEMUL",
    "TEK4027",
    "GKS",
    "GRINNELL",
    "IMAGEN",
    "POSTSCRIPT",
    "GPOSTSCRIPT",
    "EPS",
    "HPGL",
    "XWINDOW",
    "XWINDOWS",
)
DEVICE_ALIASES = {
    "POSTSCR": "POSTSCRIPT",
    "POSTSCRIPT": "POSTSCRIPT",
    "XWINDOW": "XWINDOW",
    "XWINDOWS": "XWINDOW",
    "VERSATEK": "VERSATEK",
    "VERSATEC": "VERSATEK",
    "SIXEL": "SIXEL",
    "SIXELS": "SIXEL",
}
SET_DEVICE_KEYWORDS = (
    "ORIENTATION",
    "LANDSCAPE",
    "PORTRAIT",
    "COLOR",
    "FILE",
    "OUTPUT",
    "DDNAME",
    "CHANNEL",
    "INTERACTIVE",
    "SEQUENTIAL",
    "SLAVE",
    "ADD",
    "UNIT",
    "IDENT",
    "NUMBER",
    "PERMANENT",
    "WIDTH",
    "HEIGHT",
    "REVERSE",
    "SIDEWAYS",
    "ROTATED",
)
PNG_BACKGROUND_DEVICES = {
    "white": "png16m",
    "transparent": "png16malpha",
}


class RenderMetadata(TypedDict, total=False):
    """Optional execution metadata returned by render/output tools."""

    source_kind: str
    normalized_device_config: dict[str, Any]
    dpi: int
    background: str
    crop_applied: bool
    output_path_overridden: bool
    output_path: str
    intermediate_postscript_path: str


class RenderResult(TypedDict):
    """Structured success result returned by render/output MCP tools."""

    success: bool
    format: str
    message: str
    artifact_id: str
    resource_uri: str
    metadata: RenderMetadata


@dataclass
class SourceInput:
    """Normalized render/output input information."""

    source_text: str
    base_dir: Path
    source_kind: Literal["input_path", "script"]


@dataclass
class ParsedSetDevice:
    """Parsed `SET DEVICE` configuration from one script line."""

    original_line: str
    device: str
    orientation: int | None = None
    orientation_keyword: str | None = None
    page_orientation: str | None = None
    color: bool | None = None
    output_key: str | None = None
    output_value: str | None = None
    width: str | None = None
    height: str | None = None
    reverse: bool = False
    sequential: bool = False
    interactive: bool = False
    slave: bool = False
    add: bool = False
    unit: str | None = None
    ident: str | None = None
    number: str | None = None
    permanent: bool = False
    channel: str | None = None
    option_tokens: list[str] | None = None
    unknown_options: dict[str, str] | None = None


class PolicyError(ValueError):
    """Raised when parsed `SET DEVICE` syntax is unsupported by a tool."""


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
            "Unable to find `td` on PATH. Set TD_EXECUTABLE_PATH or install td. "
            "You can inspect the current runtime with get_server_runtime_info."
        )
    return Path(resolved).resolve()


def resolve_gs_executable() -> Path:
    """Resolve the Ghostscript executable from the environment or PATH."""
    configured = os.environ.get(GS_EXECUTABLE_ENV)
    if configured:
        candidate = Path(configured).expanduser()
        if not candidate.is_file():
            raise FileNotFoundError(
                f"{GS_EXECUTABLE_ENV} points to a missing file: {candidate}"
            )
        if not os.access(candidate, os.X_OK):
            raise PermissionError(
                f"{GS_EXECUTABLE_ENV} points to a non-executable file: {candidate}"
            )
        return candidate.resolve()

    resolved = shutil.which("gs")
    if resolved is None:
        raise FileNotFoundError(
            "Unable to find `gs` on PATH. Set GS_EXECUTABLE_PATH or install Ghostscript to convert PostScript to PNG. "
            "You can inspect the current runtime with get_server_runtime_info."
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


def resolve_output_path(output_path: str | None, *, default_filename: str) -> Path:
    """Resolve an output path or allocate a temp output path."""
    if output_path is None:
        directory = Path(tempfile.mkdtemp(prefix="topdrawer-mcp-render-out-"))
        return (directory / default_filename).resolve()

    candidate = Path(output_path).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    return candidate.resolve()


def resolve_base_dir(base_dir: str | None) -> Path:
    """Resolve the base directory used for relative paths inside a script."""
    if base_dir is None:
        return Path.cwd().resolve()

    candidate = Path(base_dir).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    resolved = candidate.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Base directory does not exist: {resolved}")
    if not resolved.is_dir():
        raise NotADirectoryError(f"Base directory is not a directory: {resolved}")
    return resolved


def resolve_source_input(
    *,
    input_path: str | None = None,
    script: str | None = None,
    base_dir: str | None = None,
) -> SourceInput:
    """Validate and normalize one render/output input source."""
    has_input_path = bool(input_path and input_path.strip())
    has_script = bool(script and script.strip())
    if has_input_path == has_script:
        raise ValueError("input validation error: provide exactly one of input_path or script")

    if has_input_path:
        resolved_input = resolve_input_path(input_path or "")
        return SourceInput(
            source_text=resolved_input.read_text(encoding="utf-8", errors="replace"),
            base_dir=resolved_input.parent.resolve(),
            source_kind="input_path",
        )

    assert script is not None
    return SourceInput(
        source_text=script,
        base_dir=resolve_base_dir(base_dir),
        source_kind="script",
    )


def build_wrapper_text(source_text: str, ps_filename: str = TD_PS_FILENAME) -> str:
    """Prepend a PostScript output directive to the original Topdrawer input."""
    normalized = source_text
    if normalized and not normalized.endswith("\n"):
        normalized += "\n"
    return f"SET DEVICE POSTSCR FILE='{ps_filename}'\n{normalized}"


def find_set_device_lines(source_text: str) -> list[tuple[int, str]]:
    """Return all lines that begin with `SET DEVICE`."""
    lines: list[tuple[int, str]] = []
    for line_number, line in enumerate(source_text.splitlines(), start=1):
        if line.lstrip().startswith("//"):
            continue
        if SET_DEVICE_PATTERN.match(line):
            lines.append((line_number, line))
    return lines


def _canonicalize_device(token: str) -> str:
    upper = token.strip().upper()
    if upper in DEVICE_ALIASES:
        return DEVICE_ALIASES[upper]
    matches = [name for name in DEVICE_NAMES if name.startswith(upper)]
    unique_matches = {DEVICE_ALIASES.get(name, name) for name in matches}
    if len(unique_matches) == 1:
        return unique_matches.pop()
    raise ValueError(f"unknown SET DEVICE name: {token!r}")


def _canonicalize_keyword(token: str) -> str:
    upper = token.strip().upper()
    matches = [name for name in SET_DEVICE_KEYWORDS if name.startswith(upper)]
    if len(matches) == 1:
        return matches[0]
    raise ValueError(f"unknown SET DEVICE option: {token!r}")


def parse_set_device_line(line: str) -> ParsedSetDevice:
    """Parse one `SET DEVICE` line into a normalized internal form."""
    try:
        tokens = shlex.split(line, posix=True)
    except ValueError as exc:
        raise ValueError(f"parse error for invalid SET DEVICE syntax: {exc}") from exc

    if len(tokens) < 3 or tokens[0].upper() != "SET" or tokens[1].upper() != "DEVICE":
        raise ValueError("parse error for invalid SET DEVICE syntax: expected `SET DEVICE ...`")

    parsed = ParsedSetDevice(original_line=line, device=_canonicalize_device(tokens[2]))

    for token in tokens[3:]:
        if "=" in token:
            key, value = token.split("=", 1)
            try:
                keyword = _canonicalize_keyword(key)
            except ValueError:
                if parsed.unknown_options is None:
                    parsed.unknown_options = {}
                parsed.unknown_options[key.upper()] = value
                continue
            if keyword == "ORIENTATION":
                try:
                    parsed.orientation = int(value)
                except ValueError as exc:
                    raise ValueError(
                        "parse error for invalid SET DEVICE syntax: ORIENTATION must be an integer"
                    ) from exc
                if parsed.orientation not in {0, 1, 2, 3}:
                    raise ValueError(
                        "parse error for invalid SET DEVICE syntax: ORIENTATION must be 0..3"
                    )
                parsed.orientation_keyword = "ORIENTATION"
            elif keyword == "COLOR":
                normalized = value.strip().upper()
                if normalized not in {"ON", "OFF"}:
                    raise ValueError(
                        "parse error for invalid SET DEVICE syntax: COLOR must be ON or OFF"
                    )
                parsed.color = normalized == "ON"
            elif keyword in {"FILE", "OUTPUT", "DDNAME"}:
                parsed.output_key = keyword
                parsed.output_value = value
            elif keyword == "CHANNEL":
                parsed.channel = value
            elif keyword == "UNIT":
                parsed.unit = value
            elif keyword == "IDENT":
                parsed.ident = value
            elif keyword == "NUMBER":
                parsed.number = value
            elif keyword == "WIDTH":
                parsed.width = value
            elif keyword == "HEIGHT":
                parsed.height = value
            else:
                raise ValueError(
                    f"parse error for invalid SET DEVICE syntax: unsupported key/value option {keyword!r}"
                )
            continue

        try:
            keyword = _canonicalize_keyword(token)
        except ValueError:
            if parsed.option_tokens is None:
                parsed.option_tokens = []
            parsed.option_tokens.append(token)
            continue

        if keyword == "LANDSCAPE":
            parsed.page_orientation = "LANDSCAPE"
        elif keyword == "PORTRAIT":
            parsed.page_orientation = "PORTRAIT"
        elif keyword == "COLOR":
            parsed.color = True
        elif keyword == "REVERSE":
            parsed.reverse = True
        elif keyword == "SEQUENTIAL":
            parsed.sequential = True
        elif keyword == "INTERACTIVE":
            parsed.interactive = True
        elif keyword == "SLAVE":
            parsed.slave = True
        elif keyword == "ADD":
            parsed.add = True
        elif keyword == "PERMANENT":
            parsed.permanent = True
        elif keyword in {"SIDEWAYS", "ROTATED"}:
            parsed.orientation = 1
            parsed.orientation_keyword = keyword
        else:
            raise ValueError(
                f"parse error for invalid SET DEVICE syntax: unsupported token {keyword!r}"
            )

    return parsed


def validate_set_device_policy(parsed: ParsedSetDevice, *, output_format: str) -> None:
    """Validate parsed `SET DEVICE` usage against current tool policy."""
    if parsed.device not in SUPPORTED_POSTSCRIPT_DEVICES:
        raise PolicyError(
            f"unsupported device error: {parsed.device!r} is valid Topdrawer syntax but unsupported by generate_topdrawer_{output_format}"
        )
    if parsed.option_tokens:
        raise PolicyError(
            "unsupported option or mode error: device option strings are valid Topdrawer syntax but unsupported by current output tools"
        )
    if parsed.unknown_options:
        raise PolicyError(
            "unsupported option or mode error: unrecognized SET DEVICE options are unsupported by current output tools"
        )
    if parsed.interactive or parsed.slave or parsed.add or parsed.unit is not None:
        raise PolicyError(
            "unsupported option or mode error: interactive, slave, and multi-device SET DEVICE modes are unsupported by current output tools"
        )
    if parsed.channel is not None:
        raise PolicyError(
            "unsupported option or mode error: CHANNEL routing is unsupported by current output tools"
        )
    if parsed.ident is not None or parsed.number is not None or parsed.permanent:
        raise PolicyError(
            "unsupported option or mode error: IDENT, NUMBER, and PERMANENT are unsupported by current output tools"
        )


def normalize_execution_device_config(
    source_text: str,
    *,
    output_format: str,
    execution_output_path: Path,
) -> tuple[ParsedSetDevice, bool]:
    """Build the effective execution-time device config for one source script."""
    set_device_lines = find_set_device_lines(source_text)
    if len(set_device_lines) > 1:
        raise PolicyError(
            "unsupported option or mode error: multiple SET DEVICE commands are unsupported by current output tools"
        )

    output_path_overridden = False
    if not set_device_lines:
        parsed = ParsedSetDevice(original_line="", device="POSTSCRIPT")
    else:
        _, line = set_device_lines[0]
        parsed = parse_set_device_line(line)
        validate_set_device_policy(parsed, output_format=output_format)
        if parsed.output_key is not None or parsed.channel is not None:
            output_path_overridden = True

    parsed.output_key = "FILE"
    parsed.output_value = str(execution_output_path)
    return parsed, output_path_overridden


def build_set_device_line(parsed: ParsedSetDevice) -> str:
    """Return a canonical execution-time `SET DEVICE` line."""
    parts = ["SET DEVICE", parsed.device]
    if parsed.orientation_keyword == "ORIENTATION" and parsed.orientation is not None:
        parts.append(f"ORIENTATION={parsed.orientation}")
    elif parsed.orientation_keyword in {"SIDEWAYS", "ROTATED"}:
        parts.append(parsed.orientation_keyword)
    if parsed.page_orientation:
        parts.append(parsed.page_orientation)
    if parsed.color is True:
        parts.append("COLOR=ON")
    elif parsed.color is False:
        parts.append("COLOR=OFF")
    if parsed.width is not None:
        parts.append(f"WIDTH={parsed.width}")
    if parsed.height is not None:
        parts.append(f"HEIGHT={parsed.height}")
    if parsed.reverse:
        parts.append("REVERSE")
    if parsed.sequential:
        parts.append("SEQUENTIAL")
    if parsed.output_value is not None:
        parts.append(f"FILE='{parsed.output_value}'")
    return " ".join(parts)


def build_execution_source_text(source_text: str, parsed: ParsedSetDevice) -> str:
    """Rewrite script text with one canonical execution-time `SET DEVICE` line."""
    set_device_line = build_set_device_line(parsed)
    kept_lines = [line for line in source_text.splitlines() if not SET_DEVICE_PATTERN.match(line)]
    rebuilt = "\n".join([set_device_line, *kept_lines])
    if rebuilt and not rebuilt.endswith("\n"):
        rebuilt += "\n"
    return rebuilt


def read_postscript_bbox(ps_path: Path, gs_executable: Path) -> tuple[int, int, int, int]:
    """Read the PostScript bounding box via Ghostscript's bbox device."""
    bbox_result = subprocess.run(
        [
            str(gs_executable),
            "-q",
            "-dSAFER",
            "-dNOPAUSE",
            "-dBATCH",
            "-sDEVICE=bbox",
            str(ps_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    bbox_output = f"{bbox_result.stdout}{bbox_result.stderr}"
    if bbox_result.returncode != 0:
        raise RuntimeError(
            "Ghostscript bounding-box read failure: "
            f"`gs` bbox exited with code {bbox_result.returncode}: {bbox_output.strip()}"
        )

    for line in bbox_output.splitlines():
        if line.startswith("%%BoundingBox:"):
            parts = line.split()
            if len(parts) == 5:
                return tuple(int(value) for value in parts[1:5])

    raise RuntimeError(
        "Ghostscript bounding-box read failure: `gs` bbox did not report a BoundingBox"
    )


def build_gs_png_command(
    gs_executable: Path,
    ps_path: Path,
    output_path: Path,
    *,
    background: Literal["white", "transparent"] = "white",
    crop: bool = True,
    bbox: tuple[int, int, int, int] | None = None,
    padding_points: int = GS_PADDING_POINTS,
    resolution_dpi: int = GS_RENDER_DPI,
) -> list[str]:
    """Build the Ghostscript command for PNG output."""
    device_name = PNG_BACKGROUND_DEVICES[background]
    command = [
        str(gs_executable),
        "-q",
        "-dSAFER",
        "-dBATCH",
        "-dNOPAUSE",
        f"-sDEVICE={device_name}",
        f"-r{resolution_dpi}",
        f"-sOutputFile={output_path}",
    ]
    if crop:
        if bbox is None:
            raise ValueError("crop=true requires a BoundingBox")
        llx, lly, urx, ury = bbox
        width = urx - llx + padding_points * 2
        height = ury - lly + padding_points * 2
        tx = padding_points - llx
        ty = padding_points - lly
        command.extend(
            [
                f"-dDEVICEWIDTHPOINTS={width}",
                f"-dDEVICEHEIGHTPOINTS={height}",
                "-dFIXEDMEDIA",
                "-c",
                f"{tx} {ty} translate",
            ]
        )
    command.extend(["-f", str(ps_path)])
    return command


def _normalized_device_config_metadata(parsed: ParsedSetDevice) -> dict[str, Any]:
    """Return metadata for the normalized execution-time device config."""
    data: dict[str, Any] = {
        "device": parsed.device,
        "output_key": parsed.output_key,
        "output_value": parsed.output_value,
    }
    if parsed.orientation is not None:
        data["orientation"] = parsed.orientation
    if parsed.orientation_keyword is not None:
        data["orientation_keyword"] = parsed.orientation_keyword
    if parsed.page_orientation is not None:
        data["page_orientation"] = parsed.page_orientation
    if parsed.color is not None:
        data["color"] = parsed.color
    if parsed.width is not None:
        data["width"] = parsed.width
    if parsed.height is not None:
        data["height"] = parsed.height
    if parsed.reverse:
        data["reverse"] = True
    if parsed.sequential:
        data["sequential"] = True
    if parsed.option_tokens:
        data["option_tokens"] = parsed.option_tokens
    if parsed.unknown_options:
        data["unknown_options"] = dict(parsed.unknown_options)
    return data


def _run_td_to_postscript(
    source_text: str,
    *,
    base_dir: Path,
    output_path: Path,
    output_format: str,
) -> tuple[Path, str, bool, str, ParsedSetDevice]:
    """Run Topdrawer to produce PostScript at `output_path`."""
    td_executable = resolve_td_executable()
    with tempfile.TemporaryDirectory(prefix="topdrawer-mcp-render-work-") as workdir_text:
        workdir = Path(workdir_text)
        wrapper_path = workdir / TD_WRAPPER_FILENAME
        parsed_device, output_path_overridden = normalize_execution_device_config(
            source_text,
            output_format=output_format,
            execution_output_path=output_path,
        )
        execution_source_text = build_execution_source_text(source_text, parsed_device)
        wrapper_path.write_text(
            execution_source_text,
            encoding="utf-8",
        )
        td_result = subprocess.run(
            [str(td_executable), str(wrapper_path)],
            cwd=base_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        td_output = f"{td_result.stdout}{td_result.stderr}"
        if td_result.returncode != 0:
            raise RuntimeError(
                f"Topdrawer execution error: `td` exited with code {td_result.returncode}: {td_output.strip()}"
            )
        if any(marker in td_output for marker in TD_ERROR_MARKERS):
            raise RuntimeError(
                f"Topdrawer execution error: `td` reported an execution error: {td_output.strip()}"
            )
        if not output_path.exists():
            raise FileNotFoundError(
                f"missing PostScript artifact: `td` did not produce the expected PostScript output: {output_path}"
            )
    return output_path, str(td_executable), output_path_overridden, execution_source_text, parsed_device


def generate_topdrawer_postscript(
    *,
    input_path: str | None = None,
    script: str | None = None,
    base_dir: str | None = None,
    output_path: str | None = None,
    overwrite: bool = False,
) -> RenderResult:
    """Generate PostScript output from Topdrawer input."""
    source = resolve_source_input(input_path=input_path, script=script, base_dir=base_dir)
    resolved_output = resolve_output_path(output_path, default_filename="render.ps")
    if resolved_output.exists() and not overwrite:
        raise FileExistsError(
            f"Output file already exists: {resolved_output}. Pass overwrite=True to replace it."
        )
    resolved_output.parent.mkdir(parents=True, exist_ok=True)

    generated_path, _, output_path_overridden, execution_source_text, parsed_device = _run_td_to_postscript(
        source.source_text,
        base_dir=source.base_dir,
        output_path=resolved_output,
        output_format="postscript",
    )
    artifact = get_artifact_manager().create_artifact(
        output_file=generated_path,
        format="postscript",
        output_mime_type="application/postscript",
        source_text=execution_source_text,
        source_kind=source.source_kind,
        metadata={
            "source_kind": source.source_kind,
            "output_path_overridden": output_path_overridden,
            "normalized_device_config": _normalized_device_config_metadata(parsed_device),
            **({"output_path": str(resolved_output)} if output_path is not None else {}),
        },
    )
    metadata: RenderMetadata = {
        "source_kind": source.source_kind,
        "output_path_overridden": output_path_overridden,
        "normalized_device_config": _normalized_device_config_metadata(parsed_device),
        **({"output_path": str(resolved_output)} if output_path is not None else {}),
    }
    return RenderResult(
        success=True,
        format="postscript",
        message="Generated PostScript successfully.",
        artifact_id=artifact.artifact_id,
        resource_uri=artifact.resource_uri,
        metadata=metadata,
    )


def generate_topdrawer_png(
    *,
    input_path: str | None = None,
    script: str | None = None,
    base_dir: str | None = None,
    output_path: str | None = None,
    overwrite: bool = False,
    dpi: int = GS_RENDER_DPI,
    padding: int = GS_PADDING_POINTS,
    crop: bool = True,
    background: Literal["white", "transparent"] = "white",
) -> RenderResult:
    """Generate PNG output from Topdrawer input."""
    if background not in PNG_BACKGROUND_DEVICES:
        raise ValueError(
            "input validation error: background must be one of 'white' or 'transparent'"
        )
    source = resolve_source_input(input_path=input_path, script=script, base_dir=base_dir)
    resolved_output = resolve_output_path(output_path, default_filename="render.png")
    if resolved_output.exists() and not overwrite:
        raise FileExistsError(
            f"Output file already exists: {resolved_output}. Pass overwrite=True to replace it."
        )
    resolved_output.parent.mkdir(parents=True, exist_ok=True)

    gs_executable = resolve_gs_executable()
    with tempfile.TemporaryDirectory(prefix="topdrawer-mcp-render-ps-") as ps_dir_text:
        ps_output = Path(ps_dir_text) / TD_PS_FILENAME
        generated_ps, _, output_path_overridden, execution_source_text, parsed_device = _run_td_to_postscript(
            source.source_text,
            base_dir=source.base_dir,
            output_path=ps_output,
            output_format="png",
        )
        bbox = read_postscript_bbox(generated_ps, gs_executable) if crop else None
        gs_result = subprocess.run(
            build_gs_png_command(
                gs_executable,
                generated_ps,
                resolved_output,
                background=background,
                crop=crop,
                bbox=bbox,
                padding_points=padding,
                resolution_dpi=dpi,
            ),
            capture_output=True,
            text=True,
            check=False,
        )
        gs_output = f"{gs_result.stdout}{gs_result.stderr}"
        if gs_result.returncode != 0:
            raise RuntimeError(
                f"Ghostscript raster render failure: `gs` exited with code {gs_result.returncode}: {gs_output.strip()}"
            )
        if not resolved_output.exists():
            raise FileNotFoundError(
                "final PNG artifact missing after Ghostscript reported success: "
                f"{resolved_output}"
            )
        artifact = get_artifact_manager().create_artifact(
            output_file=resolved_output,
            format="png",
            output_mime_type="image/png",
            source_text=execution_source_text,
            source_kind=source.source_kind,
            metadata={
                "source_kind": source.source_kind,
                "dpi": dpi,
                "background": background,
                "crop_applied": crop,
                "output_path_overridden": output_path_overridden,
                "normalized_device_config": _normalized_device_config_metadata(parsed_device),
                **({"output_path": str(resolved_output)} if output_path is not None else {}),
                "intermediate_postscript_path": str(generated_ps),
            },
        )

    metadata: RenderMetadata = {
        "source_kind": source.source_kind,
        "dpi": dpi,
        "background": background,
        "crop_applied": crop,
        "output_path_overridden": output_path_overridden,
        "normalized_device_config": _normalized_device_config_metadata(parsed_device),
        **({"output_path": str(resolved_output)} if output_path is not None else {}),
        "intermediate_postscript_path": str(generated_ps),
    }
    return RenderResult(
        success=True,
        format="png",
        message="Generated PNG successfully.",
        artifact_id=artifact.artifact_id,
        resource_uri=artifact.resource_uri,
        metadata=metadata,
    )


def render_topdrawer_source_text(
    source_text: str,
    *,
    base_dir: str | None = None,
    output_path: str | None = None,
    overwrite: bool = False,
) -> RenderResult:
    """Compatibility wrapper that renders Topdrawer source text into PNG."""
    return generate_topdrawer_png(
        script=source_text,
        base_dir=base_dir,
        output_path=output_path,
        overwrite=overwrite,
    )


def render_topdrawer_input(
    input_path: str,
    output_path: str | None = None,
    overwrite: bool = False,
) -> RenderResult:
    """Compatibility wrapper that renders an existing Topdrawer input file into PNG."""
    return generate_topdrawer_png(
        input_path=input_path,
        output_path=output_path,
        overwrite=overwrite,
    )


def _summarize_output(output: str) -> str:
    """Return the first non-empty line from process output."""
    for line in output.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""
