# Java Coding Guidelines

This is for both bots and humans.

Target: Java LTS version (e.g., Java 11, 17, 21) or as specified by the project.

## Style & Idioms

* **Adhere strictly to the [Google Java Style Guide](https://google.github.io/styleguide/javaguide.html).** This is the primary source for all style and formatting rules.
* Use modern Java features appropriately (e.g., Lambdas, Streams, `Optional`, `var` for local variables where it enhances readability - Java 10+).
* Prefer immutability for objects where possible. Use `final` for fields, parameters, and local variables when their values should not change.
* Leverage Java's strong typing system. Use classes, interfaces, enums, and records (Java 14+) effectively to model data and behavior.
* Use interfaces to define contracts and promote loose coupling. Code to interfaces, not implementations.
* Employ clear and concise comments. Use `//` for single-line comments and `/* ... */` for multi-line comments. Javadoc (`/** ... */`) is used for API documentation.
* Ensure proper punctuation and grammar in comments and documentation.
* Avoid comments that merely restate what the code obviously does. Focus on *why* the code is written a certain way if it's non-obvious, or if it has subtle side effects or complex logic.
* Use TODO comments, e.g., `// TODO: Refactor this to improve performance.` or `// TODO(username): Add error handling for specific case X.`, when adding stub implementations or noting future work.
* Organize imports according to the Google Java Style Guide (no wildcard imports, specific ordering).
* Follow standard naming conventions (PascalCase for classes/interfaces/enums/records, camelCase for methods/variables, SCREAMING\_SNAKE\_CASE for constants).

## Documentation Comments (Javadoc)

* Write comprehensive Javadoc comments for all public classes, interfaces, enums, records, methods, and fields.
* Follow Javadoc conventions and the Google Java Style Guide's Javadoc section.
* Use standard Javadoc tags:
  * `@param` for method parameters.
  * `@return` for method return values (omit if `void`).
  * `@throws` or `@exception` for exceptions a method might throw.
  * `@since` to denote when a feature was added.
  * `@see` for references to other related code or documentation.
  * `@deprecated` for features that should no longer be used.
* The first sentence of a Javadoc comment should be a concise summary.
* Provide clear examples for public APIs where appropriate.

## Formatting

* **Format code using a tool that enforces the Google Java Style Guide.** The `google-java-format` tool is the standard.
  * This can be integrated into IDEs or run as a build step (e.g., via Maven or Gradle plugins).
* Line length: 100 characters (as per Google Java Style Guide).
* Refer to the project's `.editorconfig` if present, ensuring it aligns with Google Java Style.

## Modernizing Code

* Keep up-to-date with LTS Java versions and adopt new language features where they improve clarity, conciseness, and performance.
* [ ] Refactor legacy code periodically to incorporate modern best practices and library improvements.
* Analyze code with static analysis tools that can suggest modernizations.

## Testing

* Write comprehensive unit tests using JUnit 5 (Jupiter).
* Use mocking frameworks like Mockito for isolating units under test.
* Test class names should end with `Test` (e.g., `MyClassTest`). Test method names should be descriptive, often using `should_doSomething_when_condition` or similar patterns.
* Use expressive assertions (e.g., AssertJ or Hamcrest, in addition to JUnit's built-in assertions).
* Strive for high test coverage.
* Add Javadoc or comments to test classes and complex test methods explaining their scope and purpose.
* Run tests as part of the build process (e.g., `mvn test` or `gradle test`).
* Fix underlying code issues rather than special-casing test behavior.
* If porting tests: Maintain 1:1 logic parity accurately; do not invent behavior.

## Tooling & Environment

* Use a standard build tool: Maven or Gradle. Define dependencies, plugins, and build lifecycle clearly.
* Use a modern JDK (LTS versions are generally preferred for stability).
* Utilize IDEs like IntelliJ IDEA or Eclipse with appropriate plugins for Google Java Style formatting and other Java development aids.
* Incorporate static analysis tools into the build process:
  * Checkstyle (configured for Google Style).
  * SpotBugs or PMD for finding potential bugs and code smells.
  * SonarQube or SonarLint for comprehensive code quality analysis.

## Concurrency

* Use the `java.util.concurrent` package for high-level concurrency utilities (e.g., ExecutorService, ThreadPoolExecutor, ConcurrentHashMap, CountDownLatch, Semaphore).
* Be mindful of thread safety. Clearly document the thread-safety of classes.
* Synchronize access to shared mutable state correctly using `synchronized` blocks/methods, `ReentrantLock`, or other appropriate mechanisms.
* Avoid deadlocks and race conditions. Use tools and code reviews to help identify potential concurrency issues.
* Prefer higher-level concurrency abstractions over manual thread management (`new Thread()`) where possible.

## Error Handling

* Use exceptions for exceptional conditions. Distinguish between checked exceptions (for recoverable conditions the caller should handle) and unchecked/runtime exceptions (for programming errors or unrecoverable issues).
* Throw specific exceptions. Avoid throwing generic `Exception` or `RuntimeException`.
* Document exceptions thrown by methods using `@throws` in Javadoc.
* Use try-with-resources (Java 7+) for managing resources that implement `AutoCloseable` to prevent resource leaks.
* Use `Optional<T>` (Java 8+) to represent values that might be absent, as an alternative to returning `null` in some cases (especially for public APIs). Handle `Optional` values appropriately.

## Logging

* Use SLF4J (Simple Logging Facade for Java) as a logging API.
* Provide a concrete logging implementation via a binding like Logback (preferred) or Log4j2.
* Use structured logging where appropriate, especially for application logs that will be parsed.
* Log at appropriate levels (TRACE, DEBUG, INFO, WARN, ERROR).
* Do not use `System.out.println()` or `System.err.println()` for application logging; use the logging framework.
* When logging exceptions, include the full stack trace.

## Porting

* If porting from another language, maintain 1:1 logic parity in implementation and tests where sensible.
* Adapt idioms to be Java-specific. This includes object-oriented design, standard library usage, and error handling with exceptions.

## Licensing

Include the following Apache 2.0 license header at the top of each `.java` file, updating the year:

```java
// Copyright 2025 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// SPDX-License-Identifier: Apache-2.0
```
