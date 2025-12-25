# Java Dotprompt

This directory contains the Java implementation of the Dotprompt library.

## Usage

Add the following dependency to your project:

**Maven:**
```xml
<dependency>
    <groupId>com.google.dotprompt</groupId>
    <artifactId>dotprompt</artifactId>
    <version>0.1.0</version>
</dependency>
```

**Gradle:**
```groovy
implementation 'com.google.dotprompt:dotprompt:0.1.0'
```

**Bazel:**
```starlark
maven_install(
    artifacts = [
        "com.google.dotprompt:dotprompt:0.1.0",
    ],
    # ...
)
```

## Building

```bash
bazel build //java/com/google/dotprompt:dotprompt
```

## Testing

```bash
bazel test //java/com/google/dotprompt/...
```

---

# Deploying to Maven Central

This section describes the process for releasing the `dotprompt` Java library to Maven Central.

## Prerequisites

1.  **GPG Keys**: You need a GPG key pair to sign artifacts.
    *   Export the private key: `gpg --armor --export-secret-keys <KEY_ID>`
    *   Note the passphrase.

2.  **Sonatype OSSRH Account**: You need an account on [s01.oss.sonatype.org](https://s01.oss.sonatype.org/) with access to the `com.google.dotprompt` group ID.

## GitHub Secrets Configuration

Configure these secrets in the repository settings (Settings → Secrets and variables → Actions):

| Secret Name             | Description                           |
|-------------------------|---------------------------------------|
| `OSSRH_USERNAME`        | Your Sonatype username                |
| `OSSRH_TOKEN`           | Your Sonatype password or user token  |
| `MAVEN_GPG_PRIVATE_KEY` | ASCII-armored GPG private key         |
| `MAVEN_GPG_PASSPHRASE`  | Passphrase for your GPG key           |

## Release Process

Releases are managed by [release-please](https://github.com/googleapis/release-please).

### Automated Flow

1.  **Commit changes** to `main` using conventional commit messages with the `java` scope:
    ```
    feat(java): add new template helper
    fix(java): resolve parsing issue
    ```

2.  **Release-please creates a PR** automatically with:
    *   Updated version in `BUILD.bazel`
    *   Generated `CHANGELOG.md`

3.  **Merge the release PR** when ready.

4.  **Publishing is automated** via `.github/workflows/publish_java.yml`:
    *   Triggers on release creation
    *   Signs and uploads to Maven Central

### Verification

*   Check the GitHub Actions workflow logs for success.
*   Log in to [Sonatype OSSRH](https://s01.oss.sonatype.org/) to verify the staging repository.
*   After sync (typically 10-30 minutes), verify on [Maven Central](https://search.maven.org/search?q=g:com.google.dotprompt).

## Local Testing (Dry Run)

To verify artifacts build correctly without publishing:

```bash
bazel build //java/com/google/dotprompt:dotprompt_pkg
```

To inspect the generated POM:

```bash
bazel build //java/com/google/dotprompt:dotprompt_pkg-pom
cat bazel-bin/java/com/google/dotprompt/dotprompt_pkg-pom.xml
```
