# Architecture Guide - Copilot CLI Web UI

This document provides a deep technical dive into the system architecture, design patterns, and implementation details for the Copilot CLI web application.

## Table of Contents

1. [System Design](#system-design)
2. [Backend Architecture](#backend-architecture)
3. [Frontend Architecture](#frontend-architecture)
4. [WebSocket Communication](#websocket-communication)
5. [Authentication & Security](#authentication--security)
6. [Data Models](#data-models)
7. [Key Patterns & Best Practices](#key-patterns--best-practices)
8. [Error Handling & Recovery](#error-handling--recovery)

## System Design

### Architecture Pattern

The system follows a **client-server architecture** with **event-driven WebSocket messaging** for real-time updates:

```
┌──────────────────────────────────────┐
│      React Frontend (Port 3000)      │
│  ┌──────────────────────────────────┐│
│  │ Pages + Components + React Hooks ││
│  │ (State management via React)     ││
│  └──────────────────────────────────┘│
│  ┌──────────────────────────────────┐│
│  │ Services (API, WebSocket, Auth)  ││
│  └──────────────────────────────────┘│
└──────────────────────────────────────┘
              ↕ HTTP + WebSocket
              (localhost:8001)
┌──────────────────────────────────────┐
│      FastAPI Backend (Port 8001)     │
│  ┌──────────────────────────────────┐│
│  │ API Routes + WebSocket Handler   ││
│  └──────────────────────────────────┘│
│  ┌──────────────────────────────────┐│
│  │ Services (Auth, Doc Gen, GitHub) ││
│  └──────────────────────────────────┘│
│  ┌──────────────────────────────────┐│
│  │ WebSocket Manager + Message Queue││
│  └──────────────────────────────────┘│
└──────────────────────────────────────┘
         ↓ Subprocess + API calls
    ┌─────────────────────────────────┐
    │   Copilot CLI + GitHub API      │
    └─────────────────────────────────┘
```

### Design Principles

1. **Separation of Concerns**: API layer ↔ Service layer ↔ Data models
2. **Real-time Communication**: WebSocket for streaming, HTTP for state changes
3. **Async-First**: All I/O operations are async to prevent blocking
4. **Fault Tolerance**: Auto-reconnect, message replay, error boundaries
5. **Type Safety**: Full TypeScript frontend, Pydantic models backend

---

## Backend Architecture

### FastAPI Application Structure

```python
# backend/src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import auth, documents, features, repositories, websocket
from src.services.websocket_manager import WebSocketManager

app = FastAPI()

# Global WebSocket connection manager
ws_manager = WebSocketManager()

# CORS for localhost development
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", ...])

# Include routers
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(features.router)
app.include_router(repositories.router)
app.include_router(websocket.router)
```

### Layer Architecture

#### 1. API Layer (`src/api/`)

Each module handles a specific domain:

**auth.py** - Authentication endpoints
```python
POST /api/v1/auth/github       # GitHub PAT authentication
POST /api/v1/auth/logout       # Clear session
GET  /api/v1/auth/session      # Get current user info
```

**documents.py** - Document generation endpoints
```python
POST /api/v1/features/{id}/generate-spec    # Generate specification
POST /api/v1/features/{id}/generate-plan    # Generate plan  
POST /api/v1/features/{id}/generate-task    # Generate task
```

Key implementation detail - **async generation with WebSocket emission**:

```python
@router.post("/api/v1/features/{feature_id}/generate-spec", response_model=DocumentResponse)
async def generate_spec(feature_id: str, request: SpecGenerationRequest):
    """Generate specification with real-time WebSocket updates."""
    
    if request.operation_id:
        # Notify WebSocket clients that operation is starting
        await _emit_ws_message(request.operation_id, MessageType.EXECUTION, 
                              "Starting spec generation...")
    
    # Run blocking operation in thread pool to prevent event loop blocking
    await _run_with_progress(request.operation_id, request.sequence, 
                            "Generating specification...", 
                            doc_gen.generate_spec, ...)
    
    if request.operation_id:
        # Notify completion
        await _emit_ws_message(request.operation_id, MessageType.COMPLETE, 
                              "Spec generation complete!")
```

**websocket.py** - WebSocket connection handler
```python
@router.websocket("/api/v1/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Handle WebSocket upgrades and subscriptions."""
    await ws_manager.connect(websocket, session_id)
    # Listen for subscription messages
    while True:
        message = await websocket.receive_json()
        if message["type"] == "subscribe":
            ws_manager.subscribe(session_id, message["operation_id"])
```

#### 2. Service Layer (`src/services/`)

**websocket_manager.py** - Connection and subscription management

```python
class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # session -> operation_ids
        self.message_history: Dict[str, List[WSMessage]] = {}
    
    async def broadcast_to_operation(self, operation_id: str, message: WSMessage):
        """Send message to all clients subscribed to this operation."""
        # Keep last 100 messages for replay
        self.message_history[operation_id].append(message)
        
        # Broadcast to all subscribed connections
        for session_id, operations in self.subscriptions.items():
            if operation_id in operations:
                for connection in self.active_connections[session_id]:
                    await connection.send_json(
                        message.model_dump(mode="json")  # Serialize datetime
                    )
```

**doc_generator.py** - Copilot CLI wrapper

```python
class DocGenerator:
    def __init__(self, cli_path: str, github_token: str):
        self.cli_path = cli_path
        self.github_token = github_token
    
    def generate_spec(self, repo_path: str, feature_name: str, 
                      prompt: str) -> SpecResult:
        """Run Copilot CLI to generate specification."""
        cmd = [
            self.cli_path,
            "scaffold",
            "--repo", repo_path,
            "--feature", feature_name,
            "--prompt", prompt,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return SpecResult(content=result.stdout)
```

**auth_service.py** - Session and authentication

```python
class AuthService:
    def __init__(self):
        self.sessions: Dict[str, SessionData] = {}  # In-memory storage
    
    def create_session(self, github_token: str) -> SessionData:
        """Create new session with GitHub PAT."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = SessionData(
            session_id=session_id,
            github_token=github_token,
            created_at=datetime.now(),
            github_user=self._get_github_user(github_token),
        )
        return self.sessions[session_id]
    
    def validate_session(self, session_id: str) -> bool:
        """Check if session is valid."""
        return session_id in self.sessions
```

#### 3. Data Models (`src/models/`)

Pydantic models for request/response validation:

```python
# src/models/documents.py
from pydantic import BaseModel, Field
from typing import Optional

class SpecGenerationRequest(BaseModel):
    sequence: str
    operation_id: Optional[str] = None
    feature_id: str

class DocumentResponse(BaseModel):
    id: str
    type: str  # "spec", "plan", "task"
    content: str
    created_at: datetime
    updated_at: datetime

# src/models/websocket.py
class MessageType(str, Enum):
    THINKING = "thinking"
    EXECUTION = "execution"
    ERROR = "error"
    COMPLETE = "complete"
    INFO = "info"

class WSMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType
    content: str
    timestamp: datetime
    sender: str = "Copilot CLI"
```

### Key Backend Features

#### Async/Threading Pattern

Document generation uses subprocess (blocking I/O), solved with `asyncio.to_thread`:

```python
async def _run_with_progress(operation_id: str, prompt: str, 
                            status_msg: str, gen_func, *args):
    """Run blocking generation in thread pool."""
    await _emit_ws_message(operation_id, MessageType.EXECUTION, status_msg)
    
    # Run in thread pool - doesn't block event loop
    result = await asyncio.to_thread(gen_func, *args)
    
    return result
```

This allows:
- Multiple generate requests to be handled concurrently
- WebSocket messages to stream while generation is happening
- Frontend to receive updates in real-time

#### CORS Configuration

```python
# Allows frontend to make requests from different ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Frontend Architecture

### Next.js + React Stack

```
next.config.js              # Build & runtime config
├── src/
│   ├── pages/             # Next.js route pages
│   │   ├── index.tsx      # Dashboard
│   │   ├── auth/
│   │   │   └── callback.tsx
│   │   ├── repositories/
│   │   │   ├── [owner]/
│   │   │   │   └── [repo]/
│   │   │   │       └── features/
│   │   │   │           └── [feature]/index.tsx
│   │   │   └── index.tsx
│   │   └── ...
│   ├── components/        # Reusable React components
│   ├── services/          # Client-side services
│   ├── hooks/             # Custom React hooks
│   ├── utils/             # Utility functions
│   ├── types/             # TypeScript type defs
│   ├── styles/            # Global & component styles
│   └── contexts/          # React Context providers
└── public/                # Static assets
```

### State Management

**React Hooks** (not Redux - simpler for this project size):

```typescript
// src/hooks/useDocument.ts
function useDocument(featureId: string, docType: "spec" | "plan" | "task") {
    const [content, setContent] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);
    
    const generateDocument = useCallback(async (prompt: string) => {
        setLoading(true);
        try {
            const response = await apiService.post(
                `/api/v1/features/${featureId}/generate-${docType}`,
                { sequence: prompt, operation_id: generateId() }
            );
            setContent(response.content);
        } catch (err) {
            setError(err as Error);
        } finally {
            setLoading(false);
        }
    }, [featureId]);
    
    return { content, loading, error, generateDocument };
}
```

### Component Architecture

#### ConversationPanel Component

Displays streaming WebSocket messages in real-time:

```typescript
// src/components/ConversationPanel.tsx
interface Message {
    id: string;
    type: MessageType;
    content: string;
    timestamp: Date;
}

export function ConversationPanel({ operationId }: Props) {
    const [messages, setMessages] = useState<Message[]>([]);
    const { subscribe, unsubscribe } = useWebSocket();
    const messagesEndRef = useRef<HTMLDivElement>(null);
    
    useEffect(() => {
        if (!operationId) return;
        
        // Subscribe to operation messages
        const unsubscribeFn = subscribe(operationId, (message: Message) => {
            setMessages(prev => [...prev, message]);
            messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
        });
        
        return unsubscribeFn;
    }, [operationId, subscribe]);
    
    return (
        <div className="fixed bottom-4 right-4 w-96 h-80 bg-white rounded-lg shadow-lg">
            <div className="overflow-auto h-full p-4">
                {messages.map(msg => (
                    <MessageBubble key={msg.id} message={msg} />
                ))}
                <div ref={messagesEndRef} />
            </div>
        </div>
    );
}
```

#### DocumentEditor Component

Handles spec/plan/task editing with generation capability:

```typescript
// src/components/DocumentEditors/DocumentEditor.tsx
export function DocumentEditor({ docType, featureId }: Props) {
    const [operationId, setOperationId] = useState<string>(""); // For WebSocket
    const [showPanel, setShowPanel] = useState(false);
    const { content, loading, generate } = useDocument(featureId, docType);
    
    const handleGenerate = async () => {
        const newOperationId = `${docType}-${featureId}-${Date.now()}`;
        setOperationId(newOperationId);
        setShowPanel(true);
        
        await generate({
            sequence: userPrompt,
            operation_id: newOperationId,  // Pass to backend
        });
    };
    
    return (
        <>
            <div className="editor-container">
                {/* Editor UI */}
                <button onClick={handleGenerate} disabled={loading}>
                    Generate {capitalize(docType)}
                </button>
            </div>
            
            {showPanel && (
                <ConversationPanel operationId={operationId} />
            )}
        </>
    );
}
```

### Service Layer

#### WebSocket Client Service

```typescript
// src/services/websocket.ts
class WebSocketClient {
    private socket: WebSocket | null = null;
    private sessionId: string;
    private messageHandlers: Map<string, Set<MessageHandler>> = new Map();
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    
    connect(): Promise<void> {
        return new Promise((resolve, reject) => {
            const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
            const url = `${protocol}//${window.location.host}/api/v1/ws?session_id=${this.sessionId}`;
            
            this.socket = new WebSocket(url);
            
            this.socket.onopen = () => {
                console.log("WebSocket connected");
                this.reconnectAttempts = 0;
                this.requestReplay();  // Get messages from while disconnected
                resolve();
            };
            
            this.socket.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.dispatchMessage(message);
            };
            
            this.socket.onerror = (err) => reject(err);
            this.socket.onclose = () => this.reconnect();
        });
    }
    
    subscribe(operationId: string, handler: MessageHandler): () => void {
        if (!this.messageHandlers.has(operationId)) {
            // Tell backend we want messages for this operation
            this.send({ type: "subscribe", operation_id: operationId });
            this.messageHandlers.set(operationId, new Set());
        }
        
        this.messageHandlers.get(operationId)!.add(handler);
        
        // Return unsubscribe function
        return () => {
            this.messageHandlers.get(operationId)?.delete(handler);
        };
    }
    
    private reconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) return;
        
        const delay = Math.pow(2, this.reconnectAttempts) * 1000;
        this.reconnectAttempts++;
        
        setTimeout(() => this.connect(), delay);
    }
    
    private requestReplay() {
        // Ask backend for message history
        this.send({ type: "request_replay" });
    }
    
    private dispatchMessage(message: any) {
        const handlers = this.messageHandlers.get(message.operation_id);
        handlers?.forEach(handler => handler(message));
    }
}

export const wsClient = new WebSocketClient();
export const useWebSocket = () => ({
    subscribe: (opId: string, handler: MessageHandler) => 
        wsClient.subscribe(opId, handler),
});
```

#### HTTP API Client

```typescript
// src/services/api.ts
class APIClient {
    private baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001";
    private axiosInstance = axios.create({
        baseURL: this.baseURL,
        timeout: 30000,
    });
    
    constructor() {
        // Add request interceptor for session ID
        this.axiosInstance.interceptors.request.use(
            (config) => {
                const sessionId = sessionStorage.getItem("copilot_session_id");
                if (sessionId) {
                    config.headers["X-Session-ID"] = sessionId;
                }
                return config;
            }
        );
        
        // Add response interceptor for error handling
        this.axiosInstance.interceptors.response.use(
            (response) => response,
            (error) => {
                if (error.response?.status === 401) {
                    // Session expired, redirect to login
                    window.location.href = "/auth/login";
                }
                return Promise.reject(error);
            }
        );
    }
    
    async post<T>(path: string, data?: any): Promise<T> {
        const response = await this.axiosInstance.post<T>(path, data);
        return response.data;
    }
    
    async get<T>(path: string): Promise<T> {
        const response = await this.axiosInstance.get<T>(path);
        return response.data;
    }
}

export const apiService = new APIClient();
```

---

## WebSocket Communication

### Message Protocol

**Client → Server** (subscriptions):
```json
{
    "type": "subscribe",
    "operation_id": "spec-feature-123-1234567890"
}
```

**Server → Client** (messages):
```json
{
    "id": "msg-uuid",
    "type": "execution",
    "content": "Generating specification...",
    "timestamp": "2026-02-19T10:30:45.123456Z",
    "sender": "Copilot CLI",
    "operation_id": "spec-feature-123-1234567890"
}
```

### Message Lifecycle

```
1. Frontend generates document
   └─> POST /generate-spec with operation_id
   
2. Backend receives request
   └─> Emits MessageType.EXECUTION "Starting..."
   └─> Runs generation in thread
   
3. During generation
   └─> Emits MessageType.EXECUTION "Progress..."
   └─> Multiple messages possible
   
4. Generation completes
   └─> Emits MessageType.COMPLETE "Done!"
   
5. On error
   └─> Emits MessageType.ERROR "Failed..."
   
6. Client receives all via WebSocket
   └─> ConversationPanel displays in real-time
   
7. On disconnect + reconnect
   └─> Client requests replay
   └─> Server resends last N messages
```

### Replay Mechanism

Handles disconnections gracefully:

```typescript
// Client requests replay on reconnect
private requestReplay() {
    this.send({ type: "request_replay" });
}

// Server responds with message history
@router.websocket("/api/v1/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await ws_manager.connect(websocket, session_id)
    
    while True:
        message = await websocket.receive_json()
        
        if message["type"] == "request_replay":
            # Send last messages for all subscribed operations
            for op_id in ws_manager.subscriptions.get(session_id, set()):
                history = ws_manager.message_history.get(op_id, [])
                for msg in history[-100:]:  # Last 100 messages
                    await websocket.send_json(msg.model_dump(mode="json"))
```

---

## Authentication & Security

### Session-Based Authentication (Current)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User enters GitHub PAT                                   │
│    POST /api/v1/auth/github { token: "ghp_xxx..." }        │
│                                                              │
│ 2. Backend validates token with GitHub API                  │
│    GET https://api.github.com/user (Authorization: token)  │
│                                                              │
│ 3. Backend creates session                                  │
│    session_id = uuid()                                      │
│    sessions[session_id] = { token, user_info, created_at } │
│    Response: { session_id, user_login, ... }               │
│                                                              │
│ 4. Client stores session_id in sessionStorage               │
│    sessionStorage.setItem("copilot_session_id", session_id) │
│                                                              │
│ 5. Client includes session_id in all requests               │
│    Header: X-Session-ID: session_id                        │
│    OR: WS query param: /ws?session_id=xxx                  │
│                                                              │
│ 6. Backend validates session on every request               │
│    if session_id not in sessions: return 401 Unauthorized  │
└─────────────────────────────────────────────────────────────┘
```

### Security Considerations

**Current Implementation**:
- ✅ CORS restricted to localhost (development)
- ✅ Session validation on every request
- ✅ GitHub token stored only in backend (not sent to client)
- ✅ WebSocket requires valid session

**Future Improvements**:
- [ ] OAuth2 with GitHub app (replace PAT)
- [ ] HTTPS + Secure cookies instead of sessionStorage
- [ ] Rate limiting per session
- [ ] Token refresh/rotation mechanism
- [ ] CSRF protection on state-changing operations

---

## Data Models

### Backend Models (Pydantic)

```python
# Auth
class SessionData(BaseModel):
    session_id: str
    github_token: str
    github_user: GitHubUser
    created_at: datetime

class GitHubUser(BaseModel):
    id: int
    login: str
    name: Optional[str]
    avatar_url: str

# Documents
class DocumentBase(BaseModel):
    type: str  # "spec", "plan", "task"
    feature_id: str
    content: str

class Document(DocumentBase):
    id: str
    created_at: datetime
    updated_at: datetime

# WebSocket Messages
class WSMessage(BaseModel):
    id: str
    type: MessageType
    content: str
    timestamp: datetime
    sender: str = "Copilot CLI"
    operation_id: str
```

### Frontend Types (TypeScript)

```typescript
// Auth
interface SessionInfo {
    sessionId: string;
    userLogin: string;
    avatarUrl: string;
}

// Documents
interface Document {
    id: string;
    type: "spec" | "plan" | "task";
    featureId: string;
    content: string;
    createdAt: Date;
    updatedAt: Date;
}

// WebSocket
type MessageType = "thinking" | "execution" | "error" | "complete" | "info";

interface WSMessage {
    id: string;
    type: MessageType;
    content: string;
    timestamp: Date;
    sender: string;
    operationId: string;
}

// Components
interface DocumentEditorProps {
    docType: "spec" | "plan" | "task";
    featureId: string;
    initialContent?: string;
    onSave?: (content: string) => Promise<void>;
}
```

---

## Key Patterns & Best Practices

### 1. Error Boundary Pattern (Frontend)

```typescript
class ErrorBoundary extends React.Component<Props, State> {
    state = { hasError: false, error: null };
    
    static getDerivedStateFromError(error: Error) {
        return { hasError: true, error };
    }
    
    componentDidCatch(error: Error, info: React.ErrorInfo) {
        console.error("Error caught:", error, info);
    }
    
    render() {
        if (this.state.hasError) {
            return <ErrorFallback error={this.state.error} />;
        }
        return this.props.children;
    }
}
```

### 2. Dependency Injection (Backend)

```python
# Instead of importing service directly
# Pass service as dependency

from fastapi import Depends

async def get_doc_generator() -> DocGenerator:
    return DocGenerator(cli_path="/usr/bin/copilot", github_token=os.getenv("GITHUB_TOKEN"))

@router.post("/generate-spec")
async def generate_spec(request: SpecGenerationRequest,
                       generator: DocGenerator = Depends(get_doc_generator)):
    # Use injected generator
    result = await asyncio.to_thread(generator.generate_spec, ...)
    return result
```

### 3. Retry with Exponential Backoff (Frontend)

```typescript
async function retryWithBackoff<T>(
    fn: () => Promise<T>,
    maxAttempts = 3,
    baseDelay = 1000
): Promise<T> {
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            return await fn();
        } catch (error) {
            if (attempt === maxAttempts) throw error;
            const delay = baseDelay * Math.pow(2, attempt - 1);
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
}

// Usage
const response = await retryWithBackoff(() =>
    apiService.post("/api/v1/generate-spec", data)
);
```

### 4. Message Coalescing (Backend)

To avoid spamming WebSocket with repeated progress messages:

```python
async def _emit_ws_message(operation_id: str, msg_type: MessageType, 
                          content: str):
    """Emit single message, not repeated heartbeats."""
    
    message = WSMessage(
        id=str(uuid.uuid4()),
        type=msg_type,
        content=content,
        timestamp=datetime.now(),
        operation_id=operation_id,
    )
    
    # Broadcast to all subscribed clients
    await ws_manager.broadcast_to_operation(operation_id, message)
```

Rather than:
```python
# ❌ DON'T DO THIS - spams WebSocket
for i in range(100):
    await _emit_ws_message(operation_id, MessageType.EXECUTION, "Progress...")
    await asyncio.sleep(2)
```

Do this:
```python
# ✅ DO THIS - single progress update
await _emit_ws_message(operation_id, MessageType.EXECUTION, "Starting...")
# Run generation
result = await asyncio.to_thread(generator.generate_spec, ...)
# Final message when done
await _emit_ws_message(operation_id, MessageType.COMPLETE, "Done!")
```

### 5. Type-Safe API Responses

All endpoints return typed response models:

```python
# ✅ Good
@router.post("/generate-spec", response_model=DocumentResponse)
async def generate_spec(request: SpecGenerationRequest) -> DocumentResponse:
    # Guaranteed return type checked at runtime
    return DocumentResponse(id="...", type="spec", content="...", ...)

# ❌ Avoid
@router.post("/generate-spec")
async def generate_spec(request):
    return {"id": "...", "type": "spec", ...}  # No type checking
```

---

## Error Handling & Recovery

### Backend Error Handling

```python
from fastapi import HTTPException, status

@router.post("/generate-spec")
async def generate_spec(request: SpecGenerationRequest):
    try:
        # Validate request
        if not request.sequence:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="sequence is required"
            )
        
        # Validate session
        if not auth_service.validate_session(request.session_id):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )
        
        # Run generation
        if request.operation_id:
            await _emit_ws_message(request.operation_id, MessageType.EXECUTION, "Starting...")
        
        try:
            result = await asyncio.to_thread(
                doc_gen.generate_spec, request.sequence, timeout=300
            )
        except subprocess.TimeoutExpired:
            await _emit_ws_message(request.operation_id, MessageType.ERROR,
                                  "Generation timed out after 5 minutes")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Document generation timed out"
            )
        except subprocess.CalledProcessError as e:
            await _emit_ws_message(request.operation_id, MessageType.ERROR,
                                  f"Generation failed: {e.stderr}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Document generation failed"
            )
        
        if request.operation_id:
            await _emit_ws_message(request.operation_id, MessageType.COMPLETE,
                                  "Document generated successfully!")
        
        return DocumentResponse(id="...", content=result.content, ...)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_spec: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
```

### Frontend Error Handling

```typescript
export async function useDocumentGeneration(featureId: string) {
    const [error, setError] = useState<Error | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    
    const generate = useCallback(async (prompt: string) => {
        setError(null);
        setIsLoading(true);
        
        try {
            const response = await retryWithBackoff(() =>
                apiService.post(`/api/v1/features/${featureId}/generate-spec`, {
                    sequence: prompt,
                },
                { timeout: 600000 }  // 10 minute timeout for long operations
            ),
            maxAttempts: 3
            );
            
            return response;
        } catch (err) {
            const message = err instanceof Error ? err.message : "Unknown error";
            setError(new Error(`Failed to generate: ${message}`));
            throw err;
        } finally {
            setIsLoading(false);
        }
    }, [featureId]);
    
    return { generate, error, isLoading };
}
```

### WebSocket Recovery

```typescript
class WebSocketClient {
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    
    private async reconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error("Max reconnection attempts reached");
            return;
        }
        
        const delay = Math.pow(2, this.reconnectAttempts) * 1000 + 
                     Math.random() * 1000;  // Jitter to avoid thundering herd
        
        this.reconnectAttempts++;
        
        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        await new Promise(resolve => setTimeout(resolve, delay));
        
        try {
            await this.connect();
        } catch (err) {
            console.error("Reconnection failed:", err);
            this.reconnect();  // Recursive retry
        }
    }
}
```

---

## Performance Considerations

### Frontend

- **Code Splitting**: Next.js automatic route-based code splitting
- **Image Optimization**: next/image for automatic optimization
- **Memoization**: React.memo for expensive components
- **Lazy Loading**: dynamic imports for heavy components

### Backend

- **Connection Pooling**: FastAPI + asyncio handles connection management
- **Message Pagination**: Limit query results with skip/limit
- **Caching**: In-memory caches for frequently accessed data
- **Async All I/O**: No blocking operations on main thread

### WebSocket

- **Selective Broadcasting**: Only send to subscribed clients
- **Message Buffering**: Keep last 100 messages for replay
- **Connection Limits**: Max connections per session to prevent DOS

---

## Testing Strategy

### Backend Unit Tests

```python
# tests/test_websocket_manager.py
import pytest
from src.services.websocket_manager import WebSocketManager

@pytest.fixture
def ws_manager():
    return WebSocketManager()

def test_broadcast_to_operation(ws_manager, mock_websocket):
    ws_manager.active_connections["session1"] = [mock_websocket]
    ws_manager.subscribe("session1", "op1")
    
    message = WSMessage(type=MessageType.EXECUTION, content="Test")
    
    await ws_manager.broadcast_to_operation("op1", message)
    
    mock_websocket.send_json.assert_called_once()
```

### Frontend Tests

```typescript
// tests/ConversationPanel.test.tsx
import { render, screen } from "@testing-library/react";
import { ConversationPanel } from "@/components/ConversationPanel";

describe("ConversationPanel", () => {
    it("displays messages in real-time", async () => {
        const mockSubscribe = jest.fn((opId, handler) => {
            handler({
                type: "execution",
                content: "Test message",
                timestamp: new Date(),
            });
        });
        
        // Mock WebSocket service
        jest.mock("@/services/websocket", () => ({
            useWebSocket: () => ({ subscribe: mockSubscribe }),
        }));
        
        render(<ConversationPanel operationId="op1" />);
        
        expect(screen.getByText("Test message")).toBeInTheDocument();
    });
});
```

### Integration Tests

```python
# tests/test_api_integration.py
@pytest.mark.asyncio
async def test_generate_spec_with_websocket():
    """Test full flow: request → generation → WebSocket emission."""
    
    # 1. Create session
    session = auth_service.create_session("ghp_token")
    
    # 2. Make generation request
    response = await client.post(
        "/api/v1/features/123/generate-spec",
        json={
            "sequence": "Create a todo app",
            "operation_id": "op1",
            "session_id": session.session_id,
        }
    )
    
    # 3. Assert response
    assert response.status_code == 200
    assert response.json()["type"] == "spec"
    
    # 4. Assert WebSocket messages were emitted
    # (Check broker or mock)
    assert ws_manager.message_history["op1"][0].type == MessageType.EXECUTION
    assert ws_manager.message_history["op1"][-1].type == MessageType.COMPLETE
```

---

## Deployment Architecture

### Local Development
```bash
# Terminal 1: Backend
cd backend && python -m uvicorn src.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev

# Ports: Backend 8001, Frontend 3000
```

### Docker Compose (All-in-one)
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8001:8001"
    environment:
      GITHUB_TOKEN: ${GITHUB_TOKEN}
      
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_BASE_URL: http://backend:8001
```

### Production Deployment
- **Backend**: Gunicorn + Uvicorn workers behind Nginx
- **Frontend**: Next.js standalone build + Vercel/Netlify or Nginx
- **Database**: PostgreSQL (currently in-memory, planned upgrade)
- **Cache**: Redis for session storage
- **Monitoring**: Prometheus + Grafana

---

## Conclusion

The architecture is designed to enable real-time document generation with transparent AI reasoning, focusing on:

1. **Responsiveness**: WebSocket streaming provides instant feedback
2. **Reliability**: Error handling and reconnection mechanisms
3. **Scalability**: Async architecture supports many concurrent users
4. **Maintainability**: Clear separation of concerns, type-safe models
5. **Extensibility**: Service layer makes it easy to add new features

Key innovations in this phase:
- ✅ WebSocket message streaming during long-running operations
- ✅ Async/threading pattern for non-blocking I/O
- ✅ Message replay mechanism for disconnect resilience
- ✅ Type-safe request/response models with Pydantic

Next architectural enhancements planned:
- OAuth2 authentication
- Database persistence layer
- Message queue (RabbitMQ/Redis) for reliability
- API versioning strategy
- GraphQL layer (optional)

