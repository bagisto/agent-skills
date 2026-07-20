import { expect, test } from "@playwright/test";

const routes = (process.env.THEME_SMOKE_ROUTES ?? "/")
    .split(",")
    .map((route) => route.trim())
    .filter(Boolean);

const ignoredResponsePattern = process.env.THEME_SMOKE_IGNORED_RESPONSE_URLS
    ? new RegExp(process.env.THEME_SMOKE_IGNORED_RESPONSE_URLS)
    : null;

const readySelector = process.env.THEME_SMOKE_READY_SELECTOR?.trim();
const observationMs = Number(process.env.THEME_SMOKE_OBSERVATION_MS ?? "1000");

if (!Number.isFinite(observationMs) || observationMs < 0 || observationMs > 10000) {
    throw new Error("THEME_SMOKE_OBSERVATION_MS must be between 0 and 10000 milliseconds");
}

for (const route of routes) {
    test(`theme smoke: ${route}`, async ({ page }) => {
        const pageErrors: string[] = [];
        const consoleFailures: string[] = [];
        const failedRequests: string[] = [];
        const errorResponses: string[] = [];

        page.on("pageerror", (error) => pageErrors.push(error.message));
        page.on("console", (message) => {
            if (message.type() === "error" || /^\[Vue warn\]/.test(message.text())) {
                consoleFailures.push(`${message.type()}: ${message.text()}`);
            }
        });
        page.on("requestfailed", (request) => {
            if (!(ignoredResponsePattern?.test(request.url()) ?? false)) {
                failedRequests.push(`${request.method()} ${request.url()}`);
            }
        });
        page.on("response", (response) => {
            if (
                response.status() >= 400
                && !(ignoredResponsePattern?.test(response.url()) ?? false)
            ) {
                errorResponses.push(`${response.status()} ${response.request().method()} ${response.url()}`);
            }
        });

        const response = await page.goto(route, { waitUntil: "domcontentloaded" });

        expect(response?.ok(), `HTTP failure for ${route}`).toBeTruthy();
        await expect(page.locator("html")).toHaveAttribute("lang", /.+/);
        await expect(page.locator("html")).toHaveAttribute("dir", /^(ltr|rtl)$/);
        await expect(page.locator("main").first()).toBeVisible();
        if (readySelector) {
            await expect(page.locator(readySelector).first()).toBeVisible();
        }
        if (observationMs) {
            await page.waitForTimeout(observationMs);
        }
        expect(pageErrors, `page errors for ${route}`).toEqual([]);
        expect(consoleFailures, `console/Vue failures for ${route}`).toEqual([]);
        expect(failedRequests, `failed requests for ${route}`).toEqual([]);
        expect(errorResponses, `HTTP error responses for ${route}`).toEqual([]);
    });
}
