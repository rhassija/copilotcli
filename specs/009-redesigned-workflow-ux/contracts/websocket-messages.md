# API Contract: WebSocket Message Protocol

**Phase**: Phase 1 Design  
**Date**: February 18, 2026  
**Status**: ✅ Complete

---

## Overview

This document specifies the WebSocket protocol for real-time streaming of Copilot CLI execution and LLM thinking.

**Protocol**: WebSocket (RFC 6455) over HTTPS/WSS  
**Base URI**: `wss://api.example.com/ws` (production) or `ws://localhost:8000/ws` (development)  
**Message Format**: JSON UTF-8 encoded  
**Connection Timeout**: 5 minutes (user inactivity or operation completion)

---

## Connection Lifecycle

### 1. Client Initiates Connection

**URL**:
```
wss://api.example.com/ws?operation_id=op_abc123&session_id=sess_def456
```

**Query Parameters**:
- `operation_id` (required): UUID of the operation (clarify, analyze, plan)
- `session_id` (required): Browser session identifier
- `last_received_sequence` (optional): For reconnection, last message sequence received

**Headers**:
```
GET /ws?operation_id=op_abc123 HTTP/1.1
Host: api.example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
Authorization: Bearer ghp_xxxx (if token validation needed)
```

---

### 2. Server Accepts Connection

**Response**:
```
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYrb9TYG37K4xE=
```

**Initial Message**:
```json
{
  "type": "system",
  "content": "Connected to operation op_abc123",
  "timestamp": "2026-02-18T14:23:45Z",
  "sequence": -1,
  "operation_id": "op_abc123"
}
```

---

### 3. Server Streams Messages

Backend sends messages as Copilot CLI subprocess generates output.

**Message Flow**:
```
Client connects
    ↓
Server: Send system "Connected" message
    ↓
[For each line from Copilot CLI subprocess]:
  Parse line
  Create WebSocket message
  Send to client
    ↓
[Loop until process exits]
    ↓
Server: Send "complete" message
    ↓
Close WebSocket (or allow client close)
```

---

### 4. Client Closes Connection

**Client sends**:
```
Connection: close
Sec-WebSocket-Close: 1000 (normal closure)
```

**Server responds**:
```
Sec-WebSocket-Close: 1000
```

**Server action**: 
- Stops streaming
- Completes any in-flight operation (persists to GitHub)
- Cleans up WebSocket session resources

---

## Message Format

### Full Message Structure

```json
{
  "id": "msg_001",
  "operation_id": "op_abc123",
  "sequence": 0,
  "type": "thinking|execution|error|complete|system",
  "content": "Message text content...",
  "timestamp": "2026-02-18T14:23:45.123Z",
  "sender": "copilot|system",
  "metadata": {
    "subsection": "optional subsection identifier",
    "priority": "normal|high|low"
  }
}
```

### Field Definitions

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | UUID string | Yes | Unique message ID within operation |
| `operation_id` | UUID string | Yes | Operation this message belongs to |
| `sequence` | integer | Yes | Ordering index (0, 1, 2, ...) |
| `type` | enum | Yes | Message category (see below) |
| `content` | string | Yes | Message text; max 10KB |
| `timestamp` | ISO8601 | Yes | When server generated message (UTC) |
| `sender` | enum | Yes | 'copilot' (CLI output), 'system' (server) |
| `metadata` | object | No | Optional context (subsection, priority) |

### Message Types

#### Type: `thinking`

LLM reasoning/analysis step. User can expand/collapse for readability.

**Example**:
```json
{
  "sequence": 0,
  "type": "thinking",
  "content": "Analyzing specification document for ambiguities and missing requirements...",
  "timestamp": "2026-02-18T14:23:46.100Z",
  "sender": "copilot"
}
```

**UI Rendering**: 
- Collapsible section (closed by default)
- Gray background or indented text
- Icon: 💭 (thinking emoji)

---

#### Type: `execution`

Action or result. Important to user; always visible.

**Example**:
```json
{
  "sequence": 3,
  "type": "execution",
  "content": "Generated 5 clarification questions based on specification gaps.",
  "timestamp": "2026-02-18T14:23:50.200Z",
  "sender": "copilot"
}
```

**UI Rendering**:
- Always visible (not collapsible)
- Icon: ⚙️ (action emoji)

---

#### Type: `error`

Error or warning. Highlighted for user attention.

**Example**:
```json
{
  "sequence": 1,
  "type": "error",
  "content": "User Story 1 lacks acceptance criteria. Copilot will generate clarification question.",
  "timestamp": "2026-02-18T14:23:47.500Z",
  "sender": "copilot",
  "metadata": {
    "priority": "high"
  }
}
```

**UI Rendering**:
- Red or orange background
- Icon: ⚠️ (warning emoji)
- Always visible

---

#### Type: `complete`

Operation finished. Final message.

**Example**:
```json
{
  "sequence": 8,
  "type": "complete",
  "content": "Clarification complete. 5 questions generated. Spec ready for review.",
  "timestamp": "2026-02-18T14:23:55.800Z",
  "sender": "system"
}
```

**UI Rendering**:
- Green background or checkmark icon
- Indicates WebSocket will close after this message (in 1-2 seconds)

---

#### Type: `system`

Server-generated system message (connection, reconnection, stats).

**Example**:
```json
{
  "sequence": -1,
  "type": "system",
  "content": "Reconnected. Replaying 3 missed messages...",
  "timestamp": "2026-02-18T14:23:45.000Z",
  "sender": "system"
}
```

**UI Rendering**:
- Gray text, smaller font
- Optional (may not show in UI)

---

## Message Examples by Operation

### Operation: Clarify Specification

```json
[
  {
    "id": "msg_001",
    "operation_id": "op_clarify_123",
    "sequence": 0,
    "type": "thinking",
    "content": "Reading specification document...",
    "timestamp": "2026-02-18T14:23:46Z"
  },
  {
    "sequence": 1,
    "type": "thinking",
    "content": "Identified 3 areas with potential ambiguity:\n1. User Story 1: 'accessible repositories' is vague\n2. FR-AUTH-001: Missing token scope details\n3. FR-WS-002: Unclear message buffering strategy",
    "timestamp": "2026-02-18T14:23:47Z"
  },
  {
    "sequence": 2,
    "type": "execution",
    "content": "Generating clarification question 1 of 3...",
    "timestamp": "2026-02-18T14:23:48Z"
  },
  {
    "sequence": 3,
    "type": "execution",
    "content": "Q1: In User Story 1, when you say 'accessible repositories', do you mean:\n  A) Repositories owned by the user\n  B) Repositories the user has contributed to\n  C) Repositories shared within the organization\n  D) All of the above\n\nContext: This affects the GitHub API query strategy and filtering logic.",
    "timestamp": "2026-02-18T14:23:49Z"
  },
  {
    "sequence": 4,
    "type": "execution",
    "content": "Q2: For GitHub token scopes, should the app request...",
    "timestamp": "2026-02-18T14:23:50Z"
  },
  {
    "sequence": 5,
    "type": "execution",
    "content": "Q3: For WebSocket message buffering during high volume, what is acceptable latency?",
    "timestamp": "2026-02-18T14:23:51Z"
  },
  {
    "sequence": 6,
    "type": "complete",
    "content": "Clarification questions generated. Please review and respond in the conversation panel below.",
    "timestamp": "2026-02-18T14:23:52Z"
  }
]
```

### Operation: Analyze Task Breakdown

```json
[
  {
    "sequence": 0,
    "type": "thinking",
    "content": "Parsing task document...",
    "timestamp": "2026-02-18T14:24:00Z"
  },
  {
    "sequence": 1,
    "type": "thinking",
    "content": "Found 12 tasks. Checking for dependencies and risks...",
    "timestamp": "2026-02-18T14:24:01Z"
  },
  {
    "sequence": 2,
    "type": "execution",
    "content": "Analysis Results:\n- Completeness Score: 85/100\n- Risk Level: MEDIUM\n- Identified Circular Dependencies: None\n- Missing Tasks Detected: 2 (error handling, end-to-end testing)",
    "timestamp": "2026-02-18T14:24:05Z"
  },
  {
    "sequence": 3,
    "type": "error",
    "content": "WARNING: Tasks 3 and 7 have no effort estimate. Recommend T-shirt sizing (S/M/L) or story points.",
    "timestamp": "2026-02-18T14:24:06Z"
  },
  {
    "sequence": 4,
    "type": "execution",
    "content": "Recommended additions:\n1. 'Error Handling & Recovery' task (depends on Core API)\n2. 'Integration Testing Suite' task (depends on all feature tasks)",
    "timestamp": "2026-02-18T14:24:07Z"
  },
  {
    "sequence": 5,
    "type": "complete",
    "content": "Analysis complete. Review recommendations above and update task.md if needed.",
    "timestamp": "2026-02-18T14:24:08Z"
  }
]
```

---

## Reconnection Handling

### Scenario: Network Drop During Operation

**Step 1: Connection Lost**
```
Client WebSocket closes unexpectedly (network glitch, etc.)
Backend: Keeps operation running, maintains message history
```

**Step 2: Client Detects & Reconnects**
```
Client code detects WebSocket close event.
After 1-2 second backoff, client reconnects:

wss://api.example.com/ws?operation_id=op_abc123
                          &session_id=sess_def456
                          &last_received_sequence=5
```

**Step 3: Server Replays Missed Messages**
```
Server receives reconnection with last_received_sequence=5.
Server: Looks up operation history for op_abc123 (retained 5-10 min).
Server: Sends missed messages 6, 7, 8, ... to client.
Server: Resumes streaming any new messages from Copilot CLI.
```

**Example Replay Message**:
```json
{
  "sequence": -2,
  "type": "system",
  "content": "Reconnected. Replaying 2 missed messages (6-7)...",
  "timestamp": "2026-02-18T14:23:55Z",
  "sender": "system"
}
```

**Client UI Impact**:
- Brief "disconnected" indicator
- Auto-reconnect message
- Continued message stream resumes seamlessly

---

## Message Ordering Guarantees

**Sequence Number**: Strictly increasing integer (0, 1, 2, ...)

**Guarantees**:
- ✅ Within single connection: Sequential (1, 2, 3, ...)
- ✅ After reconnection: Replay from last_received_sequence + 1
- ✅ No gaps (except during disconnect, which replays)
- ✅ No duplicates (if client stores by sequence + operation_id)

**Client Logic**:
```javascript
// Track last received sequence to handle reconnects
let lastSequence = -1;

websocket.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  
  if (msg.sequence <= lastSequence) {
    // Duplicate or out-of-order; ignore
    console.warn(`Duplicate/OOO message: seq=${msg.sequence}, lastSeq=${lastSequence}`);
    return;
  }
  
  lastSequence = msg.sequence;
  renderMessage(msg); // Display to user
};
```

---

## Performance & Backpressure

### Message Rate

**Typical rate**: 1-5 messages per second  
**Peak rate**: Up to 20 messages/sec (aggressive Copilot CLI output)

### Backpressure Problem

What if backend generates 1000 messages/sec but network can only send 10?

**Solution**:
- Backend queues messages if sending slower than generation
- Queue max size: 100 messages (5 KB each) = ~500 KB
- If queue fills: Backend drops oldest "thinking" messages first (preserves "execution" and "error")
- Client never sees dropped thinking (resumed from latest state)

### Compression

**Optional**: Server may enable WebSocket permessage-deflate compression for large messages (> 1 KB).

---

## Error Handling

### Network Errors

**Client timeout (> 30 sec no message)**:
```javascript
setTimeout(() => {
  if (lastSequence < expectedSequence) {
    // Timeout; close and reconnect
    websocket.close(1000, 'Timeout waiting for messages');
  }
}, 30000);
```

**Server timeout (client silent > 5 min)**:
```python
# Backend: If no new messages from Copilot CLI for 5 min, send ping
if time.time() - last_copilot_message > 300:
  ws.send({type: 'system', content: 'Alive check...'})
```

### Operation Failures

**Copilot CLI crashes**:
```json
{
  "sequence": 5,
  "type": "error",
  "content": "Copilot CLI process exited with error code 1: 'Authentication failed. Check GITHUB_TOKEN environment variable.'",
  "timestamp": "2026-02-18T14:24:10Z"
}
```

**Backend error**:
```json
{
  "sequence": 6,
  "type": "error",
  "content": "Internal server error: Failed to persist spec to GitHub. Please try again or contact support.",
  "timestamp": "2026-02-18T14:24:11Z"
}
```

**Next message** (after error): 
```json
{
  "sequence": 7,
  "type": "complete",
  "content": "Operation failed. No changes persisted.",
  "timestamp": "2026-02-18T14:24:12Z"
}
```

---

## Scaling Considerations

### Single Operation, Many Clients

Multiple users can listen to same operation via different WebSocket connections.

```
Operation: op_clarify_123 (running)
  ├─ Client A connected
  ├─ Client B connected
  └─ Client C connected

Backend: Broadcasts each message to all connected clients simultaneously.
```

**Implementation**:
```python
# Backend pseudo-code
class WebSocketManager:
  def __init__(self):
    self.connections = {}  # operation_id -> [websocket connections]
  
  def broadcast_message(self, operation_id, message):
    for ws in self.connections.get(operation_id, []):
      await ws.send_json(message)
```

### Message History Retention

**Duration**: 5-10 minutes per operation_id  
**Storage**: Redis or in-memory cache  
**Cleanup**: Manual expiration or TTL (5 min after operation completes)

---

## Testing & Debugging

### Client-Side Testing

```javascript
// Mock WebSocket for unit tests
class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.messages = [];
  }
  
  send(data) { /* no-op */ }
  close() { /* no-op */ }
  
  // Simulate server messages
  simulateMessage(msg) {
    this.onmessage({ data: JSON.stringify(msg) });
  }
}

// Test reconnection
test('Reconnect replays missed messages', () => {
  const ws = new MockWebSocket(...);
  
  // Simulate initial messages
  ws.simulateMessage({sequence: 0, ...});
  ws.simulateMessage({sequence: 1, ...});
  
  // Simulate disconnect + reconnect
  ws.close();
  ws.onopen(); // New connection
  
  // Server should replay messages 2+
  ws.simulateMessage({sequence: -2, type: 'system', content: 'Replaying...'});
  ws.simulateMessage({sequence: 2, ...});
});
```

### Server-Side Testing

```python
# Backend: pytest fixture
@pytest.fixture
async def ws_client(app):
  async with AsyncClient(app, base_url="ws://localhost") as client:
    with client.websocket_connect("/ws?operation_id=op_test_123") as ws:
      yield ws

@pytest.mark.asyncio
async def test_message_ordering(ws_client):
  # Send 10 messages
  for i in range(10):
    msg = await ws_client.receive_json()
    assert msg['sequence'] == i
```

---

## Security

### Token Validation

- WebSocket URL should NOT include token (query params logged)
- Instead: Validate Authorization header or session_id during handshake
- Session_id must be created during initial POST /auth/verify

### Message Injection Prevention

- All messages generated by backend only
- No user input reflected in messages
- Sanitize Copilot CLI output before broadcasting

### Rate Limiting Per Client

- Max 1000 messages per operation (prevents memory DoS)
- Max 100 concurrent WebSocket connections per user session
- Enforce via middleware

---

## Conclusion

WebSocket protocol provides low-latency, real-time streaming of Copilot CLI execution with robust reconnection and message replay. Supports 5-10 concurrent users with 2-3 concurrent operations per user during Phase 1.

