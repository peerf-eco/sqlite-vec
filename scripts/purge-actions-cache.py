#!/usr/bin/env python3
"""Delete GitHub Actions cache entries for a repository older than a max age.

GitHub gives no control over cache TTL (entries linger for 7 days after last
access) and offers no way to schedule a purge, so workflows call this to
implement a short, explicit retention window.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://api.github.com"


def request(method: str, url: str, token: str) -> tuple[int, dict | list]:
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "sqlite-vec-cache-purge")
    try:
        with urllib.request.urlopen(req) as response:
            body = response.read()
            return response.status, (json.loads(body) if body else {})
    except urllib.error.HTTPError as exc:
        body = exc.read()
        try:
            return exc.code, (json.loads(body) if body else {})
        except json.JSONDecodeError:
            return exc.code, {"message": body.decode("utf-8", "replace")}


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument(
        "--max-age-minutes",
        type=int,
        default=60,
        help="delete caches not accessed within this window (default: 60)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="list what would be deleted without deleting",
    )
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("GITHUB_TOKEN or GH_TOKEN must be set", file=sys.stderr)
        return 1

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=args.max_age_minutes)
    deleted = 0
    page = 1
    while True:
        status, payload = request(
            "GET", f"{API}/repos/{args.repo}/actions/caches?per_page=100&page={page}", token
        )
        if status != 200:
            print(f"error listing caches: {status} {payload}", file=sys.stderr)
            return 1
        caches = payload.get("actions_caches", [])
        if not caches:
            break

        for entry in caches:
            last_accessed = parse_timestamp(entry["last_accessed_at"])
            if last_accessed > cutoff:
                continue
            key = entry["key"]
            cache_id = entry["id"]
            if args.dry_run:
                print(f"would delete {cache_id} {key} (last accessed {last_accessed})")
                deleted += 1
                continue
            status, payload = request(
                "DELETE", f"{API}/repos/{args.repo}/actions/caches/{cache_id}", token
            )
            if status in (204, 200, 404):
                print(f"deleted {cache_id} {key} (last accessed {last_accessed})")
                deleted += 1
            else:
                print(f"error deleting {cache_id} {key}: {status} {payload}", file=sys.stderr)
                return 1

        page += 1

    print(f"{deleted} cache entr{'y' if deleted == 1 else 'ies'} older than {args.max_age_minutes}m removed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())