---
name: bagisto-api-develop
description: Use when working inside the bagisto-api package — installing or removing it, adding or changing a REST or GraphQL endpoint or resource, building an admin menu's API, or fixing package behaviour. Install and removal happen only on explicit request, never automatically. Trigger phrases include "ApiResource", "Provider", "Processor", "DTO", "resolver", "install the bagisto-api package", "remove the package", "add an endpoint", "extend an endpoint".
license: MIT
metadata:
  author: bagisto
  references:
    - install: Composer + manual install, post-install, verify
    - uninstall: Removing the package cleanly (both methods) + data warnings
    - structure: Package directory map + shared base classes
    - api-structure: Surfaces, transports, the 5-file pattern, declaring a resource, feature surface map
    - conventions: Coding standards + the conventions checklist
    - precautions: The ranked foot-guns
    - limitations: Parity-not-superset, known limits, deferred scope
    - testing: Pest + Playwright + the cache cycle
---

# Developing the Bagisto API package

Use this when you are working **inside** the `bagisto-api` package (`packages/Webkul/BagistoApi`, namespace `Webkul\BagistoApi`) — installing it, removing it, adding or changing an endpoint/resource, or fixing package behaviour. This is the guide rails: it tells you where the authoritative spec is, the rules you must not break, and points you at the detailed references.

## CRITICAL — install / remove only when asked

**Installing or removing the package is NEVER an automatic action.** Detecting the package files, a `composer.json`, or a Bagisto project does **not** mean you should install, reinstall, optimise, or uninstall anything. Only perform install (`reference/install.md`) or removal (`reference/uninstall.md`) when the **client explicitly asks for it**, and for install, ask whether they want the **Composer (stable)** or **Manual (newest)** method first.

## Authoritative sources — read these FIRST

The package ships its own complete documentation. **Read the relevant part before writing code** — almost every menu/resource is already specified with its exact behaviour, validation, events, and quirks:

| Source | What it gives you |
|--------|-------------------|
| `CLAUDE.md` (package root) | The authoritative conventions + a coverage table for **every** endpoint, with the per-resource decisions and quirks. **Read this first** for the resource you're touching. |
| `docs/superpowers/specs/` | Design specs for larger features. |
| `CHANGELOG.md` | What shipped, consumer-facing, under `[Unreleased]`. |
| `PERFORMANCE.md` | Caching / IRI / schema-build performance notes. |
| GitHub `bagisto/bagisto-api` | The canonical code — copy the closest existing resource rather than writing the pattern from scratch. |
| `https://api-docs.bagisto.com` (+ `/llms.txt`) | The consumer-facing request/response shapes + the full endpoint index. |

**Rule: don't improvise behaviour that `CLAUDE.md` already specifies.** Search it for the resource/menu first.

## Reference map — open the one you need

| Topic | Reference file | Use when |
|-------|----------------|----------|
| Install the package | `reference/install.md` | Client asks to install / set up the API |
| Remove the package | `reference/uninstall.md` | Client asks to remove / uninstall the package |
| Where files go | `reference/structure.md` | Adding any file; finding the right directory + base class |
| Surfaces, transports, declaring a resource | `reference/api-structure.md` | Designing a new endpoint; understanding the 5-file pattern + feature surface |
| Coding standards + checklist | `reference/conventions.md` | Writing/reviewing a resource against the rules |
| Foot-guns | `reference/precautions.md` | Before you ship — the things that silently break |
| What the API will / won't do | `reference/limitations.md` | Scoping a feature; deciding "do we support this?" |
| Tests + cache cycle | `reference/testing.md` | Running/adding tests; the cache commands |

## The 5-file pattern (the spine of every resource)

Model (`#[ApiResource]` — REST + GraphQL ops + OpenAPI block) → DTO (typed input) → Provider (read path) → Processor (write path) → lang (`src/Resources/lang/en/app.php`). Storefront resources live under `src/`; admin resources under `src/Admin/`. **Tag every Provider/Processor in `BagistoApiServiceProvider::register()`** — an untagged one is silently bypassed (404 / wrong data). Full detail in `reference/api-structure.md` and `reference/structure.md`.

## The two non-negotiables

1. **A REST change can break GraphQL** — they share the same Provider/Processor. **Always run the resource's GraphQL test before the REST test**, and confirm it's green before considering the change done. This is the single most important rule.
2. **Parity with the Bagisto admin panel, not a superset.** Mirror what the admin UI does; where core lacks a feature, block the gap with a clear error rather than half-extending. See `reference/limitations.md`.

Everything else — the full checklist, the ranked foot-guns, and the test/cache commands — is in the references above. Open them rather than guessing.
