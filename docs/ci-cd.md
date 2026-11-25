# CI/CD and Automated Release Architecture Guide

> **English** | [Português (Brasil)](ci-cd.pt-BR.md)

This document describes the automated continuous integration and delivery architecture for the **pgscope** server.

## 1. Pipeline Overview

The project uses GitHub Actions workflows for continuous validation and zero-manual-intervention releases:

```
[Developer Branch]
       │
       ▼ (Pull Request)
[.github/workflows/ci.yml]
       ├── Lint & Formatting (Ruff)
       ├── Type Checking (Pyright)
       ├── Unit & Release Tests (pytest tests/unit tests/release)
       ├── Package Build (uv build)
       ├── HypoPG Integration Gate (PG16 & PG17)
       └── PR Metadata & Conventional Commits Validation
       │
       ▼ (Merge to main)
[Release Handoff]
       │
       ▼ (Trigger reusable .github/workflows/release.yml)
[Release Please Job]
       ├── Open/update the release PR "chore(release): X.Y.Z" (pyproject.toml, uv.lock, CHANGELOG.md)
       ├── Enable auto-merge (squash); the PR must pass the required CI checks
       └── When the release PR merges: create tag vX.Y.Z & GitHub Release
       │
       ▼ (On New Release)
[Attach Distributions]
       └── Build wheel/sdist and upload them to the GitHub Release
       │
       ▼ (On New Release)
[Standalone Binaries & Homebrew] (.github/workflows/binaries.yml, triggered by the published release)
       ├── Build darwin/linux amd64/arm64 tarballs + sha256 and upload to the GitHub Release
       └── Update Casks/pgscope.rb in Diaszano/homebrew-tap
       │
       ▼ (On New Release)
[Multiarch GHCR Staging & Delivery]
       ├── Docker Buildx & QEMU (linux/amd64, linux/arm64)
       ├── Generate SLSA Provenance & SBOM (SPDX)
       ├── Stage immutable image: ghcr.io/diaszano/pgscope:sha-<commit-sha>
       ├── Fail-closed vulnerability scan (Trivy HIGH/CRITICAL exit 1)
       └── Promote immutable digest to stable SemVer aliases:
           - ghcr.io/diaszano/pgscope:vX.Y.Z
           - ghcr.io/diaszano/pgscope:X.Y.Z
           - ghcr.io/diaszano/pgscope:X.Y
           - ghcr.io/diaszano/pgscope:X
           - ghcr.io/diaszano/pgscope:latest
```

## 2. Dependency Management & Versioning Invariants

- **Dependency Lock Verification**: `uv lock --check` ensures that dependencies in `uv.lock` strictly match `pyproject.toml`.
- **Release Tag Specification**: Stable releases strictly follow the format `vX.Y.Z` where X, Y, and Z are non-negative integers. Prerelease tags (`-rc`, `-alpha`, `-beta`) are prohibited from stable delivery.
- **Version Source**: Release Please derives the next version from Conventional Commits (`feat` bumps minor, `fix` bumps patch) and records it in `.release-please-manifest.json`, `pyproject.toml` and `uv.lock` in the release PR.
- **Zero-Version Policy**: While on `0.x.y`, breaking changes increment minor (`0.3.0` -> `0.4.0`) rather than bumping to `1.0.0`.

## 3. Pulling and Verifying Images

Users and orchestrators should deploy images using immutable content digests:

```bash
# Replace the placeholder with the digest verified for your deployment:
docker pull ghcr.io/diaszano/pgscope@sha256:<verified-digest>

# Run container
docker run -it --rm \
  ghcr.io/diaszano/pgscope@sha256:<verified-digest> \
  postgres://mcp_agent:password@localhost:5432/mydb
```

## 4. Partial Release Recovery Procedure

In rare scenarios where Release Please successfully tags a release and publishes to GitHub Releases, but network or container registry timeouts interrupt image build or promotion:

1. **Do not create a duplicate version or re-tag manually.**
2. Navigate to Actions -> **Retry Publish** workflow (`.github/workflows/retry-publish.yml`).
3. Click **Run workflow**, enter the existing verified tag (e.g. `v0.3.0`), and submit.
4. The workflow verifies the tag format, matching `pyproject.toml` version, and checked-out tag commit, builds the staging image from that exact commit, scans both architectures with Trivy, and repairs safe aliases without bumping version numbers.
5. Recovery never changes a version tag to a different digest. It advances floating aliases only when their recorded image version is not newer than the requested release; missing or unparseable version metadata stops recovery. Normal release promotion and recovery share one concurrency group to prevent alias races.
6. If only the standalone binaries or the Homebrew cask failed, run **Build and Release Standalone Binaries** (`.github/workflows/binaries.yml`) manually with the same tag.

For a rollback, redeploy a previously verified `repository@sha256:<verified-digest>` reference. This changes the deployed image only; it does not publish a release or move registry aliases.

## 5. End-to-End Delivery Verification & Handoff

The repository-readiness review on 2026-11-03 found no successful `main` CI run from which to confirm GitHub's displayed job contexts. The proposed names and remote evidence are recorded in [GitHub settings](github-settings.md). GHCR publication and package access also remain unverified.

Before merging any change to `main` or tagging production versions, the full suite of automated verification gates must pass:

- **Repository Hygiene & Conventions**:
  - `uv run pytest -q tests/release/test_repository_conventions.py`
  - `uv run pytest -q tests/release/test_dependabot_config.py`
  - `uv run pytest -q tests/release/test_pr_metadata.py`
- **Code Quality & Static Analysis**:
  - `uv lock --check`
  - `uv run ruff check .`
  - `uv run ruff format --check .`
  - `uv run pyright` (currently reports existing diagnostics; see [project readiness](project-readiness.md))
- **Testing Layers**:
  - `uv run pytest -q tests/unit`
  - `uv run pytest -q tests/release`
  - `uv run pytest -q tests/integration` (PostgreSQL 16 & 17 HypoPG containers)
- **Artifact Build Verification**:
  - `uv build` (producing valid wheel and sdist)
  - `docker buildx build --platform linux/amd64,linux/arm64 .`
- **Security & Attestation Invariants**:
  - Pinned GitHub Actions commit SHAs in `.github/workflows/*.yml`
  - Fail-closed Trivy container vulnerability scanner
  - Immutable SHA256 digest promotion without floating-tag race conditions

## 6. Release Secrets and Repository Settings

| Secret | Used by | Required access |
|--------|---------|-----------------|
| `RELEASE_PLEASE_TOKEN` | `release.yml` (Release Please and auto-merge) | Personal access token with write access to this repository's contents and pull requests |
| `HOMEBREW_TAP_TOKEN` | `binaries.yml` (Homebrew cask update) | Personal access token with write access to the contents of `Diaszano/homebrew-tap` |

A personal access token is used for releases because pull requests and releases created with `GITHUB_TOKEN` do not trigger other workflows. With the default token, CI would never run on the release PR (its required checks would stay pending) and `binaries.yml` would not start when the release is published.

The pipeline relies on **Allow auto-merge** being enabled and on the `main` ruleset requiring the CI checks. Nothing pushes directly to `main`, so no ruleset bypass is needed. The release PR uses the branch `release-please--branches--main`, which `scripts/ci/check_pr_metadata.py` accepts.

## 7. Python Versions

| Role | Version | Defined in |
|------|---------|------------|
| Minimum supported (floor) | 3.12 | `requires-python`, Ruff `target-version`, Pyright `pythonVersion`; tested by the `unit-floor` CI job |
| Built, shipped and used for development | 3.14 | `mise.toml` (`python_version`), the CI workflows, the `Dockerfile` and the standalone binaries |

`tests/release/test_python_versions.py` fails if these drift apart. To move to another Python version, change `python_version` in `mise.toml`, the `uv python install` lines in the workflows and the `Dockerfile` image tags together.
