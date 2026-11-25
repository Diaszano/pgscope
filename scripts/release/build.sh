#!/usr/bin/env bash
# Verify the lockfile and build immutable distributions (wheel + sdist) for a release.
# Run by the release workflow after Release Please has stamped the version in the release PR.

set -euo pipefail

echo "==> Verifying lockfile integrity..."
uv lock --check

echo "==> Building distribution packages (wheel + sdist)..."
uv build

echo "✅ Release build completed successfully."
