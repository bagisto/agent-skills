# Coding standards + conventions checklist

These are the rules the package is built to. Apply them to every new resource and check them in review. Each item is one line; the per-resource detail lives in the package `CLAUDE.md`.

## Coding standards

- **DRY — one home per cross-cutting concern.** Before writing a helper, grep for an existing one (auth → `AdminAuthHelper`/`ChecksAdminPermission`; cart resolution → `AdminCartGuard`; envelope → `AdminCollectionEnvelopeNormalizer`; etc.). Two resources sharing more than a few mechanical lines → extract a base class / trait / guard. When DRY conflicts with parity, **parity wins for behaviour, DRY wins for our own structure**.
- **Model-relations-driven design.** Read the core model's `with` / relations / `appends` / `casts` / `translatedAttributes` first, then surface those fields. Don't add API files for relations the admin UI doesn't expose.
- **Mirror Bagisto core.** Reuse the same repository, validation rules, events, and permission key the core controller uses. Fire the same `*.before` / `*.after` events so core listeners keep working.
- **No code comments.** Package files are kept comment-free (functional OpenAPI `summary`/`description` strings are fine; drop `//` and docblocks).
- **Lint with Pint** — `./vendor/bin/pint packages/Webkul/BagistoApi`.
- **Single-file lang.** All strings in `src/Resources/lang/en/app.php`, namespaced by top-level key (`app.admin.*`). Never add a second lang file. Watch indentation — a mis-indented duplicate key is silently kept at the wrong path and leaks the raw key.

## The conventions checklist (per resource)

- [ ] Build **both** REST and GraphQL on the resource (same Provider/Processor serves both).
- [ ] **Tag** every Provider (`ProviderInterface`) and Processor (`ProcessorInterface`) in `BagistoApiServiceProvider::register()`.
- [ ] Output DTO / resource properties are **snake_case** + `use AcceptsCamelCaseWrites` — multi-word fields must resolve over GraphQL; output still surfaces as camelCase via `OutputOnlySnakeToCamelNameConverter`. **Add a GraphQL test that queries a multi-word field.**
- [ ] Declare **`extraArgs`** on `QueryCollection` for every custom GraphQL filter. Never set a custom `name:` on `QueryCollection`.
- [ ] Admin collections return the `{ data, meta }` envelope (free via `AbstractAdminCollectionProvider`).
- [ ] `normalizationContext: ['skip_null_values' => false]` on every Eloquent-backed resource.
- [ ] Pagination is `?per_page=N` (+ `?page=N`), default 10, cap 50. Custom REST providers must read `request()->query('per_page')` and apply the same default + cap.
- [ ] Nested object/list fields are **plain associative arrays**, not typed-DTO arrays (avoids the IRI-serialisation trap). Query them bare over GraphQL (`items { id sku }`), not as `{ edges { node } }`.
- [ ] Correct exception → status (see `api-structure.md`): 401 / 403 / 400 / 404 / 422 / `OperationFailedException` for GraphQL-null.
- [ ] **Action/result resources** (no `GET /…/{id}`) don't expose a selectable GraphQL `id` — return result fields (`cartId` / `orderId` / `success` / `message`).
- [ ] Detail resource **returns itself**, not a separate `output:` DTO (else the GraphQL `id` 500s — the Invoice template).
- [ ] OpenAPI `requestBody` + `responses` examples filled with **real** data (derive by hitting the endpoint once — never invent fields).
- [ ] Permission gate via `ChecksAdminPermission` / role `permission_type` + `permissions` (read directly — **never call `bouncer()`**; it needs a session admin that token requests don't have).
- [ ] **Parity with the admin panel, not a superset** (see `limitations.md`).
- [ ] Run the resource's **GraphQL test before** the REST test; both green before done.
- [ ] Add a `CHANGELOG.md` entry under `[Unreleased]` and update the `CLAUDE.md` coverage row.

## Permission resolution (admin)

Token requests carry no session-bound admin, so `bouncer()->hasPermission()` always returns false. Resolve via the resolved admin's role: `permission_type === 'all'` passes everything; `'custom'` checks the perm in `role->permissions`; `'same_as_web'` reads the live role. `AdminApiGuard` applies the token's ability scope so a `custom`/`all` token can never exceed its owner's role. Use the `ChecksAdminPermission` trait — don't reinvent the check.
