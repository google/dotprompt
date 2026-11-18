/*
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * Internal implementation details of Dotprompt. Not a public API.
 *
 * <p>Everything in this package may change or disappear in any release, with no compatibility
 * guarantees. Do not depend on it from outside Dotprompt. The classes are {@code public} only
 * because Java has no visibility level shared across packages; the Bazel target is restricted to
 * the {@code com.google.dotprompt} packages.
 *
 * <h2>Contents</h2>
 *
 * <pre>
 *  ┌─────────────┬────────────────────────────────────────────────────────────┐
 *  │ Class       │ Purpose                                                    │
 *  ├─────────────┼────────────────────────────────────────────────────────────┤
 *  │ Markers     │ Nonce generation, marker formatting, matching, splitting   │
 *  │ MarkerPiece │ Text or trusted-marker piece of a rendered template string │
 *  └─────────────┴────────────────────────────────────────────────────────────┘
 * </pre>
 *
 * <p>The marker helpers ({@code role}, {@code history}, {@code section}, {@code media}) emit
 * in-band markers of the form {@code <<<dotprompt:{nonce}:{body}>>>} into the rendered string, and
 * the parser splits them back out. Only markers carrying the per-render nonce are honored. Custom
 * helpers emitting markers is not a supported use case.
 */
package com.google.dotprompt.internal;
