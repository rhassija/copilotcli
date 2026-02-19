# Data Model & Domain Entities

**Phase**: Phase 1 Design  
**Date**: February 18, 2026  
**Specification**: [Feature Specification](spec.md)  
**Status**: ✅ Complete

---

## Overview

This document defines the data model for the Copilot CLI web UI, covering all entities, relationships, validation rules, and state transitions.

**Scope**: All entities and relationships needed for Phase 1 MVP (auth, repo selection, spec/plan/task management, WebSocket sessions).

---

## Core Entity Definitions

### 1. User

**Purpose**: Represent an authenticated GitHub user

```yaml
Entity: User
Identifier: github_username (unique)
Attributes:
  - id: UUID (internal ID for DB storage, Phase 2+)
  - github_username: string (e.g., "rajesh-hassija")
  - github_user_id: integer (GitHub user ID)
  - name: string (display name)
  - avatar_url: string (GitHub avatar)
  - email: string (optional, if accessible via token)
  - created_at: timestamp (when user first authenticated)
  - last_active: timestamp (last API call)
  - token_validated_at: timestamp (last token validation)

Constraints:
  - github_username must be 1-39 characters, alphanumeric + hyphens
  - email is optional (depends on GitHub token scopes)
  - last_active updates on each API call; used for session management

Relationships:
  - User → Repository (1:many) - GitHub API enumeration
  - User → AuthSession (1:many) - multiple browser tabs/devices
```

**Storage** (Phase 1): Sessions only (no persistent database)  
**Storage** (Phase 2): PostgreSQL users table with login audit trail

### 2. AuthSession

**Purpose**: Track authenticated sessions and token data

```yaml
Entity: AuthSession
Identifier: session_id (UUID)
Attributes:
  - session_id: UUID (unique)
  - github_username: string (FK to User)
  - token_hash: string (SHA-256 hash, never plaintext)
  - created_at: timestamp
  - last_active: timestamp
  - expires_at: timestamp (token expiration)
  - browser_fingerprint: string (optional, for Phase 2 CSRF protection)
  - ip_address: string (for audit, masked in logs)

Constraints:
  - Token must have "repo" and "workflow" scopes
  - Session expires when token expires (GitHub determines)
  - 401 response from GitHub invalidates session
  - Max 100 symbols in token_hash (SHA-256 = 64 hex chars)

Relationships:
  - AuthSession → User (N:1)
  - AuthSession → WebSocketSession (1:many) - one session may have multiple tabs/WS connections
```

**Storage** (Phase 1): In-memory + browser sessionStorage  
**Storage** (Phase 2): Redis (distributed session management)

### 3. Repository

**Purpose**: Represent a GitHub repository accessible to user

```yaml
Entity: Repository
Identifier: {owner}/{repo} (composite, e.g., "facebook/react")
Attributes:
  - id: string (GitHub repository ID, unique across GitHub)
  - owner: string (repository owner login)
  - name: string (repository name)
  - full_name: string (owner/name)
  - description: string (repo description)
  - url: string (GitHub HTTPS URL)
  - is_private: boolean
  - is_fork: boolean
  - created_at: timestamp (GitHub creation)
  - updated_at: timestamp (last GitHub push)
  - default_branch: string (e.g., "main" or "master")
  - topics: [string] (GitHub repo topics/tags)

Constraints:
  - Only includes repos user has at least "read" access
  - Filter private repos if token lacks full "repo" scope
  - Updated from GitHub API on each repo list fetch
  - No local state; always reflect GitHub authority

Relationships:
  - Repository → Branch (1:many) - GitHub branches
  - Repository → Feature (1:many) - feature branches created by UI
  - Repository → Spec/Plan/Task files (1:many) - stored in GitHub

State:
  - Initial: Empty (no features)
  - Active: Has 1+ feature branches
  - Final: N/A (persists for user lifetime on GitHub)
```

**Storage**: GitHub API cache (in-memory, expires after 5 min)  
**CRUD**: Read-only (via GitHub API; creation handled by Branch entity)

### 4. Branch

**Purpose**: Represent a Git branch in a repository

```yaml
Entity: Branch
Identifier: {owner}/{repo}/refs/heads/{branch_name}
Attributes:
  - id: string (GitHub SHA of branch tip)
  - name: string (branch name, e.g., "feature/user-auth")
  - is_default: boolean (true if main branch)
  - commit_sha: string (commit SHA at branch tip)
  - created_at: timestamp (when branch created)
  - updated_at: timestamp (last commit)

Constraints:
  - Branch name must be valid Git ref (no spaces, special chars)
  - Default branch is read-only (to avoid breaking repo)
  - Feature branches created by Copilot CLI (not by UI directly)

Relationships:
  - Branch → Feature (1:1 or N:1) - branch may have single feature or no feature
  - Branch → Spec/Plan/Task files - documents stored in branch

State Transitions:
  - Existing → Feature (when user links to feature)
  - Feature → Archived (when feature completion marked)
```

**Storage**: GitHub API (no local cache needed)  
**CRUD**: 
  - Create: Via Copilot CLI (initiated by UI, invoked as subprocess)
  - Read: From GitHub API
  - Delete: User action (via GitHub web UI, not our app scope)

### 5. Feature

**Purpose**: Represent a feature being developed (spec, plan, task workflow)

```yaml
Entity: Feature
Identifier: id (UUID)
Attributes:
  - id: UUID (internal unique ID)
  - repository_id: string (FK to Repository)
  - repository_full_name: string (owner/repo for display)
  - branch_name: string (feature branch name, e.g., "feature/user-auth")
  - branch_sha: string (branch commit SHA, for optimistic locking)
  - name: string (human-readable feature name)
  - description: string (optional, one-liner)
  - created_at: timestamp (when feature created)
  - created_by: string (github_username)
  - updated_at: timestamp (last document modified)
  - status: enum ('draft'|'in-progress'|'completed'|'archived')
  - spec_version: integer (version counter)
  - plan_version: integer (version counter)
  - task_version: integer (version counter)

Constraints:
  - feature.name must be 1-100 characters
  - status changes: draft → in-progress → completed → archived
  - spec_version, plan_version, task_version start at 0 (no doc yet)
  - branch_sha enables conflict detection (if GitHub branch moved)

Relationships:
  - Feature → User (N:1, via created_by)
  - Feature → Repository (N:1)
  - Feature → Spec (1:1, optional)
  - Feature → Plan (1:1, optional)
  - Feature → Task (1:1, optional)
  - Feature → AnalysisResult (1:1, optional)
  - Feature → WebSocketSession (1:many) - multiple concurrent sessions
  
State Machine:
  - Create: User clicks "Create Feature" → branch created on GitHub → Feature created in system
  - Draft: Initial state after creation
  - In-Progress: Manually set when user begins spec/plan workflow
  - Completed: Manually set after all tasks done
  - Archived: Read-only state, hidden from list by default
```

**Storage** (Phase 1): In-memory session state + GitHub repo (branch exists)  
**Storage** (Phase 2): PostgreSQL features table

### 6. Spec (Specification Document)

**Purpose**: Feature specification document (spec.md)

```yaml
Entity: Spec
Identifier: feature_id (FK, 1:1 relationship)
Attributes:
  - id: UUID (internal)
  - feature_id: UUID (FK)
  - content: string (full markdown text)
  - version: integer (starts at 1)
  - created_at: timestamp
  - updated_at: timestamp
  - created_by: string (github_username)
  - updated_by: string (github_username)
  - github_path: string (GitHub repo path, e.g., ".specify/specs/[spec-id]/spec.md")
  - github_sha: string (current file SHA in GitHub, for conflict detection)

Constraints:
  - content must be non-empty markdown
  - max 100KB (prevents abuse)
  - version auto-increments on each write
  - One spec per feature (1:1)

Relationships:
  - Spec → Feature (N:1, FK)
  - Spec → Clarification (1:many) - clarification questions/answers
  - Spec ← Plan (one-to-many previous versions ref)
  
State Transitions:
  - Not-Exist → Draft (user creates)
  - Draft → In-Progress (user edits)
  - In-Progress → Clarified (after clarify operation)
```

**Storage**: GitHub repository (spec.md file)  
**File Path**: `specs/{feature-id}/spec.md` (or `.specify/specs/...`)  
**CRUD**:
  - Create: Generate from template via Copilot CLI
  - Read: Fetch from GitHub API
  - Update: User edits, save via PUT /features/{id}/spec
  - Delete: User action (delete branch, not individual files)

### 7. Clarification

**Purpose**: Track clarifying questions and answers during spec refinement

```yaml
Entity: Clarification
Identifier: id (UUID)
Attributes:
  - id: UUID
  - spec_id: UUID (FK)
  - question: string (the ambiguity identified)
  - context_from_spec: string (excerpt from spec causing ambiguity)
  - answer: string (user response/clarification)
  - status: enum ('pending'|'answered'|'applied')
  - created_at: timestamp
  - answered_at: timestamp (when user provided answer)
  - applied_at: timestamp (when answer incorporated into spec)

Constraints:
  - question must be 10-500 characters
  - answer required before "answered" status
  - Clarifications are immutable after "applied" (audit trail)

Relationships:
  - Clarification → Spec (N:1, FK)
  
State Machine:
  - Pending: Generated by Copilot CLI clarify operation
  - Answered: User provides response
  - Applied: Response incorporated into spec; spec content re-generated
```

**Storage** (Phase 1): In-memory during clarify session  
**Storage** (Phase 2): Audit table in PostgreSQL

### 8. Plan (Planning Document)

**Purpose**: Implementation plan document (plan.md)

```yaml
Entity: Plan
Identifier: feature_id (FK, 1:1 relationship)
Attributes:
  - id: UUID
  - feature_id: UUID (FK)
  - content: string (full markdown text)
  - version: integer (starts at 1, independent of spec version)
  - created_at: timestamp
  - updated_at: timestamp
  - created_by: string
  - updated_by: string
  - derived_from_spec_version: integer (which spec version generated this plan)
  - github_path: string (GitHub file path)
  - github_sha: string (current SHA)

Constraints:
  - content must be non-empty markdown
  - max 100KB
  - derived_from_spec_version tracks dependency (for re-gen detection)
  - One plan per feature (1:1)

Relationships:
  - Plan → Feature (N:1)
  - Plan → Task (optional next step)
  - Plan ← Spec (reference which spec version it came from)
```

**Storage**: GitHub repository (plan.md file)  
**CRUD**: Create/Read/Update (Delete = delete feature)

### 9. Task (Task Definition Document)

**Purpose**: Task breakdown document (task.md)

```yaml
Entity: Task
Identifier: feature_id (FK, 1:1)
Attributes:
  - id: UUID
  - feature_id: UUID (FK)
  - content: string (full markdown)
  - version: integer
  - created_at: timestamp
  - updated_at: timestamp
  - created_by: string
  - updated_by: string
  - derived_from_plan_version: integer (which plan version generated this)
  - github_path: string
  - github_sha: string

Constraints:
  - content must be non-empty markdown
  - max 200KB (tasks can be large)
  - derived_from_plan_version tracks dependency

Relationships:
  - Task → Feature (N:1)
  - Task → AnalysisResult (1:1, optional)
```

**Storage**: GitHub repository (task.md file)  
**CRUD**: Create/Read/Update

### 10. AnalysisResult

**Purpose**: Results from Analyze operation on task breakdown

```yaml
Entity: AnalysisResult
Identifier: id (UUID)
Attributes:
  - id: UUID
  - feature_id: UUID (FK)
  - task_id: UUID (FK, can be null if analysis done on plan)
  - task_version: integer (which task version was analyzed)
  - completeness_score: float (0-100, % of feature coverage)
  - risk_level: enum ('low'|'medium'|'high')
  - identified_dependencies: [string] (task IDs or descriptions)
  - missing_tasks: [string] (gaps in task list)
  - risks: [string] (identified concerns)
  - recommendations: [string] (suggestions for improvement)
  - created_at: timestamp
  - created_by: string
  - operation_id: string (FK to WebSocketSession, for tracing)

Constraints:
  - completeness_score 0-100
  - risk_level derived from missing_tasks + risks count
  - Immutable after creation (snapshot of analysis)

Relationships:
  - AnalysisResult → Feature (N:1)
  - AnalysisResult → Task (N:1)
  - AnalysisResult → WebSocketSession (N:1)
```

**Storage** (Phase 1): In-memory during session  
**Storage** (Phase 2): PostgreSQL audit table

### 11. WebSocketSession

**Purpose**: Track real-time operation sessions (clarify, analyze, plan generation)

```yaml
Entity: WebSocketSession
Identifier: id (UUID)
Attributes:
  - id: UUID (operation_id)
  - feature_id: UUID (FK)
  - operation_type: enum ('clarify'|'analyze'|'plan'|'task'|'impl')
  - status: enum ('running'|'completed'|'failed'|'interrupted')
  - started_at: timestamp
  - completed_at: timestamp (null if running)
  - started_by: string (github_username)
  - input_spec_version: integer (spec version input to operation)
  - output_content: string (generated content, if successful)
  - error_message: string (if failed)
  - message_count: integer (total WebSocket messages sent)

Constraints:
  - Operation runs for max 5 minutes (timeout)
  - Message history retention: 5-10 min per operation

Relationships:
  - WebSocketSession → Feature (N:1)
  - WebSocketSession → WebSocketMessage (1:many)
  - WebSocketSession → AnalysisResult (1:1, optional, if operation_type='analyze')
```

**Storage** (Phase 1): In-memory (cleared on restart)  
**Storage** (Phase 2): PostgreSQL + Redis message queue

### 12. WebSocketMessage

**Purpose**: Individual real-time message from Copilot CLI execution

```yaml
Entity: WebSocketMessage
Identifier: id (UUID)
Attributes:
  - id: UUID
  - operation_id: UUID (FK to WebSocketSession)
  - sequence: integer (message ordering, starts at 0)
  - type: enum ('thinking'|'execution'|'error'|'complete')
  - content: string (message text)
  - timestamp: ISO8601 (when message generated)
  - sender: enum ('copilot'|'system'|'user')

Constraints:
  - content max 10KB (prevents memory exhaustion)
  - sequence auto-increments per operation_id
  - type 'complete' marks last message
  - timestamp is server-side (not client clock)

Relationships:
  - WebSocketMessage → WebSocketSession (N:1)
```

**Message Examples**:
```json
{
  "id": "msg_001",
  "operation_id": "op_abc123",
  "sequence": 0,
  "type": "thinking",
  "content": "Analyzing specification for ambiguities...",
  "timestamp": "2026-02-18T14:23:45Z",
  "sender": "copilot"
}

{
  "sequence": 1,
  "type": "thinking",
  "content": "User story 1 lacks acceptance criteria. Generating clarification question...",
  "timestamp": "2026-02-18T14:23:47Z"
}

{
  "sequence": 2,
  "type": "execution",
  "content": "Q1: For 'User Story 1 - Repository Selection', what is the maximum number of repos a user should be able to filter through?",
  "timestamp": "2026-02-18T14:23:48Z"
}

{
  "sequence": 3,
  "type": "complete",
  "content": "Clarification complete. 3 questions generated.",
  "timestamp": "2026-02-18T14:23:50Z"
}
```

**Storage** (Phase 1): In-memory + sent to connected WebSocket clients  
**Storage** (Phase 2): Redis stream for durability

---

## Relationships & Cardinality

### Entity Relationship Diagram (Text Format)

```
User (1) ──┬──────── (N) AuthSession
           │
           └──────── (N) Feature
                     (created_by)

Repository (1) ────────── (N) Feature
                (referenced_by)

Feature (1) ────┬────── (1) Spec
                ├────── (1) Plan  
                ├────── (1) Task
                ├────── (1) AnalysisResult
                └────── (N) WebSocketSession
                       (for clarify/analyze ops)

Spec (1) ────────── (N) Clarification
         (version questions)

WebSocketSession (1) ────────── (N) WebSocketMessage
                    (message stream)
```

### Key Constraints

| Constraint | Rule | Rationale |
|-----------|------|-----------|
| **1:1 (Spec, Plan, Task per Feature)** | Each feature has max 1 spec content, plan content, task content | Simplifies workflow; new versions update same entity, not create new |
| **N:1 (Feature per Repo)** | Multiple features per repo allowed | Single repo, multiple features (e.g., auth, payment, api) |
| **Spec→Plan→Task Ordering** | Plan version refs spec version; Task version refs plan version | Enables re-generation detection; deferred plan/task if spec updated |
| **Message History per Operation** | Server retains 5-10 min of messages per operation_id | Enables WebSocket reconnection replay without loss |
| **Token Never Persisted** | AuthSession stores only token_hash, never plaintext token | Security; prevents credential exposure |

---

## State Machines

### Feature Lifecycle

```
Create Feature
    ↓
[draft] ←→ [in-progress] → [completed] → [archived]
    ↑           ↓
    └─ Modify Spec, Plan, Task
```

### Spec Lifecycle

```
Not Exist
    ↓
Generate from Template
    ↓
[draft] → Edit Content → [in-progress] → Clarify → [clarified] → Done
           (user edits)    (content chg)  (Q&A)     (integrated)
```

### WebSocketSession Lifecycle

```
User triggers Clarify/Analyze/Plan
    ↓
[running] ← Streaming messages via WebSocket
    ↓
Copilot CLI completes
    ↓
[completed] → Persist updated document to GitHub
              [failed] - if error occurred
              [interrupted] - if user disconnected
```

---

## Validation Rules

### Spec Content

- ✅ Must be valid Markdown
- ✅ Must contain at least one user story
- ✅ Must have acceptance criteria for each requirement
- ✅ Max 100KB (file size limit)

### Plan Content

- ✅ Must be valid Markdown
- ✅ Must reference spec version it came from
- ✅ Must contain task breakdown or timeline
- ✅ Max 100KB

### Task Content

- ✅ Must be valid Markdown
- ✅ Must reference plan version it came from
- ✅ Should contain effort estimates (t-shirt sizing or hours)
- ✅ Max 200KB (tasks often larger)

### GitHub Branch Names

- ✅ Must follow Git ref naming (no spaces, special chars)
- ✅ Common pattern: `feature/{name}`, `bugfix/{name}`
- ✅ Max 255 characters
- ✅ Cannot contain `..` or end with `.lock`

---

## Migration Strategy (if needed)

**Phase 1 to Phase 2**: 
- Features stored in-memory → PostgreSQL `features` table
- AuthSession in-memory → Redis with PostgreSQL audit log
- WebSocket messages in-memory → Redis stream + PostgreSQL snapshots
- No data loss; add migrations script to sync existing sessions

---

## Conclusion

This data model provides a clean separation of concerns:
- **Immutable GitHub State**: Repository, Branch (authoritative, cached)
- **Mutable User Content**: Spec, Plan, Task (versioned, audit-trailed)
- **Session State**: AuthSession, WebSocketSession (temporary, in-memory)
- **Analysis Results**: AnalysisResult (snapshot, time-bounded)

All entities designed for Phase 1 MVP simplicity with Phase 2 persistence growth path.

