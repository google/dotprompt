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

/// History helper for including conversation history in prompts.
///
/// The {{#history}} helper renders previous conversation messages,
/// supporting multi-turn conversations.
///
/// ## Usage
///
/// ```handlebars
/// {{#history}}
/// {{role}}: {{content}}
/// {{/history}}
/// ```
///
/// ## Data Requirements
///
/// The history helper expects a `messages` array in the data context,
/// where each message has `role` and `content` fields.
library;

import "../types.dart";

/// Marker class for the history helper.
///
/// This helper processes the message history from the data context
/// and renders each message according to the block template.
class HistoryHelper {
  /// Private constructor to prevent instantiation.
  HistoryHelper._();

  /// The name of this helper in templates.
  static const String name = "history";

  /// Renders conversation history from the data context.
  ///
  /// Takes a list of [Message] objects and renders them using the
  /// provided block content.
  static String render(
    List<Message>? messages,
    String Function(Message) renderBlock,
  ) {
    if (messages == null || messages.isEmpty) {
      return "";
    }

    final buffer = StringBuffer();
    for (final message in messages) {
      buffer.write(renderBlock(message));
    }
    return buffer.toString();
  }
}
