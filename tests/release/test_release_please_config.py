from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _config() -> dict[str, Any]:
    return json.loads((ROOT / "release-please-config.json").read_text(encoding="utf-8"))


def test_release_please_contract_configuration() -> None:
    cfg = _config()

    assert cfg["release-type"] == "python"
    # Pre-1.0 policy: breaking changes bump minor, features bump minor, fixes bump patch.
    assert cfg["bump-minor-pre-major"] is True
    assert cfg["bump-patch-for-minor-pre-major"] is False
    assert cfg["include-v-in-tag"] is True
    assert cfg["include-component-in-tag"] is False
    assert cfg["pull-request-title-pattern"] == "chore(release): ${version}"


def test_release_please_stamps_the_lockfile() -> None:
    package = _config()["packages"]["."]

    assert package["package-name"] == "pgscope"
    assert {"type": "toml", "path": "uv.lock", "jsonpath": "$.package[?(@.name.value=='pgscope')].version"} in package["extra-files"]


def test_manifest_matches_project_version() -> None:
    manifest = json.loads((ROOT / ".release-please-manifest.json").read_text(encoding="utf-8"))
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert manifest == {".": pyproject["project"]["version"]}


def test_semantic_release_config_is_gone() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert "semantic_release" not in pyproject.get("tool", {})


def test_no_manual_tagging_in_justfile() -> None:
    justfile_path = ROOT / "justfile"

    if justfile_path.is_file():
        content = justfile_path.read_text(encoding="utf-8")
        # Ensure no manual release publication shortcuts
        assert "gh release create" not in content, "justfile must not create GitHub releases manually"
        assert "git tag -a" not in content and "git tag v" not in content, "justfile must not create manual git release tags"
        assert "release-preview" in content, "justfile must provide 'release-preview' recipe"
