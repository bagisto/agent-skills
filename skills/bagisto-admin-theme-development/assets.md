## Vite-Powered Assets

### Step 1: Create Asset Configuration Files

Create in your package root:

**File:** `package.json`

```json
{
    "name": "custom-admin-theme",
    "private": true,
    "description": "Custom Admin Theme Package for Bagisto",
    "scripts": {
        "dev": "vite",
        "build": "vite build"
    },
    "devDependencies": {
        "autoprefixer": "^10.4.14",
        "axios": "^1.1.2",
        "laravel-vite-plugin": "^0.7.2",
        "postcss": "^8.4.23",
        "tailwindcss": "^3.3.2",
        "vite": "^4.0.0"
    }
}
```

**File:** `vite.config.js`

```javascript
import { defineConfig, loadEnv } from "vite";
import laravel from "laravel-vite-plugin";
import path from "path";

export default defineConfig(({ mode }) => {
    const envDir = "../../../";

    Object.assign(process.env, loadEnv(mode, envDir));

    return {
        build: {
            emptyOutDir: true,
        },
        envDir,
        server: {
            host: process.env.VITE_HOST || "localhost",
            port: process.env.VITE_ADMIN_PORT || 5174,
            cors: true,
        },
        plugins: [
            laravel({
                hotFile: "../../../public/admin-custom-vite.hot",
                publicDirectory: "../../../public",
                buildDirectory: "themes/admin/custom-admin/build",
                input: [
                    "src/Resources/assets/css/app.css",
                    "src/Resources/assets/js/app.js",
                ],
                refresh: true,
            }),
        ],
    };
});
```

**File:** `tailwind.config.js`

```javascript
module.exports = {
    content: [
        "./src/Resources/**/*.blade.php",
        "../../../resources/admin-themes/custom-admin-theme/**/*.blade.php"
    ],
    theme: {
        extend: {
            colors: {
                navyBlue: "#060C3B",
            },
        },
    },
    plugins: [],
};
```

**File:** `postcss.config.js`

```javascript
module.exports = {
    plugins: {
        tailwindcss: {},
        autoprefixer: {},
    },
}
```

### Step 2: Add to Bagisto Vite Config

**File:** `config/bagisto-vite.php`

```php
'admin-custom-theme' => [
    'hot_file' => 'admin-custom-vite.hot',
    'build_directory' => 'themes/admin/custom-admin/build',
    'package_assets_directory' => 'src/Resources/assets',
],
```

### Development Commands

```bash
# Navigate to package
cd packages/Webkul/CustomAdminTheme

# Install dependencies
npm install

# Start dev server with hot reload
npm run dev

# Build for production
npm run build
```

## Development Workflow

### Option A: Symlink (Recommended)

Create symlink for real-time development without republishing:

```bash
# Remove published views
rm -rf resources/admin-themes/custom-admin-theme/views

# Create symlink from package to resources
ln -s $(pwd)/packages/Webkul/CustomAdminTheme/src/Resources/views resources/admin-themes/custom-admin-theme/views
```

### Option B: Direct Package Development

Work directly in package and republish when needed:

```bash
# After making changes
php artisan vendor:publish --provider="Webkul\CustomAdminTheme\Providers\CustomAdminThemeServiceProvider" --force
```
