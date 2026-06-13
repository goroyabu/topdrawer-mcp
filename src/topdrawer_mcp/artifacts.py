from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from functools import cache
from pathlib import Path
from secrets import token_hex
from typing import Any


ARTIFACT_ROOT_ENV = "TOPDRAWER_ARTIFACT_ROOT"
ARTIFACT_TTL_SECONDS_ENV = "TOPDRAWER_ARTIFACT_TTL_SECONDS"
ARTIFACT_MAX_BYTES_ENV = "TOPDRAWER_ARTIFACT_MAX_BYTES"
ARTIFACT_MAX_COUNT_ENV = "TOPDRAWER_ARTIFACT_MAX_COUNT"
DEFAULT_ARTIFACT_TTL_SECONDS = 24 * 60 * 60
DEFAULT_ARTIFACT_MAX_BYTES = 256 * 1024 * 1024
DEFAULT_ARTIFACT_MAX_COUNT = 200


@dataclass
class ArtifactRecord:
    """Persistent metadata for one generated artifact bundle."""

    artifact_id: str
    format: str
    created_at: str
    last_accessed_at: str
    expires_at: str
    size_bytes: int
    source_kind: str
    resource_uri: str
    output_mime_type: str
    output_resource_uri: str
    source_resource_uri: str
    metadata_resource_uri: str
    output_filename: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "format": self.format,
            "created_at": self.created_at,
            "last_accessed_at": self.last_accessed_at,
            "expires_at": self.expires_at,
            "size_bytes": self.size_bytes,
            "source_kind": self.source_kind,
            "resource_uri": self.resource_uri,
            "output_mime_type": self.output_mime_type,
            "output_resource_uri": self.output_resource_uri,
            "source_resource_uri": self.source_resource_uri,
            "metadata_resource_uri": self.metadata_resource_uri,
            "output_filename": self.output_filename,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ArtifactRecord:
        return cls(
            artifact_id=payload["artifact_id"],
            format=payload["format"],
            created_at=payload["created_at"],
            last_accessed_at=payload["last_accessed_at"],
            expires_at=payload["expires_at"],
            size_bytes=int(payload["size_bytes"]),
            source_kind=payload["source_kind"],
            resource_uri=payload["resource_uri"],
            output_mime_type=payload["output_mime_type"],
            output_resource_uri=payload["output_resource_uri"],
            source_resource_uri=payload["source_resource_uri"],
            metadata_resource_uri=payload["metadata_resource_uri"],
            output_filename=payload["output_filename"],
            metadata=dict(payload.get("metadata", {})),
        )


class ArtifactManager:
    """Manage generated artifact bundles and expose them via MCP resources."""

    def __init__(
        self,
        root_dir: Path,
        *,
        ttl_seconds: int,
        max_bytes: int,
        max_count: int,
    ) -> None:
        self.root_dir = root_dir
        self.ttl_seconds = ttl_seconds
        self.max_bytes = max_bytes
        self.max_count = max_count
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.cleanup()

    def create_artifact(
        self,
        *,
        output_file: Path,
        format: str,
        output_mime_type: str,
        source_text: str,
        source_kind: str,
        metadata: dict[str, Any],
    ) -> ArtifactRecord:
        artifact_id = self._generate_artifact_id()
        artifact_dir = self.root_dir / artifact_id
        artifact_dir.mkdir(parents=True, exist_ok=False)

        output_filename = f"output{output_file.suffix.lower()}"
        stored_output_path = artifact_dir / output_filename
        stored_source_path = artifact_dir / "source.top"

        shutil.copy2(output_file, stored_output_path)
        stored_source_path.write_text(source_text, encoding="utf-8")

        now = _utc_now()
        record = ArtifactRecord(
            artifact_id=artifact_id,
            format=format,
            created_at=now,
            last_accessed_at=now,
            expires_at=_iso_after_seconds(self.ttl_seconds),
            size_bytes=_calculate_directory_size(artifact_dir),
            source_kind=source_kind,
            resource_uri=self.artifact_manifest_uri(artifact_id),
            output_mime_type=output_mime_type,
            output_resource_uri=self.artifact_output_uri(artifact_id),
            source_resource_uri=self.artifact_source_uri(artifact_id),
            metadata_resource_uri=self.artifact_metadata_uri(artifact_id),
            output_filename=output_filename,
            metadata=metadata,
        )
        self._write_record(artifact_dir, record)
        self.cleanup()
        return self.load_artifact(artifact_id)

    def cleanup(self) -> None:
        records = self._load_existing_records()
        now = _dt_utc_now()

        for record in records:
            if _parse_iso(record.expires_at) <= now:
                self._delete_artifact_dir(self.root_dir / record.artifact_id)

        records = self._load_existing_records()
        records.sort(key=lambda item: _parse_iso(item.last_accessed_at))

        while len(records) > self.max_count or sum(item.size_bytes for item in records) > self.max_bytes:
            oldest = records.pop(0)
            self._delete_artifact_dir(self.root_dir / oldest.artifact_id)
            records = self._load_existing_records()
            records.sort(key=lambda item: _parse_iso(item.last_accessed_at))

    def load_artifact(self, artifact_id: str) -> ArtifactRecord:
        artifact_dir = self.root_dir / artifact_id
        record_path = artifact_dir / "metadata.json"
        if not record_path.exists():
            raise FileNotFoundError(f"artifact not found: {artifact_id}")

        record = ArtifactRecord.from_dict(json.loads(record_path.read_text(encoding="utf-8")))
        if _parse_iso(record.expires_at) <= _dt_utc_now():
            self._delete_artifact_dir(artifact_dir)
            raise FileNotFoundError(f"artifact expired: {artifact_id}")
        return record

    def read_manifest(self, artifact_id: str) -> dict[str, Any]:
        record = self._touch_artifact(artifact_id)
        return {
            "artifact_id": record.artifact_id,
            "format": record.format,
            "created_at": record.created_at,
            "expires_at": record.expires_at,
            "output": record.output_resource_uri,
            "source": record.source_resource_uri,
            "metadata": record.metadata_resource_uri,
        }

    def read_output(self, artifact_id: str) -> bytes | str:
        record = self._touch_artifact(artifact_id)
        output_path = self.root_dir / artifact_id / record.output_filename
        if not output_path.exists():
            raise FileNotFoundError(f"artifact output missing: {artifact_id}")
        if record.output_mime_type == "image/png":
            return output_path.read_bytes()
        return output_path.read_text(encoding="utf-8", errors="replace")

    def read_source(self, artifact_id: str) -> str:
        self._touch_artifact(artifact_id)
        source_path = self.root_dir / artifact_id / "source.top"
        if not source_path.exists():
            raise FileNotFoundError(f"artifact source missing: {artifact_id}")
        return source_path.read_text(encoding="utf-8", errors="replace")

    def read_metadata(self, artifact_id: str) -> dict[str, Any]:
        record = self._touch_artifact(artifact_id)
        return record.to_dict()

    def artifact_manifest_uri(self, artifact_id: str) -> str:
        return f"resource://artifacts/{artifact_id}"

    def artifact_output_uri(self, artifact_id: str) -> str:
        return f"resource://artifacts/{artifact_id}/output"

    def artifact_source_uri(self, artifact_id: str) -> str:
        return f"resource://artifacts/{artifact_id}/source"

    def artifact_metadata_uri(self, artifact_id: str) -> str:
        return f"resource://artifacts/{artifact_id}/metadata"

    def _touch_artifact(self, artifact_id: str) -> ArtifactRecord:
        artifact_dir = self.root_dir / artifact_id
        record = self.load_artifact(artifact_id)
        record.last_accessed_at = _utc_now()
        record.size_bytes = _calculate_directory_size(artifact_dir)
        self._write_record(artifact_dir, record)
        return record

    def _load_existing_records(self) -> list[ArtifactRecord]:
        records: list[ArtifactRecord] = []
        if not self.root_dir.exists():
            return records
        for artifact_dir in self.root_dir.iterdir():
            if not artifact_dir.is_dir():
                continue
            record_path = artifact_dir / "metadata.json"
            if not record_path.exists():
                self._delete_artifact_dir(artifact_dir)
                continue
            try:
                record = ArtifactRecord.from_dict(
                    json.loads(record_path.read_text(encoding="utf-8"))
                )
            except (json.JSONDecodeError, KeyError, ValueError, TypeError):
                self._delete_artifact_dir(artifact_dir)
                continue
            record.size_bytes = _calculate_directory_size(artifact_dir)
            if record.artifact_id != artifact_dir.name:
                self._delete_artifact_dir(artifact_dir)
                continue
            records.append(record)
        return records

    def _write_record(self, artifact_dir: Path, record: ArtifactRecord) -> None:
        record_path = artifact_dir / "metadata.json"
        record_path.write_text(
            json.dumps(record.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _delete_artifact_dir(self, artifact_dir: Path) -> None:
        shutil.rmtree(artifact_dir, ignore_errors=True)

    def _generate_artifact_id(self) -> str:
        return f"tdart_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{token_hex(4)}"


def get_artifact_manager() -> ArtifactManager:
    """Return the shared artifact manager instance."""
    return _artifact_manager()


@cache
def _artifact_manager() -> ArtifactManager:
    return ArtifactManager(
        _artifact_root_dir(),
        ttl_seconds=_artifact_ttl_seconds(),
        max_bytes=_artifact_max_bytes(),
        max_count=_artifact_max_count(),
    )


def _artifact_root_dir() -> Path:
    configured = os.environ.get(ARTIFACT_ROOT_ENV)
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path(tempfile.gettempdir()) / "topdrawer-mcp-artifacts").resolve()


def _artifact_ttl_seconds() -> int:
    return int(os.environ.get(ARTIFACT_TTL_SECONDS_ENV, str(DEFAULT_ARTIFACT_TTL_SECONDS)))


def _artifact_max_bytes() -> int:
    return int(os.environ.get(ARTIFACT_MAX_BYTES_ENV, str(DEFAULT_ARTIFACT_MAX_BYTES)))


def _artifact_max_count() -> int:
    return int(os.environ.get(ARTIFACT_MAX_COUNT_ENV, str(DEFAULT_ARTIFACT_MAX_COUNT)))


def _utc_now() -> str:
    return _dt_utc_now().isoformat()


def _dt_utc_now() -> datetime:
    return datetime.now(UTC)


def _iso_after_seconds(seconds: int) -> str:
    return str(_dt_utc_now().timestamp() + seconds)


def _parse_iso(value: str) -> datetime:
    try:
        return datetime.fromtimestamp(float(value), UTC)
    except ValueError:
        return datetime.fromisoformat(value)


def _calculate_directory_size(path: Path) -> int:
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            total += item.stat().st_size
    return total
