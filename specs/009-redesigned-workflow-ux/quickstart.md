# Developer Quickstart Guide

**Phase**: Phase 1 Design  
**Date**: February 18, 2026  
**Target Audience**: Backend and frontend developers beginning Phase 2 implementation  
**Status**: ✅ Complete

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Setup](#project-setup)
3. [Local Development](#local-development)
4. [First Workflow](#first-workflow)
5. [Testing](#testing)
6. [Debugging Tips](#debugging-tips)
7. [Common Issues](#common-issues)
8. [Architecture Overview](#architecture-overview)

---

## Prerequisites

### Required Software

- **Python 3.13**: Backend runtime (via pre-existing `copilotcompanion` virtual environment)
- **Node.js 18+**: Frontend runtime + npm/yarn
- **Git**: Version control

### Python Virtual Environment (Pre-Created)

The `copilotcompanion` Python 3.13 virtual environment is pre-created at `./copilotcompanion/` and must be used for all backend work:

```bash
# Activate the environment
source ./copilotcompanion/bin/activate

# Verify activation (should show Python 3.13.x)
python --version

# Verify correct pip
which pip  # Should show ./copilotcompanion/bin/pip
```

**All backend tasks (setup, development, testing) MUST use this environment.**

### Required Accounts & Tokens

- **GitHub Account**: To test repository operations
- **GitHub Personal Access Token (PAT)**: For local development
  - Scopes needed: `repo`, `workflow`
  - [Generate PAT](https://github.com/settings/tokens?type=beta)
  - Store securely; never commit to repo

### Required Knowledge

- Basic Python (FastAPI familiarity helpful)
- Basic JavaScript/React (TypeScript assumed)
- Git workflows (branches, commits)
- GitHub API concepts (optional, documented inline)

---

## Project Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/copilot-ui.git
cd copilot-ui
```

### 2. Backend Setup

```bash
cd backend

# Activate pre-existing copilotcompanion environment (from repo root)
source ../copilotcompanion/bin/activate

# Verify correct environment
python --version  # Should show Python 3.13.x

# Install dependencies (or update if already installed)
pip install -r requirements.txt

# Create .env file from template
cp .env.example .env

# Add your GitHub token to .env
# GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
# COPILOT_TOKEN=xxxx (if separate)

# Verify setup
python -c "import fastapi; print(f'FastAPI {fastapi.__version__} installed')"
```

**IMPORTANT**: Always use the `copilotcompanion` environment for all backend work. Never create a new venv.

**Backend Directory Structure**:
```
backend/
├── src/
│   ├── main.py              # FastAPI app
│   ├── models/              # Data models
│   ├── services/            # Business logic
│   ├── api/                 # API endpoints
│   └── utils/               # Utilities
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
├── venv/                   # Virtual environment
└── README.md
```

### 3. Frontend Setup

```bash
cd ../frontend

# Install Node dependencies
npm install  # or yarn install

# Create .env.local from template
cp .env.example .env.local

# Update API endpoints (if custom backend URL)
# NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Verify setup
npm --version
npx next --version
```

**Frontend Directory Structure**:
```
frontend/
├── src/
│   ├── pages/
│   │   ├── index.tsx        # Home/redirect
│   │   ├── login.tsx        # Auth flow
│   │   └── workflow.tsx     # Main app
│   ├── components/          # Reusable components
│   ├── services/            # API + WebSocket clients
│   ├── hooks/               # Custom React hooks
│   ├── types/               # TypeScript interfaces
│   └── utils/               # Utilities
├── public/                  # Static assets
├── tests/                   # Test files
├── package.json
├── tsconfig.json
└── next.config.js
```

### 4. Docker Compose (Optional)

For all-in-one local environment:

```bash
cd ..
docker-compose up
```

This starts:
- Backend API on http://localhost:8000
- Frontend on http://localhost:3000
- (Optional) Mock GitHub API server on http://localhost:9000

---

## Local Development

### Starting Backend Server

```bash
cd backend

# Activate virtual environment
source venv/bin/activate

# Start uvicorn development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**API Documentation**: Open http://localhost:8000/docs (Swagger UI)

### Starting Frontend Dev Server

```bash
cd frontend
npm run dev
```

**Expected output**:
```
> next dev
  ▲ Next.js 14.0.0
  - Local:        http://localhost:3000
  - Environments: .env.local
```

**Open**: http://localhost:3000 in your browser

### Verifying Setup

**Backend health check**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/verify \
  -H "Content-Type: application/json" \
  -d '{"token": "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"}'
```

**Frontend loads**: http://localhost:3000 should show login screen

---

## First Workflow

### Step 1: Authenticate

1. Open http://localhost:3000
2. Click "Authenticate with GitHub"
3. Paste your GitHub PAT in the token input field
4. Click "Verify"
5. You should see "Authentication successful" message

**Behind the scenes**:
- Frontend sends POST /auth/verify to backend
- Backend validates token via GitHub API `/user` endpoint
- Backend returns user info (login, avatar)
- Frontend stores token in sessionStorage
- Frontend redirects to repo selector

### Step 2: Select Repository

1. Browse or search for a GitHub repository (e.g., your own fork)
2. Click to select it
3. You should see existing branches listed

**Behind the scenes**:
- Frontend fetches GET /repos?search=... from backend
- Backend calls GitHub API to list repositories
- Results are cached for 5 minutes
- Branch list fetched via GET /repos/{owner}/{repo}/branches

### Step 3: Create Feature

1. Click "Create New Feature"
2. Enter feature name (e.g., "user-authentication")
3. Choose source branch (usually "main")
4. Click "Create"

**Behind the scenes**:
- Frontend calls POST /repos/{owner}/{repo}/branches
- Backend invokes Copilot CLI: `copilot init-feature --branch-name feature/user-authentication`
- Copilot CLI creates branch on GitHub + initializes spec.md template
- Frontend receives WebSocket stream of messages during creation
- Feature is now ready for specification

### Step 4: Create Specification

1. Select the feature just created
2. Click on "Spec" tab
3. Click "Create New Spec" or "Generate Spec"
4. (If generate): Watch real-time WebSocket messages as Copilot CLI generates spec

**Manually create spec**:
1. Click text area and paste/type specification markdown
2. Click "Save" → Persists to GitHub repo

### Step 5: Trigger Clarify Operation

1. Click "Clarify" button on Spec tab
2. Watch WebSocket conversation panel
3. You'll see:
   - "thinking" messages (analysis)
   - "execution" messages (questions/results)
   - "complete" message (done)

**Behind the scenes**:
- Frontend opens WebSocket `/ws?operation_id=op_abc123`
- Backend spawns: `copilot clarify --spec-file specs/{id}/spec.md`
- Copilot CLI streams thinking + execution output
- Each line becomes a WebSocket message
- On completion, spec.md updates in GitHub

### Step 6: View Plan Tab

1. Click "Plan" tab
2. Click "Generate Plan" or "Create Plan"
3. Watch real-time generation

**Spec → Plan flow**:
- Backend checks spec exists and is valid
- Backend invokes: `copilot plan --spec-file ... --output-plan-file ...`
- Copilot CLI generates plan.md
- Plan.md pushed to GitHub branch
- Frontend displays plan content

---

## Testing

### Backend Unit Tests

```bash
cd backend

# Run all tests
pytest tests/unit

# Run specific test file
pytest tests/unit/test_github_client.py

# Run with coverage
pytest --cov=src tests/unit

# Run specific test
pytest tests/unit/test_github_client.py::test_validate_token_success
```

**Expected output**:
```
tests/unit/test_github_client.py::test_validate_token_success PASSED
tests/unit/test_github_client.py::test_validate_token_expired PASSED
...
===== 15 passed in 1.23s =====
```

### Frontend Component Tests

```bash
cd frontend

# Run component tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage
```

### Integration Tests

```bash
cd backend

# Run integration tests (may require real GitHub API)
pytest tests/integration -v

# Skip slow tests
pytest tests/integration -v -m "not slow"
```

### End-to-End Tests

```bash
cd frontend

# Run E2E tests (requires backend running)
npm run test:e2e

# Run specific test
npm run test:e2e -- --grep "Create Feature"

# Run in debug mode
npm run test:e2e:debug
```

---

## Debugging Tips

### Backend Debugging

**Enable verbose logging**:
```python
# In src/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

**Inspect requests**:
```bash
# Swagger UI: http://localhost:8000/docs
# Try endpoints interactively, see request/response

# Or use curl:
curl -v http://localhost:8000/api/v1/repos \
  -H "Authorization: Bearer ghp_xxxx"
```

**Debug subprocess output**:
```python
# In services/copilot_runner.py
process = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
for line in process.stdout:
    print(f"[COPILOT] {line.rstrip()}")  # See CLI output
```

**Check environment variables**:
```bash
echo $GITHUB_TOKEN  # Verify token is set
env | grep GITHUB   # List all GitHub-related vars
```

### Frontend Debugging

**Browser DevTools**:
- Open http://localhost:3000
- Press F12 → Developer Tools
- Console tab: See error messages
- Network tab: Inspect API calls
- Storage tab: View sessionStorage (token)

**React DevTools**:
- Install [React DevTools extension](https://react-devtools-tutorial.vercel.app/)
- Inspect component props, state, hooks

**WebSocket Debugging**:
```javascript
// Add to src/services/websocket.ts
ws.addEventListener('open', () => console.log('[WS] Connected'));
ws.addEventListener('message', (event) => {
  console.log('[WS] Message:', JSON.parse(event.data));
});
ws.addEventListener('error', (event) => {
  console.error('[WS] Error:', event);
});
ws.addEventListener('close', () => console.log('[WS] Closed'));
```

### Common DevTools Combos

**Check API response**:
1. Open DevTools Network tab
2. Perform action (e.g., click "Authenticate")
3. Look for POST request to /auth/verify
4. Click request → Preview/Response tabs

**Inspect React state**:
1. Install React DevTools
2. Open React tab in DevTools
3. Click component in component tree
4. See props and state on right panel
5. Edit state to test changes

---

## Common Issues

### Issue: "GitHub token invalid" error

**Cause**: Token expired, revoked, or wrong format

**Solution**:
1. Check token in GitHub settings: https://github.com/settings/tokens
2. Regenerate if needed
3. Verify it has `repo` + `workflow` scopes
4. Update `.env` file
5. Restart backend: `Ctrl+C` then `uvicorn src.main:app --reload`

### Issue: "Module not found: FastAPI"

**Cause**: Python dependencies not installed

**Solution**:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Port 8000 already in use"

**Cause**: Another process running on port 8000

**Solution**:
```bash
# On macOS/Linux
lsof -i :8000
kill -9 <PID>

# Or use different port
uvicorn src.main:app --port 8001
```

### Issue: "Connection refused" when calling API from frontend

**Cause**: Backend not running OR CORS not enabled

**Solution**:
1. Check backend is running: http://localhost:8000/docs should load
2. Backend must have CORS middleware enabled:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
3. Restart backend

### Issue: WebSocket reconnection not working

**Cause**: Message queue not retained server-side OR client not sending last_received_sequence

**Solution**:
1. Check server is storing messages in memory/Redis
2. Client should send reconnection URL with `last_received_sequence` query param
3. Verify backend responds with replay messages

---

## Architecture Overview

### Workflow Layers

```
┌───────────────────────────────────────────────────────────┐
│ Browser (Frontend: React/Next.js)                          │
│ ├─ GitHub Token: sessionStorage                            │
│ ├─ WebSocket: Real-time message streaming                  │
│ ├─ Document Editors: Spec/Plan/Task tabs                   │
│ └─ React Hooks: useRepos, useFeature, useDocument          │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTPS + WebSocket
┌──────────────────────────────────────────────────────────────┐
│ Backend (Python: FastAPI + Uvicorn)                          │
│ ├─ Auth Service: GitHub token validation                     │
│ ├─ GitHub Client: REST API wrapper                           │
│ ├─ Copilot Runner: Subprocess orchestration                  │
│ ├─ WebSocket Manager: Message streaming                      │
│ └─ Document Storage: GitHub API persistence                  │
└──────────────────┬──────────────────────────────────────────┘
                   │ GitHub API v3
┌──────────────────────────────────────────────────────────────┐
│ GitHub Cloud                                                 │
│ ├─ Repositories: Code storage                                │
│ ├─ Branches: Feature isolation                               │
│ ├─ Files: spec.md, plan.md, task.md                          │
│ └─ API: Authentication + CRUD                                │
└──────────────────┬──────────────────────────────────────────┘
                   │ subprocess + token env var
┌──────────────────────────────────────────────────────────────┐
│ Copilot CLI (Agent Backend)                                  │
│ ├─ Spec Generation: NLU + requirements breakdown             │
│ ├─ Clarification: Q&A for ambiguities                        │
│ ├─ Planning: Task breakdown + estimates                      │
│ └─ Analysis: Risk assessment + recommendations               │
└──────────────────────────────────────────────────────────────┘
```

### Data Flow Example: Clarify Operation

```
1. User clicks "Clarify" on Spec tab
   └─ Frontend JS: sendMessage({action: 'clarify'})

2. Frontend POST /features/{id}/clarify
   └─ Backend receives request, validates token

3. Backend: Validates spec exists and is valid markdown
   └─ Generates operation_id = "op_abc123"

4. Frontend: Opens WebSocket /ws?operation_id=op_abc123
   └─ Backend: Accepts connection, sends "Connected" message

5. Backend: Spawns subprocess
   └─ `copilot clarify --spec-file {spec.md}` with GITHUB_TOKEN env var

6. Copilot CLI writes output line-by-line to stdout
   └─ Backend: Reads each line, creates WebSocket message

7. Backend: Broadcasts message to all connected WebSocket clients
   └─ Frontend: Receives message, renders in UI (thinking/execution/etc)

8. Copilot CLI exits (success or error)
   └─ Backend: Sends "complete" message, updates spec.md in GitHub

9. Frontend: Receives complete message, shows "Ready for next step"
   └─ User can now proceed to Plan tab or make further edits
```

### Key Design Principles

1. **Cloud-First**: All documents in GitHub; no local persistence
2. **Async-First**: WebSocket streaming for non-blocking UX
3. **Subprocess Pattern**: Copilot CLI as independent backend engine
4. **Token Security**: Never logged, never persisted, sessionStorage only
5. **Scalable Architecture**: Frontend and backend can evolve independently

---

## Next Steps

After completing the quickstart workflow:

1. **Review Data Model** (`data-model.md`) to understand entity relationships
2. **Study API Contracts** (`github-integration.md` + `websocket-messages.md`)
3. **Implement Sprint 1**: Auth endpoint + repo/branch listing (1 week)
4. **Implement Sprint 2**: Document operations + WebSocket (2 weeks)
5. **Implement Sprint 3**: Edge cases + error handling (1 week)

---

## Support & Resources

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **GitHub API**: https://docs.github.com/en/rest
- **FastAPI**: https://fastapi.tiangolo.com/
- **Next.js**: https://nextjs.org/docs
- **WebSocket**: https://developer.mozilla.org/en-US/docs/Web/API/WebSocket
- **Copilot CLI Docs**: (Internal; reference app.py existing POC)

---

## Feedback

Found an issue in this guide? Need clarification?
- File an issue: GitHub Issues
- Add to team wiki: (Internal documentation)
- Pair with code reviewer for context

Happy coding! 🚀

