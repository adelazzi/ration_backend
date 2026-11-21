# Software requirements specification

**Product:** Ration

**Version:** 1.0 draft, 21 November 2026

**Audience:** customer representative, project team, and reviewers.

## 1. Purpose, scope, and conventions

This specification describes current product behaviour and outstanding requests from the latest customer meeting. Business context and boundaries are defined in [Vision and scope](vision-and-scope.md); sources, identifier conventions, and status meanings are defined in the [documentation index](README.md).

Requirements sourced from the implementation are a description of the present baseline, not retrospective customer approval. Meeting interpretations remain subject to the [open questions](customer-feedback.md#3-questions-to-resolve).

**Priority:** Core = preserve the existing calculation/review workflow; Follow-up = address the latest requested changes; Clarify = resolve meaning before committing behaviour. These are proposed team priorities, not a negotiated release plan.

This tailored SRS does not include data models, data dictionaries, diagrams, architecture, usability testing, user instructions, or a demo script. No service-level or performance threshold is invented where the available sources specify none.

## 2. User classes and operating context

Managers prepare and maintain estimates. Accountants review prices and projects. Creators read approved and completed projects. Superusers can perform all these actions and provision accounts. Five working profiles are described in [Stakeholders and personas](stakeholders-and-personas.md).

The current product is an English-language web application requiring access to the running service. Physical production, supplier-price validity, material availability, and actual strength remain outside its control.

## 3. Functional requirements

### 3.1 Access and project preparation

| ID | Requirement | Source | Priority | Implementation |
|---|---|---|---|---|
| FR-01 | The system shall allow an administrator to create staff accounts and assign a Manager, Accountant, or Creator role, without public self-registration. | SRC-IMPL | Core | Implemented |
| FR-02 | The system shall allow active users to sign in with email and password and sign out of their session. | SRC-IMPL | Core | Implemented |
| FR-03 | The system shall allow a manager to create a Draft project with a name, optional description, and non-negative integer Full and Half block quantities, with at least one positive quantity. | SRC-IMPL | Core | Implemented |
| FR-04 | The system shall require one active mix compatible with every block type requested in a new project, using that mix for the whole project. | MN-11; SRC-IMPL | Core | Implemented |
| FR-05 | The system shall present selectable mix alternatives with project-wide material quantities and, when prices are complete and share one currency, a project total for the entered quantities. | MN-02, MN-03; SRC-IMPL | Core | Partial: normal previews exist; the preview does not detect mixed currencies (section 7). |
| FR-06 | The system shall display the selected mix, block quantities, material quantities, applicable prices, material subtotals, and total for a priced project; it shall explain when a total cannot be produced. | MN-03; SRC-IMPL | Core | Implemented on project details |
| FR-07 | The system shall allow a manager to edit a Draft project's name, description, quantities, and mix, or delete it unless saved estimates or project review decisions protect it. | SRC-IMPL | Core | Implemented |
| FR-08 | The system shall allow a manager to maintain materials and mixes, including material weight per unit, recipe quantities, applicable block types, production yield, and availability for new selections. | SRC-IMPL | Core | Implemented |

### 3.2 Prices and financial review

| ID | Requirement | Source | Priority | Implementation |
|---|---|---|---|---|
| FR-09 | The system shall allow a manager to propose a default material price and shall keep it Pending until an accountant reviews it. | MN-08; SRC-IMPL | Core | Implemented |
| FR-10 | The system shall allow an accountant to approve or decline a Pending default price and, on decline, optionally supply a positive corrected price that becomes approved. | SRC-IMPL | Core | Implemented |
| FR-11 | The system shall allow a manager to set a positive project-specific material price or restore the default price while the project is Draft or Pending, without changing other projects' prices. | SRC-IMPL | Core | Implemented |
| FR-12 | The system shall allow a manager to submit a Draft project with a selected mix as Pending, or return a Pending project to Draft. | SRC-IMPL | Core | Implemented |
| FR-13 | The system shall allow an accountant to approve a Pending project only when its total is calculable, or decline it to Draft with a mandatory explanatory comment. | SRC-IMPL | Core | Implemented |
| FR-14 | The system shall retain project review decisions with reviewer, time, decision, and any comment, and default-price review decisions with reviewer and time. | SRC-IMPL | Core | Implemented; not a complete administrative audit trail |
| FR-15 | The system shall allow a manager to complete an Approved project only with a calculable total, saving its recipe breakdown, material quantities, applied unit prices, subtotals, and total as a historical estimate. | SRC-IMPL | Core | Implemented; snapshot limits are stated in section 7. |

### 3.3 Visibility and calculator simplification

| ID | Requirement | Source | Priority | Implementation |
|---|---|---|---|---|
| FR-16 | The system shall restrict a Creator to read-only access to Approved and Completed projects, denying access to Draft and Pending projects. | SRC-IMPL | Core | Implemented |
| FR-17 | The system shall allow signed-in users to search the projects visible to them by name or description and filter them by project status. | SRC-IMPL | Core | Implemented |
| FR-18 | The system shall show an accountant the pending project's material quantities, applied prices, and subtotals on the page where the project is reviewed. | MN-04; SRC-IMPL | Core | Implemented at page level; a more specific meaning of “directly” is unresolved (Q-02). |
| FR-19 | New project quantity fields shall be empty with a zero hint rather than a prefilled zero; editing a project shall show its saved positive quantities. | MN-01, interpreted; SRC-IMPL | Core | Implemented interpretation; Q-01 remains open. |
| FR-20 | The interface shall call a selectable recipe a “mix” or “mixture”, distinguishing it from a production batch. | MN-06 | Follow-up | Partial; existing “Batch” recipe names remain (Q-03). |
| FR-21 | The project calculator shall not require an MPa input or display MPa on its mix-selection cards. | MN-10, proposed screen interpretation | Follow-up | Partial: no strength input, but MPa remains on cards; confirm Q-06. |
| FR-22 | The system shall provide an application-wide currency setting. Permissions, application to prices, and treatment of existing records require clarification before detailed acceptance. | MN-07 | Follow-up | Not implemented; Q-04 blocks detailed specification. |
| FR-23 | The requested removal of “wheelwide” from price setting shall be specified after confirming the term, affected controls, and affected screens. No broader removal is inferred. | MN-09 | Clarify | Clarification required; this is a tracked request, not an executable acceptance requirement (Q-05). |

## 4. Business rules

| ID | Rule |
|---|---|
| BR-01 | Full and Half block counts are separate demands. A blank or zero count means no demand for that type. At least one type must have a positive integer count. |
| BR-02 | One selected mix supplies the entire project. A Both mix supports either or both block types; a Full-only or Half-only mix supports only its matching type. An existing project's deactivated mix can be retained when editing. |
| BR-03 | For each requested type, batches = ceiling(requested blocks / mix yield). The configured yield is applied separately to each type; Full and Half counts are not combined before rounding. |
| BR-04 | A material's required quantity is its amount per batch multiplied by the sum of required batches. Tonnes = quantity × configured tonnes per unit, when weight is available. Current starting weights are 0.100 t per sand wheelbarrow, 0.090 t per stone wheelbarrow, and 0.050 t per cement bag; these are editable assumptions. |
| BR-05 | Use the newest project-specific price if present; otherwise use the most recently reviewed approved default price, with creation time as a secondary ordering. Pending and declined default prices are not used. Project-specific prices take effect without a separate price review; the accountant considers them in project review. |
| BR-06 | Convert a per-tonne price to a base-unit price by multiplying by tonnes per unit. The current per-m³ price for wheelbarrow materials is divided by 16. Each material subtotal is rounded to two decimal places; project total is the sum of material subtotals. Average cost per requested block is total / requested blocks, rounded to two decimals. It is not cost per produced block. |
| BR-07 | A complete total requires at least one recipe ingredient, requested blocks, a price for every ingredient, and a single currency across the prices. Currency codes are compared without case differences. No exchange-rate conversion is performed. |
| BR-08 | Direct project changes are limited by status as shown below. Approval does not save a frozen estimate; shared default prices, mix contents, or material weights can still affect the live calculation before completion. |
| BR-09 | Completion saves the estimate and ends manager transitions. The normal project workflow does not edit, re-price, delete, or reopen a completed project. This is not a guarantee against privileged administrative changes. |

### 4.1 Project transitions

| Current state | Actor and action | Condition | Result |
|---|---|---|---|
| Draft | Manager submits | A mix is selected. A complete price set is not required merely to submit. | Pending |
| Pending | Manager recalls | Project is still Pending. | Draft |
| Pending | Accountant approves | Total is calculable under BR-07. | Approved; visible to Creators |
| Pending | Accountant declines | A non-empty comment is supplied. | Draft; decision retained |
| Approved | Manager completes | Total is calculable under BR-07. | Completed; estimate saved |
| Completed | Manager requests another state | No reopening transition exists. | Remains Completed |

Project name, quantities, and mix selection can be edited only in Draft. Project prices can be changed in Draft or Pending. “Declined” is a review decision, not a project state.

### 4.2 Role permissions

| Action | Manager | Accountant | Creator | Superuser |
|---|---|---|---|---|
| Read projects | All | All | Approved / Completed only | All |
| Create, edit, delete projects | Subject to status and protection rules | No | No | Subject to the normal workflow rules |
| Set project prices | Draft / Pending | No | No | Draft / Pending |
| Maintain mixes/materials; propose default prices | Yes | No | No | Yes |
| Read mixes, materials, price history | Yes | Yes | No | Yes |
| Review prices and Pending projects | No | Yes | No | Yes |
| Submit, recall, complete projects | Yes, subject to transitions | No | No | Yes, subject to transitions |
| Provision accounts through administration | No | No | No | Yes |
| Change a future global currency setting | Not specified | Not specified | Not specified | Not specified |

Managers are not restricted to their own projects in the current implementation.

## 5. Quality requirements

These requirements use observable invariants rather than unsupported performance targets. They describe current baseline expectations.

| ID | Requirement and scope | Quality attribute | Verification reference |
|---|---|---|---|
| NFR-01 | Protected project-changing and review actions shall enforce role permissions even when a signed-in user sends a direct request rather than using the visible controls. | Security: integrity / access control | `RoleTests.test_only_manager_can_create_edit_and_delete`; `ProjectStatusTests.test_manager_cannot_approve`; `ProjectStatusTests.test_creator_cannot_review` |
| NFR-02 | Given unchanged requested counts, recipe, yield, material weights, and effective prices, repeated authoritative calculations shall return identical material quantities and two-decimal monetary totals. | Functional suitability: correctness | BR-03–BR-07; `EstimateTests.test_batches_round_up`; `EstimateTests.test_cost_per_block_for_seeded_batches` provide fixed expected examples, not an exhaustive repeatability proof. |
| NFR-03 | A completed project's saved total shall remain unchanged when a later default material price becomes approved. | Reliability: preservation of recorded results | `ProjectStatusTests.test_history_ignores_later_price_changes` |
| NFR-04 | Material amounts and prices shown in a non-completed project's breakdown shall identify their units; the price breakdown shall identify default versus project-specific price sources. | Interaction clarity | `ViewTests.test_project_page_shows_tonnes_and_total`; review of the project-detail template. Full display coverage is not claimed. |

No response-time, uptime, recovery-time, or cross-browser compliance claim is made in this baseline. Passwords use the existing account system's hashed storage; this document does not introduce encryption or token-format requirements.

## 6. Verification references and traceability

[User stories](user-stories.md) links every story to requirements, use cases, and acceptance criteria. The table below identifies existing automated evidence for the main requirements; method names are in [core/tests.py](../core/tests.py) unless stated otherwise.

| Requirements | Existing evidence |
|---|---|
| FR-01, FR-02 | [accounts/tests.py](../accounts/tests.py): `AdminUserCreationTests.test_admin_creates_user_with_email_name_and_role`; `AuthFlowTests.test_login_with_email`; `AuthFlowTests.test_register_page_is_gone` |
| FR-03, FR-04 | `ViewTests.test_create_project_requires_blocks_and_mixture`; `ViewTests.test_create_project_rejects_mixture_for_other_block_type`; `EstimateTests.test_full_and_half_blocks_share_one_mixture` |
| FR-05, FR-06 | `EstimateTests.test_pricing_data_for_live_totals`; `ViewTests.test_project_page_shows_tonnes_and_total`. These do not execute the browser preview or verify its mixed-currency case. |
| FR-07, FR-08 | `RoleTests.test_manager_edits_project_name_and_blocks`; `RoleTests.test_manager_deletes_project`; `ViewTests.test_create_mix_with_fixed_materials`; `MaterialFormTests.test_add_bagged_material_with_weight_in_kg` |
| FR-09, FR-10 | `EstimateTests.test_pending_price_is_not_used`; `ViewTests.test_accountant_can_approve_price`; `RoleTests.test_accountant_declines_with_corrected_price` |
| FR-11 | `ProjectPriceTests.test_project_price_does_not_change_other_projects_or_defaults`; `ProjectPriceTests.test_newest_project_price_wins_and_reset_restores_default` |
| FR-12–FR-14 | `ProjectStatusTests.test_pending_back_to_draft`; `ProjectStatusTests.test_accountant_approves_pending_project`; `ProjectStatusTests.test_accountant_declines_back_to_draft_with_comment`; `ProjectStatusTests.test_accountant_cannot_approve_unpriced_project` |
| FR-15, FR-16 | `ProjectStatusTests.test_completing_saves_costs_as_history`; `ProjectStatusTests.test_completed_project_is_locked`; `RoleTests.test_creator_sees_only_approved_projects` |
| FR-17 | `RoleTests.test_project_list_filters_by_status_and_search` |
| FR-18 | [project-detail template](../core/templates/core/project_detail.html): common material breakdown and project review section. No dedicated accountant-layout test is claimed. |
| FR-19 | `QuantityHintTests.test_block_counts_start_empty_with_zero_hint`; `QuantityHintTests.test_edit_shows_saved_count_and_leaves_missing_type_empty` |
| FR-20–FR-23 | No complete acceptance evidence. The strength-input test does not assert absence of MPa on cards. Currency and ambiguous price-entry changes must not be marked passed. |

These are evidence pointers, not a fresh execution report or a claim that all acceptance criteria pass.

## 7. Known boundaries and unresolved issues

- The live mix-card preview does not reject mixed currencies, whereas the saved project's calculation does. FR-05 is therefore Partial; a displayed preview must not be taken as proof of a valid final total in this case.
- Approval blocks direct project edits but does not freeze the calculation's shared inputs. Q-07 must be resolved before describing an approved amount as immutable.
- Completion preserves the numeric estimate and recipe breakdown, but material names and weight-based tonne displays still use the current material configuration. It is not a fully immutable copy of all material attributes.
- Price-decline comments are not mandatory or recorded as project-style review comments. The mandatory comment rule applies to project decline.
- The current role name Creator means read-only access, not project creation. Creators can currently see financial amounts.
- FR-20–FR-23 and the open questions in [Customer feedback](customer-feedback.md) remain visible follow-up items, not claims about delivered features.

## 8. Glossary

| Term | Meaning in this baseline |
|---|---|
| Mix / mixture | The recipe and configured block yield selected for the entire project. |
| Batch | One production run of a mix. It is not a synonym for the selectable recipe. Existing recipe names containing “Batch” await Q-03. |
| Yield | Blocks produced per batch, as configured for the mix. |
| Full / Half | The two supported block categories, F and H. Counts are calculated separately using the chosen mix. |
| Default price | An approved shared material price used unless the project has its own price. |
| Project price | A material price specific to one project, taking precedence over its default. |
| Estimate | Calculated material requirements and material cost; not a complete production budget or supplier quotation. |
| Pending | A project or proposed default price waiting for review. |
| Approved | A project accepted by an accountant, or a default price accepted for use. These are different review contexts. |
| Completed | A project whose estimate has been saved as history and whose normal workflow is closed. |
| Creator | The application's read-only business role for Approved and Completed projects. |
| Tonne | 1,000 kg; shown as `t`. |
| Wheelbarrow / bag | Operational material units with configurable weight. Price-entry treatment is subject to Q-05. |
| MPa | A stored mix-strength label. It does not determine the cost formula; its calculator display is subject to FR-21. |
