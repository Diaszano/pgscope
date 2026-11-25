# pgscope Release Checklist & Rollback Procedure

> **English** | [Português (Brasil)](release-checklist.pt-BR.md)

Base Version: (evaluated dynamically from `pyproject.toml`)
Primary Image Registry: `ghcr.io/diaszano/pgscope`
Release Automation: Release Please (googleapis/release-please-action v5.0.0) via GitHub Actions

## Pre-Release Verification Checklist

Execute the following verification gates before tagging and publishing any release:

- [ ] **Dependency Lock**: Run `uv lock --check` to ensure `uv.lock` is consistent with `pyproject.toml`.
- [ ] **Lint and Formatting**: Run `just lint` (`uv run ruff check .` and `uv run ruff format --check .`).
- [ ] **Static Type Analysis**: Run `just typecheck` (`uv run pyright`).
- [ ] **Unit and Release Tests**: Run `uv run pytest -q tests/unit tests/release` (the CI job runs both suites).
- [ ] **Integration Test Suite**: Run `just test-integration` across PostgreSQL 16 and 17 with HypoPG extension containers.
- [ ] **Release Suite**: Run `uv run pytest -q tests/release` covering SemVer rules, conventions, security scans, and workflow gates.
- [ ] **Performance Benchmarks**: Run `uv run --group dev pytest -q tests/performance --run-performance`.
- [ ] **Smoke Tests**: Run `uv run pytest -q tests/release/test_smoke.py` when changing runtime packaging or container startup.
- [ ] **Package Build**: Run `uv build` and inspect wheel contents under `dist/`.
- [ ] **Container Build**: Verify multi-architecture container build for `linux/amd64` and `linux/arm64`.

## Automated CI/CD & Delivery Gates

1. **Pull Requests**:
   - All PRs execute read-only checks across linting, typechecking, tests, package build, and HypoPG integration.
   - PR metadata is validated against Conventional Commits.
   - Privileged secrets and publish permissions are blocked on PR events.

2. **Main Branch & Release Please**:
   - Pushes to `main` evaluate commit history using Conventional Commits.
   - Release Please opens or updates a release pull request (`chore(release): X.Y.Z`, branch `release-please--branches--main--components--pgscope`) that bumps `pyproject.toml`, `uv.lock` and `CHANGELOG.md` (pre-1.0 zero-version policy: breaking changes increment minor).
   - Auto-merge (squash) is enabled on that PR and completes once the required checks pass. Nothing pushes directly to `main`.
   - Merging the release PR makes Release Please create the `vX.Y.Z` tag and GitHub Release, and the workflow then attaches the wheel and sdist to it. The new flow has not produced a release yet, so remote release artifacts have not been verified for it.

3. **GHCR Multiarch Delivery**:
   - Multiarch images (`linux/amd64,linux/arm64`) are built with Docker Buildx and staged using immutable commit SHAs.
   - Container vulnerability scans run with Trivy (fail-closed on HIGH/CRITICAL CVEs).
   - Buildx is configured to generate provenance and SBOM for each image build; registry publication has not been verified.
   - Verified staging digests are promoted to `vX.Y.Z`, `X.Y`, `X`, and `latest` tags on `ghcr.io/diaszano/pgscope`.

4. **Standalone Binaries & Homebrew**:
   - Publishing the release triggers `.github/workflows/binaries.yml`, which builds `darwin`/`linux` `amd64`/`arm64` tarballs with `sha256` files, uploads them to the release and updates `Casks/pgscope.rb` in `Diaszano/homebrew-tap`.
   - The workflow fails if `HOMEBREW_TAP_TOKEN` is missing, a checksum is missing, or the tap push fails.

## Production Rollback & Emergency Backout Procedure

If regressions, unexpected query rejections, or client incompatibilities emerge in production:

1. **Disable Query Guardrails**:
   Set `DATABASE_QUERY_GUARDRAILS_ENABLED=false` in the server environment. This immediately restores legacy statement behavior without breaking connection pools or dropping security warnings.
2. **Disable Cursor Pagination**:
   Set `DATABASE_PAGINATION_ENABLED=false` if clients have issues consuming continuation tokens.
3. **In-Memory Store Isolation**:
   The cursor cache is strictly in-process and memory-bounded with zero external storage dependencies (no external cache services or broker daemons required). Restarting the container or process cleanly flushes active cursor state without persistent corruption.
4. **Binary / Container Rollback**:
   Re-deploy a previously verified image by digest (`ghcr.io/diaszano/pgscope@sha256:<verified-release-digest>`; placeholder only) or a wheel from a verified GitHub Release. Do not assume a mutable tag or release artifact exists until verified.
5. **Publish-Only Recovery**:
   If release publication fails midway (e.g., GitHub Release exists but container promotion timed out), trigger `.github/workflows/retry-publish.yml` with the validated release tag to safely republish without bumping versions. If only the standalone binaries or the Homebrew cask failed, run `.github/workflows/binaries.yml` manually (`workflow_dispatch`) with the same tag.
