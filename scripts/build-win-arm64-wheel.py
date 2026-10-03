#!/usr/bin/env python3
"""Assemble the win_arm64 sqlite-vec wheel.

Upstream ships `py3-none-<platform>` wheels whose only non-Python payload is a
prebuilt vec0 loadable extension, and sqlite-dist has no Windows+AArch64 entry
(it raises `unreachable!()` for that Os/Cpu pair in src/targets/pip.rs). This
script reproduces that layout for Windows on ARM64 so the result is a
drop-in `import sqlite_vec` replacement.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import re
import struct
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

IMAGE_FILE_MACHINE_ARM64 = 0xAA64
IMAGE_NT_OPTIONAL_HDR64_MAGIC = 0x20B

PRE_RELEASE_ALIASES = {
    "a": "a",
    "alpha": "a",
    "b": "b",
    "beta": "b",
    "c": "rc",
    "pre": "rc",
    "preview": "rc",
    "rc": "rc",
}

VERSION_RE = re.compile(
    r"""
    ^
    (?P<release>\d+(?:\.\d+)*)
    (?:[-_.]?(?P<pre_label>alpha|beta|preview|pre|rc|a|b|c)[-_.]?(?P<pre_number>\d+)?)?
    (?:[-_.]?(?P<post_label>rev|r|post)[-_.]?(?P<post_number>\d+)?)?
    (?:\+(?P<local>[a-z0-9]+(?:[-_.][a-z0-9]+)*))?
    $
    """,
    re.VERBOSE | re.IGNORECASE,
)

SUMMARY = (
    "sqlite-vec vector search extension for Python on Windows ARM64 "
    "(win_arm64). The `sqlite-vec` distribution only publishes a win_amd64 "
    "wheel, which cannot be installed on Windows on ARM."
)

INIT_PREAMBLE = '''
from os import path
import sqlite3

__version__ = "{version}"
__version_info__ = tuple(__version__.split("."))

def loadable_path():
  """ Returns the full path to the {package_name} loadable SQLite extension bundled with this package """

  loadable_path = path.join(path.dirname(__file__), "vec0")
  return path.normpath(loadable_path)

def load(conn: sqlite3.Connection)  -> None:
  """ Load the {package_name} SQLite extension into the given database connection. """

  conn.load_extension(loadable_path())
'''


class WheelError(RuntimeError):
    pass


def pep440_version(raw: str) -> str:
    match = VERSION_RE.match(raw.strip())
    if match is None:
        raise WheelError(f"cannot normalize version {raw!r} to PEP 440")

    normalized = match.group("release")
    pre_label = match.group("pre_label")
    if pre_label:
        normalized += PRE_RELEASE_ALIASES[pre_label.lower()]
        if match.group("pre_number"):
            normalized += match.group("pre_number")
    post_label = match.group("post_label")
    if post_label:
        normalized += ".post" + (match.group("post_number") or "0")
    local = match.group("local")
    if local:
        normalized += "+" + re.sub(r"[-_]", ".", local.lower())
    return normalized


def escaped_name(name: str) -> str:
    return re.sub(r"[^\w\d.]+", "_", name, flags=re.UNICODE)


def assert_arm64_pe(path: Path) -> None:
    data = path.read_bytes()
    if len(data) < 0x40 or data[:2] != b"MZ":
        raise WheelError(f"{path} is not a PE image (missing MZ signature)")
    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe_offset : pe_offset + 4] != b"PE\0\0":
        raise WheelError(f"{path} is not a PE image (missing PE signature)")
    machine = struct.unpack_from("<H", data, pe_offset + 4)[0]
    if machine != IMAGE_FILE_MACHINE_ARM64:
        raise WheelError(
            f"{path} targets machine 0x{machine:04x}, expected "
            f"0x{IMAGE_FILE_MACHINE_ARM64:04x} (ARM64)"
        )
    magic = struct.unpack_from("<H", data, pe_offset + 24)[0]
    if magic != IMAGE_NT_OPTIONAL_HDR64_MAGIC:
        raise WheelError(f"{path} is not a PE32+ image (optional header magic 0x{magic:04x})")


def build_init_module(version: str, dist_name: str) -> bytes:
    extra_init = (ROOT / "bindings" / "python" / "extra_init.py").read_text(
        encoding="utf-8"
    )
    preamble = INIT_PREAMBLE.format(version=version, package_name=dist_name)
    return (preamble + extra_init).encode("utf-8")


def record_hash(payload: bytes) -> str:
    digest = hashlib.sha256(payload).digest()
    return "sha256=" + base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def build_wheel(dll: Path, outdir: Path, dist_name: str, description: str) -> Path:
    version = pep440_version((ROOT / "VERSION").read_text(encoding="utf-8").strip())
    name_escaped = escaped_name(dist_name)
    dist_info = f"{name_escaped}-{version}.dist-info"
    wheel_name = f"{name_escaped}-{version}-py3-none-win_arm64.whl"

    assert_arm64_pe(dll)

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    metadata = (
        "Metadata-Version: 2.1\n"
        f"Name: {dist_name}\n"
        f"Version: {version}\n"
        f"Summary: {SUMMARY}\n"
        "License: MIT License, Apache License, Version 2.0\n"
        "Requires-Python: >=3.8\n"
        "Description-Content-Type: text/markdown\n"
        "Project-URL: Source, https://github.com/peerf-eco/sqlite-vec\n"
        "Project-URL: Upstream, https://github.com/asg017/sqlite-vec\n"
        "\n"
        f"{description}\n"
        f"\nUpstream project README follows.\n\n{readme}"
    ).encode("utf-8")

    wheel_metadata = (
        "Wheel-Version: 1.0\n"
        "Generator: sqlite-vec win_arm64 wheel builder\n"
        "Root-Is-Purelib: false\n"
        "Tag: py3-none-win_arm64\n"
    ).encode("utf-8")

    payloads: list[tuple[str, bytes]] = [
        ("sqlite_vec/__init__.py", build_init_module(version, dist_name)),
        ("sqlite_vec/vec0.dll", dll.read_bytes()),
        (f"{dist_info}/METADATA", metadata),
        (f"{dist_info}/WHEEL", wheel_metadata),
        (f"{dist_info}/top_level.txt", b"sqlite_vec\n"),
    ]

    record = io.StringIO()
    writer = csv.writer(record, lineterminator="\n")
    for arcname, payload in payloads:
        writer.writerow([arcname, record_hash(payload), len(payload)])
    writer.writerow([f"{dist_info}/RECORD", "", ""])
    payloads.append((f"{dist_info}/RECORD", record.getvalue().encode("utf-8")))

    outdir.mkdir(parents=True, exist_ok=True)
    wheel_path = outdir / wheel_name
    with zipfile.ZipFile(wheel_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for arcname, payload in payloads:
            info = zipfile.ZipInfo(arcname, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, payload)

    return wheel_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dll", required=True, type=Path, help="path to vec0.dll")
    parser.add_argument("--outdir", type=Path, default=ROOT / "dist")
    parser.add_argument("--dist-name", default="sqlite-vec-win-arm64")
    parser.add_argument("--description", default="")
    args = parser.parse_args()

    if not args.dll.is_file():
        print(f"{args.dll} does not exist", file=sys.stderr)
        return 1

    try:
        wheel_path = build_wheel(args.dll, args.outdir, args.dist_name, args.description)
    except WheelError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        shown = wheel_path.relative_to(ROOT)
    except ValueError:
        shown = wheel_path
    print(shown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())