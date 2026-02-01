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

"""Bazel persistent worker support for Flutter/Dart builds.

This module provides utilities for running Dart actions as persistent workers,
enabling significantly faster incremental builds.

# ELI5 (Explain Like I'm 5)

## What is a Worker?

Imagine you're baking cookies. Without a worker:
1. Turn on the oven
2. Wait for it to heat up
3. Bake cookies
4. Turn off the oven
5. Repeat for every batch!

That's slow! A "worker" keeps the oven warm:
- Heat up once
- Bake many batches quickly
- Only turn off at the end

The same applies to Flutter/Dart builds - starting the Dart VM is like
preheating an oven. Workers keep it running!

## Key Terms

| Term | Simple Explanation |
|------|-------------------|
| **Worker** | A helper that stays running between tasks |
| **Persistent** | Stays alive - doesn't quit after each task |
| **Flagfile** | A text file with a list of instructions |
| **Hot Reload** | Update the app without restarting it |
| **Analyzer** | Checks your code for errors |

# Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    Bazel Persistent Worker Flow                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  1. First build: Bazel starts worker process                                   │
│     bazel build :app ──▶ spawn analyzer_worker --persistent_worker             │
│                                                                                 │
│  2. Subsequent builds: Reuse running worker                                    │
│     bazel build :app ──▶ send WorkRequest to worker ──▶ receive response       │
│                                                                                 │
│  3. Worker maintains:                                                           │
│     • Parsed ASTs                                                              │
│     • Type information                                                          │
│     • Dependency graph                                                          │
│                                                                                 │
│  Result: 10-50x faster incremental builds                                      │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

# Usage

```python
load("@rules_flutter//private:workers.bzl", "dart_worker_action")

def _my_rule_impl(ctx):
    # Run a Dart action as a persistent worker
    dart_worker_action(
        ctx = ctx,
        worker = ctx.executable._analyzer_worker,
        arguments = ["--analyze", ctx.file.src.path],
        inputs = [ctx.file.src],
        outputs = [ctx.outputs.report],
    )
```
"""

def worker_args_file(ctx, name, arguments):
    """Create an arguments file for worker protocol.

    Workers receive arguments via a file to avoid command-line length limits.

    Args:
        ctx: Rule context.
        name: Name for the args file.
        arguments: List of arguments.

    Returns:
        The args file.
    """
    args_file = ctx.actions.declare_file(name + ".args")
    ctx.actions.write(
        output = args_file,
        content = "\n".join(arguments),
    )
    return args_file

def dart_worker_action(
        ctx,
        worker,
        arguments,
        inputs,
        outputs,
        mnemonic = "DartWorker",
        progress_message = None,
        use_worker = True,
        execution_requirements = None):
    """Run a Dart action, optionally as a persistent worker.

    When use_worker is True, the action will be run as a persistent worker,
    keeping the Dart VM alive between builds for faster incremental builds.

    Args:
        ctx: Rule context.
        worker: The worker executable (File).
        arguments: List of arguments to pass to the worker.
        inputs: List of input files.
        outputs: List of output files.
        mnemonic: Action mnemonic for logging.
        progress_message: Progress message to display.
        use_worker: If True, run as persistent worker. If False, run normally.
        execution_requirements: Dict of execution requirements.
    """
    if execution_requirements == None:
        execution_requirements = {}

    if use_worker:
        # Add worker-specific execution requirements
        execution_requirements = dict(execution_requirements)
        execution_requirements["supports-workers"] = "1"
        execution_requirements["requires-worker-protocol"] = "json"

        # Workers expect the persistent_worker flag
        worker_args = ["--persistent_worker"]

        # If inputs/outputs are depset, convert to list for safety if needed,
        # but ctx.actions.run handles depsets.
        # The lint error was about iterating over depsets in Starlark.
        # Use depset constructor for joining if needed, though ctx.actions.run usually handles list/depset mix for inputs.

        ctx.actions.run(
            executable = worker,
            arguments = worker_args + arguments,
            inputs = inputs,
            outputs = outputs,
            mnemonic = mnemonic,
            progress_message = progress_message,
            execution_requirements = execution_requirements,
        )
    else:
        # Normal (non-worker) execution
        ctx.actions.run(
            executable = worker,
            arguments = arguments,
            inputs = inputs,
            outputs = outputs,
            mnemonic = mnemonic,
            progress_message = progress_message,
            execution_requirements = execution_requirements,
        )

def get_worker_key(worker, extra_flags = None):
    """Get a unique key for a worker configuration.

    Workers are pooled by key - workers with the same key share instances.

    Args:
        worker: The worker executable path.
        extra_flags: Optional list of flags that affect worker behavior.

    Returns:
        A string key for the worker configuration.
    """
    if extra_flags:
        return worker.path + ":" + ",".join(extra_flags)
    return worker.path

# Standard execution requirements for workers
WORKER_EXECUTION_REQUIREMENTS = {
    "supports-workers": "1",
    "requires-worker-protocol": "json",
}

# Execution requirements for multiplexed workers (multiple concurrent requests)
MULTIPLEX_WORKER_REQUIREMENTS = {
    "supports-workers": "1",
    "supports-multiplex-workers": "1",
    "requires-worker-protocol": "json",
}
