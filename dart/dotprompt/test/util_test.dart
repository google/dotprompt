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

import "package:dotprompt/dotprompt.dart";
import "package:test/test.dart";

void main() {
  group("validatePromptName", () {
    group("valid names", () {
      test("accepts simple name", () {
        expect(() => validatePromptName("my-prompt"), returnsNormally);
      });

      test("accepts namespaced name", () {
        expect(() => validatePromptName("org/my-prompt"), returnsNormally);
      });

      test("accepts name with underscores", () {
        expect(() => validatePromptName("my_prompt"), returnsNormally);
      });

      test("accepts name with dots in filename", () {
        expect(() => validatePromptName("my.prompt"), returnsNormally);
      });

      test("accepts deeply nested namespace", () {
        expect(() => validatePromptName("a/b/c/d"), returnsNormally);
      });

      test("accepts alphanumeric..alphanumeric pattern", () {
        expect(() => validatePromptName("a..b"), returnsNormally);
      });

      test("accepts file..txt pattern", () {
        expect(() => validatePromptName("file..txt"), returnsNormally);
      });
    });

    group("empty and whitespace", () {
      test("rejects empty string", () {
        expect(
          () => validatePromptName(""),
          throwsA(isA<ArgumentError>()),
        );
      });

      test("rejects whitespace-only string", () {
        expect(
          () => validatePromptName("   "),
          throwsA(isA<ArgumentError>()),
        );
      });
    });

    group("null byte injection (CWE-134)", () {
      test("rejects null byte", () {
        expect(
          () => validatePromptName("file\x00.txt"),
          throwsA(isA<ArgumentError>()),
        );
      });

      test("rejects null byte escape sequence", () {
        expect(
          () => validatePromptName(r"file\0.txt"),
          throwsA(isA<ArgumentError>()),
        );
      });
    });

    group("path traversal (CWE-22)", () {
      test("rejects ../", () {
        expect(
          () => validatePromptName("../secret"),
          throwsA(isA<ArgumentError>()),
        );
      });

      test("rejects ../../", () {
        expect(
          () => validatePromptName("../../etc/passwd"),
          throwsA(isA<ArgumentError>()),
        );
      });

      test("rejects .. segment", () {
        expect(
          () => validatePromptName("foo/../bar"),
          throwsA(isA<ArgumentError>()),
        );
      });

      test("rejects ./", () {
        expect(
          () => validatePromptName("./secret"),
          throwsA(isA<ArgumentError>()),
        );
      });

      test("rejects only dots segment", () {
        expect(
          () => validatePromptName("..."),
          throwsA(isA<ArgumentError>()),
        );
      });

      test("rejects ..config bypass", () {
        expect(
          () => validatePromptName("..config"),
          throwsA(isA<ArgumentError>()),
        );
      });

      test("rejects safe.. bypass", () {
        expect(
          () => validatePromptName("safe.."),
          throwsA(isA<ArgumentError>()),
        );
      });
    });

    group("absolute paths", () {
      test("rejects Unix absolute path", () {
        expect(
          () => validatePromptName("/etc/passwd"),
          throwsA(isA<ArgumentError>()),
        );
      });

      test("rejects Windows drive letter", () {
        expect(
          () => validatePromptName("C:/windows"),
          throwsA(isA<ArgumentError>()),
        );
      });

      test("rejects bare drive letter", () {
        expect(
          () => validatePromptName("C:"),
          throwsA(isA<ArgumentError>()),
        );
      });
    });

    group("UNC paths", () {
      test("rejects UNC path with forward slashes", () {
        expect(
          () => validatePromptName("//server/share"),
          throwsA(isA<ArgumentError>()),
        );
      });

      test("rejects UNC path with backslashes", () {
        expect(
          () => validatePromptName(r"\\server\share"),
          throwsA(isA<ArgumentError>()),
        );
      });
    });

    group("trailing slash", () {
      test("rejects trailing slash", () {
        expect(
          () => validatePromptName("prompt/"),
          throwsA(isA<ArgumentError>()),
        );
      });
    });

    group("URL-encoded bypasses", () {
      test("rejects URL-encoded path traversal", () {
        expect(
          () => validatePromptName("%2e%2e/%2e%2e"),
          throwsA(isA<ArgumentError>()),
        );
      });

      test("rejects double-encoded path traversal", () {
        expect(
          () => validatePromptName("%252e%252e"),
          throwsA(isA<ArgumentError>()),
        );
      });
    });

    group("Unicode homograph attacks (CWE-156)", () {
      test("rejects non-ASCII characters", () {
        expect(
          () => validatePromptName("ｆｉｌｅ"),
          throwsA(isA<ArgumentError>()),
        );
      });

      test("rejects mixed ASCII and non-ASCII", () {
        expect(
          () => validatePromptName("file\u200B"),
          throwsA(isA<ArgumentError>()),
        );
      });

      test("rejects Cyrillic lookalikes", () {
        // Cyrillic "а" (U+0430) looks like Latin "a"
        expect(
          () => validatePromptName("p\u0430ssword"),
          throwsA(isA<ArgumentError>()),
        );
      });
    });
  });
}
