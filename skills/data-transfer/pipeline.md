# The import pipeline

## Contents

- [States](#states)
- [Options an operator chooses](#options-an-operator-chooses)
- [The queued stages](#the-queued-stages)
- [Images](#images)
- [Events](#events)
- [Debugging a stuck import](#debugging-a-stuck-import)

## States

`Helpers\Import` is the orchestrator and its constants are the state machine, in
order:

```
pending → validating → validated → downloading
        → processing → processed
        → linking    → linked
        → indexing   → indexed
        → completed
```

`downloading` runs only when the file references images; `linking` and
`indexing` only when the importer's `isLinkingRequired()` /
`isIndexingRequired()` return true. An import that never leaves a state is the
signal to look at the queue, not the importer — see below.

## Options an operator chooses

| Constant | Values | Meaning |
|---|---|---|
| `VALIDATION_STRATEGY_*` | `skip-errors`, `stop-on-errors` | Whether bad rows are skipped or the run aborts |
| `ACTION_*` | `append`, `delete` | Insert-or-update, versus remove by identifier |
| `IMAGE_SOURCE_*` | `url`, `upload`, `directory` | Where product images come from |

`ERROR_ROWS_PREVIEW` and `ERROR_MESSAGES_PREVIEW` are both 10 — the UI shows the
first ten of each, so a run with thousands of failures reports ten. Read the
generated error report file for the rest; `AbstractSource::generateErrorReport()`
writes it and `errorFilePath()` locates it.

## The queued stages

`AbstractImporter` builds the chain with Laravel batches:

```php
$chain[] = Bus::batch($typeBatches['import'])->allowFailures();

if ($this->isLinkingRequired()) {
    $chain[] = Bus::batch($typeBatches['link'])->allowFailures();
}

if ($this->isIndexingRequired()) {
    $chain[] = Bus::batch($typeBatches['index'])->allowFailures();
}
```

The jobs, in `Jobs/Import/`: `ValidateChunk`, `DownloadImages`, `ImportBatch`,
`LinkBatch`, `IndexBatch`, plus the `Completed` terminator and the
`Indexing` / `Linking` markers.

Two things follow from `allowFailures()`:

- **One failed batch does not stop the chain.** The import can reach
  `completed` with batches that failed. Report counts from the import record
  rather than assuming success from the terminal state.
- **Failures land in `failed_jobs`**, not in the import's own error report,
  which only covers row-level validation.

Two concerns harden the jobs: `RetriesOnDeadlock` (concurrent batches touching
the same tables) and `BoundedByRetryAfter` (keeps a retry inside the queue's
`retry_after`, so a long job is not run twice in parallel). A new job in this
pipeline should use both.

## Images

`Concerns\DownloadsImages` fetches product images in its own `Bus::batch` during
the `downloading` state. The source is one of `url`, `upload` or `directory`,
stored on the import record (`image_source`, added by a later migration).

A URL import reaches the network for every image. Expect it to dominate the
run, and expect failures to be per-image rather than fatal.

## Events

The pipeline dispatches, and third-party code should listen rather than patch:

```
data_transfer.imports.started
data_transfer.imports.linking
data_transfer.imports.indexing
data_transfer.imports.completed
```

## Debugging a stuck import

Work down this list in order; the cause is nearly always the first two.

1. **Is a queue worker running?** Everything after validation is queued. With no
   worker the import parks in `processing` forever and looks like a code bug.
2. **Is `QUEUE_CONNECTION=sync`?** Then the whole import runs inside the HTTP
   request and dies on PHP's execution limit for any real file. Sync is only
   viable for tiny fixtures.
3. **Check `failed_jobs`.** `allowFailures()` means a batch can fail without
   stopping the chain, so the import may report `completed` while records are
   missing.
4. **Read the error report file**, not just the ten rows the UI previews.
5. **Confirm the header row.** `validateColumns()` runs before any row is
   examined, and reports three distinct header faults — reading the right one
   saves the search:
   - `ERROR_CODE_COLUMN_EMPTY_HEADER` — a blank header cell, reported by
     position
   - `ERROR_CODE_COLUMN_NAME_INVALID` — the name fails `^[a-z][a-z0-9_]*$`,
     so an uppercase letter, space or hyphen in the header
   - `ERROR_CODE_INVALID_ATTRIBUTE` — a well-formed name that is not in
     `$validColumnNames`
   All three are header problems, not data problems.
6. **Check `type` still matches a registry key.** `Import` resolves the class
   through `config('importers.'.$type.'.importer')`; a renamed key leaves old
   import records pointing at nothing.

When reproducing locally, set a real queue connection and run
`php artisan queue:work` in a second terminal — reproducing on `sync` gives a
different failure mode from the one being reported.
