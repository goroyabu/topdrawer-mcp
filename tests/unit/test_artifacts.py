from __future__ import annotations

import json
from pathlib import Path

import pytest

from topdrawer_mcp import artifacts


pytestmark = pytest.mark.unit


def _make_manager(tmp_path: Path, ttl_seconds: int = 3600, max_bytes: int = 1024 * 1024, max_count: int = 10):
    return artifacts.ArtifactManager(
        tmp_path / "artifacts",
        ttl_seconds=ttl_seconds,
        max_bytes=max_bytes,
        max_count=max_count,
    )


def test_create_artifact_writes_bundle_files(tmp_path: Path):
    manager = _make_manager(tmp_path)
    output_file = tmp_path / "output.png"
    output_file.write_bytes(b"\x89PNG\r\n\x1a\n")

    record = manager.create_artifact(
        output_file=output_file,
        format="png",
        output_mime_type="image/png",
        source_text="plot\n",
        source_kind="script",
        metadata={"dpi": 160},
    )

    artifact_dir = manager.root_dir / record.artifact_id
    assert (artifact_dir / "output.png").exists()
    assert (artifact_dir / "source.top").read_text(encoding="utf-8") == "plot\n"
    metadata = json.loads((artifact_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["artifact_id"] == record.artifact_id
    assert metadata["output_mime_type"] == "image/png"


def test_read_manifest_returns_resource_links(tmp_path: Path):
    manager = _make_manager(tmp_path)
    output_file = tmp_path / "output.ps"
    output_file.write_text("%!PS-Adobe-1.0\n", encoding="utf-8")

    record = manager.create_artifact(
        output_file=output_file,
        format="postscript",
        output_mime_type="application/postscript",
        source_text="plot\n",
        source_kind="script",
        metadata={},
    )

    manifest = manager.read_manifest(record.artifact_id)

    assert manifest["artifact_id"] == record.artifact_id
    assert manifest["output"] == f"resource://artifacts/{record.artifact_id}/output"
    assert manifest["source"] == f"resource://artifacts/{record.artifact_id}/source"
    assert manifest["metadata"] == f"resource://artifacts/{record.artifact_id}/metadata"


def test_read_output_returns_bytes_for_png(tmp_path: Path):
    manager = _make_manager(tmp_path)
    output_file = tmp_path / "output.png"
    output_file.write_bytes(b"\x89PNG\r\n\x1a\n")

    record = manager.create_artifact(
        output_file=output_file,
        format="png",
        output_mime_type="image/png",
        source_text="plot\n",
        source_kind="script",
        metadata={},
    )

    output = manager.read_output(record.artifact_id)

    assert isinstance(output, bytes)


def test_load_artifact_preserves_output_mime_type(tmp_path: Path):
    manager = _make_manager(tmp_path)
    output_file = tmp_path / "output.ps"
    output_file.write_text("%!PS-Adobe-1.0\n", encoding="utf-8")

    record = manager.create_artifact(
        output_file=output_file,
        format="postscript",
        output_mime_type="application/postscript",
        source_text="plot\n",
        source_kind="script",
        metadata={},
    )

    loaded = manager.load_artifact(record.artifact_id)

    assert loaded.output_mime_type == "application/postscript"


def test_read_source_returns_text(tmp_path: Path):
    manager = _make_manager(tmp_path)
    output_file = tmp_path / "output.ps"
    output_file.write_text("%!PS-Adobe-1.0\n", encoding="utf-8")

    record = manager.create_artifact(
        output_file=output_file,
        format="postscript",
        output_mime_type="application/postscript",
        source_text="plot\n",
        source_kind="script",
        metadata={},
    )

    assert manager.read_source(record.artifact_id) == "plot\n"


def test_cleanup_removes_expired_artifacts(tmp_path: Path):
    manager = _make_manager(tmp_path, ttl_seconds=3600)
    output_file = tmp_path / "output.ps"
    output_file.write_text("%!PS-Adobe-1.0\n", encoding="utf-8")

    record = manager.create_artifact(
        output_file=output_file,
        format="postscript",
        output_mime_type="application/postscript",
        source_text="plot\n",
        source_kind="script",
        metadata={},
    )

    metadata_path = manager.root_dir / record.artifact_id / "metadata.json"
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    payload["expires_at"] = "0"
    metadata_path.write_text(json.dumps(payload), encoding="utf-8")

    manager.cleanup()

    with pytest.raises(FileNotFoundError, match="artifact not found|artifact expired"):
        manager.load_artifact(record.artifact_id)


def test_cleanup_enforces_count_limit(tmp_path: Path):
    manager = _make_manager(tmp_path, max_count=1)
    one = tmp_path / "one.ps"
    two = tmp_path / "two.ps"
    one.write_text("%!PS-Adobe-1.0\n", encoding="utf-8")
    two.write_text("%!PS-Adobe-1.0\n", encoding="utf-8")

    first = manager.create_artifact(
        output_file=one,
        format="postscript",
        output_mime_type="application/postscript",
        source_text="one\n",
        source_kind="script",
        metadata={},
    )
    second = manager.create_artifact(
        output_file=two,
        format="postscript",
        output_mime_type="application/postscript",
        source_text="two\n",
        source_kind="script",
        metadata={},
    )

    with pytest.raises(FileNotFoundError, match="artifact not found|artifact expired"):
        manager.load_artifact(first.artifact_id)
    assert manager.load_artifact(second.artifact_id).artifact_id == second.artifact_id
