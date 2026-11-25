"""Python versions must not drift: one supported floor, one version that is built, shipped and developed on."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ("ci.yml", "release.yml", "binaries.yml")


def _pyproject() -> dict[str, Any]:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _floor() -> str:
    match = re.fullmatch(r">=(\d+\.\d+)", _pyproject()["project"]["requires-python"])
    assert match, "requires-python must be a plain '>=X.Y' floor"
    return match.group(1)


def _shipped() -> str:
    mise = tomllib.loads((ROOT / "mise.toml").read_text(encoding="utf-8"))
    version = mise["vars"]["python_version"]
    # One definition in mise: the Python tool and uv's interpreter both follow it.
    assert mise["tools"]["python"] == "{{ vars.python_version }}"
    assert mise["env"]["UV_PYTHON"] == "{{ vars.python_version }}"
    return version


def test_tool_configs_target_the_supported_floor() -> None:
    floor = _floor()
    tools = _pyproject()["tool"]

    assert tools["ruff"]["target-version"] == f"py{floor.replace('.', '')}"
    assert tools["pyright"]["pythonVersion"] == floor
    assert f"Python {floor} or higher" in (ROOT / "README.md").read_text(encoding="utf-8")


def test_workflows_run_the_shipped_python_except_the_floor_job() -> None:
    floor, shipped = _floor(), _shipped()
    found = 0

    for name in WORKFLOWS:
        workflow = yaml.safe_load((ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8"))
        for job_id, job in workflow["jobs"].items():
            for step in job.get("steps", []):
                for version in re.findall(r"uv python install (\S+)", step.get("run", "")):
                    expected = floor if job_id == "unit-floor" else shipped
                    assert version == expected, f"{name}:{job_id} installs Python {version}, expected {expected}"
                    found += 1

    assert found, "workflows must pin the Python they run"


def test_ci_tests_the_floor_and_gates_the_release_on_it() -> None:
    ci = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))

    assert "unit-floor" in ci["jobs"]
    assert "unit-floor" in ci["jobs"]["release"]["needs"]


def test_docker_image_uses_the_shipped_python() -> None:
    shipped = _shipped()
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert f"FROM ghcr.io/astral-sh/uv:python{shipped}-bookworm-slim AS builder" in dockerfile
    assert f"FROM python:{shipped}-slim-bookworm" in dockerfile
    assert f"/usr/local/lib/python{shipped}/site-packages" in dockerfile
