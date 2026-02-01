# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Bazel persistent worker support for Dart builds.

This module provides utilities for running Dart actions as persistent workers,
enabling significantly faster incremental builds by keeping the Dart VM alive
between build actions.

# ELI5 (Explain Like I'm 5)

## What is a Worker?

Imagine you're painting pictures. Without a worker:
1. Get out all your paints and brushes
2. Paint one picture
3. Clean everything up and put it away
4. Repeat for EVERY picture!

That's slow! A "worker" is like leaving your paints out:
- Set up once
- Paint many pictures quickly
- Only clean up at the end

The same applies to Dart compilation - starting the Dart VM is expensive,
so we keep it running!

## Key Terms

| Term | Simple Explanation |
|------|-------------------|
| **Worker** | A helper that stays running between tasks |
| **Persistent** | Stays alive - doesn't quit after each task |
| **Flagfile** | A text file with a list of instructions |
| **Mnemonic** | A short name for the action (like DartCompile) |
| **Execution Requirements** | Rules about how to run the action |
| **Multiplex** | Handle many requests at once (like a busy waiter) |

# Data Flow Diagrams

## Worker Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Worker Lifecycle Flow                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  BUILD START                           BUILD END                                │
│      │                                     │                                    │
│      ▼                                     ▼                                    │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐     │
│  │  Start   │ → │  Handle  │ → │  Handle  │ → │  Handle  │ → │ Shutdown │     │
│  │  Worker  │   │ Request 1│   │ Request 2│   │Request N │   │  Worker  │     │
│  │  (once)  │   │  (fast)  │   │  (fast)  │   │  (fast)  │   │  (once)  │     │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘     │
│       │              │              │              │                            │
│       └──────────────┴──────────────┴──────────────┘                            │
│                              │                                                  │
│                     VM stays warm = FAST!                                       │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Flagfile Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         Flagfile Pattern Flow                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Starlark Rule                                                                  │
│       │                                                                         │
│       │ 1. Create flagfile                                                      │
│       ▼                                                                         │
│  ┌─────────────────────────────────────────┐                                   │
│  │  compile.args                            │                                   │
│  │  ────────────────────────────────────── │                                   │
│  │  --output=/path/to/output.exe           │                                   │
│  │  --main=/path/to/main.dart              │                                   │
│  │  --package-dir=/path/to/pkg             │                                   │
│  │  exe                                     │                                   │
│  └─────────────────────────────────────────┘                                   │
│       │                                                                         │
│       │ 2. Pass as @flagfile                                                    │
│       ▼                                                                         │
│  ┌─────────────────────────────────────────┐                                   │
│  │  Worker receives: @compile.args          │                                   │
│  │  Worker reads file                        │                                   │
│  │  Worker parses arguments                  │                                   │
│  │  Worker executes compilation              │                                   │
│  └─────────────────────────────────────────┘                                   │
│                                                                                 │
│  Why? Command lines have length limits. Files don't!                           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Worker Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       Bazel Persistent Worker Protocol                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────────────────────────────────────────┐ │
│  │   Bazel Build   │    │                  Worker Process                     │ │
│  │                 │    │  ┌─────────────────────────────────────────────────┐│ │
│  │  Action 1  ─────┼────┼─▶│ WorkRequest (JSON)                             ││ │
│  │                 │    │  │   {"arguments": [...], "inputs": [...]}        ││ │
│  │                 │◀───┼──│                                                 ││ │
│  │  Response 1     │    │  │ WorkResponse (JSON)                            ││ │
│  │                 │    │  │   {"exitCode": 0, "output": "..."}             ││ │
│  │  ...            │    │  └─────────────────────────────────────────────────┘│ │
│  │                 │    │                                                     │ │
│  │  Action N  ─────┼────┼─▶ [Worker stays alive, VM warm]                     │ │
│  └─────────────────┘    └─────────────────────────────────────────────────────┘ │
│                                                                                 │
│  Benefits:                                                                      │
│  • 10-50x faster incremental builds (VM startup amortized)                     │
│  • SDK parsing cached across actions                                           │
│  • Type info and ASTs retained in memory                                       │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Usage

```python
load("//private:workers.bzl", "dart_worker_action", "create_flagfile")

def _my_rule_impl(ctx):
    # Create flagfile for arguments
    flagfile = create_flagfile(ctx, "compile", [
        "--output=" + out.path,
        ctx.file.main.path,
    ])

    # Run as persistent worker
    dart_worker_action(
        ctx = ctx,
        worker = ctx.executable._dart_worker,
        flagfile = flagfile,
        inputs = [ctx.file.main],
        outputs = [out],
        mnemonic = "DartCompile",
    )
```

## References

- [Bazel Persistent Workers](https://bazel.build/remote/persistent)
- [Worker Protocol](https://github.com/bazelbuild/bazel/blob/master/src/main/protobuf/worker_protocol.proto)
"""

# Standard execution requirements for workers
WORKER_EXECUTION_REQUIREMENTS = {
    "supports-workers": "1",
    "requires-worker-protocol": "json",
}

# Execution requirements for multiplexed workers (concurrent requests)
MULTIPLEX_WORKER_REQUIREMENTS = {
    "supports-workers": "1",
    "supports-multiplex-workers": "1",
    "requires-worker-protocol": "json",
}

# Execution requirements to disable worker strategy
NO_WORKER_REQUIREMENTS = {
    "supports-workers": "0",
}

# Execution requirements for local-only shell scripts (no workers, no remote)
SHELL_SCRIPT_REQUIREMENTS = {
    "supports-workers": "0",
    "no-remote": "1",
}

def create_flagfile(ctx, name, arguments):
    """Create an arguments file for the worker protocol (flagfile pattern).

    Workers receive arguments via a file to avoid command-line length limits
    and to enable the worker pattern. The flagfile is passed as @path/to/args.

    Args:
        ctx: Rule context.
        name: Base name for the flagfile (e.g., "compile").
        arguments: List of arguments to write.

    Returns:
        The flagfile (File object).

    Example:
        >>> flagfile = create_flagfile(ctx, "analyze", ["--fatal-infos", "lib/main.dart"])
        >>> # Use as: ["@" + flagfile.path]
    """
    args_file = ctx.actions.declare_file(ctx.label.name + "_" + name + ".args")
    ctx.actions.write(
        output = args_file,
        content = "\n".join(arguments) + "\n",
    )
    return args_file

def dart_worker_action(
        ctx,
        worker,
        inputs,
        outputs,
        mnemonic,
        flagfile = None,
        arguments = None,
        progress_message = None,
        use_worker = True,
        multiplex = False,
        execution_requirements = None,
        env = None):
    """Run a Dart action, optionally as a persistent worker.

    When use_worker is True, the action will use the Bazel persistent worker
    protocol, keeping the Dart VM alive between builds for faster incremental
    builds.

    Args:
        ctx: Rule context.
        worker: The worker executable (File).
        inputs: Depset or list of input files.
        outputs: List of output files.
        mnemonic: Action mnemonic for logging (e.g., "DartAnalyze").
        flagfile: Flagfile containing arguments (for worker mode).
        arguments: Direct arguments list (for non-worker mode, or in addition to flagfile).
        progress_message: Progress message to display.
        use_worker: If True, run as persistent worker. If False, run normally.
        multiplex: If True, use multiplexed worker (multiple concurrent requests).
        execution_requirements: Dict of additional execution requirements.
        env: Dict of environment variables.

    Note:
        When use_worker=True, a flagfile MUST be provided. The worker will
        receive "@flagfile.path" as its argument.
    """
    if execution_requirements == None:
        execution_requirements = {}
    else:
        execution_requirements = dict(execution_requirements)

    all_arguments = []

    final_inputs = inputs
    if use_worker:
        # Validate that flagfile is provided for worker mode
        if flagfile == None:
            fail("flagfile is required when use_worker=True")

        # Add worker-specific execution requirements
        if multiplex:
            execution_requirements.update(MULTIPLEX_WORKER_REQUIREMENTS)
        else:
            execution_requirements.update(WORKER_EXECUTION_REQUIREMENTS)

        # Workers receive flagfile via @ prefix
        all_arguments = ["@" + flagfile.path]

        # Add flagfile to inputs
        if type(inputs) == "depset":
            final_inputs = depset(direct = [flagfile], transitive = [inputs])
        else:
            # inputs is a list, create depset from it
            final_inputs = depset(direct = [flagfile] + inputs)

        # Additional arguments (rarely needed with workers)
        if arguments:
            all_arguments.extend(arguments)
    else:
        # Non-worker mode: use arguments directly
        if arguments:
            all_arguments = list(arguments)
        elif flagfile:
            all_arguments = ["@" + flagfile.path]
            if type(inputs) == "depset":
                final_inputs = depset(direct = [flagfile], transitive = [inputs])
            else:
                final_inputs = depset(direct = [flagfile] + inputs)

    ctx.actions.run(
        executable = worker,
        arguments = all_arguments,
        inputs = final_inputs,
        outputs = outputs,
        mnemonic = mnemonic,
        progress_message = progress_message,
        execution_requirements = execution_requirements,
        env = env,
    )

def get_worker_key(worker_path, extra_flags = None):
    """Get a unique key for a worker configuration.

    Workers are pooled by key - workers with the same key share instances.
    Use this to customize worker pooling based on configuration.

    Args:
        worker_path: Path to the worker executable.
        extra_flags: Optional list of flags that affect worker behavior.

    Returns:
        A string key for the worker configuration.

    Example:
        >>> key = get_worker_key(worker.path, ["--strict"])
        >>> # Workers with same key are reused
    """
    if extra_flags:
        return worker_path + ":" + ",".join(extra_flags)
    return worker_path

def shell_script_action(
        ctx,
        script,
        inputs,
        outputs,
        mnemonic,
        progress_message = None,
        execution_requirements = None,
        env = None):
    """Run a shell script action that doesn't support workers.

    Use this for shell-script-based actions that cannot implement the
    worker protocol. This explicitly disables the worker strategy.

    Args:
        ctx: Rule context.
        script: The shell script executable (File).
        inputs: Depset or list of input files.
        outputs: List of output files.
        mnemonic: Action mnemonic for logging.
        progress_message: Progress message to display.
        execution_requirements: Dict of additional execution requirements.
        env: Dict of environment variables.
    """
    if execution_requirements == None:
        execution_requirements = dict(SHELL_SCRIPT_REQUIREMENTS)
    else:
        execution_requirements = dict(execution_requirements)
        execution_requirements.update(SHELL_SCRIPT_REQUIREMENTS)

    ctx.actions.run(
        executable = script,
        inputs = inputs,
        outputs = outputs,
        mnemonic = mnemonic,
        progress_message = progress_message,
        execution_requirements = execution_requirements,
        env = env,
    )
