#!/usr/bin/env python3
"""Deploy backend + channel service to Render via Blueprint API."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_env() -> None:
    for env_file in (ROOT / ".env", ROOT / "backend" / ".env"):
        if not env_file.exists():
            continue
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def api_request(method: str, path: str, payload: dict | None = None) -> dict:
    token = os.environ.get("RENDER_API_KEY") or os.environ.get("RENDER_TOKEN")
    if not token:
        raise RuntimeError("RENDER_API_KEY is not set in .env")

    data = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        f"https://api.render.com/v1{path}",
        data=data,
        headers=headers,
        method=method,
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read().decode()
        return json.loads(body) if body else {}


def main() -> int:
    load_env()
    repo = os.environ.get("GITHUB_REPO", "https://github.com/krishnarawatsf/mini_crm")
    branch = os.environ.get("GITHUB_BRANCH", "main")

    try:
        result = api_request(
            "POST",
            "/blueprints",
            {
                "repo": repo,
                "branch": branch,
                "name": "xeno-crm",
            },
        )
    except RuntimeError as exc:
        print(f"SKIP: {exc}")
        print("Add RENDER_API_KEY to .env, then rerun this script.")
        print("Or deploy manually: https://dashboard.render.com/select-repo?type=blueprint")
        return 1
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()
        print(f"FAIL: Render API returned {exc.code}")
        print(detail[:500])
        return 1

    print("OK: Render blueprint created")
    print(json.dumps(result, indent=2)[:1000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
