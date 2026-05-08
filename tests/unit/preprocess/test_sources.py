from __future__ import annotations

import pytest

from topdrawer_mcp.preprocess import sources


pytestmark = pytest.mark.unit


def test_resolve_doc_source_path_uses_explicit_path(tmp_path):
    explicit = tmp_path / "topdrawer.doc"

    assert sources.resolve_doc_source_path(explicit) == explicit


def test_resolve_doc_source_path_uses_env(monkeypatch: pytest.MonkeyPatch, tmp_path):
    env_path = tmp_path / "env-topdrawer.doc"
    monkeypatch.setenv(sources.DOC_SOURCE_ENV_VAR, str(env_path))

    assert sources.resolve_doc_source_path() == env_path


def test_resolve_doc_source_path_defaults_to_data_raw():
    assert sources.resolve_doc_source_path() == sources.DEFAULT_DOC_SOURCE_PATH


def test_read_source_text_reads_utf8_with_replacement(tmp_path):
    source = tmp_path / "topdrawer.doc"
    source.write_bytes(b"valid\ninvalid:\xff\n")

    assert sources.read_source_text(source) == "valid\ninvalid:\ufffd\n"


def test_read_source_text_reports_missing_file(tmp_path):
    missing = tmp_path / "missing.doc"

    with pytest.raises(OSError, match="Unable to read Topdrawer source"):
        sources.read_source_text(missing)
