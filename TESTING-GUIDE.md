# POC Testing Guide - 001-spec-generator

## 📋 Overview

This guide walks you through testing the Copilot SDLC Platform POC. Follow each test scenario to validate the implementation against the specification.

**Status**: App running at `http://localhost:8501`  
**Environment**: copilotcompanion (Python 3.13.11)  
**Duration**: ~10-15 minutes for all tests

---

## ✅ Test 1: Basic UI Load & Layout

### Steps
1. Open `http://localhost:8501` in browser (should already be open)
2. Observe page load

### Expected Results
- ✅ Page title: "🚀 Copilot SDLC - Spec Generator POC"
- ✅ Subtitle: "Natural Language → Specification Generation (Constitution v1.0.1)"
- ✅ Left column: Input area + Activity log
- ✅ Right column: Status + Spec viewer
- ✅ Sidebar: POC info, configuration, how-it-works guide

### Test Result
- [ ] Pass
- [ ] Fail

**Notes**: _______________________________________________________________________________________

---

## ✅ Test 2: Input Validation - Empty Requirement

### Steps
1. Leave the requirement text area empty
2. Click "📤 Submit Requirement" button

### Expected Results
- ✅ Validation error appears: "Error: Requirement cannot be empty"
- ✅ Button is disabled during processing (should have re-enabled immediately since validation failed)
- ✅ No activity log updates (or only shows validation message)
- ✅ No spec file created

### Test Result
- [ ] Pass
- [ ] Fail

**Notes**: _______________________________________________________________________________________

---

## ✅ Test 3: Input Validation - Whitespace Only

### Steps
1. Type only spaces/tabs in the requirement field
2. Click "📤 Submit Requirement" button

### Expected Results
- ✅ Validation error similar to Test 2
- ✅ System treats whitespace-only as empty

### Test Result
- [ ] Pass
- [ ] Fail

**Notes**: _______________________________________________________________________________________

---

## ✅ Test 4: Basic Requirement Submission (P1 Story)

### Steps
1. Enter requirement: `"Create a simple login page"`
2. Click "📤 Submit Requirement" button
3. Watch the Activity pane for 5-10 seconds
4. Wait for completion status

### Expected Results
- ✅ Button becomes disabled during processing
- ✅ Activity log shows agent activity:
  - "Preparing specification generation..."
  - "Executing /specify command..."
  - Command output lines
- ✅ Activity pane auto-scrolls to show latest messages
- ✅ Final status message appears: "✅ Specification generated successfully"
- ✅ Spec viewer populates with markdown spec (on right side)
- ✅ Spec contains:
  - User stories
  - Functional requirements
  - Success criteria

### Timeline Goals
- ✅ Processing completes within 2 minutes (SC-001)
- ✅ Activity updates appear within 500ms of action (SC-002)

### Test Result
- [ ] Pass
- [ ] Fail (describe): _________________________________________________________________

**Notes**: _______________________________________________________________________________________

---

## ✅ Test 5: Real-Time Activity Streaming (P1 Story)

### Steps
1. Click "🔄 Clear Activity Log" in sidebar
2. Enter requirement: `"Build a multi-tenant SaaS dashboard with real-time analytics"`
3. Observe Activity pane closely as it processes

### Expected Results
- ✅ Activity log clears completely
- ✅ First message appears within 500ms of click (SC-002)
- ✅ Messages appear line-by-line (not all at once)
- ✅ Activity pane has scrollbar and auto-scrolls
- ✅ Each new line appears in its own code block
- ✅ No buffering delays visible (smooth streaming)

### Test Result
- [ ] Pass
- [ ] Fail

**Notes**: _______________________________________________________________________________________

---

## ✅ Test 6: Specification Content Quality (SC-003)

### Steps
1. From Test 4, review the generated spec.md in the Spec Viewer
2. Read it as if you were a non-technical business user
3. Answer: Can you understand what will be built?

### Expected Results
- ✅ Spec title matches your input requirement
- ✅ User stories are in plain English (not code)
- ✅ Functional requirements are readable (no technical jargon)
- ✅ Success criteria are measurable
- ✅ A business user (non-tech) could understand the spec
- ✅ Spec file exists: `specs/001-spec-generator/spec.md`

### Readability Assessment (SC-003)
- Is the spec understandable to non-tech users? **Yes / No**
- Does it require technical knowledge to understand? **Yes / No**
- Rate clarity 1-5: _______

### Test Result
- [ ] Pass
- [ ] Fail

**Notes**: _______________________________________________________________________________________

---

## ✅ Test 7: Multiple Requirement Inputs (SC-004)

### Instructions
Run **3 different requirement inputs** to validate robustness. For each:

### Test 7a: Simple Feature
**Requirement**: `"Create a user profile page"`

- [ ] Processing succeeds
- [ ] Spec generates
- [ ] Contains user stories
- **Result**: Pass / Fail

### Test 7b: Complex Feature
**Requirement**: `"Implement an e-commerce platform with shopping cart, checkout, payment processing, order history, and admin dashboard"`

- [ ] Processing succeeds (even with complex input)
- [ ] Spec generates with multiple user stories
- [ ] Captures all components mentioned
- **Result**: Pass / Fail

### Test 7c: Vague Requirement
**Requirement**: `"Improve the system"`

- [ ] Processing succeeds (even with ambiguous input)
- [ ] Spec generates (may request clarification in SC-003 review)
- [ ] System handles gracefully
- **Result**: Pass / Fail

### SC-004 Assessment
- [ ] At least 1 test case passes
- [ ] At least 2 test cases pass
- [ ] All 3 test cases pass ✅ (meets SC-004)

---

## ✅ Test 8: Spec Update Workflow (P2 Story) (SC-005)

### Steps
1. From Test 4, you have a spec for "Create a simple login page"
2. In the requirement field, enter a modification: `"Create a simple login page with password reset capability"`
3. Click "📤 Submit Requirement"
4. Wait for processing to complete

### Expected Results
- ✅ System executes new `/specify` command
- ✅ Activity log shows new processing
- ✅ Updated spec.md is generated
- ✅ Updated spec now includes password reset feature
- ✅ Completion within 2 minutes (SC-005)
- ✅ Spec file modified: `specs/001-spec-generator/spec.md` (check Git history)

### Test Result
- [ ] Pass
- [ ] Fail

**Notes**: _______________________________________________________________________________________

---

## ✅ Test 9: Error Handling - Timeout Simulation

### Steps
1. This test checks if system handles slowness gracefully
2. Monitor activity log for any error messages if processing takes >2 minutes
3. Try clicking Submit again if it appears stuck

### Expected Results
- ✅ If processing takes >2 min: timeout message appears (or clear "still processing" message)
- ✅ No hang or UI freeze
- ✅ Clear error message (not technical stack trace)
- ✅ User can retry or clear

### Test Result
- [ ] Pass (completed quickly)
- [ ] Pass (graceful timeout handling)
- [ ] Fail

**Notes**: _______________________________________________________________________________________

---

## ✅ Test 10: UI Responsiveness During Processing

### Steps
1. Submit a requirement
2. While processing, try clicking buttons/scrolling/interacting

### Expected Results
- ✅ UI remains responsive (no freezing)
- ✅ "Submit" button disabled during processing (cannot double-submit)
- ✅ Can scroll through activity log while processing
- ✅ Sidebar elements remain functional
- ✅ Spec viewer shows content as it's generated

### Test Result
- [ ] Pass
- [ ] Fail

**Notes**: _______________________________________________________________________________________

---

## ✅ Test 11: Git Integration Verification

### Steps
1. After completing Test 4, open terminal
2. Check Git status for `specs/001-spec-generator/spec.md`

### Commands
```bash
# Check if file exists and was modified
ls -la specs/001-spec-generator/spec.md

# View recent commits
git log --oneline -5 specs/001-spec-generator/

# View spec content
cat specs/001-spec-generator/spec.md | head -30
```

### Expected Results
- ✅ File exists at `specs/001-spec-generator/spec.md`
- ✅ File was recently modified (timestamp current)
- ✅ File contains the generated specification
- ✅ File has valid markdown syntax

### Test Result
- [ ] Pass
- [ ] Fail

**Notes**: _______________________________________________________________________________________

---

## ✅ Test 12: Non-Tech User Perspective (SC-003 Deep Dive)

### Steps
1. Generate a spec (reuse Test 4 output)
2. Show the spec.md file to a non-technical person (or judge yourself)
3. Ask them to identify:
   - What is being built?
   - What are the main requirements?
   - How would they know when it's complete?

### Expected Results
- ✅ Non-tech user can answer all 3 questions without technical help
- ✅ No requirement for them to understand code/APIs/databases
- ✅ Spec is in plain English
- ✅ User stories are relatable

### Questions for Non-Tech User
1. **What feature will we build?**: _______________________________________________________
2. **What are the main requirements?**: _________________________________________________
3. **How do you know when it's done?**: ________________________________________________

### Understanding Level
- [ ] Clear & comprehensible
- [ ] Mostly clear (minor clarifications needed)
- [ ] Unclear (too technical)

### Test Result
- [ ] Pass
- [ ] Fail

**Notes**: _______________________________________________________________________________________

---

## 📊 Test Summary

### Coverage

| Test # | Feature | Status | Notes |
|--------|---------|--------|-------|
| 1 | UI Layout | [ ] ✅ / [ ] ❌ | |
| 2 | Empty Validation | [ ] ✅ / [ ] ❌ | |
| 3 | Whitespace Validation | [ ] ✅ / [ ] ❌ | |
| 4 | Basic Submission (P1) | [ ] ✅ / [ ] ❌ | |
| 5 | Real-Time Activity (P1) | [ ] ✅ / [ ] ❌ | |
| 6 | Content Quality (SC-003) | [ ] ✅ / [ ] ❌ | |
| 7 | Multiple Inputs (SC-004) | [ ] ✅ / [ ] ❌ | |
| 8 | Spec Updates (P2) | [ ] ✅ / [ ] ❌ | |
| 9 | Error Handling (SC-006) | [ ] ✅ / [ ] ❌ | |
| 10 | UI Responsiveness | [ ] ✅ / [ ] ❌ | |
| 11 | Git Integration | [ ] ✅ / [ ] ❌ | |
| 12 | Non-Tech User View (SC-003) | [ ] ✅ / [ ] ❌ | |

### Success Criteria Validation

| Criterion | Test # | Status | Notes |
|-----------|--------|--------|-------|
| SC-001: <2 min workflow | 4, 8 | [ ] ✅ / [ ] ❌ | _______________ |
| SC-002: Real-time <500ms | 5 | [ ] ✅ / [ ] ❌ | _______________ |
| SC-003: Non-tech readable | 6, 12 | [ ] ✅ / [ ] ❌ | _______________ |
| SC-004: 3+ test inputs | 7a, 7b, 7c | [ ] ✅ / [ ] ❌ | _______________ |
| SC-005: Update workflow | 8 | [ ] ✅ / [ ] ❌ | _______________ |
| SC-006: Error handling | 9 | [ ] ✅ / [ ] ❌ | _______________ |
| SC-007: <5 min demo | All | [ ] ✅ / [ ] ❌ | _______________ |

### Overall Result

**Total Tests Passed**: _____ / 12  
**Success Criteria Met**: _____ / 7  

#### Overall Status
- [ ] 🟢 **READY FOR PHASE 1** (11-12 tests pass, 6-7 success criteria met)
- [ ] 🟡 **NEEDS MINOR FIXES** (8-10 tests pass, 5-6 success criteria met)
- [ ] 🔴 **NEEDS MAJOR REWORK** (<8 tests pass, <5 success criteria met)

---

## 📝 Findings & Feedback

### What Worked Well
1. _________________________________________________________________
2. _________________________________________________________________
3. _________________________________________________________________

### Issues Found
1. **Issue**: ___________________________________________________________________
   **Severity**: [ ] Critical [ ] Major [ ] Minor  
   **Reproduction**: _____________________________________________________________
   **Fix**: _________________________________________________________________

2. **Issue**: ___________________________________________________________________
   **Severity**: [ ] Critical [ ] Major [ ] Minor  
   **Reproduction**: _____________________________________________________________
   **Fix**: _________________________________________________________________

### Suggestions for Phase 1
1. _________________________________________________________________
2. _________________________________________________________________
3. _________________________________________________________________

---

## ✅ Sign-Off

**Tester**: _______________________________  
**Date**: _______________________________  
**Environment**: copilotcompanion (Python 3.13.11, Streamlit 1.54.0)  

**Approval for Phase 1**: [ ] YES - Proceed | [ ] NO - Address issues first

---

## 🚀 Ready for Phase 1?

If you answered **YES** to the approval question, Phase 1 includes:

- [ ] Real `/specify` command integration (currently stubbed)
- [ ] Approval workflow (approve/request-changes buttons)
- [ ] GitHub authentication
- [ ] Spec version history viewer
- [ ] Feedback collection from stakeholders

Next step: Discuss Phase 1 roadmap and priorities.

---

**Testing Guide v1.0**  
**Generated**: 2026-02-12  
**Related Docs**: specs/001-spec-generator/spec.md, POC-README.md
