#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Starting Xeno Mini CRM (Docker required)..."
cd "$ROOT"
docker compose up --build
