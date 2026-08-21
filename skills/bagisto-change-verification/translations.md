# The translations gate

```bash
php artisan bagisto:translations:check
```

A key must exist in all 22 locales under `Resources/lang/`. One missing locale
fails the workflow.

## The checker only scans `packages/Webkul`

`TranslationsChecker` globs `base_path('packages/Webkul')`. A package installed
from anywhere else — an extension clone symlinked into `vendor/` through a
Composer path repository, for instance — is **never examined**.

The command still prints `✅ All translations are synchronized`. That is true of
the packages it looked at, and says nothing about yours. A green result here is
not evidence for a package outside that directory, and reading it as one is how
an out-of-sync extension ships.

So when the lang files you edited live outside `packages/Webkul`, compare that
package's locales against its own `en` yourself:

```bash
php -r '
$base = "<pkg>/src/Resources/lang";
$flat = function ($a, $p = "") use (&$flat) { $o = [];
    foreach ($a as $k => $v) { $q = $p === "" ? (string) $k : "$p.$k";
        if (is_array($v)) { $o += $flat($v, $q); } else { $o[$q] = $v; } }
    return $o; };
$en = $flat(require "$base/en/app.php");
foreach (array_diff(scandir($base), [".", "..", "en"]) as $loc) {
    $t = $flat(require "$base/$loc/app.php");
    printf("%-8s missing:%d extra:%d\n", $loc,
        count(array_diff_key($en, $t)), count(array_diff_key($t, $en)));
}'
```

Every locale must report `missing:0 extra:0`. Run it **before** the change too,
so a pre-existing gap is not mistaken for one you introduced.

## Take the wording from the project, never invent it

For a new key, find an existing key whose `en` value is the same string and copy
that locale's translation — the package's own lang files first, then core's:

```php
$val = null;
foreach ($enPkg as $k => $v) {
    if ($v === $englishString && isset($localePkg[$k])) { $val = $localePkg[$k]; break; }
}
```

Common UI strings — "Edit", "Delete", "Search", "Item Status" — are already
translated somewhere in the project for every locale. A string invented for 21
languages is a string nobody proofread, and it is indistinguishable from a real
translation once it is in the file.

If a string genuinely appears nowhere, say so and leave it for a translator
rather than guessing.

## Inserting keys without reformatting the file

Do **not** load the lang array and write it back with `var_export()` — that
reformats thousands of lines and buries the change.

Insert the line textually, at the right nesting and in alphabetical order among
its siblings. Locating the block by "find the line matching `'key' => [`" is
unreliable: the same key name occurs at several depths, and a naive scan lands
in the wrong one. Track the enclosing key path instead — push on a line matching
`'name' => [`, pop on a line matching `],` — so every line knows the full path it
sits under, then insert where that path equals the target.

Verify afterwards with `php -l` on **every** locale file, not just the one you
were aiming at.
