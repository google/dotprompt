# Picoschema Reference

Picoschema is a compact, YAML-optimized schema definition format specifically
designed to aid in describing structured data for better understanding by
generative AI models. Whenever a schema is accepted by dotprompt in its
frontmatter, the Picoschema format is accepted.

Picoschema compiles to JSON Schema and is a subset of JSON Schema capabilities.

## Example

```yaml
product:
  id: string, Unique identifier for the product
  description?: string, Optional detailed description of the product
  price: number, Current price of the product
  inStock: integer, Number of items in stock
  isActive: boolean, Whether the product is currently available
  category(enum, Main category of the product): [ELECTRONICS, CLOTHING, BOOKS, HOME]
  tags(array, List of tags associated with the product): string
  primaryImage:
    url: string, URL of the primary product image
    altText: string, Alternative text for the image
  attributes(object, Custom attributes of the product):
    (*): any, Allow any attribute name with any value
  variants?(array, List of product variant objects):
    id: string, Unique identifier for the variant
    name: string, Name of the variant
    price: number, Price of the variant
```

## Basic Types

Picoschema supports the following scalar types:

| Type | Syntax | Description | Example |
|------|--------|-------------|---------|
| `string` | `fieldName: string[, description]` | String value | `title: string` |
| `number` | `fieldName: number[, description]` | Numeric value (int/float) | `price: number` |
| `integer` | `fieldName: integer[, description]` | Integer value | `age: integer` |
| `boolean` | `fieldName: boolean[, description]` | Boolean value | `isActive: boolean` |
| `null` | `fieldName: null[, description]` | Null value | `emptyField: null` |
| `any` | `fieldName: any[, description]` | Any type | `data: any` |

## Optional Fields

* **Syntax:** Add `?` after the field name
* **Description:** Marks a field as optional. Optional fields are also automatically nullable.
* **Example:** `subtitle?: string`

## Field Descriptions

* **Syntax:** Add a comma followed by the description after the type
* **Description:** Provides additional information about the field
* **Example:** `date: string, the date of publication e.g. '2024-04-09'`

## Arrays

* **Syntax:** `fieldName(array[, description]): elementType`
* **Description:** Defines an array of a specific type
* **Example:** `tags(array, string list of tags): string`

## Objects

* **Syntax:** `fieldName(object[, description]):`
* **Description:** Defines a nested object structure
* **Example:**

```yaml
address(object, the address of the recipient):
  address1: string, street address
  address2?: string, optional apartment/unit number etc.
  city: string
  state: string
```

## Enums

* **Syntax:** `fieldName(enum[, description]): [VALUE1, VALUE2, ...]`
* **Description:** Defines a field with a fixed set of possible values
* **Example:** `status(enum): [PENDING, APPROVED, REJECTED]`

## Wildcard Fields

* **Syntax:** `(*): type[, description]`
* **Description:** Allows additional properties of a specified type in an object
* **Example:** `(*): string`

## Additional Notes

1. By default, all fields are required unless marked as optional with `?`.
2. Objects defined using Picoschema do not allow additional properties unless a wildcard `(*)` is added.
3. Optional fields are automatically made nullable in the resulting JSON Schema.
4. The `any` type results in an empty schema `{}` in JSON Schema, allowing any value.

## Eject to JSON Schema

Picoschema automatically detects if a schema is already in JSON Schema format.
If the top-level schema contains a `type` property with values like "object",
"array", or any of the scalar types, it's treated as JSON Schema.

You can also explicitly use JSON Schema by defining `{"type": "object"}` at the
top level. For example:

```handlebars
---
output:
  schema:
    type: object # this is now JSON Schema
    properties:
      field1: {type: string, description: A sample field}
---
```

## Error Handling

Picoschema will throw errors in the following cases:

* If an unsupported scalar type is used
* If the schema contains values that are neither objects nor strings
* If parenthetical types other than 'object' or 'array' are used (except for 'enum')

These error checks ensure that the Picoschema is well-formed and can be
correctly translated to JSON Schema.
