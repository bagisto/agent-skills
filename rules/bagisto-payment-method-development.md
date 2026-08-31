# Payment Gateway Development

- CRITICAL: ALWAYS use the bagisto-payment-method-development skill when working with payment methods in Bagisto.
- Payment methods in Bagisto are located in `packages/Webkul/Payment/src/Payment/` and `packages/Webkul/Paypal/src/Payment/`.
- All payment methods extend `Webkul\Payment\Payment\Payment` abstract class.
- Payment configuration is defined in `Config/payment-methods.php` files.
- System configuration for admin panel is defined in `Config/system.php` files.
- Service providers must merge payment method configuration using `$this->mergeConfigFrom()`.
- Always follow the existing code patterns and PHPDoc conventions when creating payment methods.
- For testing payment methods, refer to `packages/Webkul/Shop/tests/Feature/Checkout/CheckoutTest.php`.
