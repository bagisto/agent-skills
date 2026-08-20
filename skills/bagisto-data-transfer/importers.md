# Writing an Importer

## Contents

- [Declarations](#declarations)
- [`validateRow()`](#validaterow)
- [Reporting an error](#reporting-an-error)
- [`importBatch()`](#importbatch)
- [Append and delete](#append-and-delete)
- [Hooks](#hooks)
- [Chunked validation](#chunked-validation)
- [Registering the importer](#registering-the-importer)

## Declarations

Most of an importer is properties, not code:

```php
class Importer extends AbstractImporter
{
    protected array $validColumnNames = [
        'identifier',
        'zip_code',
        'country',
        'tax_rate',
    ];

    protected array $messages = [
        self::ERROR_DUPLICATE_IDENTIFIER => 'data_transfer::app.importers.tax-rates.errors.duplicate-identifier',
    ];

    protected $permanentAttributes = ['identifier'];

    protected string $masterAttributeCode = 'identifier';

    protected bool $chunkedValidationSupported = true;
}
```

| Property | Meaning |
|---|---|
| `$validColumnNames` | Columns the file may contain. A well-formed name outside this list is `ERROR_CODE_INVALID_ATTRIBUTE` |
| `$masterAttributeCode` | The column identifying a record — the natural key |
| `$permanentAttributes` | Columns that must be present in every row |
| `$messages` | Error code → translation key, wired up in `initErrorMessages()` |
| `$chunkedValidationSupported` | Whether validation may be split across queued chunks |

`AbstractImporter` already defines the generic error codes —
`ERROR_CODE_COLUMN_NOT_FOUND`, `ERROR_CODE_COLUMN_EMPTY_HEADER`,
`ERROR_CODE_COLUMN_NAME_INVALID`, `ERROR_CODE_WRONG_QUOTES`,
`ERROR_CODE_COLUMNS_NUMBER`, `ERROR_CODE_INVALID_ATTRIBUTE`,
`ERROR_CODE_SYSTEM_EXCEPTION`. Add a class constant only for a condition
specific to your domain.

## `validateRow()`

Returns whether the row may proceed. The shape every core importer follows:

```php
public function validateRow(array $rowData, int $rowNumber): bool
{
    if (isset($this->validatedRows[$rowNumber])) {
        return ! $this->errorHelper->isRowInvalid($rowNumber);
    }

    $this->validatedRows[$rowNumber] = true;

    if ($this->import->action == Import::ACTION_DELETE) {
        if (! $this->isIdentifierExist($rowData['identifier'])) {
            $this->skipRow($rowNumber, self::ERROR_IDENTIFIER_NOT_FOUND_FOR_DELETE);

            return false;
        }

        return true;
    }

    $validator = Validator::make($rowData, [
        'identifier' => 'required|string',
        'country'    => 'required|string',
        'tax_rate'   => 'required|numeric|min:0.0001',
    ]);

    // …report failures, check uniqueness…
}
```

Four rules this encodes:

- **Memoise.** The same row can be validated more than once; the guard on
  `$this->validatedRows` keeps that cheap and keeps errors from doubling.
- **Branch on the action first.** A delete run validates that the record
  *exists*; an append run validates the payload. Applying append rules to a
  delete file rejects perfectly good rows.
- **Use Laravel's validator** for field rules rather than hand-rolled `if`s.
- **No side effects, no writes.** Validation runs over the entire file before
  anything is imported, and under `stop-on-errors` may be all that runs.

## Reporting an error

Never throw for a bad row — a single bad row must not abort the file:

```php
$this->skipRow($rowNumber, $errorCode, $columnName, $errorMessage);
```

That records the error against the row and adds the row to the skip list. Map
each error code to a translation key in `$messages`, and add the key to all 22
locales.

To attribute a Laravel validation failure to the right rule, read the failed
rule name rather than guessing:

```php
$failedAttributes = $validator->failed();

foreach ($validator->errors()->getMessages() as $attributeCode => $message) {
    $errorCode = array_key_first($failedAttributes[$attributeCode] ?? []);

    $this->skipRow($rowNumber, $errorCode, $attributeCode, current($message));
}
```

## `importBatch()`

Receives one `ImportBatch` — by default 100 rows (`AbstractImporter::BATCH_SIZE`)
— and writes them:

```php
public function importBatch(ImportBatchContract $batch): bool
{
    if ($this->import->action == Import::ACTION_DELETE) {
        return $this->deleteTaxRates($batch);
    }

    return $this->saveTaxRatesData($batch);
}
```

Inside:

- **Write through repositories**, not the query builder.
- **Prefer a bulk upsert over a per-row save.** The batch exists so the whole
  set is one or two statements.
- **Keep the counters honest** — `getCreatedItemsCount()`,
  `getUpdatedItemsCount()` and `getDeletedItemsCount()` feed the progress UI.
- **Normalise in `prepareRowForDb()`**, the hook meant for casting and defaults,
  rather than scattering conversions through the save.

## Append and delete

`Import::ACTION_APPEND` and `Import::ACTION_DELETE` are the two modes, chosen by
the operator. Both `validateRow()` and `importBatch()` must handle each. Append
means insert-or-update keyed on `$masterAttributeCode`, not blind insert.

## Hooks

| Hook | Override when |
|---|---|
| `prepareForValidation()` | Preload lookups once, before the row loop |
| `prepareRowForDb(array $rowData): array` | Cast, trim, default a row before writing |
| `initErrorMessages()` | Register domain error codes (call `parent::`) |
| `isLinkingRequired(): bool` | Rows relate to each other and need a second pass |
| `isIndexingRequired(): bool` | Imported records must reach the search/price index |
| `releaseBatchMemory()` | Per-batch caches need clearing between jobs |

`isLinkingRequired()` and `isIndexingRequired()` each add a queued stage per
batch. Products need both; tax rates need neither.

## Chunked validation

Setting `$chunkedValidationSupported = true` opts into `ValidatesInChunks`,
which validates a slice at a time and can queue the work
(`queueValidation()`, `validateChunkFragment()`, `mergeValidationFragments()`).

It requires two methods so a chunk can resume where the last one stopped:

```php
protected function captureValidationState(): array;
protected function restoreValidationState(array $state): void;
```

Anything an importer accumulates across rows — seen identifiers, counters —
must be in that state. Leave something out and duplicates across a chunk
boundary go undetected, which is the classic symptom of a half-implemented
`captureValidationState()`.

## Registering the importer

1. Add the entry to `Config/importers.php` with a `title`, the `importer` FQCN
   and all four `sample_paths`.
2. Ship the sample files at those paths.
3. Add the title and every error message to all 22 locales under
   `data_transfer::`.
4. Verify with `php artisan bagisto:translations:check`.
