● Get current date
  $ date +%Y-%m-%d
  └ 2 lines...

# Implementation Plan: Address Book

**Branch**: `001-address-book` | **Date**: `2026-02-20` | **Spec**: `/specs/001-address-book/spec.md`
**Input**: Feature specification from `/specs/001-address-book/spec.md`

---

## Summary

The Address Book feature enables users to create, search, view, edit, delete, and organize personal and business contacts. Each contact stores a name, one or more phone numbers and email addresses (with labels), a physical address, and free-text notes. Contacts can be grouped into named categories and filtered accordingly. The system is built as a web application with a Python-powered API layer handling all data operations and a Next.js front end delivering the user interface.

---

## Technical Context

**Language/Version**: Python 3.12 (API) · Node.js 20 LTS (Front End)
**Primary Dependencies**: Python REST API framework · Next.js 14
**Storage**: Relational database (PostgreSQL)
**Testing**: Python test runner (API) · JavaScript test runner (Front End)
**Target Platform**: Web browser (desktop-first, mobile-responsive)
**Project Type**: Web — separate backend API + Next.js frontend
**Performance Goals**: Search results returned within 500 ms of last keystroke; contact list of 1,000+ contacts renders and scrolls within 2 seconds
**Constraints**: Zero data loss across sessions; duplicate detection on 100% of matching full-name + primary-phone pairs; all form validation feedback presented before submission
**Scale/Scope**: Supports a minimum of 10,000 contacts per user without degraded performance; multi-user capable

---

## Constitution Check

| Gate | Status | Notes |
|------|--------|-------|
| Feature spec exists and is approved | ✅ Pass | spec.md present, status Draft — confirm stakeholder sign-off before Phase 1 |
| All P1 user stories have acceptance scenarios | ✅ Pass | User Story 1 fully defined |
| All functional requirements are traceable to user stories | ✅ Pass | FR-001 through FR-018 mapped |
| Open clarifications resolved before build | ⚠️ Pending | FR-015 (max contacts), FR-017 (export formats), FR-018 (field character limits) require answers |
| No orphaned requirements | ✅ Pass | All requirements link to at least one acceptance scenario |

*Re-check after Phase 1 design is complete.*

---

## Project Structure

### Documentation (this feature)

```text
specs/001-address-book/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API contracts per resource)
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created here)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/          # Contact, PhoneNumber, EmailAddress, Address, Group
│   ├── services/        # Business logic: contacts, search, groups, duplicates
│   └── api/             # REST endpoints: /contacts, /groups, /search
└── tests/
    ├── unit/
    ├── integration/
    └── contract/

frontend/
├── src/
│   ├── components/      # ContactCard, ContactForm, SearchBar, GroupFilter, ConfirmDialog
│   ├── pages/           # Contact list, contact detail, add/edit contact, groups
│   └── services/        # API client wrappers
└── tests/
    ├── unit/
    └── integration/
```

**Structure Decision**: Web application with two top-level projects — `backend/` for the Python API and `frontend/` for the Next.js application. They communicate exclusively through the defined API contracts. No shared source code between the two projects.

---

## Phase 0 — Research Questions

The following must be answered before design begins:

| # | Question | Owner | Blocks |
|---|----------|-------|--------|
| R-01 | What is the maximum number of contacts the system must support per user? (FR-015) | Product | FR-015, SC-004 |
| R-02 | Which export formats are required — vCard, CSV, both, or other? (FR-017) | Product | FR-017 |
| R-03 | What are the maximum character limits for each text field — e.g., name, notes, street address? (FR-018) | Product | FR-018 |
| R-04 | Must the address book support multiple users, or is it single-user only in this release? | Product | Architecture |
| R-05 | Are there accessibility requirements (e.g., WCAG 2.1 AA)? | Product | Front End design |
| R-06 | Must contacts be importable from external sources (e.g., vCard, CSV) in this release? | Product | FR scope |

---

## Phase 1 — Design Deliverables

### Data Model (`data-model.md`)

The following entities must be fully specified before any build work begins:

| Entity | Key Attributes | Relationships |
|--------|---------------|---------------|
| **Contact** | unique ID, first name, last name, notes, created date, modified date | owns many PhoneNumbers, EmailAddresses, one Address, belongs to many Groups |
| **PhoneNumber** | unique ID, number value, label (Mobile / Home / Work), is-primary flag | belongs to one Contact |
| **EmailAddress** | unique ID, email value, label (Personal / Work), is-primary flag | belongs to one Contact |
| **Address** | unique ID, street line 1, street line 2 (optional), city, state/province, postal code, country | belongs to one Contact |
| **Group** | unique ID, group name | has many Contacts; a Contact belongs to zero or more Groups |

### API Contracts (`contracts/`)

One contract file per resource. Each contract defines:
- All request and response fields
- Validation rules (required fields, formats, character limits)
- Success and error response shapes
- Duplicate detection behavior

Contracts cover: `POST /contacts`, `GET /contacts`, `GET /contacts/{id}`, `PUT /contacts/{id}`, `DELETE /contacts/{id}`, `GET /contacts/search`, `POST /groups`, `GET /groups`, `PUT /groups/{id}`, `DELETE /groups/{id}`, `GET /contacts/export`

### Quickstart (`quickstart.md`)

Step-by-step instructions for a developer to run both backend and frontend locally from a clean checkout, including how to seed sample contacts for manual testing.

---

## Phase 2 — Feature Requirements Checklist

All items below must be satisfied before the feature is considered complete.

### Contact Creation (P1)
- [ ] A contact can be saved with first name, last name, one phone number, one email, and a full address
- [ ] Saving without a first name or last name is blocked with a user-visible error
- [ ] An invalid phone number format is rejected before submission
- [ ] An invalid email format (missing `@` or domain) is rejected before submission
- [ ] A new contact appears in the contact list immediately after saving

### Search (P2)
- [ ] Typing a partial first or last name filters the contact list in real time (within 500 ms)
- [ ] Searching by phone number or partial phone number returns matching contacts
- [ ] A search with no matches shows a clear "no contacts found" message
- [ ] Clearing the search field restores the full contact list
- [ ] Searching when the address book is empty shows "address book is empty" — not a generic no-results message

### Contact Detail View (P2)
- [ ] Selecting a contact displays all stored fields on one screen
- [ ] Multiple phone numbers and email addresses are shown with their labels
- [ ] Blank optional fields are hidden or clearly marked as not provided

### Contact Editing (P3)
- [ ] Any field of an existing contact can be updated and saved
- [ ] Removing the last name so no name remains is blocked with a user-visible error
- [ ] Discarding edits without saving preserves the original contact data

### Contact Deletion (P3)
- [ ] Deleting a contact requires a confirmation step
- [ ] After confirmed deletion, the contact no longer appears in the list or search results
- [ ] Cancelling deletion leaves the contact unchanged
- [ ] A success confirmation is shown after deletion completes

### Groups (P4)
- [ ] A user can create a named group and assign contacts to it
- [ ] Filtering by a group shows only contacts in that group
- [ ] A contact belonging to multiple groups shows all group names on its detail view
- [ ] Deleting a group does not delete the contacts it contained

### Data Integrity & Edge Cases
- [ ] All contact data persists across browser sessions (close and reopen)
- [ ] A potential duplicate (same full name AND same primary phone number) triggers a warning before saving — not a block
- [ ] Phone numbers entered with spaces, dashes, or parentheses are normalized for storage and display
- [ ] Each text field enforces a maximum character limit; entering beyond the limit is rejected with a message
- [ ] The contact list of 1,000+ contacts loads and scrolls within 2 seconds
- [ ] Sorting by first name and by last name both work correctly

### Export (P4 — pending format clarification)
- [ ] Contact list can be exported to a portable format (vCard and/or CSV — to be confirmed)
- [ ] Any import of contacts from an external file flags or skips records with missing required fields rather than importing silently

---

## Success Criteria Verification

| ID | Criterion | How Verified |
|----|-----------|-------------|
| SC-001 | New contact created in under 90 seconds | Timed usability test with 5 participants on blank form |
| SC-002 | Contact located from 200+ contacts in under 10 seconds via search | Timed test with seeded dataset of 200 contacts |
| SC-003 | 95% of users complete add → find → view on first attempt | Unmoderated usability study, first-attempt success rate |
| SC-004 | Contact list with 1,000+ contacts renders within 2 seconds | Performance test with 1,000-contact dataset; measured in browser |
| SC-005 | Zero data loss across sessions | Automated test: save contacts, close session, reopen, verify all records intact |
| SC-006 | Duplicate warning shown 100% of the time for matching name + phone | Automated test: insert duplicate, verify warning appears before save |
| SC-007 | Search results appear within 500 ms of last keystroke | Automated performance test measuring API response time + render time |
| SC-008 | 90% of users rate usability 4/5 or higher | Post-task survey distributed after usability study |

---

## Open Items

| ID | Item | Status |
|----|------|--------|
| OI-01 | Maximum contact capacity per user (FR-015) | ⏳ Awaiting product decision |
| OI-02 | Export formats: vCard, CSV, or both (FR-017) | ⏳ Awaiting product decision |
| OI-03 | Maximum character limits per field (FR-018) | ⏳ Awaiting product decision |
| OI-04 | Single-user vs. multi-user scope for this release | ⏳ Awaiting product decision |
| OI-05 | Accessibility compliance target (e.g., WCAG 2.1 AA) | ⏳ Awaiting product decision |
| OI-06 | Contact import from external file: in scope for this release? | ⏳ Awaiting product decision |