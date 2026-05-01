// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// SPDX-License-Identifier: Apache-2.0

/// Shared equality utilities for deep comparison of maps and lists.
///
/// These helpers are used throughout the library for implementing
/// value-based equality on types containing maps and lists.
library;

/// Performs a deep equality comparison of two values.
///
/// Handles [Map], [List], and scalar values recursively.
bool deepEquals(dynamic a, dynamic b) {
  if (identical(a, b)) return true;
  if (a == null && b == null) return true;
  if (a == null || b == null) return false;

  if (a is Map && b is Map) return mapEquals(a, b);
  if (a is List && b is List) return listEquals(a, b);

  return a == b;
}

/// Performs a shallow equality comparison of two maps.
///
/// Returns `true` if both maps are null, or if they have the same keys
/// and equal values for each key.
bool mapEquals<K, V>(Map<K, V>? a, Map<K, V>? b) {
  if (a == null && b == null) return true;
  if (a == null || b == null) return false;
  if (a.length != b.length) return false;
  for (final key in a.keys) {
    if (!b.containsKey(key) || !deepEquals(a[key], b[key])) return false;
  }
  return true;
}

/// Performs a shallow equality comparison of two lists.
///
/// Returns `true` if both lists are null, or if they have the same length
/// and equal elements at each index.
bool listEquals<T>(List<T>? a, List<T>? b) {
  if (a == null && b == null) return true;
  if (a == null || b == null) return false;
  if (a.length != b.length) return false;
  for (var i = 0; i < a.length; i++) {
    if (!deepEquals(a[i], b[i])) return false;
  }
  return true;
}
