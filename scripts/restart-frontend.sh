#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

pkill -f "next dev" >/dev/null 2>&1 || true

cd "$repo_root/frontend"
npm run dev
