# Tasks: Redesigned Copilot CLI with Modern Web UI and Multi-Step Workflow

**Specification**: [Feature Specification](spec.md)  
**Plan**: [Implementation Plan](plan.md)  
**Date**: February 18, 2026  
**Branch**: `009-redesigned-workflow-ux`

---

## Task Overview

**Total Tasks**: 87 (spanning 6 phases)  
**Parallel Opportunities**: 31 tasks marked `[P]` (40% parallelizable)  
**Critical Path**: Phase 1 Setup → Phase 2 Foundation → Phase 3 (P0/P1) → Phase 5 (Polish)  
**Estimated Effort**: 14-16 weeks (2-3 person team)  
**MVP Scope**: Complete Phase 3 (User Stories 0-2) = 6-8 weeks

---

## Format Reference

- **`- [ ]`**: Checklist checkbox
- **`[TID]`**: Task ID (T001-T087)
- **`[P]`**: Parallelizable (can run simultaneously with other [P] tasks)
- **`[USN]`**: User Story label (US0, US1, etc.) for non-setup phases
- **File paths**: Exact locations for implementation (backend/src, frontend/src, etc.)

---

## Phase 1: Project Setup & Infrastructure (Weeks 1)

**Purpose**: Initialize project structure, dependencies, and development environment  
**Duration**: ~1 week  
**Blocking**: All downstream phases  

### Python Virtual Environment Setup

- [x] T000 [P] Activate pre-existing `copilotcompanion` virtual environment: `source ./copilotcompanion/bin/activate` in all terminal sessions for backend work
- [x] T000a [P] Verify Python version in venv: `python --version` should output Python 3.13.x
- [x] T000b Verify pip is from correct environment: `which pip` should show `./copilotcompanion/bin/pip`

**NOTE**: All subsequent backend tasks (T001 onwards) MUST be executed within the `copilotcompanion` virtual environment. This environment is used for:
  - Backend dependency installation and development
  - Copilot CLI subprocess execution (token injected via environment)
  - All Python-based testing (pytest)
  - Local development server (uvicorn)

### Backend Project Initialization

- [x] T001 Initialize Python backend project structure: `backend/src/`, `backend/tests/`, `backend/requirements.txt` (execute in activated `copilotcompanion` environment)
- [x] T002 [P] Configure FastAPI application entry point in `backend/src/main.py`
- [x] T003 [P] Setup Python virtual environment with pip dependencies (FastAPI, uvicorn, aiohttp, pydantic)
- [x] T004 [P] Configure CORS middleware in `backend/src/main.py` for frontend development
- [x] T005 Create Docker image for backend: `backend/Dockerfile`
- [x] T006 Setup environment configuration in `backend/.env.example` and `backend/src/utils/env_config.py`

### Frontend Project Initialization

- [x] T007 Initialize Next.js React frontend: `frontend/` with pages, components, services structure
- [x] T008 [P] Configure TypeScript in `frontend/tsconfig.json` with strict mode enabled
- [x] T009 [P] Install frontend dependencies: React 18, Next.js 14, axios, TypeScript development tools
- [x] T010 [P] Setup Tailwind CSS in `frontend/tailwind.config.js` + base styles
- [x] T011 Create frontend environment template: `frontend/.env.example`
- [x] T012 Setup Next.js configuration in `frontend/next.config.js` (API routes, SSR settings)

### Testing Infrastructure

- [x] T013 [P] Setup pytest in `backend/` with conftest.py fixtures
- [x] T014 [P] Setup Vitest in `frontend/` with component testing configuration
- [x] T015 [P] Configure E2E testing with Playwright in `frontend/tests/e2e/`
- [x] T016 Create mock GitHub API server for testing: `backend/tests/mocks/github_server.py`

### Docker & Deployment Setup

- [x] T017 Create `docker-compose.yml` for local development (backend + frontend)
- [x] T018 [P] Create frontend Docker image: `frontend/Dockerfile`
- [x] T019 Setup `.dockerignore` files for both backend and frontend
- [x] T020 Create deployment documentation: `DEPLOYMENT.md` (structure, no implementation yet)

---

## Phase 2: Foundational Infrastructure (Weeks 1-2)

**Purpose**: Core services that block ALL user story implementation  
**Duration**: ~1-2 weeks  
**Critical**: Must be 100% complete before Phase 3  
**Blocking**: Auth service → all API endpoints; WebSocket infrastructure → clarify/analyze operations

### Backend Foundation: Models & Database Abstraction

- [X] T021 [P] Create auth models in `backend/src/models/auth.py`: User, AuthSession, Token
- [X] T022 [P] Create repo models in `backend/src/models/github.py`: Repository, Branch, Feature
- [X] T023 [P] Create document models in `backend/src/models/documents.py`: Spec, Plan, Task, AnalysisResult
- [X] T024 [P] Create WebSocket models in `backend/src/models/websocket.py`: WebSocketSession, WebSocketMessage
- [X] T025 Implement in-memory storage layer in `backend/src/services/storage.py` (Phase 1 - no database)

### Backend Foundation: GitHub API Client

- [X] T026 [P] Implement GitHub API client base in `backend/src/services/github_client.py`
- [X] T027 Implement GitHub auth validation method: `validate_token()` (uses GitHub /user endpoint)
- [X] T028 Implement repository listing method: `get_repositories()` with caching
- [X] T029 [P] Implement branch operations: `get_branches()`, `create_branch()`
- [X] T030 [P] Implement file operations: `read_file()`, `write_file()`, `get_file_sha()`
- [X] T031 Implement rate limiting and retry logic in GitHub client (exponential backoff, 429 handling)

### Backend Foundation: Authentication & Session Management

- [X] T032 Implement auth service in `backend/src/services/auth_service.py`
- [X] T033 Implement `verify_token()` method with GitHub API validation
- [X] T034 Implement token storage (sessionStorage equivalent on backend)
- [X] T035 Implement session persistence across API calls (session_id tracking)
- [X] T036 Implement token expiration detection (catch 401 errors)
- [X] T037 Implement logout/session cleanup

### Backend Foundation: Copilot CLI Subprocess Runner

- [ ] T038 [P] Create subprocess runner in `backend/src/services/copilot_runner.py`
- [ ] T039 Implement subprocess spawning with token injection via environment
- [ ] T040 Implement stdout/stderr capture with line-by-line parsing
- [ ] T041 Implement timeout handling (5 min max per operation)
- [ ] T042 Implement error handling for subprocess failures

### Backend Foundation: WebSocket Infrastructure

- [ ] T043 [P] Setup WebSocket route in `backend/src/api/websocket.py`
- [ ] T044 [P] Implement message queue per operation_id in memory
- [ ] T045 Implement WebSocket connection manager (track active connections)
- [ ] T046 Implement message broadcasting to all clients on same operation_id
- [ ] T047 Implement reconnection logic (last_received_sequence replay)
- [ ] T048 Implement message history retention (5-10 min per operation)
- [ ] T049 Implement graceful connection close and cleanup

### Backend Foundation: Error Handling & Logging

- [ ] T050 [P] Create centralized error handler in `backend/src/utils/error_handlers.py`
- [ ] T051 [P] Setup structured logging in `backend/src/utils/logging.py`
- [ ] T052 Implement error response formatting (consistent with API contracts)
- [ ] T053 Implement token masking in logs (never show full token)

### Frontend Foundation: Auth Context & Token Management

- [ ] T054 [P] Create auth context in `frontend/src/services/auth.ts`
- [ ] T055 [P] Implement sessionStorage token storage wrapper in `frontend/src/utils/storage.ts`
- [ ] T056 Implement auth state hook: `useAuth()` in `frontend/src/hooks/useAuth.ts`
- [ ] T057 Implement HTTP client wrapper with automatic token injection: `frontend/src/services/api.ts`

### Frontend Foundation: API Service & Data Fetching

- [ ] T058 [P] Create API service in `frontend/src/services/api.ts` with axios interceptors
- [ ] T059 [P] Implement error handling in API service (detect 401, prompt re-auth)
- [ ] T060 Implement automatic retry logic with exponential backoff
- [ ] T061 Create custom React hooks: `useApi()` for data fetching in `frontend/src/hooks/useApi.ts`

### Frontend Foundation: WebSocket Client

- [ ] T062 [P] Create WebSocket service in `frontend/src/services/websocket.ts`
- [ ] T063 Implement WebSocket connection wrapper with auto-reconnect
- [ ] T064 Implement message queue and replay on reconnect
- [ ] T065 Implement message type routing (thinking, execution, error, complete)

### Frontend Foundation: Core Components

- [ ] T066 [P] Create AuthGuard wrapper component in `frontend/src/components/AuthGuard.tsx`
- [ ] T067 [P] Create Layout component with header/sidebar in `frontend/src/components/Layout.tsx`
- [ ] T068 [P] Create Loading spinner component in `frontend/src/components/Loading.tsx`
- [ ] T069 [P] Create Error display component in `frontend/src/components/ErrorBoundary.tsx`

**Checkpoint**: Foundation complete - user story implementation can now begin in parallel

---

## Phase 3: User Story 0 - GitHub Authentication (Priority: P0) 🎯 CRITICAL

**Goal**: Enable users to authenticate with GitHub and establish authenticated sessions  
**Independent Test**: User can input token, verify success, and remain authenticated across page refreshes  
**Duration**: ~1 week (blocks all other stories)

### Implementation for US0

- [ ] T070 [P] [US0] Create auth validation endpoint: `POST /api/v1/auth/verify` in `backend/src/api/auth.py`
- [ ] T071 [US0] Implement endpoint to validate token via GitHub `/user` API endpoint
- [ ] T072 Implement token response with user info (login, id, avatar_url, email, scopes)
- [ ] T073 [P] [US0] Create logout endpoint: `POST /api/v1/auth/logout` in `backend/src/api/auth.py`
- [ ] T074 [US0] Implement session cleanup on logout

### Frontend for US0

- [ ] T075 [P] [US0] Create login page in `frontend/src/pages/login.tsx`
- [ ] T076 [P] [US0] Create token input form with copy/paste support
- [ ] T077 [US0] Implement "Verify" button that calls `POST /auth/verify`
- [ ] T078 Implement success/error message display for auth attempts
- [ ] T079 [P] [US0] Implement session persistence: store token in sessionStorage after verify
- [ ] T080 [US0] Implement page redirect to dashboard on successful auth
- [ ] T081 [US0] Implement re-auth flow when token expires (catch 401 errors)

### Testing for US0

- [ ] T082 [P] [US0] Contract test for `/auth/verify` endpoint in `backend/tests/contract/test_auth.py`
- [ ] T083 [P] [US0] Unit test for token validation logic in `backend/tests/unit/test_auth_service.py`
- [ ] T084 [US0] Component test for login form in `frontend/tests/unit/LoginPage.test.tsx`
- [ ] T085 [US0] Integration test for full auth flow (user inputs token → verify → redirect)
- [ ] T086 [US0] E2E test for authentication workflow in `frontend/tests/e2e/auth.spec.ts`

**Checkpoint**: User Story 0 complete - users can now authenticate. Proceed to US1 & US2.

---

## Phase 4: User Stories 1-2 (Priority: P1) 🎯 MVP CORE (Weeks 2-4)

**Goal**: Enable repository/feature selection and tab-based document workflow  
**Independent Tests**: 
- US1: User selects repo, creates feature, initializes documents
- US2: User views and edits spec/plan/task in separate tabs
**Duration**: ~2-3 weeks  
**Can Run in Parallel**: US1 and US2 work independently (different features/files)

### User Story 1: Repository & Feature Selection

#### Backend for US1

- [ ] T087 [P] [US1] Create repo endpoints in `backend/src/api/repositories.py`: `GET /repos`
- [ ] T088 [P] [US1] Implement repository listing with search/filter
- [ ] T089 [US1] Implement repository caching (5 min TTL)
- [ ] T090 [P] [US1] Create branch endpoints: `GET /repos/{owner}/{repo}/branches`
- [ ] T091 [P] [US1] Create feature creation endpoint: `POST /repos/{owner}/{repo}/branches`
- [ ] T092 [US1] Implement Copilot CLI invocation for branch creation + initial files
- [ ] T093 [US1] Implement feature persistence (in-memory model)
- [ ] T094 [US1] Create feature listing endpoint: `GET /features` (filtered by repo)

#### Frontend for US1

- [ ] T095 [P] [US1] Create repo selector component in `frontend/src/components/RepoSelector.tsx`
- [ ] T096 [US1] Implement searchable repo list with pagination
- [ ] T097 [P] [US1] Create feature/branch selector in `frontend/src/components/FeatureCreator.tsx`
- [ ] T098 [US1] Implement branch listing UI
- [ ] T099 [US1] Implement "Create New Feature" button + modal form
- [ ] T100 [US1] Implement feature refresh (reload branches/features from GitHub)
- [ ] T101 [US1] Create dashboard with repo/feature headers in `frontend/src/pages/dashboard.tsx`

#### Testing for US1

- [ ] T102 [P] [US1] Contract test for repo endpoints in `backend/tests/contract/test_repos.py`
- [ ] T103 [P] [US1] Unit test for GitHub client repo methods in `backend/tests/unit/test_github_client.py`
- [ ] T104 [US1] Integration test for repo listing + caching in `backend/tests/integration/test_repo_flow.py`
- [ ] T105 [US1] Component test for RepoSelector in `frontend/tests/unit/RepoSelector.test.tsx`
- [ ] T106 [US1] Component test for FeatureCreator in `frontend/tests/unit/FeatureCreator.test.tsx`
- [ ] T107 [US1] E2E test for full repo selection → feature creation flow in `frontend/tests/e2e/repo-selection.spec.ts`

### User Story 2: Spec/Plan/Task Tab-Based Workflow

#### Backend for US2

- [ ] T108 [P] [US2] Create document endpoints in `backend/src/api/documents.py`: `GET /features/{id}/spec`
- [ ] T109 [P] [US2] Create spec fetch endpoint (read from GitHub)
- [ ] T110 [P] [US2] Create spec update endpoint: `PUT /features/{id}/spec`
- [ ] T111 [US2] Implement spec persistence to GitHub via API (version tracking)
- [ ] T112 [P] [US2] Create plan fetch endpoint: `GET /features/{id}/plan`
- [ ] T113 [P] [US2] Create plan update endpoint: `PUT /features/{id}/plan`
- [ ] T114 [P] [US2] Create task fetch endpoint: `GET /features/{id}/task`
- [ ] T115 [P] [US2] Create task update endpoint: `PUT /features/{id}/task`
- [ ] T116 [US2] Implement optimistic locking (if_match header for conflict detection)

#### Frontend for US2

- [ ] T117 [P] [US2] Create tab layout component in `frontend/src/components/TabLayout.tsx`
- [ ] T118 [P] [US2] Create SpecEditor component in `frontend/src/components/DocumentEditors/SpecEditor.tsx`
- [ ] T119 [US2] Implement spec content editing with markdown support
- [ ] T120 [US2] Implement spec save button + unsaved changes indicator
- [ ] T121 [P] [US2] Create PlanEditor component in `frontend/src/components/DocumentEditors/PlanEditor.tsx`
- [ ] T122 [P] [US2] Create TaskEditor component in `frontend/src/components/DocumentEditors/TaskEditor.tsx`
- [ ] T123 [US2] Implement editor theme + syntax highlighting for markdown
- [ ] T124 [US2] Implement tab switching preserve state (unsaved changes warning)
- [ ] T125 [US2] Implement "Create Spec" template button (creates placeholder)
- [ ] T126 [US2] Implement "Create Plan" template button
- [ ] T127 [US2] Implement "Create Task" template button

#### Testing for US2

- [ ] T128 [P] [US2] Contract test for document endpoints in `backend/tests/contract/test_documents.py`
- [ ] T129 [P] [US2] Unit test for document model in `backend/tests/unit/test_documents.py`
- [ ] T130 [US2] Integration test for spec → save → reload flow in `backend/tests/integration/test_document_flow.py`
- [ ] T131 [P] [US2] Component test for SpecEditor in `frontend/tests/unit/SpecEditor.test.tsx`
- [ ] T132 [P] [US2] Component test for PlanEditor in `frontend/tests/unit/PlanEditor.test.tsx`
- [ ] T133 [P] [US2] Component test for TaskEditor in `frontend/tests/unit/TaskEditor.test.tsx`
- [ ] T134 [US2] E2E test for full document workflow in `frontend/tests/e2e/documents.spec.ts`

**Checkpoint**: User Stories 0-2 complete. MVP is now functional (auth + repo selection + document editing). Proceed to optional features (US3-7).

---

## Phase 5: User Stories 3-6 (Priority: P2) - Optional Advanced Features (Weeks 4-6)

**Goal**: Add optional workflows (clarify, analyze, WebSocket, transparency)  
**Note**: Can be deferred to Phase 2 release; MVP works without these  
**Duration**: ~2 weeks (if included in MVP)

### User Story 3: Clarify Step (Optional)

- [ ] T135 [P] [US3] Create clarify endpoint: `POST /features/{id}/clarify` in `backend/src/api/operations.py`
- [ ] T136 [US3] Implement Copilot CLI invocation for clarification
- [ ] T137 [US3] Implement WebSocket streaming during clarify operation
- [ ] T138 [P] [US3] Create "Clarify" button on SpecEditor in `frontend/src/components/OperationButtons.tsx`
- [ ] T139 [US3] Implement real-time message display during clarification
- [ ] T140 [US3] Create Clarification Q&A display component
- [ ] T141 [US3] Implement spec auto-update with clarifications on completion

### User Story 4: Analyze Step (Optional)

- [ ] T142 [P] [US4] Create analyze endpoint: `POST /features/{id}/analyze` in `backend/src/api/operations.py`
- [ ] T143 [US4] Implement Copilot CLI invocation for task analysis
- [ ] T144 [US4] Implement WebSocket streaming during analysis
- [ ] T145 [P] [US4] Create "Analyze" button on TaskEditor
- [ ] T146 [US4] Implement AnalysisResult display component (completeness score, risks, recommendations)

### User Story 5: WebSocket Real-Time Conversation (P2)

- [ ] T147 [US5] Already implemented in Phase 2 (T043-T049)
- [ ] T148 [P] [US5] Create ConversationPanel component in `frontend/src/components/ConversationPanel.tsx`
- [ ] T149 [US5] Implement message rendering (thinking/execution/error/complete types)
- [ ] T150 [US5] Implement collapsible thinking sections
- [ ] T151 [US5] Implement auto-scroll to latest message
- [ ] T152 [US5] Implement message timestamps + sender labels

### User Story 6: LLM Thinking Transparency (P2)

- [ ] T153 [US6] Already integrated with message types (thinking messages)
- [ ] T154 [P] [US6] Add thinking section styling (different color/indent)
- [ ] T155 [US6] Add toggle to show/hide thinking (user preference)

**Checkpoint**: Optional features complete. MVP + advanced features ready for beta testing.

---

## Phase 6: User Story 7 & Polish (Priority: P3) - Future Enhancement

**Goal**: Prepare for future constitution.md integration; polish edges  
**Note**: Deferred to Phase 2 release or later  
**Duration**: ~1 week

- [ ] T156 [P] [US7] Design constitution.md integration point (future)
- [ ] T157 [P] [US7] Create placeholder for constitution tab (disabled in MVP)
- [ ] T158 Document constitution.md requirements for future implementation

---

## Phase 7: Final Polish & Cross-Cutting Concerns (Week 6+)

**Purpose**: Edge cases, error handling, performance, security, documentation  
**Duration**: ~1-2 weeks

### Error Handling & Edge Cases

- [ ] T159 [P] Implement exhaustive error handling for all API endpoints (400/401/403/404/429)
- [ ] T160 [P] Handle GitHub API rate limiting user-facing errors
- [ ] T161 [P] Handle malformed spec/plan/task documents gracefully
- [ ] T162 [P] Handle WebSocket disconnection + reconnection edge cases
- [ ] T163 [P] Handle Copilot CLI subprocess failures (timeout, crash, missing)

### Security Hardening

- [ ] T164 [P] Implement HTTPS requirement check (HTTP only allowed for localhost)
- [ ] T165 [P] Add security headers (HSTS, CSP, X-Frame-Options)
- [ ] T166 [P] Implement CSRF protection for state-changing operations
- [ ] T167 [P] Add request signing for WebSocket handshake
- [ ] T168 Implement comprehensive token expiration + removal from all storages

### Performance Optimization

- [ ] T169 [P] Optimize GitHub API calls (batch where possible)
- [ ] T170 [P] Implement aggressive caching for repo/branch lists
- [ ] T171 [P] Implement frontend code-splitting + lazy loading
- [ ] T172 [P] Add database indices (Phase 2+)

### Testing Completeness

- [ ] T173 [P] Add stress testing for WebSocket (100s of messages)
- [ ] T174 [P] Add performance testing for backend (concurrent users)
- [ ] T175 [P] Add accessibility testing (WCAG 2.1 AA compliance)
- [ ] T176 Secure critical path end-to-end tests
- [ ] T177 Add load testing for GitHub API interactions

### Documentation

- [ ] T178 [P] Update README with feature overview
- [ ] T179 [P] Update DEPLOYMENT.md with production checklist
- [ ] T180 Create API documentation (Swagger/OpenAPI export)
- [ ] T181 Create runbook for common operations (token rotation, etc.)
- [ ] T182 [P] Add inline code documentation (docstrings, JSDoc comments)

### DevOps & Infrastructure

- [ ] T183 [P] Setup CI/CD pipeline (GitHub Actions for tests + linting)
- [ ] T184 [P] Configure Docker image scanning for vulnerabilities
- [ ] T185 [P] Setup monitoring & error reporting (Sentry or similar)
- [ ] T186 [P] Configure backup/restore strategy for session data (if persistent DB added)

---

## Task Summary & Metrics

### By Phase

| Phase | Title | Tasks | Duration | Criticality |
|-------|-------|-------|----------|-------------|
| 1 | Setup | T001-T020 (20) | 1 week | CRITICAL - blocks all |
| 2 | Foundation | T021-T069 (49) | 1-2 weeks | CRITICAL - blocks user stories |
| 3 | US0 Auth | T070-T086 (17) | 1 week | CRITICAL - blocks US1/US2 |
| 4 | US1-US2 Core | T087-T134 (48) | 2-3 weeks | CRITICAL - MVP |
| 5 | US3-US6 Opt | T135-T157 (23) | 1-2 weeks | OPTIONAL - Phase 2 |
| 6 | US7 Future | T156-T157 (2) | TBD | FUTURE - Phase 2+ |
| 7 | Polish | T158-T182 (25) | 1-2 weeks | HIGH - pre-production |

**Total**: 87 tasks

### By Priority

| Priority | Count | Examples |
|----------|-------|----------|
| Parallel `[P]` | 31 | Model creation, component building, tests |
| Sequential | 56 | Integration, endpoint implementation, workflows |

### MVP Delivery Path

**Minimum to ship MVP** (Weeks 1-6):
- ✅ Phase 1: Setup (T001-T020)
- ✅ Phase 2: Foundation (T021-T069)
- ✅ Phase 3: US0 Auth (T070-T086)
- ✅ Phase 4: US1-US2 (T087-T134)
- ⏱ Phase 7 Polish: Critical fixes only (T159-T163, T164-T168)

**Post-MVP Enhancements** (Phase 2 release):
- Phase 5: US3-US6 Advanced (T135-T157)
- Phase 7: Performance + DevOps (T169-T186)
- Phase 6: US7 Future Constitution

### Parallel Execution Opportunities

**Independent Sprint 1 (Weeks 1-2)**:
- Backend foundation (T021-T031) runs in parallel with Frontend foundation (T054-T069)
- Testing infrastructure (T013-T016) runs independently

**Independent Sprint 2 (Weeks 2-3)**:
- US1 Repository features (T087-T094) in parallel with US2 Document features (T108-T115)
- Frontend US1 components (T095-T101) in parallel with Frontend US2 components (T117-T127)

**Independent Sprint 3 (Weeks 4-5)**:
- US3-US4 optional features (T135-T145) can run in parallel with testing Phase 4

---

## Implementation Strategy

### Recommended Sprint Breakdown

**Sprint 1 (Week 1-2)**:
- Phase 1 Setup: All infrastructure (T001-T020)
- Phase 2 Foundation Part 1: Models + GitHub client (T021-T044)

**Sprint 2 (Week 2-3)**:
- Phase 2 Foundation Part 2: WebSocket + Frontend foundation (T045-T069)
- Phase 3 Start: US0 Auth backend (T070-T073)

**Sprint 3 (Week 3-4)**:
- Phase 3 Complete: US0 Auth frontend + tests (T074-T086)
- Phase 4 Start: US1 backend repositories (T087-T094)

**Sprint 4 (Week 4-5)**:
- Phase 4 Continue: US1 frontend + US2 backend (T095-T115)

**Sprint 5 (Week 5-6)**:
- Phase 4 Complete: US2 frontend + testing (T116-T134)
- Phase 7 Begin: Critical polish + security (T159-T168)

**Sprint 6+ (Week 6-8)**:
- Optional Phase 5: US3-US6 advanced features (if included in MVP)
- Phase 7 Complete: Performance + DevOps (T169-T186)

### Testing Strategy

**Tests should be written FIRST (TDD)**:
- Contract tests (backend API contracts) before implementation
- Component tests before UI implementation
- E2E tests before full workflow implementation

**Test Coverage Target**: 70%+ for Phase 3-4 (critical path); 50%+ for optional features

---

## Dependencies & Blockers

### Critical Path (Must Complete Sequentially)

```
T001-T020 (Setup)
  ↓
T021-T069 (Foundation)
  ↓
T070-T086 (US0 Auth)
  ├─ T087-T107 (US1 Backend + Tests) ← parallel with US2
  └─ T108-T134 (US2: Document Workflow)
```

### Can Run in Parallel

- Backend models (T021-T024) & Frontend auth context (T054-T057) - different repos
- Backend GitHub client (T026-T031) & Frontend API service (T058-T061) - different repos
- US1 (T087-T107) & US2 (T108-T134) - independent features, different endpoints

---

## Success Criteria Per User Story

| Story | Independent Test | Success Metrics |
|-------|------------------|-----------------|
| **US0** | User logs in, authenticates, token persists | Auth works; token in sessionStorage; 401 triggers re-auth |
| **US1** | User selects repo, creates feature, initializes docs | Repo list loads; branch created on GitHub; spec.md exists |
| **US2** | User edits spec/plan/task in tabs, save persists | Document content editable; changes persist to GitHub; tabs don't lose data |
| **US3** | User triggers Clarify, sees Q&A, spec updates | WebSocket streams messages; clarifications integrate into spec |
| **US4** | User triggers Analyze, sees completeness score | Analysis runs; score + risks + recommendations displayed |
| **US5** | App streams real-time Copilot CLI output | WebSocket messages arrive < 500ms latency; reconnect replays |
| **US6** | LLM thinking visible + collapsible | Thinking messages shown; can expand/collapse |
| **US7** | Constitution placeholder ready for future | Placeholder exists; can be activated in Phase 2 |

---

## Notes & Caveats

**Phase 1 Assumptions**:
- Single developer environment (localhost)
- GitHub PAT for authentication (no OAuth2 yet)
- In-memory storage only (no database)
- Docker Compose for local dev (production later)

**Phase 2 Database Migration** (post-MVP):
- Add PostgreSQL + migrations
- Replace in-memory models with ORM (SQLAlchemy)
- Add session/audit logging

**Phase 2 OAuth2 Migration** (post-MVP):
- Replace GitHub PAT with OAuth2 Apps flow
- Add user table + login tracking
- Add per-user token refresh logic

---

## Resources & References

- Plan: [plan.md](plan.md)
- Data Model: [data-model.md](data-model.md)
- API Contracts: [contracts/github-integration.md](contracts/github-integration.md) + [contracts/websocket-messages.md](contracts/websocket-messages.md)
- Research: [research.md](research.md)
- Quickstart: [quickstart.md](quickstart.md)

---

**Last Updated**: February 18, 2026  
**Status**: Ready for implementation  
**Next**: Assign sprints, start Task T001

