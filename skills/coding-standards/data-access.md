# Data Access

## Go through the repository, never the query builder

Every read and write goes through a repository. Reaching for `DB::table(...)` or the model's query
builder from a controller, listener, job, or service bypasses the layer the whole codebase is built
on — and makes the operation impossible to reuse or override.

```php
// Good — the operation lives on the repository, named for what it does.
$this->pickupRepository->attachShipment($pickup, $shipment->id);
```

```php
// Bad — a service reaching past the repository into the table.
DB::table('marketplace_pickups')
    ->where('id', $pickup->id)
    ->update(['package_count' => $pickup->shipments()->count()]);
```

If the repository has no method for what you need, **add one**. That is the extension point:

```php
/**
 * Attach a shipment to a collection and refresh its package count.
 */
public function attachShipment(Pickup $pickup, int $shipmentId): void
{
    $pickup->shipments()->syncWithoutDetaching([$shipmentId]);

    $this->update(['package_count' => $pickup->shipments()->count()], $pickup->id);
}
```

**The one place `DB` is expected is a DataGrid's `prepareQueryBuilder()`**, which is built on the
query builder by design and returns a `Builder` for the grid to paginate. `DB::transaction()` and
`DB::raw()` inside a repository are also fine — the objection is to querying *tables* from outside
the data layer, not to the facade itself.

### Scope every seller-facing query in the repository

On a marketplace, a repository method that touches seller-owned data takes the seller id as its
first argument and filters on it. Then there is no call shape that can reach another seller's rows:

```php
/**
 * One of a seller's collections, or null when it is not theirs.
 */
public function findForSeller(int $sellerId, int $pickupId): ?Pickup
{
    return $this->model
        ->where('marketplace_seller_id', $sellerId)
        ->where('id', $pickupId)
        ->first();
}
```

---
