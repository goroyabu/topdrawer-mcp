from __future__ import annotations

from pathlib import Path

import pytest


pytestmark = pytest.mark.unit


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "workflow_validation"
EXPECTED_SCENARIOS = {
    "existing-script-repair-typo",
    "ambiguous-goal-polar-or-error-bars",
    "unsupported-direct-function-plot",
    "runtime-triage-missing-render-prereq",
}
EXPECTED_FILES = {"input.top", "prompt.md", "expected.md"}


def test_workflow_validation_scenarios_exist_with_expected_files():
    scenario_dirs = {path.name for path in FIXTURE_ROOT.iterdir() if path.is_dir()}

    assert scenario_dirs == EXPECTED_SCENARIOS
    for scenario in EXPECTED_SCENARIOS:
        scenario_dir = FIXTURE_ROOT / scenario
        files = {path.name for path in scenario_dir.iterdir() if path.is_file()}
        assert files == EXPECTED_FILES


def test_workflow_validation_assets_have_non_empty_text():
    for scenario in EXPECTED_SCENARIOS:
        scenario_dir = FIXTURE_ROOT / scenario
        input_text = (scenario_dir / "input.top").read_text(encoding="utf-8")
        prompt_text = (scenario_dir / "prompt.md").read_text(encoding="utf-8")
        expected_text = (scenario_dir / "expected.md").read_text(encoding="utf-8")

        assert input_text.strip()
        assert prompt_text.strip()
        assert expected_text.strip()


def test_workflow_validation_expected_files_describe_workflow_and_success():
    for scenario in EXPECTED_SCENARIOS:
        expected_text = (FIXTURE_ROOT / scenario / "expected.md").read_text(
            encoding="utf-8"
        )

        lowered = expected_text.casefold()
        assert "workflow" in lowered
        assert "success" in lowered
