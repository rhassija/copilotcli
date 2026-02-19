# Feature Specification: Copilot CLI SDLC App (Clean Roadmap)

**Feature Branch**: `001-copilocli`
**Created**: 2026-02-12
**Status**: Draft
**Input**: User description: "End-to-end SDLC app with repo targeting, guided workflow, and Speckit + Copilot orchestration."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Select Repo and Generate Spec (Priority: P1)

As a business user, I want to select a target repository and branch so that the
spec is generated in the correct codebase.

**Why this priority**: Repo targeting is foundational and prevents writing
artifacts to the tool repo.

**Independent Test**: A spec is created only in the selected repo/branch.

**Acceptance Scenarios**:

1. **Given** a valid local Git repo, **When** I select it and submit a
   requirement, **Then** `specs/###-feature/spec.md` is created in that repo.
2. **Given** the tool repo is open, **When** I target a different repo, **Then**
   no artifacts are written to the tool repo.

---

### User Story 2 - Guided Stepper with Review Gates (Priority: P1)

As a reviewer, I want a guided workflow with explicit approval steps so that I
can review each artifact before the next one is generated.

**Why this priority**: The workflow is sequential and review-heavy.

**Independent Test**: The next step is disabled until the current step is
approved.

**Acceptance Scenarios**:

1. **Given** a generated spec, **When** I do not approve it, **Then** "Generate
   Plan" remains disabled.
2. **Given** I approve the spec, **When** I proceed, **Then** the plan step
   starts and status updates to "In Progress".

---

### User Story 3 - Tool Readiness and Auth Guidance (Priority: P1)

As an operator, I want clear readiness checks so I can fix missing auth or tools
without guessing.

**Why this priority**: Copilot CLI and Speckit are external dependencies and
fail without clear guidance.

**Independent Test**: The app shows precise remediation steps when tools or auth
are missing.

**Acceptance Scenarios**:

1. **Given** Copilot CLI is unauthenticated, **When** I open the app, **Then** I
   see a banner instructing `/login` in a terminal.
2. **Given** `.specify` is missing, **When** I run a command, **Then** the UI
   offers bootstrap options (init or clone template).

---

### User Story 4 - Enriched Specs with Model Selection (Priority: P1)

As a product owner, I want the spec to be enriched by an agent and know which
model was used.

**Why this priority**: The spec must be meaningful, not boilerplate.

**Independent Test**: The generated spec includes full user stories,
requirements, and success criteria, and records the model used.

**Acceptance Scenarios**:

1. **Given** Copilot CLI is available, **When** I generate a spec, **Then** the
   output contains complete stories and requirements beyond template placeholders.
2. **Given** I select a model, **When** a spec is generated, **Then** the model
   is recorded in the artifact metadata.

---

### User Story 5 - Edit and Re-Run Existing Specs (Priority: P2)

As a reviewer, I want to update an existing spec and preserve history so changes
are traceable.

**Why this priority**: Review cycles are iterative and long-lived.

**Independent Test**: A change request creates a new spec version and a diff is
available.

**Acceptance Scenarios**:

1. **Given** an existing spec, **When** I submit a change request, **Then** a
   new version is created and diffed against the prior version.
2. **Given** multiple versions, **When** I select a prior version, **Then** I
   can view it without overwriting the latest.

---

### User Story 6 - Plan and Tasks Workflows (Priority: P2)

As a delivery lead, I want to generate a plan and tasks after spec approval so
engineering can implement reliably.

**Why this priority**: Spec alone is not actionable; plan and tasks are required
for delivery.

**Independent Test**: `/plan` and `/tasks` outputs are generated in the same
feature folder and are review-gated.

**Acceptance Scenarios**:

1. **Given** a spec is approved, **When** I run plan, **Then** `plan.md` is
   created and linked to the spec.
2. **Given** a plan is approved, **When** I run tasks, **Then** `tasks.md` is
   created with user story mapping.

---

### User Story 7 - Clarify Loop (Priority: P3)

As a reviewer, I want clarification prompts to resolve ambiguity before
continuing.

**Why this priority**: Ambiguity causes rework and misalignment.

**Independent Test**: The system blocks progression until clarifications are
resolved.

**Acceptance Scenarios**:

1. **Given** the agent flags a missing detail, **When** I answer, **Then** the
   spec is regenerated with the clarified requirement.

---

### Edge Cases

- What happens when the selected path is not a Git repository?
- How does the system handle a dirty working tree with uncommitted changes?
- What happens when Copilot CLI is authenticated but rate limited?
- How does the system behave without network access for bootstrapping Speckit?
- What happens if a repo is missing `.specify` but a template clone fails?

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
- **FR-010**: System MUST persist workflow state per repo and branch to allow
  resumption after long review delays.
- **FR-011**: System MUST support `/plan` and `/tasks` workflows after approvals.
- **FR-012**: System SHOULD support `/clarify` prompts when ambiguity is detected.
- **FR-013**: System MUST expose explicit "Next Step" buttons aligned to the
  workflow state.
- **FR-014**: System MUST show activity logs and error reasons in the UI.
- **FR-015**: System MUST show tool readiness status (Copilot, Speckit, Git).
- **FR-016**: System MUST display artifact metadata (model used, timestamps,
  branch).
- **FR-017**: System SHOULD provide a template-based bootstrap option for repos
  without `.specify`.
- **FR-018**: System MUST support targeting a different repo than the tool repo.

### Key Entities *(include if feature involves data)*

- **Repository**: Target repo path, validation status, default branch.
- **Branch**: Current branch, create/reuse selection, dirty state.
- **Workflow Step**: Spec, Plan, Tasks; status and approvals.
- **Spec Version**: Version number, diff, author, timestamp.
- **Tool Status**: Copilot auth status, Speckit readiness, model selection.
- **Artifact Metadata**: Model, prompt summary, timestamps, approvals.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can generate a spec in a selected repo within 2 minutes.
- **SC-002**: 100% of workflow steps are blocked until prior step approval.
- **SC-003**: 90% of users can resolve auth/tool readiness issues without
  developer intervention.
- **SC-004**: Spec history retains at least the last 5 versions with diffs.
- **SC-005**: Model used for generation is displayed and persisted on each
  artifact.
- **SC-006**: Plan and tasks are generated only after approval gates.
- **SC-007**: No artifacts are written to the tool repo unless explicitly
  selected by the user.
- **SC-008**: Workflow state can be resumed after 24 hours with no data loss.
