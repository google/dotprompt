/*
 * Copyright 2025 Google LLC
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

package com.google.dotprompt.models;

/**
 * Base interface for paginated responses.
 *
 * <p>This interface defines the common cursor field used for pagination across list operations.
 */
public interface PaginatedResponse {

  /**
   * Gets the cursor for fetching the next page of results.
   *
   * @return The pagination cursor, or null if there are no more results.
   */
  String cursor();
}
