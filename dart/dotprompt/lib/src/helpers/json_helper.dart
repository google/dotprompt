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

/// JSON helper for serializing objects to JSON in templates.
///
/// The {{json}} helper converts objects to JSON strings.
///
/// ## Usage
///
/// ```handlebars
/// {{json user}}
/// {{json data indent=2}}
/// ```
library;

import "dart:convert";

/// Marker class for the JSON helper.
///
/// This helper serializes data to JSON format for inclusion in prompts.
class JsonHelper {
  /// Private constructor to prevent instantiation.
  JsonHelper._();

  /// The name of this helper in templates.
  static const String name = "json";

  /// Renders a value as a JSON string.
  ///
  /// [value] is the value to serialize.
  /// [indent] is the optional indentation for pretty printing.
  static String render(dynamic value, {int? indent}) {
    if (value == null) {
      return "null";
    }

    if (indent != null && indent > 0) {
      return const JsonEncoder.withIndent("  ").convert(value);
    }

    return jsonEncode(value);
  }
}
