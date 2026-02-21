● Get current date
  $ date +%Y-%m-%d
  └ 2 lines...

# Feature Specification: Address Book

**Feature Branch**: `001-address-book`
**Created**: 2026-02-20
**Status**: Draft
**Input**: User description: "create me a business spec for an addressbook. this should have name, address, phone, etc."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add a New Contact (Priority: P1)

A user needs to store a new person's contact information — including their name, address, phone number, and email — so they can retrieve it later. This is the foundational action the address book exists to support.

**Why this priority**: Without the ability to create contacts, no other feature of the address book is useful. This is the core value proposition.

**Independent Test**: Can be fully tested by adding a single contact with all required fields, saving it, and confirming it appears in the contact list with all entered data intact.

**Acceptance Scenarios**:

1. **Given** the user is on the address book, **When** they choose to add a new contact and provide a first name, last name, phone number, street address, city, state, postal code, and email address, **Then** the contact is saved and immediately visible in the contact list.
2. **Given** the user is adding a new contact, **When** they attempt to save without providing a first name or last name, **Then** the system rejects the submission and indicates that name is required.
3. **Given** the user is adding a new contact, **When** they enter a phone number in an unrecognized format, **Then** the system notifies them and requests a valid format before allowing submission.
4. **Given** the user is adding a new contact, **When** they enter an email address that is not properly formatted (e.g., missing "@"), **Then** the system rejects the entry and prompts for a valid email.

---

### User Story 2 - Search and Find a Contact (Priority: P2)

A user wants to quickly locate a specific person in their address book by searching by name, phone number, or other identifying information, without having to scroll through the entire list.

**Why this priority**: An address book with many contacts becomes unusable without search. This is essential for any real-world volume of contacts and directly unlocks the value of storing contacts.

**Independent Test**: Can be fully tested by adding several contacts with distinct names, then searching for one by partial name and confirming the correct contact appears in results.

**Acceptance Scenarios**:

1. **Given** the address book contains multiple contacts, **When** the user types part of a contact's first or last name into the search field, **Then** only contacts whose names match the search term are displayed.
2. **Given** the address book contains multiple contacts, **When** the user searches by a phone number or partial phone number, **Then** matching contacts are returned.
3. **Given** the user performs a search that matches no contacts, **When** results are displayed, **Then** the system shows a clear message indicating no contacts were found.
4. **Given** the user clears the search field, **When** the field is empty, **Then** the full contact list is restored.

---

### User Story 3 - View Contact Details (Priority: P2)

A user selects a contact from the list to view their full details — name, all phone numbers, email, address, and any notes — presented in a readable, organized layout.

**Why this priority**: Storing contacts is only useful if users can easily retrieve and read all stored details. This completes the basic read workflow.

**Independent Test**: Can be fully tested by selecting a previously saved contact and confirming all entered fields are displayed accurately and completely.

**Acceptance Scenarios**:

1. **Given** a contact exists in the address book, **When** the user selects that contact, **Then** all stored fields for that contact are displayed, including name, phone numbers, email addresses, physical address, and notes.
2. **Given** a contact has multiple phone numbers or email addresses, **When** the user views the contact, **Then** all numbers and addresses are shown with their associated labels (e.g., "Mobile", "Work", "Home").
3. **Given** a field was left blank when the contact was created, **When** the user views the contact, **Then** blank fields are either hidden or clearly indicated as not provided.

---

### User Story 4 - Edit an Existing Contact (Priority: P3)

A user needs to update a contact's information — such as a new phone number or moved address — after the contact has already been saved.

**Why this priority**: Contact information changes over time. Without edit capability the address book quickly becomes outdated, but the core create/search/view flow can be demonstrated first.

**Independent Test**: Can be fully tested by editing a saved contact's phone number, saving the change, and confirming the updated number appears on the contact's detail view.

**Acceptance Scenarios**:

1. **Given** an existing contact, **When** the user edits the phone number field and saves, **Then** the contact's details reflect the new phone number and the old number is no longer shown.
2. **Given** an existing contact, **When** the user attempts to remove the contact's last name so that no name remains, **Then** the system prevents the save and indicates a name is required.
3. **Given** an existing contact is being edited, **When** the user discards their changes without saving, **Then** the original contact information is preserved unchanged.

---

### User Story 5 - Delete a Contact (Priority: P3)

A user needs to permanently remove a contact from their address book when that person is no longer relevant.

**Why this priority**: Data hygiene is important, but deletion is less critical than the ability to create, search, and update contacts. It is a supporting capability rather than a primary workflow.

**Independent Test**: Can be fully tested by deleting a saved contact and confirming they no longer appear in the contact list or search results.

**Acceptance Scenarios**:

1. **Given** an existing contact, **When** the user initiates deletion and confirms the action, **Then** the contact is permanently removed and no longer appears in the list or search results.
2. **Given** an existing contact, **When** the user initiates deletion but then cancels, **Then** the contact remains in the address book unchanged.
3. **Given** the user deletes a contact, **When** the deletion is confirmed, **Then** the system provides a brief confirmation that the contact was successfully removed.

---

### User Story 6 - Organize Contacts into Groups (Priority: P4)

A user wants to categorize contacts into named groups (e.g., "Family", "Work", "Clients") so they can filter and manage related contacts together.

**Why this priority**: Grouping adds organizational value for users with many contacts, but is not required for the core address book to function. It builds on a fully working basic feature set.

**Independent Test**: Can be fully tested by creating a group, assigning two or more contacts to it, and confirming that filtering by group displays only those contacts.

**Acceptance Scenarios**:

1. **Given** the user creates a group named "Work" and assigns three contacts to it, **When** they filter by "Work", **Then** only those three contacts are displayed.
2. **Given** a contact belongs to multiple groups, **When** the user views that contact, **Then** all associated group names are shown.
3. **Given** a group is deleted, **When** the deletion is confirmed, **Then** the contacts previously in that group remain in the address book and are no longer associated with the deleted group.

---

### Edge Cases

- What happens when a user attempts to add a contact with an identical name and phone number as an existing contact? The system should detect the potential duplicate and warn the user before saving.
- How does the system handle a phone number entered with non-numeric characters such as spaces, dashes, or parentheses? The system should normalize the format for storage and display.
- What happens when the address book contains zero contacts and a user performs a search? The system should display a message indicating the address book is empty rather than a generic "no results" message.
- What happens when an address field is partially filled in (e.g., city provided but no postal code)? The system should either require all address sub-fields together or allow all to be optional individually — this behavior must be defined.
- How does the system handle very long values in a field, such as an unusually long street address or a name with many characters? Display must not break, and the system should enforce a reasonable maximum character limit per field.
- What happens if a user attempts to import contacts from an external source with missing required fields? The system should skip or flag invalid records rather than silently importing incomplete data.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow a user to create a new contact with at minimum a first name and last name.
- **FR-002**: System MUST support storing the following fields per contact: first name, last name, one or more phone numbers (each labeled as Mobile, Home, or Work), one or more email addresses (each labeled as Personal or Work), street address, city, state/province, postal code, country, and a free-text notes field.
- **FR-003**: System MUST validate that phone numbers contain only recognized numeric formats before allowing a contact to be saved.
- **FR-004**: System MUST validate that email addresses conform to standard email format (contains "@" and a domain) before allowing a contact to be saved.
- **FR-005**: System MUST allow users to search contacts by first name, last name, phone number, or email address.
- **FR-006**: System MUST display search results in real time or near-real time as the user types.
- **FR-007**: System MUST allow users to view all stored fields for a selected contact on a single detail screen.
- **FR-008**: System MUST allow users to edit any field of an existing contact and save the updated information.
- **FR-009**: System MUST prevent saving an edited contact if the name fields are cleared, making the contact nameless.
- **FR-010**: System MUST allow users to delete a contact, with a confirmation step before permanent deletion.
- **FR-011**: System MUST persist all contact data so that contacts remain available after the user closes and reopens the address book.
- **FR-012**: System MUST detect potential duplicate contacts (same full name AND same primary phone number) and warn the user prior to saving.
- **FR-013**: System MUST allow users to create named groups and assign contacts to one or more groups.
- **FR-014**: System MUST allow users to filter the contact list by group.
- **FR-015**: System MUST support a minimum of [NEEDS CLARIFICATION: maximum contact capacity not specified — e.g., 500, 10,000, unlimited] contacts without degraded performance.
- **FR-016**: System MUST allow users to sort the contact list alphabetically by last name or first name.
- **FR-017**: System MUST allow users to export their contact list to a standard portable format (e.g., vCard or CSV) — [NEEDS CLARIFICATION: specific export formats required not confirmed by user].
- **FR-018**: System MUST enforce a maximum character limit on each text field to prevent excessively long inputs from causing display or storage issues — [NEEDS CLARIFICATION: specific limits per field not defined].

### Key Entities

- **Contact**: Represents a person stored in the address book. Key attributes: unique identifier, first name, last name, list of phone numbers with labels, list of email addresses with labels, physical address (street, city, state/province, postal code, country), free-text notes, date created, date last modified.
- **Phone Number**: Belongs to a Contact. Key attributes: number value, label (Mobile / Home / Work), primary flag (indicates preferred contact number).
- **Email Address**: Belongs to a Contact. Key attributes: email value, label (Personal / Work), primary flag.
- **Physical Address**: Belongs to a Contact. Key attributes: street line 1, street line 2 (optional), city, state or province, postal code, country.
- **Group**: Represents a user-defined category. Key attributes: unique identifier, group name, list of associated Contacts. A Contact may belong to zero or more Groups.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can create a complete new contact — including name, phone, email, and address — in under 90 seconds from a blank form.
- **SC-002**: A user can locate a specific contact by name from a list of 200+ contacts in under 10 seconds using search.
- **SC-003**: 95% of users can successfully add, find, and view a contact on their first attempt without requiring assistance or documentation.
- **SC-004**: The contact list renders and is fully scrollable within 2 seconds even when the address book contains 1,000 or more contacts.
- **SC-005**: Zero data loss — all contact information entered and saved by a user must be fully retrievable in subsequent sessions.
- **SC-006**: Duplicate contact warnings are surfaced in 100% of cases where both the full name and primary phone number match an existing contact.
- **SC-007**: Search results reflect the user's input within 500 milliseconds of their last keystroke.
- **SC-008**: 90% of users report the address book is easy to use in post-task satisfaction feedback (target score: 4/5 or higher on a usability survey).