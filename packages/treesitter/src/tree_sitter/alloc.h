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

#ifndef TREE_SITTER_ALLOC_H_
#define TREE_SITTER_ALLOC_H_

#ifdef __cplusplus
extern "C" {
#endif

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

// Allow clients to override allocation functions
#ifdef TREE_SITTER_REUSE_ALLOCATOR

extern void *(*ts_current_malloc)(size_t);
extern void *(*ts_current_calloc)(size_t, size_t);
extern void *(*ts_current_realloc)(void *, size_t);
extern void (*ts_current_free)(void *);

#ifndef ts_malloc
#define ts_malloc  ts_current_malloc
#endif
#ifndef ts_calloc
#define ts_calloc  ts_current_calloc
#endif
#ifndef ts_realloc
#define ts_realloc ts_current_realloc
#endif
#ifndef ts_free
#define ts_free    ts_current_free
#endif

#else

#ifndef ts_malloc
#define ts_malloc  malloc
#endif
#ifndef ts_calloc
#define ts_calloc  calloc
#endif
#ifndef ts_realloc
#define ts_realloc realloc
#endif
#ifndef ts_free
#define ts_free    free
#endif

#endif

#ifdef __cplusplus
}
#endif

#endif // TREE_SITTER_ALLOC_H_
