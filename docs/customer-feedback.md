# Latest customer feedback

**Source:** SRC-MEETING. Supplied by the team; meeting date and participants not provided.

**Status:** interpretation for review, not a signed meeting record.

## 1. Original notes

The wording is preserved, including spelling and ambiguous terms:

> The zero stayed a zero in the full block half block calculator
>
> The small field for selecting a batch
> After calacting the price it's confusing
>
> In the accountant view should see the materials directly
>
> Make it simplaer
> Rename batch to a mix
> Have a global setting for currencies
> And the default price of each material
>
> Remove the wheelwide from the set prices
> Remove mpa from the batches calculator
>
> One mixture for all of the project

## 2. Interpretation and current coverage

“Current” below is based on code inspection. It does not establish that the customer has reviewed the latest interface.

| ID | Note | Working interpretation | Current coverage / outstanding work |
|---|---|---|---|
| MN-01 | “The zero stayed a zero…” | Avoid a prefilled zero that the manager must remove before entering a quantity. | **Implemented interpretation:** quantity fields start empty with a `0` placeholder; saved positive quantities appear when editing. The original interaction should still be confirmed (Q-01). |
| MN-02 | “The small field for selecting a batch” | Make mix selection more visible and understandable. | Selectable mix cards now show materials and a project total. This addresses the likely concern, but the note contains no agreed size or layout criterion. |
| MN-03 | “After calacting the price it's confusing” | Keep the calculated total, selected mix, and material breakdown understandable together. | These are shown on the project page. The precise confusing interaction is unspecified (Q-02); do not claim the concern has been resolved. |
| MN-04 | “In the accountant view should see the materials directly” | The accountant should review material quantities, prices, and subtotals in the project being approved. | **Implemented at project-detail level:** the breakdown is on the same page as the decision. Whether “directly” means the list, initial viewport, or review page remains open (Q-02). |
| MN-05 | “Make it simplaer” | Reduce unnecessary choices in the main project calculation workflow. | A direction, not a measurable standalone requirement. FR-04, FR-18–FR-23 translate specific related requests; unresolved details remain explicit. |
| MN-06 | “Rename batch to a mix” | Use “mix” or “mixture” for the recipe being selected. Reserve “batch” for one production run. | **Partial:** main headings use mix/mixture, but initial recipe names still include “Batch 1”–“Batch 4 (optimum)”. Treatment of those names needs a decision (Q-03). |
| MN-07 | “Have a global setting for currencies” | Provide one application-wide currency setting instead of requiring repeated currency choices. | **Not implemented.** Prices currently carry individual currencies. The setting's owner and effect on existing prices must be specified (Q-04). |
| MN-08 | “And the default price of each material” | Maintain shared default material prices, reused unless a project overrides them. | **Implemented:** default prices appear on Materials; new proposals take effect after accountant approval. Their placement alongside the future currency setting is not specified. |
| MN-09 | “Remove the wheelwide from the set prices” | Possibly remove wheelbarrow-based price entry or related wording from price-setting forms. | **Clarification required.** Project price entry already uses tonnes when weight is known. Default price entry still allows base units, including wheelbarrows. Do not infer removal from recipes or production quantities. |
| MN-10 | “Remove mpa from the batches calculator” | Omit MPa from the main project calculator, without assuming removal from mix configuration. | **Partial:** there is no required-strength input, but MPa is still displayed on mix-selection cards. FR-21 captures the proposed screen scope. |
| MN-11 | “One mixture for all of the project” | Select one compatible mixture for all Full and Half blocks in a project. | **Implemented:** a project has one selected mix. |

Implementation evidence: [quantity input](../core/templates/core/_quantity.html), [project form](../core/templates/core/project_form.html), [project detail](../core/templates/core/project_detail.html), [materials page](../core/templates/core/materials.html), [forms](../core/forms.py), and [price selection and calculation](../core/services.py).

## 3. Questions to resolve

| ID | Question | Affected items | Status |
|---|---|---|---|
| Q-01 | Did the zero remain in the input, prevent replacement, or remain in the calculated result? Is the current empty-input/placeholder behaviour the intended fix? | MN-01; FR-19 | Open |
| Q-02 | Which screen or action was confusing after calculation? Where should an accountant see the materials “directly”: in the project list, at the top of the project, or simply on the review page? | MN-02–MN-05; FR-05, FR-06, FR-18 | Open |
| Q-03 | Should the existing “Batch 1”–“Batch 4” recipe names also become “Mix 1”–“Mix 4”, or does the rename concern interface labels only? | MN-06; FR-20 | Open |
| Q-04 | Who may change the global currency? Is it a default for new prices or a mandatory currency for all prices? What happens to existing and completed projects? Is conversion expected, and if so using which rates? | MN-07; FR-22; US-15 | Open |
| Q-05 | Does “wheelwide” mean “wheelbarrow”? Should its price-entry option, conversion preview, or both be removed? Does this apply to default prices only or all price-setting screens? | MN-09; FR-23 | Open |
| Q-06 | Does removing MPa mean both input and display in the project calculator? May it remain in mix configuration and project details? | MN-10; FR-21; AC-14 | Open |
| Q-07 | Is the current rule acceptable that approval blocks direct project edits, but the amount is fixed only on completion and can still change through shared prices or mix settings beforehand? | BR-07–BR-09; FR-13, FR-15 | Open; implementation-derived |

There is no recorded resolution or customer sign-off for these questions. In particular, a global currency request is not evidence of an agreed exchange-rate conversion feature.
