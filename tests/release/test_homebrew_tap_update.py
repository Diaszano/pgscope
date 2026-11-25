"""Tests for Homebrew tap cask generator and updater."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.release import update_homebrew_tap
from scripts.release.update_homebrew_tap import generate_cask_content

PLATFORMS = ("darwin_amd64", "darwin_arm64", "linux_amd64", "linux_arm64")


def _write_checksums(dist: Path, version: str, platforms: tuple[str, ...] = PLATFORMS) -> None:
    for index, platform in enumerate(platforms, start=1):
        name = f"pgscope_{version}_{platform}.tar.gz"
        (dist / f"{name}.sha256").write_text(f"{str(index) * 64}  {name}\n", encoding="utf-8")


def _run(monkeypatch: pytest.MonkeyPatch, dist: Path, *, token: str | None, push_ok: bool = True) -> int:
    monkeypatch.setattr(
        "sys.argv", ["update_homebrew_tap.py", "--version", "0.4.2", "--dist-dir", str(dist), "--output", str(dist / "pgscope.rb"), "--push"]
    )
    if token is None:
        monkeypatch.delenv("HOMEBREW_TAP_TOKEN", raising=False)
    else:
        monkeypatch.setenv("HOMEBREW_TAP_TOKEN", token)
    monkeypatch.setattr(update_homebrew_tap, "push_to_homebrew_tap", lambda *args, **kwargs: push_ok)
    return update_homebrew_tap.main()


def test_push_succeeds_with_token_and_all_checksums(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_checksums(tmp_path, "0.4.2")

    assert _run(monkeypatch, tmp_path, token="token") == 0
    assert (tmp_path / "pgscope.rb").is_file()


def test_push_without_token_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_checksums(tmp_path, "0.4.2")

    assert _run(monkeypatch, tmp_path, token=None) == 1


def test_push_failure_fails_the_job(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_checksums(tmp_path, "0.4.2")

    assert _run(monkeypatch, tmp_path, token="token", push_ok=False) == 1


def test_missing_checksum_never_publishes_an_empty_sha(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_checksums(tmp_path, "0.4.2", PLATFORMS[:3])

    assert _run(monkeypatch, tmp_path, token="token") == 1
    assert not (tmp_path / "pgscope.rb").exists()


def test_generate_cask_content_structure() -> None:
    checksums = {
        "darwin_amd64": "1111111111111111111111111111111111111111111111111111111111111111",
        "darwin_arm64": "2222222222222222222222222222222222222222222222222222222222222222",
        "linux_amd64": "3333333333333333333333333333333333333333333333333333333333333333",
        "linux_arm64": "4444444444444444444444444444444444444444444444444444444444444444",
    }
    cask_text = generate_cask_content("0.4.2", checksums)

    assert 'cask "pgscope" do' in cask_text
    assert 'version "0.4.2"' in cask_text
    assert "on_macos do" in cask_text
    assert "on_intel do" in cask_text
    assert "on_arm do" in cask_text
    assert "on_linux do" in cask_text
    assert checksums["darwin_amd64"] in cask_text
    assert checksums["darwin_arm64"] in cask_text
    assert checksums["linux_amd64"] in cask_text
    assert checksums["linux_arm64"] in cask_text
    assert 'binary "pgscope"' in cask_text
    assert "https://github.com/Diaszano/pgscope/releases/download/v#{version}/" in cask_text
