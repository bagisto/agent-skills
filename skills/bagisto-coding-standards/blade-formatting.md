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

**Comments** — owned by [comments.md](comments.md), including the syntax to
use in each layer (`{{-- --}}`, `<!-- -->`, JSDoc in `<script>` and `<style>`).

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
