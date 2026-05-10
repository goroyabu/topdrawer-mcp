from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from .commands import extract_command_entries
from .lookup import build_command_lookup_entries
from .lookup import load_command_lookup_targets
from .lookup import load_reviewed_command_lookup_entries
from .sources import DEFAULT_INDEX_DIR, read_source_text, resolve_doc_source_path
from .sources import DEFAULT_LOOKUP_REVIEWED_PATH
from .sources import DEFAULT_LOOKUP_TARGETS_PATH
from .writer import write_command_index
from .writer import write_command_lookup_index


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="topdrawer-mcp-preprocess",
        description="Generate local indexes from Topdrawer manual sources.",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Path to topdrawer.doc. Defaults to TOPDRAWER_DOC_SOURCE_PATH or data/raw/topdrawer.doc.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_INDEX_DIR,
        help="Directory for generated indexes. Defaults to data/index.",
    )
    parser.add_argument(
        "--lookup-targets",
        type=Path,
        default=DEFAULT_LOOKUP_TARGETS_PATH,
        help="Path to reviewed command lookup targets JSON. Defaults to data/lookup/command-lookup-targets.json.",
    )
    parser.add_argument(
        "--lookup-reviewed",
        type=Path,
        default=DEFAULT_LOOKUP_REVIEWED_PATH,
        help="Path to reviewed command lookup metadata JSON. Defaults to data/lookup/command-lookup-reviewed.json.",
    )
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    """Run preprocessing and return a process-style exit code."""
    args = _parser().parse_args(argv)
    source_path = resolve_doc_source_path(args.source)
    source_text = read_source_text(source_path)
    entries = extract_command_entries(source_text)
    output_path = write_command_index(
        output_dir=args.output_dir,
        source_name=source_path.name,
        entries=entries,
    )
    lookup_targets = load_command_lookup_targets(args.lookup_targets)
    lookup_reviewed = load_reviewed_command_lookup_entries(args.lookup_reviewed)
    lookup_entries = build_command_lookup_entries(
        source_text=source_text,
        targets=lookup_targets,
        reviewed_entries=lookup_reviewed,
    )
    lookup_output_path = write_command_lookup_index(
        output_dir=args.output_dir,
        source_name=source_path.name,
        entries=lookup_entries,
    )
    print(f"Wrote {len(entries)} command entries to {output_path}")
    print(f"Wrote {len(lookup_entries)} command lookup entries to {lookup_output_path}")
    return 0


def main() -> None:
    """Console script entrypoint."""
    raise SystemExit(run())
