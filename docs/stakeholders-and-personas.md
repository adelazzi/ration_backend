# Stakeholders and personas

## 1. Stakeholders

| Stakeholder | Interest / value | Responsibility |
|---|---|---|
| Customer representative | A calculation workflow that fits the block yard's work and latest feedback. | Clarify meeting notes, confirm domain assumptions, and review the requirements. |
| Manager | A consistent estimate with an appropriate mix and prices. | Prepare projects and maintain the production and pricing inputs available to this role. |
| Accountant | A clear basis for financial decisions. | Review default price proposals and pending projects. |
| Production worker | Clear information for agreed work, without draft instructions. | Read approved or completed projects; act on production instructions outside the application. |
| Administrator | Appropriate access for each staff member. | Provision accounts and assign roles. |
| Project team | A maintainable, verifiable requirements baseline. | Keep requirements, implementation status, acceptance criteria, and evidence consistent. |

The customer representative and project team are stakeholders, not additional application roles.

## 2. Persona basis

The following five **proto-personas** are representative working profiles, not research participants. Names, experience levels, and work contexts are fictional assumptions for requirements discussion. No interviews, demographic findings, or observed behaviour are claimed.

Two personas share the Manager role because their experience and goals differ. A persona does not require a separate authorization role. Relevant responsibilities are emphasized instead of invented biographical detail.

## P-01 — Michael, experienced operations manager

- **Application role:** Manager.
- **Context and behaviour:** regularly prepares estimates and maintains familiar production recipes.
- **Knowledge:** understands mixes, production yields, and how materials are purchased.
- **Goal:** prepare a complete estimate and submit it for financial review.
- **Needs:** reusable mixes, common default prices, an itemized total, and project-specific price adjustments.
- **Pain points:** repeated price entry, using a price from the wrong context, or different recipes being applied within one order.
- **Scenario:** receives a mixed Full/Half order, compares available mixes, chooses one, checks costs, and submits the project.
- **Related stories:** US-02–US-08, US-10, US-12.

## P-02 — Leah, occasional estimating manager

- **Application role:** Manager.
- **Context and behaviour:** prepares an estimate occasionally and cannot rely on familiarity with every control.
- **Knowledge:** understands the order quantities but needs the calculator to expose the relevant choices clearly.
- **Goal:** enter the order and identify an appropriate mix without unnecessary inputs.
- **Needs:** editable quantity fields, visible mix options, clear units, and totals connected to the selected mix.
- **Pain points:** an apparent fixed zero, a small selector, unexplained MPa, and uncertainty about what to do after a price appears.
- **Scenario:** enters Full and Half quantities, compares the project-wide alternatives, and saves a draft.
- **Related stories:** US-01–US-04, US-14.
- **Basis:** these concerns are derived from MN-01–MN-06 and MN-10, not from an interview with this fictional person.

## P-03 — Aisha, accountant

- **Application role:** Accountant.
- **Context and behaviour:** checks estimates prepared by managers and reviews changed material prices.
- **Knowledge:** comfortable with financial review; should not need to reconstruct the recipe's material cost externally.
- **Goal:** make an informed, attributable decision on a price or project.
- **Needs:** material quantities, applied prices, subtotals, total, price sources, and prior project review comments.
- **Pain points:** a total without its basis, unnecessary navigation, or an unexplained rejection.
- **Scenario:** opens a pending project, inspects its material breakdown, and approves it or returns it with a comment.
- **Related stories:** US-03, US-07, US-09.

## P-04 — Peter, production worker

- **Application role:** Creator, the current application's read-only role.
- **Context and behaviour:** consults the project for agreed block quantities and material requirements.
- **Knowledge:** familiar with production units such as bags and wheelbarrows.
- **Goal:** distinguish approved work from unreviewed planning.
- **Needs:** approved status, the chosen mix, block counts, and understandable material quantities.
- **Pain points:** mistaking a draft for agreed work or being unsure what a quantity's unit means.
- **Scenario:** finds an approved project and reads its mix and material requirements without editing it.
- **Related story:** US-11.
- **Boundary:** financial amounts are currently visible to this role. A separate cost-hidden producer report is not specified.

## P-05 — Sam, staff account administrator

- **Application privilege:** Superuser; not a fourth ordinary business role.
- **Context and behaviour:** provisions access when staff join or responsibilities change.
- **Knowledge:** understands staff responsibilities and basic account administration.
- **Goal:** give staff the correct access without public self-registration.
- **Needs:** account creation and explicit role assignment.
- **Pain points:** a production worker accidentally receiving editing permissions or an accountant being unable to review work.
- **Scenario:** creates an accountant account and assigns the Accountant role.
- **Related stories:** US-13; possible involvement in US-15 is subject to Q-04.
- **Basis:** this profile represents existing administration functionality, not an additional request from the meeting.
