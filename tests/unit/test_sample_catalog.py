from __future__ import annotations

import copy

import pytest

from topdrawer_mcp import sample_catalog


pytestmark = pytest.mark.unit


def test_load_sample_catalog_reads_repository_catalog():
    catalog = sample_catalog.load_sample_catalog()

    assert catalog["version"] == 1
    assert len(catalog["samples"]) == 10


def test_validate_sample_catalog_accepts_repository_catalog():
    catalog = sample_catalog.load_sample_catalog()

    sample_catalog.validate_sample_catalog(catalog)


def test_validate_sample_catalog_rejects_duplicate_ids():
    catalog = sample_catalog.load_sample_catalog()
    duplicate = copy.deepcopy(catalog)
    duplicate["samples"].append(copy.deepcopy(duplicate["samples"][0]))

    with pytest.raises(ValueError, match="duplicate sample id"):
        sample_catalog.validate_sample_catalog(duplicate)


def test_validate_sample_catalog_rejects_unknown_category():
    catalog = sample_catalog.load_sample_catalog()
    invalid = copy.deepcopy(catalog)
    invalid["samples"][0]["category"] = "unknown"

    with pytest.raises(ValueError, match="invalid sample category"):
        sample_catalog.validate_sample_catalog(invalid)


def test_validate_sample_catalog_requires_primary_commands():
    catalog = sample_catalog.load_sample_catalog()
    invalid = copy.deepcopy(catalog)
    invalid["samples"][0]["primary_commands"] = []

    with pytest.raises(ValueError, match="must declare at least one primary command"):
        sample_catalog.validate_sample_catalog(invalid)


def test_validate_sample_catalog_rejects_extra_keys():
    catalog = sample_catalog.load_sample_catalog()
    invalid = copy.deepcopy(catalog)
    invalid["samples"][0]["provenance"] = {"source_url": "https://example.test"}

    with pytest.raises(ValueError, match="entry keys must be exactly"):
        sample_catalog.validate_sample_catalog(invalid)


def test_repository_catalog_entries_do_not_include_provenance():
    catalog = sample_catalog.load_sample_catalog()

    for entry in catalog["samples"]:
        assert "provenance" not in entry
        assert set(entry) == {
            "id",
            "title",
            "category",
            "description",
            "primary_commands",
        }


def test_validate_sample_catalog_requires_full_curated_category_coverage():
    catalog = sample_catalog.load_sample_catalog()
    invalid = copy.deepcopy(catalog)
    invalid["samples"] = [
        entry for entry in invalid["samples"] if entry["category"] != "polar"
    ]

    with pytest.raises(ValueError, match="category coverage mismatch"):
        sample_catalog.validate_sample_catalog(invalid)
