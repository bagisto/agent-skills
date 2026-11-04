# A click that reports done but never landed

## Contents

- [The symptom](#the-symptom)
- [The cause: a lazy image swapping under the press](#the-cause-a-lazy-image-swapping-under-the-press)
- [Confirming it from the trace](#confirming-it-from-the-trace)
- [The fix: wait for the image, then click](#the-fix-wait-for-the-image-then-click)
- [Forcing the race to prove a fix](#forcing-the-race-to-prove-a-fix)

## The symptom

Playwright logs `click action done` and raises nothing, yet no `click` fired and
the link was never followed. The test fails at the next assertion that needs the
new page — or later, if an assertion the old page also satisfies comes first.
It is rare and tends to surface as one shard on one database, which is not
evidence of flakiness: see
[troubleshooting.md](troubleshooting.md#flaky-is-a-conclusion-not-a-starting-hypothesis).

## The cause: a lazy image swapping under the press

`v-shimmer-image`
(`packages/Webkul/Shop/src/Resources/views/components/media/images/lazy.blade.php`)
renders a `div.shimmer` placeholder under `v-if="isLoading"` and removes it from
the DOM the moment its image loads. Chromium dispatches no `click` when the
element that received the `mousedown` is removed before the `mouseup`; an
element that is only hidden keeps the click. A press that lands on the
placeholder as its image arrives is therefore lost. On **2.5**,
`omnibus-shop.spec.ts` failed this way on MariaDB while MySQL and PostgreSQL
passed the same commit: the image finished downloading about 10 ms before the
press, and the press took 9 ms.

The component and the product card are the same on **2.4** and **2.5**, so both
lines are exposed. Any link wrapping an `x-shop::media.images.lazy` image is,
most often the product card (Shop's `components/products/card.blade.php`):
search, category and compare render it, and so do the carousels on the home,
product and cart pages. The admin is not exposed, because it puts no
placeholder-swapping image inside a link.

## Confirming it from the trace

The click's Action snapshot has the `div.shimmer` inside the link and its After
snapshot the `<img>`, and the Network tab has no request for the link's `href`.
Both together are the signature; either alone points somewhere else.

## The fix: wait for the image, then click

The `<img>` is `v-show="! isLoading"`, so it is visible only once that card's
placeholder has gone, and nothing in the component brings it back. The page can
still replace the card: the category page re-mounts every card, placeholder and
all, on each sort, filter, page-size or mode change. Wait right before the
click, after the last change to the list:

```ts
private cardImage(productName: string) {
    return this.cardLink(productName).getByRole("img");
}

private async waitForCardImageLoaded(productName: string): Promise<void> {
    await expect(this.cardImage(productName)).toBeVisible();
}
```

where `cardLink()` is the link the page object already clicks. Then prove
arrival with something only the destination renders, so a lost click fails on
the line that lost it:

```ts
await this.waitForCardImageLoaded(productName);
await this.cardLink(productName).click();

await expect(this.productForm).toBeVisible();
```

`productForm` is Shop's `form:has(input[name="product_id"])`, which only the
product page renders. A heading check works too, but only with `exact: true` —
see [locators.md](locators.md#bagisto-markup-that-defeats-the-obvious-locator).
On **2.5**, `OmnibusShopPage` in the Admin suite follows this pattern as
`waitForSearchResultImageLoaded()`; **2.4** has no page object that does yet.

## Forcing the race to prove a fix

A green run proves nothing about a window this narrow. Force it in a throwaway
spec beside the one you are fixing: hold the placeholder image back, and on
`mousedown` do what Vue does when it arrives.

```ts
await shopPage.route(/product-placeholder/, async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 3000));
    await route.continue();
});

await shopPage.addInitScript(() => {
    document.addEventListener(
        "mousedown",
        (event) => {
            const shimmer = (event.target as Element).closest("a .shimmer");

            if (!shimmer) {
                return;
            }

            (shimmer.nextElementSibling as HTMLElement).style.display = "";
            shimmer.remove();
        },
        true,
    );
});
```

Run it against the old page object, where it must fail the way CI did, then
against the fix with `--trace=on`, where the image wait should hold for the
delay. Then delete the spec: it proves the page object, not the application.

The route matches the core placeholder,
`images/<template>-product-placeholder.webp`, which a product without an image
shows unless the merchant or the theme has set its own. Otherwise route
whatever URL the card's `img` requests.
