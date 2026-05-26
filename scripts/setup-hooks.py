#!/usr/bin/env python
"""
One-time git hook setup for PyConfigre.

Run with:
    uv run python scripts/setup-hooks.py

Configures git to use the hooks in `.githooks/` and sets the executable
bit on each hook file. Works on Windows, macOS, and Linux.
"""

import subprocess
import sys
from pathlib import Path

HOOKS = [
    ".githooks/commit-msg",
    ".githooks/post-checkout",
]


def main() -> int:
    root = Path(__file__).parent.parent

    result = subprocess.run(
        ["git", "config", "core.hooksPath", ".githooks"],
        cwd=root,
    )
    if result.returncode != 0:
        print("❌ Failed to set core.hooksPath.", file=sys.stderr)
        return 1

    for hook in HOOKS:
        hook_path = root / hook
        if not hook_path.exists():
            print(f"⚠️  Hook not found, skipping: {hook}")
            continue
        hook_path.chmod(0o755)
        print(f"✅ Executable bit set: {hook}")

    print("\n✅ Git hooks configured. You're all set.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
