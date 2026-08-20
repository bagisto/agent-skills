## Admin Layouts

> **Writing the Blade itself?** The **coding-standards** skill carries the markup rules —
> `:` vs `::` attribute binding, anonymous vs Vue-backed components, indentation, comment
> style, and where translations and `view_render_event` hooks go.

### Using Admin Layout

```blade
<x-admin::layouts>
    <x-slot:title>
        Page Title
    </x-slot>

    {{-- Page Header --}}
    <div class="flex gap-4 justify-between max-sm:flex-wrap">
        <p class="py-[11px] text-xl text-gray-800 dark:text-white font-bold">
            Page Heading
        </p>
        <div class="flex gap-x-2.5 items-center">
            <button class="primary-button">
                Action Button
            </button>
        </div>
    </div>

    {{-- Page content --}}
    <div class="mt-8">
        Content goes here
    </div>
</x-admin::layouts>
```

### Layout Features

The admin layout automatically provides:
- **Sidebar Navigation**: Admin menu with collapsible sections
- **Header**: Top navigation with user menu and notifications
- **Responsive Design**: Mobile-friendly layout
- **Dark Mode**: Built-in dark mode support
- **Breadcrumbs**: Automatic breadcrumb generation

### Admin Layout Best Practices

- Always use the title slot for SEO and user experience
- Follow Bagisto's admin design patterns
- Use provided CSS classes (e.g., `primary-button`, `secondary-button`)
- Keep layout structure clean and semantic

## Admin Blade Components

### Available Components

| Component | Usage | Description |
|-----------|-------|-------------|
| `<x-admin::accordion>` | Collapsible sections | Toggle content visibility |
| `<x-admin::button>` | Action buttons | Loading states supported |
| `<x-admin::charts.bar>` | Bar charts | Based on Chart.js |
| `<x-admin::charts.line>` | Line charts | Based on Chart.js |
| `<x-admin::datagrid>` | Data tables | Sorting, filtering, pagination |
| `<x-admin::drawer>` | Slide-out panels | Position: top/bottom/left/right |
| `<x-admin::dropdown>` | Dropdown menus | Position options available |
| `<x-admin::flat-picker.date>` | Date picker | Based on Flatpickr |
| `<x-admin::flat-picker.datetime>` | Date-time picker | Based on Flatpickr |
| `<x-admin::media.images>` | Image upload | Multiple images support |
| `<x-admin::media.videos>` | Video upload | Video support |
| `<x-admin::modal>` | Dialog boxes | Header, content, footer slots |
| `<x-admin::quantity-changer>` | Quantity input | +/- buttons |
| `<x-admin::seo>` | SEO metadata | Meta title and description |
| `<x-admin::table>` | Data tables | Customizable thead/tbody |
| `<x-admin::tabs>` | Tab navigation | Position: left/right/center |
| `<x-admin::shimmer.*>` | Loading effects | Skeleton loaders |

## Custom Layouts

### Creating Custom Layout

**File:** `packages/Webkul/CustomAdminTheme/src/Resources/views/layouts/master.blade.php`

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
<body class="dark:bg-gray-900">
    {{-- Custom sidebar --}}
    @include('custom-admin-theme::layouts.sidebar')
    
    <div class="flex">
        {{-- Main content area --}}
        <main class="flex-1 p-6">
            {{ $slot }}
        </main>
    </div>
</body>
</html>
```
