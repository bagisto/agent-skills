## Shop Layouts

> **Writing the Blade itself?** The **coding-standards** skill carries the markup rules —
> `:` vs `::` attribute binding, anonymous vs Vue-backed components, indentation, comment
> style, and where translations and `view_render_event` hooks go.

### Using Shop Layout

```blade
<x-shop::layouts>
    <x-slot:title>
        Page Title
    </x-slot>

    {{-- Page content --}}
</x-shop::layouts>
```

### Layout Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `has-header` | Boolean | true | Include header navigation |
| `has-feature` | Boolean | true | Show featured section |
| `has-footer` | Boolean | true | Include footer |

### Minimal Page Example

```blade
<x-shop::layouts
    :has-header="false"
    :has-footer="false"
>
    <x-slot:title>
        Minimal Page
    </x-slot>

    {{-- Content without header/footer --}}
</x-shop::layouts>
```

## Shop Blade Components

### Available Components

| Component | Usage | Description |
|-----------|-------|-------------|
| `<x-shop::accordion>` | Collapsible sections | Toggle content visibility |
| `<x-shop::breadcrumbs>` | Navigation trail | Show current page path |
| `<x-shop::button>` | Action buttons | Loading states supported |
| `<x-shop::datagrid>` | Data tables | Sorting, filtering, pagination |
| `<x-shop::drawer>` | Slide-out panels | Position: top/bottom/left/right |
| `<x-shop::dropdown>` | Dropdown menus | Position: top-left, bottom-right, etc. |
| `<x-shop::flat-picker.date>` | Date picker | Based on Flatpickr |
| `<x-shop::flat-picker.datetime>` | Date-time picker | Based on Flatpickr |
| `<x-shop::media.images>` | Image upload | Multiple images support |
| `<x-shop::modal>` | Dialog boxes | Header, content, footer slots |
| `<x-shop::quantity-changer>` | Quantity input | +/- buttons |
| `<x-shop::table>` | Data tables | Customizable thead/tbody |
| `<x-shop::tabs>` | Tab navigation | Position: left/right/center |
| `<x-shop::shimmer.*>` | Loading effects | Skeleton loaders |

## Custom Layouts

### Creating Custom Layout

**File:** `packages/Webkul/CustomTheme/src/Resources/views/layouts/master.blade.php`

```blade
<!DOCTYPE html>
<html lang="{{ app()->getLocale() }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ $title ?? config('app.name') }}</title>
    
    {{-- Load assets manually for custom layouts --}}
    @bagistoVite([
        'src/Resources/assets/css/app.css',
        'src/Resources/assets/js/app.js'
    ])
</head>
<body>
    @if($hasHeader ?? true)
        @include('custom-theme::layouts.header')
    @endif
    
    <main>
        {{ $slot }}
    </main>
    
    @if($hasFooter ?? true)
        @include('custom-theme::layouts.footer')
    @endif
</body>
</html>
```
