# Deploying Java Dotprompt

This document describes the process for releasing the `dotprompt` Java library to Maven Central.

## Prerequisites

1.  **GPG Keys**: You need a GPG key pair to sign artifacts.
    *   Export the private key: `gpg --armor --export-secret-keys <ID>`
    *   Note the passphrase.

2.  **Sonatype OSSRH Account**: You need an account on [s01.oss.sonatype.org](https://s01.oss.sonatype.org/) (or the legacy server) with access to the `com.google.dotprompt` group ID.

## GitHub Configuration

Configure the following secrets in the GitHub repository settings:

*   `OSSRH_USERNAME`: Your Sonatype username.
*   `OSSRH_TOKEN`: Your Sonatype password or user token.
*   `MAVEN_GPG_PRIVATE_KEY`: The ASCII-armored GPG private key.
*   `MAVEN_GPG_PASSPHRASE`: The passphrase for your GPG key.

## Release Process

The release process is automated via GitHub Actions (`.github/workflows/publish_java.yml`).

1.  **Create a Release**:
    *   Go to the "Releases" section on GitHub.
    *   Draft a new release.
    *   Create a new tag (e.g., `v0.1.0`).
    *   Publish the release.

2.  **Automation**:
    *   The `Publish Java Package` workflow will trigger automatically.
    *   It sets up the JDK and Bazel environment.
    *   It imports the GPG key.
    *   It runs `scripts/publish-java.sh`, which invokes `bazel run //java/com/google/dotprompt:dotprompt_pkg.publish`.

3.  **Verification**:
    *   Check the workflow run logs for success.
    *   Log in to Sonatype OSSRH to verify the staging repository if auto-release is not enabled, or check Maven Central (after a sync delay) if it is.

## Local Testing (Dry Run)

To verifying the build artifacts locally without publishing:

```bash
bazel build //java/com/google/dotprompt:dotprompt_pkg
```

This ensures the POM and JARs are correctly generated.
