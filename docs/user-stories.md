# User stories and acceptance criteria

These fifteen stories cover the current workflow and latest requested changes. Personas are working profiles, not interview participants. Requirements refer to the [SRS](srs.md), and interactions to [Use cases](use-cases.md).

Acceptance criteria describe expected outcomes. They are not execution results. For Partial or requested stories, an unmet criterion remains visible rather than being written as delivered behaviour.

## 1. Story map and traceability

| Activity | Story | Persona | Requirements | Use cases | Criteria | Current coverage |
|---|---|---|---|---|---|---|
| Prepare an order | US-01: enter block demand | P-02 | FR-03, FR-19 | UC-01 | AC-01 | Implemented interpretation of MN-01 |
| Choose a recipe | US-02: compare and select one mix | P-01, P-02 | FR-04, FR-05 | UC-01 | AC-02 | Partial: mixed-currency preview gap |
| Inspect an estimate | US-03: see the basis of the total | P-01, P-03 | FR-06, FR-18 | UC-01, UC-05, UC-07 | AC-03 | Implemented at project-detail level; Q-02 open |
| Revise an estimate | US-04: correct a Draft | P-02 | FR-07 | UC-02 | AC-04 | Implemented |
| Adjust a project price | US-05: use an individual price | P-01 | FR-11 | UC-02 | AC-05 | Implemented |
| Maintain shared prices | US-06: propose a default price | P-01 | FR-09 | UC-04 | AC-06 | Implemented |
| Review shared prices | US-07: decide on a price | P-03 | FR-10, FR-14 | UC-04 | AC-07 | Implemented |
| Request project review | US-08: submit or recall a project | P-01 | FR-12 | UC-05 | AC-08 | Implemented |
| Decide on a project | US-09: approve or explain rejection | P-03 | FR-13, FR-14, FR-18 | UC-05 | AC-09 | Implemented at page level; Q-02 open |
| Close the project | US-10: preserve the completed estimate | P-01 | FR-15 | UC-06 | AC-10 | Implemented within stated snapshot limits |
| Consult agreed work | US-11: read approved projects | P-04 | FR-16, FR-17 | UC-07 | AC-11 | Implemented |
| Maintain production inputs | US-12: reuse mixes and materials | P-01 | FR-08 | UC-03 | AC-12 | Implemented |
| Provide staff access | US-13: assign the right role | P-05 | FR-01, FR-02 | UC-08 | AC-13 | Implemented |
| Simplify calculation | US-14: use relevant, clear choices | P-02 | FR-19–FR-21 | UC-01 | AC-14 | Partial; Q-01, Q-03, Q-06 open |
| Set shared currency | US-15: configure currency once | P-01 / P-05, actor to confirm | FR-22 | UC-09 | AC-15 | Not implemented; Q-04 open |

FR-23 remains a clarification item, not an invented sixteenth story. Once Q-05 is resolved, its agreed effect should refine the relevant price-entry story and criteria.

The current-workflow stories form the baseline; US-14 and US-15 identify requested follow-up. This is not a promise that all fifteen stories have been accepted or completed.

## 2. Stories and criteria

### US-01 — Enter block demand

As an occasional estimating manager, I want to enter Full and Half block counts without first removing a prefilled zero, so that I can represent the order directly.

**AC-01**
```gherkin
Given I am signed in as a Manager
When I open the new project calculator
Then the Full and Half quantity inputs are empty with a zero hint
When I supply a name, at least one positive integer block count, and a compatible mix
And I save the project
Then the project is saved as Draft with those quantities
```
If both counts are blank/zero, or a count is negative or non-integer, the project is not saved. A blank or zero count for just one type is allowed. This criterion implements the working interpretation of MN-01, subject to Q-01.

### US-02 — Compare and select one mix

As a manager, I want to compare mix alternatives for the whole order and select one, so that the entire project's material requirements use a consistent recipe.

**AC-02**
```gherkin
Given the entered project quantities and compatible active mixes
And every ingredient is priced in the same currency
When the quantities change
Then each applicable mix preview shows material requirements and a project-wide total
When I select a mix and save
Then that one mix applies to both Full and Half blocks in the project
```
An incompatible mix cannot be saved. Missing prices prevent a complete preview total. Prices with different currencies must not be presented as a valid combined total; that preview case is currently unmet.

### US-03 — Understand the estimate

As an accountant or manager, I want to see the materials and applied prices behind a total, so that I can judge the estimate without reconstructing it elsewhere.

**AC-03**
```gherkin
Given a non-completed project with a mix and complete prices in one currency
When I open its details
Then I see block counts, the selected mix, material quantities with units, prices, and subtotals
And I see the project total and whether each price is a default or project price
```
An incomplete total is replaced by an explanation, not a misleading zero. For accountants, the breakdown and project decision are on the same page. Placement beyond that remains subject to Q-02.

### US-04 — Correct a Draft

As a manager, I want to revise a Draft's quantities or mix, so that mistakes can be corrected before review.

**AC-04**
```gherkin
Given a Draft project
When I save valid revised counts and a compatible mix
Then the project retains the revised values
And its estimate reflects those values
```
General edits to a Pending, Approved, or Completed project are refused. A Pending project must return to Draft first.

### US-05 — Use an individual project price

As a manager, I want to override a material's price for one project, so that a project-specific quotation does not change the shared price.

**AC-05**
```gherkin
Given a Draft or Pending project and an approved default material price
When I save a valid positive price for that material in this project
Then this project's estimate uses the project price
And the default price and other projects' individual prices remain unchanged
When I restore the default price
Then this project uses the effective default again
```
Approved and Completed projects reject the override. Where material weight is known, the current project price input is per tonne.

### US-06 — Propose a default price

As a manager, I want to maintain common material prices, so that new estimates can reuse them instead of requiring individual price entry.

**AC-06**
```gherkin
Given an available material
When I submit a default price with a valid basis, amount, and currency
Then the proposal is recorded as Pending
And it does not replace the effective default before accountant approval
```
A unit basis not supported by the material is rejected. Future global currency and the “wheelwide” request are not claimed as implemented here.

### US-07 — Review a default price

As an accountant, I want to approve or decline a proposed price and optionally correct it, so that shared calculations use a reviewed figure.

**AC-07**
```gherkin
Given a Pending default price
When I approve it
Then it becomes eligible as an approved default
And my identity and the review time are recorded
```
If I decline it with a valid positive corrected amount, the original is declined and a separate approved replacement is recorded. Decline without a correction does not approve the proposal. Project-style rejection comments are not required for this price decision.

### US-08 — Submit or recall a project

As a manager, I want to submit a prepared project and recall it when further work is needed, so that the review state is explicit.

**AC-08**
```gherkin
Given a Draft project with a selected mix
When I submit it
Then its status becomes Pending
And only its project prices remain directly editable
When I recall it while still Pending
Then its status becomes Draft
And general editing becomes available again
```
The manager cannot skip to Approved or Completed. Missing prices do not prevent submission, but do prevent approval.

### US-09 — Approve or explain rejection

As an accountant, I want to inspect a pending estimate and record an approval or explained rejection, so that the manager knows the financial decision and any required correction.

**AC-09**
```gherkin
Given a Pending project with a calculable total
When I approve it
Then its status becomes Approved
And my identity, decision, review time, and any comment are retained
```
Decline with a non-empty comment returns it to Draft and retains the explanation. Decline without a comment leaves it Pending. Approval with missing prices or conflicting currencies is refused. Materials must be available on the review page; Q-02 may refine their placement.

### US-10 — Preserve the completed estimate

As a manager, I want to preserve the estimate when completing an approved project, so that later price changes do not overwrite its recorded cost.

**AC-10**
```gherkin
Given an Approved project with a calculable total
When I complete it
Then its status becomes Completed
And its calculated recipe breakdown, material quantities, unit prices, subtotals, and total are saved
When a new default price is later approved
Then the saved total remains unchanged
```
The normal project workflow cannot edit, re-price, delete, or reopen it. This does not assert immutability of all material labels and weight-based displays; see SRS section 7.

### US-11 — Read approved work

As a production worker using the Creator role, I want to find and read approved projects, so that I do not act on an unreviewed draft.

**AC-11**
```gherkin
Given I am signed in as a Creator
When I browse or search projects
Then only Approved and Completed projects are available to me
When I open one
Then I can read its mix, quantities, and material breakdown
And I cannot change or review it
```
A direct request for a Draft or Pending project is denied. The current read-only view also includes financial amounts.

### US-12 — Maintain reusable production inputs

As an operations manager, I want to maintain materials and mixes with their quantities and yields, so that estimates reflect the production inputs I configure.

**AC-12**
```gherkin
Given I am signed in as a Manager
When I save a valid material with its unit and applicable weight
And I save an active mix with a positive yield and at least one positive ingredient quantity
Then the material and mix can be reused in a compatible new project
```
A mix with an invalid yield or no positive ingredients is rejected. Referenced materials and mixes cannot simply be deleted; deactivation is available.

### US-13 — Provision appropriate access

As an administrator, I want to create staff accounts with explicit roles, so that staff can perform their responsibilities without public registration.

**AC-13**
```gherkin
Given I have superuser access
When I create a valid staff account and assign the Accountant role
Then that user can sign in with their email and password
And can review prices and Pending projects
And does not receive Manager permissions from that role
```
Public registration is unavailable. Incorrect credentials do not create an authenticated session.

### US-14 — Keep the calculator focused

As an occasional estimating manager, I want the project calculator to use clear mix terminology and omit unnecessary strength information, so that I can focus on quantities, materials, and cost.

**AC-14 — proposed interpretation of the latest feedback**
```gherkin
Given I am preparing a project
When I compare the recipe options
Then the selectable recipe is described as a mix or mixture
And no MPa input is required
And MPa is not shown on the mix-selection cards
And the quantity inputs do not contain a prefilled zero
```
This criterion is not fully met: MPa remains on the cards. Renaming existing “Batch” recipe names requires Q-03; the scope of MPa removal requires Q-06. This story does not require deletion of stored strength information.

### US-15 — Configure a shared currency

As a staff member authorized to manage application settings, I want to configure the application currency once, so that currency does not need to be chosen repeatedly for material prices.

**AC-15 — candidate, blocked by Q-04**
```gherkin
Given the authorized role and currency application policy have been agreed
When that user saves an application currency setting
Then the setting persists
And subsequent price entry follows the agreed policy
```
This is not yet a complete executable acceptance criterion: Q-04 must define permissions, the effect on new prices, and the treatment of existing prices and completed estimates. No exchange-rate conversion or retroactive relabelling of amounts is authorized by this story.
