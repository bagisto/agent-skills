# Test data and environment safety

## Contents

- [Classify the environment](#classify-the-environment)
- [Isolate side effects](#isolate-side-effects)
- [Create deterministic fixtures](#create-deterministic-fixtures)
- [Restore state](#restore-state)

## Classify the environment

Before a mutating test, prove the base URL and database belong to an isolated test environment. Require an explicit opt-in such as `BAGISTO_E2E_ALLOW_MUTATION=1` in addition to repository-specific safety checks. Treat an unknown environment as non-mutating.

Never infer safety from `APP_DEBUG`, a private IP, localhost, or a non-production-looking hostname. These signals do not prove the data is disposable.

## Isolate side effects

- Use offline or sandbox payment methods and test carriers.
- Capture mail locally and disable external SMS, webhooks, ERP/CRM, analytics and fulfillment dispatch.
- Prevent search, cache, queue and cron workers from publishing test effects to shared production services.
- Use dedicated test channels, customers, coupons, products and customization records when possible.
- Do not log credentials, tokens, full addresses or payment information in traces and screenshots.
- Keep production smoke tests read-only and stop before order submission by default.

## Create deterministic fixtures

Create unique, queryable fixtures through installed helpers or factories:

- product SKU/name with controlled price, stock, visibility, categories and filterable attributes;
- category code/slug and known product membership;
- customer email and addresses owned by the run;
- valid/invalid coupon with known rules and time window;
- theme customization per type, theme, channel, locale, order and status;
- shipping/payment configuration compatible with the intended cart;
- representative fixture for every enabled product type.

Do not rely on demo labels, the first product, current time-sensitive promotions, shared stock, or an assumed category slug.

## Restore state

Prefer transaction/database reset mechanisms already owned by the test suite. Otherwise record original values before mutation and restore exactly:

- theme customization content, status and sort order;
- channel theme/logo/locale/currency settings;
- configuration flags, shipping/payment methods and tax settings;
- product inventory, price, status and visibility;
- coupon usage/configuration;
- customer session and cart;
- created orders or other test records according to repository cleanup policy.

Use `finally` for admin propagation tests. Report cleanup failure as a test failure even when the main assertion passed. Never delete an unverified record by broad query, wildcard, age, or display label.
