#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

pkill -f "uvicorn src.main:app" >/dev/null 2>&1 || true

cd "$repo_root/backend"
source "$repo_root/copilotcompanion/bin/activate"
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
