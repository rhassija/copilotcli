# Git Commit Guide - What to Share

**Last Updated**: February 22, 2026

---

## ✅ What to COMMIT (Share in Git)

### Source Code
- ✅ `backend/` - All Python source code
- ✅ `frontend/src/` - All TypeScript/React source code
- ✅ `specs/` - Feature specifications
- ✅ `scripts/` - Build and run scripts
  - ✅ `build-docker-allinone.sh`
  - ✅ `run-docker-allinone.sh`
  - ✅ `start-all.sh`
  - ✅ `restart-backend.sh`
  - ✅ `restart-frontend.sh`

### Configuration Files
- ✅ `Dockerfile.allinone` - Docker image definition
- ✅ `docker-compose.yml` - Docker Compose configuration
- ✅ `docker-compose.allinone.yml` - All-in-one compose config
- ✅ `.dockerignore` - Docker build exclusions
- ✅ `package.json` - Node.js dependencies
- ✅ `requirements.txt` - Python dependencies
- ✅ `.env.example` - Environment variable template
- ✅ `tsconfig.json` - TypeScript configuration
- ✅ `next.config.js` - Next.js configuration
- ✅ `tailwind.config.js` - Tailwind CSS configuration

### Documentation
- ✅ `README.md` - Project overview
- ✅ `DOCKER-DEPLOYMENT.md` - Docker deployment guide
- ✅ `DOCKER-QUICK-REFERENCE.md` - Quick command reference
- ✅ `DOCKER-DEPLOYMENT-SUMMARY.md` - Deployment summary
- ✅ `DOCS-INDEX.md` - Documentation navigation
- ✅ `DEPLOYMENT.md` - All deployment options
- ✅ `docs/QUICKSTART.md` - Getting started guide
- ✅ `docs/ARCHITECTURE.md` - Technical architecture
- ✅ `TESTING-GUIDE.md` - Testing instructions
- ✅ `IMPLEMENTATION-SUMMARY.md` - Implementation status
- ✅ `PLAN-TASK-GENERATION-GUIDE.md` - Workflow guide

### Git Configuration
- ✅ `.gitignore` - Files to exclude from Git

---

## ❌ What NOT to COMMIT (Exclude from Git)

### Build Artifacts
- ❌ `frontend/.next/` - Next.js build output
- ❌ `frontend/dist/` - Production build
- ❌ `frontend/build/` - Build directory
- ❌ `backend/__pycache__/` - Python bytecode
- ❌ `backend/dist/` - Python distribution files
- ❌ `*.pyc`, `*.pyo` - Compiled Python files

### Dependencies
- ❌ `frontend/node_modules/` - Node.js packages (install with npm)
- ❌ `backend/env/` - Python virtual environment (create locally)
- ❌ `backend/venv/` - Python virtual environment
- ❌ `copilotcompanion/` - May be committed if pre-existing, otherwise exclude

### Runtime Data & Logs
- ❌ `.docker-data/` - Docker runtime persistent storage
- ❌ `.docker-data-*/` - Multiple instance data
- ❌ `backend/.data/` - Backend runtime data
- ❌ `.data/` - Any data directory
- ❌ `*.log` - Log files
- ❌ `npm-debug.log*` - npm debug logs

### Secrets & Environment
- ❌ `.env` - Environment variables with secrets
- ❌ `.env.local` - Local environment overrides
- ❌ `.env.*.local` - Any local env files
- ❌ Any files containing GitHub tokens, API keys, passwords

### Docker Images & Exports
- ❌ `*.tar.gz` - Docker image exports (too large for Git)
- ❌ `copilot-companion*.tar.gz` - Specifically named exports
- ❌ `docker-save-*.tar.gz` - Docker save outputs

### IDE & OS Files
- ❌ `.vscode/` - VS Code settings (or add to .gitignore exceptions)
- ❌ `.idea/` - IntelliJ/WebStorm settings
- ❌ `.DS_Store` - macOS metadata
- ❌ `Thumbs.db` - Windows thumbnails
- ❌ `*.swp`, `*.swo` - Vim swap files

### Test & Coverage
- ❌ `coverage/` - Test coverage reports
- ❌ `.pytest_cache/` - pytest cache
- ❌ `htmlcov/` - HTML coverage reports

### Temporary Files
- ❌ `*.tmp`, `*.temp` - Temporary files
- ❌ `*.cache` - Cache files
- ❌ `*.bak` - Backup files

---

## 🐳 Docker Image - Should You Upload to GitHub?

### ❌ **NO - Do NOT Upload Docker Image to GitHub**

**Reasons:**
1. **Too Large**: The image is ~2GB (600-700MB compressed)
2. **GitHub Limits**: GitHub has file size limits (100MB recommended max)
3. **Not Source Code**: GitHub is for source code, not binary artifacts
4. **Bandwidth Cost**: Every clone would download the huge image
5. **Version Control**: Images don't benefit from Git's diff/merge features

### ✅ **Instead, Share Docker Image via:**

#### Option 1: Docker Hub (Recommended for Teams)

**Advantages:**
- Purpose-built for Docker images
- Free public repositories
- Easy pull/push
- Automatic build integration

**How to:**
```bash
# You push once:
docker login
docker tag copilot-companion:allinone yourusername/copilot-companion:latest
docker push yourusername/copilot-companion:latest

# Others pull:
docker pull yourusername/copilot-companion:latest
```

**Cost:** Free for public repos, $5-9/month for private

#### Option 2: Let People Build from Source (Best for Open Source)

**Advantages:**
- No hosting cost
- Always up-to-date with latest code
- Transparent what's in the image
- Users can customize

**How to:**
```bash
# Share repository URL, they run:
git clone https://github.com/your-org/copilotcli.git
cd copilotcli
./scripts/build-docker-allinone.sh
./scripts/run-docker-allinone.sh
```

**Cost:** Free

#### Option 3: Image File via Cloud Storage (For Limited Distribution)

**Advantages:**
- Works for private/closed distribution
- One-time setup
- No Docker Hub account needed

**How to:**
```bash
# You create:
docker save copilot-companion:allinone | gzip > copilot-companion.tar.gz

# Upload to:
- Google Drive
- Dropbox
- AWS S3
- Company network share

# They download and load:
gunzip -c copilot-companion.tar.gz | docker load
```

**Cost:** Depends on cloud storage provider

#### Option 4: Private Docker Registry (For Enterprises)

**Advantages:**
- Full control
- Private and secure
- Integrates with company infrastructure

**Options:**
- AWS ECR (Elastic Container Registry)
- Azure Container Registry
- Google Container Registry
- Self-hosted Docker Registry

**Cost:** $0.10-0.50 per GB stored (varies)

---

## 📦 What to Include in Your GitHub Repository

### Minimal Required Files

```
copilotcli/
├── .gitignore                      ✅ COMMIT
├── README.md                       ✅ COMMIT
├── Dockerfile.allinone             ✅ COMMIT
├── docker-compose.yml              ✅ COMMIT
├── DOCKER-DEPLOYMENT.md            ✅ COMMIT
├── backend/
│   ├── src/                        ✅ COMMIT (all source code)
│   ├── requirements.txt            ✅ COMMIT
│   ├── .env.example                ✅ COMMIT
│   └── .data/                      ❌ EXCLUDE
├── frontend/
│   ├── src/                        ✅ COMMIT (all source code)
│   ├── package.json                ✅ COMMIT
│   ├── .env.example                ✅ COMMIT
│   ├── node_modules/               ❌ EXCLUDE
│   └── .next/                      ❌ EXCLUDE
├── scripts/
│   ├── build-docker-allinone.sh    ✅ COMMIT
│   ├── run-docker-allinone.sh      ✅ COMMIT
│   └── start-all.sh                ✅ COMMIT
├── docs/                           ✅ COMMIT (all documentation)
├── specs/                          ✅ COMMIT (feature specs)
├── .docker-data/                   ❌ EXCLUDE
└── copilot-companion.tar.gz        ❌ EXCLUDE
```

---

## 🚀 Recommended Git Workflow

### 1. Check What's Changed

```bash
git status
```

### 2. Add Files to Commit

```bash
# Add all new documentation
git add DOCKER-*.md DOCS-INDEX.md

# Add scripts
git add scripts/build-docker-allinone.sh
git add scripts/run-docker-allinone.sh
git add scripts/start-all.sh

# Add Dockerfile
git add Dockerfile.allinone

# Add updated docs
git add README.md DEPLOYMENT.md docs/QUICKSTART.md

# Add code changes
git add backend/src/services/github_client.py
git add .gitignore
```

### 3. Commit with Clear Message

```bash
git commit -m "Add Docker all-in-one deployment

- Created Dockerfile.allinone for single container deployment
- Added build and run automation scripts
- Updated branch discovery to include numeric branches (001-*, 002-*)
- Added comprehensive Docker deployment documentation
- Updated .gitignore to exclude runtime data and exports"
```

### 4. Push to GitHub

```bash
git push origin main
```

---

## ✅ Pre-Commit Checklist

Before committing, verify:

- [ ] No `.env` files with secrets
- [ ] No GitHub tokens in code
- [ ] No `.docker-data/` directories
- [ ] No `*.tar.gz` Docker image exports
- [ ] No `node_modules/` directories
- [ ] No Python `__pycache__/` directories
- [ ] No `.next/` build artifacts
- [ ] All scripts have execute permissions (`chmod +x`)
- [ ] `.env.example` has placeholders, not real values
- [ ] Documentation is up-to-date

---

## 📋 Quick Commands

### Check what will be committed:
```bash
git status
git diff --cached
```

### Remove accidentally staged file:
```bash
git reset HEAD <file>
```

### Remove file from Git but keep locally:
```bash
git rm --cached <file>
echo "<file>" >> .gitignore
```

### Clean untracked files (careful!):
```bash
git clean -fd -n  # Dry run
git clean -fd     # Actually clean
```

---

## 🎯 Summary

### ✅ DO Commit to GitHub:
- Source code
- Configuration files (without secrets)
- Documentation
- Build scripts
- Dockerfile
- .env.example templates

### ❌ DON'T Commit to GitHub:
- Docker images (*.tar.gz)
- Runtime data (.docker-data/, .data/)
- Dependencies (node_modules/, venv/)
- Secrets (.env, tokens)
- Build artifacts (.next/, dist/)
- IDE files (.vscode/, .idea/)
- Log files (*.log)

### 🐳 For Docker Image Sharing:
1. **Best for Open Source**: Let people build from source
2. **Best for Teams**: Share via Docker Hub
3. **Best for Limited Distribution**: Image file via cloud storage
4. **Best for Enterprise**: Private Docker registry

---

**Last Updated**: February 22, 2026  
**Related Docs**: 
- [DOCKER-DEPLOYMENT.md](DOCKER-DEPLOYMENT.md) - How to share images
- [README.md](README.md) - Project overview
- [.gitignore](.gitignore) - Exclusion patterns
