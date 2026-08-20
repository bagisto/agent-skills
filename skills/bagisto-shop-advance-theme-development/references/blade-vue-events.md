# Blade, Vue, and Render-Event Contracts

## Contents

- [Preserve the runtime layout](#preserve-the-runtime-layout)
- [Override Blade components correctly](#override-blade-components-correctly)
- [Register inline Vue safely](#register-inline-vue-safely)
- [Preserve render-event extension points](#preserve-render-event-extension-points)
- [Diagnose integration failures](#diagnose-integration-failures)
- [Validate the browser runtime](#validate-the-browser-runtime)

Read this reference when changing the main layout, Shop Blade components, inline Vue components, or extension injection points.

## Preserve the runtime layout

Treat the installed Shop layout as a runtime contract, not merely as markup.

Locate it from component registration and `<x-shop::layouts>` resolution:

```bash
rg -n "anonymousComponentPath|<x-shop::layouts|app\\.mount|@bagistoVite" <shop-root> <active-theme-view-root>
```

Read the complete active layout before replacing it.

Preserve these head responsibilities unless the user explicitly removes one:

- Emit the document type.
- Set `lang` from the active locale.
- Set `dir` from locale direction.
- Provide the page-title slot.
- Provide charset and viewport metadata.
- Expose base URL and current-currency metadata used by scripts.
- Render the meta stack.
- Render the styles stack.
- Load the channel favicon or theme fallback.
- Load the theme CSS and JavaScript entry points.
- Preserve configured custom CSS.
- Preserve head render events.
- Preserve optional platform features detected in the current layout.

Preserve these body responsibilities:

- Render body-level extension events.
- Provide a keyboard-accessible skip link.
- Wrap Vue-controlled storefront content in one stable mount root.
- Render flash-message infrastructure.
- Render confirmation-dialog infrastructure.
- Honor header, feature or services, and footer props.
- Render cookie or consent UI when enabled.
- Give the primary content a stable `main` target.
- Render the page slot.
- Render the scripts stack before mounting Vue.
- Mount the global app exactly once.
- Preserve before and after mount events.
- Preserve configured custom JavaScript.

Keep layout props backward compatible.

When adding a prop:

1. Give it a safe default.
2. Keep existing kebab-case call sites working.
3. Test pages that deliberately disable the header, services, or footer.
4. Avoid requiring data unavailable on checkout, error, email, or guest pages.

Do not replace the runtime layout with a bare HTML shell unless you also reconstruct every required responsibility.

## Override Blade components correctly

Preserve the original relative path when overriding a Shop view.

Use these resolution rules:

- Override `<x-shop::layouts>` at the installed Shop component's relative path.
- Override `<x-shop::layouts.header>` at the registered header component path.
- Keep `shop::` includes namespaced to Shop unless the theme provider registers another namespace.
- Use a custom namespace only after calling `loadViewsFrom` for that namespace.
- Do not assume that a file named `layouts/master.blade.php` affects an anonymous layout component.
- Keep missing components available through the installed theme view finder's fallback.

Inspect component props and slots before changing markup:

```bash
rg -n "^@props|@isset\\(\\$(header|content|footer|toggle)" <shop-view-root>/components
```

Preserve:

- prop names and defaults;
- named slots;
- forwarded attributes;
- refs used by parent Vue components;
- input `name` and `id` values;
- `v-pre` boundaries;
- pushed script identifiers;
- accessibility roles and labels.

Do not document a component only from its directory name. Confirm that an `index.blade.php` or class-backed component exists.

## Register inline Vue safely

Detect the installed frontend contract before writing Vue:

1. Read the current asset entry file.
2. Identify where the global `app` object is created.
3. Identify global plugins, directives, and aliases.
4. Read the current package dependencies.
5. Preserve the installed module format and Vite plugins.

Use the established inline-component pattern when the current Shop views use it:

```blade
<v-example>
    <div aria-busy="true"><!-- fallback or shimmer --></div>
</v-example>

@pushOnce('scripts')
    <script type="text/x-template" id="v-example-template">
        <section>
            @{{ message }}
        </section>
    </script>

    <script type="module">
        app.component('v-example', {
            template: '#v-example-template',

            data() {
                return {
                    message: '',
                };
            },
        });
    </script>
@endPushOnce
```

Adapt the example to the syntax used by the installed source.

Follow these rules:

- Give each template ID a unique, stable value.
- Register each component before the global app mounts.
- Use `@pushOnce` when repeated component instances would duplicate registration.
- Escape Vue interpolation from Blade with the installed convention.
- Keep server-rendered fallback content meaningful.
- Use `type="module"` when the installed layout expects module scripts.
- Access Axios, emitters, validation, and other plugins through the established app contract.
- Add a dependency only after confirming that the current package does not already provide it.
- Update the package manifest and lock strategy together when adding a dependency.
- Avoid creating a second Vue app inside a Shop page.
- Avoid mounting over markup that must remain outside Vue control.
- Preserve CSRF and locale behavior provided by the installed HTTP plugin.

When placing inline Blade inside a Vue template:

- Keep Blade directives balanced before Vue processes the template.
- Escape literal Vue braces.
- Use bound attributes for runtime values.
- Use Blade attributes for server-known values.
- Keep form names identical to backend request contracts.
- Treat HTML from administrators or CMS records according to the existing sanitization contract.

## Preserve render-event extension points

Treat `view_render_event` calls as extension API surface.

Discover the actual event names instead of inventing them:

```bash
rg -n "view_render_event\\(" <shop-view-root>
```

Preserve existing events when overriding a view:

- Keep the exact event string.
- Keep before and after ordering.
- Keep the parameter keys and value types.
- Keep events adjacent to the UI region they wrap.
- Keep mount events around global Vue mounting.
- Keep layout head and body events in valid HTML locations.
- Keep checkout and product events inside the forms or state regions expected by extensions.

Add a new event only when a stable extension point is required.

Name new events consistently with the installed hierarchy:

1. Start with the platform and storefront scope.
2. Add page or component scope.
3. Add the specific region.
4. End with `before` or `after` when wrapping a region.

Pass only data that is already available and safe for listeners.

Distinguish event systems:

| Event system | Use for |
|---|---|
| `view_render_event` | Server-side extension injection while rendering Blade |
| Laravel `Event::dispatch` | Backend lifecycle behavior |
| Vue emits or shared emitter | Client-side component communication |
| Native DOM events | Browser behavior and accessibility |

Do not replace a server render event with a client event; extensions may listen before JavaScript starts.

## Diagnose integration failures

Check these causes in order:

1. Confirm that the active theme resolves the intended view path.
2. Confirm that the Vite manifest contains both entry points.
3. Confirm that the global `app` exists before inline registration.
4. Confirm that inline registration runs before `app.mount`.
5. Confirm that the mount root exists exactly once.
6. Confirm that template IDs are unique.
7. Confirm that Blade did not consume Vue interpolation.
8. Confirm that all imported packages exist in the current package manifest.
9. Confirm that pushed scripts are rendered by the active layout.
10. Confirm that a removed render event is not required by an extension.
11. Confirm that Content Security Policy permits the installed inline-script pattern.
12. Confirm that cached compiled views do not mask the current source.

## Validate the browser runtime

Test at least:

- a page with no inline Vue;
- a page with one inline component;
- a page with repeated component instances;
- a page that disables the standard header and footer;
- a right-to-left locale;
- a guest session and an authenticated customer session;
- a page with an extension injected through a render event.

Fail validation on:

- uncaught browser exceptions;
- Vue warnings caused by the theme;
- duplicate component-registration warnings;
- missing Vite assets;
- failed API requests;
- hydration or mount-root replacement of required server markup;
- inaccessible focus order after drawers or modals open;
- missing extension output at preserved event locations.

Capture the rendered HTML, browser console, failed requests, and a desktop and mobile screenshot as forward-test artifacts.
