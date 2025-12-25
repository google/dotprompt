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

package com.google.dotprompt.store;

import java.nio.file.Path;

/**
 * Configuration options for directory-based prompt stores.
 *
 * @param directory The base directory where prompt files are stored.
 */
public record DirStoreOptions(Path directory) {

  /**
   * Creates options from a string path.
   *
   * @param directory The directory path as a string.
   * @return A new DirStoreOptions instance.
   */
  public static DirStoreOptions of(String directory) {
    return new DirStoreOptions(Path.of(directory));
  }
}
