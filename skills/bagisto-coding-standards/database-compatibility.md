# Database Compatibility

Every query, migration and raw fragment has to work on **MySQL 8.0, MariaDB 10.11 and
PostgreSQL 16**. All three are first-class and CI runs the suite against nine versions of them,
so a MySQL-only construct fails the pipeline rather than a reviewer. Use the existing
abstractions:

- **Case-insensitive LIKE**: use `db_grammar()->caseInsensitiveLike()` instead of a hardcoded `'like'`. It returns `LIKE` on MySQL (already case-insensitive) and `ILIKE` on PostgreSQL. Use `db_grammar()->caseSensitiveLike()` when exact case matching is needed.

  ```php
  $query->where('name', db_grammar()->caseInsensitiveLike(), '%'.$search.'%');
  ```

- **Empty strings → NULL/default**: MySQL coerces `""` to `0`/`NULL`; PostgreSQL rejects it. Use model set mutators (`setXxxAttribute`), paired with `$casts` for the read side, and never sanitize in controllers.

  ```php
  public function setPriorityAttribute($value): void
  {
      $this->attributes['priority'] = $value !== '' && $value !== null ? (int) $value : 0;
  }
  ```

- **Boolean columns**: add `$casts` with `'boolean'`. For the write side, use repository validation or model mutators.
- **DB-specific SQL**: use `db_grammar()` methods (`concat`, `groupConcat`, `findInSet`, `dateFormat`, `jsonExtractText`, `jsonExtractNumeric`, `caseInsensitiveLike`, `caseSensitiveLike`, and the rest of `Webkul\Core\Contracts\DatabaseGrammar`).
- **CASE expression types**: both branches must return the same type. Use `CAST(id AS VARCHAR(255))` — `CAST(... AS CHAR)` truncates to 1 character on PostgreSQL.
- **GROUP BY**: PostgreSQL requires every non-aggregated SELECT column in GROUP BY.
- **`DB::raw()` in `updateOrCreate()`**: fails on INSERT; split into find + update/create.
- **A failed statement aborts the whole PostgreSQL transaction.** MySQL lets a transaction continue
  after a duplicate-key error, so `try { insert } catch (UniqueConstraintViolationException) { … }`
  looks like it works. On PostgreSQL every later statement in that transaction fails with
  `25P02 current transaction is aborted`, and the catch block can do nothing — including inside a
  caller's transaction, which it also poisons. Resolve the conflict in one statement the database
  settles itself (`upsert()`, which compiles to `ON CONFLICT … DO UPDATE` and
  `ON DUPLICATE KEY UPDATE`) rather than catching the violation.

  ```php
  $query->upsert([$row], ['term', 'channel_id', 'locale'], ['uses' => $increment, 'results']);
  ```

  Qualify any column an upsert's update clause reads — PostgreSQL rejects a bare `uses` there as
  ambiguous between the stored row and the one being inserted.

## Where the abstraction lives

`db_grammar()` resolves to `Webkul\Core\Contracts\DatabaseGrammar`, implemented by
`MySqlGrammar` and `PgSqlGrammar` under `packages/Webkul/Core/src/Helpers/Database/Grammar/`.
Read the contract before hand-rolling SQL — a helper for what you need usually exists, and adding
one there is better than a `whereRaw` that only one engine understands.
