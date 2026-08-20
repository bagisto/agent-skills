---
name: data-transfer
description: Use when adding or changing a Bagisto import — an Importer class, a file source, the importers registry, the queued import pipeline, or a stuck or failing import job. Trigger phrases include "import", "importer", "data transfer", "CSV", "XLSX", "XML", "bulk upload", "import batch", "queued import", "validate rows".
requires: coding-standards
---

# Data Transfer

`packages/Webkul/DataTransfer` moves bulk records into Bagisto from a file. The
package ships three importers — **products**, **customers** and **tax rates** —
and a queued pipeline that validates, imports, links and indexes in batches.

**Import only.** There is no exporter here; a DataGrid's own export handles
outbound data — see the `datagrid-development` skill.

## Reference files

| File | Load when |
|---|---|
| [importers.md](importers.md) | Writing or changing an Importer — the contract, validation, batches |
| [pipeline.md](pipeline.md) | The state machine, queued jobs, and debugging a stuck import |

## The registry

An importer is registered in `Config/importers.php`, merged into the top-level
**`importers`** key (not `data_transfer.importers`):

```php
'tax_rates' => [
    'title'        => 'data_transfer::app.importers.tax-rates.title',
    'importer'     => 'Webkul\DataTransfer\Helpers\Importers\TaxRate\Importer',
    'sample_paths' => [
        'csv'  => 'data-transfer/samples/csv/tax-rates.csv',
        'xls'  => 'data-transfer/samples/xls/tax-rates.xls',
        'xlsx' => 'data-transfer/samples/xlsx/tax-rates.xlsx',
        'xml'  => 'data-transfer/samples/xml/tax-rates.xml',
    ],
],
```

The admin create/edit screens iterate `config('importers')` directly, so a new
entry appears in the type dropdown with no view change. `Import` resolves the
class with `config('importers.'.$type.'.importer')` — the array key is the
`type` stored on the import record, so renaming a key orphans existing imports.

Provide all four sample paths. The UI offers a sample download per format, and a
missing file is a broken link rather than a graceful fallback.

## The importer contract

Extend `Helpers\Importers\AbstractImporter` and implement exactly two methods:

```php
abstract public function validateRow(array $rowData, int $rowNumber): bool;
abstract public function importBatch(ImportBatchContract $importBatchContract): bool;
```

Everything else is declared as properties — `$validColumnNames`,
`$masterAttributeCode`, `$permanentAttributes`, `$messages` — or overridden as
hooks. See [importers.md](importers.md).

## Sources

`Helpers\Sources\` supplies `CSV`, `XLS`, `XLSX` and `XML`, all extending
`AbstractSource`, which is an iterator over rows plus
`generateErrorReport(array $errors)`. An importer never opens the file itself —
it reads `$this->source`, so the same importer serves every format.

## Non-negotiables

- **Rows are validated before anything is written.** `validateRow()` must be
  free of side effects: it runs over the whole file, and on
  `stop-on-errors` the import may never reach `importBatch()`.
- **Work in batches, never row-by-row over the whole file.**
  `AbstractImporter::BATCH_SIZE` is 100 and the pipeline dispatches one job per
  batch. An importer that loads the file into memory defeats the design and
  fails on the file sizes this feature exists for.
- **Go through repositories** for writes, as everywhere else in Bagisto.
- **Every message goes through `trans()`** in the `data_transfer::` namespace,
  in all 22 locales.
- **Declare `isLinkingRequired()` / `isIndexingRequired()` honestly.** Returning
  true adds a queued stage per batch; returning false when linking is needed
  leaves records half-related with no error.
- **The queue must be running** for anything past validation. With
  `QUEUE_CONNECTION=sync` the whole import runs inline in the request and will
  time out on a real file.

**REQUIRED SUB-SKILL:** Use change-verification before calling any change done.
