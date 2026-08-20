## Base Payment Class Reference

**Location:** `packages/Webkul/Payment/src/Payment/Payment.php`

All payment methods extend `Webkul\Payment\Payment\Payment` abstract class:

```php
<?php

namespace Webkul\Payment\Payment;

use Webkul\Checkout\Facades\Cart;

abstract class Payment
{
    /**
     * Cart.
     *
     * @var \Webkul\Checkout\Contracts\Cart
     */
    protected $cart;

    /**
     * Checks if payment method is available.
     *
     * @return bool
     */
    public function isAvailable()
    {
        return $this->getConfigData('active');
    }

    /**
     * Get payment method code.
     *
     * @return string
     */
    public function getCode()
    {
        if (empty($this->code)) {
            // throw exception
        }

        return $this->code;
    }

    /**
     * Get payment method title.
     *
     * @return string
     */
    public function getTitle()
    {
        return $this->getConfigData('title');
    }

    /**
     * Get payment method description.
     *
     * @return string
     */
    public function getDescription()
    {
        return $this->getConfigData('description');
    }

    /**
     * Get payment method image.
     *
     * @return string
     */
    public function getImage()
    {
        return $this->getConfigData('image');
    }

    /**
     * Retrieve information from payment configuration.
     *
     * @param  string  $field
     * @return mixed
     */
    public function getConfigData($field)
    {
        return core()->getConfigData('sales.payment_methods.'.$this->getCode().'.'.$field);
    }

    /**
     * Abstract method to get the redirect URL.
     *
     * @return string The redirect URL.
     */
    abstract public function getRedirectUrl();

    /**
     * Set cart.
     *
     * @return void
     */
    public function setCart()
    {
        if (! $this->cart) {
            $this->cart = Cart::getCart();
        }
    }

    /**
     * Get cart.
     *
     * @return \Webkul\Checkout\Contracts\Cart
     */
    public function getCart()
    {
        if (! $this->cart) {
            $this->setCart();
        }

        return $this->cart;
    }

    /**
     * Return cart items.
     *
     * @return \Illuminate\Database\Eloquent\Collection
     */
    public function getCartItems()
    {
        if (! $this->cart) {
            $this->setCart();
        }

        return $this->cart->items;
    }

    /**
     * Get payment method sort order.
     *
     * @return string
     */
    public function getSortOrder()
    {
        return $this->getConfigData('sort');
    }

    /**
     * Get payment method additional information.
     *
     * @return array
     */
    public function getAdditionalDetails()
    {
        if (empty($this->getConfigData('instructions'))) {
            return [];
        }

        return [
            'title' => trans('admin::app.configuration.index.sales.payment-methods.instructions'),
            'value' => $this->getConfigData('instructions'),
        ];
    }
}
```

## Key Methods to Implement

| Method | Purpose | Required |
|--------|---------|----------|
| `getRedirectUrl()` | Return URL for redirect payment methods | Yes (abstract) |
| `getImage()` | Return payment method logo URL | No (uses default) |
| `getAdditionalDetails()` | Return additional info (instructions, etc.) | No (uses default) |
| `isAvailable()` | Override to add custom availability logic | No (uses default) |
| `getConfigData($field)` | Override if codes are not in convention | No (uses default) |

> **Implementation Note:** Usually, you don't need to explicitly set the `$code` property because if your codes are properly set, then config data can get properly. However, if codes are not in convention then you might need this property to override the default behavior.
