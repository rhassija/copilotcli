# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Redesigned Copilot CLI with modern web UI supporting multi-step workflow (spec → clarify → plan → analyze → task → implement) with GitHub authentication (PAT Phase 1, OAuth2 Phase 2), tab-based document editing, and real-time WebSocket conversations displaying LLM thinking/execution visibility. All repositories and documents sourced from GitHub.com via GitHub API (cloud-first architecture). Non-Streamlit modern web framework (React/Next.js recommended) orchestrating Copilot CLI subprocess backend.

## Technical Context

**Language/Version**: Python 3.13 (Copilot CLI backend subprocess via `copilotcompanion` venv) + TypeScript/JavaScript (React/Next.js frontend)
**Python Environment**: `copilotcompanion` (pre-created, located at `./copilotcompanion/`)  
**Primary Dependencies**: 
- Backend: FastAPI (WebSocket + GitHub API integration) or similar async-capable HTTP framework
- Frontend: React 18+ with Next.js (recommended) for SSR, API integration, and modern UX
- Copilot CLI: Subprocess-based execution with environment-injected GitHub token
- GitHub API v3: Primary data source for repos, branches, file operations
- WebSocket: Real-time streaming of Copilot CLI output and LLM thinking

**Storage**: GitHub API only (cloud-first); no local filesystem for workflow documents  
**Testing**: 
- Backend: pytest + mock GitHub API responses
- Frontend: Jest/Vitest + React Testing Library
- Integration: E2E tests with GitHub API (or mock server)

**Target Platform**: Modern web application (browsers: Chrome, Safari, Edge, Firefox; requires HTTPS)  
**Project Type**: Web (fullstack) - separate frontend and backend services  
**Performance Goals**: 
- GitHub API calls < 2s response time (including network)
- WebSocket message latency < 500ms UI update
- Copilot CLI spec generation < 60s, plan < 45s, analysis < 30s
- Repository list rendering < 100ms for 100+ repos
- Tab switching < 100ms

**Constraints**: 
- NO Streamlit; modern scalable framework required
- NO local filesystem for spec/plan/task documents (GitHub API exclusive)
- Cloud-first: repositories exclusively from GitHub.com
- Secure token handling: browser sessionStorage only, never logged
- GitHub token must be injected before Copilot CLI subprocess execution

**Scale/Scope**: 
- Phase 1 (MVP): Individual + small team usage (5-50 users)
- Support 100+ personal/org repositories per user
- Support 50+ feature branches per repository
- 8 core user stories prioritized (P0-P3)
- 48 functional requirements across 7 domains

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| **I. Natural Language First** | ✅ PASS | Spec/Plan/Task workflows accept user input without code/syntax; clarify step surfaces ambiguity for confirmation; non-tech readable acceptance scenarios defined |
| **II. Speckit Scaffold + Agent Enrichment** | ✅ PASS | UX orchestrates Speckit templates (spec.md, plan.md, task.md) + Copilot CLI for content generation; agent fills business logic, UI manages structure only |
| **III. Target Repo as Source of Truth** | ✅ PASS | All artifacts written to user-selected GitHub repo/branch; `.specify/` and `specs/` namespace under target repo; no tool repo writes unless explicitly chosen |
| **IV. Non-Tech Readability & Review** | ✅ PASS | All user stories include plain English acceptance scenarios; success criteria are measurable; clarification step explicitly surfaces ambiguity for non-tech review |
| **V. Sequential, Review-Gated Workflow** | ✅ PASS | Spec → (optional) Clarify → Plan → (optional) Analyze → Task progression documented; each step has explicit completion indicators; review gates clear between steps |

**Gate Status**: ✅ PASS - All principles satisfied; no violations requiring justification.

**Operational Requirements Check**:
- ✅ Repo selector (GitHub.com browsing + branch creation/selection)
- ✅ Auth readiness (GitHub token validation before repo access)
- ✅ Speckit readiness (templates provided in plan.md)
- ✅ Model provenance (Copilot CLI version + model used in generated artifacts)
- ✅ Edit and re-run support (not blocking, deferred to Phase 2)

**Workflow Gates**:
1. ✅ Capture requirement (8 user stories documented)
2. ⏳ Generate spec (Phase 1 deliverable)
3. ⏳ Review spec (user action, not tool scope)
4. ⏳ Generate plan (Phase 1 deliverable - this plan)
5. ⏳ Review plan (user action)
6. ⏳ Generate tasks (Phase 2 /speckit.tasks command)
7. ⏳ Review tasks (user action, not tool scope)

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

## Project Structure

### Documentation (this feature)

```text
specs/009-redesigned-workflow-ux/
├── spec.md                  # Feature specification (✅ Complete)
├── plan.md                  # This file - implementation roadmap
├── research.md              # Phase 0 research findings (in-progress)
├── data-model.md            # Phase 1 data model & entities
├── contracts/               # Phase 1 API contracts (OpenAPI)
│   ├── github-integration.md
│   ├── websocket-messages.md
│   └── document-operations.md
├── quickstart.md            # Phase 1 developer quickstart
├── checklists/
│   └── requirements.md      # Quality validation checklist
└── tasks.md                 # Phase 2 output (/speckit.tasks command - NOT created here)
```

### Python Virtual Environment (Pre-Existing)

**IMPORTANT**: The `copilotcompanion` Python 3.13 virtual environment is pre-created at `./copilotcompanion/` and must be used for all backend development and execution.

```bash
# Activate for development
source ./copilotcompanion/bin/activate

# Verify correct environment
python --version  # Should show Python 3.13.x
which pip         # Should show ./copilotcompanion/bin/pip
```

**All backend tasks (setup, development, testing, subprocess execution) MUST be run within this environment.**

### Source Code (repository root)

```text
copilot-ui/                         # Project root (new repository or subdirectory)

backend/
├── src/
│   ├── main.py              # FastAPI app initialization + WebSocket server
│   ├── models/
│   │   ├── github.py        # GitHub API models (Repo, Branch, File)
│   │   ├── workflow.py      # Workflow state models (Feature, Spec, Plan, Task)
│   │   └── auth.py          # Auth models (User, Session, Token)
│   ├── services/
│   │   ├── github_client.py # GitHub API integration (repos, branches, files)
│   │   ├── copilot_runner.py # Copilot CLI subprocess orchestration
│   │   ├── auth_service.py  # GitHub token validation + session management
│   │   └── websocket_streamer.py # WebSocket message broadcasting
│   ├── api/
│   │   ├── auth.py          # POST /auth/verify, POST /auth/logout
│   │   ├── repositories.py  # GET /repos, POST /repos/{id}/branches
│   │   ├── features.py      # GET /features, POST /features
│   │   ├── documents.py     # GET /docs/:type, PUT /docs/:type
│   │   └── operations.py    # POST /clarify, POST /analyze, WebSocket /ws
│   └── utils/
│       ├── env_config.py    # Environment configuration
│       └── error_handlers.py # Centralized error handling
├── tests/
│   ├── unit/
│   │   ├── test_github_client.py
│   │   ├── test_auth_service.py
│   │   └── test_copilot_runner.py
│   ├── integration/
│   │   ├── test_github_api_flow.py
│   │   └── test_document_workflow.py
│   └── contract/
│       └── test_websocket_messages.py
├── requirements.txt         # Python dependencies (FastAPI, aiohttp, python-dotenv)
├── Dockerfile              # Backend containerization
└── README.md               # Backend setup & deployment

frontend/
├── src/
│   ├── pages/
│   │   ├── login.tsx        # GitHub auth flow
│   │   ├── dashboard.tsx    # Main app with repo selector
│   │   └── workflow.tsx     # Tab-based spec/plan/task editor
│   ├── components/
│   │   ├── RepoSelector.tsx
│   │   ├── FeatureCreator.tsx
│   │   ├── DocumentEditors/
│   │   │   ├── SpecEditor.tsx
│   │   │   ├── PlanEditor.tsx
│   │   │   └── TaskEditor.tsx)
│   │   ├── ConversationPanel.tsx # Real-time WebSocket messages
│   │   ├── OperationButtons.tsx  # Clarify, Analyze, Generate buttons
│   │   └── AuthGuard.tsx    # Session persistence + redirect
│   ├── services/
│   │   ├── api.ts           # Backend API client (axios/fetch)
│   │   ├── github.ts        # GitHub token management
│   │   ├── websocket.ts     # WebSocket connection wrapper
│   │   └── auth.ts          # Auth context provider
│   ├── hooks/
│   │   ├── useRepos.ts      # Fetch + cache repositories
│   │   ├── useFeature.ts    # Manage feature selection
│   │   └── useDocument.ts   # Manage document editing state
│   ├── types/
│   │   └── index.ts         # TypeScript interfaces (Repo, Feature, Spec, etc.)
│   └── utils/
│       └── storage.ts       # sessionStorage wrapper
├── tests/
│   ├── unit/
│   │   └── components/
│   ├── integration/
│   │   └── workflows/
│   └── e2e/
│       └── github-integration.spec.ts
├── package.json            # Dependencies (Next.js, React, axios, WebSocket)
├── next.config.js          # Next.js configuration
├── Dockerfile              # Frontend containerization
└── README.md               # Frontend setup & development

docker-compose.yml          # Orchestrate backend + frontend services
.env.example                # Environment variables template (GitHub token handling)
DEPLOYMENT.md              # Production deployment guide
```

**Structure Decision**: **Option 2 - Web Application (Fullstack)**
- Rationale: Requires separate frontend (React/Next.js) and backend (FastAPI) for scalability, async WebSocket support, and independent deployment
- Frontend handles: UI orchestration, document editing, user interactions, session persistence
- Backend handles: Copilot CLI subprocess execution, GitHub API gateway, WebSocket streaming, auth validation
- Communication: REST API + WebSocket protocol

## Complexity Tracking

> **Status**: No violations. Constitution Check passed with all principles satisfied. No architecture exceptions requiring justification.

All design decisions (fullstack web app, FastAPI + React/Next.js, GitHub API as primary, WebSocket for async) are standard patterns for this feature class and do not exceed reasonable complexity budgets.

---

## Phase 0: Research & Clarification

**Objective**: Resolve all NEEDS CLARIFICATION items from Technical Context and establish best practices for dependencies.

**Status**: ✅ COMPLETE - All critical ambiguities resolved in previous clarification workflow.

**Key Decisions Locked**:
- ✅ Repositories exclusively from GitHub.com (no local filesystem)
- ✅ All spec/plan/task files persisted to GitHub via GitHub API (cloud-first)
- ✅ Copilot CLI subprocess for backend workflow engine
- ✅ React/Next.js for modern web frontend
- ✅ FastAPI for backend with WebSocket support
- ✅ GitHub PAT (Phase 1) + OAuth2 (Phase 2) authentication strategy

**Research Findings** (extracted from spec clarification + existing app.py POC):

### Copilot CLI Subprocess Integration Pattern
- **Pattern**: `subprocess.Popen(cmd)` with stdout/stderr capture
- **Benefits**: Proven in existing POC; maintains separation of concerns; CLI evolves independently
- **Gotchas**: Must inject GitHub token via environment; must handle subprocess errors gracefully
- **Reference**: Existing `src/ui/app.py` demonstrates working pattern

### GitHub API Best Practices for Enterprise
- **Token Scopes**: `repo` (full repo access) + `workflow` (trigger GH Actions)
- **Rate Limiting**: 1000 req/hour per token; implement retry logic with exponential backoff
- **Error Handling**: Catch 401 (expired token), 403 (insufficient scopes), 404 (private repo)
- **File Operations**: Use GitHub API for CRUD (no local clone required)
- **Pagination**: Implement for repos/branches lists

### WebSocket Streaming for Real-Time UX
- **Pattern**: Backend streams Copilot CLI subprocess output line-by-line via WebSocket
- **Message Format**: `{type: 'thinking'|'execution'|'error'|'complete', content: string, timestamp: ISO8601}`
- **Reconnection**: Maintain message history server-side for 5-10 minutes (replay on reconnect)
- **Backpressure**: Implement message queue if client consuming slower than generation

### Browser Token Storage Security
- **Recommendation**: sessionStorage (not localStorage) - cleared on tab close
- **Rationale**: Balances UX (survives page refresh) with security (cleared on exit)
- **Never**: Log, store in cookies, or persist to disk unencrypted

---

## Phase 1: Design & Contracts

**Objective**: Generate data model, API contracts, and developer quickstart.

### 1.1 Data Model & Entities

**Core Entities**:

```
User
├── id: UUID
├── github_username: string (unique)
├── github_token_hash: string (never stored plaintext)
├── created_at: timestamp
└── last_active: timestamp

Repository
├── id: string (GitHub repo ID)
├── owner: string
├── name: string
├── full_name: string (owner/name)
├── description: string
├── url: string (GitHub URL)
├── is_private: boolean
├── updated_at: timestamp
└── branches: [Branch]

Branch
├── id: string (branch SHA)
├── name: string
├── is_default: boolean
├── created_at: timestamp
└── updated_at: timestamp

Feature
├── id: string (UUID)
├── repository_id: string
├── branch_name: string
├── created_at: timestamp
├── spec: Spec
├── plan: Plan
├── task: Task
└── analysis_results: AnalysisResult (optional)

Spec
├── id: string
├── content: string (markdown)
├── feature_id: string
├── created_at: timestamp
├── updated_at: timestamp
├── version: integer (for edit history)
└── clarifications: [Clarification]

Clarification
├── id: string
├── question: string
├── answer: string (user response)
├── context_from_spec: string
└── applied_at: timestamp

Plan
├── id: string
├── content: string (markdown)
├── feature_id: string
├── created_at: timestamp
├── updated_at: timestamp
├── version: integer
└── derived_from_spec_version: integer

Task
├── id: string
├── content: string (markdown)
├── feature_id: string
├── created_at: timestamp
├── updated_at: timestamp
├── version: integer
└── derived_from_plan_version: integer

AnalysisResult
├── id: string
├── task_id: string
├── completeness_score: float (0-100)
├── identified_dependencies: [string]
├── risks: [string]
├── missing_tasks: [string]
├── created_at: timestamp
└── recommendations: [string]

WebSocketMessage
├── id: string (UUID)
├── operation_id: string (maps to clarify/analyze/plan job)
├── type: enum ('thinking'|'execution'|'error'|'complete')
├── content: string
├── timestamp: ISO8601
└── sequence: integer (for ordering)
```

**Relationships**:
- User → Repository (1:many via GitHub API)
- Repository → Branch (1:many)
- Branch → Feature (1:1, branch_name == feature identifier)
- Feature → Spec/Plan/Task (1:1 each)
- Spec ← Clarification (1:many)
- WebSocketMessage → OperationSession (1:many)

### 1.2 API Contracts (OpenAPI 3.0)

**Base URL**: `http://localhost:8000/api` (dev) or `https://api.copilot-ui.example.com/api` (prod)

**Authentication Header**: `Authorization: Bearer {github_token}`

**Core Endpoints**:

```
POST /auth/verify
  Request: { token: string }
  Response: { success: boolean, user: { login, name, avatar_url } }
  Errors: 401 (invalid token), 400 (malformed request)

POST /auth/logout
  Response: { success: boolean }

GET /repos?search=&limit=50&offset=0
  Response: { repos: [Repository], total: integer }
  Errors: 401 (expired token), 429 (rate limited)

GET /repos/{owner}/{repo}/branches
  Response: { branches: [Branch] }

POST /repos/{owner}/{repo}/branches
  Request: { branch_name: string, source_branch: string }
  Response: { branch: Branch, spec_path: string }

GET /features/{feature_id}/spec
  Response: { spec: { id, content, version, updated_at } }

PUT /features/{feature_id}/spec
  Request: { content: string }
  Response: { spec: Spec, updated_at }
  Note: Persists to GitHub repo immediately

POST /features/{feature_id}/clarify
  Request: { spec_version: integer }
  Response: { operation_id: string }
  WebSocket: Opens `/ws?operation_id={operation_id}` for streaming

GET /features/{feature_id}/plan
  Response: { plan: { id, content, version } or { error: 'not_created' } }

POST /features/{feature_id}/plan
  Request: { template_type: 'default' }
  Response: { operation_id: string }
  Backend: Invokes Copilot CLI, streams via WebSocket

PUT /features/{feature_id}/plan
  Request: { content: string }
  Response: { plan: Plan }
  GitHub: Persists plan.md to branch

GET /features/{feature_id}/task
  Response: { task: { id, content, version } or { error: 'not_created' } }

PUT /features/{feature_id}/task
  Request: { content: string }
  Response: { task: Task }

POST /features/{feature_id}/analyze
  Request: { task_version: integer }
  Response: { operation_id: string }
  WebSocket: Opens `/ws?operation_id={operation_id}`

WebSocket /ws
  Query Params: { operation_id: string }
  Message Format: { type, content, timestamp, sequence }
  Reconnection: Server maintains 5-min message history per operation_id
  Close: Operation completes or user closes tab
```

### 1.3 Developer Quickstart

**Prerequisites**:
- Python 3.11+ with FastAPI, aiohttp, PyGithub (backend)
- Node.js 18+ with React 18, Next.js, Tailwind CSS (frontend)
- Docker + Docker Compose (local development)
- GitHub Personal Access Token (PAT) with `repo` + `workflow` scopes

**Setup**:

```bash
# Clone + navigate
git clone <repo> && cd copilot-ui

# Backend setup
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export GITHUB_TOKEN=ghp_xxxyx  # For local testing
uvicorn main:app --reload

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev  # Runs on http://localhost:3000

# Docker Compose (alternative)
cd ..
docker-compose up  # Brings up both services + frontend on :3000, backend on :8000
```

**First Flow**:
1. Open http://localhost:3000
2. Click "Authenticate with GitHub"
3. Paste your GitHub token, click "Verify"
4. Select a repository from the list
5. Click "Create New Feature" or select existing branch
6. Wait for Spec tab to load; click "Create New Spec" if empty
7. Edit spec content, then click "Clarify" to test WebSocket streaming
8. Responses appear in real-time in the Conversation panel
9. Click "Create Plan" to generate plan via Copilot CLI

**Testing**:

```bash
# Backend unit tests
cd backend && pytest tests/unit

# Frontend component tests
cd frontend && npm run test

# E2E tests (mock GitHub API)
cd frontend && npm run test:e2e

# Integration test (real GitHub, requires token)
export GITHUB_TOKEN=ghp_xxx
python -m pytest tests/integration
```

---

## Phase 1 Deliverables Checklist

- ✅ Plan.md (this document) - architecture + design + quickstart
- ⏳ research.md - best practices + dependency analysis (generated from Phase 0)
- ⏳ data-model.md - expanded entity diagrams + relationship matrix (generated separately)
- ⏳ contracts/github-integration.md - detailed GitHub API usage patterns
- ⏳ contracts/websocket-messages.md - WebSocket message specifications + examples
- ⏳ contracts/document-operations.md - Spec/Plan/Task CRUD patterns
- ⏳ quickstart.md - copy of section 1.3 above, formatted for developer onboarding

### Next Steps (Post-Review)

1. **Review this plan** - stakeholder approval on architecture + milestones
2. **Generate tasks** - `/speckit.tasks` command creates detailed task breakdown
3. **Update agent context** - Run `.specify/scripts/bash/update-agent-context.sh copilot` to register this plan with agent
4. **Start Phase 2 (Implementation)** - Backend + Frontend development with weekly reviews
