#!/bin/bash

# Git Add Script - Commit Docker Deployment Changes
# This script adds all the files that should be committed for Docker deployment

set -e

echo "=================================================="
echo "      Git Add - Docker Deployment Files"
echo "=================================================="
echo ""

cd "$(dirname "$0")/.."

echo "Adding new documentation files..."
git add DOCKER-DEPLOYMENT.md
git add DOCKER-QUICK-REFERENCE.md
git add DOCKER-DEPLOYMENT-SUMMARY.md
git add DOCS-INDEX.md
git add GIT-COMMIT-GUIDE.md

echo "Adding Docker configuration..."
git add Dockerfile.allinone
git add docker-compose.allinone.yml 2>/dev/null || echo "  (docker-compose.allinone.yml not found, skipping)"

echo "Adding build and run scripts..."
git add scripts/build-docker-allinone.sh
git add scripts/run-docker-allinone.sh
git add scripts/start-all.sh

echo "Adding updated documentation..."
git add README.md
git add DEPLOYMENT.md
git add docs/QUICKSTART.md

echo "Adding .gitignore changes..."
git add .gitignore

echo "Adding code changes..."
git add backend/src/services/github_client.py
git add backend/src/api/repositories.py 2>/dev/null || true
git add backend/src/services/storage.py 2>/dev/null || true
git add backend/src/main.py 2>/dev/null || true
git add frontend/src/app/features/page.tsx 2>/dev/null || true

echo ""
echo "✅ Files staged for commit!"
echo ""
echo "Next steps:"
echo "  1. Review changes:    git status"
echo "  2. Review diff:       git diff --cached"
echo "  3. Commit:            git commit -m 'Your message'"
echo "  4. Push:              git push origin main"
echo ""
echo "Suggested commit message:"
echo "---"
cat << 'EOF'
Add Docker all-in-one deployment and documentation

- Created Dockerfile.allinone for single container deployment
- Added build-docker-allinone.sh and run-docker-allinone.sh scripts
- Updated branch discovery to support numeric branches (001-*, 002-*)
- Added comprehensive Docker deployment documentation:
  - DOCKER-DEPLOYMENT.md (complete guide)
  - DOCKER-QUICK-REFERENCE.md (command cheat sheet)
  - DOCKER-DEPLOYMENT-SUMMARY.md (summary)
  - DOCS-INDEX.md (documentation navigation)
  - GIT-COMMIT-GUIDE.md (what to commit)
- Updated README.md, DEPLOYMENT.md, and QUICKSTART.md
- Updated .gitignore to exclude runtime data and Docker exports
- Fixed authentication and session management issues
- Added persistent storage support

Docker image: copilot-companion:allinone
Build: ./scripts/build-docker-allinone.sh
Run: ./scripts/run-docker-allinone.sh
EOF
echo "---"
