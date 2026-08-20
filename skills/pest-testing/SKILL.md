---
name: pest-testing
description: Use when writing or changing a Bagisto Pest test — feature or unit tests, assertions, datasets, mocking, architecture tests, or registering a new package's suite. Trigger phrases include "pest", "test", "unit test", "feature test", "assertion", "dataset", "mock", "testsuite", "TDD", "coverage".
license: MIT
---

# Pest Testing in Bagisto

## When to Apply

Activate this skill when:
- Creating new tests (unit or feature)
- Modifying existing tests
- Debugging test failures
- Working with datasets, mocking, or test organization
- Writing architecture tests
- Testing Bagisto packages (Admin, Shop, Core, etc.)

## Reference files — load only what the current task needs

| File | Load when |
|---|---|
| [suite-layout.md](suite-layout.md) | Where tests live, the suites, Pest.php bindings, autoload wiring |
| [writing-tests.md](writing-tests.md) | Running tests, test structure, assertions, mocking, datasets, architecture tests |
| [new-package.md](new-package.md) | Registering a new package's tests, pitfalls, best practices |

**REQUIRED SUB-SKILL:** Use change-verification before calling any change done.
