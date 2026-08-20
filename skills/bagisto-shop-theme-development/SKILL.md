---
name: bagisto-shop-theme-development
description: Use when creating or changing a Bagisto storefront theme — a theme package, shop layouts, Blade component overrides, or the Vite asset pipeline for the customer-facing side. Trigger phrases include "shop theme", "storefront theme", "shop layout", "theme package", "vite", "tailwind", "publish views", "custom layout".
requires: bagisto-coding-standards
license: MIT
---

# Shop Theme Development

## Overview

Shop theme development in Bagisto involves creating custom storefront themes packaged as Laravel packages. The end result is a self-contained package that can be distributed and maintained independently.

## When to Apply

Activate this skill when:
- Creating custom storefront themes as packages
- Building theme packages for distribution
- Working with Vite-powered assets
- Customizing customer-facing pages
- Overriding default shop templates

## Bagisto Shop Theme Architecture

### Core Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **Theme Configuration** | Defines available themes | `config/themes.php` |
| **Views Path** | Blade template files | Defined in theme config |
| **Assets Path** | CSS, JS, images | Defined in theme config |
| **Theme Middleware** | Resolves active theme | `packages/Webkul/Shop/src/Http/Middleware/Theme.php` |
| **Theme Facade** | Manages theme operations | `packages/Webkul/Theme/src/Themes.php` |

### Key Configuration Properties

```php
// config/themes.php
'shop-default' => 'default',

'shop' => [
    'default' => [
        'name' => 'Default',
        'assets_path' => 'public/themes/shop/default',
        'views_path' => 'resources/themes/default/views',
        'vite' => [
            'hot_file' => 'shop-default-vite.hot',
            'build_directory' => 'themes/shop/default/build',
            'package_assets_directory' => 'src/Resources/assets',
        ],
    ],
],
```

## Reference files — load only what the current task needs

| File | Load when |
|---|---|
| [creating-a-theme.md](creating-a-theme.md) | Scaffolding the theme package and registering it |
| [assets.md](assets.md) | The Vite pipeline, the build, and the dev-server workflow |
| [layouts.md](layouts.md) | Shop layouts, Blade components, custom layouts |
| [reference.md](reference.md) | Package layout, key files, pitfalls, testing |

**REQUIRED SUB-SKILL:** Use bagisto-change-verification before calling any change done.
