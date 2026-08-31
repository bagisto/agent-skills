# Shipping Method Development

- CRITICAL: ALWAYS use the bagisto-shipping-method-development skill when working with shipping methods in Bagisto.
- Shipping methods in Bagisto are located in `packages/Webkul/Shipping/src/Carriers/`.
- All shipping methods extend `Webkul\Shipping\Carriers\AbstractShipping` abstract class.
- Shipping carrier configuration is defined in `Config/carriers.php` files.
- System configuration for admin panel is defined in `Config/system.php` files.
- Service providers must merge carrier configuration using `$this->mergeConfigFrom()`.
- Always follow the existing code patterns and PHPDoc conventions when creating shipping methods.
- Use `core()->convertPrice()` for multi-currency support when setting prices.
- Check `$item->getTypeInstance()->isStockable()` for per-item shipping calculations.
