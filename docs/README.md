# Ration: requirements documentation

**Version:** 1.0, draft for review

**Prepared:** 21 November 2026

**Baseline:** current Ration implementation and the latest customer meeting notes supplied by the team.

## Reading order

| Document | Purpose |
|---|---|
| [Vision and scope](vision-and-scope.md) | The business problem, objectives, boundaries, assumptions, and risks. |
| [Stakeholders and personas](stakeholders-and-personas.md) | Responsibilities and five representative user profiles. |
| [Customer feedback](customer-feedback.md) | Original meeting notes, interpretations, implementation gaps, and open questions. |
| [Use cases](use-cases.md) | Actor goals, preconditions, main flows, alternatives, and outcomes. |
| [User stories](user-stories.md) | Fifteen stories, acceptance criteria, and their links to requirements and use cases. |
| [Software requirements](srs.md) | Functional requirements, business rules, quality requirements, glossary, and verification references. |

This is a requirements specification, not a user manual. Usability testing, data models and dictionaries, diagrams, architecture, user guides, and demo scripts are outside this documentation increment.

## Sources and authority

- **SRC-IMPL:** the current repository. It is evidence of existing behaviour, not proof that the customer has accepted every implemented rule.
- **SRC-MEETING:** the latest customer notes reproduced in [Customer feedback](customer-feedback.md). The meeting date, participants, and formal approval record were not supplied.
- **SRC-COURSE:** the course material listed below. It guides the documentation method, not the product's feature scope.

Earlier project specifications are not treated as the current requirements baseline. Features mentioned only in those documents are not silently carried forward. Where the latest notes request a change, the current behaviour and requested outcome are recorded separately.

### Course references

| Material | Guidance applied |
|---|---|
| *1 - Intro to project*, slides 9–11 | Vision and scope; five personas; at least five use cases; 10–15 stories; software specification. |
| *Vision and Scope Template* | Business objectives, success measures, release boundaries, stakeholders, assumptions, and risks. |
| *Software Requirements Specification Template (SRS)* | Identified requirements, feature descriptions, quality attributes, conventions, and glossary. Only sections within this increment's scope are developed. |
| *T5 - Use Cases*, slides 20–29 | Preconditions, postconditions, main flows, alternatives, and exceptions. |
| *T6 - User Stories and Personas*, slides 3, 16, 24–29 | Role–goal–benefit stories, Given/When/Then criteria, and context-based personas. |
| *T4 - NonFunctionalRequirement*, slides 7–14 | Specific, measurable, verifiable quality requirements. |
| *T7 - Elicitation interviews*, slides 16, 22–23 | Distinguish facts from interpretations and ask about concrete examples. |
| *RE Fall 2026 - Lecture 5*, slides 16–21; *Lecture 9-10*, slides 34, 46–56 | System boundaries, traceability, consistent terminology, and explicit resolution of conflicts. |

## Conventions

- `BG` identifies a business goal; `P`, a persona; `MN`, a meeting note; `Q`, an open question.
- `UC` identifies a use case; `US`, a user story; `AC`, an acceptance criterion.
- `FR` identifies a functional requirement; `BR`, a business rule; `NFR`, a quality requirement.
- Identifiers belong to this baseline. They do not imply equivalence to identifiers in earlier specifications.
- **Shall** expresses specified behaviour. A requirement's implementation status must be read alongside it.
- **Implemented** means supported by the inspected implementation. It does not mean customer acceptance or complete test coverage.
- **Partial** means some specified behaviour exists but a known part remains unmet.
- **Not implemented** means a requested capability is absent.
- **Clarification required** means the notes do not yet define an actionable requirement.

The priorities in the SRS are the team's proposed delivery order, not a customer-approved ranking. Pending requests have no committed delivery date. Proposed interpretations and persona details are not presented as interview findings.

## Maintaining the baseline

For each clarified or changed requirement, record the source, decision, date, affected identifiers, and implementation status. Keep existing identifiers when refining the same requirement. Do not mark an open question resolved or this baseline approved without an actual decision.

| Version | Date | Change |
|---|---|---|
| 1.0 draft | 21 November 2026 | Initial documentation based on the current implementation and latest supplied meeting notes; earlier feature commitments are not imported. |
