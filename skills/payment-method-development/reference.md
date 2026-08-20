## Built-in Payment Methods

- **CashOnDelivery**: `packages/Webkul/Payment/src/Payment/CashOnDelivery.php`
- **MoneyTransfer**: `packages/Webkul/Payment/src/Payment/MoneyTransfer.php`
- **PaypalStandard**: `packages/Webkul/Paypal/src/Payment/Standard.php`
- **PaypalSmartButton**: `packages/Webkul/Paypal/src/Payment/SmartButton.php`

## Best Practices for Payment Classes

### Error Handling

Always implement comprehensive error handling in your payment methods:

```php
/**
 * Handle payment errors gracefully.
 *
 * @param  \Exception  $e
 * @return array
 */
protected function handlePaymentError(\Exception $e)
{
    // Log the error for debugging.
    \Log::error('Payment error in ' . $this->code, [
        'error' => $e->getMessage(),
        'trace' => $e->getTraceAsString(),
    ]);

    // Return user-friendly error message.
    return [
        'success' => false,
        'error'   => 'Payment processing failed. Please try again or contact support.',
    ];
}
```

### Security Considerations

Always validate and sanitize data before processing payments to protect your application and customers:

```php
/**
 * Validate payment data before processing.
 *
 * @param  array  $data
 * @return bool
 *
 * @throws \InvalidArgumentException
 */
protected function validatePaymentData($data)
{
    $validator = validator($data, [
        'amount'        => 'required|numeric|min:0.01',
        'currency'      => 'required|string|size:3',
        'customer_email'=> 'required|email',
    ]);

    if ($validator->fails()) {
        throw new \InvalidArgumentException($validator->errors()->first());
    }

    return true;
}
```

### Logging and Debugging

Proper logging helps you track payment activities and troubleshoot issues without exposing sensitive information:

```php
/**
 * Log payment activities for debugging and audit.
 *
 * @param  string  $action
 * @param  array   $data
 * @return void
 */
protected function logPaymentActivity($action, $data = [])
{
    // Remove sensitive data before logging.
    $sanitizedData = array_diff_key($data, [
        'api_key'      => '',
        'secret_key'   => '',
        'card_number'  => '',
        'cvv'          => '',
    ]);

    \Log::info("Payment {$action} for {$this->code}", $sanitizedData);
}
```

> **Implementation Note:** The methods shown in this section are **demonstration examples** for best practices. In real-world applications, you need to implement these methods according to your specific payment gateway requirements and business logic. Use these examples as reference guides and adapt them to your particular use case.

## Example: PayPal Smart Button (Complex Integration)

For complex payment integrations like PayPal, see `packages/Webkul/Paypal/src/Payment/SmartButton.php`:

- Extends PayPal base class which extends Payment.
- Uses PayPal SDK for API calls.
- Implements createOrder, captureOrder, getOrder, refundOrder.
- Handles sandbox/live environment switching.

## Package Structure

```
packages
└── Webkul
    └── CustomStripePayment
        └── src
            ├── Payment
            │   └── CustomStripePayment.php                 # Payment processing logic
            ├── Config
            │   ├── payment-methods.php                     # Payment method definition
            │   └── system.php                              # Admin configuration
            └── Providers
                └── CustomStripePaymentServiceProvider.php  # Registration
```

## Testing

Payment methods can be tested using the checkout tests in `packages/Webkul/Shop/tests/Feature/Checkout/CheckoutTest.php`.

## Key Files Reference

| File | Purpose |
|------|---------|
| `packages/Webkul/Payment/src/Payment/Payment.php` | Base abstract class |
| `packages/Webkul/Payment/src/Payment.php` | Payment facade methods |
| `packages/Webkul/Payment/src/Config/payment-methods.php` | Default payment methods config |
| `packages/Webkul/Paypal/src/Payment/SmartButton.php` | Complex payment example |
| `packages/Webkul/Paypal/src/Providers/PaypalServiceProvider.php` | Service provider example |
| `packages/Webkul/Payment/src/Payment/CashOnDelivery.php` | Simple payment example |
| `packages/Webkul/Payment/src/Payment/MoneyTransfer.php` | Payment with additional details |

## Common Pitfalls

- Forgetting to merge config in service provider
- Not matching `$code` property with config array key
- Not registering service provider in `bootstrap/providers.php`
- Forgetting to run `composer dump-autoload` after adding package
- Not clearing cache after configuration changes
- Not following PHPDoc conventions with proper punctuation
