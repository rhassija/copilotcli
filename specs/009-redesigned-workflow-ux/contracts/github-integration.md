# API Contract: GitHub Integration

**Phase**: Phase 1 Design  
**Date**: February 18, 2026  
**Status**: ✅ Complete

---

## Overview

This document specifies all REST API endpoints for GitHub repository access and document operations. All endpoints require `Authorization: Bearer {github_token}` header.

**Base URL**: `/api/v1`  
**Protocol**: HTTPS only (HTTP for localhost development)  
**Rate Limit**: GitHub API 1000 requests/hour per token

---

## Authentication Endpoints

### POST /auth/verify

Validate GitHub token and retrieve user info.

**Request**:
```json
{
  "token": "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "scopes": ["repo", "workflow"]
}
```

**Response**: 200 OK
```json
{
  "valid": true,
  "user": {
    "login": "rajesh-hassija",
    "id": 12345678,
    "name": "Rajesh Hassija",
    "avatar_url": "https://avatars.githubusercontent.com/u/12345678?v=4",
    "email": "rajesh@example.com"
  },
  "scopes_granted": ["repo", "workflow"],
  "token_expires_at": "2027-02-18T14:23:45Z"
}
```

**Response**: 401 Unauthorized
```json
{
  "valid": false,
  "error": "Invalid token or insufficient scopes",
  "required_scopes": ["repo", "workflow"]
}
```

**Errors**:
- `400 Bad Request`: Malformed token or missing payload
- `401 Unauthorized`: Invalid/expired token or insufficient scopes
- `403 Forbidden`: Token has been revoked
- `429 Too Many Requests`: Rate limited (retry after header present)

---

### POST /auth/logout

Clear session and invalidate token.

**Request**:
```json
{
  "session_id": "sess_abc123"
}
```

**Response**: 200 OK
```json
{
  "success": true,
  "message": "Session cleared"
}
```

---

## Repository Access Endpoints

### GET /repos

List all accessible GitHub repositories.

**Query Parameters**:
- `search` (string, optional): Filter repos by name/owner (case-insensitive substring)
- `type` (string, optional): 'all' (default), 'owner', 'member', 'org', 'forks'
- `sort` (string, optional): 'updated' (default), 'created', 'pushed', 'stars'
- `limit` (integer, default: 30): Max 100 results per request
- `offset` (integer, default: 0): Pagination offset

**Request**:
```
GET /repos?search=copilot&type=owner&sort=updated&limit=30&offset=0
Authorization: Bearer ghp_xxxx
```

**Response**: 200 OK
```json
{
  "repositories": [
    {
      "id": "MDEwOlJlcG9zaXRvcnk=",
      "owner": "rajesh-hassija",
      "name": "copilotcli",
      "full_name": "rajesh-hassija/copilotcli",
      "description": "AI-powered CLI for software development",
      "url": "https://github.com/rajesh-hassija/copilotcli",
      "is_private": false,
      "is_fork": false,
      "stars": 42,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2026-02-18T14:23:45Z",
      "default_branch": "main"
    }
  ],
  "total": 15,
  "limit": 30,
  "offset": 0,
  "pagination": {
    "has_next": false,
    "has_previous": false
  }
}
```

**Caching**: Cache results for 5 minutes per token (include Cache-Control headers)

**Errors**:
- `401 Unauthorized`: Token invalid/expired
- `429 Too Many Requests`: GitHub rate limit exceeded (include Retry-After)

---

### GET /repos/{owner}/{repo}/branches

List branches in a repository.

**Path Parameters**:
- `owner` (string): Repository owner
- `repo` (string): Repository name

**Query Parameters**:
- `protected` (boolean, optional): Return only protected branches
- `limit` (integer, default: 50): Max 100
- `offset` (integer, default: 0): Pagination

**Request**:
```
GET /repos/rajesh-hassija/copilotcli/branches
Authorization: Bearer ghp_xxxx
```

**Response**: 200 OK
```json
{
  "branches": [
    {
      "name": "main",
      "commit": {
        "sha": "abc123def456",
        "url": "https://api.github.com/repos/rajesh-hassija/copilotcli/commits/abc123def456"
      },
      "protected": true,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2026-02-18T14:23:45Z"
    },
    {
      "name": "feature/user-auth",
      "commit": {
        "sha": "xyz789abc123",
        "url": "https://api.github.com/repos/rajesh-hassija/copilotcli/commits/xyz789abc123"
      },
      "protected": false,
      "created_at": "2026-02-15T10:00:00Z",
      "updated_at": "2026-02-18T13:45:00Z"
    }
  ],
  "total": 5,
  "limit": 50,
  "offset": 0
}
```

**Errors**:
- `401 Unauthorized`: Token invalid
- `403 Forbidden`: User lacks access to repo
- `404 Not Found`: Repo doesn't exist

---

### POST /repos/{owner}/{repo}/branches

Create a new feature branch (via Copilot CLI subprocess).

**Path Parameters**:
- `owner` (string): Repository owner
- `repo` (string): Repository name

**Request**:
```json
{
  "branch_name": "feature/user-auth",
  "source_branch": "main"
}
```

**Response**: 201 Created
```json
{
  "branch": {
    "name": "feature/user-auth",
    "commit": {
      "sha": "xyz789abc123",
      "url": "https://api.github.com/repos/rajesh-hassija/copilotcli/commits/xyz789abc123"
    }
  },
  "spec_path": "specs/001-user-auth/spec.md",
  "created_at": "2026-02-18T14:23:45Z"
}
```

**Errors**:
- `400 Bad Request`: Invalid branch name or conflict with existing branch
- `403 Forbidden`: User lacks write access
- `409 Conflict`: Branch already exists

---

## Document Operations Endpoints

### GET /features/{feature_id}/spec

Fetch specification document.

**Path Parameters**:
- `feature_id` (string): Feature UUID

**Request**:
```
GET /features/feat_abc123/spec
Authorization: Bearer ghp_xxxx
```

**Response**: 200 OK
```json
{
  "spec": {
    "id": "spec_def789",
    "feature_id": "feat_abc123",
    "content": "# Feature Specification\n\n## Overview\n...",
    "version": 2,
    "created_at": "2026-02-15T10:00:00Z",
    "updated_at": "2026-02-18T14:23:45Z",
    "created_by": "rajesh-hassija",
    "updated_by": "rajesh-hassija",
    "github_path": "specs/001-user-auth/spec.md",
    "github_sha": "abc123def456"
  }
}
```

**Response**: 404 Not Found (document doesn't exist yet)
```json
{
  "error": "spec_not_found",
  "message": "No specification found for this feature. Create one to proceed.",
  "create_url": "/api/v1/features/feat_abc123/spec/create"
}
```

---

### PUT /features/{feature_id}/spec

Update specification document.

**Path Parameters**:
- `feature_id` (string): Feature UUID

**Request**:
```json
{
  "content": "# Updated Feature Specification\n\n...",
  "if_match": "abc123def456"
}
```

**Note**: `if_match` is optional; if provided, server validates against github_sha for optimistic locking.

**Response**: 200 OK
```json
{
  "spec": {
    "id": "spec_def789",
    "version": 3,
    "updated_at": "2026-02-18T14:25:00Z",
    "github_sha": "xyz789abc123"
  }
}
```

**Errors**:
- `400 Bad Request`: Invalid markdown or content too large (>100KB)
- `409 Conflict`: GitHub SHA mismatch (branch moved; user must refresh)
- `412 Precondition Failed`: if_match doesn't match current SHA

**Side Effects**:
- Increments spec.version
- Pushes to GitHub repository immediately
- Returns new github_sha for client caching

---

### POST /features/{feature_id}/plan

Create plan document via Copilot CLI.

**Path Parameters**:
- `feature_id` (string): Feature UUID

**Request**:
```json
{
  "from_spec_version": 2,
  "template": "default"
}
```

**Response**: 202 Accepted (async operation)
```json
{
  "operation_id": "op_ghi012",
  "status": "running",
  "message": "Plan generation started. Connect to WebSocket for real-time updates.",
  "websocket_url": "wss://api.example.com/ws?operation_id=op_ghi012",
  "estimated_duration_seconds": 45
}
```

**Errors**:
- `400 Bad Request`: Spec doesn't exist or invalid version
- `409 Conflict`: Plan already exists (use PUT to update)

**Backend Behavior**:
- Spawns Copilot CLI subprocess: `copilot plan --spec-file {spec.md} --from-branch main`
- Streams output via WebSocket (operation_id: op_ghi012)
- On completion: creates/updates plan.md in GitHub repo
- Client receives `type: 'complete'` WebSocket message with status

---

### PUT /features/{feature_id}/plan

Update plan document (manual edit).

**Path Parameters**:
- `feature_id` (string): Feature UUID

**Request**:
```json
{
  "content": "# Updated Implementation Plan\n\n...",
  "if_match": "xyz789abc123"
}
```

**Response**: 200 OK
```json
{
  "plan": {
    "id": "plan_jkl345",
    "version": 2,
    "updated_at": "2026-02-18T14:30:00Z",
    "github_sha": "new_sha_12345"
  }
}
```

---

### GET /features/{feature_id}/task

Fetch task document.

**Response**: 200 OK (if exists) or 404 Not Found (if not created yet)

**Format**: Same as Spec operations

---

### PUT /features/{feature_id}/task

Update task document (manual edit).

**Request**:
```json
{
  "content": "# Implementation Tasks\n\n...",
  "if_match": "current_sha"
}
```

**Response**: 200 OK

---

### POST /features/{feature_id}/analyze

Analyze task breakdown for completeness and risks (via Copilot CLI).

**Path Parameters**:
- `feature_id` (string): Feature UUID

**Request**:
```json
{
  "from_task_version": 1
}
```

**Response**: 202 Accepted (async operation)
```json
{
  "operation_id": "op_mno678",
  "status": "running",
  "message": "Analysis in progress. Connect to WebSocket for results.",
  "websocket_url": "wss://api.example.com/ws?operation_id=op_mno678",
  "estimated_duration_seconds": 30
}
```

**Backend Behavior**:
- Spawns Copilot CLI: `copilot analyze --task-file {task.md}`
- Streams analysis thinking + results via WebSocket
- On completion: stores AnalysisResult snapshot (not persisted to GitHub)

---

## WebSocket Events

### WebSocket /ws

Connect to real-time operation stream.

**URI**: `wss://api.example.com/ws?operation_id={operation_id}&session_id={session_id}`

**Connection Handshake**:
```json
{
  "type": "system",
  "content": "Connected to operation op_ghi012. Waiting for results...",
  "timestamp": "2026-02-18T14:23:45Z"
}
```

**Message Stream** (from backend as Copilot CLI processes):
```json
[
  {
    "id": "msg_001",
    "operation_id": "op_ghi012",
    "sequence": 0,
    "type": "thinking",
    "content": "Analyzing specification for implementation approach...",
    "timestamp": "2026-02-18T14:23:46Z"
  },
  {
    "sequence": 1,
    "type": "thinking",
    "content": "Identified 5 core components needed for this feature.",
    "timestamp": "2026-02-18T14:23:48Z"
  },
  {
    "sequence": 2,
    "type": "execution",
    "content": "Creating implementation plan with task breakdown...",
    "timestamp": "2026-02-18T14:23:50Z"
  },
  {
    "sequence": 3,
    "type": "complete",
    "content": "Plan generated successfully. 12 tasks created.",
    "timestamp": "2026-02-18T14:23:55Z"
  }
]
```

**Reconnection on Drop**:
```
Client discovers connection closed.
Client reconnects: wss://.../ws?operation_id=op_ghi012&last_sequence=2
Server sends: Messages 3, 4, ... (replay from last_sequence + 1)
```

**Client Close**:
```
Client closes WebSocket (browser tab closed, user navigated away)
Server: Cleans up WebSocket session, but keeps operation running
Operation completes: Results persisted to GitHub even if client not connected
```

---

## Error Responses (Standard)

All errors follow format:

```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable message",
    "details": ["Additional context if available"],
    "request_id": "req_xyz123"
  },
  "timestamp": "2026-02-18T14:23:45Z"
}
```

### Common HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | GET successful |
| 201 | Created | Branch creation successful |
| 202 | Accepted | Async operation started |
| 400 | Bad Request | Invalid branch name |
| 401 | Unauthorized | Invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Document doesn't exist |
| 409 | Conflict | Branch already exists |
| 429 | Too Many Requests | GitHub API rate limit exceeded |
| 500 | Internal Server Error | Backend error (rare) |

---

## Rate Limiting & Retry Strategy

**GitHub API Limit**: 1000 requests/hour per token

**Recommendation**:
- Frontend caches repository list for 5 minutes
- Batch file operations when possible
- Implement exponential backoff on 429 responses
- Display user-friendly message: "Approaching API rate limit. Please wait 10 minutes before next operation."

**Retry Logic**:
```
if response.status == 429:
  retry_after = int(response.headers['Retry-After'])
  wait(retry_after seconds)
  retry()
```

---

## Examples

### Example 1: Full Workflow

```
1. POST /auth/verify
   → Token validated, user identified

2. GET /repos?search=copilot&limit=10
   → List repos; 3 matching results

3. GET /repos/rajesh-hassija/copilotcli/branches
   → List branches; "main" + 2 feature branches

4. POST /repos/rajesh-hassija/copilotcli/branches
   → Create feature/user-auth; Copilot CLI creates branch + initializes spec.md

5. WebSocket /ws?operation_id=op_ghi012
   → Receive real-time messages as plan generates

6. PUT /features/{id}/task
   → User manually edits tasks

7. POST /features/{id}/analyze
   → WebSocket streams analysis result
```

### Example 2: Error Handling (Rate Limit)

```
Client: POST /repos/.../branches
Response: 429 Too Many Requests
Header: Retry-After: 3600

Client: Display message "You've used 1000/1000 GitHub API requests this hour. Retry after 1 hour."
```

---

## Versioning

**Current Version**: v1  
**Base Path**: `/api/v1`

Future versions (`/api/v2`) will be created only for breaking changes; minor features will extend v1.

