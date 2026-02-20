# Copilot CLI - Web UI with Real-Time WebSocket Streaming

A modern web-based interface for the Copilot CLI that enables real-time, streaming document generation (specifications, plans, and tasks) with live updates and transparent AI thinking processes.

## 🎯 Overview

This project provides a Next.js + FastAPI web application that allows users to:

- **Authenticate** with GitHub to access repositories and features
- **Generate documents** (specification, plan, task) from natural language using Copilot CLI
- **Stream updates** in real-time via WebSocket as documents are generated
- **View AI reasoning** with collapsible thinking sections
- **Edit and manage** documents in a modern tab-based interface

## 🏗 Architecture

### Full-Stack Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                           CLIENT (Port 3000)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Next.js 14 + React 18 + TypeScript                      │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Pages: Dashboard, Repo Selection, Features, Docs │  │  │
│  │  │  Components: DocumentEditor, ConversationPanel    │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Services: API Client, WebSocket Manager, Auth    │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                  HTTP + WebSocket (localhost:8001)              │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
┌──────────────────────────────┼───────────────────────────────────┐
│                           SERVER (Port 8001)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FastAPI (Python 3.13)                                   │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  API Endpoints:                                    │  │  │
│  │  │  • POST /api/v1/auth/github (GitHub auth)        │  │  │
│  │  │  • GET  /api/v1/repositories (list repos)        │  │  │
│  │  │  • GET  /api/v1/features (list features)         │  │  │
│  │  │  • POST /api/v1/features/:id/generate-spec       │  │  │
│  │  │  • POST /api/v1/features/:id/generate-plan       │  │  │
│  │  │  • POST /api/v1/features/:id/generate-task       │  │  │
│  │  │  • WS   /api/v1/ws (WebSocket connection)        │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Services:                                         │  │  │
│  │  │  • WebSocket Manager (broadcast, subscriptions)  │  │  │
│  │  │  • Document Generator (Copilot CLI wrapper)      │  │  │
│  │  │  • GitHub Client (repo/branch operations)        │  │  │
│  │  │  • Auth Service (session management)             │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                    Copilot CLI (subprocess)                     │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
                    GitHub API (authenticated)
```

### WebSocket Message Flow

```
User clicks "Generate Spec" (Frontend)
        │
        ├─→ Generate request with operation_id
        │
        ├─→ Backend receives, creates WebSocket message
        │
        ├─→ MessageType.EXECUTION: "Starting spec generation..."
        │
        ├─→ Backend runs generation in async thread
        │
        ├─→ MessageType.EXECUTION: "Generating specification..." (progress)
        │
        ├─→ Copilot CLI runs (subprocess), produces spec.md
        │
        ├─→ MessageType.COMPLETE: "Spec generation complete..."
        │
        └─→ Frontend receives all messages via WebSocket subscription
            │
            ├─→ ConversationPanel displays messages in real-time
            │
            └─→ User sees streaming progress without page reload
```

## 📁 Folder Structure

```
copilotcli/
├── backend/                          # FastAPI Python backend
│   ├── src/
│   │   ├── api/                      # API endpoints
│   │   │   ├── auth.py              # GitHub authentication endpoints
│   │   │   ├── documents.py         # Document generation (spec/plan/task)
│   │   │   ├── features.py          # Feature management endpoints
│   │   │   ├── repositories.py      # Repository listing endpoints
│   │   │   └── websocket.py         # WebSocket connection handler
│   │   ├── models/                  # Pydantic request/response models
│   │   │   ├── auth.py
│   │   │   ├── documents.py
│   │   │   ├── features.py
│   │   │   └── websocket.py
│   │   ├── services/                # Business logic services
│   │   │   ├── auth_service.py      # GitHub auth logic
│   │   │   ├── doc_generator.py     # Copilot CLI wrapper
│   │   │   ├── feature_service.py   # Feature branch operations
│   │   │   ├── repo_service.py      # Repository operations
│   │   │   └── websocket_manager.py # WebSocket connection management
│   │   ├── utils/                   # Utility functions
│   │   │   └── logging.py           # Structured logging
│   │   └── main.py                  # FastAPI app initialization
│   ├── tests/                        # Unit and integration tests
│   ├── conftest.py                  # Pytest configuration
│   ├── pytest.ini                   # Pytest settings
│   ├── requirements.txt             # Python dependencies
│   ├── Dockerfile                   # Docker build config
│   ├── .env.example                 # Environment variable template
│   └── pyvenv.cfg                   # Virtual environment config
│
├── frontend/                         # Next.js React frontend
│   ├── src/
│   │   ├── components/              # React components
│   │   │   ├── ConversationPanel.tsx    # WebSocket message display
│   │   │   ├── DocumentEditors/
│   │   │   │   ├── DocumentEditor.tsx   # Spec/plan/task editing
│   │   │   │   ├── SpecEditor.tsx
│   │   │   │   ├── PlanEditor.tsx
│   │   │   │   └── TaskEditor.tsx
│   │   │   ├── Layouts/
│   │   │   ├── Navigation/
│   │   │   └── UI/                  # Reusable UI components
│   │   ├── pages/                   # Next.js pages (routes)
│   │   │   ├── index.tsx            # Dashboard/home
│   │   │   ├── auth/
│   │   │   ├── repositories/
│   │   │   └── features/
│   │   ├── services/                # Client-side services
│   │   │   ├── api.ts              # HTTP client
│   │   │   ├── auth.ts             # Auth service
│   │   │   ├── websocket.ts        # WebSocket client
│   │   │   └── storage.ts          # Session storage
│   │   ├── hooks/                   # React custom hooks
│   │   ├── utils/                   # Utility functions
│   │   ├── styles/                  # Global styles
│   │   └── types/                   # TypeScript type definitions
│   ├── public/                       # Static assets
│   ├── tests/                        # Frontend tests
│   ├── package.json                 # Node dependencies
│   ├── tsconfig.json                # TypeScript config
│   ├── tailwind.config.js           # Tailwind CSS config
│   ├── next.config.js               # Next.js config
│   ├── vitest.config.ts             # Vitest test config
│   ├── playwright.config.ts         # E2E test config
│   ├── Dockerfile                   # Docker build config
│   ├── .env.example                 # Environment variables
│   └── .env.local                   # Local overrides (git-ignored)
│
├── specs/                            # Specification documents
│   ├── 001-copilotcli/              # [ARCHIVED] Original POC spec
│   └── 009-redesigned-workflow-ux/  # [CURRENT] Active specification
│       └── spec.md                  # Full feature spec
│
├── scripts/                          # Utility scripts
│   ├── restart-backend.sh           # Restart backend server
│   └── restart-frontend.sh          # Restart frontend server
│
├── .specify/                         # Speckit configuration
│   └── scripts/
│       └── bash/
│           └── check-prerequisites.sh
│
├── docs/                             # Documentation (generated)
│   ├── ARCHITECTURE.md              # Technical architecture
│   ├── QUICKSTART.md                # Getting started guide
│   └── API.md                       # API documentation
│
├── docker-compose.yml               # Local development stack
├── DEPLOYMENT.md                    # Deployment guide
├── IMPLEMENTATION-SUMMARY.md        # What's been done
├── PLAN-TASK-GENERATION-GUIDE.md   # Document generation workflow
├── TESTING-GUIDE.md                 # Testing instructions
└── README.md                        # This file
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ (for frontend)
- **Python** 3.13+ (for backend)
- **Git** (for repository operations)
- **GitHub PAT** (Personal Access Token)

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/copilotcli.git
cd copilotcli
```

### 2. Setup Backend

```bash
cd backend

# Create virtual environment
python3.13 -m venv env
source env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env.local
# Edit .env.local with your GitHub token and settings

# Run the server
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
```

Backend runs on: **http://localhost:8001**

### 3. Setup Frontend

In a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Update NEXT_PUBLIC_API_BASE_URL=http://localhost:8001 if needed

# Run dev server
npm run dev
```

Frontend runs on: **http://localhost:3000**

### 4. Test the Connection

1. Open http://localhost:3000 in your browser
2. Authenticate with GitHub
3. Select a repository and feature
4. Click "Generate Spec" and watch the WebSocket messages appear in real-time

## 🔄 WebSocket Message Types

The ConversationPanel displays real-time updates during document generation:

| Message Type | Display | Example |
|-------------|---------|---------|
| `THINKING` | Collapsible section with reasoning | "Analyzing business requirements..." |
| `EXECUTION` | Fixed status message | "Generating specification..." |
| `ERROR` | Red error box | "Failed to generate: API rate limit" |
| `COMPLETE` | Green success box | "Spec generation complete!" |
| `INFO` | Blue info message | "Using template: enterprise-app" |

Messages stream in real-time as the backend runs Copilot CLI operations.

## 🛠 Development Workflow

### Using Convenience Scripts

```bash
# Quick restart of backend (kills old process, starts new)
cd scripts
chmod +x restart-backend.sh restart-frontend.sh
./restart-backend.sh

# In another terminal
./restart-frontend.sh
```

### Environment Variables

**Backend** (`.env.local`):
```env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxx
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
DEBUG=true
```

**Frontend** (`.env.local`):
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001
NEXT_PUBLIC_LOG_LEVEL=debug
```

### Running Tests

**Backend Unit Tests**:
```bash
cd backend
pytest tests/ -v
```

**Frontend Unit Tests**:
```bash
cd frontend
npm run test:unit
```

**E2E Tests**:
```bash
cd frontend
npm run test:e2e
```

## 📊 Key Features Implemented

### ✅ Completed

- **WebSocket Infrastructure**: Connection manager, message queuing, subscription model
- **Real-time Streaming**: Status messages broadcast to all connected clients
- **Document Generation**: Spec, plan, and task generation endpoints with progress tracking
- **Conversation Panel**: Display streaming messages with timestamps and message types
- **UI Components**: Modern React components with Tailwind CSS styling
- **Session Auth**: GitHub PAT-based authentication with session storage
- **Cross-browser WebSocket**: Auto-reconnect, message replay on reconnect

### ⏳ In Progress / Planned

- **OAuth2 GitHub Login**: Replace PAT with OAuth flow
- **Database Integration**: Replace in-memory storage with PostgreSQL
- **Clarify/Analyze Workflows**: Full workflows for requirements clarification and analysis
- **Production Deployment**: Docker containers, Kubernetes manifests, CI/CD pipeline
- **API Documentation**: OpenAPI/Swagger docs with interactive explorer
- **Comprehensive Testing**: Higher test coverage for edge cases

## 🐳 Docker Deployment

For local development with Docker:

```bash
# Build and run all services
docker-compose up --build

# Frontend: http://localhost:3000
# Backend: http://localhost:8001
```

For production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md).

## 📚 Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Technical design and patterns
- **[QUICKSTART.md](docs/QUICKSTART.md)** - Step-by-step setup guide
- **[TESTING-GUIDE.md](TESTING-GUIDE.md)** - How to run tests
- **[PLAN-TASK-GENERATION-GUIDE.md](PLAN-TASK-GENERATION-GUIDE.md)** - Document generation workflow
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment instructions
- **[IMPLEMENTATION-SUMMARY.md](IMPLEMENTATION-SUMMARY.md)** - What's been implemented

## 🔌 API Endpoints

### Authentication

```
POST   /api/v1/auth/github          Authenticate with GitHub PAT
POST   /api/v1/auth/logout          Clear session
GET    /api/v1/auth/session         Get current session info
```

### Repositories & Features

```
GET    /api/v1/repositories         List GitHub repositories
GET    /api/v1/features/:repo       List feature branches in repo
POST   /api/v1/features/:repo       Create new feature branch
GET    /api/v1/features/:repo/:id   Get feature details
```

### Document Generation

```
POST   /api/v1/features/:id/generate-spec     Generate specification
POST   /api/v1/features/:id/generate-plan     Generate plan
POST   /api/v1/features/:id/generate-task     Generate task
```

### WebSocket

```
WS     /api/v1/ws                   WebSocket connection (subscribe to operation_id)
```

## 🤝 Contributing

### Code Style

- **Backend**: Black formatter, Pylint for linting
- **Frontend**: Prettier + ESLint for formatting/linting
- **TypeScript**: Strict mode enabled

### Git Workflow

1. Create a feature branch: `git checkout -b feature/description`
2. Commit with clear messages: `git commit -m "Add feature: description"`
3. Push and create a pull request
4. Ensure tests pass before merging

## 📝 License

[Your License Here]

## 👥 Support

For issues and questions:

- **GitHub Issues**: [Create an issue](https://github.com/your-org/copilotcli/issues)
- **Documentation**: See [Architecture Guide](docs/ARCHITECTURE.md)
- **Slack/Discord**: [Your community channel]

---

**Last Updated**: February 19, 2026  
**Current Phase**: Core Feature Implementation (WebSocket Streaming ✅)  
**Next Phase**: OAuth2 Integration & Database Layer
