#!/usr/bin/env python3
"""Generate sqlite-vec.h from sqlite-vec.h.tmpl.

Portable stand-in for `make sqlite-vec.h`, which shells out to envsubst and
date(1). Those are not guaranteed to exist on the Windows runners used to build
the win_arm64 wheel, so this script performs the same substitution in Python.
"""

import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "sqlite-vec.h.tmpl"
OUTPUT = ROOT / "sqlite-vec.h"


def git(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return result.stdout.strip()


def main() -> int:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not version:
        print("VERSION is empty", file=sys.stderr)
        return 1

    numeric = re.split(r"[-+]", version, maxsplit=1)[0]
    parts = numeric.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        print(f"VERSION {version!r} is not MAJOR.MINOR.PATCH", file=sys.stderr)
        return 1

    date = git("log", "-n", "1", "--pretty=format:%cI", "--", "VERSION")
    if not date:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    source = git("log", "-n", "1", "--pretty=format:%H", "--", "VERSION")

    rendered = TEMPLATE.read_text(encoding="utf-8")
    for placeholder, value in (
        ("${VERSION_MAJOR}", parts[0]),
        ("${VERSION_MINOR}", parts[1]),
        ("${VERSION_PATCH}", parts[2]),
        ("${VERSION}", version),
        ("${DATE}", date),
        ("${SOURCE}", source),
    ):
        rendered = rendered.replace(placeholder, value)

    if OUTPUT.exists() and OUTPUT.read_text(encoding="utf-8") == rendered:
        print(f"{OUTPUT.name} already up to date")
        return 0

    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"wrote {OUTPUT.name} (v{version})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())