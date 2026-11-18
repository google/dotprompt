# Making Releases

Releases are manual: each package is versioned and published on its own. Bump
the version and changelog in a PR, merge it, then publish from `main`.

Commit messages still follow [Conventional
Commits](https://www.conventionalcommits.org/) with the package scopes listed
in `GEMINI.md`; they drive changelog entries and make it easy to see what
changed per package.

## Choosing a version

* `fix`: patch bump.
* `feat`: minor bump.
* Breaking change: major bump, or minor while the package is still `0.x`.

Mind downstream ranges. For example, Genkit depends on `dotprompt ^1.x` (npm)
and `dotprompt ^2.x` (pub.dev), so a fix shipped as a new major version won't
reach existing Genkit installs.

## Per package

| Package | Bump | Publish |
|---------|------|---------|
| `dotprompt` (npm, `js/`) | `js/package.json` | Run the **Release JS** workflow (`releaseTag`: `latest` or `next`). It publishes the version in `js/package.json`. |
| `dotpromptz` (PyPI, `python/dotpromptz/`) | `pyproject.toml`, `CHANGELOG.md`; then `uv lock` in `python/` and `scripts/export_requirements` | Create a GitHub release tagged `dotpromptz-X.Y.Z`. `publish_python_dotpromptz_package.yml` checks the tag against `pyproject.toml` and publishes. |
| `dotpromptz-handlebars` (PyPI, `python/handlebars/`) | same as above | GitHub release tagged `dotpromptz-handlebars-X.Y.Z` (`publish_python_handlebarrz_package.yml`). |
| `dotprompt` (pub.dev, `dart/dotprompt/`) | `pubspec.yaml`, `CHANGELOG.md` | `dart pub publish` from `dart/dotprompt/`. |
| Go module (`go/`) | `CHANGELOG.md` (optional) | Not tagged; consumers use pseudo-versions (`go get github.com/google/dotprompt/go@main`). If tags are ever added they must be `go/vX.Y.Z`, and from then on `@latest` resolves to the newest tag. |
| VS Code extension | `packages/vscode/package.json` | GitHub release tagged `dotprompt-vscode-X.Y.Z` (`vscode_publish.yml`). |
| Monaco, CodeMirror, tree-sitter (npm) | the package's `package.json` | Published by `web_editors.yml` / `treesitter.yml` when a push to `main` modifies that `package.json`. |
| JetBrains plugin | `plugin.xml` | Published by `ide_plugins.yml` when a push to `main` modifies `plugin.xml`. |
| `promptly` (npm) | `rs/promptly` | Push a `promptly-vX.Y.Z` tag (`promptly-npm.yml`). |
| Rust crate, Java library | `rs/dotprompt/Cargo.toml`, `java/com/google/dotprompt/BUILD.bazel` | Not published yet. `publish_rust.yml` / `publish_java.yml` run on GitHub releases tagged `dotprompt-rs-X.Y.Z` / `dotprompt-java-X.Y.Z`. |
