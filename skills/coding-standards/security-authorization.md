# Authorization

## Contents

- [Admin: how a route is authorized](#admin-how-a-route-is-authorized)
- [The one case that is not fail-closed](#the-one-case-that-is-not-fail-closed)
- [`UNRESTRICTED_ROUTES`](#unrestricted_routes)
- [Two-factor](#two-factor)
- [Storefront: ownership, not permissions](#storefront-ownership-not-permissions)
- [What to check on a new route](#what-to-check-on-a-new-route)

## Admin: how a route is authorized

Three things cooperate:

1. **`Config/acl.php`** maps a permission key to the route names it covers.
2. **`Bouncer` middleware** resolves the current route name and refuses it when
   the role does not hold the mapped key.
3. **`bouncer()->hasPermission($key)`** is called in controllers and views to
   gate actions and hide controls.

The middleware's own comment states the intent:

> Anything not listed here and not mapped in `acl.php` is refused, so a route
> added without an ACL entry fails closed instead of being silently open to
> every role.

So on Bagisto a missing ACL entry is a **broken feature for custom roles**, not
an open door. That is the opposite of some sibling products — do not carry a
"fail-open" assumption across.

## The one case that is not fail-closed

`checkIfAuthorized()` is reached from `isPermissionsEmpty()`, which returns early
when the role's `permission_type` is `all`:

```php
if ($role->permission_type === 'all') {
    return false;          // …and checkIfAuthorized() never runs
}
```

So a route with **no ACL entry** is:

| Role | Result |
|---|---|
| `permission_type = all` | reachable |
| any custom role | `401` |

The practical consequence: a new route tested only as a super-admin looks fine
and 401s for everyone else. Always exercise a custom role — that is what the
ACL Playwright specs do.

## `UNRESTRICTED_ROUTES`

A short list in the middleware of routes every signed-in admin may reach
whatever their role grants — the admin's own account and 2FA, notifications, the
datagrid chrome and saved filters, the TinyMCE uploader, Magic AI.

They qualify because they act on the admin's **own** record or back shared UI no
single permission owns.

**Adding to this list removes a route from ACL entirely.** It needs a stated
reason and a reviewer. If the answer is "the permission was awkward to wire up",
the fix is the ACL entry.

Note `admin.settings.users.destroy` is on the list — deleting a user is
self-service account deletion here, not a privileged action. Read the list before
assuming anything about it.

## Two-factor

The middleware lets exactly four routes past the 2FA check — the setup and
verification screens, and logout — and the comment explains why the boundary is
drawn there:

> in particular disabling 2FA — must stay behind the verification check, so that
> a session which has logged in with the password but has not passed two-factor
> verification cannot use it to switch two-factor authentication off.

A session that has passed the password but not the second factor is
**partially authenticated**. Any new route reachable in that state must not
change security settings, read customer data, or act on an order.

## Storefront: ownership, not permissions

Customers have no roles. Authorization is **ownership**, enforced by scoping the
query to the authenticated customer:

```php
'customer_id' => auth()->guard('customer')->id(),
// …
$query->where('customer_id', auth()->guard('customer')->id());
```

The rule: **an id from the request never selects a row on its own.** It is always
combined with the owner. Otherwise incrementing an order id in the URL reads
someone else's order — the classic IDOR, and the easiest real vulnerability to
introduce in this codebase.

This applies to orders, invoices, shipments, addresses, downloadable products,
reviews, RMA requests and the cart. It applies to a DataGrid too: a storefront
grid's `prepareQueryBuilder()` must carry the customer filter, because the grid
happily paginates whatever the query returns.

A guest cart is owned by the session, not a customer id — check how the
surrounding code identifies it rather than inventing a scheme.

## What to check on a new route

1. **Is it in `acl.php`?** If not, and not deliberately unrestricted, custom
   roles get a 401.
2. **Does the controller check too?** Middleware covers the route name; a
   controller acting on an id still needs to confirm the actor may touch *that
   record*.
3. **Is the gate in the view mirrored on the server?** A `bouncer()` check around
   a button is presentation only.
4. **Storefront: is the query scoped to the owner?**
5. **Does a custom role actually reach it?** Exercise it, do not reason about it.
6. **Mass actions too.** `mass_delete` and `mass_update` take an array of ids
   from the browser; each needs the same permission and the same ownership scope
   as the single-record path.
