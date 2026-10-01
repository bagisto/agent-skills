# The naming gate

Route names are snake_case, translation keys are kebab-case, and storage directories are plural and
kebab-case. Each grep should print nothing:

```bash
# a route name carrying a hyphen or a capital
grep -rhoE "name\(['\"][^'\"]+['\"]\)" --include=*.php packages/Webkul routes \
  | sed -E "s/name\(['\"]//; s/['\"]\)//" | grep -E "[-A-Z]"

# a translation key segment carrying an underscore, outside the namespace itself
grep -rnoE "::[a-z_]+\.[a-zA-Z0-9.-]*_" --include=*.php --include=*.blade.php packages/Webkul

# a storage directory that is snake_case
find storage/app/public storage/app/private -type d -name '*_*'
```

A key or name that mirrors data rather than a label is the exception — currency and locale codes keep
their own casing.
