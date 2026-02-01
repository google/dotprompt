# rules_flutter Development Guidelines

## Overview

`rules_flutter` provides hermetic, cross-platform Bazel rules for building Flutter applications.
The rules are designed to be fully portable and work natively on Windows, macOS, and Linux
without requiring external shell interpreters.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              rules_flutter                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────────┐   │
│  │  Core Rules     │   │  SDK Repository │   │  Module Extension       │   │
│  │  (defs.bzl)     │   │  (repositories  │   │  (extensions.bzl)       │   │
│  ├─────────────────┤   │   .bzl)         │   ├─────────────────────────┤   │
│  │ flutter_library │   ├─────────────────┤   │ flutter.configure()     │   │
│  │ flutter_binary  │   │ flutter_sdk     │   └─────────────────────────┘   │
│  │ flutter_test    │   │ repository rule │                                 │
│  │ flutter_app     │   └─────────────────┘                                 │
│  └─────────────────┘                                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Cross-Platform Design

All rules generate platform-specific scripts:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     Script Generation Pattern                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  is_windows = ctx.target_platform_has_constraint(windows_constraint)     │
│                                                                          │
│  ┌─────────────────────────┐     ┌─────────────────────────┐            │
│  │  Windows (.bat)         │     │  Unix (.sh)             │            │
│  ├─────────────────────────┤     ├─────────────────────────┤            │
│  │ @echo off               │     │ #!/bin/bash             │            │
│  │ setlocal                │     │ set -e                  │            │
│  │ %FLUTTER_BIN% build ... │     │ "$FLUTTER_BIN" build ...│            │
│  └─────────────────────────┘     └─────────────────────────┘            │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Independence Requirements

`rules_flutter` must be completely independent:

1. **No external dependencies** on parent repository code
2. **All imports** must be relative to the module
3. **Bzlmod-first** design using `Label()` for external references
4. **Self-contained** - ready for BCR publication

## Module Documentation Standards

Every module (`.bzl`, `.dart`, `.go` file) should include comprehensive documentation with the following sections:

### Required Sections

1. **ELI5 (Explain Like I'm 5)**: Simple analogies explaining the concept
2. **Key Terms Table**: Terminology definitions in table format
3. **Data Flow Diagrams**: ASCII art showing how data moves through the system
4. **Usage Examples**: Practical code examples

### ELI5 Format

```
# ELI5 (Explain Like I'm 5)

## What is [Concept]?

Imagine you're [simple analogy]...
```

Example:

```
# ELI5 (Explain Like I'm 5)

## What is a Worker?

Imagine you're building with LEGO. Without a worker, every time you
want to build something, you have to get out the LEGO, build, then
put it all away. A "worker" leaves the LEGO out so you can build
faster!
```

### Key Terms Table Format

```markdown
## Key Terms

| Term | Simple Explanation |
|------|-------------------|
| **Worker** | A helper that stays running between tasks |
| **Flagfile** | A text file with a list of instructions |
```

### Data Flow Diagram Standards

Use ASCII box drawing for all diagrams:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Diagram Title                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                                    │
│  │  Step 1  │ → │  Step 2  │ → │  Step 3  │                                    │
│  └──────────┘   └──────────┘   └──────────┘                                    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

Box drawing characters:
- Corners: `┌ ┐ └ ┘`
- Lines: `─ │`
- T-junctions: `├ ┤ ┬ ┴`
- Cross: `┼`
- Arrows: `→ ← ↓ ↑ ▶ ◀ ▼ ▲`

## Rule Implementation Pattern

```python
def _flutter_rule_impl(ctx):
    # 1. Platform detection
    is_windows = ctx.target_platform_has_constraint(
        ctx.attr._windows_constraint[platform_common.ConstraintValueInfo]
    )
    
    # 2. Declare output with correct extension
    script_ext = ".bat" if is_windows else ".sh"
    runner = ctx.actions.declare_file(ctx.label.name + script_ext)
    
    # 3. Get Flutter SDK path
    flutter_bin = ctx.executable.flutter_sdk
    
    # 4. Generate platform-specific script
    content = generate_windows_script(...) if is_windows else generate_unix_script(...)
    
    # 5. Write and return
    ctx.actions.write(runner, content, is_executable = True)
    return [DefaultInfo(executable = runner, runfiles = ...)]
```

## Licensing

Include Apache 2.0 header in all files:

```python
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# ...
# SPDX-License-Identifier: Apache-2.0
```

## Testing

Test every rule on all platforms:
- Windows (native .bat)
- macOS (native .sh)
- Linux (native .sh)

## BCR Publication Checklist

- [ ] MODULE.bazel with proper metadata
- [ ] BUILD.bazel with exports
- [ ] README.md with documentation
- [ ] ROADMAP.md with feature status
- [ ] All rules cross-platform tested
- [ ] No hardcoded paths
- [ ] License headers on all files
