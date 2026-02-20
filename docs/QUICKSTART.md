# Quick Start Guide - Copilot CLI Web UI

Complete step-by-step instructions to get the Copilot CLI web application running on your local machine in **5 minutes**.

## 📋 Prerequisites

Before starting, ensure you have:

- **macOS, Linux, or Windows (WSL2)**
- **Git** (`git --version` to verify)
- **Node.js 18+** (`node --version`)
- **Python 3.13+** (`python3 --version` or `python3.13 --version`)
- **GitHub Personal Access Token (PAT)**
  - Go to https://github.com/settings/tokens
  - Click "Generate new token (classic)"
  - Grant scopes: `repo`, `user`
  - Copy and save the token (you'll need it)

## 🚀 Start Here - 5 Minute Setup

### Step 1: Clone the Repository (30 seconds)

```bash
git clone https://github.com/your-org/copilotcli.git
cd copilotcli
```

### Step 2: Start Backend Server (1 minute)

```bash
cd backend

# Create virtual environment
python3.13 -m venv env

# Activate it
# On macOS/Linux:
source env/bin/activate
# On Windows (Command Prompt):
# env\Scripts\activate
# On Windows (PowerShell):
# env\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy env template
cp .env.example .env.local

# Edit .env.local and add your GitHub token
# GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# (use your text editor to add the token)

# Start the server (it will run on http://localhost:8001)
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
```

**✅ Backend ready when you see:**
```
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Application startup complete
```

### Step 3: Start Frontend Server (1 minute)

**In a new terminal**, open the frontend folder:

```bash
cd frontend

# Install dependencies
npm install

# Copy env template
cp .env.example .env.local

# Check that NEXT_PUBLIC_API_BASE_URL=http://localhost:8001 is set
# (It should be by default)

# Start the dev server (it will run on http://localhost:3000)
npm run dev
```

**✅ Frontend ready when you see:**
```
▲ Next.js 14.x.x
- Local: http://localhost:3000
- Environments: .env.local
```

### Step 4: Open the Application (30 seconds)

1. Open your browser
2. Go to **http://localhost:3000**
3. You should see the login screen

## 🧪 Test the Full Flow

### 1. Authenticate with GitHub

```
1. Click "Sign In with GitHub"
2. Paste your Personal Access Token
3. Click "Authenticate"
4. You should see ✅ "Authentication successful!"
```

### 2. Select a Repository

```
1. Click "Select Repository"
2. Search for one of your GitHub repos
3. Click on it to select
```

### 3. Create or Select a Feature

```
1. Click "Create New Feature" (or select an existing one)
2. Enter a feature name like "user-authentication"
3. Click "Create"
```

### 4. Generate a Specification

```
1. Click on the "Specification" tab
2. Enter a prompt like:
   "Create a GitHub authentication system using OAuth2"
3. Click "Generate Specification"
4. Watch the real-time updates in the Conversation Panel (bottom right)
```

**🎉 You should see messages streaming in real-time:**
```
✓ Starting spec generation...
✓ Generating specification...
✓ Spec generation complete!
```

## 🛠 Convenience Scripts

We provide shell scripts to quickly restart servers:

```bash
# From the repository root, make scripts executable
chmod +x scripts/restart-backend.sh scripts/restart-frontend.sh

# Restart backend (kills old process, starts new)
scripts/restart-backend.sh

# Restart frontend
scripts/restart-frontend.sh
```

### ⚠️ If you get "Address already in use"

**Kill the old process:**

```bash
# Find process on port 8001 (backend)
lsof -i :8001
# Kill it (replace 12345 with the PID)
kill -9 12345

# Find process on port 3000 (frontend)
lsof -i :3000
kill -9 12345
```

## 📁 Folder Layout (After Setup)

```
copilotcli/
├── backend/
│   ├── env/                    # Virtual environment (created in Step 2)
│   ├── src/
│   │   ├── api/               # API endpoints
│   │   ├── models/
│   │   ├── services/
│   │   └── main.py
│   ├── .env.local             # Your GitHub token (git-ignored)
│   └── requirements.txt
│
├── frontend/
│   ├── node_modules/          # Dependencies (created in Step 3)
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── ...
│   ├── .env.local             # Backend URL (git-ignored)
│   ├── package.json
│   └── ...
│
├── docs/
│   ├── ARCHITECTURE.md        # Technical deep dive
│   └── ...
│
└── README.md                  # Main documentation
```

## 🔧 Environment Configuration

### Backend Configuration (.env.local)

```env
# Required
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional
DEBUG=true                                    # Enable debug logging
ALLOWED_ORIGINS=http://localhost:3000,…     # CORS allowed origins
COPILOT_CLI_PATH=/usr/local/bin/cocli       # Path to Copilot CLI
```

### Frontend Configuration (.env.local)

```env
# Backend API address (don't change for local development)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001

# Optional
NEXT_PUBLIC_LOG_LEVEL=debug                 # Logging verbosity
```

## 🐛 Troubleshooting

### "Cannot find module" error in backend

```bash
# Make sure you're in the backend folder and venv is activated
cd backend
source env/bin/activate  # macOS/Linux

# Reinstall dependencies
pip install -r requirements.txt
```

### "Module not found" error in frontend

```bash
# Make sure you're in the frontend folder
cd frontend

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### WebSocket connection fails in browser console

```
1. Check backend is running: http://localhost:8001/docs
2. Check CORS settings in backend/.env.local
3. Try refresh browser (Cmd+R or Ctrl+R)
4. Check browser DevTools Console tab for specific error
```

### Can't authenticate with GitHub

```
1. Verify your GitHub token is valid (doesn't start with "ghp_"?)
2. Check token has "repo" and "user" scopes
3. Token might be expired - generate a new one
4. Make sure you pasted it correctly (no extra spaces)
```

### "Address already in use" port error

```bash
# Kill process on port 8001
lsof -i :8001 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Kill process on port 3000
lsof -i :3000 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### Generation times out

```
1. Copilot CLI might be slow - this can take 2-5 minutes
2. Check backend logs for errors
3. Try with a simpler prompt first
4. Check your GitHub token has valid access
```

## 📊 Verifying Everything Works

### Health Check Endpoints

```bash
# Check backend is alive
curl http://localhost:8001/docs

# Check frontend is alive
curl http://localhost:3000

# Both should return 200 OK with HTML content
```

### Backend API Test

```bash
# Without auth (should fail with 401)
curl http://localhost:8001/api/v1/repositories

# With session header (only works after you auth in UI)
curl -H "X-Session-ID: your-session-id" http://localhost:8001/api/v1/repositories
```

## 🚢 Next Steps After Setup

### Try These Features

1. **Generate different document types**
   - Specification (complex system design)
   - Plan (implementation roadmap)
   - Task (detailed executable task)

2. **Test WebSocket stability**
   - Generate while network disconnected (open DevTools Network tab)
   - See if messages replay when connection resumes

3. **Review generated documents**
   - Check that Copilot CLI output is good quality
   - Edit and refine documents as needed

### Explore the Code

- [`backend/src/main.py`](../backend/src/main.py) - FastAPI app setup
- [`backend/src/api/documents.py`](../backend/src/api/documents.py) - Generation endpoints
- [`frontend/src/components/ConversationPanel.tsx`](../frontend/src/components/ConversationPanel.tsx) - Real-time UI
- [`frontend/src/services/websocket.ts`](../frontend/src/services/websocket.ts) - WebSocket client

### Learn the Architecture

Read [ARCHITECTURE.md](docs/ARCHITECTURE.md) for:
- System design and patterns
- WebSocket message flow
- Backend service layer
- Frontend state management
- Security and error handling

## 📚 Additional Resources

- **[README.md](README.md)** - Project overview and features
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Technical deep dive
- **[TESTING-GUIDE.md](TESTING-GUIDE.md)** - How to run tests
- **[PLAN-TASK-GENERATION-GUIDE.md](PLAN-TASK-GENERATION-GUIDE.md)** - Document generation workflow
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment

## 💡 Tips & Tricks

### VSCode Extensions for Development

```json
{
  "recommendations": [
    "ms-python.python",           // Python development
    "charliermarsh.ruff",          // Python linter
    "dbaeumer.vscode-eslint",      // Frontend linting
    "esbenp.prettier-vscode",      // Code formatting
    "firsttris.vscode-jest-runner", // Test runner
    "ms-vscode.makefile-tools"     // Build tasks
  ]
}
```

### Hot Reload

Both backend and frontend have hot reload enabled:

```bash
# Backend: Changes to .py files auto-reload
# Frontend: Changes to .tsx/.ts files auto-reload
```

Just save your file and the server will update!

### View Backend API Documentation

After starting backend, visit:

```
http://localhost:8001/docs
```

This is interactive Swagger UI showing all endpoints with try-it-out buttons.

### Debug WebSocket Messages

In browser DevTools:

1. Open **Developer Tools** (F12 or Cmd+Option+I)
2. Go to **Network** tab
3. Filter to "WS" (WebSocket)
4. Click the connection showing `ws://localhost:8001/api/v1/ws`
5. View **Messages** tab to see real-time WebSocket traffic

## 🎯 Getting Help

| Issue | How to Debug |
|-------|-------------|
| Backend won't start | Check `python3 --version` is 3.13+, check pip packages with `pip list` |
| Frontend won't start | Check `node --version` is 18+, check `npm list` for dependency conflicts |
| WebSocket connection fails | Check browser console, check backend logs, verify CORS in .env |
| Generation times out | Check Copilot CLI is installed and callable, increase timeout in requests |
| Can't authenticate | Verify GitHub token format (ghp_xxxxx), check token scopes, try new token |

---

**Video tutorial coming soon!** In the meantime, screenshots are available in the [docs folder](docs/).

**Last Updated**: February 19, 2026  
**Current Version**: 1.0.0 (Beta)  
**Status**: ✅ Ready for local development
