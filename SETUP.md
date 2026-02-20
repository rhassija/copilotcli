# Setup Guide - Copilot CLI Web UI

Complete instructions for getting the Copilot CLI Web UI running on your machine. Choose the setup method that works best for you.

## 📋 Table of Contents

- [Quick Comparison](#quick-comparison)
- [Method 1: Docker (Easiest)](#method-1-docker-easiest)
- [Method 2: Automated Setup Script](#method-2-automated-setup-script)
- [Method 3: Manual Setup](#method-3-manual-setup)
- [Environment Configuration](#environment-configuration)
- [Verify Installation](#verify-installation)
- [Troubleshooting](#troubleshooting)
- [Useful Commands](#useful-commands)

---

## Quick Comparison

| Aspect | Docker | Setup Script | Manual |
|--------|--------|--------------|--------|
| **Time to Start** | 10-15 min | 5-10 min | 10-15 min |
| **Prerequisites** | Docker only | Python, Node.js | Python, Node.js |
| **Good for** | Testing, demos | Development | Learning, CI/CD |
| **Code Editing** | Limited | Full access | Full access |
| **Performance** | Good | Best | Best |
| **Cross-platform** | ✓ (Mac, Linux, Windows) | ✓ (with WSL on Windows) | ✓ |

---

## Method 1: Docker (Easiest)

### ✓ When to Use
- First time trying the project
- Want to test without installing Python/Node.js
- Want reproducible environment
- Using Windows (Docker is more reliable than WSL)

### Prerequisites
- **Docker Desktop** installed ([Download](https://www.docker.com/products/docker-desktop))
- GitHub Personal Access Token ([Get one](https://github.com/settings/tokens))

### Steps

#### 1. Clone Repository
```bash
git clone https://github.com/your-org/copilotcli.git
cd copilotcli
```

#### 2. Configure Environment
```bash
# Copy environment template
cp .env.template .env

# Edit .env and add your GitHub token
nano .env  # or: code .env
```

Add this line:
```
GITHUB_TOKEN=ghp_your_token_here
```

#### 3. Start Services
```bash
docker-compose up
```

Wait for output like:
```
copilot-ui-frontend  | ▲ Next.js 14.0.4
copilot-ui-frontend  | ○ Listening on http://0.0.0.0:3000
copilot-ui-backend   | Uvicorn running on http://0.0.0.0:8000
```

#### 4. Access Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

#### 5. Stop Services
```bash
docker-compose down
```

### Useful Docker Commands
```bash
# View logs
docker-compose logs -f

# Rebuild images
docker-compose build --no-cache

# Remove volumes (clean slate)
docker-compose down -v

# Run specific service
docker-compose up backend

# Execute command in container
docker exec copilot-ui-backend python -m pytest
```

---

## Method 2: Automated Setup Script (Recommended for Development)

### ✓ When to Use
- Contributing to the project
- Want full IDE support and code editing
- Prefer native development environment
- Need hot-reload with code changes

### Prerequisites

**macOS:**
```bash
# Install Python 3.13
brew install python@3.13

# Install Node.js
brew install node

# Install Git
brew install git
```

**Linux (Ubuntu/Debian):**
```bash
# Install Python 3.13
sudo apt-get update
sudo apt-get install python3.13 python3.13-venv

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install nodejs

# Install Git
sudo apt-get install git
```

**Windows (WSL2):**
```bash
# Same as Linux instructions above
# Or use Windows Subsystem for Linux
```

### Steps

#### 1. Clone Repository
```bash
git clone https://github.com/your-org/copilotcli.git
cd copilotcli
```

#### 2. Run Setup Script
```bash
chmod +x setup.sh
./setup.sh
```

The script will:
- ✓ Check for required software
- ✓ Create Python virtual environment
- ✓ Install Python dependencies
- ✓ Install Node.js dependencies
- ✓ Generate .env files
- ✓ Prompt for GitHub token

#### 3. Follow the Prompts

When prompted, provide your GitHub Personal Access Token:
- Go to: https://github.com/settings/tokens
- Click: "Generate new token (classic)"
- Set scopes: `repo`, `user`
- Paste the token when prompted

#### 4. Start Services

**Option A: Using npm/python directly**

Terminal 1 - Backend:
```bash
source backend/venv/bin/activate
cd backend
python -m uvicorn src.main:app --reload --port 8001
```

Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

**Option B: Using Make (simpler)**
```bash
# Terminal 1
make backend

# Terminal 2
make frontend

# Or run both (needs background execution)
make run
```

#### 5. Access Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs

### Setup Script Options
```bash
# Full setup with all checks
./setup.sh

# Skip dependency version checks
./setup.sh --skip-deps

# Setup for development
./setup.sh --dev

# Show help
./setup.sh --help
```

---

## Method 3: Manual Setup

### ✓ When to Use
- Want full control over installation
- Debugging setup issues
- Learning how the project works
- Integrating with existing tools

### Prerequisites
Same as Method 2 - see [Prerequisites](#prerequisites)

### Backend Setup

#### 1. Create Virtual Environment
```bash
cd backend
python3.13 -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows
```

#### 2. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Configure Environment
```bash
cp .env.example .env.local
# Edit .env.local and add GITHUB_TOKEN
nano .env.local
```

#### 4. Start Backend Server
```bash
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Application startup complete
```

### Frontend Setup

#### 1. Install Dependencies
```bash
cd frontend
npm install
```

#### 2. Configure Environment
```bash
cp .env.example .env.local
# Edit .env.local - usually no changes needed for local dev
nano .env.local
```

#### 3. Start Development Server
```bash
npm run dev
```

You should see:
```
> next dev
▲ Next.js 14.0.4
○ Listening on http://0.0.0.0:3000
```

### Access Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs

---

## Environment Configuration

### GitHub Personal Access Token (Required)

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a name: `copilot-cli-web`
4. Select scopes:
   - ✓ `repo` (access repositories)
   - ✓ `user` (read user profile)
5. Click "Generate token"
6. **Copy immediately** (won't be shown again!)
7. Add to your `.env` or `.env.local`:
   ```
   GITHUB_TOKEN=ghp_your_token_here
   ```

### Environment Variables Reference

See `.env.template` for complete documentation of all variables:

**Backend (.env.local):**
```
# Required
GITHUB_TOKEN=ghp_...
PORT=8001

# Optional (defaults provided)
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000
```

**Frontend (.env.local):**
```
# Usually works as-is for local development
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_WS_URL=ws://localhost:8001
```

---

## Verify Installation

### Checklist

- [ ] Backend running on http://localhost:8001
- [ ] Frontend running on http://localhost:3000
- [ ] Can access http://localhost:8001/docs (API documentation)
- [ ] Can login with GitHub token
- [ ] Can see repositories in the UI
- [ ] WebSocket connection established (check browser console)

### Quick Test Commands

```bash
# Backend health check
curl http://localhost:8001/health

# Frontend is up
curl http://localhost:3000

# Check WebSocket
wscat -c ws://localhost:8001/api/v1/ws
```

### Browser Console Check

Open http://localhost:3000 and check browser console (F12):
```javascript
// Should see WebSocket connection
console.log('WebSocket connected')

// Should see API calls
// Look in Network tab for /api/v1/... requests
```

---

## Troubleshooting

### Issue: "Python 3.13 not found"

**Solution:**
```bash
# Check Python version
python3 --version

# If you have Python 3.12, you can use it (mostly compatible)
python3 -m venv venv

# Or install Python 3.13
brew install python@3.13  # macOS
sudo apt-get install python3.13  # Linux
```

### Issue: "pip install fails"

**Solution:**
```bash
# Upgrade pip
pip install --upgrade pip

# Try again
pip install -r requirements.txt

# If still failing, install packages individually
pip install fastapi uvicorn pydantic aiohttp requests PyGithub python-dotenv
```

### Issue: "Port 8001/3000 already in use"

**Solution:**
```bash
# Kill processes using the port
lsof -ti :8001 | xargs kill -9  # Backend
lsof -ti :3000 | xargs kill -9  # Frontend

# Or use different ports
cd backend
python -m uvicorn src.main:app --reload --port 8002

# In frontend
npm run dev -- -p 3001
```

### Issue: "Cannot connect to backend from frontend"

**Solution:**
Check `.env.local` in frontend:
```bash
# Should be:
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_WS_URL=ws://localhost:8001

# If using Docker, use container names:
NEXT_PUBLIC_API_URL=http://backend:8000
NEXT_PUBLIC_WS_URL=ws://backend:8000
```

### Issue: "Git authentication error"

**Solution:**
```bash
# Update GitHub token
# 1. Generate new token at https://github.com/settings/tokens
# 2. Update .env.local with new token
# 3. Restart services

# Verify token
curl -H "Authorization: token ghp_your_token" https://api.github.com/user
```

### Issue: "Docker build fails"

**Solution:**
```bash
# Clean Docker cache
docker system prune -a

# Rebuild with no cache
docker-compose build --no-cache

# Check Docker logs
docker-compose logs
```

---

## Useful Commands

### Using Make

```bash
# Show all available commands
make help

# Setup
make setup

# Development
make backend        # Run backend
make frontend       # Run frontend
make run           # Run both

# Testing
make test          # All tests
make test-backend  # Backend tests only
make lint          # Run linters
make format        # Auto-format code

# Docker
make docker-up     # Start Docker services
make docker-down   # Stop Docker services

# Cleanup
make clean         # Clean build artifacts
make clean-all     # Clean including dependencies
```

### Manual Commands

```bash
# Backend
cd backend
source venv/bin/activate
python -m uvicorn src.main:app --reload --port 8001

# Frontend
cd frontend
npm run dev

# Testing
cd backend
pytest -v

# Linting
cd backend
flake8 src
black src --check

# Type checking
cd backend
mypy src
cd ../frontend
npm run type-check
```

### Stopping Services

```bash
# Stop individual services (press Ctrl+C in terminal)

# Or stop all
make stop

# Or manually
pkill -f "uvicorn src.main:app"
pkill -f "next dev"
```

---

## Next Steps

- [ ] Read [docs/QUICKSTART.md](../docs/QUICKSTART.md) for advanced usage
- [ ] Read [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) to understand the codebase
- [ ] Check [README.md](../README.md) for overview
- [ ] Start developing!

## Getting Help

- **Setup issues?** Check [Troubleshooting](#troubleshooting)
- **Code questions?** Read [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)
- **Found a bug?** Create a GitHub issue
- **Want to contribute?** See [CONTRIBUTING.md](../CONTRIBUTING.md)

---

**Last Updated:** February 2026
