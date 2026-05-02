# Dart/JS Feature Parity Audit

This document tracks feature parity between the Dart and JavaScript (canonical) Dotprompt implementations.

**Last Updated:** 2026-05-01

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
| `MetadataPart` | ✅ | ✅ | `metadata: object` |

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
| Empty frontmatter | ✅ | ✅ | |
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
| Array types (`type[]` suffix) | ✅ | ✅ | |
| Enum types | ✅ | ✅ | |
| Named schema references | ✅ | ✅ | |
| Async schema resolution | ✅ | ✅ | |

## Templating Engine

| Feature | JS | Dart | Notes |
|---------|----|----|-------|
| Handlebars-style syntax | ✅ | ✅ | Dart uses custom `handlebars_dart` library |
| Variable substitution | ✅ | ✅ | `{{name}}` |
| Dot notation access | ✅ | ✅ | `{{user.name}}` |
| Block helpers | ✅ | ✅ | `{{#if}}...{{/if}}` |
| Partial templates | ✅ | ✅ | `{{> partialName}}` |
| Recursive partial resolution | ✅ | ✅ | |
| Unescaped output | ✅ | ✅ | `{{{raw}}}` |
| Comments | ✅ | ✅ | `{{! comment }}` |
| Helper arguments | ✅ | ✅ | `{{role "system"}}` |

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

## Spec Conformance

| Test Suite | Tests | Status | Notes |
|------------|-------|--------|-------|
| `metadata.yaml` | ✅ | All pass | |
| `variables.yaml` | ✅ | All pass | |
| `partials.yaml` | ✅ | All pass | |
| `picoschema.yaml` | ✅ | All pass | |
| `unicode.yaml` | ✅ | All pass | |
| `helpers/` | ✅ | All pass | |
| **Total** | **117/117** | **✅ All pass** | |

## Platform-Specific Differences

| Aspect | JS | Dart | Notes |
|--------|----|----|-------|
| Template engine | Handlebars.js | `handlebars_dart` | Custom pure-Dart Handlebars implementation |
| Async model | Promises | Futures | Native async for both |
| Type system | TypeScript interfaces | Dart classes + sealed | Dart has stronger types |
| Part types | Union types | Sealed class | Dart 3 pattern matching |
| JSON serialization | Manual | `toJson()`/`fromJson()` | Dart has consistent pattern |
| Immutability | Partial | Full (`@immutable`) | Dart enforces immutability |

## Known Gaps (TODO)

| Feature | Priority | JS Has | Dart Has | Notes |
|---------|----------|--------|----------|-------|
| `validatePromptName()` security util | High | ✅ | ✅ | Path traversal prevention (CWE-22) |
| `DirStore` implementation | Medium | ✅ | ❌ | Filesystem-based store |
| `removeUndefinedFields()` util | Low | ✅ | ➖ | Dart handles nulls differently |
| `PromptStoreWritable` interface | Low | ❌ | ✅ | Dart adds write operations |

## Summary

**Parity Status: ~95% — Full spec conformance achieved (117/117 tests pass)**

The Dart implementation has comprehensive feature parity with the JavaScript canonical
implementation. The custom `handlebars_dart` library provides full Handlebars support
including helper arguments, block helpers, and partial templates.

### ✅ Complete Features:
1. **API Surface**: All public methods match (parse, compile, render, defineHelper, definePartial, defineTool)
2. **Data Types**: All types implemented with proper Dart idioms (sealed classes, immutability)
3. **Parsing**: Full frontmatter and template parsing
4. **Picoschema**: Full conversion support
5. **Templating**: Full Handlebars support via custom `handlebars_dart` library
6. **Built-in Helpers**: All helpers work (role, history, section, media, json, ifEquals, unlessEquals)
7. **Spec Conformance**: 117/117 spec tests pass

### 🛠️ Remaining Work
- Implement `DirStore` for filesystem-based prompt loading

Minor differences like sealed classes vs union types are intentional platform adaptations.
