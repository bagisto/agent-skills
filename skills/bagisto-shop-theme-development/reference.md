## Complete Package Structure

```
packages/Webkul/CustomTheme/
├── src/
│   ├── Providers/
│   │   └── CustomThemeServiceProvider.php
│   └── Resources/
│       ├── assets/
│       │   ├── css/
│       │   │   └── app.css
│       │   ├── js/
│       │   │   └── app.js
│       │   ├── images/
│       │   └── fonts/
│       └── views/
│           ├── layouts/
│           │   └── master.blade.php
│           ├── home/
│           │   └── index.blade.php
│           ├── components/
│           └── ...
├── package.json
├── vite.config.js
├── tailwind.config.js
└── postcss.config.js
```

## Key Files Reference

| File | Purpose |
|------|---------|
| `config/themes.php` | Theme configuration |
| `config/bagisto-vite.php` | Vite asset configuration |
| `packages/Webkul/Shop/src/Providers/ShopServiceProvider.php` | Shop package registration |
| `packages/Webkul/Shop/src/Http/Middleware/Theme.php` | Theme resolution |
| `packages/Webkul/Theme/src/Themes.php` | Theme facade |
| `packages/Webkul/Shop/src/Resources/views/components/*` | Shop components |

## Common Pitfalls

- Not clearing cache after theme config changes
- Forgetting to run composer dump-autoload after package registration
- Not copying complete shop assets (views and assets)
- Using custom layouts without manually loading @bagistoVite assets
- Working in published files instead of package source files
- Missing symlink setup for development workflow

## Testing

Test your theme by:
1. Activating theme in channel settings
2. Visiting storefront pages
3. Checking responsive design
4. Verifying all shop functionality works
5. Testing hot reload during development
