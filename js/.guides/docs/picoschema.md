---
title: Using Picoschema
description: Read this for Dotprompt's Picoschema YAML schema reference, useful for complex input/output schema help.
---

Picoschema is a compact, YAML-optimized schema definition format specifically designed to aid in describing structured data for better understanding by GenAI models. Whenever a schema is accepted by Dotprompt in its Frontmatter, the Picoschema format is accepted.

Picoschema compiles to JSON Schema and is a subset of JSON Schema capabilities.

## Full Example

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

## Picoschema Reference

### Basic Types

Picoschema supports the following scalar types:

#### **string**
- **Syntax:** `fieldName: string[, optional description]`
- **Description:** Represents a string value.
- **Example:** `title: string`

#### **number**
- **Syntax:** `fieldName: number[, optional description]`
- **Description:** Represents a numeric value (integer or float).
- **Example:** `price: number`

#### **integer**
- **Syntax:** `fieldName: integer[, optional description]`
- **Description:** Represents an integer value.
- **Example:** `age: integer`

#### **boolean**
- **Syntax:** `fieldName: boolean[, optional description]`
- **Description:** Represents a boolean value.
- **Example:** `isActive: boolean`

#### **null**
- **Syntax:** `fieldName: null[, optional description]`
- **Description:** Represents a null value.
- **Example:** `emptyField: null`

#### **any**
- **Syntax:** `fieldName: any[, optional description]`
- **Description:** Represents a value of any type.
- **Example:** `data: any`

### Optional Fields

- **Syntax:** Add `?` after the field name.
- **Description:** Marks a field as optional. Optional fields are also automatically nullable.
- **Example:** `subtitle?: string`

### Field Descriptions

- **Syntax:** Add a comma followed by the description after the type.
- **Description:** Provides additional information about the field.
- **Example:** `date: string, the date of publication e.g. '2024-04-09'`

### Arrays

- **Syntax:** `fieldName(array[, optional description]): elementType`
- **Description:** Defines an array of a specific type.
- **Example:** `tags(array, string list of tags): string`

### Objects

- **Syntax:** `fieldName(object[, optional description]):`
- **Description:** Defines a nested object structure.
- **Example:**
  ```yaml
  address(object, the address of the recipient):
    address1: string, street address
    address2?: string, optional apartment/unit number etc.
    city: string
    state: string
  ```

### Enums

- **Syntax:** `fieldName(enum[, optional description]): [VALUE1, VALUE2, ...]`
- **Description:** Defines a field with a fixed set of possible values.
- **Example:** `status(enum): [PENDING, APPROVED, REJECTED]`

### Wildcard Fields

- **Syntax:** `(*): type[, optional description]`
- **Description:** Allows additional properties of a specified type in an object.
- **Example:** `(*): string`

### Additional Notes

1. By default, all fields are required unless marked as optional with `?`.
2. Objects defined using Picoschema do not allow additional properties unless a wildcard `(*)` is added.
3. Optional fields are automatically made nullable in the resulting JSON Schema.
4. The `any` type results in an empty schema `{}` in JSON Schema, allowing any value.

## Eject to JSON Schema

Picoschema automatically detects if a schema is already in JSON Schema format. If the top-level schema contains a `type` property with values like "object", "array", or any of the scalar types, it's treated as JSON Schema.

You can also explicitly use JSON Schema by defining `{"type": "object"}` at the top level. For example:

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
1. If an unsupported scalar type is used.
2. If the schema contains values that are neither objects nor strings.
3. If parenthetical types other than 'object' or 'array' are used (except for 'enum').

These error checks ensure that the Picoschema is well-formed and can be correctly translated to JSON Schema.