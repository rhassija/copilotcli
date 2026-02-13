# Copilot CLI SDLC Platform Constitution

<!-- 
  SYNC IMPACT REPORT v1.0.1
  Version Bump: 1.0.0 → 1.0.1 (PATCH: Frontend UX clarification for POC phase)
  Last Amended: 2026-02-12
  Status: Active
  
  Changes Made:
  - Technology Stack: Clarified frontend as Streamlit for minimal POC phase
  - Added Development Phases section with POC → Production roadmap
  - Added Python Environment section referencing copilotcompanion pyenv
  - Architecture remains Speckit-orchestrated, principles unchanged
  
  Template Update Status:
  ✅ plan-template.md: Verified - Constitution Check gate aligns with principles
  ✅ spec-template.md: Verified - User story prioritization (P1/P2/P3) aligns with SDLC phases
  ✅ tasks-template.md: Verified - Task organization by user story supports continuous SDLC integration
  ✅ Technology Stack: Clarified for POC phase (Streamlit)
-->

## Core Principles

### I. Natural Language-First Interface
All user interactions—whether from business stakeholders, product managers, or developers—MUST originate as natural language prompts in the UX interface. The UX MUST accept plain English requirements, change requests, and implementation directives without requiring users to write code, markdown, or structured syntax. Examples: "Create a login feature that allows users to reset passwords," "Generate deployment tasks for the payment system," "Refine the spec to include role-based access control."

**Rationale**: Democratizes software development by removing technical barriers. Business users can express needs directly; developers express intent clearly. Natural language creates a shared communication substrate across all personas.

### II. Speckit-Driven Orchestration
Behind the UX interface, all transformations of natural language input MUST be delegated to Speckit commands—`/specify`, `/plan`, `/tasks`, `/implement`, and other core commands. The UX layer MUST NOT perform business logic; it MUST translate user intent into Speckit invocations and present structured results. The UX is a thin facade; Speckit is the engine.

**Rationale**: Ensures consistency, testability, and maintainability. Speckit commands remain the single source of algorithmic truth. The UX is decoupled from core logic and can evolve independently.

### III. Repository-as-Source-of-Truth
All artifacts—specifications, implementation plans, task lists, code—MUST be stored in the same Git repository. No external dependency on Jira, wiki, or third-party databases. Every meaningful decision MUST be recorded in `.specify/memory/`, `specs/`, or source code; every artifact MUST be version-controlled and auditable. Non-tech users access specs via the UX, but the UX reads from and writes to Git.

**Rationale**: Single source of truth minimizes sync errors, enables offline work, preserves history, and empowers teams to self-serve without privileged access to external tools. Git is universally trusted.

### IV. Non-Tech User Accessibility
All generated artifacts—specification files, plans, task summaries—MUST be presentable in plain English, with no technical jargon or code syntax required for comprehension. Business users MUST be able to read, understand, and approve specs without engineering training. Change requests from non-tech users MUST be accepted in natural language and fed back to Speckit for automatic amendment.

**Rationale**: Broadens participation, improves requirement clarity, reduces rework, and builds accountability across the organization.

### V. Continuous SDLC Integration (Full Lifecycle in One Folder)
The workflow MUST support the complete software development lifecycle—from business requirement through specification, planning, tasking, implementation, and deployment—within a single Git folder and Speckit command chain. No hand-offs to external systems; no context loss between phases. A business user's natural language prompt MUST trigger an automated chain: spec creation → review → plan generation → task breakdown → developer handoff to `/implement`.

**Rationale**: Eliminates process friction, maintains context, enables rapid iteration, and creates accountability for the full lifecycle in one place.

## Technology Stack & Architecture

### POC Phase (Minimal Viable Platform)
- **Frontend UX**: Streamlit (rapid prototyping; web-based, Python-native)
- **Backend Services**: Python APIs that invoke Speckit CLI and Copilot SDK
- **Speckit Integration**: Direct CLI invocation via `/specify`, `/plan`, `/tasks`, `/implement` commands
- **Copilot SDK**: Integrated for AI-assisted code generation, natural language processing, and suggestion refinement
- **Repository**: Git as version control; `.specify/` folder structure for memory, templates, and configuration
- **Persistence**: File-based (Git) for artifacts; lightweight session state for UX
- **Authentication**: GitHub integration for consistency with Copilot ecosystem
- **Python Environment**: `copilotcompanion` (pyenv virtual environment)

### Production Phase (Target Roadmap)
Once POC validates the natural language → Speckit orchestration concept with end-to-end test scenarios:
- **Frontend UX**: Migrate to [React/Vue/Angular + TypeScript] for production-grade responsiveness, state management, and UX polish
- **Backend Services**: Node.js/Python/TypeScript APIs with scalability, authentication, audit logging
- **Persistence**: PostgreSQL for UX state, session management; specs and artifacts remain in Git
- **Authentication**: Enterprise SSO (GitHub/OAuth) integration
- **Deployment**: Containerized services (Docker), orchestration via Kubernetes or similar

## POC & Development Phases

### Phase 0: Minimal POC (Streamlit-Based Prototype)
**Goal**: Validate the core workflow—natural language input → Speckit command invocation → artifact generation → non-tech user review.

**Scope**:
1. Streamlit UX with text input for business requirements
2. Backend invocation of `/specify` command to generate spec.md
3. Non-tech user reads and approves spec via UX
4. Feedback loop: user requests changes via natural language → `/specify` invoked again
5. Developer handoff notification (spec ready)

**Success Criteria**:
- Non-technical user can input requirement in plain English
- Spec is generated and reviewable in UX
- User can request changes, spec updates automatically
- Full artifact trail visible in Git

**Exit Gate**: End-to-end workflow proof-of-concept validated with minimal test scenarios (e.g., "Create a login feature", "Add reporting page")

### Phase 1: POC Validation & Iteration
- Gather feedback from business users and developers
- Identify workflow friction points
- Integrate with GitHub (auth, artifact storage)
- Build foundation for `/plan` and `/tasks` exposed via UX

### Phase 2: Production UX Migration
- Migrate frontend to production framework (React/Vue/Angular)
- Scale backend to support concurrent users, audit logging
- Implement advanced features: version history, approval workflows, role-based access
- Full integration with GitHub Copilot SDK

## Development Workflow

### Phase 1: Business User Initiates Requirement
1. Non-tech user opens UX, enters natural language requirement (e.g., "Allow users to export reports as PDF")
2. UX accepts input, displays a preview of how the requirement will be interpreted
3. User confirms or refines the prompt

### Phase 2: Speckit /specify Command
1. UX invokes Speckit's `/specify` command with the refined requirement
2. Speckit generates `specs/[###-feature]/spec.md` with user stories, acceptance criteria, edge cases, functional requirements
3. UX retrieves the generated spec and displays a non-technical summary to the business user

### Phase 3: Review & Approval
1. Business user reviews the spec via UX (plain English summary + spec.md preview)
2. User approves or requests natural language changes (e.g., "Add support for batch exports")
3. If changes requested: UX sends amended prompt to Speckit `/specify`; Speckit updates spec.md; loop to review

### Phase 4: Developer Handoff
1. Once approved, UX creates a task or branch notification for developers
2. Developer opens VS Code with Speckit extension; uses `/implement` command to generate implementation plan and tasks
3. Developer implements according to generated tasks, creating code in same Git folder

### Phase 5: Artifact Evolution
1. All intermediate artifacts (research.md, data-model.md, contracts/, tasks.md) are stored in `specs/[###-feature]/`
2. Non-tech users can view high-level summaries; developers/architects can access technical details
3. Any subsequent requirement change loops back to Phase 2 via UX natural language input

## Quality & Testing Discipline

- **Specification Completeness**: Specs MUST include user stories (prioritized P1/P2/P3), acceptance scenarios, functional requirements, and edge cases—verified before developer handoff
- **Acceptance Criteria Clarity**: Each spec MUST be reviewable by non-tech users; ambiguous language MUST be flagged and resolved before implementation
- **Task Breakdown Verification**: Tasks MUST be independently testable, with clear file paths and dependencies, enabling parallel development
- **Regression Coverage**: Changes requested via natural language MUST not remove or weaken prior acceptance criteria without explicit business sign-off

## Governance

- **Constitution Authority**: This constitution supersedes all other development practices and workflow documentation
- **Amendment Process**: Any amendment to this constitution MUST include rationale, impact analysis on all affected templates (plan, spec, tasks), and approval from project leadership before taking effect
- **Version Semantics**: 
  - MAJOR: Principle removal or redefinition; breaking changes to Speckit command contract
  - MINOR: New principle added or existing principle expanded; new required sections in artifacts
  - PATCH: Clarifications, wording refinement, non-semantic governance updates
- **Runtime Guidance**: Refer to `.specify/templates/commands/` for detailed execution workflows for each Speckit command; these documents provide tactical guidance under this strategic framework
- **Compliance Review**: All generated artifacts (specs, plans, tasks) MUST be auditable for compliance with the five Core Principles; tooling SHOULD flag violations before artifact finalization

**Version**: 1.0.1 | **Ratified**: 2026-02-12 | **Last Amended**: 2026-02-12
