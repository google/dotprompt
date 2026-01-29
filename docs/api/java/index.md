# Java API

The `com.google.dotprompt` package is the Java implementation of the Dotprompt
file format.

## Installation

\=== "Maven"
`xml     <dependency>       <groupId>com.google.dotprompt</groupId>       <artifactId>dotprompt</artifactId>       <version>0.1.0</version>     </dependency>
    `

\=== "Gradle (Kotlin)"
`kotlin
    implementation("com.google.dotprompt:dotprompt:0.1.0")
    `

\=== "Gradle (Groovy)"
`groovy
    implementation 'com.google.dotprompt:dotprompt:0.1.0'
    `

## Quick Start

```java
import com.google.dotprompt.Dotprompt;
import com.google.dotprompt.DotpromptOptions;
import com.google.dotprompt.models.DataArgument;
import com.google.dotprompt.models.RenderedPrompt;

import java.util.Map;

public class Example {
    public static void main(String[] args) {
        String source = """
            ---
            model: gemini-pro
            input:
              schema:
                name: string
            ---
            Hello, {{name}}!
            """;

        Dotprompt dotprompt = new Dotprompt();

        DataArgument data = DataArgument.builder()
            .input(Map.of("name", "World"))
            .build();

        RenderedPrompt rendered = dotprompt.render(source, data, null);

        rendered.getMessages().forEach(message -> {
            System.out.printf("%s: %s%n", message.getRole(), message.getContent());
        });
    }
}
```

## Core Classes

### Dotprompt

The main entry point for working with Dotprompt templates.

```java
public class Dotprompt {
    // Constructors
    public Dotprompt();
    public Dotprompt(DotpromptOptions options);

    // Parsing
    public ParsedPrompt parse(String source);

    // Compilation
    public PromptFunction compile(String source);
    public PromptFunction compile(String source, PromptMetadata additionalMetadata);

    // Rendering
    public RenderedPrompt render(String source, DataArgument data);
    public RenderedPrompt render(String source, DataArgument data, PromptMetadata options);

    // Registration
    public Dotprompt defineHelper(String name, HelperFn fn);
    public Dotprompt definePartial(String name, String source);
    public Dotprompt defineTool(ToolDefinition definition);
}
```

### DotpromptOptions

Builder for configuring a Dotprompt instance.

```java
DotpromptOptions options = DotpromptOptions.builder()
    .defaultModel("gemini-pro")
    .modelConfigs(Map.of(
        "gemini-pro", Map.of("temperature", 0.7)
    ))
    .helpers(Map.of(
        "uppercase", (params, options) -> params.get(0).toString().toUpperCase()
    ))
    .partials(Map.of(
        "header", "Welcome to {{appName}}!"
    ))
    .build();

Dotprompt dotprompt = new Dotprompt(options);
```

## Models

### ParsedPrompt

Result of parsing a Dotprompt template.

```java
public class ParsedPrompt {
    public String getTemplate();
    public String getName();
    public String getDescription();
    public String getVariant();
    public String getVersion();
    public String getModel();
    public Object getConfig();
    public PromptInputConfig getInput();
    public PromptOutputConfig getOutput();
    public List<String> getTools();
    public List<ToolDefinition> getToolDefs();
    public Map<String, Map<String, Object>> getExt();
    public Map<String, Object> getRaw();
}
```

### RenderedPrompt

Result of rendering a Dotprompt template.

```java
public class RenderedPrompt extends PromptMetadata {
    public List<Message> getMessages();
}
```

### Message

A single message in a conversation.

```java
public class Message {
    public Role getRole();
    public List<Part> getContent();
    public Map<String, Object> getMetadata();
}

public enum Role {
    USER("user"),
    MODEL("model"),
    TOOL("tool"),
    SYSTEM("system");
}
```

### Part

Content within a message. Part is a sealed interface with several implementations:

```java
public sealed interface Part permits TextPart, MediaPart, DataPart,
    ToolRequestPart, ToolResponsePart, PendingPart {
}

public record TextPart(String text, Map<String, Object> metadata) implements Part {}

public record MediaPart(MediaContent media, Map<String, Object> metadata) implements Part {}

public record MediaContent(String url, String contentType) {}

public record DataPart(Map<String, Object> data, Map<String, Object> metadata) implements Part {}
```

### DataArgument

Runtime data for rendering a template.

```java
public class DataArgument {
    public static Builder builder();

    public Map<String, Object> getInput();
    public List<Document> getDocs();
    public List<Message> getMessages();
    public Map<String, Object> getContext();

    public static class Builder {
        public Builder input(Map<String, Object> input);
        public Builder docs(List<Document> docs);
        public Builder messages(List<Message> messages);
        public Builder context(Map<String, Object> context);
        public DataArgument build();
    }
}
```

### ToolDefinition

```java
public class ToolDefinition {
    public String getName();
    public String getDescription();
    public Object getInputSchema();
    public Object getOutputSchema();

    public static Builder builder();
}
```

## Stores

### DirStore

Load prompts from a filesystem directory (async).

```java
import com.google.dotprompt.store.DirStore;
import com.google.dotprompt.store.DirStoreOptions;

DirStore store = new DirStore(DirStoreOptions.builder()
    .directory("./prompts")
    .build());

CompletableFuture<PromptData> future = store.load("greeting", null);
PromptData prompt = future.join();
```

### DirStoreSync

Synchronous version.

```java
import com.google.dotprompt.store.DirStoreSync;
import com.google.dotprompt.store.DirStoreOptions;

DirStoreSync store = new DirStoreSync(DirStoreOptions.builder()
    .directory("./prompts")
    .build());

PromptData prompt = store.load("greeting", null);
```

## Resolvers

### ToolResolver

```java
@FunctionalInterface
public interface ToolResolver {
    CompletableFuture<ToolDefinition> resolve(String name);
}

// Usage
DotpromptOptions options = DotpromptOptions.builder()
    .toolResolver(name -> CompletableFuture.supplyAsync(() -> {
        // Look up tool definition
        return loadToolFromDatabase(name);
    }))
    .build();
```

### SchemaResolver

```java
@FunctionalInterface
public interface SchemaResolver {
    CompletableFuture<Object> resolve(String name);
}
```

### PartialResolver

```java
@FunctionalInterface
public interface PartialResolver {
    CompletableFuture<String> resolve(String name);
}
```

## Picoschema

Convert Picoschema to JSON Schema.

```java
import com.google.dotprompt.parser.Picoschema;

Map<String, Object> schema = Map.of(
    "name", "string",
    "age?", "integer, The person's age"
);

Object jsonSchema = Picoschema.toJsonSchema(schema, null);
```

## Built-in Helpers

| Helper | Description | Example |
|--------|-------------|---------|
| `role` | Set message role | `{{role "system"}}` |
| `media` | Insert media content | `{{media url="..." contentType="image/png"}}` |
| `history` | Insert message history | `{{history}}` |
| `section` | Create a content section | `{{section "code"}}` |
| `json` | Serialize to JSON | `{{json data indent=2}}` |
| `ifEquals` | Conditional equality | `{{#ifEquals a b}}...{{/ifEquals}}` |
| `unlessEquals` | Conditional inequality | `{{#unlessEquals a b}}...{{/unlessEquals}}` |

## Kotlin Interoperability

The Java library works seamlessly with Kotlin:

```kotlin
import com.google.dotprompt.Dotprompt
import com.google.dotprompt.models.DataArgument

fun main() {
    val source = """
        ---
        model: gemini-pro
        ---
        Hello, {{name}}!
    """.trimIndent()

    val dotprompt = Dotprompt()

    val data = DataArgument.builder()
        .input(mapOf("name" to "World"))
        .build()

    val rendered = dotprompt.render(source, data, null)

    rendered.messages.forEach { message ->
        println("${message.role}: ${message.content}")
    }
}
```

## External Documentation

* [Javadoc](https://javadoc.io/doc/com.google.dotprompt/dotprompt)
* [GitHub source](https://github.com/google/dotprompt/tree/main/java)
