from __future__ import annotations

import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_DOC_SOURCE_PATH = ROOT_DIR / "data" / "raw" / "topdrawer.doc"
DEFAULT_INDEX_DIR = ROOT_DIR / "data" / "index"
DOC_SOURCE_ENV_VAR = "TOPDRAWER_DOC_SOURCE_PATH"


def resolve_doc_source_path(path: str | Path | None = None) -> Path:
    """Resolve the canonical Topdrawer .doc source path."""
    if path is not None:
        return Path(path)
    return Path(os.environ.get(DOC_SOURCE_ENV_VAR, DEFAULT_DOC_SOURCE_PATH))


def read_source_text(path: str | Path) -> str:
    """Read a source manual text file with replacement for undecodable bytes."""
    resolved = Path(path)
    try:
        return resolved.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise OSError(
            f"Unable to read Topdrawer source at {resolved}. "
            f"Provide --source or set {DOC_SOURCE_ENV_VAR}."
        ) from exc
