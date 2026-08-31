# Coding Standards

- CRITICAL: ALWAYS use the bagisto-coding-standards skill when writing or changing any Bagisto PHP or Blade. It owns code style, comments and docblocks, Laravel idiom, data access, Blade, security and localization; `vendor/bin/pint` owns everything mechanical.
- Every method and property carries a docblock, whatever its visibility. Class members run constants → properties → constructor → public → protected → private.
- No comments inside a method body, array literal, route group or markup — in PHP, Blade, JS or Vue alike. A non-obvious reason goes in the docblock or the commit message.
- A condition with more than one clause goes multiline, the boolean operator leading each line.
- All database access goes through a repository. The one sanctioned exception is a DataGrid's `prepareQueryBuilder()`.
- Events are dot-delimited strings (`catalog.product.update.after`), never event classes, and fire in `before`/`after` pairs.
- `env()` is called only inside `config/`; read admin settings with `core()->getConfigData()`.
- Authorize on the server, scope every storefront query to the authenticated customer, and escape with `e()` anything interpolated into markup — an attribute is the dangerous position.

## Blade

- CRITICAL: the same skill covers every `.blade.php` file.
- Binding: `attr="text"` is a literal, `:attr="expr"` is a Blade/PHP expression, `::attr="expr"` escapes to a literal `:attr` for Vue. Getting `:` vs `::` wrong is the most common source of bugs.
- Reuse the globally registered `x-admin::` / `x-shop::` components and layouts; prefix only your own new components with your package namespace.
- Vue-backed components: `<v-name>` wrapper + `<script type="text/x-template" id="v-name-template">` + `app.component("v-name", ...)`, all inside `@pushOnce('scripts')` … `@endPushOnce`. Emit runtime values as `@{{ … }}`.
- Formatting: 4 spaces; more than one attribute means one per line with the closing `>` on its own line; a single attribute stays inline; no blank lines between a tag's attributes; one blank line between sibling blocks.
- Align the `=>` in Blade `@props`/arrays. Do NOT align them in real `.php` files — Pint single-spaces those.
- Comments follow the layer they sit in: `{{-- --}}` for Blade/PHP notes, `<!-- -->` for markup section dividers, and `/** … */` JSDoc blocks inside `<script>` and `<style>` — never `//` or bare `/* */` there.
- Comment casing: a sentence is capitalized and punctuated; a bare title/label is Title Case with no trailing period.
- Never hardcode UI strings — use `@lang('<ns>::app…')`, and add new keys to every locale.
- Gate admin actions with `@if (bouncer()->hasPermission('resource.action'))`.
- Bracket meaningful content with `{!! view_render_event('bagisto.<area>.<path>.before') !!}` / `.after`.
