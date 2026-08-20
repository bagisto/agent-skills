## Complete Package Structure

```
packages/Webkul/CustomAdminTheme/
├── src/
│   ├── Providers/
│   │   └── CustomAdminThemeServiceProvider.php
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
│           ├── dashboard/
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
| `packages/Webkul/Admin/src/Providers/AdminServiceProvider.php` | Admin package registration |
| `packages/Webkul/Admin/src/Resources/views/components/*` | Admin components |
| `packages/Webkul/Theme/src/Themes.php` | Theme facade |

## Common Pitfalls

- Not clearing cache after theme config changes
- Forgetting to run composer dump-autoload after package registration
- Not copying complete admin assets (views and assets)
- Using custom layouts without manually loading @bagistoVite assets
- Working in published files instead of package source files
- Missing symlink setup for development workflow

## Testing

Test your admin theme by:
1. Setting admin-default in config/themes.php
2. Logging into admin panel
3. Checking dashboard and various admin pages
4. Verifying responsive design
5. Verifying all admin functionality works
6. Testing hot reload during development
