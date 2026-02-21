✗ Check existing spec files
  $ ls /Users/rajeshhassija/Documents/GitHub/copilotcli/.specify/memory/ 2>/dev/null && ls
  /Users/rajeshhassija/Documents/GitHub/copilotcli/specs/001-address-book/ 2>/dev/null || echo "no
  specs dir"
  Permission denied and could not request permission from user

● Glob "**/*" in /Users/rajeshhassija/Documents/GitHub/copilotcli/.specify
  └ 12 files found

✗ Glob "specs/**/*" in /Users/rajeshhassija/Documents/GitHub/copilotcli
  └ Permission denied and could not request permission from user

Based on the full specification and plan provided, here is the completed tasks.md:

---

# Tasks: Address Book

**Input**: Design documents from `/specs/001-address-book/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md (Phase 0 open items pending), data-model.md (Phase 1), contracts/ (Phase 1)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2…)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure — no user stories depend directly on this, but it gates all later work.

- [ ] T001 Create top-level folder structure: `backend/` for the API layer, `frontend/` for the user interface, and `specs/001-address-book/` for design documents
- [ ] T002 Initialize the back-end project with the chosen language and framework dependencies, configured to run locally on a known port
- [ ] T003 [P] Initialize the front-end project with the chosen framework dependencies, configured to communicate with the back-end API on its local port
- [ ] T004 [P] Configure code style and formatting rules for both back-end and front-end projects
- [ ] T005 [P] Create a `.env.example` file documenting every required environment variable (database connection, ports, etc.) — no real secrets committed
- [ ] T006 Author `quickstart.md` with step-by-step instructions for running both projects locally from a clean checkout, including how to seed 20 sample contacts for manual testing

**Checkpoint**: A developer can clone the repository, follow `quickstart.md`, and see both the back-end and front-end start without errors.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T007 Define the relational database schema covering all five entities — Contact, PhoneNumber, EmailAddress, Address, Group — including their fields, data types, required/optional flags, and relationships as specified in `data-model.md`
- [ ] T008 Set up the database migration tooling so schema changes can be applied and rolled back repeatably
- [ ] T009 [P] Define the API routing structure with one route file per resource: `/contacts`, `/groups`, `/search`, `/contacts/export`
- [ ] T010 [P] Implement a consistent error-response format used by every API endpoint (validation errors, not-found errors, server errors)
- [ ] T011 [P] Implement request logging so every inbound API call and its outcome is recorded
- [ ] T012 Configure environment-based settings so the application reads database credentials, port numbers, and feature flags from environment variables — not hardcoded values
- [ ] T013 Create the five base data models (Contact, PhoneNumber, EmailAddress, Address, Group) wired to the database schema from T007

**Checkpoint**: Foundation ready — the database is reachable, all five models exist, API routing responds to requests, and errors return a consistent shape. User story implementation can now begin.

---

## Phase 3: User Story 1 — Add a New Contact (Priority: P1) 🎯 MVP

**Goal**: A user can fill out a contact form with name, phone, email, and address and save a new contact that immediately appears in the contact list.

**Independent Test**: Add a single contact with all required fields filled in, save it, and confirm it appears in the contact list with every entered value intact. Then attempt to save without a name, with a bad phone number, and with a malformed email — confirm each is rejected with a clear message.

### Back-End — Contact Creation

- [ ] T014 [P] [US1] Implement the `POST /contacts` API endpoint that accepts a contact payload and writes a new Contact record plus its associated PhoneNumbers, EmailAddresses, and Address to the database
- [ ] T015 [P] [US1] Implement validation rules for `POST /contacts`: first name required, last name required, at least one phone number required, phone number must contain only digits and recognized separators, email must contain `@` and a domain — return field-level error messages for each violation
- [ ] T016 [US1] Implement duplicate-detection logic: before saving, check whether a contact with the same full name AND same primary phone number already exists; if so, return a warning response (not a hard block) so the front end can prompt the user to confirm
- [ ] T017 [US1] Implement phone-number normalization: strip spaces, dashes, and parentheses from stored and displayed values consistently

### Front-End — Contact Creation

- [ ] T018 [P] [US1] Build the Add Contact screen containing fields for: first name, last name, one or more phone numbers (each with a Mobile / Home / Work label selector), one or more email addresses (each with a Personal / Work label selector), street line 1, street line 2 (optional), city, state/province, postal code, country, and a free-text notes field
- [ ] T019 [US1] Wire the Add Contact form to `POST /contacts`; display field-level validation messages returned by the API inline next to the offending field before the form is submitted
- [ ] T020 [US1] Display a confirmation dialog when the API returns a duplicate-detection warning, giving the user the choice to save anyway or cancel
- [ ] T021 [US1] On successful save, navigate the user to the contact list and ensure the new contact is visible without a manual page reload
- [ ] T022 [US1] Enforce a maximum character limit on every text field in the form; display a character-count indicator or error message when the limit is reached

**Checkpoint**: User Story 1 is fully functional. A user can add a contact, see validation errors on bad input, receive a duplicate warning when applicable, and confirm the new contact appears in the list after saving.

---

## Phase 4: User Story 2 — Search and Find a Contact (Priority: P2)

**Goal**: A user can type into a search field and see a filtered list of matching contacts in real time, without scrolling through all contacts.

**Independent Test**: Seed the address book with 10 contacts with distinct names. Type a partial first name — confirm only matching contacts appear. Search by partial phone number — confirm matching contacts appear. Clear the field — confirm the full list returns. Search for a name that does not exist — confirm a "no contacts found" message appears.

### Back-End — Search

- [ ] T023 [P] [US2] Implement the `GET /contacts/search` endpoint accepting a `query` parameter and returning contacts whose first name, last name, phone number, or email address contains the search string; results must be returned within 500 ms for a dataset of 1,000+ contacts
- [ ] T024 [US2] Add a database index on the fields used for search (first name, last name, phone number, email) to meet the 500 ms response-time target

### Front-End — Search

- [ ] T025 [P] [US2] Add a search bar to the contact list screen that calls `GET /contacts/search` as the user types, with a debounce so the API is not called on every keystroke
- [ ] T026 [US2] Display search results within 500 ms of the user's last keystroke; show a loading indicator if the response takes longer
- [ ] T027 [US2] Show a "no contacts found" message when a search returns zero results
- [ ] T028 [US2] Show an "address book is empty" message (distinct from the no-results message) when the address book contains zero contacts and a search is performed
- [ ] T029 [US2] Restore the full contact list when the search field is cleared

**Checkpoint**: User Stories 1 and 2 both work independently. A user can add contacts and then find them by name or phone number using the search bar.

---

## Phase 5: User Story 3 — View Contact Details (Priority: P2)

**Goal**: A user selects a contact and sees all stored fields displayed in a clear, organized layout on a single screen.

**Independent Test**: Select a previously saved contact and confirm every entered field is displayed — name, all phone numbers with labels, all emails with labels, full address, and notes. Confirm that blank optional fields are either hidden or marked as "not provided."

### Back-End — Contact Detail

- [ ] T030 [P] [US3] Implement the `GET /contacts/{id}` endpoint returning all fields for a single contact, including all associated phone numbers with labels, all email addresses with labels, the physical address, and notes

### Front-End — Contact Detail

- [ ] T031 [P] [US3] Build the Contact Detail screen displaying: full name, all phone numbers with their labels (Mobile / Home / Work) and a primary indicator, all email addresses with their labels (Personal / Work) and a primary indicator, full physical address, notes, and the date last modified
- [ ] T032 [US3] When a field was left blank at creation, either hide it entirely or display a clearly worded "not provided" indicator — do not show blank lines
- [ ] T033 [US3] Make the Contact Detail screen navigable from the contact list by tapping or clicking a contact row

**Checkpoint**: User Stories 1, 2, and 3 all work independently. A user can add a contact, find it by search, and view its full details.

---

## Phase 6: User Story 4 — Edit an Existing Contact (Priority: P3)

**Goal**: A user can update any field of a saved contact and save the changes, or discard changes and leave the contact unchanged.

**Independent Test**: Open a saved contact, change the phone number, save, and confirm the new number appears on the detail view and the old number is gone. Then open a contact, clear both name fields, attempt to save — confirm it is blocked. Then open a contact, make a change, and discard — confirm the original data is intact.

### Back-End — Contact Editing

- [ ] T034 [P] [US4] Implement the `PUT /contacts/{id}` endpoint that accepts an updated contact payload, validates it using the same rules as creation (name required, phone format, email format), and writes the changes to the database
- [ ] T035 [US4] Ensure `PUT /contacts/{id}` rejects a payload where both first name and last name are blank, returning a clear field-level error

### Front-End — Contact Editing

- [ ] T036 [P] [US4] Add an Edit button on the Contact Detail screen that opens the same form used for creation, pre-populated with the contact's current values
- [ ] T037 [US4] Wire the edit form to `PUT /contacts/{id}`; display field-level validation errors inline as on the creation form
- [ ] T038 [US4] Add a Discard Changes option (button or navigation back) that returns the user to the unmodified contact detail view without saving
- [ ] T039 [US4] After a successful save, return the user to the Contact Detail screen showing the updated values

**Checkpoint**: User Stories 1–4 all work independently. A user can create, find, view, and update a contact.

---

## Phase 7: User Story 5 — Delete a Contact (Priority: P3)

**Goal**: A user can permanently remove a contact, with a confirmation step to prevent accidental deletion.

**Independent Test**: Delete a saved contact — confirm a confirmation dialog appears. Confirm deletion — confirm the contact is gone from the list and from search results, and a success message appears. Repeat but cancel at the confirmation step — confirm the contact remains unchanged.

### Back-End — Contact Deletion

- [ ] T040 [P] [US5] Implement the `DELETE /contacts/{id}` endpoint that permanently removes the contact and all its associated phone numbers, email addresses, and address records from the database
- [ ] T041 [US5] Ensure the `DELETE` endpoint returns a success response body that the front end can use to display a confirmation message

### Front-End — Contact Deletion

- [ ] T042 [P] [US5] Add a Delete button on the Contact Detail screen
- [ ] T043 [US5] When Delete is tapped, show a confirmation dialog clearly stating the contact will be permanently removed; provide Confirm and Cancel actions
- [ ] T044 [US5] On confirmed deletion, remove the contact from the list, show a brief success notification, and navigate away from the (now deleted) detail screen
- [ ] T045 [US5] On cancelled deletion, close the dialog and leave the contact unchanged

**Checkpoint**: User Stories 1–5 all work independently. A user can perform the full contact lifecycle: create → find → view → edit → delete.

---

## Phase 8: User Story 6 — Organize Contacts into Groups (Priority: P4)

**Goal**: A user can create named groups, assign contacts to them, and filter the contact list by group.

**Independent Test**: Create a group named "Work." Assign three contacts to it. Filter by "Work" — confirm only those three contacts appear. View one of those contacts — confirm "Work" is listed among its groups. Delete the "Work" group — confirm the three contacts still exist in the address book and are no longer associated with "Work."

### Back-End — Groups

- [ ] T046 [P] [US6] Implement `POST /groups` to create a named group; group name is required and must be unique per user
- [ ] T047 [P] [US6] Implement `GET /groups` to return all groups with their member contact IDs
- [ ] T048 [P] [US6] Implement `PUT /groups/{id}` to rename a group or update its member list
- [ ] T049 [P] [US6] Implement `DELETE /groups/{id}` that removes the group but does NOT delete the contacts it contained; the contacts' group association is removed
- [ ] T050 [US6] Update `GET /contacts` and `GET /contacts/search` to accept an optional `group_id` filter parameter that restricts results to contacts in that group

### Front-End — Groups

- [ ] T051 [P] [US6] Add a Groups management screen where users can create a new group by entering a name, view all existing groups, and delete a group with a confirmation step
- [ ] T052 [US6] Allow users to assign a contact to one or more groups from the Add Contact and Edit Contact forms, using a multi-select control listing all existing groups
- [ ] T053 [US6] Display all group names a contact belongs to on the Contact Detail screen
- [ ] T054 [US6] Add a group filter control to the contact list screen; selecting a group shows only contacts in that group; clearing the filter restores the full list

**Checkpoint**: All six user stories are fully functional. The complete address book feature — create, search, view, edit, delete, and group — is independently testable and deliverable.

---

## Phase 9: Data Integrity, Edge Cases & Export

**Purpose**: Close out functional requirements not tied to a single user story, and surface open items for resolution.

- [ ] T055 [P] Verify contact data persists across sessions: save a contact, close and reopen the application, confirm the contact is present with all fields intact (SC-005)
- [ ] T056 [P] Implement and test the partial-address rule: either all address sub-fields (street, city, state, postal code, country) are optional individually, OR they must all be provided together — the chosen behavior must match `data-model.md` and be communicated to users via clear form guidance
- [ ] T057 [P] Define and enforce maximum character limits per field (pending resolution of OI-03): first name, last name, phone number, email, street line 1, street line 2, city, state/province, postal code, country, notes — each field must reject input beyond its limit with a readable error message
- [ ] T058 [P] Verify the contact list with 1,000+ contacts loads and is fully scrollable within 2 seconds (SC-004); implement pagination or virtual scrolling on the front end if needed
- [ ] T059 [P] Verify the contact list supports sorting alphabetically by last name and by first name (FR-016)
- [ ] T060 Implement the `GET /contacts/export` endpoint once export format is confirmed (OI-02); supported formats: vCard and/or CSV
- [ ] T061 [P] Add an Export button to the contact list screen that triggers a file download in the confirmed format(s)
- [ ] T062 If contact import from external file is confirmed in scope (OI-06): implement import logic that validates each record against required-field rules, imports valid records, and flags or skips invalid records with a summary shown to the user — invalid records are never silently imported

**Checkpoint**: All functional requirements FR-001 through FR-018 are satisfied (open items resolved), all success criteria SC-001 through SC-008 are verifiable, and no data loss scenarios exist.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Quality improvements that apply across all user stories.

- [ ] T063 [P] Run the full `quickstart.md` walkthrough from a clean checkout; fix any step that does not work as documented
- [ ] T064 [P] Conduct a timed usability check against SC-001 (new contact created in under 90 seconds from blank form)
- [ ] T065 [P] Conduct a timed search check against SC-002 (contact located from 200+ contacts in under 10 seconds)
- [ ] T066 [P] Verify SC-006: write an automated scenario that inserts a contact and then attempts to insert an identical full name + primary phone; confirm the duplicate warning appears 100% of the time
- [ ] T067 [P] Verify SC-007: measure API response time from last keystroke to results rendered; confirm it is within 500 ms on a dataset of 1,000 contacts
- [ ] T068 [P] Update all API contract files in `contracts/` to reflect any changes made during implementation
- [ ] T069 Performance review: identify any API endpoint or front-end screen that does not meet its stated performance target and resolve the gap
- [ ] T070 Accessibility review: verify all interactive elements are keyboard-navigable and screen-reader labelled (adjust target if OI-05 is resolved with a specific standard such as WCAG 2.1 AA)

---

## Dependencies & Execution Order

### Phase Dependencies

| Phase | Depends On | Notes |
|-------|-----------|-------|
| Phase 1 — Setup | None | Start immediately |
| Phase 2 — Foundational | Phase 1 complete | **Blocks all user stories** |
| Phases 3–8 (User Stories) | Phase 2 complete | Can proceed in parallel once foundation is ready |
| Phase 9 — Edge Cases & Export | Phases 3–8 complete | Needs full feature set in place |
| Phase 10 — Polish | Phase 9 complete | Final pass before delivery |

### User Story Dependencies

| Story | Priority | Can Start After | Depends On Other Stories? |
|-------|----------|----------------|--------------------------|
| US1 — Add Contact | P1 | Phase 2 | None — fully independent |
| US2 — Search | P2 | Phase 2 | Reads contacts created by US1, but independently testable |
| US3 — View Detail | P2 | Phase 2 | Reads contacts created by US1, but independently testable |
| US4 — Edit Contact | P3 | Phase 2 | Requires a contact to edit; otherwise independent |
| US5 — Delete Contact | P3 | Phase 2 | Requires a contact to delete; otherwise independent |
| US6 — Groups | P4 | Phase 2 | Requires contacts to assign; otherwise independent |

### Parallel Opportunities

- All tasks marked `[P]` within a phase can be worked simultaneously by different team members
- Once Phase 2 is complete, all six user story phases can be staffed in parallel
- Back-end and front-end tasks within each user story can be worked in parallel

---

## Open Items Blocking Completion

These items from the plan must be resolved before the affected tasks can be finalized:

| ID | Blocks | Item |
|----|--------|------|
| OI-01 | T058, performance targets | Maximum contact capacity per user (FR-015) |
| OI-02 | T060, T061 | Export formats: vCard, CSV, or both (FR-017) |
| OI-03 | T057 | Maximum character limits per field (FR-018) |
| OI-04 | Architecture | Single-user vs. multi-user scope for this release |
| OI-05 | T070 | Accessibility compliance target |
| OI-06 | T062 | Contact import from external file: in scope? |

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 — Add a New Contact
4. **STOP AND VALIDATE**: Confirm a contact can be created, validates correctly, detects duplicates, and appears in the list
5. Demo or deploy as MVP

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. Add User Story 1 (Add Contact) → test independently → demo
3. Add User Stories 2 + 3 (Search + View Detail) → test independently → demo
4. Add User Stories 4 + 5 (Edit + Delete) → test independently → demo
5. Add User Story 6 (Groups) → test independently → demo
6. Resolve open items → complete Phase 9 + Phase 10 → release

### Parallel Team Strategy

With three or more developers, once Phase 2 is complete:
- Developer A: User Story 1 (P1 — highest priority)
- Developer B: User Story 2 + 3 (P2)
- Developer C: User Story 4 + 5 (P3)
- User Story 6 picked up by whoever finishes first

---

## Notes

- `[P]` tasks = operate on different files or services with no shared dependencies — safe to run simultaneously
- `[Story]` label maps every task to a specific user story for traceability back to the spec
- Each user story is independently completable and testable before moving to the next priority
- Resolve all Phase 0 open items (OI-01 through OI-06) before beginning Phase 9
- Commit after each task or logical group; do not batch unrelated changes in a single commit
- Stop at every **Checkpoint** to validate the story independently before proceeding