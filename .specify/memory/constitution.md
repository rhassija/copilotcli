# Copilot SDLC Platform Constitution

<!--
  SYNC IMPACT REPORT v1.2.0
  Version Bump: 1.1.0 → 1.2.0 (MINOR: clean rewrite reflecting current learnings
  and roadmap for repo targeting, agent enrichment, and guided workflow)
  Last Amended: 2026-02-12
  Status: Active

  Changes Made:
  - Consolidated principles into five clean, testable rules
  - Clarified Speckit role as scaffold + agent enrichment
  - Added explicit repo/branch targeting and workflow gates
  - Codified auth/tool readiness requirements

  Added Sections:
  - Operational Requirements
  - Workflow & Review Gates

  Removed Sections:
  - Detailed phase roadmap (moved to specs as implementation roadmap)

  Templates Requiring Updates:
  ✅ .specify/templates/plan-template.md (verified)
  ✅ .specify/templates/spec-template.md (verified)
  ✅ .specify/templates/tasks-template.md (verified)
  ✅ .specify/templates/checklist-template.md (verified)
  ✅ .specify/templates/agent-file-template.md (verified)

  Runtime Guidance Updates:
  ⚠ POC-README.md (not updated for clean rewrite)
  ⚠ IMPLEMENTATION-SUMMARY.md (not updated for clean rewrite)

  Follow-up TODOs:
  - Align POC docs when migrating to new project
-->

## Core Principles

### I. Natural Language First
All user interaction MUST be natural language. Users MUST be able to define,
review, and request changes without writing code, markdown, or structured
syntax. The UX MUST preserve user intent verbatim and display it back for
confirmation.

**Rationale**: Keeps business and technical stakeholders aligned with a shared,
non-technical interface.

### II. Speckit Scaffold + Agent Enrichment
Speckit provides structure (templates, folders, scripts). The agent (Copilot
CLI now, SDK later) fills in the content. The UX MUST orchestrate both steps and
MUST NOT embed business logic itself.

**Rationale**: Separates structure from intelligence and keeps the workflow
auditable.

### III. Target Repo as Source of Truth
All artifacts MUST be written to the user-selected repository and branch. The
UX MUST never write artifacts to the tool's development repo unless explicitly
chosen. Specs, plans, tasks, and related artifacts MUST live under
`.specify/` and `specs/` in the target repo.

**Rationale**: Prevents accidental writes and keeps audit history in the correct
codebase.

### IV. Non-Tech Readability and Review
All generated artifacts MUST be understandable by non-technical reviewers.
Specs MUST be plain English and must include acceptance scenarios and
measurable outcomes. Ambiguity MUST be surfaced as explicit clarifications.

**Rationale**: Ensures real business review and reduces rework.

### V. Sequential, Review-Gated Workflow
Commands run one at a time with explicit review gates between steps. The UX MUST
track status per repo/branch and only allow the next step after approval.

**Rationale**: Matches real-world review cycles and prevents accidental
progression.

## Operational Requirements

The UX MUST provide:
- Repo selector (path + validation) and branch selector (create or reuse)
- Auth readiness checks for Copilot CLI, with clear guidance to fix issues
- Speckit readiness checks (presence of `.specify`); bootstrap options if missing
- Model selection controls and visible model provenance in generated artifacts
- Edit and re-run flows for existing specs (versioning + diff support)

## Workflow & Review Gates

1. Capture requirement (draft)
2. Generate spec (scaffold + agent)
3. Review spec (approve or request changes)
4. Generate plan (scaffold + agent)
5. Review plan
6. Generate tasks (scaffold + agent)
7. Review tasks

Each step MUST be resumable with full context, even after days or weeks.

## Governance

- **Constitution Authority**: This constitution supersedes all other workflow
  documents.
- **Amendment Process**: Amendments MUST include rationale, impact analysis on
  templates (spec, plan, tasks, checklist), and approval by project leadership.
- **Version Semantics**:
  - MAJOR: Principle removal or breaking changes to workflow
  - MINOR: New principle or new required artifact sections
  - PATCH: Clarifications or wording refinements
- **Compliance Review**: Tooling MUST check outputs against the Core Principles
  before marking a step as approved.

**Version**: 1.2.0 | **Ratified**: 2026-02-12 | **Last Amended**: 2026-02-12
