# Vision and scope

**Product:** Ration

**Version:** 1.0 draft

**Sources:** SRC-IMPL and SRC-MEETING, as defined in the [documentation index](README.md).

## 1. Business requirements

### 1.1 Background and problem

Ration supports planning for concrete block production. A manager needs to turn an order for Full and/or Half blocks into material quantities and an estimated material cost. An accountant needs to inspect the basis of the estimate before approving it. A production worker needs access to the agreed project rather than an editable draft.

Without a shared calculation and review workflow, quantities, recipe choices, and prices can be communicated or checked separately. This creates a risk of inconsistent estimates and unclear approval responsibility. The team's earlier description of a manual process is background context; its exact tools, time costs, and error rates have not been re-established through the latest supplied notes.

The latest meeting particularly identifies confusing calculation and selection controls, unnecessary terminology, repeated settings, and the need for one mix throughout a project.

### 1.2 Business goals and success measures

| ID | Goal | Observable success criterion |
|---|---|---|
| BG-01 | Prepare a consistent material estimate for an order. | A project with valid quantities, one compatible mix, and complete prices produces a material breakdown and total matching the documented rules. |
| BG-02 | Make financial review explicit. | An accountant can inspect material quantities and prices, approve a pending project, or return it with an explanation. |
| BG-03 | Reuse common information without unintended project-wide changes. | Approved default prices are reused; an individual project price changes that project's calculation only. |
| BG-04 | Provide a trustworthy completed-project record. | Completing a project saves its calculated amounts and total; later default price changes do not change the saved total. |
| BG-05 | Simplify the calculation workflow in line with the latest feedback. | One mix is selected for the project; calculator terminology and MPa presentation meet the clarified customer requests. Global currency and price-entry scope are resolved explicitly. |

These are acceptance-oriented measures, not evidence of achieved business savings. No measured time reduction, error reduction, financial benefit, or customer acceptance is claimed.

### 1.3 Vision statement

For concrete block yard staff who need a shared basis for production estimates, Ration provides one project workflow for choosing a mix, calculating materials and cost, obtaining financial approval, and preserving the completed estimate. The focus is a clear calculation and review process, not a general manufacturing or accounting system.

## 2. Scope and limitations

### 2.1 Current implemented scope

- Administrator-provisioned accounts, email/password sign-in, and role-based actions.
- Projects containing Full blocks, Half blocks, or both, with one compatible mixture.
- Comparison of mix alternatives using the entered project quantities.
- Material quantities and estimated material costs, with explicit units and price sources.
- Manager-maintained materials, mix recipes, production yields, and default price proposals.
- Accountant approval or rejection of default prices, with an optional corrected replacement price.
- Project-specific material prices and restoration of default prices.
- Draft, Pending, Approved, and Completed project states.
- Project review, recorded decisions, and completed-project cost snapshots.
- Read-only access to approved and completed projects for the Creator role.
- Project search and status filters.

### 2.2 Latest requested follow-up

The latest notes remain relevant even when the implementation does not yet meet them:

- Complete the mix terminology change, subject to clarification of existing recipe names.
- Remove MPa from the project calculator, subject to confirmation of the screen scope.
- Add an application-wide currency setting, after its permissions and effect are clarified.
- Clarify and apply the requested change to wheelbarrow-related price setting.
- Clarify the remaining confusion after calculation and the location of materials in accountant views.

See [Customer feedback](customer-feedback.md) for the distinction between implemented behaviour, requested changes, and open questions. No delivery date is assigned here.

### 2.3 Exclusions

Offline operation, synchronization, currency exchange, imperial-unit conversion, statistical analytics, downloadable report exports, and a comprehensive administrative audit trail are not part of this baseline. This is not a statement that the customer has permanently rejected them; they are not inferred from earlier specifications.

Ration estimates material requirements and material cost. It does not establish actual material availability, guarantee block strength, calculate labour or transport costs, or certify physical production quality.

This documentation increment excludes usability testing, data documentation, diagrams, architecture, user guides, and demo preparation.

## 3. Business context

### 3.1 Responsibilities

The Manager prepares and updates estimates. The Accountant reviews financial inputs and project submissions. The production worker reads approved work through the application's Creator role. An administrator provisions accounts. Detailed user contexts are in [Stakeholders and personas](stakeholders-and-personas.md).

### 3.2 Priorities and constraints

Calculation correctness, role separation, one-mix consistency, and an understandable review basis take precedence over adding unrelated functionality. Existing capabilities are documented separately from requested improvements. No new schedule, team size, budget commitment, or service-level target is inferred from the earlier submissions.

The current interface is in English and requires a connection to the application. Completing a project records an estimate, not proof that the physical blocks have been produced.

### 3.3 Assumptions and dependencies

- Managers supply meaningful block counts, recipe quantities, material weights, and production yields.
- Accountants judge whether the proposed prices and estimates are appropriate; the software does not verify supplier quotations.
- The configured yield is used for each block type to which the selected mix applies.
- Weights per wheelbarrow or bag are configurable operational assumptions, not universal constants.
- The team can obtain customer clarification for the open questions before implementing ambiguous changes.

### 3.4 Main risks

| Risk | Likelihood / impact | Response |
|---|---|---|
| A short meeting note is interpreted more broadly than intended. | Likelihood unknown / High | Preserve the original wording and resolve the questions before widening scope. |
| A material weight or production yield does not match site practice. | Likelihood unknown / High | Make assumptions explicit and confirm them with the responsible customer representative. |
| An approved total changes before completion through shared settings. | Present capability / High | State the current limitation and resolve Q-07; do not describe approval as a frozen estimate. |
| Documentation claims requested features are already implemented. | Likelihood unknown / High | Maintain status and evidence links for each requirement. |
| A production worker interprets “Creator” as permission to create projects. | Likelihood unknown / Medium | Define the role explicitly as read-only in this baseline. |

Likelihoods are not quantified because supporting operational evidence has not been supplied.
