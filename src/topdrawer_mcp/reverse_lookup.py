from __future__ import annotations

from typing import TypedDict

from topdrawer_mcp.command_lookup import CommandLookupEntry
from topdrawer_mcp.command_lookup import load_command_lookup_index


DEFAULT_LIMIT = 5
MAX_LIMIT = 20
_EXACT_FIELD_WEIGHTS = {
    "command": 100,
    "aliases": 90,
    "title": 60,
    "summary": 50,
}
_TERM_FIELD_WEIGHTS = {
    "command": 20,
    "aliases": 18,
    "title": 12,
    "summary": 10,
    "parent_command": 4,
    "section": 2,
}
_CURATED_SUMMARY_BONUS = 5


class ReverseLookupResult(TypedDict):
    query: str
    commands: list[str]


def _normalize_query(value: str) -> str:
    normalized = " ".join(value.casefold().split())
    if not normalized:
        raise ValueError("query must be a non-empty string")
    return normalized


def _query_terms(value: str) -> list[str]:
    return [term for term in _normalize_query(value).split(" ") if term]


def _clamp_limit(limit: int) -> int:
    return max(1, min(MAX_LIMIT, limit))


def _entry_search_texts(entry: CommandLookupEntry) -> dict[str, str | list[str]]:
    return {
        "command": entry["command"].casefold(),
        "aliases": [alias.casefold() for alias in entry["aliases"]],
        "title": entry["title"].casefold(),
        "summary": entry["summary"].casefold(),
        "parent_command": (entry["parent_command"] or "").casefold(),
        "section": entry["section"].casefold(),
    }


def _text_contains(field_text: str | list[str], needle: str) -> bool:
    if isinstance(field_text, list):
        return any(needle in item for item in field_text)
    return needle in field_text


def _score_field_matches(search_texts: dict[str, str | list[str]], query: str, terms: list[str]) -> int:
    score = 0
    for field_name, weight in _EXACT_FIELD_WEIGHTS.items():
        if _text_contains(search_texts[field_name], query):
            score += weight

    for term in terms:
        for field_name, weight in _TERM_FIELD_WEIGHTS.items():
            if _text_contains(search_texts[field_name], term):
                score += weight

    return score


def _score_curated_entry_boost(entry: CommandLookupEntry, base_score: int) -> int:
    if base_score <= 0:
        return 0

    if entry["summary"].strip():
        return _CURATED_SUMMARY_BONUS
    return 0


def _score_entry(entry: CommandLookupEntry, query: str, terms: list[str]) -> int:
    search_texts = _entry_search_texts(entry)
    base_score = _score_field_matches(search_texts, query, terms)
    score = base_score + _score_curated_entry_boost(entry, base_score)

    return score


def reverse_lookup_command_candidates(
    query: str,
    limit: int = DEFAULT_LIMIT,
) -> ReverseLookupResult:
    normalized_query = _normalize_query(query)
    terms = _query_terms(query)
    clamped_limit = _clamp_limit(limit)
    candidates: list[tuple[int, CommandLookupEntry]] = []

    for entry in load_command_lookup_index()["entries"]:
        score = _score_entry(entry, normalized_query, terms)
        if score > 0:
            candidates.append((score, entry))

    candidates.sort(
        key=lambda item: (
            -item[0],
            len(item[1]["command"]),
            item[1]["command"],
        )
    )

    commands: list[str] = []
    seen_commands: set[str] = set()
    for _, entry in candidates:
        command = entry["command"]
        if command in seen_commands:
            continue
        seen_commands.add(command)
        commands.append(command)
        if len(commands) >= clamped_limit:
            break

    return {
        "query": normalized_query,
        "commands": commands,
    }
