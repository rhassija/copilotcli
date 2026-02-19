# Plan.md & Tasks.md Generation Guide

## ✅ Implementation Status

**All generation endpoints are now fully functional:**

- ✅ **Spec Generation** - `/api/v1/features/{id}/generate-spec`
- ✅ **Plan Generation** - `/api/v1/features/{id}/generate-plan`
- ✅ **Task Generation** - `/api/v1/features/{id}/generate-task`

## 🎯 User Workflow

### How to Generate Documents

1. **Create a Feature**
   - Login to the web UI (http://localhost:3000)
   - Select a repository from the left panel
   - Click "Create Feature" button
   - Enter feature title and branch name
   - Feature is created with empty spec.md, plan.md, tasks.md

2. **Navigate to Editor**
   - Click "Edit" on any feature in the feature list
   - You'll see three tabs: **Specification**, **Plan**, **Tasks**

3. **Generate Spec (First)**
   - Stay on the "Specification" tab
   - Click the **🤖 Generate** button
   - Enter your requirement description (what you want to build)
   - Enable Copilot (recommended) or use template fallback
   - Wait 7-10 minutes for generation (progress shown)
   - Click **💾 Save** when generation completes

4. **Generate Plan (Second)**
   - Switch to the "Plan" tab
   - Click the **🤖 Generate** button
   - Enter additional context or leave empty (will use spec)
   - Enable Copilot
   - Wait 5-7 minutes for generation
   - Click **💾 Save** when done

5. **Generate Tasks (Third)**
   - Switch to the "Tasks" tab
   - Click the **🤖 Generate** button
   - Enter additional context or leave empty (will use spec + plan)
   - Enable Copilot
   - Wait 5-7 minutes for generation
   - Click **💾 Save** when done

## 🔧 Technical Details

### Backend Endpoints

All endpoints follow the same pattern:

```
POST /api/v1/features/{feature_id}/generate-{docType}

Request Body:
{
  "requirement_description": "Your feature description",
  "enable_copilot": true,
  "copilot_model": "gpt-4" (optional),
  "include_context": true
}

Response:
{
  "content": "Generated markdown content",
  "used_copilot": true,
  "model_used": "gpt-4",
  "message": "Document generated successfully"
}
```

### Context Propagation

- **Spec**: Uses only the requirement description
- **Plan**: Uses requirement + spec content (if available)
- **Tasks**: Uses requirement + spec content + plan content (if available)

### Templates

Located in `.specify/templates/`:
- `spec-template.md` - Specification template
- `plan-template.md` - Implementation plan template
- `tasks-template.md` - Task breakdown template

### Copilot CLI Integration

The system uses the real Copilot CLI installed in VS Code:
- Path: `~/Library/Application Support/Code/User/globalStorage/github.copilot-chat/copilotCli/copilot`
- Token injection: Handled via environment variables
- Timeout: 10 minutes frontend, unlimited backend
- Fallback: Template-based generation if Copilot fails

## 🧪 Testing Checklist

### Manual Testing Steps

- [ ] Create a new feature via UI
- [ ] Verify spec.md, plan.md, tasks.md are created (empty)
- [ ] Open editor and see all three tabs
- [ ] Generate spec with Copilot enabled
  - [ ] Verify generation completes without timeout
  - [ ] Verify content is enriched (not just template)
  - [ ] Click Save and verify GitHub file is updated
- [ ] Generate plan with Copilot enabled
  - [ ] Verify plan uses spec as context
  - [ ] Verify generation completes
  - [ ] Click Save and verify GitHub file is updated
- [ ] Generate tasks with Copilot enabled
  - [ ] Verify tasks use spec + plan as context
  - [ ] Verify generation completes
  - [ ] Click Save and verify GitHub file is updated
- [ ] Switch between tabs
  - [ ] Verify unsaved changes indicator works
  - [ ] Verify tab switching preserves content
- [ ] Test without Copilot (template fallback)
  - [ ] Generate spec with Copilot disabled
  - [ ] Verify template-based content is generated

### Expected Results

**With Copilot Enabled:**
- Spec: Comprehensive feature specification with sections
- Plan: Detailed implementation plan with architecture, tech stack, milestones
- Tasks: Actionable task breakdown with dependencies and priorities

**Without Copilot (Template Fallback):**
- Spec: Basic template with placeholders
- Plan: Basic template with section headers
- Tasks: Basic checklist template

## 🐛 Troubleshooting

### Generation Times Out
- **Cause**: Complex requirements or slow Copilot response
- **Solution**: Frontend timeout is now 10 minutes (600 seconds)
- **Workaround**: Simplify requirement description or disable Copilot

### Copilot Not Available
- **Check**: Backend logs for "Copilot CLI not found" warning
- **Verify**: Run `ls -la ~/Library/Application\ Support/Code/User/globalStorage/github.copilot-chat/copilotCli/copilot`
- **Fallback**: Disable Copilot to use template-based generation

### Content Not Saved
- **Symptom**: Green success message appears but GitHub file not updated
- **Check**: Backend logs for GitHub API errors
- **Verify**: Check GitHub PAT has write permissions
- **Debug**: Check feature persistence in `backend/.data/features/`

### Plan/Task Generation Doesn't Use Context
- **Cause**: `include_context: true` not sent or spec/plan not saved
- **Solution**: Always save documents before generating next one
- **Verify**: Check backend logs for "Loaded spec context" messages

## 📝 Recently Fixed Issues

### 2026-02-19: Endpoint Naming Fixed
- **Issue**: Backend had `/generate-tasks` (plural) but frontend called `/generate-task` (singular)
- **Fix**: Changed backend route from `generate-tasks` to `generate-task` for consistency
- **Files Modified**: `backend/src/api/documents.py`

### 2026-02-19: Timeout Increased
- **Issue**: Spec generation took 7-10 minutes but frontend timeout was 90 seconds
- **Fix**: Increased frontend timeout to 600 seconds (10 minutes)
- **Files Modified**: `frontend/src/components/DocumentEditors/DocumentEditor.tsx`

### 2026-02-19: Port Configuration Fixed
- **Issue**: Frontend targeting port 8000 but backend running on 8001
- **Fix**: Updated `.env.local` to use `http://localhost:8001`
- **Files Modified**: `frontend/.env.local`

## 📚 Related Documentation

- [tasks.md](specs/009-redesigned-workflow-ux/tasks.md) - Implementation task list
- [plan.md](specs/009-redesigned-workflow-ux/plan.md) - Architecture and tech stack
- [TESTING-GUIDE.md](TESTING-GUIDE.md) - Comprehensive testing guide

## 🚀 Next Steps

1. **Automated Testing** (Phase 4 Testing: T102-T107, T128-T134)
   - Contract tests for generation endpoints
   - Integration tests for full workflow
   - E2E tests with Playwright

2. **UI Enhancements** (Phase 5: Optional)
   - Real-time progress indicator during generation
   - WebSocket streaming of Copilot CLI output
   - Preview comparison (before/after generation)

3. **Production Hardening** (Phase 7: Polish)
   - Async generation with background jobs
   - Retry logic for transient failures
   - Rate limiting for Copilot API calls
