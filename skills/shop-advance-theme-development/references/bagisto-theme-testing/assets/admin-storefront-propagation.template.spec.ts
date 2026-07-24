import { expect, test, type Locator } from "@playwright/test";

function required(name: string): string {
    const value = process.env[name]?.trim();
    if (!value) {
        throw new Error(`${name} is required for the admin propagation contract`);
    }
    return value;
}

async function readEditableValue(field: Locator): Promise<string> {
    const tagName = await field.evaluate((element) => element.tagName.toLowerCase());
    if (tagName === "input" || tagName === "textarea") {
        return field.inputValue();
    }
    if ((await field.getAttribute("contenteditable")) === "true") {
        return (await field.textContent()) ?? "";
    }
    throw new Error("Adapt readEditableValue for the installed Bagisto editor component");
}

async function writeEditableValue(field: Locator, value: string): Promise<void> {
    const tagName = await field.evaluate((element) => element.tagName.toLowerCase());
    if (tagName === "input" || tagName === "textarea") {
        await field.fill(value);
        return;
    }
    if ((await field.getAttribute("contenteditable")) === "true") {
        await field.fill(value);
        return;
    }
    throw new Error("Adapt writeEditableValue for the installed Bagisto editor component");
}

test("admin content propagates to the intended storefront scope and is restored", async ({
    browser,
    baseURL,
}) => {
    if (process.env.BAGISTO_E2E_ALLOW_MUTATION !== "1") {
        throw new Error("Set BAGISTO_E2E_ALLOW_MUTATION=1 only for an approved isolated environment");
    }
    if (!baseURL) {
        throw new Error("The Playwright config must define use.baseURL");
    }

    const adminStorageState = required("BAGISTO_THEME_ADMIN_STORAGE_STATE");
    const adminEditUrl = new URL(required("BAGISTO_THEME_ADMIN_EDIT_URL"), baseURL).toString();
    const adminFieldSelector = required("BAGISTO_THEME_ADMIN_FIELD_SELECTOR");
    const adminSaveSelector = required("BAGISTO_THEME_ADMIN_SAVE_SELECTOR");
    const adminSuccessSelector = required("BAGISTO_THEME_ADMIN_SUCCESS_SELECTOR");
    const storefrontUrl = new URL(required("BAGISTO_THEME_STOREFRONT_URL"), baseURL).toString();
    const storefrontSelector = required("BAGISTO_THEME_STOREFRONT_SELECTOR");
    const isolationUrlValue = process.env.BAGISTO_THEME_ISOLATION_URL?.trim();
    const isolationUrl = isolationUrlValue
        ? new URL(isolationUrlValue, baseURL).toString()
        : undefined;
    const isolationSelector = process.env.BAGISTO_THEME_ISOLATION_SELECTOR?.trim() || storefrontSelector;
    const marker = `E2E-THEME-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    let originalValue: string | undefined;

    const saveAdminValue = async (value: string): Promise<void> => {
        const context = await browser.newContext({ storageState: adminStorageState });
        const page = await context.newPage();
        try {
            await page.goto(adminEditUrl);
            const field = page.locator(adminFieldSelector).first();
            await expect(field).toBeVisible();
            await writeEditableValue(field, value);
            await page.locator(adminSaveSelector).click();
            await expect(page.locator(adminSuccessSelector)).toBeVisible();
        } finally {
            await context.close();
        }
    };

    const readStorefrontValue = async (url: string, selector: string): Promise<string> => {
        const context = await browser.newContext();
        const page = await context.newPage();
        try {
            await page.goto(url, { waitUntil: "domcontentloaded" });
            const target = page.locator(selector).first();
            await expect(target).toBeVisible();
            return (await target.textContent()) ?? "";
        } finally {
            await context.close();
        }
    };

    const adminContext = await browser.newContext({ storageState: adminStorageState });
    const adminPage = await adminContext.newPage();
    try {
        await adminPage.goto(adminEditUrl);
        const field = adminPage.locator(adminFieldSelector).first();
        await expect(field).toBeVisible();
        originalValue = await readEditableValue(field);
    } finally {
        await adminContext.close();
    }

    try {
        await saveAdminValue(marker);
        await expect.poll(() => readStorefrontValue(storefrontUrl, storefrontSelector)).toContain(marker);

        if (isolationUrl) {
            await expect.poll(() => readStorefrontValue(isolationUrl, isolationSelector)).not.toContain(marker);
        }
    } finally {
        if (originalValue !== undefined) {
            await saveAdminValue(originalValue);
            await expect.poll(() => readStorefrontValue(storefrontUrl, storefrontSelector)).not.toContain(marker);
        }
    }
});
