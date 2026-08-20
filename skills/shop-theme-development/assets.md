## Vite-Powered Assets

### Step 1: Create Asset Configuration Files

Create in your package root:

**File:** `package.json`

```json
{
    "name": "custom-theme",
    "private": true,
    "description": "Custom Theme Package for Bagisto",
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
            port: process.env.VITE_PORT || 5173,
            cors: true,
        },
        plugins: [
            laravel({
                hotFile: "../../../public/custom-theme-vite.hot",
                publicDirectory: "../../../public",
                buildDirectory: "themes/custom-theme/build",
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
        "../../../resources/themes/custom-theme/**/*.blade.php"
    ],
    theme: {
        container: {
            center: true,
            screens: { "2xl": "1440px" },
            padding: { DEFAULT: "90px" },
        },
        screens: {
            sm: "525px",
            md: "768px",
            lg: "1024px",
            xl: "1240px",
            "2xl": "1440px",
            1180: "1180px",
            1060: "1060px",
            991: "991px",
        },
        extend: {
            colors: {
                navyBlue: "#060C3B",
                darkGreen: "#40994A",
            },
            fontFamily: {
                poppins: ["Poppins"],
                dmserif: ["DM Serif Display"],
            },
        },
    },
    plugins: [],
    safelist: [{ pattern: /icon-/ }],
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
'custom-theme' => [
    'hot_file' => 'custom-theme-vite.hot',
    'build_directory' => 'themes/custom-theme/build',
    'package_assets_directory' => 'src/Resources/assets',
],
```

### Development Commands

```bash
# Navigate to package
cd packages/Webkul/CustomTheme

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
rm -rf resources/themes/custom-theme/views

# Create symlink from package to resources
ln -s $(pwd)/packages/Webkul/CustomTheme/src/Resources/views resources/themes/custom-theme/views
```

### Option B: Direct Package Development

Work directly in package and republish when needed:

```bash
# After making changes
php artisan vendor:publish --provider="Webkul\CustomTheme\Providers\CustomThemeServiceProvider" --force
```
