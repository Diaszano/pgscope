from __future__ import annotations

import os
from pathlib import Path


def test_build_script_structure() -> None:
    root = Path(__file__).resolve().parents[2]
    script_path = root / "scripts" / "release" / "build.sh"

    assert script_path.is_file(), "scripts/release/build.sh missing"
    assert os.access(script_path, os.X_OK), "scripts/release/build.sh must be executable"

    content = script_path.read_text(encoding="utf-8")
    assert "set -euo pipefail" in content, "Script must use strict error handling"
    assert "uv lock --check" in content, "Script must verify lockfile consistency"
    assert "uv build" in content, "Script must invoke uv build"
