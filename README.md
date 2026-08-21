# bagisto/agent-skills

Agent skills for [Bagisto](https://bagisto.com) — a Laravel-based open-source e-commerce platform.

These skills provide domain-specific, reusable context for AI agents (Claude Code, Cursor, Windsurf, etc.) working inside a Bagisto codebase.

## Available Skills

### `bagisto-coding-standards`

The conventions this codebase holds to — Laravel idiom, code style, comments, data access, Blade, security, localization.

**Activates when:** writing, changing or reviewing any Bagisto PHP or Blade — or when the user mentions `standards`, `conventions`, `code style`, `docblock`, `comments`, `repository pattern`, `blade`, `binding`, `event`, `migration`, `security`, `XSS`, `authorization`, `escaping`.

---

### `bagisto-package-development`

Package development in Bagisto.

**Activates when:** creating packages, migrations, models, repositories, routes, controllers, views, localization, DataGrid, menus, ACL, or system configuration — or when the user mentions `package`, `migration`, `model`, `repository`, `controller`, `DataGrid`, `menu`, or `ACL`.

---

### `bagisto-shipping-method-development`

Shipping method development in Bagisto.

**Activates when:** creating shipping methods, integrating shipping carriers like FedEx, UPS, DHL, or any third-party shipping provider — or when the user mentions `shipping`, `shipping method`, `shipping carrier`, `delivery`, or needs to add a new shipping option to checkout.

---

### `bagisto-payment-method-development`

Payment gateway development in Bagisto.

**Activates when:** creating payment methods, integrating payment gateways like Stripe, PayPal, or any third-party payment processor — or when the user mentions `payment`, `payment gateway`, `payment method`, `Stripe`, `PayPal`, or needs to add a new payment option to the checkout.

---

### `bagisto-product-type-development`

Product type development in Bagisto.

**Activates when:** creating custom product types, defining product behaviors, or implementing specialized product logic — or when the user mentions `product type`, `custom product`, or needs to implement product-specific behavior.

---

### `bagisto-shop-theme-development`

Shop theme development in Bagisto.

**Activates when:** creating custom storefront themes, modifying shop layouts, building theme packages, or working with Vite-powered assets for the customer-facing side of the application.

---

### `bagisto-shop-advance-theme-development`

Shop Advance Theme Development in Bagisto — an advanced, end-to-end storefront theme workflow that ships design references, scaffolding scripts, templates, and full Playwright commerce coverage.

**Activates when:** creating, redesigning, extending, debugging, validating, packaging, testing, or upgrading production Bagisto storefront themes — UI/UX design direction, design tokens and commerce design systems, Shop theme registration and resource overlays, Blade/Vue components, Vite/Tailwind assets, dynamic admin-controlled and theme-customization content, channels, localization/RTL, accessibility, performance, distributable packages, or resolving theme inheritance and asset-manifest failures.

---

### `bagisto-admin-theme-development`

Admin theme development in Bagisto.

**Activates when:** creating custom admin themes, modifying admin layouts, building admin theme packages, or working with admin panel styling and interface customization.

---

### `bagisto-pest-testing`

Tests applications using the Pest 3 PHP framework.

**Activates when:** writing tests, creating unit or feature tests, adding assertions, testing Livewire components, architecture testing, debugging test failures, working with datasets or mocking — or when the user mentions `test`, `spec`, `TDD`, `expects`, `assertion`, `coverage`, or needs to verify functionality works.

---

### `bagisto-data-transfer`

Bulk imports — Importer classes, file sources, and the queued import pipeline.

**Activates when:** adding or changing a Bagisto import — an Importer class, a file source, the importers registry, the queued import pipeline, or a stuck or failing import job — or when the user mentions `import`, `importer`, `data transfer`, `CSV`, `XLSX`, `XML`, `bulk upload`, `import batch`, `queued import`.

---

### `bagisto-theme-sections`

The Appearance area — theme sections, the editor and its preview, drafts and publishing.

**Activates when:** working on the Bagisto Appearance area — theme sections, the section editor and its storefront preview, draft and publish behaviour, section media, or the theme gallery — or when the user mentions `section`, `theme section`, `appearance`, `preview`, `draft`, `publish`, `unsaved changes`, `theme gallery`.

---

### `bagisto-attribute-development`

The EAV attribute system — attributes, families, groups, options, and how values are stored.

**Activates when:** working with Bagisto's EAV attribute system — adding or changing an attribute, family or group, reading or writing a product attribute value, or debugging a value that reads back empty or from the wrong locale or channel — or when the user mentions `attribute`, `EAV`, `attribute family`, `attribute option`, `value_per_locale`, `value_per_channel`, `product_flat`, `swatch`.

---

### `bagisto-datagrid-development`

Admin listing pages — DataGrid classes, columns, filters, actions and export.

**Activates when:** building or changing a Bagisto admin listing page — a DataGrid class with columns, search, filters, sorting, row actions, mass actions or export, and the controller and Blade view that render it — or when the user mentions `datagrid`, `admin listing`, `add a column`, `mass action`, `prepareQueryBuilder`, `listing page`, `grid filter`, `export grid`.

---

### `bagisto-playwright-testing`

End-to-end testing with Playwright — specs, page objects, ACL role coverage and failing runs.

**Activates when:** writing, changing or debugging a Bagisto end-to-end test — Playwright specs, page objects, ACL role coverage, fixtures, or a failing E2E run in CI — or when the user mentions `playwright`, `e2e`, `end to end`, `spec.ts`, `page object`, `browser test`, `flaky test`, `shard`.

---

### `bagisto-code-review`

Reviewing a change or PR — correctness, security, architecture, conventions.

**Activates when:** reviewing Bagisto code changes or a pull request for correctness, convention compliance or quality, or when asked whether a change is ready to merge — or when the user mentions `review`, `code review`, `PR review`, `conventions`, `violations`, `code quality`, `ready to merge`.

---

### `bagisto-git-workflow`

Branches, commit messages, CHANGELOG entries and pull requests.

**Activates when:** branching, committing, writing a CHANGELOG entry or opening a pull request against a Bagisto repository — or when the user mentions `branch`, `commit`, `commit message`, `PR`, `pull request`, `changelog`, `merge`, `release notes`.

---

### `bagisto-change-verification`

The completion gate — code style, tests, end-to-end tests and translation completeness.

**Activates when:** a change is about to be called done, or when asked to run the verification gates — or when the user mentions `verify`, `is this done`, `run the gates`, `pint`, `pest`, `playwright`, `translations check`, `ready to commit`.

---

### `bagisto-api-develop`

Install / remove / extend the `bagisto-api` package.

**Activates when:** installing or removing the package, or adding/changing a REST or GraphQL endpoint, a resource, or an admin menu's API — or when the user mentions `ApiResource`, `Provider`, `Processor`, `DTO`, "install the package", or "add an endpoint". (Install and removal run only on explicit request.)

---

### `bagisto-api-shop`

Build a storefront app or UI on the **Shop API** (`/api/shop/*` + `/api/graphql`).

**Activates when:** building a customer-facing storefront, catalog/cart/checkout flow, customer account, or mobile shopping app — or when the user mentions products, cart, checkout, coupons, wishlist, or customer login/account.

---

### `bagisto-api-admin`

Build an admin app or UI on the **Admin API** (`/api/admin/*` + `/api/admin/graphql`).

**Activates when:** building an admin dashboard, back-office panel, or an order/catalog/customer/marketing/CMS/settings management screen — or when the user mentions admin orders, products, customers, reporting, or "admin panel on the API".

---

### `bagisto-documentation`

Write and maintain any Bagisto documentation site — developer documentation, the merchant user guide, or another guide. Judges the audience first, then covers page content, code samples, screenshots, the sidebar and redirects.

**Activates when:** writing or updating a documentation page, capturing or replacing a screenshot, or moving and deleting pages — or when the user mentions docs, the user guide, developer documentation, or a doc redirect.

---

## Install

Install all skills from this repo into your AI agent:

```bash
npx skills add bagisto/agent-skills
```

Install a specific skill only:

```bash
npx skills add bagisto/agent-skills --skill "bagisto-admin-theme-development"
npx skills add bagisto/agent-skills --skill "bagisto-attribute-development"
npx skills add bagisto/agent-skills --skill "bagisto-change-verification"
npx skills add bagisto/agent-skills --skill "bagisto-code-review"
npx skills add bagisto/agent-skills --skill "bagisto-coding-standards"
npx skills add bagisto/agent-skills --skill "bagisto-data-transfer"
npx skills add bagisto/agent-skills --skill "bagisto-datagrid-development"
npx skills add bagisto/agent-skills --skill "bagisto-documentation"
npx skills add bagisto/agent-skills --skill "bagisto-git-workflow"
npx skills add bagisto/agent-skills --skill "bagisto-package-development"
npx skills add bagisto/agent-skills --skill "bagisto-payment-method-development"
npx skills add bagisto/agent-skills --skill "bagisto-pest-testing"
npx skills add bagisto/agent-skills --skill "bagisto-playwright-testing"
npx skills add bagisto/agent-skills --skill "bagisto-product-type-development"
npx skills add bagisto/agent-skills --skill "bagisto-shipping-method-development"
npx skills add bagisto/agent-skills --skill "bagisto-shop-advance-theme-development"
npx skills add bagisto/agent-skills --skill "bagisto-shop-theme-development"
npx skills add bagisto/agent-skills --skill "bagisto-theme-sections"
npx skills add bagisto/agent-skills --skill "bagisto-api-develop"
npx skills add bagisto/agent-skills --skill "bagisto-api-shop"
npx skills add bagisto/agent-skills --skill "bagisto-api-admin"
```

## Repository Structure

```
agent-skills/
├── bin/
│   └── lint-skills.sh                          # the authoring standard, enforced
├── .github/workflows/skills-tests.yml          # runs the linter and its tests on every push
├── skills/
│   ├── CONTRIBUTING.md                         # the authoring standard, written down
│   ├── .lint-allow                             # skills exempted from the size cap, with a reason
│   ├── tests/
│   │   └── lint-skills.test.sh                 # proves every lint rule fires
│   ├── api-platform-development/            # grouping folder; its skills are already prefixed
│   │   ├── bagisto-api-develop/             # SKILL.md + reference/
│   │   ├── bagisto-api-shop/                # SKILL.md + reference/
│   │   └── bagisto-api-admin/               # SKILL.md + reference/
│   ├── bagisto-admin-theme-development/     # SKILL.md + assets, creating-a-theme, layouts, reference
│   ├── bagisto-attribute-development/       # SKILL.md + attributes, eav
│   ├── bagisto-change-verification/         # SKILL.md
│   ├── bagisto-code-review/                 # SKILL.md
│   ├── bagisto-coding-standards/            # SKILL.md + 9 references
│   ├── bagisto-data-transfer/               # SKILL.md + importers, pipeline
│   ├── bagisto-datagrid-development/        # SKILL.md + actions, columns
│   ├── bagisto-documentation/              # SKILL.md + developer-docs, user-guide, screenshots, publishing
│   ├── bagisto-git-workflow/                # SKILL.md
│   ├── bagisto-package-development/         # SKILL.md + core, data-layer, features, ui
│   ├── bagisto-payment-method-development/  # SKILL.md + implementation, payment-api, reference
│   ├── bagisto-pest-testing/                # SKILL.md + new-package, suite-layout, writing-tests
│   ├── bagisto-playwright-testing/          # SKILL.md + authoring, troubleshooting
│   ├── bagisto-product-type-development/    # SKILL.md + abstract-type, building-a-type, configuration
│   ├── bagisto-shipping-method-development/ # SKILL.md + carrier-api, implementation, reference
│   ├── bagisto-shop-advance-theme-development/   # SKILL.md + workflow
│   ├── bagisto-shop-theme-development/      # SKILL.md + assets, creating-a-theme, layouts, reference
│   └── bagisto-theme-sections/              # SKILL.md + drafts, sections
├── AGENTS.md
└── README.md
```

## Contributing

The authoring standard is [skills/CONTRIBUTING.md](skills/CONTRIBUTING.md). Its
mechanical rules are enforced:

```bash
bin/lint-skills.sh                      # frontmatter, size caps, requires, dangling links
bash skills/tests/lint-skills.test.sh   # proves each rule actually fires
```

A `SKILL.md` is a router of at most 150 lines; depth lives in reference files
beside it, capped at 500 lines each, loaded only when a task needs them.
