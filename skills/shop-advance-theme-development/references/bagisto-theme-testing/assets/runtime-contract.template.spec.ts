import { expect, test } from "@playwright/test";

const routes = (process.env.BAGISTO_THEME_TEST_ROUTES ?? "/")
    .split(",")
    .map((route) => route.trim())
    .filter(Boolean);

const viewports = [
    { name: "mobile", width: 390, height: 844 },
    { name: "tablet", width: 768, height: 1024 },
    { name: "desktop", width: 1440, height: 1000 },
];

const readySelector = process.env.BAGISTO_THEME_TEST_READY_SELECTOR?.trim();
const ignoredUrlPattern = process.env.BAGISTO_THEME_TEST_IGNORED_URLS
    ? new RegExp(process.env.BAGISTO_THEME_TEST_IGNORED_URLS)
    : null;
const observationMs = Number(process.env.BAGISTO_THEME_TEST_OBSERVATION_MS ?? "750");

if (!Number.isFinite(observationMs) || observationMs < 0 || observationMs > 10_000) {
    throw new Error("BAGISTO_THEME_TEST_OBSERVATION_MS must be between 0 and 10000");
}

for (const route of routes) {
    for (const viewport of viewports) {
        test(`runtime contract: ${route} at ${viewport.name}`, async ({ page, baseURL }) => {
            if (!baseURL) {
                throw new Error("The Playwright config must define use.baseURL");
            }

            const expectedOrigin = new URL(baseURL).origin;
            const pageErrors: string[] = [];
            const consoleErrors: string[] = [];
            const requestFailures: string[] = [];
            const responseFailures: string[] = [];
            const shouldObserve = (url: string) =>
                new URL(url).origin === expectedOrigin
                && !(ignoredUrlPattern?.test(url) ?? false);

            page.on("pageerror", (error) => pageErrors.push(error.message));
            page.on("console", (message) => {
                if (message.type() === "error" || /^\[Vue warn\]/.test(message.text())) {
                    consoleErrors.push(`${message.type()}: ${message.text()}`);
                }
            });
            page.on("requestfailed", (request) => {
                if (shouldObserve(request.url())) {
                    requestFailures.push(`${request.method()} ${request.url()}`);
                }
            });
            page.on("response", (response) => {
                if (response.status() >= 400 && shouldObserve(response.url())) {
                    responseFailures.push(
                        `${response.status()} ${response.request().method()} ${response.url()}`,
                    );
                }
            });

            await page.setViewportSize({ width: viewport.width, height: viewport.height });
            const response = await page.goto(route, { waitUntil: "domcontentloaded" });

            expect(response?.ok(), `HTTP failure for ${route}`).toBeTruthy();
            await expect(page.locator("html")).toHaveAttribute("lang", /.+/);
            await expect(page.locator("html")).toHaveAttribute("dir", /^(ltr|rtl)$/);
            await expect(page.locator("main").first()).toBeVisible();
            await expect(page).toHaveTitle(/\S+/);

            if (readySelector) {
                await expect(page.locator(readySelector).first()).toBeVisible();
            }
            if (observationMs > 0) {
                await page.waitForTimeout(observationMs);
            }

            const brokenImages = await page.locator("img:visible").evaluateAll((images) =>
                images
                    .filter((image) => {
                        const element = image as HTMLImageElement;
                        return element.complete && element.naturalWidth === 0;
                    })
                    .map((image) => (image as HTMLImageElement).currentSrc || image.getAttribute("src")),
            );
            const horizontalOverflow = await page.evaluate(
                () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
            );

            expect(pageErrors, "uncaught page errors").toEqual([]);
            expect(consoleErrors, "console/Vue errors").toEqual([]);
            expect(requestFailures, "same-origin request failures").toEqual([]);
            expect(responseFailures, "same-origin HTTP failures").toEqual([]);
            expect(brokenImages, "broken visible images").toEqual([]);
            expect(horizontalOverflow, "horizontal overflow in CSS pixels").toBeLessThanOrEqual(1);
        });
    }
}
