## Plan for Java `dotprompt` Implementation

The Java implementation can mirror the structure and functionality of the TypeScript version. Here's a phased approach:

**Phase 1: Core Parsing and Rendering Foundation**

1.  **Project Setup**:
    *   Establish the Java project structure within your Bazel workspace (e.g., `java/src/main/java/com/google/dotprompt`).
    *   Create an initial `java/BUILD.bazel` file.
2.  **Type Definitions (`types.java` or similar package)**:
    *   Translate TypeScript interfaces from `js/src/types.ts` into Java records, classes, or interfaces.
    *   Utilize Guava's immutable collections (e.g., `ImmutableList`, `ImmutableMap`) where appropriate for data integrity.
3.  **Parsing Logic (`ParseUtil.java` or `parser` package)**:
    *   Implement `parseDocument`:
        *   Use a YAML library (SnakeYAML is often bundled with Handlebars.java, or you can add it explicitly) to parse frontmatter.
        *   Replicate the logic from `js/src/parse.ts` for `extractFrontmatterAndBody`, handling reserved keywords and extension fields (`ext`).
    *   Implement `toMessages`:
        *   Adapt the marker-based string splitting logic (e.g., `splitByRoleAndHistoryMarkers`).
        *   Convert text pieces into `Message` and `Part` objects.
        *   Implement history insertion logic (`insertHistory`, `messagesHaveHistory`).
4.  **Handlebars Integration**:
    *   Integrate `com.github.jknack:handlebars` for template rendering.
    *   Create Java equivalents of the built-in Handlebars helpers found in `js/src/helpers.ts` (e.g., `JsonHelper`, `RoleHelper`, `HistoryHelper`, `MediaHelper`, `SectionHelper`, `IfEqualsHelper`, `UnlessEqualsHelper`).
5.  **`Dotprompt.java` Class (Core Functionality)**:
    *   Develop the main `Dotprompt` class.
    *   The constructor should initialize the Handlebars engine and register built-in and custom helpers/partials.
    *   Implement `parse(String source)`: Calls the Java equivalent of `parseDocument`.
    *   Implement `compile(String source)`:
        *   Parses the source.
        *   Resolves partials (initially, this can be synchronous or map-based).
        *   Compiles the Handlebars template.
        *   Returns a `PromptFunction` (which can be a Java functional interface).
    *   Implement `render(String source, DataArgument data, PromptMetadata options)`: Calls `compile` and then the resulting function.
    *   Initially, focus on synchronous operations for resolvers.

**Phase 2: Advanced Metadata, Schemas, and Tools**

1.  **PicoSchema Parser (`Picoschema.java` or `schema` package)**:
    *   Implement the logic to parse the Picoschema format and convert it into JSON Schema objects. This will involve handling types, optional fields, descriptions, arrays, objects, enums, and wildcards.
    *   Integrate `SchemaResolver` functionality.
2.  **`Dotprompt.java` Enhancements**:
    *   Implement `renderMetadata`.
    *   Implement internal methods for `resolveMetadata`, `resolveTools`, and `renderPicoschema` (which will use your `Picoschema.java` implementation).
    *   Add methods `defineTool(ToolDefinition def)`, `defineHelper(...)`, `definePartial(...)`.
    *   Incorporate `toolResolver`, `schemaResolver`, and `partialResolver` into the metadata and compilation flows.

**Phase 3: Asynchronous Operations with Dagger Producers & DI**

1.  **Dagger Setup**:
    *   Integrate Dagger for dependency injection. Define modules and components for `Dotprompt`, its configuration, the Handlebars engine, and various resolvers.
2.  **Dagger Producers for Asynchronous Resolvers**:
    *   Refactor `partialResolver`, `schemaResolver`, and `toolResolver` to support asynchronous operations (e.g., returning `ListenableFuture` from Guava or `CompletableFuture`). This is crucial if these resolvers need to fetch data from external sources (network, filesystem I/O).
    *   Use Dagger Producers (`@ProducerModule`, `@Produces`) to manage these asynchronous dependencies within the `compile` and `renderMetadata` methods.
    *   Methods like `compile` might become `compileAsync` returning a future.
3.  **Logging with Flogger**:
    *   Integrate Google Flogger for structured logging throughout the library, especially for parsing issues, resolver activity, and rendering steps.

**Phase 4: Prompt Storage and LLM Adapters**

1.  **PromptStore Implementation (`stores/DirectoryPromptStore.java`)**:
    *   Create a Java version of the `DirStore` from `js/src/stores/dir.ts` for filesystem-based prompt and partial management.
    *   This includes file I/O, directory scanning, and content-based versioning (e.g., using SHA1 hashes).
2.  **LLM Adapters (`adapters/GeminiAdapter.java`, `adapters/OpenAIAdapter.java`, etc.)**:
    *   Translate the TypeScript adapters. These classes will take a `RenderedPrompt` object and convert it into the specific request format required by different LLM providers.

**Phase 5: Testing, Error Handling, and Polish**

1.  **Unit and Integration Testing**:
    *   Write comprehensive tests using Google Truth for all components: parsing, rendering, schema conversion, helpers, metadata processing, store operations, and adapters.
    *   Ensure edge cases and error conditions are well-covered.
2.  **Error Prone Integration**:
    *   Configure Error Prone as a `java_plugin` in your Bazel `java_library` and `java_test` rules to catch common Java pitfalls during compilation.
3.  **Code Style and Reviews**:
    *   Adhere to the Google Java Style Guide.
    *   Conduct thorough code reviews.
    *   Refactor for clarity, performance, and maintainability.

## Publishing to Maven Central

**I. Prerequisites & Setup**

1.  **Sonatype OSSRH Account**:
    *   Register for an account at oss.sonatype.org.
    *   Request publishing permissions for your chosen `groupId` (e.g., `com.google.dotprompt`) via a JIRA ticket with Sonatype.
2.  **GPG Key**:
    *   Generate a GPG key pair.
    *   Distribute your public GPG key to a public key server (e.g., `keys.openpgp.org`, `keyserver.ubuntu.com`).
3.  **Project Information (for `pom.xml`)**:
    *   `groupId`: e.g., `com.google.dotprompt`
    *   `artifactId`: e.g., `dotprompt-java`
    *   `version`: e.g., `0.1.0`
    *   `name`: Human-readable project name.
    *   `description`: Short project description.
    *   `url`: Project website/repository URL.
    *   `licenses`: License information (e.g., Apache-2.0).
    *   `scm`: Source Control Management details.
    *   `developers`: Developer information.

**II. Bazel Configuration for Artifact Generation**

1.  **Add `rules_jvm_publish`**:
    *   Update `java.MODULE.bazel` to include `bazel_dep(name = "rules_jvm_publish", version = "0.30.0")` (or latest).
    *   Run `bazel sync` or equivalent.

2.  **Define your `java_library`**:
    *   Ensure your main library code is built using a `java_library` rule in the appropriate `BUILD.bazel` file.

3.  **Configure Publishing with `java_maven_publish`**:
    *   In the same `BUILD.bazel` file as your `java_library`, add a `java_maven_publish` target:
        ```starlark
        load("@rules_jvm_publish//java:defs.bzl", "java_maven_publish")

        java_maven_publish(
            name = "dotprompt_publish",
            target = ":dotprompt_lib",  # Points to your java_library
            group_id = "com.google.dotprompt", # Your groupId
            artifact_id = "dotprompt-java",    # Your artifactId
            version = "0.1.0-SNAPSHOT",        # Or release version
            # pom_template = ":pom_template.xml", # For comprehensive POM details
            include_javadoc = True,
            include_sources = True,
            # gpg_sign = True, # Enable GPG signing
            # gpg_key_name = "YOUR_GPG_KEY_ID",
        )
        ```
    *   Create a `pom_template.xml` for detailed POM metadata (licenses, SCM, developers).

**III. Building the Artifacts**

1.  Build the publishing target:
    ```bash
    bazel build //path/to/your/java/library:dotprompt_publish
    ```
2.  Artifacts (JAR, sources JAR, Javadoc JAR, POM) will be in `bazel-bin/path/to/your/java/library/dotprompt_publish_files/`.

**IV. Signing the Artifacts**

1.  **Using `rules_jvm_publish`**:
    *   If `gpg_sign = True` is set, artifacts should be signed automatically. Ensure GPG is configured.
2.  **Manual Signing** (if needed):
    *   Navigate to the artifact directory.
    *   For each file (`.jar`, `-sources.jar`, `-javadoc.jar`, `.pom`), create a detached signature:
        ```bash
        gpg --detach-sign --armor your-artifact-name-version.jar
        ```
    *   This creates corresponding `.asc` files.

**V. Deploying to OSSRH Staging**

1.  **Configure Maven `settings.xml`**:
    *   Add OSSRH server credentials and GPG passphrase to `~/.m2/settings.xml`.
        ```xml
        <settings>
          <servers>
            <server>
              <id>ossrh</id>
              <username>YOUR_OSSRH_USERNAME</username>
              <password>YOUR_OSSRH_PASSWORD_OR_TOKEN</password>
            </server>
          </servers>
          <profiles>
            <profile>
              <id>ossrh</id>
              <activation><activeByDefault>true</activeByDefault></activation>
              <properties>
                <gpg.executable>gpg</gpg.executable>
                <gpg.passphrase>YOUR_GPG_PASSPHRASE</gpg.passphrase>
              </properties>
            </profile>
          </profiles>
        </settings>
        ```
2.  **Publish using `rules_jvm_publish`**:
    *   Run the publish target (command may vary based on `rules_jvm_publish` version):
        ```bash
        bazel run //path/to/your/java/library:dotprompt_publish.publish -- \
            --repository_url=https://oss.sonatype.org/service/local/staging/deploy/maven2/ \
            --maven_server_id=ossrh
        ```

**VI. Releasing from OSSRH to Maven Central**

1.  Log in to https://oss.sonatype.org/.
2.  Go to "Staging Repositories".
3.  Find your staging repository (e.g., `comgoogle-xxxx`).
4.  Select it and click "Close". This triggers validations.
5.  If "Close" is successful (no errors in activity log), select it again and click "Release".
6.  Artifacts will sync to Maven Central (can take minutes to hours).
