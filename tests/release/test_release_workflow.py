"""Tests for the reusable release workflow specification and safety invariants."""

from __future__ import annotations

import os
import re
import subprocess
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


def _run_auto_merge_step(tmp_path: Path, *, pr_numbers: str, auto_fails: bool = False) -> tuple[subprocess.CompletedProcess[str], str]:
    wf = _load_release_workflow()
    step = next(step for step in wf["jobs"]["release-please"]["steps"] if step.get("name") == "Enable auto-merge on the release pull request")
    assert step["env"]["GH_TOKEN"] == "${{ secrets.RELEASE_PLEASE_TOKEN }}"

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    log = tmp_path / "gh.log"
    (fake_bin / "gh").write_text(
        "#!/bin/sh\n"
        'echo "$*" >> "$FAKE_GH_LOG"\n'
        'case "$1" in\n'
        '  api) printf "%s" "$FAKE_PR_NUMBERS" ;;\n'
        '  pr) if [ "$FAKE_AUTO_FAILS" = 1 ]; then case " $* " in *" --auto "*) exit 1 ;; esac; fi ;;\n'
        "esac\n",
        encoding="utf-8",
    )
    (fake_bin / "gh").chmod(0o755)
    env = {
        **os.environ,
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "GH_REPO": "Diaszano/pgscope",
        "FAKE_GH_LOG": str(log),
        "FAKE_PR_NUMBERS": pr_numbers,
        "FAKE_AUTO_FAILS": "1" if auto_fails else "0",
    }
    result = subprocess.run(["bash", "-euo", "pipefail", "-c", step["run"]], env=env, capture_output=True, text=True)
    return result, log.read_text(encoding="utf-8") if log.exists() else ""


def test_release_pr_is_found_through_the_rest_api_not_search(tmp_path: Path) -> None:
    result, calls = _run_auto_merge_step(tmp_path, pr_numbers="44")

    assert result.returncode == 0, result.stderr
    assert "api --paginate repos/Diaszano/pgscope/pulls?state=open" in calls
    assert "pr list" not in calls


def test_auto_merge_is_enabled_on_the_release_pr(tmp_path: Path) -> None:
    result, calls = _run_auto_merge_step(tmp_path, pr_numbers="44\n43")

    assert result.returncode == 0, result.stderr
    assert "pr merge 44 --auto --squash" in calls
    assert "pr merge 43" not in calls


def test_release_pr_is_merged_directly_when_auto_merge_is_refused(tmp_path: Path) -> None:
    result, calls = _run_auto_merge_step(tmp_path, pr_numbers="44", auto_fails=True)

    assert result.returncode == 0, result.stderr
    assert "pr merge 44 --auto --squash" in calls
    assert "pr merge 44 --squash" in calls.replace("--auto ", "")
    assert calls.strip().splitlines()[-1] == "pr merge 44 --squash"


def test_no_release_pr_is_not_an_error(tmp_path: Path) -> None:
    result, calls = _run_auto_merge_step(tmp_path, pr_numbers="")

    assert result.returncode == 0, result.stderr
    assert "No open release pull request." in result.stdout
    assert "pr merge" not in calls


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
