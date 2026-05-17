from __future__ import annotations

import os
from pathlib import Path
from typing import Literal
from typing import TypedDict

from topdrawer_mcp.command_lookup import DEFAULT_COMMAND_LOOKUP_MANUAL_PATH
from topdrawer_mcp.preprocess.sources import DEFAULT_LOOKUP_REVIEWED_PATH
from topdrawer_mcp.preprocess.sources import DEFAULT_LOOKUP_TARGETS_PATH
from topdrawer_mcp.render import GS_EXECUTABLE_ENV
from topdrawer_mcp.render import TD_EXECUTABLE_ENV
from topdrawer_mcp.render import resolve_gs_executable
from topdrawer_mcp.render import resolve_td_executable


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_MANUAL_PATH = ROOT_DIR / "data" / "topdrawer.txt"
TOPDRAWER_MANUAL_ENV = "TOPDRAWER_MANUAL_PATH"


class ManualRuntimeInfo(TypedDict):
    """Resolved manual-search runtime source."""

    env_var: str
    configured_path: str | None
    resolved_path: str
    exists: bool
    source: Literal["env", "default"]
    error: str | None
    user_action: list[str]


class LookupSourceInfo(TypedDict):
    """One tracked source used to build command lookup data."""

    name: str
    path: str
    exists: bool


class ExecutableRuntimeInfo(TypedDict):
    """Resolved executable status for one external binary."""

    env_var: str
    configured_path: str | None
    resolved_path: str | None
    available: bool
    error: str | None


class RenderRuntimeInfo(TypedDict):
    """Runtime render dependency status."""

    available: bool
    td: ExecutableRuntimeInfo
    gs: ExecutableRuntimeInfo
    missing_requirements: list[str]
    user_action: list[str]


class RuntimeInfoResult(TypedDict):
    """Structured runtime/config inspection payload."""

    manual: ManualRuntimeInfo
    command_lookup_sources: list[LookupSourceInfo]
    render: RenderRuntimeInfo


def get_runtime_info() -> RuntimeInfoResult:
    """Return read-only runtime/config inspection information."""
    td_info = _resolve_executable_info(TD_EXECUTABLE_ENV, resolve_td_executable)
    gs_info = _resolve_executable_info(GS_EXECUTABLE_ENV, resolve_gs_executable)
    missing_requirements = [
        name
        for name, info in (("td", td_info), ("gs", gs_info))
        if not info["available"]
    ]

    return {
        "manual": _manual_runtime_info(),
        "command_lookup_sources": _command_lookup_source_info(),
        "render": {
            "available": td_info["available"] and gs_info["available"],
            "td": td_info,
            "gs": gs_info,
            "missing_requirements": missing_requirements,
            "user_action": _render_user_action(td_info, gs_info),
        },
    }


def _manual_runtime_info() -> ManualRuntimeInfo:
    configured = os.environ.get(TOPDRAWER_MANUAL_ENV)
    source: Literal["env", "default"] = "env" if configured else "default"
    resolved = Path(configured).expanduser() if configured else DEFAULT_MANUAL_PATH
    exists = resolved.exists()
    error = None if exists else f"Manual file does not exist: {resolved.resolve(strict=False)}"
    return {
        "env_var": TOPDRAWER_MANUAL_ENV,
        "configured_path": configured,
        "resolved_path": str(resolved.resolve(strict=False)),
        "exists": exists,
        "source": source,
        "error": error,
        "user_action": _manual_user_action(resolved, configured, exists),
    }


def _command_lookup_source_info() -> list[LookupSourceInfo]:
    sources = [
        ("manual", DEFAULT_COMMAND_LOOKUP_MANUAL_PATH),
        ("targets", DEFAULT_LOOKUP_TARGETS_PATH),
        ("reviewed", DEFAULT_LOOKUP_REVIEWED_PATH),
    ]
    return [
        {
            "name": name,
            "path": str(path.resolve(strict=False)),
            "exists": path.exists(),
        }
        for name, path in sources
    ]


def _resolve_executable_info(
    env_var: str,
    resolver: callable,
) -> ExecutableRuntimeInfo:
    configured = os.environ.get(env_var)
    try:
        resolved = resolver()
    except (FileNotFoundError, PermissionError) as exc:
        return {
            "env_var": env_var,
            "configured_path": configured,
            "resolved_path": None,
            "available": False,
            "error": str(exc),
        }

    return {
        "env_var": env_var,
        "configured_path": configured,
        "resolved_path": str(resolved),
        "available": True,
        "error": None,
    }


def _manual_user_action(
    resolved: Path,
    configured: str | None,
    exists: bool,
) -> list[str]:
    if exists:
        return []
    if configured:
        return [
            f"Update {TOPDRAWER_MANUAL_ENV} in the MCP client env to point at an existing manual file.",
            "You can inspect the current runtime with get_server_runtime_info.",
        ]
    return [
        f"Set {TOPDRAWER_MANUAL_ENV} in the MCP client env, or add the manual at {resolved.resolve(strict=False)}.",
        "You can inspect the current runtime with get_server_runtime_info.",
    ]


def _render_user_action(
    td_info: ExecutableRuntimeInfo,
    gs_info: ExecutableRuntimeInfo,
) -> list[str]:
    actions: list[str] = []
    if not td_info["available"]:
        actions.append(
            f"Set {TD_EXECUTABLE_ENV} in the MCP client env, or install td on PATH."
        )
    if not gs_info["available"]:
        actions.append(
            f"Set {GS_EXECUTABLE_ENV} in the MCP client env, or install gs on PATH."
        )
    if actions:
        actions.append("You can inspect the current runtime with get_server_runtime_info.")
    return actions
