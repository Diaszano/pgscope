"""Tests for the reusable release workflow specification and safety invariants."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


def _load_release_workflow() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    path = root / ".github" / "workflows" / "release.yml"
    assert path.is_file(), ".github/workflows/release.yml missing"
    return yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def test_release_workflow_structure_and_concurrency() -> None:
    wf = _load_release_workflow()

    on_events = wf.get("on")
    assert isinstance(on_events, dict)
    assert "workflow_call" in on_events

    # Release and recovery share this lock so neither can race alias promotion.
    concurrency = wf.get("concurrency")
    assert concurrency is not None, "release.yml must define concurrency group"
    if isinstance(concurrency, dict):
        assert concurrency.get("group") == "image-alias-promotion"
        assert concurrency.get("cancel-in-progress") in ("false", False)


def test_release_job_uses_pinned_release_please_with_pat() -> None:
    wf = _load_release_workflow()
    jobs = wf.get("jobs", {})
    assert "release-please" in jobs, "release.yml must have a 'release-please' job"

    job = jobs["release-please"]
    # Only the PAT writes to the repository; the job token stays read-only.
    assert job.get("permissions") == {"contents": "read"}

    action = next(step for step in job["steps"] if step.get("id") == "release")
    assert re.fullmatch(r"googleapis/release-please-action@[0-9a-f]{40}", action["uses"]), "release-please-action must be pinned to a commit SHA"
    assert action["with"]["token"] == "${{ secrets.RELEASE_PLEASE_TOKEN }}"
    assert action["with"]["config-file"] == "release-please-config.json"
    assert action["with"]["manifest-file"] == ".release-please-manifest.json"

    secrets = wf["on"]["workflow_call"]["secrets"]
    assert secrets["RELEASE_PLEASE_TOKEN"]["required"] in ("true", True)


def test_release_pr_enables_auto_merge() -> None:
    wf = _load_release_workflow()
    steps = wf["jobs"]["release-please"]["steps"]
    step = next(step for step in steps if step.get("name") == "Enable auto-merge on the release pull request")

    assert step["env"]["GH_TOKEN"] == "${{ secrets.RELEASE_PLEASE_TOKEN }}"
    assert "autorelease: pending" in step["run"]
    assert "gh pr merge" in step["run"]
    assert "--auto" in step["run"]
    assert "--squash" in step["run"]


def test_release_publishes_distributions_to_the_release() -> None:
    wf = _load_release_workflow()
    job = wf["jobs"]["publish-dist"]

    assert job["needs"] == "release-please"
    assert job["if"] == "needs.release-please.outputs.released == 'true'"
    assert job["permissions"] == {"contents": "write"}
    steps_text = yaml.dump(job["steps"])
    assert "scripts/release/build.sh" in steps_text
    assert "gh release upload" in steps_text


def test_release_job_outputs_contract() -> None:
    wf = _load_release_workflow()
    on_events = wf.get("on")
    assert isinstance(on_events, dict)
    call_config = on_events.get("workflow_call", {})
    outputs = call_config.get("outputs", {})

    expected_outputs = {"released", "tag", "release_sha", "version"}
    assert expected_outputs <= set(outputs.keys()), f"Missing required outputs: {expected_outputs - set(outputs.keys())}"
