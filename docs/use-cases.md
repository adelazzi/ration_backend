# Use cases

Use cases describe goals and actor/system interactions, not button-by-button instructions. FR and BR identifiers refer to the [SRS](srs.md). UC-01–UC-08 describe the current workflow, with known gaps identified; UC-09 is a requested capability, not an implemented flow.

All ordinary flows require a signed-in, active account with the stated permissions. “Manager” and “Accountant” include a superuser performing the corresponding business action.

## UC-01 — Prepare a project estimate

- **Primary actor:** Manager.
- **Goal:** obtain a project estimate using one mix for all requested blocks.
- **Trigger:** the manager starts preparing an order estimate.
- **Preconditions:** at least one active, compatible mix is configured.
- **Requirements:** FR-03–FR-06, FR-19–FR-21; BR-01–BR-07.

**Main flow**
1. The manager supplies a project name and Full and/or Half block quantities.
2. The system presents applicable mixes with material requirements and available price previews.
3. The manager selects one mix for the whole project.
4. The system validates the project and mix compatibility.
5. The system saves a Draft and presents its material breakdown and calculated total.

**Alternatives and exceptions**
- **1a:** both quantities are blank/zero, negative, or non-integer: validation prevents saving.
- **3a:** no mix is selected, or it does not support all requested types: saving is rejected.
- **2a / 5a:** a price is missing: the material requirements remain available, but no complete total is shown.
- **5b:** prices have different currencies: the saved project explains that they cannot be added. The live preview currently lacks this check.

**Success postcondition:** a Draft exists with valid quantities and one selected mix.

**Failure guarantee:** invalid input does not create a project. An unpriced project may still be saved.

**Outstanding:** terminology and MPa display follow FR-20/FR-21, not a claim of full implementation.

## UC-02 — Revise a project estimate

- **Primary actor:** Manager.
- **Goal:** correct the project's demand, mix, or individual prices.
- **Trigger:** the manager identifies a needed change.
- **Preconditions:** the project exists; general edits require Draft; price-only edits permit Draft or Pending.
- **Requirements:** FR-07, FR-11; BR-05–BR-09.

**Main flow**
1. The manager opens the project and chooses a permitted change.
2. For a Draft, the manager revises project details, quantities, or the selected mix.
3. The system validates and saves the changes.
4. The manager optionally supplies a positive price for a material in this project.
5. The system recalculates using the project price in preference to the default.

**Alternatives and exceptions**
- **2a:** the project is Pending: general edits are blocked; it must return to Draft through UC-05 first.
- **4a:** the manager restores the default price instead; the project override is removed.
- **2b / 4b:** the project is Approved or Completed: the direct change is refused.
- **2c / 4c:** invalid quantities, incompatible mix, or invalid project price: the rejected change is not applied.
- **1a:** the manager deletes a Draft instead: deletion succeeds only without protected estimates or project review decisions.

**Success postcondition:** permitted revisions are reflected in this project's estimate; other projects' individual prices are unchanged.

**Failure guarantee:** a rejected operation leaves the affected project values unchanged.

## UC-03 — Maintain production mixes and materials

- **Primary actor:** Manager.
- **Goal:** keep reusable calculation inputs aligned with production practice.
- **Trigger:** a new material/mix or a change in production inputs is needed.
- **Preconditions:** the manager has access to configuration; a mix can reference available materials.
- **Requirements:** FR-08; BR-02–BR-04.

**Main flow**
1. The manager creates or edits a material, supplying its operational unit and applicable weight.
2. The system validates and saves it.
3. The manager creates or edits a mix, specifying supported block types, a positive yield, and ingredient quantities.
4. The system validates and saves the mix for reuse in projects.

**Alternatives and exceptions**
- **1a / 3a:** a material or mix is marked unavailable for new selections instead.
- **3b:** the yield is invalid, an ingredient quantity is negative, or no positive ingredient quantity is supplied: saving is rejected.
- **1b / 3c:** deletion of a referenced material or mix is refused; it may be deactivated instead.

**Success postcondition:** valid reusable settings are updated.

**Failure guarantee:** rejected changes are not saved.

**Boundary:** changing shared inputs can affect existing live estimates; it is not a controlled project-revision mechanism.

## UC-04 — Establish a default material price

- **Primary actor:** Manager.
- **Supporting actor:** Accountant.
- **Goal:** make a reviewed shared price available to projects.
- **Trigger:** the manager proposes a new material price.
- **Preconditions:** the material is available for a new price proposal.
- **Requirements:** FR-09, FR-10, FR-14; BR-05–BR-07.

**Main flow**
1. The manager supplies the material, price basis, amount, and currency.
2. The system validates the proposal and records it as Pending.
3. The accountant reviews the pending price and approves it.
4. The system records the reviewer and time and makes the approved price eligible for calculations.

**Alternatives and exceptions**
- **1a:** the basis is not valid for the material: the proposal is rejected.
- **2a:** the manager withdraws the proposal before review.
- **3a:** the accountant declines it: the proposal does not become an effective price.
- **3b:** the accountant declines and supplies a valid positive corrected amount: the original is declined and a separate approved replacement is recorded.
- **3c:** the corrected amount is invalid: the decision is not applied.

**Success postcondition:** a reviewed default price is available; project overrides still take precedence.

**Failure guarantee:** a Pending or Declined proposal is not used as the default.

**Outstanding:** global currency and wheelbarrow-related price-entry changes are not implemented by this flow.

## UC-05 — Obtain a decision on a project

- **Primary actor:** Manager.
- **Supporting actor:** Accountant.
- **Goal:** have the prepared estimate financially reviewed.
- **Trigger:** the manager submits a Draft.
- **Preconditions:** the project is Draft and has a selected mix.
- **Requirements:** FR-12–FR-14, FR-18; BR-07, BR-08.

**Main flow**
1. The manager submits the project.
2. The system changes its status to Pending.
3. The accountant opens the pending project and inspects its material quantities, prices, subtotals, and total on the review page.
4. The accountant approves the project.
5. The system records the decision, reviewer, time, and any comment, and changes the project to Approved.

**Alternatives and exceptions**
- **2a:** while still Pending, the manager recalls it to Draft.
- **3a:** prices are missing or currencies conflict: the project can remain Pending, but approval is blocked until a complete total is available.
- **4a:** the accountant declines with a comment: a decision is recorded and the project returns to Draft.
- **4b:** decline is attempted without a comment: the project remains Pending.
- **4c:** the project is no longer Pending: the review is not applied.

**Success postcondition:** the Approved project becomes visible to Creators.

**Decline postcondition:** the project is Draft with an explanation retained.

**Failure guarantee:** an invalid review does not change status or add a decision.

**Boundary:** approval does not freeze shared calculation inputs; see Q-07.

## UC-06 — Preserve a completed estimate

- **Primary actor:** Manager.
- **Goal:** preserve the material estimate when closing the project workflow.
- **Trigger:** the manager marks an Approved project completed.
- **Preconditions:** the project is Approved and its current total is calculable.
- **Requirements:** FR-15; BR-08, BR-09.

**Main flow**
1. The manager requests completion.
2. The system calculates the current estimate.
3. The system saves its recipe breakdown, material amounts, applied unit prices, subtotals, and total.
4. The system records the completion time and changes the project to Completed.

**Alternatives and exceptions**
- **2a:** the total is no longer calculable: completion is refused.
- **1a:** the project is not Approved: the transition is refused.
- **4a:** later normal workflow requests to reopen, re-price, edit, or delete the project are refused.

**Success postcondition:** the project is Completed and a saved estimate is displayed.

**Failure guarantee:** a refused completion leaves its prior status unchanged.

**Boundary:** completion is a manager's declaration, not a measurement of physical production.

## UC-07 — Inspect an accessible project

- **Primary actors:** Manager, Accountant, Creator.
- **Goal:** retrieve a project and inspect the information permitted for the actor.
- **Trigger:** the actor looks for a project.
- **Preconditions:** a project visible to the actor exists.
- **Requirements:** FR-06, FR-16–FR-18; BR-08, BR-09.

**Main flow**
1. The system lists projects visible to the actor.
2. The actor optionally searches by name/description or filters by status.
3. The actor opens a project.
4. The system shows its status, mix, block quantities, and material/cost breakdown; a Completed project uses its saved estimate.

**Alternatives and exceptions**
- **2a:** no projects match: the list is empty.
- **3a:** a Creator requests a Draft or Pending project directly: access is denied without exposing that project.
- **4a:** the actor is a Creator: changing and review actions are unavailable and direct attempts are denied.
- **4b:** the live estimate is incomplete: the reason is shown instead of a complete total.

**Success postcondition:** the permitted information has been presented; no project is changed.

**Boundary:** Creators currently see financial amounts as well as material quantities.

## UC-08 — Provision staff access

- **Primary actor:** Administrator with superuser privileges.
- **Goal:** grant a staff member the appropriate business role.
- **Trigger:** staff access is required.
- **Preconditions:** the administrator is authenticated in administration.
- **Requirements:** FR-01, FR-02.

**Main flow**
1. The administrator supplies the staff account's username, email, name, password, and role.
2. The system validates and creates the account.
3. The staff member signs in using the email and password.
4. The system permits actions according to the assigned role.

**Alternatives and exceptions**
- **2a:** account details fail validation: the account is not created.
- **3a:** credentials are incorrect or the account is inactive: sign-in is refused.
- **1a:** a visitor requests public registration: no public registration flow is provided.

**Success postcondition:** the staff member has an account with explicit access permissions.

**Failure guarantee:** unsuccessful authentication does not create an authenticated session.

## UC-09 — Configure the application currency (requested)

- **Primary actor:** authorized settings user; exact role unresolved in Q-04.
- **Goal:** avoid selecting the currency separately for each new material price.
- **Trigger:** a currency configuration is needed.
- **Preconditions:** permissions and the effect on existing prices have been agreed.
- **Requirement:** FR-22.
- **Status:** not implemented; the following is a proposed outline, not an accepted interaction design.

**Candidate main flow**
1. The authorized user chooses an application currency.
2. The system saves the setting.
3. Price entry uses it according to the policy agreed in Q-04.

**Alternatives and exceptions:** validation, unauthorized changes, and treatment of existing prices remain to be specified after Q-04.

**Intended postcondition:** the application has a shared currency setting. Detailed effects cannot be accepted until Q-04 is resolved. No currency conversion is implied.
