# Attributes, families, groups and options

## Contents

- [The flags](#the-flags)
- [Creating an attribute](#creating-an-attribute)
- [Options](#options)
- [Families and groups](#families-and-groups)
- [Validation](#validation)
- [Swatches](#swatches)
- [System attributes](#system-attributes)

## The flags

`Attribute::$fillable` is the whole contract. Each flag changes behaviour
somewhere far from the attribute itself:

| Flag | Effect |
|---|---|
| `is_required` | Adds `required` to the product form's rules |
| `is_unique` | The value must be unique across products |
| `value_per_locale` | One value row per locale |
| `value_per_channel` | One value row per channel |
| `is_filterable` | Offered as a storefront layered-navigation filter — **needs a `product_flat` column** |
| `is_configurable` | May be used as a configurable product's axis |
| `is_visible_on_front` | Shown on the product page |
| `is_comparable` | Included in the compare table |
| `is_user_defined` | `false` marks a system attribute — see below |
| `enable_wysiwyg` | Renders a rich-text editor for `textarea` |
| `default_value` | Pre-filled on a new product |
| `position` | Order within its group |
| `swatch_type` | For `select` used as a variant axis |
| `validation`, `regex` | See [Validation](#validation) |

`is_configurable` is only meaningful on a `select`: a configurable product's
axes must be option-backed, so a text attribute cannot be one.

## Creating an attribute

Through `AttributeRepository`, never the model:

```php
$attribute = $this->attributeRepository->create([
    'code'             => 'material',
    'admin_name'       => 'Material',
    'type'             => 'select',
    'validation'       => null,
    'position'         => 10,
    'is_required'      => 0,
    'is_unique'        => 0,
    'value_per_locale' => 1,
    'value_per_channel'=> 0,
    'is_filterable'    => 1,
    'is_configurable'  => 1,
    'options'          => [
        'option_1' => ['admin_name' => 'Cotton', 'sort_order' => 1],
    ],
]);
```

Then, if the attribute is filterable or belongs in a listing, **add a
`product_flat` column of the same name** in a migration. The flat indexer fills
only columns that already exist, so without it the attribute is skipped
silently.

`code` is the identity used everywhere — in `product_flat`, in imports, in
`$product->{$code}`. Changing it later orphans every value and every reference.

## Options

`select`, `multiselect` and `checkbox` carry them — the three types
`AttributeRepository::create()` creates options for — stored in
`attribute_options` with labels in `attribute_option_translations`.

- **The stored value is the option id.** `select` writes one id to
  `integer_value`; `multiselect` and `checkbox` write comma-separated ids to
  `text_value`.
- **Labels are translatable**, so a new option needs its label in all 22 locales.
- **`sort_order` drives display order**, not insertion order.
- **Deleting an option orphans the products using it** — their stored id no
  longer resolves. Check usage first.

Swatch options additionally carry `swatch_value` (a colour or an image path) and
a translatable `swatch_alt`.

## Families and groups

```
attribute_families  →  attribute_groups  →  attributes
```

A family is a whole product form; a group is a section within it. A product
belongs to one family, which determines its attributes entirely — an attribute
absent from the family is absent from the form, so nothing is ever saved for it.

Use `AttributeFamilyRepository` and `AttributeGroupRepository`. Both
`AttributeFamily::custom_attributes()` and `AttributeGroup::custom_attributes()`
walk the relation.

Adding an attribute to an existing family makes it appear on every product of
that family, with no value until each is saved — reads fall back to
`default_value`, or null.

## Validation

`validation` holds one of `ValidationEnum`: `numeric`, `email`, `decimal`,
`url`, `regex`. Only `regex` uses the separate `regex` column.

`Attribute::$validations` (the `getValidationsAttribute` accessor) assembles the
frontend rule string from the flags — `required` from `is_required`, `decimal`
for a `price`, a `size:` rule for `file` and `image` read from the admin config.

Two things this accessor teaches:

- **Upload size comes from configuration**, not from a constant —
  `catalog.products.attribute.file_attribute_upload_size` and its image
  counterpart, defaulting to 2048.
- **An empty rule must never reach the output.** An attribute with
  `validation = regex` and a null `regex` would emit a bare `regex:`, which
  breaks both the PHP validator and the JavaScript that parses the rule string.
  Guard for it whenever you build rules from an attribute.

A regex must be valid in **both** PCRE and JavaScript, since it is enforced
server-side and in the browser. Bagisto restricts the shared modifiers to
`imsu`.

## Swatches

`SwatchTypeEnum` is `dropdown`, `color`, `image`, `text`. It applies to a
`select` used as a configurable axis and changes only how options render — the
stored value is still the option id.

## System attributes

`is_user_defined = false` marks an attribute Bagisto itself depends on — `sku`,
`name`, `price`, `status` and the rest. The admin controller refuses to edit or
delete them:

```php
if (! $attribute->is_user_defined) {
    // reject
}
```

Never flip the flag to work around that guard. Code throughout the catalogue,
the indexers and the storefront reads these by code and assumes their type and
scope; changing one breaks far from where it was edited.
