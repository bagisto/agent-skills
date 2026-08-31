# Product Type Development

- CRITICAL: ALWAYS use the bagisto-product-type-development skill when working with product types in Bagisto.
- Product types extend `Webkul\Product\Type\AbstractType` base class.
- Product type configuration is defined in `Config/product-types.php` files.
- Reference files: `configuration.md` (config structure), `abstract-type.md` (AbstractType methods), `building-a-type.md` (a complete implementation).
- Product types must be registered in service provider using `$this->mergeConfigFrom()`.
- Key methods to override: `isSaleable()`, `isStockable()`, `showQuantityBox()`, `haveSufficientQuantity()`, `prepareForCart()`, `getTypeValidationRules()`.
- Use `$additionalViews` for custom admin interface sections.
- Use `$skipAttributes` to hide irrelevant attributes for product type.
