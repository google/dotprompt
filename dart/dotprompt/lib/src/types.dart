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

/// Core type definitions for the Dotprompt library.
///
/// This module contains the fundamental types used throughout the library,
/// including message roles, data arguments, and configuration types.
///
/// ## Type Hierarchy
///
/// ```
/// DataArgument
/// ├── input: Map<String, dynamic>?    # Input variables for rendering
/// ├── context: ContextData?            # Context data (@state, @auth, etc.)
/// ├── messages: List<Message>?         # Previous message history
/// └── docs: List<Document>?            # Document references
///
/// ContextData
/// ├── state: Map<String, dynamic>?     # @state variables
/// └── [arbitrary keys]                 # Any @key variables
/// ```
library;

import "package:meta/meta.dart";

/// Represents the role of a message sender in a conversation.
///
/// Roles are used to distinguish between different participants in a
/// prompt conversation (user input vs model output vs system instructions).
///
/// ## Standard Roles
///
/// | Role   | Description                                      |
/// |--------|--------------------------------------------------|
/// | user   | Human user input                                 |
/// | model  | AI model response                                |
/// | system | System instructions/configuration                |
/// | tool   | Tool/function call results                       |
///
/// ## Example
///
/// ```dart
/// final message = Message(
///   role: Role.user,
///   content: [TextPart(text: 'Hello!')],
/// );
/// ```
enum Role {
  /// User role - represents human input.
  user("user"),

  /// Model role - represents AI model responses.
  model("model"),

  /// System role - represents system instructions.
  system("system"),

  /// Tool role - represents tool/function call results.
  tool("tool");

  /// Creates a [Role] with the given string value.
  const Role(this.value);

  /// The string representation of the role.
  final String value;

  /// Parses a string into a [Role].
  ///
  /// Throws [ArgumentError] if the string doesn't match a known role.
  static Role fromString(String s) {
    final normalized = s.toLowerCase();
    for (final role in Role.values) {
      if (role.value == normalized) {
        return role;
      }
    }
    throw ArgumentError.value(s, "role", "Unknown role: $s");
  }

  /// Parses a string into a [Role], returning null if unknown.
  static Role? tryParse(String s) {
    final normalized = s.toLowerCase();
    for (final role in Role.values) {
      if (role.value == normalized) {
        return role;
      }
    }
    return null;
  }

  @override
  String toString() => value;
}

/// Data argument passed to prompt rendering.
///
/// Contains all the data needed to render a prompt template, including
/// input variables, context data, message history, and documents.
///
/// ## Components
///
/// - [input]: The main input variables for template substitution
/// - [context]: Context data accessible via @ variables (@state, @auth, etc.)
/// - [messages]: Previous message history for multi-turn conversations
/// - [docs]: Document references for RAG patterns
///
/// ## Example
///
/// ```dart
/// final data = DataArgument(
///   input: {'name': 'Alice', 'topic': 'AI'},
///   context: ContextData(
///     state: {'count': 5},
///     auth: {'email': 'alice@example.com'},
///   ),
/// );
/// ```
@immutable
class DataArgument {
  /// Creates a new [DataArgument].
  const DataArgument({this.input, this.context, this.messages, this.docs});

  /// Creates a [DataArgument] from a JSON map.
  factory DataArgument.fromJson(Map<String, dynamic> json) => DataArgument(
        input: json["input"] as Map<String, dynamic>?,
        context: json["context"] != null ? ContextData.fromJson(json["context"] as Map<String, dynamic>) : null,
        messages: json["messages"] != null
            ? (json["messages"] as List).map((e) => Message.fromJson(e as Map<String, dynamic>)).toList()
            : null,
        docs: json["docs"] != null
            ? (json["docs"] as List).map((e) => Document.fromJson(e as Map<String, dynamic>)).toList()
            : null,
      );

  /// Input variables for template substitution.
  final Map<String, dynamic>? input;

  /// Context data accessible via @ variables.
  final ContextData? context;

  /// Previous message history.
  final List<Message>? messages;

  /// Document references.
  final List<Document>? docs;

  /// Converts this to a JSON-serializable map.
  Map<String, dynamic> toJson() => {
        if (input != null) "input": input,
        if (context != null) "context": context!.toJson(),
        if (messages != null) "messages": messages!.map((m) => m.toJson()).toList(),
        if (docs != null) "docs": docs!.map((d) => d.toJson()).toList(),
      };

  /// Creates a copy with the given fields replaced.
  DataArgument copyWith({
    Map<String, dynamic>? input,
    ContextData? context,
    List<Message>? messages,
    List<Document>? docs,
  }) =>
      DataArgument(
        input: input ?? this.input,
        context: context ?? this.context,
        messages: messages ?? this.messages,
        docs: docs ?? this.docs,
      );

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is DataArgument &&
          _mapEquals(input, other.input) &&
          context == other.context &&
          _listEquals(messages, other.messages) &&
          _listEquals(docs, other.docs);

  @override
  int get hashCode => Object.hash(input.hashCode, context, messages.hashCode, docs.hashCode);

  @override
  String toString() => "DataArgument(input: $input, context: $context, "
      "messages: $messages, docs: $docs)";
}

/// Context data accessible via @ variables in templates.
///
/// Any key in the context can be accessed using the @key syntax in templates.
/// Common context variables include @state, @auth, and @user.
///
/// ## Example
///
/// ```dart
/// final context = ContextData(
///   state: {'count': 42, 'status': 'active'},
///   data: {
///     'auth': {'email': 'alice@example.com'},
///     'user': {'role': 'admin'},
///   },
/// );
/// // In template: {{@state.count}}, {{@auth.email}}, {{@user.role}}
/// ```
@immutable
class ContextData {
  /// Creates a [ContextData] with the given state and additional data.
  const ContextData({this.state, Map<String, dynamic>? data}) : _data = data ?? const {};

  /// Creates a [ContextData] from a JSON map.
  factory ContextData.fromJson(Map<String, dynamic> json) {
    final data = Map<String, dynamic>.from(json);
    final state = data.remove("state") as Map<String, dynamic>?;
    return ContextData(state: state, data: data);
  }

  /// The @state context variable.
  final Map<String, dynamic>? state;

  /// Additional context data (accessible as @key).
  final Map<String, dynamic> _data;

  /// Gets a context value by key.
  dynamic operator [](String key) {
    if (key == "state") return state;
    return _data[key];
  }

  /// Gets all context keys.
  Iterable<String> get keys => {"state", ..._data.keys};

  /// Converts this to a JSON-serializable map.
  Map<String, dynamic> toJson() => {
        if (state != null) "state": state,
        ..._data,
      };

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is ContextData && _mapEquals(state, other.state) && _mapEquals(_data, other._data);

  @override
  int get hashCode => Object.hash(state.hashCode, _data.hashCode);

  @override
  String toString() => "ContextData(state: $state, data: $_data)";
}

/// A document reference for RAG patterns.
///
/// Documents can be included in prompts for retrieval-augmented generation.
@immutable
class Document {
  /// Creates a new [Document].
  const Document({required this.content, this.metadata});

  /// Creates a [Document] from a JSON map.
  factory Document.fromJson(Map<String, dynamic> json) => Document(
        content: json["content"] as String,
        metadata: json["metadata"] as Map<String, dynamic>?,
      );

  /// The document content.
  final String content;

  /// Optional metadata.
  final Map<String, dynamic>? metadata;

  /// Converts this to a JSON-serializable map.
  Map<String, dynamic> toJson() => {
        "content": content,
        if (metadata != null) "metadata": metadata,
      };

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is Document && content == other.content && _mapEquals(metadata, other.metadata);

  @override
  int get hashCode => Object.hash(content, metadata.hashCode);

  @override
  String toString() => "Document(content: $content, metadata: $metadata)";
}

/// A chat message in a prompt.
///
/// Messages consist of a role (sender) and content parts (text, media, etc.).
///
/// ## Example
///
/// ```dart
/// final message = Message(
///   role: Role.user,
///   content: [
///     TextPart(text: 'What is this image?'),
///     MediaPart(media: MediaContent(url: 'image.png', contentType: 'image/png')),
///   ],
/// );
/// ```
@immutable
class Message {
  /// Creates a new [Message].
  const Message({required this.role, required this.content, this.metadata});

  /// Creates a [Message] from a JSON map.
  factory Message.fromJson(Map<String, dynamic> json) => Message(
        role: Role.fromString(json["role"] as String),
        content: (json["content"] as List).map((e) => Part.fromJson(e as Map<String, dynamic>)).toList(),
        metadata: json["metadata"] as Map<String, dynamic>?,
      );

  /// The role of the message sender.
  final Role role;

  /// The message content parts.
  final List<Part> content;

  /// Optional metadata.
  final Map<String, dynamic>? metadata;

  /// Converts this to a JSON-serializable map.
  Map<String, dynamic> toJson() => {
        "role": role.value,
        "content": content.map((p) => p.toJson()).toList(),
        if (metadata != null) "metadata": metadata,
      };

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Message &&
          role == other.role &&
          _listEquals(content, other.content) &&
          _mapEquals(metadata, other.metadata);

  @override
  int get hashCode => Object.hash(role, content.hashCode, metadata.hashCode);

  @override
  String toString() => "Message(role: $role, content: $content, metadata: $metadata)";
}

/// Abstract base class for message content parts.
///
/// Parts represent different types of content in a message:
/// - [TextPart]: Plain text content
/// - [MediaPart]: Media content (images, audio, video)
/// - [ToolRequestPart]: Tool/function call request
/// - [ToolResponsePart]: Tool/function call response
/// - [DataPart]: Arbitrary structured data
/// - [PendingPart]: Placeholder for async content
@immutable
sealed class Part {
  const Part();

  /// Creates a [Part] from a JSON map.
  factory Part.fromJson(Map<String, dynamic> json) {
    if (json.containsKey("text")) {
      return TextPart.fromJson(json);
    } else if (json.containsKey("media")) {
      return MediaPart.fromJson(json);
    } else if (json.containsKey("toolRequest")) {
      return ToolRequestPart.fromJson(json);
    } else if (json.containsKey("toolResponse")) {
      return ToolResponsePart.fromJson(json);
    } else if (json.containsKey("data")) {
      return DataPart.fromJson(json);
    } else if (json.containsKey("pending")) {
      return PendingPart.fromJson(json);
    } else if (json.containsKey("metadata")) {
      return MetadataPart.fromJson(json);
    }
    throw ArgumentError.value(json, "json", "Unknown part type");
  }

  /// Converts this part to a JSON-serializable map.
  Map<String, dynamic> toJson();
}

/// A text content part.
@immutable
class TextPart extends Part {
  /// Creates a new [TextPart].
  const TextPart({required this.text});

  /// Creates a [TextPart] from a JSON map.
  factory TextPart.fromJson(Map<String, dynamic> json) => TextPart(text: json["text"] as String);

  /// The text content.
  final String text;

  @override
  Map<String, dynamic> toJson() => {"text": text};

  @override
  bool operator ==(Object other) => identical(this, other) || other is TextPart && text == other.text;

  @override
  int get hashCode => text.hashCode;

  @override
  String toString() => "TextPart(text: $text)";
}

/// Media content (images, audio, video).
@immutable
class MediaContent {
  /// Creates a new [MediaContent].
  const MediaContent({required this.contentType, this.url, this.data});

  /// Creates a [MediaContent] from a JSON map.
  factory MediaContent.fromJson(Map<String, dynamic> json) => MediaContent(
        contentType: json["contentType"] as String,
        url: json["url"] as String?,
        data: json["data"] as String?,
      );

  /// The MIME content type.
  final String contentType;

  /// URL to the media content.
  final String? url;

  /// Base64-encoded inline data.
  final String? data;

  /// Converts this to a JSON-serializable map.
  Map<String, dynamic> toJson() => {
        "contentType": contentType,
        if (url != null) "url": url,
        if (data != null) "data": data,
      };

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is MediaContent && contentType == other.contentType && url == other.url && data == other.data;

  @override
  int get hashCode => Object.hash(contentType, url, data);

  @override
  String toString() => "MediaContent(contentType: $contentType, url: $url, data: $data)";
}

/// A media content part.
@immutable
class MediaPart extends Part {
  /// Creates a new [MediaPart].
  const MediaPart({required this.media});

  /// Creates a [MediaPart] from a JSON map.
  factory MediaPart.fromJson(Map<String, dynamic> json) => MediaPart(
        media: MediaContent.fromJson(json["media"] as Map<String, dynamic>),
      );

  /// The media content.
  final MediaContent media;

  @override
  Map<String, dynamic> toJson() => {"media": media.toJson()};

  @override
  bool operator ==(Object other) => identical(this, other) || other is MediaPart && media == other.media;

  @override
  int get hashCode => media.hashCode;

  @override
  String toString() => "MediaPart(media: $media)";
}

/// A tool/function call request.
@immutable
class ToolRequest {
  /// Creates a new [ToolRequest].
  const ToolRequest({required this.name, required this.ref, this.input});

  /// Creates a [ToolRequest] from a JSON map.
  factory ToolRequest.fromJson(Map<String, dynamic> json) => ToolRequest(
        name: json["name"] as String,
        ref: json["ref"] as String,
        input: json["input"] as Map<String, dynamic>?,
      );

  /// The tool name.
  final String name;

  /// A unique reference ID for this request.
  final String ref;

  /// Input arguments for the tool.
  final Map<String, dynamic>? input;

  /// Converts this to a JSON-serializable map.
  Map<String, dynamic> toJson() => {
        "name": name,
        "ref": ref,
        if (input != null) "input": input,
      };

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is ToolRequest && name == other.name && ref == other.ref && _mapEquals(input, other.input);

  @override
  int get hashCode => Object.hash(name, ref, input.hashCode);

  @override
  String toString() => "ToolRequest(name: $name, ref: $ref, input: $input)";
}

/// A tool/function call request part.
@immutable
class ToolRequestPart extends Part {
  /// Creates a new [ToolRequestPart].
  const ToolRequestPart({required this.toolRequest});

  /// Creates a [ToolRequestPart] from a JSON map.
  factory ToolRequestPart.fromJson(Map<String, dynamic> json) => ToolRequestPart(
        toolRequest: ToolRequest.fromJson(
          json["toolRequest"] as Map<String, dynamic>,
        ),
      );

  /// The tool request.
  final ToolRequest toolRequest;

  @override
  Map<String, dynamic> toJson() => {"toolRequest": toolRequest.toJson()};

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is ToolRequestPart && toolRequest == other.toolRequest;

  @override
  int get hashCode => toolRequest.hashCode;

  @override
  String toString() => "ToolRequestPart(toolRequest: $toolRequest)";
}

/// A tool/function call response.
@immutable
class ToolResponse {
  /// Creates a new [ToolResponse].
  const ToolResponse({required this.name, required this.ref, this.output});

  /// Creates a [ToolResponse] from a JSON map.
  factory ToolResponse.fromJson(Map<String, dynamic> json) => ToolResponse(
        name: json["name"] as String,
        ref: json["ref"] as String,
        output: json["output"],
      );

  /// The tool name.
  final String name;

  /// The reference ID from the original request.
  final String ref;

  /// The tool output.
  final dynamic output;

  /// Converts this to a JSON-serializable map.
  Map<String, dynamic> toJson() => {
        "name": name,
        "ref": ref,
        if (output != null) "output": output,
      };

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is ToolResponse && name == other.name && ref == other.ref && output == other.output;

  @override
  int get hashCode => Object.hash(name, ref, output);

  @override
  String toString() => "ToolResponse(name: $name, ref: $ref, output: $output)";
}

/// A tool/function call response part.
@immutable
class ToolResponsePart extends Part {
  /// Creates a new [ToolResponsePart].
  const ToolResponsePart({required this.toolResponse});

  /// Creates a [ToolResponsePart] from a JSON map.
  factory ToolResponsePart.fromJson(Map<String, dynamic> json) => ToolResponsePart(
        toolResponse: ToolResponse.fromJson(
          json["toolResponse"] as Map<String, dynamic>,
        ),
      );

  /// The tool response.
  final ToolResponse toolResponse;

  @override
  Map<String, dynamic> toJson() => {"toolResponse": toolResponse.toJson()};

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is ToolResponsePart && toolResponse == other.toolResponse;

  @override
  int get hashCode => toolResponse.hashCode;

  @override
  String toString() => "ToolResponsePart(toolResponse: $toolResponse)";
}

/// An arbitrary structured data part.
@immutable
class DataPart extends Part {
  /// Creates a new [DataPart].
  const DataPart({required this.data});

  /// Creates a [DataPart] from a JSON map.
  factory DataPart.fromJson(Map<String, dynamic> json) => DataPart(data: json["data"] as Map<String, dynamic>);

  /// The data content.
  final Map<String, dynamic> data;

  @override
  Map<String, dynamic> toJson() => {"data": data};

  @override
  bool operator ==(Object other) => identical(this, other) || other is DataPart && _mapEquals(data, other.data);

  @override
  int get hashCode => data.hashCode;

  @override
  String toString() => "DataPart(data: $data)";
}

/// A pending placeholder part.
@immutable
class PendingPart extends Part {
  /// Creates a new [PendingPart].
  const PendingPart({required this.pending});

  /// Creates a [PendingPart] from a JSON map.
  factory PendingPart.fromJson(Map<String, dynamic> json) => PendingPart(pending: json["pending"] as bool);

  /// Whether this is a pending placeholder.
  final bool pending;

  @override
  Map<String, dynamic> toJson() => {"pending": pending};

  @override
  bool operator ==(Object other) => identical(this, other) || other is PendingPart && pending == other.pending;

  @override
  int get hashCode => pending.hashCode;

  @override
  String toString() => "PendingPart(pending: $pending)";
}

/// A metadata part for section markers and other metadata.
///
/// Contains metadata like `pending` and `purpose` for sections.
@immutable
class MetadataPart extends Part {
  /// Creates a new [MetadataPart].
  const MetadataPart({required this.metadata});

  /// Creates a [MetadataPart] from a JSON map.
  factory MetadataPart.fromJson(Map<String, dynamic> json) =>
      MetadataPart(metadata: json["metadata"] as Map<String, dynamic>);

  /// The metadata content.
  final Map<String, dynamic> metadata;

  @override
  Map<String, dynamic> toJson() => {"metadata": metadata};

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is MetadataPart && _mapEquals(metadata, other.metadata);

  @override
  int get hashCode => metadata.hashCode;

  @override
  String toString() => "MetadataPart(metadata: $metadata)";
}

// Helper functions for equality comparisons
bool _mapEquals<K, V>(Map<K, V>? a, Map<K, V>? b) {
  if (a == null && b == null) return true;
  if (a == null || b == null) return false;
  if (a.length != b.length) return false;
  for (final key in a.keys) {
    if (!b.containsKey(key) || a[key] != b[key]) return false;
  }
  return true;
}

bool _listEquals<T>(List<T>? a, List<T>? b) {
  if (a == null && b == null) return true;
  if (a == null || b == null) return false;
  if (a.length != b.length) return false;
  for (var i = 0; i < a.length; i++) {
    if (a[i] != b[i]) return false;
  }
  return true;
}
