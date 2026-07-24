---
name: blade-conventions
description: "Blade template conventions for any Bagisto package or module (Admin, Shop, or any custom Webkul-style package). Activates when creating or editing Blade views, building Blade components (anonymous @props components or Vue-backed x-template components), wiring forms, datagrids, modals, layouts, or slots, or matching the project's markup, attribute-binding, indentation, and formatting style. The conventions are framework-wide; only the per-package namespace tokens differ."
license: MIT
metadata:
  author: bagisto
---

# Bagisto Blade Conventions

## Overview

Bagisto UIs are Blade templates that lean heavily on **Blade components** and an inline **Vue 3** layer. New views must be indistinguishable from the surrounding code: same component idioms, the same `:` vs `::` binding rules, and the same indentation/attribute formatting. This skill captures those conventions so generated Blade matches the codebase exactly.

**These conventions are the same in every package** — `Admin`, `Shop`, and any custom Webkul-style module. What changes between packages is only a set of **namespace tokens** (the `x-<ns>::` component prefix, the `<ns>::` translation namespace, and the `view_render_event` names); see "Per-package namespaces" below. When in doubt, open a nearby view in the *same package* and mirror it.

Core UIs live under `packages/Webkul/Admin/src/Resources/views/` and `packages/Webkul/Shop/src/Resources/views/`; other packages (including your own) follow the same directory shape under their own `src/Resources/views/`. Each package that ships components has a `components/example.blade.php` that demonstrates usage — treat it as the canonical reference.

## Per-package namespaces (Admin, Shop, custom modules)

A package's tokens come from two calls in its `ServiceProvider::boot()`:

```php
// Registers the `<ns>::` view + translation namespace  →  view('<ns>::…'), @lang('<ns>::…')
$this->loadViewsFrom(__DIR__.'/../Resources/views', '<ns>');

// Registers the `x-<ns>::` anonymous component prefix   →  <x-<ns>::button />
Blade::anonymousComponentPath(__DIR__.'/../Resources/views/components', '<ns>');
```

So Admin registers `admin` (→ `x-admin::`, `@lang('admin::…')`), Shop registers `shop`, and a package of your own — say `RMA` — registers `rma` (→ `x-rma::`, `@lang('rma::…')`).

What this means when working outside Admin/Shop:

- **Reuse the shared components freely.** `x-admin::` and `x-shop::` components/layouts are registered **globally**, so an RMA admin page still wraps in `<x-admin::layouts>` and uses `<x-admin::datagrid>`, `<x-admin::form.control-group.*>`, `<x-admin::modal>`, etc. A customer-facing page uses `<x-shop::layouts>` and shop components. You do **not** re-implement these.
- **Prefix only your own new components** with your package namespace: `<x-rma::return-request-card>`.
- **Translations use your namespace:** `@lang('rma::app.return-requests.index.title')`, with keys under `packages/Webkul/RMA/src/Resources/lang/`.
- **`view_render_event` names follow the package/area**, e.g. `bagisto.rma.return-requests.list.before` (mirror the naming of nearby events in that package).
- **Everything else is unchanged:** the `:`/`::` binding rules, the Vue `<v-x>` + x-template recipe, `@props`, formatting, ACL, and script stacking all apply verbatim.

Quick substitution map when moving between packages:

| Token | Admin | Shop | Your package (example: RMA) |
|---|---|---|---|
| Own component prefix | `x-admin::` | `x-shop::` | `x-rma::` |
| Translation namespace | `admin::app.…` | `shop::app.…` | `rma::app.…` |
| Layout to wrap in | `x-admin::layouts` | `x-shop::layouts` | reuse `x-admin::`/`x-shop::` layouts |
| Event prefix | `bagisto.admin.…` | `bagisto.shop.…` | `bagisto.rma.…` |

## When to Apply

Activate when:
- Creating or editing any `.blade.php` under the Admin or Shop packages
- Building a reusable Blade component (anonymous or Vue-backed)
- Wiring forms, datagrids, modals, drawers, tabs, or layouts
- Matching the project's attribute-binding, indentation, and blank-line style

## Directory & Component Structure

Admin and Shop mirror each other. Pages sit under a feature folder (`catalog/`, `sales/`, `checkout/`, `customers/`, …); shared components sit under `components/`. Common components in both: `accordion, button, datagrid, drawer, dropdown, form, layouts, media, modal, quantity-changer, shimmer, table, tabs, tinymce`.

Namespaced invocation: `<x-admin::name>` / `<x-shop::name>`, nested with dots: `<x-admin::form.control-group.control>`, `<x-admin::charts.bar>`.

## Component Invocation & Data Binding (most important rule)

Three distinct attribute forms — pick deliberately:

| Syntax | Resolves as | Use for | Example |
|---|---|---|---|
| `attr="text"` | static string | literals | `name="quantity"` |
| `:attr="expr"` | **Blade/PHP** expression | PHP values, routes, `trans()`, `old()` | `:src="route('admin.sales.orders.index')"` |
| `::attr="expr"` | escaped `:` → **literal `:attr` for Vue** | data passed into the Vue component | `::value="item?.quantity"`, `::labels="chartLabels"` |

The `::` (double colon) is Blade escaping a single `:` so the rendered HTML contains `:attr="expr"` for Vue to bind at runtime. Getting `:` vs `::` right is the single most common source of bugs.

**`::` only works on a Blade component tag** — `<x-admin::…>`, `<x-shop::…>`, `<x-marketplace::…>`. Blade unescapes it while compiling the component. A plain custom element (`<v-quantity-changer>`, `<v-field>`, any `<v-…>` you wrote yourself) is passed through as literal HTML, so `::attr` reaches the browser **with both colons**, Vue does not recognise it as a binding, and the prop silently never arrives. On a plain `<v-…>` element write a single colon:

```blade
<x-admin::quantity-changer ::value="item.qty" />   {{-- component  → renders :value  --}}

<v-quantity-changer :value="item.qty"></v-quantity-changer>   {{-- plain element → write : --}}
```

The failure is silent and easy to misread: the prop is `undefined`, so any computed that walks it throws during render and the component freezes on whatever it last drew — typically its loading shimmer. If a `<v-…>` component renders its placeholder forever, check the colons first.

Named slots use `<x-slot:name> … </x-slot>`:

```blade
<x-admin::drawer>
    <x-slot:toggle>Toggle</x-slot>
    <x-slot:content>Body</x-slot>
</x-admin::drawer>
```

## The Two Component Types

### 1. Anonymous Blade component (`@props` + `$attributes`)

```blade
@props([
    'isActive' => false,
    'position' => 'right',
])

<div {{ $attributes->merge(['class' => 'box-shadow rounded bg-white dark:bg-gray-900']) }}>
    {{ $slot }}
</div>
```

- Declare inputs with `@props([...])`.
- Forward extra attributes with `$attributes->merge([...])`.
- Consume default slot with `{{ $slot }}`, named slots with `{{ $toggle }}` etc.

### 2. Vue-backed component (dominant pattern)

A thin custom-element wrapper + an inline x-template + registration on the global `app`:

```blade
@props([
    'name'  => '',
    'value' => 1,
])

<v-quantity-changer
    {{ $attributes->merge(['class' => 'flex items-center']) }}
    name="{{ $name }}"
    value="{{ $value }}"
>
</v-quantity-changer>

@pushOnce('scripts')
    <script
        type="text/x-template"
        id="v-quantity-changer-template"
    >
        <div>
            <span
                class="icon-minus cursor-pointer"
                role="button"
                @click="decrease"
            ></span>

            <p>@{{ quantity }}</p>
        </div>
    </script>

    <script type="module">
        app.component("v-quantity-changer", {
            template: '#v-quantity-changer-template',

            props: ['name', 'value'],

            data() {
                return {
                    quantity: this.value,
                };
            },

            methods: {
                decrease() {
                    this.$emit('change', --this.quantity);
                },
            },
        });
    </script>
@endPushOnce
```

Rules for this pattern:
- Wrapper element is `<v-name>`; template id is `#v-name-template`.
- Register with `app.component("v-name", { template: '#v-name-template', ... })`.
- Wrap scripts in `@pushOnce('scripts')` … `@endPushOnce` (the layout renders `@stack('scripts')`, so the block emits once no matter how many times the component is used).
- Emit literal Vue mustaches as `@{{ expr }}` so Blade does not try to render them.
- Pass data in via `::attr` (Vue binding) or `attr="{{ $php }}"` (server value).

## Page Skeleton

```blade
<x-admin::layouts>
    <x-slot:title>
        @lang('admin::app.catalog.attributes.index.title')
    </x-slot>

    <div class="flex items-center justify-between">
        <p class="text-xl font-bold text-gray-800 dark:text-white">
            @lang('admin::app.catalog.attributes.index.title')
        </p>

        @if (bouncer()->hasPermission('catalog.attributes.create'))
            <a href="{{ route('admin.catalog.attributes.create') }}">
                <div class="primary-button">
                    @lang('admin::app.catalog.attributes.index.create-btn')
                </div>
            </a>
        @endif
    </div>

    {!! view_render_event('bagisto.admin.catalog.attributes.list.before') !!}

    <x-admin::datagrid :src="route('admin.catalog.attributes.index')" />

    {!! view_render_event('bagisto.admin.catalog.attributes.list.after') !!}
</x-admin::layouts>
```

Shop pages use `<x-shop::layouts>` and may add `@push('meta')` for SEO tags and `@inject('helper', '...')` for view helpers.

## Cross-Cutting Idioms

- **Extensibility hooks** — bracket meaningful content with `{!! view_render_event('bagisto.<area>.<path>.before') !!}` and `.after`. The dotted name follows the view path. Present in the large majority of pages.
- **Translations** — never hardcode UI strings. Use `@lang('admin::app.…')` / `@lang('shop::app.…')` or `trans('…')`, always package-namespaced. When adding keys, add them to **all** locales under `Resources/lang/`.
- **ACL (admin only)** — gate create/edit/delete buttons and datagrid actions with `@if (bouncer()->hasPermission('resource.action'))`.
- **Forms** — `<x-admin::form :action="route(...)" method="POST">` wraps a VeeValidate `v-form`. Build fields with the control-group trio:
  ```blade
  <x-admin::form.control-group>
      <x-admin::form.control-group.label class="required">
          @lang('...')
      </x-admin::form.control-group.label>

      <x-admin::form.control-group.control
          type="text"
          name="admin_name"
          rules="required"
          :value="old('admin_name')"
          :label="trans('...')"
      />

      <x-admin::form.control-group.error control-name="admin_name" />
  </x-admin::form.control-group>
  ```
  Validation is client-side; `control-name` on the error component must match the field `name`.
- **DataGrids** — `<x-admin::datagrid :src="route('…')" />`. Columns, filters, and actions are defined in a PHP `DataGrid` class; the Blade tag only points at the JSON endpoint.
- **Blade ↔ Vue escaping** — `@{{ vueVar }}` prints a literal Vue mustache; wrap a block in `v-pre` to keep Blade from touching `@`/`{{ }}` inside it.
- **Theming / i18n shell** — the layout sets `class="… dark …"` and `dir="{{ core()->getCurrentLocale()->direction }}"`; use Tailwind `dark:` and `ltr:`/`rtl:` variants for theme/RTL awareness.

## Formatting & Style Rules

These are enforced by hand in `.blade.php` (Pint does **not** format Blade), so match them precisely.

**Indentation**
- 4 spaces, no tabs. One clean 4-space step per nesting level.

**Attribute layout**
- **More than one attribute → one per line**, each indented +4 from the tag, with the closing `>` (or `/>`) on **its own line** aligned with the opening `<tag`:
  ```blade
  <x-admin::form.control-group.control
      type="text"
      name="admin_name"
      :value="old('admin_name')"
  />
  ```
- **Single attribute → inline**: `<x-admin::form.control-group.error control-name="admin_name" />`.
- Attribute lines are **contiguous** — no blank lines between attributes inside one tag.
- Loose attribute order: control-flow/Vue directives (`v-if`, `v-else`) → `class` / `:class` → plain & `aria-*` attributes → **event handlers (`@click`, `@change`) last**.

**`@props` — align the `=>`**
```blade
@props([
    'name'      => '',
    'value'     => 1,
    'minValue'  => 1,
    'removable' => false,
])
```
Pad keys so the `=>` arrows line up. A `@props` block is a declaration the reader scans as a table, so it is the one place alignment earns its keep.

**PHP inside `@php … @endphp` — Pint's rules, applied by hand**

Inside an `@php` block you are writing plain PHP, so it follows exactly what `vendor/bin/pint`
would produce for a `.php` file — most visibly, **a single space either side of `=>`, never padded
to align**:

```blade
@php
    $steps = [
        'label' => trans($prefix.'.source'),
        'hint' => trans($prefix.'.source-hint'),
        'validate' => ['file'],
    ];
@endphp
```

Pint does **not** format `.blade.php` files, so nothing enforces this — you have to write it that
way yourself. When unsure how a construct should look, write it in a scratch `.php` file, run Pint
on it, and copy the result. The same applies to the rest of Pint's output: spacing, operators,
trailing commas, and short closures.

Everything outside `@php` — `@props`, directive arguments, inline `{{ }}` expressions — is Blade's
own layer and keeps the Blade rules on this page.

**Blank lines**
- One blank line between sibling blocks/elements and around `view_render_event` hooks.
- One blank line after the `@props([...])` block before the markup.

**Directive casing / naming**
- Standard push block: `@pushOnce('scripts')` … `@endPushOnce` (note the capital `P` in `@endPushOnce`). `'styles'` is used rarely for CSS.

**Comments**

Two rules from the **package-development** skill govern Blade too, and they pull in opposite directions — apply both:

- **"Every method gets a docblock"** — a Vue `method` or `computed` in a `<script>` block is a method. It gets a `/** … */` describing what it does, as a capitalised sentence ending in a full stop. Same for any function inside an `@php` block.
- **"Comment only what the code cannot say"** — *inside* a method body, and in the markup, the default is no comment. Explain a constraint that is invisible locally, a workaround, or a line that looks removable but is load-bearing; skip anything that merely restates the markup or the call.

What follows is the syntax to use for each layer.

Each comment syntax belongs to its own layer — pick by *where* the comment sits, then follow the casing/punctuation rule for that layer.

- **Blade `{{-- --}}`** — for Blade/PHP-level notes (file headers, `@php` logic, control-flow explanations). Never ships to the browser.
  - If the comment is a **sentence** (or sentences), write it as prose with a **capital first letter and terminal punctuation**. Multi-line headers explain *what the view is and why*:
    ```blade
    {{--
        The friendly "What kind of product?" create funnel (stepped scratch page only). It maps a
        plain kind + a "Does it have variations?" answer to a Bagisto product type behind the scenes.
    --}}
    ```
  - If it is a **short label/title** (not a sentence), use **Title Case** with no trailing period: `{{-- Media --}}`, `{{-- Type-Specific Controls --}}`.
  - **Not inside `@php … @endphp`.** Blade does not strip its own comment there — it copies it verbatim into the compiled PHP, producing a parse error. Inside an `@php` block you are writing plain PHP, so use PHP comment syntax and the PHP conventions that go with it; put a `{{-- --}}` header *above* the block if the whole block needs explaining:
    ```blade
    {{-- Everything the wizard needs to describe its steps. --}}
    @php
        // The upload-size config is stored in MB; VeeValidate's size rule expects KB.
        $maxUploadKb = $maxUploadMb * 1024;
    @endphp
    ```

- **HTML `<!-- -->`** — section dividers *inside* an x-template / markup. Keep them short: a **Title-Cased** label or a natural question — mirror the heading the block renders. No trailing period on labels; a `?` on a question is fine:
  ```blade
  <!-- What kind of product? -->
  <!-- Attribute Family (Searchable) -->
  <!-- SKU -->
  ```

- **JS `/** … */` (JSDoc block)** — inside `<script>`. This is the **only** comment form used in the Vue layer — **no `//` line comments**. Every `computed`/`method` gets one, as a capitalized sentence ending in a full stop. Statements *inside* a method get one only when genuinely non-obvious:
  ```js
  /**
   * The axis checkboxes only appear for a variable kind, once the seller has said "yes"
   * and picked a family.
   */
  showAxes() {
      return this.isVariable && this.hasVariations === true && !! this.familyId;
  }
  ```
  A trivial one-liner still gets its docblock — but keep it to the one sentence, and don't pile extra commentary onto statements that already read clearly.

- **CSS `/** … */` (JSDoc block)** — inside `<style>`, same form as JS: describe *why* a rule exists (especially non-obvious ones like `:checked`-driven state or scrollbar hiding), as a punctuated sentence:
  ```css
  /**
   * Hide the navigation radios; they only drive the :checked state.
   */
  #rma-steps .rma-step-radio { … }
  ```

Rule of thumb: **sentence → capitalized + punctuated; bare title/label → Title Case, no period.** In `<script>`/`<style>` always use the `/** … */` block form, never `//` or bare `/* */`.

## Recipe: New Vue-backed component

1. Create `views/components/<name>/index.blade.php`.
2. `@props([...])` for the server-side inputs (aligned `=>`).
3. Render `<v-<name> {{ $attributes->merge([...]) }} …>` passing data via `attr="{{ $php }}"`.
4. `@pushOnce('scripts')`: an `<script type="text/x-template" id="v-<name>-template">` and `<script type="module"> app.component("v-<name>", { template: '#v-<name>-template', props, data, computed, methods }) </script>`; close with `@endPushOnce`.
5. Emit runtime values as `@{{ … }}`; bind parent data with `::attr`.
6. Use it as `<x-{admin|shop}::<name> ::value="…" @change="…" />`.

## Recipe: New page

1. Wrap in `<x-admin::layouts>` / `<x-shop::layouts>` with an `<x-slot:title>`.
2. Add a header row (title + permission-gated action buttons via `bouncer()`).
3. Bracket the main content with `view_render_event` `.before`/`.after`.
4. Put every string through `@lang`/`trans` with the package namespace.

## Do / Don't

- **Do** reuse existing `<x-{admin|shop}::…>` components and slots; **don't** hand-roll markup a component already provides.
- **Do** pick `::` for anything the Vue layer consumes and `:` for PHP values.
- **Do** align `=>` in a `@props` block; **don't** align it inside `@php … @endphp` or in a `.php` file — that is plain PHP, so Pint's single-space rule applies.
- **Do** wrap component scripts in `@pushOnce('scripts')` … `@endPushOnce`.
- **Do** namespace all strings through `@lang`/`trans` and add new keys to every locale.
- **Don't** put blank lines between a tag's attributes; **do** put a blank line between sibling blocks.
- **Do** gate admin actions with `bouncer()->hasPermission(...)`.
