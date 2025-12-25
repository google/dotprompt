# Making Releases

This repository uses
[release-please](https://github.com/googleapis/release-please) for managing
releases across multiple packages. Release-please automates versioning and
changelog generation based on [Conventional
Commits](https://www.conventionalcommits.org/).

## Monorepo Structure

The repository is configured to manage releases independently for the following
packages:

* `js/` - JavaScript implementation of dotprompt
* `python/dotpromptz/` - Python implementation of dotprompt
* `python/handlebarrz/` - Python implementation of handlebarrz
* `go/` - Go implementation of dotprompt
* `java/` - Java implementation of dotprompt

## How It Works

1. When commits are pushed to `main`, `release-please` automatically creates or
   updates release PRs for each package that has changes.
2. Each package has its own release PR and will be versioned independently.
3. When a release PR is merged, `release-please` will:
   * Create a new release with appropriate tags.
   * Update the package version.
   * Generate changelog entries.

## Commit Message Format

To ensure proper versioning, commit messages should follow the [Conventional
Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

* `feat`: A new feature (triggers a minor version bump)
* `fix`: A bug fix (triggers a patch version bump)
* `docs`: Documentation changes
* `style`: Code style changes (formatting, etc.)
* `refactor`: Code changes that neither fix bugs nor add features
* `perf`: Performance improvements
* `test`: Adding or updating tests
* `build`: Changes to build system or dependencies
* `ci`: Changes to CI configuration
* `chore`: Other changes that don't modify source code
* `revert`: Reverting a previous commit

### Scopes

To target specific packages, use these scopes:

* `js`: For changes to the JavaScript implementation
* `py`: For changes affecting all Python packages
* `py/dotpromptz`: For changes to the Python dotpromptz package
* `py/handlebarrz`: For changes to the Python handlebarrz package
* `go`: For changes to the Go implementation
* `java`: For changes to the Java implementation
* `deps`: For dependency updates

### Examples

```
feat(js): add new template helper function

fix(py/dotpromptz): resolve issue with template parsing

docs(go): update API documentation

build(py/handlebarrz): update build configuration
```

## Breaking Changes

For breaking changes, add `BREAKING CHANGE:` in the commit message body or
footer:

```
feat(js): change API interface

BREAKING CHANGE: The `render` method now returns a Promise instead of a string
```

This will trigger a major version bump for the affected package.

## Manual Release

If you need to manually trigger a release, you can:

1. Create a new release PR by running the release-please GitHub Action workflow
   manually
2. Or push a commit to main with the appropriate conventional commit message

## Checking Release Status

The `.release-please-manifest.json` file tracks the current version of each
package.
