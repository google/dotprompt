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

/// Unit tests for core types.
library;

import "package:dotprompt/dotprompt.dart";
import "package:test/test.dart";

void main() {
  group("Role", () {
    test("fromString parses valid roles", () {
      expect(Role.fromString("user"), equals(Role.user));
      expect(Role.fromString("model"), equals(Role.model));
      expect(Role.fromString("system"), equals(Role.system));
      expect(Role.fromString("tool"), equals(Role.tool));
    });

    test("fromString is case insensitive", () {
      expect(Role.fromString("USER"), equals(Role.user));
      expect(Role.fromString("Model"), equals(Role.model));
    });

    test("fromString throws on unknown role", () {
      expect(() => Role.fromString("unknown"), throwsA(isA<ArgumentError>()));
    });

    test("toString returns value", () {
      expect(Role.user.toString(), equals("user"));
      expect(Role.model.toString(), equals("model"));
    });
  });

  group("DataArgument", () {
    test("creates with input", () {
      const data = DataArgument(input: {"name": "Alice"});
      expect(data.input?["name"], equals("Alice"));
    });

    test("serializes to JSON", () {
      const data = DataArgument(input: {"name": "Alice"});
      final json = data.toJson();
      expect((json["input"] as Map)["name"], equals("Alice"));
    });

    test("deserializes from JSON", () {
      final json = {
        "input": {"name": "Alice"},
      };
      final data = DataArgument.fromJson(json);
      expect(data.input?["name"], equals("Alice"));
    });

    test("copyWith creates modified copy", () {
      const original = DataArgument(input: {"name": "Alice"});
      final modified = original.copyWith(input: {"name": "Bob"});
      expect(original.input?["name"], equals("Alice"));
      expect(modified.input?["name"], equals("Bob"));
    });
  });

  group("ContextData", () {
    test("accesses state", () {
      const context = ContextData(state: {"count": 42});
      expect(context.state?["count"], equals(42));
      expect((context["state"] as Map)["count"], equals(42));
    });

    test("accesses additional data", () {
      final context = ContextData.fromJson(const {
        "state": {"count": 42},
        "auth": {"email": "test@example.com"},
      });
      expect((context["auth"] as Map)["email"], equals("test@example.com"));
    });

    test("serializes to JSON", () {
      const context = ContextData(
        state: {"count": 42},
        data: {
          "auth": {"email": "test@example.com"},
        },
      );
      final json = context.toJson();
      expect((json["state"] as Map)["count"], equals(42));
      expect((json["auth"] as Map)["email"], equals("test@example.com"));
    });
  });

  group("Message", () {
    test("creates with role and content", () {
      const message = Message(
        role: Role.user,
        content: [TextPart(text: "Hello!")],
      );
      expect(message.role, equals(Role.user));
      expect(message.content.length, equals(1));
    });

    test("serializes to JSON", () {
      const message = Message(
        role: Role.user,
        content: [TextPart(text: "Hello!")],
      );
      final json = message.toJson();
      expect(json["role"], equals("user"));
      expect(((json["content"] as List)[0] as Map)["text"], equals("Hello!"));
    });

    test("deserializes from JSON", () {
      final json = {
        "role": "model",
        "content": [
          {"text": "Hi there!"},
        ],
      };
      final message = Message.fromJson(json);
      expect(message.role, equals(Role.model));
      expect((message.content.first as TextPart).text, equals("Hi there!"));
    });
  });

  group("Part", () {
    group("TextPart", () {
      test("creates with text", () {
        const part = TextPart(text: "Hello!");
        expect(part.text, equals("Hello!"));
      });

      test("serializes to JSON", () {
        const part = TextPart(text: "Hello!");
        expect(part.toJson(), equals({"text": "Hello!"}));
      });

      test("deserializes from JSON", () {
        final json = {"text": "Hello!"};
        final part = Part.fromJson(json);
        expect(part, isA<TextPart>());
        expect((part as TextPart).text, equals("Hello!"));
      });
    });

    group("MediaPart", () {
      test("creates with media content", () {
        const part = MediaPart(
          media: MediaContent(url: "image.png", contentType: "image/png"),
        );
        expect(part.media.url, equals("image.png"));
        expect(part.media.contentType, equals("image/png"));
      });

      test("serializes to JSON", () {
        const part = MediaPart(
          media: MediaContent(url: "image.png", contentType: "image/png"),
        );
        final json = part.toJson();
        expect((json["media"] as Map)["url"], equals("image.png"));
        expect((json["media"] as Map)["contentType"], equals("image/png"));
      });

      test("deserializes from JSON", () {
        final json = {
          "media": {"url": "image.png", "contentType": "image/png"},
        };
        final part = Part.fromJson(json);
        expect(part, isA<MediaPart>());
        expect((part as MediaPart).media.url, equals("image.png"));
      });
    });

    group("ToolRequestPart", () {
      test("creates with tool request", () {
        const part = ToolRequestPart(
          toolRequest: ToolRequest(
            name: "search",
            ref: "call_123",
            input: {"query": "weather"},
          ),
        );
        expect(part.toolRequest.name, equals("search"));
        expect(part.toolRequest.ref, equals("call_123"));
        expect(part.toolRequest.input?["query"], equals("weather"));
      });

      test("serializes and deserializes", () {
        const part = ToolRequestPart(
          toolRequest: ToolRequest(name: "search", ref: "call_123"),
        );
        final json = part.toJson();
        final restored = Part.fromJson(json);
        expect(restored, isA<ToolRequestPart>());
        expect(
          (restored as ToolRequestPart).toolRequest.name,
          equals("search"),
        );
      });
    });

    group("ToolResponsePart", () {
      test("creates with tool response", () {
        const part = ToolResponsePart(
          toolResponse: ToolResponse(
            name: "search",
            ref: "call_123",
            output: {"results": <String>[]},
          ),
        );
        expect(part.toolResponse.name, equals("search"));
        expect(part.toolResponse.output, isA<Map<String, dynamic>>());
      });
    });
  });
}
