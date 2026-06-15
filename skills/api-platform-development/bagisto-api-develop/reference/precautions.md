# Precautions — the foot-guns, ranked by how much they hurt

These are the things that silently break. Check them before you ship.

1. **A REST change can break GraphQL.** They share the same Processor/Provider (routed by `$data` type + `$operation` instance). A new REST branch can shadow the GraphQL branch. **Always run the resource's GraphQL test before the REST test** and confirm green. The single most important rule.

2. **Route cache hides a new endpoint.** With the route cache on (the fast steady state), a newly-added `#[ApiResource]` op will NOT appear until the cache is rebuilt. After editing a resource: `php artisan optimize:clear && php artisan bagisto-api-platform:clear-cache` (routes now resolve but responses are slow + the first GraphQL run may be stale — may need a second run), live-test, then **`php artisan bagisto-api-platform:optimize`** to restore speed. **Never leave the working copy with caches cleared.** Note `php artisan test` itself clears the route/config cache — re-optimise after a test session.

3. **GraphQL camelCase / IRI nullability.** Multi-word camelCase scalar fields (`orderId`, `createdAt`, `grandTotal`) return **null** over GraphQL unless the property is **snake_case + `AcceptsCamelCaseWrites`** (single-token fields like `id`/`state` always resolve, which is why tests that only query those miss the bug). Always add a GraphQL test that queries a multi-word field.

4. **Detail resource with a separate `output:` DTO 500s on the GraphQL `id`.** API Platform names the GraphQL type after the resource shortName but the provider returns a different class → the IRI can't be generated → "Cannot return null for non-nullable field `…​.id`". **Fix: the detail resource returns ITSELF** (fields on the resource class + `AcceptsCamelCaseWrites`), no `output:` DTO — the Invoice template in `CLAUDE.md`.

5. **Custom `name:` on `QueryCollection` takes the whole GraphQL endpoint down.** One combined schema is built; one broken resource throws "Operation 'collection_query' not found" for every admin GraphQL op. Drop the `name:` — the auto-derived plural is what you want. (`Mutation(name: …)` is fine and required.)

6. **Untagged Provider/Processor → silent 404 / wrong data.** Tag every state class in `BagistoApiServiceProvider::register()`. New `src/Admin/{Models,Dto}` dirs must also be added to the three `api-platform.php` `resources` configs.

7. **Typed-DTO arrays serialise as IRIs / empty connections.** Nested item lists must be **plain associative arrays**, not arrays of typed DTOs — else REST emits IRI strings and GraphQL emits all-null cursor nodes. (API Platform GraphQL resolves a relation by the parent's PRIMARY KEY; Sales addresses/items key on `order_id`, not the resource PK — so the Eloquent-relation rebuild for them does NOT work. This was proven and reverted; don't re-litigate it. Use plain arrays.)

8. **Snapshot currency codes can throw.** `core()->formatPrice($amount, $code)` 500s if the order/invoice's snapshot currency code no longer resolves to a `Currency` row. Wrap in a `safeFormatPrice()`-style try/catch that falls back to the raw value.

9. **The core product update assumes a FULL admin-form submission.** A partial update must use the surgical 3rd-arg `ProductRepository::update($data, $id, $attributeCodes)` for attribute-only edits, and reconstruct current state (booleans/multiselects/relations/CGP) for the full-form path — else a partial PUT wipes half the product.

10. **No internal symbols in CONSUMER docs.** The api-docs (and the consumer-facing skills) describe behaviour + payloads only — no class/method/file/`Webkul\…` names. (This package-dev skill DOES use real names — it's package-facing.)

11. **No auto-commit; no unprompted regression sweeps.** The user commits everything themselves. Don't run full test sweeps in wrap-up passes if the implementation already ran the affected tests green.
