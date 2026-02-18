# Research Findings & Best Practices

**Phase**: Phase 0  
**Date**: February 18, 2026  
**Specification**: [Feature Specification](spec.md)  
**Status**: ✅ Complete

---

## Research Summary

All critical technical unknowns resolved through specification clarification workflow (Feb 18, 2026). This document captures best practices, architectural patterns, and technology decisions used in the implementation plan.

---

## Technology Stack & Decisions

### Backend Framework

**Decision**: FastAPI (Python 3.11+)

**Rationale**:
- ✅ Native async/await support for WebSocket streaming and GitHub API calls
- ✅ Proven in production for concurrent user sessions
- ✅ Excellent async library ecosystem (aiohttp, asyncpg)
- ✅ ASGI server (Uvicorn) scales for Phase 1 (5-50 users)
- ✅ Poetry/pip dependency management aligns with Copilot CLI

**Alternatives Considered**:
- ❌ Flask: Synchronous; requires threading/multiprocessing for async operations
- ❌ Django: Overkill for this scope; slower startup
- ✅ Quart: Lighter than FastAPI but less ecosystem support

**Decision Lock**: FastAPI + Uvicorn for backend

### Frontend Framework

**Decision**: React 18 + Next.js 14 (TypeScript)

**Rationale**:
- ✅ Server-side rendering (SSR) for initial auth page performance
- ✅ React hooks + modern component patterns for document editing UX
- ✅ Excellent TypeScript support for API contract safety
- ✅ Built-in API routes (`/pages/api`) for backend integration
- ✅ Static export capability for future CDN deployment

**Alternatives Considered**:
- ⚠ Vue.js 3: Smaller ecosystem; requires separate backend framework
- ❌ Svelte: Smaller community; fewer UI component libraries
- ❌ Streamlit: Explicitly out of scope (lacks async/WebSocket)

**Build Tool**: Vite (not create-react-app; faster dev server)  
**UI Components**: Shadcn/ui or Tailwind CSS (no heavy framework burden)  
**HTTP Client**: Axios or fetch API with wrapper

**Decision Lock**: Next.js + React 18 + TypeScript for frontend

### GitHub API Integration

**Decision**: GitHub REST API v3 with async HTTP client

**Rationale**:
- ✅ Mature, well-documented REST API (GraphQL slower for list operations)
- ✅ Supports all required operations: repos, branches, file CRUD
- ✅ Rate limits: 1000/hour per token (sufficient for Phase 1)
- ✅ Personal Access Tokens (PAT) work with local dev + small teams
- ✅ Clear migration path to OAuth2 in Phase 2

**Authentication Models**:
- **Phase 1 (Current)**: GitHub PAT (Classic) with `repo` + `workflow` scopes
- **Phase 2 (Future)**: GitHub OAuth Apps with web flow negotiation

**Token Management**:
- Never log tokens or include in error messages
- Store in backend only after frontend validation
- Use sessionStorage in browser (cleared on tab close)
- Implement token refresh logic (detect 401, prompt re-auth)

**HTTP Client Libraries**:
- Backend: `aiohttp` (async) or `httpx` (async + sync)
- Frontend: `axios` or native fetch API

**Decision Lock**: GitHub REST API v3 + aiohttp backend + axios frontend

### WebSocket Architecture

**Decision**: Native WebSocket protocol for real-time Copilot CLI output streaming

**Rationale**:
- ✅ Web standard; browser native support (no external libraries)
- ✅ Bi-directional communication for operation status + message history replay
- ✅ Lower latency than polling (< 500ms vs 1000ms+)
- ✅ Backend can maintain connection state + message history

**Message Format**:
```json
{
  "id": "msg_abc123",
  "operation_id": "op_xyz789",
  "type": "thinking|execution|error|complete",
  "content": "User story narrative...",
  "timestamp": "2026-02-18T14:23:45Z",
  "sequence": 1
}
```

**Reconnection Strategy**:
- Server maintains 5-10 minute message history per operation_id
- Client auto-reconnects with last_sequence for replay
- Prevents message loss on network hiccups

**Libraries**:
- Frontend: `socket.io-client` or native WebSocket API (+ reconnection logic)
- Backend: `fastapi.WebSocketRoute` with connection management

**Decision Lock**: Native WebSocket + server-side message history

### Testing Strategy

#### Backend Testing

**Unit Tests** (pytest):
- GitHub API client mocking (responses library)
- Auth service token validation
- Copilot CLI subprocess spawning
- WebSocket message formatting

**Integration Tests**:
- Mock GitHub API server (httpretty or responses)
- Real Copilot CLI subprocess (with test repo)
- Document CRUD workflows

**Test Coverage Target**: 70%+ (focus on error paths)

#### Frontend Testing

**Component Tests** (Vitest + React Testing Library):
- Document editors (spec/plan/task)
- Auth flow components
- Repo/feature selectors
- Conversation panel rendering

**E2E Tests** (Playwright or Cypress):
- Full workflow: auth → repo select → create feature → spec → clarify → plan
- Uses mock backend server
- Tests WebSocket reconnection scenarios

**Test Coverage Target**: 60%+ (focus on user workflows)

**Decision Lock**: pytest + Vitest + E2E with mock servers

---

## Architectural Patterns

### Subprocess Execution Pattern (Copilot CLI)

**Pattern**: Backend spawns Copilot CLI as subprocess; captures stdout/stderr; streams via WebSocket

```python
# Backend pseudo-code pattern
import subprocess
import json

def clarify_spec(feature_id, spec_content):
    operation_id = generate_uuid()
    
    # Start Copilot CLI subprocess
    process = subprocess.Popen(
        ["copilot", "clarify", "--spec", spec_content],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={...GITHUB_TOKEN...}
    )
    
    # Stream outputs via WebSocket
    for line in process.stdout:
        message = parse_copilot_output(line)
        broadcast_ws_message(operation_id, message)
    
    # Handle completion
    return_code = process.wait()
    if return_code == 0:
        persist_spec_to_github(feature_id, updated_spec_content)
    else:
        broadcast_ws_message(operation_id, {type: 'error', content: stderr})
```

**Gotchas**:
- ✅ Inject token via environment (not CLI args)
- ✅ Handle long-running processes (async subprocess wrapper needed)
- ✅ Persist output before WebSocket close
- ✅ Clean up temp files after completion

**Reference**: Existing `src/ui/app.py` demonstrates working pattern

### Document Editing with Browser Caching

**Pattern**: 
1. Load document from GitHub API
2. User edits in browser (changes in memory)
3. Save click → persist to GitHub API
4. Discard changes → reload from GitHub

**Implementation**:
- React state holds document content + unsaved changes flag
- Autosave debounced (5-10 sec) or manual save button
- Tab switch warning if unsaved changes

### GitHub API Rate Limiting Handling

**Pattern**: Exponential backoff + user-friendly retry guidance

```python
import asyncio

async def github_api_call_with_retry(url, headers):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await client.get(url, headers=headers)
            if response.status == 429:  # Rate limited
                retry_after = int(response.headers.get('Retry-After', 60))
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_after)
                    continue
                else:
                    return error_response('Rate limited. Please retry in 1 hour.')
            return response
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise
```

---

## Security Considerations

### GitHub Token Handling

**Rule 1: Never Log Tokens**
- Mask in logs: `ghp_***xyz` (show last 3 chars only)
- Never include in error messages
- Never send to third-party service (Sentry, DataDog must have masking rules)

**Rule 2: Browser Storage Only in sessionStorage**
- sessionStorage: Cleared on tab close (good UX, acceptable risk for Phase 1)
- LocalStorage: Increases persistence attack surface; avoid
- Cookies: httpOnly + sameSite=Strict (Phase 2 OAuth2)

**Rule 3: HTTPS Only**
- All GitHub API calls must use HTTPS
- WebSocket over WSS (secure WebSocket)
- Dev environment uses HTTP + localhost (acceptable)

**Rule 4: Token Expiration Detection**
- GitHub API returns 401 for expired/revoked tokens
- Catch 401 → prompt user to re-authenticate
- Auto-retry with new token after user re-enters

### API Rate Limiting

**GitHub PAT Rate Limits**:
- 1000 requests/hour per token (authenticated)
- 60 requests/hour per IP (unauthenticated - not used here)

**Mitigation**:
- Implement request deduplication (cache repo listings for 5 min)
- Batch file operations (create multiple files in single GitHub API call if possible)
- Inform users when approaching limits (e.g., "850/1000 requests used this hour")

---

## Dependency Analysis

### Python Backend Dependencies

**Core**:
- `fastapi`: HTTP framework
- `uvicorn`: ASGI server
- `pydantic`: Request/response validation
- `python-dotenv`: Environment variable management

**GitHub Integration**:
- `PyGithub`: High-level GitHub API client OR
- `aiohttp`: Async HTTP client (lower-level, more control)
- `requests`: Fallback HTTP client (synchronous)

**WebSocket**:
- `websockets`: Native WebSocket library (comes with FastAPI)

**Testing**:
- `pytest`: Test framework
- `pytest-asyncio`: Async test support
- `responses` or `httpretty`: HTTP mocking
- `pytest-cov`: Coverage reporting

**Database** (Phase 2):
- `sqlalchemy`: ORM (only if server-side session storage needed)
- `asyncpg`: Async Postgres driver (Phase 2)

### Node.js Frontend Dependencies

**Core**:
- `react@18`: UI framework
- `next@14`: React framework
- `typescript`: Type safety

**HTTP**:
- `axios`: HTTP client
- `swr` or `react-query`: Data fetching + caching

**UI**:
- `tailwindcss`: Utility CSS framework
- `shadcn/ui`: React component library (optional, built on Tailwind)
- `react-markdown`: Render markdown spec/plan/task content

**WebSocket**:
- `socket.io-client`: WebSocket client (with reconnection logic) OR
- Native WebSocket API (simpler, no external library)

**Testing**:
- `vitest`: Fast unit test runner
- `@testing-library/react`: Component testing
- `@testing-library/jest-dom`: Assertion helpers
- `@playwright/test`: E2E testing

**Build**:
- `vite`: Build tool (if using Vite + React)
- `next` (built-in): If using Next.js

---

## Deployment & DevOps

### Local Development

**Docker Compose** approach:
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports: [8000:8000]
    environment: {GITHUB_TOKEN, COPILOT_TOKEN}
  frontend:
    build: ./frontend
    ports: [3000:3000]
    depends_on: [backend]
```

### Production Deployment

**Recommended (Future Phase 2)**:
- Backend: Docker image → ECS/Kubernetes
- Frontend: Next.js SSR → Vercel, Netlify, or custom Docker
- Database: PostgreSQL (if needed for session storage)
- Secrets: GitHub Secrets, HashiCorp Vault, or AWS Secrets Manager

---

## Glossary & Definitions

| Term | Definition | Scope |
|------|-----------|-------|
| **GitHub PAT** | Personal Access Token; github.com credentials for API access | Phase 1 focus |
| **WebSocket** | Real-time bidirectional protocol for async message streaming | Real-time UX |
| **Operation ID** | Unique identifier for a Copilot CLI execution (clarify/analyze) | Session tracking |
| **Feature Branch** | Git branch created by Copilot CLI for feature development | Core entity |
| **Document Persistence** | Writing spec/plan/task to GitHub repository via API | Cloud-first pattern |
| **Subprocess** | Spawned Copilot CLI process managed by backend | Execution model |
| **HTTPS** | Encrypted HTTP required for all external API calls | Security |

---

## Recommendation for Next Phase

**Phase 1 is Code-Ready**: All architectural decisions locked. Backend can begin with:
1. FastAPI scaffold + GitHub API client wrapper
2. Auth endpoint + token validation
3. Repository listing + branch management
4. WebSocket endpoint + Copilot CLI subprocess runner

Frontend can begin with:
1. Next.js scaffold + auth flow
2. Repo/feature selector UI
3. Document editor components (spec/plan/task tabs)
4. WebSocket message display

**Target**: MVP complete in 4-6 weeks (with small team).

