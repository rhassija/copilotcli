# Copilot SDLC Platform - POC Implementation

## Feature: 001-spec-generator

**Branch**: `001-spec-generator`  
**Status**: POC (Prototype)  
**Phase**: Minimal Viable Platform (Streamlit-Based)  
**Constitution Version**: 1.1.0  

## Overview

This POC demonstrates the core Copilot SDLC workflow:

```
Business User (Natural Language)
         ↓
    Streamlit UX
         ↓
      Speckit Scaffold + Copilot CLI
         ↓
   Agent Activity (Real-Time Stream)
         ↓
   Specification Generated (spec.md)
         ↓
   Git Committed
         ↓
  Non-Tech User Reviews & Approves
```

## Quick Start

### Prerequisites

- `copilotcompanion` pyenv environment (Python 3.13.11)
- Streamlit installed in the environment
- Git configured in repository
- Speckit CLI available (or stubbed for POC)

### Setup

```bash
# Activate the Python environment
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
pyenv activate copilotcompanion

# Install dependencies (if not already done)
pip install -r requirements-poc.txt

# Or install individually:
pip install streamlit>=1.28.0
pip install GitPython>=3.1.0
```

### Run the POC

```bash
# From repository root
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
pyenv activate copilotcompanion

streamlit run src/ui/app.py
```

The UI will open at `http://localhost:8501`

## User Guide

### 1. Enter Requirement

Type your feature requirement in plain English. Example:

```
"Create a user authentication system that allows users to sign up, log in, 
and reset their passwords via email"
```

### 2. Submit & Watch

Click **"📤 Submit Requirement"** and observe:
- Agent activity streams in real-time
- Speckit scaffolding runs (feature folder + template)
- Copilot CLI enriches the spec
- Processing status updates

### 3. Review Specification

Once complete, the generated `spec.md` displays:
- User stories (prioritized P1/P2/P3)
- Functional requirements
- Success criteria
- Edge cases

### 4. Request Changes (P2 Feature)

Update your requirement and resubmit. The system:
- Re-runs Copilot CLI enrichment with combined context
- Generates updated spec.md
- Commits changes to Git

## Project Structure

```
copilotcli/
├── src/
│   └── ui/
│       └── app.py                 # Streamlit POC app
├── specs/
│   └── 001-spec-generator/
│       └── spec.md               # Generated specification
├── .specify/
│   ├── memory/
│   │   └── constitution.md       # SDLC Platform Constitution
│   ├── scripts/
│   └── templates/
├── requirements-poc.txt          # Python dependencies
└── README.md                      # This file
```

## Architecture

### Frontend (UX Layer)
- **Framework**: Streamlit
- **Purpose**: Accept natural language input, stream agent activity, display specs
- **Input**: User requirement (plain English text)
- **Output**: Real-time activity log, generated spec.md

### Backend (Orchestration Layer)
- **Engine**: Speckit scaffolding + Copilot CLI enrichment
- **Purpose**: Transform requirement → specification
- **Input**: Natural language requirement
- **Output**: spec.md with user stories, requirements, success criteria

### Storage Layer
- **Primary**: Git repository (`.specify/`, `specs/` directories)
- **Artifacts**: Constitutions, templates, generated specs
- **Version Control**: Full audit trail and rollback capability

### Environment
- **Python**: 3.13.11 (copilotcompanion pyenv)
- **Virtual Env**: `~/.pyenv/versions/3.13.11/envs/copilotcompanion`
- **CLI Access**: Speckit scaffolding + Copilot CLI

## Success Criteria (POC Phase)

From [specs/001-spec-generator/spec.md](specs/001-spec-generator/spec.md):

✅ **SC-001**: End-to-end workflow completes within 2 minutes  
✅ **SC-002**: Agent activity displays in real-time (<500ms latency)  
✅ **SC-003**: Non-tech user understands generated spec without technical help  
✅ **SC-004**: 3+ test requirements produce valid specifications  
✅ **SC-005**: Spec update workflow works end-to-end  
✅ **SC-006**: Error handling displays user-friendly messages  
✅ **SC-007**: Demo to stakeholders <5 minutes  

## Testing the POC

### Test Scenario 1: Basic Requirement → Spec

```
Input: "Create a login page"
Expected: 
  - Agent activity streams
  - spec.md generated in specs/001-spec-generator/
  - Non-tech user can read it
```

### Test Scenario 2: Complex Requirement

```
Input: "Build a multi-tenant SaaS platform with role-based access control, 
audit logging, and webhook integrations"
Expected:
  - Detailed user stories generated
  - All functional requirements captured
  - Success criteria measurable
```

### Test Scenario 3: Spec Updates (P2)

```
Initial: "Create a login page"
Update: "Add two-factor authentication"
Expected:
  - Updated spec.md incorporates 2FA
  - Previous spec accessible in Git history
```

## Known Limitations (POC Phase)

1. **No queuing**: Only one request at a time. Subsequent requests display "Please wait" message.
2. **Copilot auth required**: Copilot CLI must be authenticated in a terminal session.
3. **No approval workflow**: Users view specs but cannot explicit approve/reject. Phase 1 will add this.
4. **Minimal error recovery**: Timeouts/failures show raw messages. Phase 2 will add retry logic.
5. **Single-repo targeting**: The app writes to the current repo only (repo selector pending).

## Next Steps (Phase 1 & Beyond)

### Phase 1: Validation & Iteration
- [ ] Gather feedback from business users
- [ ] Add approval workflow (approve/request-changes buttons)
- [ ] Add repo/branch selection
- [ ] Add Copilot auth status checks + guidance
- [ ] Version history for specs

### Phase 2: Production UX
- [ ] Migrate to React/Vue/Angular
- [ ] Scale backend for concurrent users
- [ ] Add role-based access control
- [ ] Implement audit logging
- [ ] Deploy to production infrastructure

### Phase 3: Full Integration
- [ ] Connect `/plan` workflow (generate implementation plans)
- [ ] Connect `/tasks` workflow (break down into developer tasks)
- [ ] Connect `/implement` workflow (code generation)
- [ ] Full SDLC pipeline in single UI

## Configuration

### Environment Variables

```bash
# Optional: Override default Python env
export PYTHON_ENV=copilotcompanion

# Optional: Development mode (verbose logging)
export DEBUG=1
```

### Streamlit Config

Create `~/.streamlit/config.toml` to customize:

```toml
[client]
showErrorDetails = true

[logger]
level = "debug"
```

## Debugging

### View logs

```bash
# Streamlit writes to terminal - watch for errors
# Activity log is captured in UI

# Check Git commits
git log --oneline specs/001-spec-generator/
```

### Common Issues

**Issue**: "Command not found: streamlit"
```bash
# Solution: Ensure environment is activated
eval "$(pyenv init --path)"
pyenv activate copilotcompanion
```

**Issue**: "Copilot CLI not authenticated"
```bash
# Solution: Ensure Speckit CLI is installed in copilotcompanion env
pip install speckit  # or invoke from other location
```

**Issue**: Git errors when committing spec
```bash
# Solution: Configure Git identity
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

## Contributing

When making changes to this POC:

1. Update spec at `specs/001-spec-generator/spec.md` if requirements change
2. Test locally with multiple requirement inputs
3. Commit all changes to `001-spec-generator` branch
4. Document findings in PR description
5. Reference spec success criteria when testing

## References

- **Constitution**: [.specify/memory/constitution.md](.specify/memory/constitution.md)
- **Specification**: [specs/001-spec-generator/spec.md](specs/001-spec-generator/spec.md)
- **Streamlit Docs**: https://docs.streamlit.io
- **Speckit**: [To be linked when available]

---

**Status**: 🟢 POC Ready for Testing  
**Last Updated**: 2026-02-12  
**Maintained By**: Copilot SDLC Team
