# CoPilot Companion: Technical Architecture & Design Decisions

**Project**: CoPilot Companion - Democratizing Spec-Driven Development  
**Date**: February 20, 2026  
**Status**: ✅ Research Complete | Architecture Locked  
**Scope**: Phase 1 MVP (Backend + Frontend + GitHub Integration)

---

## Executive Summary

This document captures the architectural decisions, technology stack, and best practices for CoPilot Companion -- a web-based orchestration layer that brings AI-powered spec-driven development to business teams, not just engineers.

All critical technical unknowns have been resolved. The architecture is optimized for three core principles: **minimal complexity**, **git-first persistence**, and **real-time transparency**. This design enables a lean MVP in 4-6 weeks while maintaining a clear path to enterprise features.

---

## Why This Architecture?

### The Challenge
CoPilot Companion bridges business and technical teams. Business users need a friction-free interface. Engineers need version control and familiar tools. The architecture must serve both without compromising either's workflow.

### The Solution
We chose **lightweight orchestration over platform building**. Instead of creating yet another proprietary system, CoPilot Companion acts as a connector: a modern web layer that translates business language into structured Git artifacts. The architecture prioritizes:

- **Git as the single source of truth** -- no proprietary database for specs
- **Real-time streaming over polling** -- users see progress, not delayed results
- **Subprocess orchestration over custom AI** -- leverage GitHub Copilot's improvements automatically
- **Minimal state management** -- stateless backend, sessionStorage frontend

---

## Technology Stack & Decisions

### Backend Framework

**Technology**: FastAPI (Python 3.11+)

**Why FastAPI**:
- **Native async/await** for WebSocket streaming and real-time GitHub API operations
- **Battle-tested** in production environments with concurrent user sessions
- **Rich ecosystem** with mature libraries (aiohttp, asyncpg, Pydantic)
- **Efficient scaling** via ASGI server (Uvicorn) -- handles Phase 1 (5-50 concurrent users) with a single instance
- **Aligned tooling** with the Copilot CLI ecosystem (shared Python dependencies)

**What We Rejected and Why**:
- **Flask**: Synchronous by design; real-time WebSocket streaming requires thread/process complexity
- **Django**: Too much infrastructure for this use case; slower development iteration
- **Quart**: Lighter alternative, but less ecosystem maturity and smaller community

**Outcome**: FastAPI + Uvicorn provides the sweet spot between simplicity and capability

### Frontend Framework

**Technology**: React 18 + Next.js 14 (TypeScript)

**Why Next.js + React**:
- **Server-side rendering (SSR)** makes first-page-load fast for authentication flow
- **Modern React patterns** (hooks, suspense) enable responsive document editing and real-time updates
- **Type safety** with TypeScript reduces API contract bugs and improves developer experience
- **Built-in API routes** allow seamless backend integration without separate middleware
- **Export flexibility** for future CDN deployment and static optimization

**Build & UI Strategy**:
- **Vite** for dev server speed (10x faster than create-react-app)
- **Tailwind CSS + Shadcn/ui** for accessible, lightweight components (no bootstrap/material bloat)
- **Axios or native fetch** for HTTP with consistent error handling

**What We Didn't Use and Why**:
- **Vue.js 3**: Smaller JavaScript ecosystem; would need separate backend framework
- **Svelte**: Smaller community; fewer production-grade UI libraries
- **Streamlit**: Python-only; doesn't support async/WebSocket needed for real-time updates

**Outcome**: Next.js provides React developers a productive environment aligned with modern web standards

### GitHub API Integration

**Technology**: GitHub REST API v3 with async HTTP client

**Why REST API v3**:
- **Time-tested and stable** with excellent documentation and community support
- **Covers all required operations**: repository listing, branching, file CRUD, and workflow triggers
- **Predictable rate limits**: 1000 requests/hour per authenticated token (sufficient for Phase 1 usage patterns)
- **Personal Access Tokens (PAT)** work seamlessly with local development and small teams
- **Clear upgrade path** to OAuth2 in Phase 2 for multi-tenant scenarios

**Authentication Strategy**:
- **Phase 1**: GitHub Personal Access Token (scope: `repo` + `workflow`)
- **Phase 2**: GitHub OAuth Apps for web-based sign-in flow

**Security Guards for Token Handling**:
- Tokens never logged or included in error messages (mask as `ghp_***xyz`)
- Stored backend-side after frontend submits it
- Browser keeps token only in `sessionStorage` (auto-cleared on tab close)
- Implement 401 detection with automatic re-authentication prompts

**HTTP Client Selection**:
- **Backend**: `aiohttp` (async) for concurrent GitHub API calls
- **Frontend**: `axios` for consistency across API requests

**Outcome**: REST API v3 offers stability, simplicity, and a well-worn path for GitHub integrations

### Real-Time Streaming with WebSocket

**Technology**: Native WebSocket protocol for live Copilot CLI output

**Why WebSocket**:
- **Web standard** with native browser support -- no external libraries required
- **Bi-directional communication** enables real-time progress updates AND server-initiated reconnection recovery
- **Orders of magnitude lower latency** compared to HTTP polling (< 200ms vs 1000ms+)
- **Server-side state tracking** maintains operation context and message history for resilience

**Message Protocol**:
```json
{
  "id": "msg_abc123",
  "operation_id": "op_xyz789",
  "type": "thinking|execution|error|complete",
  "content": "Generating user story narrative...",
  "timestamp": "2026-02-18T14:23:45Z",
  "sequence": 1
}
```

**Resilience Strategy**:
- Server persists 5-10 minute message history per operation
- Client auto-reconnects using `last_sequence` number
- Automatic message replay on reconnection prevents data loss
- Handles transient network interruptions transparently

**Implementation**:
- **Frontend**: Native WebSocket API with built-in reconnection logic
- **Backend**: FastAPI's `WebSocketRoute` with connection pooling

**Outcome**: WebSocket provides real-time transparency without external dependencies or polling overhead

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

### Real-Time AI Processing: Subprocess Orchestration

**Pattern**: Backend spawns Copilot CLI as subprocess; captures all output streams; broadcasts results via WebSocket in real-time

**Why This Pattern**:
Rather than building proprietary AI models, we orchestrate GitHub Copilot CLI as a subprocess. This approach:
- Automatically benefits from Copilot's continuous improvements
- Decouples our system from AI training/infrastructure
- Simplifies error handling (CLI returns structured exit codes and stderr)
- Enables progress transparency (can stream stdout line-by-line)

**Typical Implementation**:
```python
# Simplified pseudocode showing the orchestration pattern
import subprocess
import json
from datetime import datetime

def execute_copilot_operation(operation_type, input_spec):
    operation_id = generate_uuid()
    
    # Prepare environment with GitHub token
    env = get_environment_variables(github_token)
    
    # Spawn Copilot CLI subprocess
    process = subprocess.Popen(
        ["copilot", operation_type, "--input", input_spec],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    
    # Stream output to all connected WebSocket clients
    for line in process.stdout:
        message = parse_output_line(line)  # Extract structured data
        broadcast_to_websocket_clients(operation_id, message)
    
    # Await completion and handle result
    return_code = process.wait()
    if return_code == 0:
        persist_results_to_github(operation_id, parsed_output)
    else:
        broadcast_error(operation_id, process.stderr.read())
```

**Critical Implementation Details**:
- **Never pass token as CLI argument** -- always inject via environment variables
- **Stream stdout in real-time** -- don't wait for process completion to show feedback
- **Persist results before WebSocket close** -- prevent data loss on client disconnect
- **Clean up temporary files** -- Copilot CLI may create temp directories
- **Implement timeouts** -- long-running processes should have configurable limits

**Production Hardening**:
- Use `asyncio.create_subprocess_exec()` instead of `subprocess.Popen` for true async execution
- Implement connection pooling to avoid spawning too many processes
- Add structured logging of all subprocess interactions for audit trails

### Document Persistence: Git as Source of Truth

**Pattern**: All user-generated content (specs, plans, tasks) is persisted as files in a Git repository, not in a proprietary database

**Why This Pattern**:
- **Version control is free** -- Git provides history, blame, and rollback automatically
- **Works offline** -- users can continue work if backend is unavailable
- **Familiar to engineers** -- no special tools or databases required
- **Portable** -- users can migrate repos without vendor lock-in

**Implementation**:
1. User creates/edits spec in browser → stored in memory (React state)
2. User clicks "Save" → frontend sends content to backend
3. Backend commits changes to Git repository via GitHub API
4. Backend broadcasts "saved" confirmation via WebSocket
5. On page reload → fetch latest from GitHub; merge with any local memory edits

### GitHub API Rate Limiting: Exponential Backoff

**Pattern**: When GitHub API returns 429 (rate limited), wait with exponential backoff and friendly user messaging

**Why This Pattern**:
- Provides automatic resilience without user intervention
- Respects API provider's rate limits (ethical API consumption)
- Graceful degradation (feature works, just slower)

**Implementation**:
```python
import asyncio
from functools import wraps

async def github_api_call_with_retry(operation):
    max_retries = 3
    base_wait = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            response = await operation()
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_after + (2 ** attempt))
                    continue
                else:
                    return error('Rate limit exceeded. Please retry in 1 hour.')
            return response
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(base_wait * (2 ** attempt))
            else:
                raise
```

---

## Security Considerations

### GitHub Token Security

**Never Log Tokens**
- Tokens should never appear in logs, error messages, or crash reports
- **Implement masking**: Show only last 3-4 characters (e.g., `ghp_***abc123`)
- Configure external logging services (Sentry, DataDog) with masking rules
- Regular audit: Search logs for patterns that look like tokens

**Never Store Tokens Permanently**
- Frontend: Use `sessionStorage` only (auto-cleared on tab close)
- **Avoid**: `localStorage` (persists across browser sessions)
- **Avoid**: Cookies without `httpOnly` flag (accessible to JavaScript)
- Backend: Store in memory only during active sessions

**HTTPS Only**
- All API communication must use HTTPS (HTTP for localhost only)
- WebSocket over WSS (secure WebSocket) in production
- GitHub API requires HTTPS; enforce on our backend too

**Token Expiration & Rotation**
- Monitor for 401 (Unauthorized) responses from GitHub API
- Catch 401 → prompt user to re-authenticate
- Implement token refresh/renewal (depends on GitHub authentication model)

### API Rate Limiting & Fair Use

**GitHub's Limits**:
- 1000 requests/hour per authenticated Personal Access Token
- 60 requests/hour per IP (unauthenticated -- not applicable here)

**How We Respect Limits**:
- **Implement request deduplication**: Cache repo listings for 5-10 minutes
- **Batch operations**: Combine multiple file updates into single API call where possible
- **Progressive loading**: Lazy-load file lists instead of loading all at once
- **User transparency**: Display "850/1000 requests used this hour" in UI

**When Limits Are Hit**:
- Implement exponential backoff (wait longer between retries)
- Show friendly message: "GitHub API busy. Retrying in 30 seconds."
- Never retry more than 3-5 times (prevent infinite loops)

### Input Validation & XSS Prevention

**Backend Validation**:
- Validate all input from frontend (treat like external API calls)
- Spec content: Limit size (e.g., max 100KB per spec)
- GitHub tokens: Validate format before using
- Operation parameters: Whitelist allowed values (e.g., operation_type in ["clarify", "analyze", "plan"])

**Frontend Rendering**:
- Use React's built-in XSS protections (JSX escapes by default)
- For dynamic HTML (Markdown specs): Use `react-markdown` or sanitizer library
- Never use `dangerouslySetInnerHTML` without sanitizing content first

### Dependency Security

**Before Production**:
- Regular `npm audit` and `pip audit` runs
- Monitor dependencies for known vulnerabilities (GitHub Dependabot)
- Use pinned versions (avoid `*` ranges) for critical dependencies
- Review changelog before upgrading major versions

**Supply Chain**:
- Use only official npm and PyPI registries
- Consider signing commits (GPG) for production branches
- Regular security reviews of dependency usage (unused imports)

### Deployment Security

**Environment Variables**:
- Never commit `.env` files to Git (use `.env.template` instead)
- Rotate tokens regularly
- Use separate tokens for dev, staging, production

**Docker Image Security**:
- Scan Docker images for vulnerabilities (`docker scan`)
- Use minimal base images (Python slim, Node.js alpine)
- Run containers as non-root user
- Don't add secrets to Docker images (use build args + runtime env)

**Secrets Management**:
- Local dev: `.env.local` files (gitignored)
- GitHub Actions: GitHub Secrets or external vault
- Production: AWS Secrets Manager, HashiCorp Vault, or similar

### Audit & Monitoring

**Recommended Logging**:
- API request/response times (performance monitoring)
- Failed authentication attempts (security)
- GitHub API errors (debugging)
- WebSocket connection events (for troubleshooting)

**What NOT to Log**:
- User tokens or credentials
- Full request bodies (redact sensitive fields)
- Personal data (unless anonymized)

**Retention Policy**:
- Development: 7 days
- Production: 30-90 days (depending on compliance requirements)

---

## Dependency Analysis

### Python Backend Dependencies

**Core Framework & Server**:
- `fastapi` -- Web framework with built-in async support
- `uvicorn` -- ASGI server (production-grade)
- `pydantic` -- Request/response validation and type safety
- `python-dotenv` -- Environment variable management

**GitHub Integration & HTTP**:
- `aiohttp` -- Async HTTP client for concurrent GitHub API calls (recommended)
- `requests` -- Synchronous HTTP client (fallback)
- **Option 1**: PyGithub for high-level API abstraction
- **Option 2**: Direct REST API calls with aiohttp (lower-level control)

**Real-Time Communication**:
- `websockets` -- Native WebSocket support (included with FastAPI)

**Testing & Quality**:
- `pytest` -- Test framework
- `pytest-asyncio` -- Async test support
- `responses` or `httpretty` -- HTTP response mocking
- `pytest-cov` -- Coverage reporting

**Future Phase 2 (Database)**:
- `sqlalchemy` -- ORM (only if server-side session storage needed)
- `asyncpg` -- Async PostgreSQL driver

### Node.js Frontend Dependencies

**React & Framework**:
- `react@18` -- UI framework
- `next@14` -- React meta-framework (SSR, routing, API routes)
- `typescript` -- Type safety

**HTTP & Data Fetching**:
- `axios` -- HTTP client with consistent error handling
- `swr` or `react-query` -- Data fetching + automatic caching

**UI & Styling**:
- `tailwindcss` -- Utility-first CSS framework
- `shadcn/ui` -- Component library built on Tailwind (optional)
- `react-markdown` -- Render Markdown content (specs, plans)

**Real-Time Communication**:
- Native **WebSocket API** (no external library needed) OR
- `socket.io-client` (if using Socket.io; adds reconnection logic)

**Testing & Quality**:
- `vitest` -- Fast unit test runner
- `@testing-library/react` -- Component testing
- `@testing-library/jest-dom` -- Assertion helpers
- `@playwright/test` -- End-to-end browser testing

**Build Tools**:
- `vite` -- Development server (if not using Next.js)
- Next.js built-in tooling (if using Next.js)

### Dependency Version Strategy

**Before Production**:
- Pin major versions (e.g., `fastapi>=0.100,<1.0`)
- Use `~=` for stable dependencies (`pydantic~=2.0`)
- Run security audits: `npm audit`, `pip audit`
- Test upgrade path before deploying

**Maintenance**:
- Enable Dependabot in GitHub for automated pull requests
- Review and test dependency updates monthly
- Monitor security advisories (npm, PyPI, GitHub)

**Rationale**:
Pinned versions prevent unexpected breaking changes while still allowing patch updates (bug fixes). Automated tooling reduces manual overhead.

---

## Deployment & DevOps

### Local Development

**Quick Start**:
```bash
# Clone repository
git clone https://github.com/your-org/copilot-companion
cd copilot-companion

# Option 1: Docker Compose (recommended)
docker-compose up

# Option 2: Automated setup script
./setup.sh

# Option 3: Manual setup
python -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
npm install --prefix frontend
export GITHUB_TOKEN=<your-token>
npm run dev --prefix frontend &
uvicorn backend.main:app --reload
```

**Docker Compose Configuration**:
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      GITHUB_TOKEN: ${GITHUB_TOKEN}
      COPILOT_TOKEN: ${COPILOT_TOKEN}
    volumes:
      - ./backend:/app  # Hot-reload on code changes

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
```

**Development Workflow**:
- Backend changes auto-reload (Uvicorn `--reload` flag)
- Frontend changes hot-reload (Next.js dev server)
- Database migrations (Phase 2): Use Alembic for schema versioning

### Production Deployment

**Backend**:
- **Container**: Docker image with slim Python base
- **Orchestration**: ECS (AWS), Kubernetes, or Cloud Run (GCP)
- **Server**: Uvicorn with gunicorn (3-4 workers for concurrency)
- **Environment**: Set via secrets manager (GitHub Secrets, AWS Secrets Manager)

**Frontend**:
- **Options**:
  - **Vercel** (recommended for Next.js): Git-linked automatic deployments
  - **Netlify** or **GitHub Pages**: Static export (if not using SSR)
  - **Self-hosted**: Docker + reverse proxy (Nginx)
- **CDN**: Cloudflare or AWS CloudFront for static assets

**Database** (Phase 2):
- **PostgreSQL** on AWS RDS, Google Cloud SQL, or managed Postgres provider
- **Connection pooling**: pgBouncer to prevent connection exhaustion
- **Backups**: Automated daily snapshots with retention policy

**Monitoring**:
- **Application**: Sentry or Datadog for error tracking
- **Performance**: New Relic, Datadog, or AWS CloudWatch
- **Logging**: CloudWatch, ELK stack, or Datadog (ensure token masking)

**CI/CD Pipeline** (GitHub Actions):
```yaml
# .github/workflows/deploy.yml (simplified)
name: Deploy
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm test --prefix frontend
      - run: pytest backend/
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: docker build -f backend/Dockerfile -t backend:latest .
      - run: docker build -f frontend/Dockerfile -t frontend:latest .
  deploy:
    runs-on: ubuntu-latest
    needs: [test, build]
    steps:
      - run: docker push backend:latest
      - run: docker push frontend:latest
      - run: kubectl set image deployment/copilot-backend backend=backend:latest
```

### Scaling Considerations

**Phase 1** (5-50 concurrent users):
- Single Uvicorn instance sufficient
- SQLite or in-memory session storage
- GitHub API rate limits (1000/hour) not stressed

**Phase 2** (50-500 concurrent users):
- Multiple Uvicorn instances behind load balancer
- PostgreSQL for persistent sessions
- Redis for caching GitHub API responses
- Consider GitHub App (higher rate limits)

**Phase 3** (500+ concurrent users):
- Kubernetes auto-scaling
- Database read replicas
- Message queue (Celery/RabbitMQ) for long-running tasks
- GitHub App with OAuth2 (one token per user session)

---

## Glossary & Reference

| Term | Definition | Scope |
|------|-----------|-------|
| **GitHub Personal Access Token** | Credential for API access; `ghp_*` format; scopes control permissions | Phase 1: Core auth mechanism |
| **WebSocket** | Real-time bidirectional protocol; enables server-push and client-listen | Real-time UX feature |
| **Operation ID** | UUID for each Copilot CLI execution; used for message tracking and replay | Session state |
| **Feature Branch** | Git branch created/managed by Copilot CLI for feature development | Git workflow |
| **Subprocess** | Spawned Copilot CLI process managed by backend; enables AI orchestration | Core execution model |
| **HTTPS** | Encrypted HTTP; required for all public API calls | Security requirement |
| **Rate Limit** | GitHub API quota; 1000 requests/hour per authenticated token | API constraint |
| **Exponential Backoff** | Retry strategy with increasing delay (1s, 2s, 4s, ...) | Resilience pattern |
| **Stateless** | Backend doesn't store request context; each request is independent | Scalability principle |
| **Idempotent** | Operation produces same result if repeated; safe to retry | Error recovery |

---

## Next Steps & Future Phases

### Phase 1 (MVP - 4-6 weeks)
✅ **Complete**: Architecture design, technology selection, prototype

**In Progress**: Full stack implementation
- ✓ FastAPI backend scaffold
- ✓ GitHub API client wrapper
- ✓ WebSocket real-time streaming
- ✓ Next.js frontend with auth flow
- ✓ Document editor components
- ✓ End-to-end integration tests

**Target Launch**: GitHub repo + demo video

### Phase 2 (Production Readiness - 6-8 weeks)
- **OAuth2 Authentication**: Multi-user support with GitHub OAuth Apps
- **PostgreSQL Backend**: Persistent storage for sessions and operation history
- **Kubernetes Deployment**: Auto-scaling and high availability
- **Advanced Copilot Integration**: Leverage new Copilot API features
- **Usage Analytics**: Track which features create most value

### Phase 3 (Enterprise Edition - 4+ months)
- **Self-Hosted Option**: On-premise deployment for regulated industries
- **Team Collaboration**: Real-time co-editing of specs
- **Audit Logging**: Full compliance trail for SOC 2 / ISO 27001
- **Custom Integration**: API for extending with proprietary tools
- **Advanced AI**: Fine-tune Copilot on company-specific patterns

---

## Conclusion

CoPilot Companion's architecture prioritizes three core principles:

1. **Minimal Complexity** -- Use off-the-shelf tools (GitHub API, Copilot CLI) instead of building proprietary systems. This reduces maintenance burden and automatically benefits from ecosystem improvements.

2. **Git-First Persistence** -- Treat version control as the permanent record. This aligns with engineering workflows and eliminates vendor lock-in.

3. **Real-Time Transparency** -- WebSocket streaming ensures users see progress and understand system state. This builds trust and enables better error diagnosis.

With this foundation, the MVP can launch in 4-6 weeks. The architecture scales to enterprise needs (Phase 2, Phase 3) without fundamental redesign. All technical unknowns have been resolved; implementation is the next milestone.

**For Developers**: Start with the technology stack (FastAPI + React 18 + Next.js) and reference the architectural patterns. Full example implementations are in `src/ui/app.py` and the working prototype.

**For Architects**: This document captures all design decisions, trade-offs, and future migration paths. Use this as the reference for on-boarding new technical leads.

**For Stakeholders**: CoPilot Companion bridges the gap between business teams and AI-powered development. It's lean, focused, and ready to demonstrate real value within a quarter.

