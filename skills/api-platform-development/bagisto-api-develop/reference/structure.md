# Package structure — where things go

Package root: `packages/Webkul/BagistoApi/`. Namespace: `Webkul\BagistoApi\` → `src/`. Provider: `Webkul\BagistoApi\Providers\BagistoApiServiceProvider` (auto-discovered via the package `composer.json` `extra.laravel.providers`).

**Storefront resources live under `src/`; admin resources under `src/Admin/`.** Keep the two trees separate — never put an admin resource in the shop tree or vice-versa.

## The 5-file pattern per resource

| Piece | Storefront path | Admin path | Responsibility |
|-------|-----------------|------------|----------------|
| **Model** | `src/Models/*.php` | `src/Admin/Models/Admin*.php` | The `#[ApiResource]` declaration — REST + GraphQL operations + OpenAPI block. (Admin models are POPOs: response-shape definitions, not Eloquent tables.) |
| **DTO** | `src/Dto/*.php` | `src/Admin/Dto/*Input.php` | Typed input contract — validation surface + GraphQL input type. |
| **Provider** | `src/State/*Provider.php` | `src/Admin/State/*Provider.php` | Read path — auth + query + envelope. |
| **Processor** | `src/State/*Processor.php` | `src/Admin/State/*Processor.php` | Write path — validation + repo call + events + permission gate. |
| **Resolver** | `src/Resolver/` | `src/Admin/Resolver/` | Custom GraphQL query resolvers (only when the default item/collection resolver won't do). |
| **Lang** | `src/Resources/lang/en/app.php` | same file | All user-facing strings — **single file**, namespaced by top-level key (`app.admin.*`, etc.). Never create a second lang file. |

## Shared scaffolding — reuse, don't re-implement

Admin base classes + traits in `src/Admin/State/Concerns/`:

| Class / trait | Reuse for |
|---------------|-----------|
| `AbstractAdminCollectionProvider` | Any admin listing — auth + args + paging + sort + `{data,meta}` envelope. Implement only `getSortable()` / `buildQuery()` / `applyFilters()` / `applySort()` / `mapRow()`. |
| `AbstractAdminItemProvider` | Any admin detail — auth + id resolution + 404. Implement only `getNotFoundLangKey()` / `findEntity()` / `mapToDto()`. |
| `ChecksAdminPermission` | The Sanctum-token role-permission gate (never call `bouncer()` — it reads the session admin, absent on token requests). |
| `BuildsAdminInvoice` / `…Shipment` / `…Refund` / `…Transaction` / `…Booking` | Sales detail/list mapping shared by provider + create-processor. |
| `MapsOrderActionItems` / `MapsOrderAddress` | Order-action item + address mapping. |
| `StreamsAdminCsvExport` | The datagrid "Export" CSV endpoints. |
| `ResolvesAdminDateRange` | Dashboard/Reporting date windows. |
| `TranslatesActionPayload` | DTO / GraphQL-args / request-body input fallback chain. |

Cross-cutting helpers/infra elsewhere in `src/`:

| Path | Role |
|------|------|
| `src/Serializer/AdminCollectionEnvelopeNormalizer.php` | Wraps any `/api/admin` paginator as `{ data, meta }`. |
| `src/Serializer/PaginationHeaderNormalizer.php` + `src/Http/Middleware/PaginationHeaders.php` | The `X-Total-*` pagination headers. |
| `src/Serializer/OutputOnlySnakeToCamelNameConverter.php` | Surfaces snake_case props as camelCase in output. |
| `src/Routing/CustomIriConverter.php` | Fast-path IRI generation for admin resources (perf). |
| `src/Http/Middleware/` | `EnforceAdminApiAuth`, `VerifyStorefrontKey`, `VerifyGraphQLStorefrontKey`, `NormalizeEmptyJsonBody`, `SetAdminApiAuditContext`, etc. |
| `src/Admin/Auth/AdminApiGuard.php` | The `admin-api` guard (Integration tokens). |
| `src/Console/Commands/` | `bagisto-api-platform:{install,optimize,clear-cache,warm-cache}`, `bagisto-api:generate-key`, `bagisto-api:key:manage`. |
| `config/` | `api-platform.php`, `api-platform-vendor.php`, `graphql-auth.php`, `storefront.php`. |

**Before writing a new helper, grep the package for one that already does the job** (DRY — see `conventions.md`). If two resources share more than a few lines of mechanical logic, extract a base class / trait / guard.

## Tests

```
tests/Feature/
├── GraphQL/                 shop GraphQL tests
├── RestApi/                 shop REST tests
└── Admin/
    ├── GraphQL/             admin GraphQL tests
    ├── RestApi/             admin REST tests
    ├── Audit/               admin API audit-trail tests
    └── Web/                 admin-panel (blade) tests
```

One file per resource per transport: `<Resource>Test.php`. See `testing.md` for how to run them.

## Registering state classes (mandatory)

Every Provider (`ProviderInterface`) and Processor (`ProcessorInterface`) must be tagged in `BagistoApiServiceProvider::register()`. An untagged Provider is silently bypassed (API Platform falls back to the default Eloquent provider → 404 or wrong data); an untagged Processor can't be resolved for DI. New `src/Admin/{Models,Dto}` directories also need to be listed in the three `api-platform.php` `resources` configs so the classes are scanned.
