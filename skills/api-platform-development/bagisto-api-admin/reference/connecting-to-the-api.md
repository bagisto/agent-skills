# Connecting to the Admin API

Read this before writing any call. Covers auth, the verify protocol, the list→detail→action pattern, pagination, permissions, and errors. Exact request/response shapes always come from the api-docs endpoint page.

## 1. The backend + the docs

- REST base: `/api/admin/*`. GraphQL: `POST /api/admin/graphql` (admin only — **separate** from the shop `/api/graphql`).
- **Source of truth:** `https://api-docs.bagisto.com` (Admin API) + its `/llms.txt` index. Fetch `llms.txt` to find the endpoint, open its page for the exact body/response.
- Store the base URL + token in env vars; never ship the admin token in a public client bundle you don't control.

## 2. Verify-before-coding protocol (every new call)

1. **PAUSE** — don't write from memory.
2. **QUERY** — open the endpoint's api-docs page (or the MCP doc server).
3. **VERIFY** — confirm path, method, required fields, filters, response shape.
4. **IMPLEMENT** — write the call with the verified shape.
5. **CHECK** — validate the response/types.

## 3. Authentication (pre-issued Integration token)

Every admin request carries:

```
Authorization: Bearer <id>|<token>
```

- **There is no admin login endpoint.** The token is created once in the store's admin panel: **Configuration → API → Integration → Module Settings** (enable the module), then **Settings → Integration → Create → Generate**. The plaintext token is shown once.
- A token is **scoped to one admin** and **capped by that admin's role permissions** — it can never do more than its owner could in the panel.
- `GET /api/admin/get` (GraphQL `readAdminProfile`) returns the token's own admin profile — use it as a "who am I / is the token valid" check.
- Document auth once; don't re-prompt per screen.

### Discovery — build navigation + gate UI without hardcoding

Two read-only endpoints (REST + GraphQL) tell a client what the **current token** can do, so you don't hardcode the menu or learn permissions by hitting 403s:

- `GET /api/admin/menu` (GraphQL `getAdminMenu`) — the admin sidebar as a nested tree, **filtered to the token's role**. Each node carries its label, hierarchy, permission key, and the matching API endpoint (`apiResource: { rest, graphql }`, or `null` for group headers / panel-only screens). Drive your nav from this.
- `GET /api/admin/permissions` (GraphQL `getAdminPermissions`) — the token's effective `{ permissionType, permissions }` (`["*"]` for full access). Use it to show/hide actions.

## 4. The list → detail → action pattern

Almost every admin screen is one of these three calls:

```
  LIST    GET /api/admin/<resource>?page=&per_page=&<filters>   → { data:[…], meta:{…} }
            │ pick a row
            ▼
  DETAIL  GET /api/admin/<resource>/{id}                         → full record (relations embedded)
            │ act on it
            ▼
  ACTION  POST/PUT/DELETE /api/admin/<resource>[/{id}][/<action>] → result (+ often the refreshed record)
```

- **Detail embeds relations** — the detail payload inlines what the screen needs (items, addresses, etc.), so you rarely chain follow-up GETs.
- **Actions carry eligibility rules** — e.g. an order can only be cancelled/invoiced/shipped/refunded in certain states; the endpoint returns a clear error when it can't. Each menu page documents these.

## 5. Pagination & the `{ data, meta }` envelope

Admin collections return:

```json
{ "data": [ /* rows */ ], "meta": { "currentPage": 1, "perPage": 10, "lastPage": 14, "total": 137, "from": 1, "to": 10 } }
```

- Page with `?page=N` + `?per_page=N` (default **10**, cap **50**) plus the per-screen filters (each listing documents its own filter set; multiple filters are **AND**-combined — more filters = more restrictive).
- Count headers are also exposed: `X-Total-Count`, `X-Page`, `X-Per-Page`, `X-Total-Pages`.
- Null fields are included (not stripped).
- GraphQL collections use **cursor** pagination instead (`edges`/`node`, `pageInfo`) — see `graphql.md`.

## 6. Permissions

- The token inherits the admin's role. An endpoint the role lacks permission for returns **403** — surface "you don't have permission for this" rather than a generic error.
- Mass-actions and destructive deletes carry the same per-feature permission as their single-record counterparts.

## 7. Error handling

| Status | Meaning | UX |
|--------|---------|----|
| 200 / 201 | Success | — |
| 204 | Deleted (no body) | Remove the row |
| 401 | Unauthenticated (missing/expired/revoked token) | Re-issue the token in the panel |
| 403 | Forbidden (role lacks the permission) | "No permission for this action" |
| 400 | Bad input / business-rule violation | Friendly message |
| 404 | Not found | — |
| 409 | Wrong-step (e.g. Create-Order sequence) | Send the user to the missing prerequisite |
| 422 | Validation / ineligible action | Inline field/eligibility message |

## 8. Data-layer patterns

- Use a query library (TanStack Query, etc.); cache lists keyed by filters+page; invalidate the list/detail query after a mutating action so the table reflects the change.
- Detail responses are the source of truth after an action — many actions return the refreshed record so you can update the view without a follow-up GET.
- A thin typed fetch wrapper that always attaches the Bearer token keeps every call consistent.
