# Developer guidance and delivery modes

## Contents

- [Select a delivery mode](#select-a-delivery-mode)
- [Keep one quality bar](#keep-one-quality-bar)
- [Create a contract card](#create-a-contract-card)
- [Use the safe implementation loop](#use-the-safe-implementation-loop)
- [Guide a beginner effectively](#guide-a-beginner-effectively)
- [Work efficiently with an experienced developer](#work-efficiently-with-an-experienced-developer)
- [Use common storefront recipes](#use-common-storefront-recipes)
- [Hand off maintainable work](#hand-off-maintainable-work)

Read this reference when the user asks for teaching, a step-by-step implementation, a team handoff, or help suitable for a beginner. Also use it when a task spans Blade, Vue, Tailwind, dynamic theme content, and Bagisto contracts and the ownership boundaries need to be made explicit.

## Select a delivery mode

Choose from evidence in the request; ask only when the choice would materially change the output.

| Mode | Use when | Communication | Implementation granularity |
|---|---|---|---|
| Guided | User is learning Bagisto or asks for explanation | Explain ownership, source contract, command purpose, and expected evidence | One coherent surface at a time with targeted checks |
| Standard | User wants the completed change with useful context | Explain decisions and non-obvious risks | Group related overrides and validate by affected journey |
| Expert | User demonstrates repository and Bagisto fluency and prefers brevity | Lead with diffs, contracts, risks, and evidence | Optimize for reviewable patches and fast regression gates |

Do not equate concise communication with skipped investigation. Do not infer beginner status from grammar or language fluency.

## Keep one quality bar

Apply the same requirements in every mode:

- discover the installed architecture;
- preserve Bagisto contracts and extension seams;
- keep merchant content dynamic where required;
- implement accessible responsive states;
- respect dependency, license, and protected-path policy;
- build and run affected tests;
- report skipped validation and risk;
- avoid activation until required gates pass.

Change how work is explained and divided, not whether safety checks run.

## Create a contract card

Before overriding a meaningful surface, capture a compact contract card in task notes:

```text
Surface:
Installed source view:
Route/controller and variables:
Blade props/slots/attributes:
Vue components/refs/template IDs:
Forms and field names:
API requests/responses:
Render events and payloads:
Dynamic content owner:
Product types/extensions affected:
Fallback/empty/error behavior:
Targeted tests:
```

For a CSS-only adjustment, record only the applicable rows. For product, cart, checkout, account, or layout changes, fill every relevant row from the installed source. This prevents a visual redesign from silently deleting runtime behavior.

## Use the safe implementation loop

Repeat this loop for each coherent surface:

1. **Locate:** resolve the active theme path and exact installed Shop source.
2. **Read:** inspect the full view plus its controller, resources, scripts, events, and tests as applicable.
3. **Contract:** complete the contract card and identify merchant-owned data.
4. **Compose:** apply the approved brief, tokens, states, and responsive behavior.
5. **Override:** copy the exact relative view only when markup must change; prefer token/CSS changes when markup is already suitable.
6. **Validate statically:** run syntax, formatter, translation, theme, and baseline checks that apply.
7. **Validate at runtime:** test the affected journey with console, page-error, failed-request, accessibility, mobile, and RTL evidence as applicable.
8. **Review:** compare against the brief, installed contract, and real content extremes.
9. **Record:** report changed files, behavior, evidence, and remaining risk.

Do not redesign every page before testing the first complete customer path. Establish the shared layout and tokens, prove one representative listing-to-product flow, then expand.

## Guide a beginner effectively

Give concrete orientation before code:

- explain whether the change belongs to theme configuration, package provider, Blade, Tailwind, Vue, theme customization, CMS, channel settings, or a backend repository;
- show the installed source path and the theme override path;
- state why a file is copied or why inheritance is retained;
- explain which values are visual and which are server-authoritative;
- name the command's working directory and expected successful output;
- distinguish source assets from generated public build output;
- point out which files must never be edited directly.

Use small, complete milestones:

1. Confirm the active theme resolves.
2. Establish tokens and base typography.
3. Implement header/navigation without losing runtime responsibilities.
4. Implement one dynamic home section with an empty state.
5. Implement product cards and one listing surface.
6. Implement product detail while preserving every installed type.
7. Style cart and checkout without moving calculations client-side.
8. Complete account, CMS, extension, error, and edge states.
9. Run the release matrix and document rollback.

At each milestone, show what changed, how to verify it, and what remains inherited. Avoid dumping a complete fork on a beginner without explaining its maintenance cost.

Common beginner guardrails:

- Never edit `public/.../build` to change CSS or JavaScript; edit source and rebuild.
- Never modify Shop views directly for a theme override.
- Never invent a route, request field, API shape, render event, or product-type option name.
- Never put authoritative price, discount, tax, stock, shipping, or payment calculations in JavaScript.
- Never hardcode merchant campaign content merely to make a screenshot look complete.
- Never add a package because a visual example uses it; check the installed runtime first.
- Never treat a successful home page as proof that cart and checkout work.

## Work efficiently with an experienced developer

Keep expert handoff compact and evidence-heavy:

- provide discovered identities and architecture decisions once;
- summarize the contract card rather than explaining Blade fundamentals;
- show the maintained override scope and upstream-diff status;
- call out extension, product-type, and data ownership implications;
- report commands, exit status, browser matrix, and skipped gates;
- identify the smallest review boundary and rollback unit.

Do not hide assumptions behind brevity. Surface unsupported architecture, ambiguous dynamic ownership, dependency changes, and activation risk immediately.

## Use common storefront recipes

### Create a modern dynamic homepage

1. Inspect the installed homepage controller, customization repository, supported types, and renderer.
2. Define the visual sequence in the theme brief and identify each section's content owner.
3. Reuse installed customization types when their editor and option schema fit.
4. For a genuinely new schema, complete the customization-component contract and implement Admin validation, editing, rendering, isolation, and tests in the extension package.
5. Design missing, disabled, untranslated, and incomplete content states.
6. Test channel/theme/locale filtering and administrator sort order.

### Redesign category, search, and product cards

1. Preserve query, filters, sort, limit, view mode, pagination, and resource shapes.
2. Define the card anatomy for image, title, price, rating, badges, options, and actions.
3. Use the server/API price and state; do not derive them from displayed strings.
4. Test long names, sale prices, missing images, unavailable items, empty results, grid/list modes, and mobile filters.

### Redesign product detail

1. Discover every installed product type and its exact form fields.
2. Preserve gallery, price/tax, stock, validation, related/up-sell, wishlist, compare, review, SEO, and render-event contracts.
3. Use type-specific views and backend preparation; do not flatten forms into product ID and quantity.
4. Test one representative of every installed type plus failure and out-of-stock states.

### Redesign cart and checkout

1. Treat returned cart resources and checkout APIs as authoritative.
2. Preserve item IDs, option details, totals, coupons, estimates, addresses, shipping, payment, redirects, errors, and duplicate-submit locks.
3. Reduce decorative variance and motion around irreversible actions.
4. Test guest/customer and stockable/non-stockable flows with sandbox integrations in an isolated environment.

### Apply a styling-only change

1. Confirm markup and behavior do not need to change.
2. Prefer semantic token or component-class changes over copying views.
3. Verify Tailwind scans every source that uses the class.
4. Build and test the affected states, including focus, disabled, error, and responsive variants.

## Hand off maintainable work

Give the next developer:

- theme identity, scaffold mode, registration strategy, and active channel state;
- approved design direction, tokens, dials, page exceptions, and anti-goals;
- source-to-override mapping and maintained override scope;
- dynamic content ownership and administrator editing path;
- build working directory, manifest location, and dependency policy;
- test data assumptions and covered product types/extensions;
- formatter, translation, PHP, build, browser, accessibility, and performance evidence;
- baseline status, known warnings, skipped checks, rollback, and next safe change.

The handoff is successful when another developer can explain where content is managed, where visual tokens live, which views are intentionally owned, and how to prove a future change without editing Bagisto source.
