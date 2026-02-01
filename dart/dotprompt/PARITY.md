# Dart/JS Feature Parity Audit

This document tracks feature parity between the Dart and JavaScript (canonical) Dotprompt implementations.

**Last Updated:** 2026-01-30

**Legend:**
- ✅ Implemented and tested
- 🟡 Partial implementation
- ❌ Not implemented
- ➖ Not applicable

## Core API Surface

### Dotprompt Class

| Feature | JS | Dart | Notes |
|---------|----|----|-------|
| `constructor(options?)` | ✅ | ✅ | `DotpromptOptions` |
| `parse(source)` | ✅ | ✅ | Returns `ParsedPrompt` |
| `compile(source)` | ✅ | ✅ | Returns `PromptFunction` |
| `render(source, data, options?)` | ✅ | ✅ | Returns `RenderedPrompt` |
| `renderMetadata(source, options?)` | ✅ | ✅ | Returns resolved metadata |
| `defineHelper(name, fn)` | ✅ | ✅ | Register custom helper |
| `definePartial(name, source)` | ✅ | ✅ | Register partial template |
| `defineTool(definition)` | ✅ | ✅ | Register tool definition |
| `defineSchema(name, schema)` | ➖ | ✅ | Dart adds explicit schema registration |

### DotpromptOptions

| Option | JS | Dart | Notes |
|--------|----|----|-------|
| `defaultModel` | ✅ | ✅ | Default model name |
| `modelConfigs` | ✅ | ✅ | Per-model configuration |
| `helpers` | ✅ | ✅ | Pre-registered helpers |
| `partials` | ✅ | ✅ | Pre-registered partials |
| `tools` | ✅ | ✅ | Tool definitions map |
| `toolResolver` | ✅ | ✅ | Async tool resolution |
| `schemas` | ✅ | ✅ | Schema definitions map |
| `schemaResolver` | ✅ | ✅ | Async schema resolution |
| `partialResolver` | ✅ | ✅ | Async partial resolution |
| `store` | ✅ | ✅ | PromptStore for loading |

## Data Types

### Core Types

| Type | JS | Dart | Notes |
|------|----|----|-------|
| `ParsedPrompt` | ✅ | ✅ | Template + metadata |
| `RenderedPrompt` | ✅ | ✅ | Config + messages |
| `PromptFunction` | ✅ | ✅ | Compiled render function |
| `PromptMetadata` | ✅ | ✅ | Prompt configuration |
| `DataArgument` | ✅ | ✅ | Render input data |

### Message Types

| Type | JS | Dart | Notes |
|------|----|----|-------|
| `Message` | ✅ | ✅ | Role + content parts |
| `Role` | ✅ | ✅ | user/model/system/tool |
| `Document` | ✅ | ✅ | RAG document |
| `ContextData` | ✅ | ✅ | @ variable context |

### Part Types

| Type | JS | Dart | Notes |
|------|----|----|-------|
| `Part` (base) | ✅ | ✅ | Dart uses sealed class |
| `TextPart` | ✅ | ✅ | `text: string` |
| `MediaPart` | ✅ | ✅ | `media: MediaContent` |
| `DataPart` | ✅ | ✅ | `data: object` |
| `ToolRequestPart` | ✅ | ✅ | `toolRequest: ToolRequest` |
| `ToolResponsePart` | ✅ | ✅ | `toolResponse: ToolResponse` |
| `PendingPart` | ✅ | ✅ | `pending: true` |

### Tool Types

| Type | JS | Dart | Notes |
|------|----|----|-------|
| `ToolDefinition` | ✅ | ✅ | name, description, inputSchema, outputSchema |
| `ToolRequest` | ✅ | ✅ | name, ref, input |
| `ToolResponse` | ✅ | ✅ | name, ref, output |

### Resolver Types

| Type | JS | Dart | Notes |
|------|----|----|-------|
| `PartialResolver` | ✅ | ✅ | `(name) => string?` |
| `ToolResolver` | ✅ | ✅ | `(name) => ToolDefinition?` |
| `SchemaResolver` | ✅ | ✅ | `(name) => JSONSchema?` |

## Built-in Helpers

| Helper | JS | Dart | Notes |
|--------|----|----|-------|
| `json` | ✅ | ✅ | `{{json data indent=2}}` |
| `role` | ✅ | ✅ | `{{role "system"}}` |
| `history` | ✅ | ✅ | `{{history}}` |
| `section` | ✅ | ✅ | `{{section "code"}}` |
| `media` | ✅ | ✅ | `{{media url="..." contentType="..."}}` |
| `ifEquals` | ✅ | ✅ | `{{#ifEquals a b}}...{{/ifEquals}}` |
| `unlessEquals` | ✅ | ✅ | `{{#unlessEquals a b}}...{{/unlessEquals}}` |

## Parsing Features

| Feature | JS | Dart | Notes |
|---------|----|----|-------|
| YAML frontmatter extraction | ✅ | ✅ | |
| Template body extraction | ✅ | ✅ | |
| Namespaced metadata (`ext.namespace.key`) | ✅ | ✅ | |
| Reserved keywords handling | ✅ | ✅ | |
| Empty frontmatter | ✅ | ✅ | Fixed in Dart |
| Multi-message parsing | ✅ | ✅ | Role markers |
| History insertion | ✅ | ✅ | |
| Media markers | ✅ | ✅ | |
| Section markers | ✅ | ✅ | |

## Picoschema

| Feature | JS | Dart | Notes |
|---------|----|----|-------|
| Type scalars (string, integer, etc.) | ✅ | ✅ | |
| Optional fields (`?` suffix) | ✅ | ✅ | |
| Descriptions (`, description`) | ✅ | ✅ | |
| Nested objects | ✅ | ✅ | |
| Array types (`(*)` suffix) | ✅ | ✅ | |
| Enum types | ✅ | ✅ | |
| Named schema references | ✅ | ✅ | |
| Async schema resolution | ✅ | ✅ | |

## Templating Engine

| Feature | JS | Dart | Notes |
|---------|----|----|-------|
| Handlebars-style syntax | ✅ | 🟡 | Dart uses mustache_template (see note below) |
| Variable substitution | ✅ | ✅ | `{{name}}` |
| Dot notation access | ✅ | ✅ | `{{user.name}}` |
| Block helpers | ✅ | 🟡 | `{{#if}}...{{/if}}` - native only |
| Partial templates | ✅ | ✅ | `{{> partialName}}` |
| Recursive partial resolution | ✅ | ✅ | Cycle detection |
| Unescaped output | ✅ | ✅ | `{{{raw}}}` |
| Comments | ✅ | ✅ | `{{! comment }}` |
| **Helper arguments** | ✅ | ❌ | `{{role "system"}}` - **CRITICAL GAP** |

### ⚠️ Critical Templating Limitation

The Dart implementation uses `mustache_template` which does **NOT** support Handlebars-style
helper arguments like `{{role "system"}}` or `{{media url="..." contentType="..."}}`.

Mustache only allows tag names with `a-z`, `A-Z`, `-`, `_`, and `.`. Spaces and quoted
strings cause parse errors.

**Options to resolve:**
1. **Pre-process helpers**: Expand `{{role "system"}}` before Mustache parsing
2. **Switch template library**: Use `handlebars` or `jinja_template` package
3. **Use lenient mode**: Check if `mustache_template` has a lenient parser option

## Store Interface

| Feature | JS | Dart | Notes |
|---------|----|----|-------|
| `PromptStore` interface | ✅ | ✅ | |
| `load(name, options)` | ✅ | ✅ | Load prompt by name |
| `loadPartial(name, options)` | ✅ | ✅ | Load partial by name |
| `list()` | ✅ | ✅ | List all prompts |
| `listPartials()` | ✅ | ✅ | List all partials |

## Error Handling

| Exception/Error | JS | Dart | Notes |
|-----------------|----|----|-------|
| Parse errors | ✅ | ✅ | `ParseException` |
| Render errors | ✅ | ✅ | `RenderException` |
| Tool resolution errors | ✅ | ✅ | `ToolResolutionException` |
| Partial resolution errors | ✅ | ✅ | `PartialResolutionException` |
| Schema validation errors | ✅ | ✅ | `SchemaValidationException` |
| Picoschema errors | ✅ | ✅ | `PicoschemaException` |

## Metadata Fields

| Field | JS | Dart | Notes |
|-------|----|----|-------|
| `name` | ✅ | ✅ | Prompt name |
| `variant` | ✅ | ✅ | Prompt variant |
| `version` | ✅ | ✅ | Prompt version |
| `description` | ✅ | ✅ | Prompt description |
| `model` | ✅ | ✅ | Model to use |
| `config` | ✅ | ✅ | Model configuration |
| `input.schema` | ✅ | ✅ | Input schema (Picoschema) |
| `input.default` | ✅ | ✅ | Default input values |
| `output.schema` | ✅ | ✅ | Output schema (Picoschema) |
| `output.format` | ✅ | ✅ | Output format (json/text) |
| `tools` | ✅ | ✅ | Tool names array |
| `toolDefs` | ✅ | ✅ | Resolved tool definitions |
| `ext` | ✅ | ✅ | Extension metadata |
| `raw` | ✅ | ✅ | Raw frontmatter data |

## Platform-Specific Differences

| Aspect | JS | Dart | Notes |
|--------|----|----|-------|
| Template engine | Handlebars | mustache_template | Behavioral parity maintained |
| Async model | Promises | Futures | Native async for both |
| Type system | TypeScript interfaces | Dart classes + sealed | Dart has stronger types |
| Part types | Union types | Sealed class | Dart 3 pattern matching |
| JSON serialization | Manual | `toJson()`/`fromJson()` | Dart has consistent pattern |
| Immutability | Partial | Full (`@immutable`) | Dart enforces immutability |

## Known Gaps (TODO)

| Feature | Priority | JS Has | Dart Has | Notes |
|---------|----------|--------|----------|-------|
| `validatePromptName()` security util | High | ✅ | ❌ | Path traversal prevention (CWE-22) |
| `DirStore` implementation | Medium | ✅ | ❌ | Filesystem-based store |
| `removeUndefinedFields()` util | Low | ✅ | ➖ | Dart handles nulls differently |
| `PromptStoreWritable` interface | Low | ❌ | ✅ | Dart adds write operations |

### Security: `validatePromptName` (MUST IMPLEMENT)

The JS implementation includes comprehensive prompt name validation to prevent:
- Path traversal attacks (CWE-22): `../../etc/passwd`
- Null byte injection (CWE-134): `file\x00.txt`
- UNC path attacks: `\\server\share`
- Unicode homograph attacks: visually similar characters
- URL-encoded bypass attempts: `%2e%2e/`

**Action Required:** Port `validatePromptName()` from `js/src/util.ts` to Dart before any filesystem operations.

## Test Coverage

| Test Suite | JS | Dart | Notes |
|------------|----|----|-------|
| Dotprompt class tests | ✅ | ✅ | |
| Parse tests | ✅ | ✅ | |
| Picoschema tests | ✅ | ✅ | |
| Helper tests | ✅ | ✅ | |
| Types tests | ✅ | ✅ | Dart has JSON serialization tests |
| Spec conformance tests | ✅ | 🟡 | Dart spec runner exists but needs integration |

## Summary

**Parity Status: ~75% (BLOCKED by template engine limitation)**

The Dart implementation has substantial feature parity with the JavaScript canonical
implementation, but is **blocked** by a critical template engine limitation.

### ✅ Complete Features (works today):
1. **API Surface**: All public methods match (parse, compile, render, defineHelper, definePartial, defineTool)
2. **Data Types**: All types implemented with proper Dart idioms (sealed classes, immutability)
3. **Parsing**: Full frontmatter and template parsing
4. **Picoschema**: Full conversion support
5. **Simple Variable Substitution**: `{{name}}`, `{{user.email}}` work

### ⚠️ Blocked Features (need template engine fix):
1. **Built-in Helpers**: `{{role "..."}}`, `{{media url="..."}}` etc. fail to parse
2. **Block Helpers with Args**: `{{#ifEquals a b}}...{{/ifEquals}}` fail to parse
3. **Spec Conformance Tests**: 11/16 tests fail due to helper syntax

### 🛠️ Required Work
To achieve full parity, the Dart implementation needs one of:
1. Pre-process template to expand helpers before Mustache parsing
2. Switch to a Handlebars-compatible Dart template library
3. Implement custom template parser with Handlebars support

Minor differences like sealed classes vs union types are intentional platform adaptations.
