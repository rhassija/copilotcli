# Feature Specification: Guided Workflow and Repo-Targeted Orchestration

**Feature Branch**: `006-guided-workflow-roadmap`
**Created**: 2026-02-12
**Status**: Draft
**Input**: User description: "Clean spec capturing learnings, roadmap, and requirements for repo selection, auth, Speckit readiness, and guided workflow."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Select Repo and Generate Spec (Priority: P1)

As a business user, I want to select a target repository and branch so that the
spec is generated in the correct codebase.

**Why this priority**: Repo targeting is foundational; without it, output lands
in the wrong place.

**Independent Test**: A spec is generated inside the selected repo and not in
any other location.

**Acceptance Scenarios**:

1. **Given** a valid local Git repo, **When** I select it and submit a
   requirement, **Then** a spec is created under `specs/###-feature/spec.md` in
   that repo.
2. **Given** a repo with multiple branches, **When** I choose "Use existing
   branch", **Then** the spec is created on that branch without creating a new
   branch.

---

### User Story 2 - Guided Stepper with Review Gates (Priority: P1)

As a reviewer, I want a guided workflow with explicit approval steps so that I
can review each artifact before the next one is generated.

**Why this priority**: The workflow is sequential and review-heavy; gating is
required for trust.

**Independent Test**: The next step is disabled until I approve the current
artifact.

**Acceptance Scenarios**:

1. **Given** a generated spec, **When** I do not approve it, **Then** the
   "Generate Plan" button remains disabled.
2. **Given** I approve the spec, **When** I proceed, **Then** the plan step
   starts and the workflow status updates to "In Progress".

---

### User Story 3 - Tool Readiness and Auth Guidance (Priority: P2)

As an operator, I want clear readiness checks so that I can fix missing
authentication or tools without guessing.

**Why this priority**: Copilot CLI and Speckit are external dependencies and
frequently fail without guidance.

**Independent Test**: The UI shows a clear error and step-by-step fix when auth
is missing.

**Acceptance Scenarios**:

1. **Given** Copilot CLI is unauthenticated, **When** I open the app, **Then** I
   see a clear banner with instructions to run `/login`.
2. **Given** `.specify` is missing, **When** I try to run a command, **Then** the
   UI offers bootstrap options (init or clone template).

---

### User Story 4 - Edit and Re-Run Spec (Priority: P2)

As a reviewer, I want to update an existing spec and preserve history so that
changes are traceable.

**Why this priority**: Spec review is iterative and spans multiple sessions.

**Independent Test**: The new spec version is saved with a visible diff.

**Acceptance Scenarios**:

1. **Given** an existing spec, **When** I submit a change request, **Then** a new
   version is generated and a diff is shown.
2. **Given** multiple versions exist, **When** I select a prior version, **Then**
   I can view it without overwriting the latest.

---

### Edge Cases

- What happens when the selected path is not a Git repository?
- How does the system handle a dirty working tree with uncommitted changes?
- What happens when Copilot CLI is authenticated but rate limited?
- How does the system handle a repo without `.specify` and without network
  access to bootstrap?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow selecting a target repository path and validate
  it contains a Git root.
- **FR-002**: System MUST allow selecting an existing branch or creating a new
  feature branch.
- **FR-003**: System MUST write all artifacts under the selected repo in
  `specs/###-feature/` and `.specify/`.
- **FR-004**: System MUST verify Copilot CLI authentication and display clear
  remediation steps when missing.
- **FR-005**: System MUST verify Speckit readiness and offer bootstrap options
  when `.specify` is missing.
- **FR-006**: System MUST provide a guided, step-by-step workflow with review
  gates between spec, plan, and tasks.
- **FR-007**: System MUST preserve and display spec version history with diffs.
- **FR-008**: System MUST allow model selection and record the model used in
  generated artifacts.
- **FR-009**: System MUST provide a safe re-run mechanism for existing specs
  without overwriting history.
- **FR-010**: System MUST persist workflow state per repo and branch so users can
  resume after delays.

### Key Entities *(include if feature involves data)*

- **Repository**: Target repo path, validation status, default branch.
- **Branch**: Current branch, create/reuse selection, dirty state.
- **Workflow Step**: Spec, Plan, Tasks; status and approvals.
- **Spec Version**: Version number, diff, author, timestamp.
- **Tool Status**: Copilot auth status, Speckit readiness, model selection.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can generate a spec in a selected repo within 2 minutes.
- **SC-002**: 100% of workflow steps are blocked until prior step approval.
- **SC-003**: 90% of users can resolve auth/tool readiness issues without
  developer intervention.
- **SC-004**: Spec history retains at least the last 5 versions with diffs.
- **SC-005**: Model used for generation is displayed and persisted on each
  artifact.
