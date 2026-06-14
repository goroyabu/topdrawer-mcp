from __future__ import annotations

import pytest

from topdrawer_mcp.reverse_lookup import reverse_lookup_command_candidates


pytestmark = pytest.mark.unit


def test_reverse_lookup_rejects_empty_query():
    with pytest.raises(ValueError, match="query must be a non-empty string"):
        reverse_lookup_command_candidates("   ")


def test_reverse_lookup_finds_set_polar_first():
    result = reverse_lookup_command_candidates("polar")

    assert result["commands"]
    assert result["commands"][0] == "SET POLAR"


def test_reverse_lookup_returns_join_for_points_and_line():
    result = reverse_lookup_command_candidates("points and line")

    assert "JOIN" in result["commands"]


def test_reverse_lookup_prefers_default_limit_of_five():
    result = reverse_lookup_command_candidates("set")

    assert result["commands"]
    assert len(result["commands"]) <= 5


def test_reverse_lookup_honors_explicit_limit():
    result = reverse_lookup_command_candidates("set", limit=2)

    assert result["commands"]
    assert len(result["commands"]) <= 2
