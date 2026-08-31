# Authoring a spec and its page object

## Contents

- [Layout](#layout)
- [The page object](#the-page-object)
- [Fixtures](#fixtures)
- [Test data](#test-data)
- [ACL specs](#acl-specs)
- [Naming](#naming)

## Layout

A feature needs two files: a spec that states intent, and a page object that
owns every locator.

```
tests/e2e-pw/
├── tests/<section>/<feature>.spec.ts        # what should happen
└── pages/admin/<section>/<Feature>Page.ts   # how to drive it
```

`tests/` mirrors the admin menu (`catalog/`, `customers/`, `marketing/`,
`settings/`, `appearance/`). Put a new spec where its menu section sits, so the
shard split stays even and the file is findable from the UI.

Note one existing exception: every ACL spec lives in `tests/settings/acl/`,
including `catalog-acl.spec.ts` and `cms-acl.spec.ts`, which cover other
sections. Follow that, not the menu, for ACL.

## The page object

Extend `BasePage`, which supplies `visit()` (relative to the configured base
URL) and `dataPath()` (files under `tests/e2e-pw/data`). Resolve paths through
`utils/paths.ts` rather than walking up from `__dirname`.

```ts
import { expect, type Page } from "@playwright/test";
import { BasePage } from "../../BasePage";
import { generateName } from "../../../utils/faker";

export class SectionsPage extends BasePage {
    constructor(page: Page) {
        super(page);
    }

    private get createButton() {
        return this.page.getByTitle("Create Section");
    }

    private sectionRow(name: string) {
        return this.page
            .locator("div[data-draggable]")
            .filter({ hasText: name });
    }

    async open(): Promise<void> {
        await this.visit("admin/appearance/themes/default/sections");
        await this.page.waitForLoadState("networkidle");
        await expect(this.createButton).toBeVisible();
    }

    async createSection(type: string): Promise<string> {
        const name = generateName();
        // …drive the UI, assert the outcome…
        return name;
    }
}
```

Rules that hold across the existing suite:

- **Locators are private getters or private methods.** A spec never contains a
  selector. A locator that takes an argument (a row by name, a field by label)
  is a private method, not a getter.
- **Member order: getters, then private helpers, then public actions.** A
  private helper wedged between two public methods is the same defect the
  `bagisto-package-development` skill names for PHP classes.
- **Public methods are named for the user's intent** — `createSection`,
  `deleteSection`, `expectFooterLinksNotOffered` — and assert their own outcome.
  A method that only clicks and returns pushes the assertion into the spec,
  where the locator is not available.
- **Return what the caller needs to assert on**, usually the generated name.
- **Docblock any method whose reason is not obvious from its name** — a
  `/** … */` above the method, never a comment inside the body.

## Fixtures

`setup.ts` exports `test` with two fixtures. Import from there, never from
`@playwright/test` directly, or you lose them:

```ts
import { test } from "../../setup";
```

| Fixture | Gives you |
|---|---|
| `adminPage` | A page already logged into admin, via cached `storageState`, re-logging in if the session expired. Also `fillInTinymce(iframeSelector, content)`. |
| `shopPage` | A fresh storefront context, no auth. Also `fillInTinymce`. |

Never call the login flow yourself in a spec — `adminPage` has done it.

## Test data

Use `utils/faker.ts` rather than literals, so parallel shards and repeat runs do
not collide: `generateName`, `generateEmail`, `generateSKU`, `generateSlug`,
`generateDescription`, `getImageFile`, and others.

A generated name is also what makes a row-scoped assertion possible — it is
unique, so `filter({ hasText: name })` resolves to exactly one row.

Binary fixtures live in `tests/e2e-pw/data/` and are reached with
`this.dataPath("file.png")`.

## ACL specs

ACL coverage is data-driven rather than hand-written per role. `pages/admin/acl/`
holds a class chain (`shared.ts` → per-section files → `index.ts` exporting
`ACLManagement`) plus `routes.ts`, a map from a permission key to what that role
may and may not reach:

```ts
"appearance->themes": {
    allowed: "admin/appearance/themes",
    sidebar: "/admin/appearance/themes",
    notAllowed: [
        "admin/appearance/themes/default/sections",
        "admin/dashboard",
        // …
    ],
},
```

A spec then creates the role, creates a user, and verifies:

```ts
const aclManagement = new ACLManagement(adminPage);
await aclManagement.createRole("custom", ["appearance"]);
await aclManagement.editRolePermission(["appearance.sections"]);  // untick siblings
await aclManagement.createUser();
await aclManagement.verfiyAssignedRole(["appearance->themes"]);
```

Notes that catch people out:

- **Ticking a parent permission ticks every descendant**, and ticking a child
  ticks its ancestors. `editRolePermission([...])` **unticks** the keys passed,
  which is how a single-permission role is produced.
- **`sidebar` is optional.** A page reached from inside another screen has no
  menu entry, so omit it rather than asserting a link that cannot exist.
- **Permissions are exact-match**, not prefix-match: holding `appearance` alone
  grants neither `appearance.themes` nor `appearance.sections`. Verify what a
  role actually opens before asserting it.
- `verfiyAssignedRole` is spelled that way in the codebase. Match it.

## Naming

- Spec file: `<feature>.spec.ts`, lower-kebab.
- `test.describe("<feature> management")`, matching the existing suite.
- Test title: `should <expected outcome>` — describe the behaviour, not the
  mechanism. `should stage a reorder until it is published`, not
  `should call the reorder endpoint`.
- Page object: `<Feature>Page.ts`, PascalCase class of the same name.
