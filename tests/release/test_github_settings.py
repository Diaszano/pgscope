"""Tests for GitHub settings grounded in observed repository ownership and workflows."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_proposal_accounts_for_the_single_observed_maintainer() -> None:
    content = (ROOT / "docs" / "github-settings.md").read_text(encoding="utf-8").lower()

    assert "only collaborator observed" in content
    assert "do not require an approving review" in content
    assert "another independent maintainer" in content


def test_proposal_uses_workflow_context_names_and_both_required_postgres_versions() -> None:
    content = (ROOT / "docs" / "github-settings.md").read_text(encoding="utf-8")

    for job in (
        "Validate PR Conventions",
        "Lint & Code Style",
        "Static Type Analysis",
        "Unit & Release Tests",
        "Package Build & Version Gate",
        "Integration (PG 16)",
        "Integration (PG 17)",
    ):
        assert job in content
    assert "exact displayed contexts" in content
    assert "experimental `Integration (PG 18)`" in content
    assert "do not enforce this check set yet" in content.lower()
    assert "release handoff depends on that job" in content


def test_release_pr_guidance_documents_tokens_and_auto_merge() -> None:
    content = (ROOT / "docs" / "github-settings.md").read_text(encoding="utf-8").lower()

    assert "does not push to `main`" in content
    assert "release_please_token" in content
    assert "homebrew_tap_token" in content
    assert "github_token" in content
    assert "do not trigger workflows" in content
    assert "allow auto-merge" in content
    assert "release-please--branches--main" in content
    assert "broad human-role bypass" in content


def test_remote_rules_and_ghcr_unknowns_are_explicit() -> None:
    content = (ROOT / "docs" / "github-settings.md").read_text(encoding="utf-8").lower()

    assert "has not been applied" in content
    assert "no branch protection rules or repository rulesets" in content
    assert "ghcr package" in content
    assert "remain unverified" in content


def test_rollback_digest_is_labeled_as_a_placeholder() -> None:
    content = (ROOT / "docs" / "github-settings.md").read_text(encoding="utf-8").lower()

    assert "placeholder" in content
    assert "<verified-release-digest>" in content
    assert "sha256:0123456789" not in content


def test_security_policy_references_governance_without_promising_sla() -> None:
    content = (ROOT / "SECURITY.md").read_text(encoding="utf-8").lower()

    assert "github-settings.md" in content
    assert "if it is enabled" in content
    assert "within 48 hours" not in content
