from __future__ import annotations

from copy import deepcopy

import pytest

from topdrawer_mcp import reference_data


pytestmark = pytest.mark.unit


def test_validate_reference_topic_accepts_set_window_reference():
    topic = reference_data.load_reference_topic(
        reference_data.DEFAULT_SET_WINDOW_REFERENCE_PATH
    )

    reference_data.validate_reference_topic(topic)


def test_validate_reference_topic_rejects_duplicate_ids():
    topic = reference_data.load_reference_topic(
        reference_data.DEFAULT_SET_WINDOW_REFERENCE_PATH
    )
    duplicate = deepcopy(topic)
    duplicate["entries"].append(deepcopy(duplicate["entries"][0]))

    with pytest.raises(ValueError, match="duplicate reference entry id"):
        reference_data.validate_reference_topic(duplicate)


def test_validate_reference_topic_rejects_missing_rules():
    topic = reference_data.load_reference_topic(
        reference_data.DEFAULT_SET_WINDOW_REFERENCE_PATH
    )
    invalid = deepcopy(topic)
    invalid["entries"][0]["rules"] = []

    with pytest.raises(ValueError, match="reference field 'rules' must be a non-empty list"):
        reference_data.validate_reference_topic(invalid)


def test_set_window_reference_contains_expected_entry_ids():
    topic = reference_data.load_reference_topic(
        reference_data.DEFAULT_SET_WINDOW_REFERENCE_PATH
    )

    ids = [entry["id"] for entry in topic["entries"]]
    assert ids == [
        "absolute",
        "numbered",
        "relative",
        "positive-vs-negative",
        "practical-notes",
    ]


def test_validate_symbol_code_reference_accepts_repository_data():
    reference = reference_data.load_symbol_code_reference()

    reference_data.validate_symbol_code_reference(reference)


def test_validate_symbol_code_reference_rejects_duplicate_codes():
    reference = reference_data.load_symbol_code_reference()
    duplicate = deepcopy(reference)
    duplicate["rows"].append(deepcopy(duplicate["rows"][0]))

    with pytest.raises(ValueError, match="duplicate symbol code"):
        reference_data.validate_symbol_code_reference(duplicate)


def test_symbol_code_reference_contains_practical_subset():
    reference = reference_data.load_symbol_code_reference()

    rows = {row["code"]: row["glyph"] for row in reference["rows"]}
    assert rows["0P"] == "+"
    assert rows["AP"] == "●"
    assert rows["AG"] == "α"
