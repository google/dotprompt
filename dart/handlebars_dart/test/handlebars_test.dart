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

import "package:handlebars_dart/handlebars_dart.dart";
import "package:test/test.dart";

void main() {
  group("Handlebars", () {
    late Handlebars hb;

    setUp(() {
      hb = Handlebars();
    });

    group("variable substitution", () {
      test("simple variable", () {
        final template = hb.compile("Hello {{name}}!");
        expect(template({"name": "World"}), equals("Hello World!"));
      });

      test("dot notation path", () {
        final template = hb.compile("Hello {{user.name}}!");
        expect(
          template({
            "user": {"name": "Alice"},
          }),
          equals("Hello Alice!"),
        );
      });

      test("missing variable returns empty", () {
        final template = hb.compile("Hello {{name}}!");
        expect(template(<String, dynamic>{}), equals("Hello !"));
      });

      test("this context with dot", () {
        final template = hb.compile("Value: {{.}}");
        expect(template("hello"), equals("Value: hello"));
      });

      test("slash path notation", () {
        final template = hb.compile("{{user/name}}");
        expect(
          template({
            "user": {"name": "Alice"},
          }),
          equals("Alice"),
        );
      });

      test("mixed path separators", () {
        final template = hb.compile("{{a.b/c.d}}");
        expect(
          template({
            "a": {
              "b": {
                "c": {"d": "value"},
              },
            },
          }),
          equals("value"),
        );
      });
    });

    group("HTML escaping", () {
      test("escapes HTML by default", () {
        final template = hb.compile("{{content}}");
        expect(
          template({"content": "<script>alert('xss')</script>"}),
          equals("&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"),
        );
      });

      test("triple braces disable escaping", () {
        final template = hb.compile("{{{content}}}");
        expect(template({"content": "<b>bold</b>"}), equals("<b>bold</b>"));
      });
    });

    group("helpers", () {
      test("simple helper with argument", () {
        hb.registerHelper("upper", (args, options) => args[0].toString().toUpperCase());

        final template = hb.compile("{{upper name}}");
        expect(template({"name": "world"}), equals("WORLD"));
      });

      test("helper with string literal argument", () {
        hb.registerHelper("greet", (args, options) => "Hello, ${args[0]}!");

        final template = hb.compile('{{greet "Alice"}}');
        expect(template(<String, dynamic>{}), equals("Hello, Alice!"));
      });

      test("helper with hash arguments", () {
        hb.registerHelper("link", (args, options) {
          final url = options.hash["url"];
          final text = args.isNotEmpty ? args[0] : "click";
          return SafeString('<a href="$url">$text</a>');
        });

        final template = hb.compile('{{link "Go" url="https://example.com"}}');
        expect(template(<String, dynamic>{}), equals('<a href="https://example.com">Go</a>'));
      });

      test("helper returning SafeString bypasses escaping", () {
        hb.registerHelper("bold", (args, options) => SafeString("<b>${args[0]}</b>"));

        final template = hb.compile("{{bold name}}");
        expect(template({"name": "test"}), equals("<b>test</b>"));
      });
    });

    group("block helpers", () {
      test("if block - truthy", () {
        final template = hb.compile("{{#if show}}visible{{/if}}");
        expect(template({"show": true}), equals("visible"));
      });

      test("if block - falsy", () {
        final template = hb.compile("{{#if show}}visible{{/if}}");
        expect(template({"show": false}), equals(""));
      });

      test("if/else block", () {
        final template = hb.compile("{{#if show}}yes{{else}}no{{/if}}");
        expect(template({"show": true}), equals("yes"));
        expect(template({"show": false}), equals("no"));
      });

      test("unless block", () {
        final template = hb.compile("{{#unless hidden}}visible{{/unless}}");
        expect(template({"hidden": false}), equals("visible"));
        expect(template({"hidden": true}), equals(""));
      });

      test("each block with list", () {
        final template = hb.compile("{{#each items}}{{.}} {{/each}}");
        expect(
          template({
            "items": ["a", "b", "c"],
          }),
          equals("a b c "),
        );
      });

      test("each block with index", () {
        final template = hb.compile("{{#each items}}{{@index}}:{{.}} {{/each}}");
        expect(
          template({
            "items": ["a", "b"],
          }),
          equals("0:a 1:b "),
        );
      });

      test("with block", () {
        final template = hb.compile("{{#with user}}{{name}}{{/with}}");
        expect(
          template({
            "user": {"name": "Alice"},
          }),
          equals("Alice"),
        );
      });

      test("each block with @first and @last", () {
        final template = hb.compile("{{#each items}}{{#if @first}}[{{/if}}{{.}}{{#if @last}}]{{/if}}{{/each}}");
        expect(
          template({
            "items": ["a", "b", "c"],
          }),
          equals("[abc]"),
        );
      });

      test("each block with objects and @key", () {
        final template = hb.compile("{{#each person}}{{@key}}={{.}} {{/each}}");
        expect(
          template({
            "person": {"name": "Alice", "age": "30"},
          }),
          anyOf([
            equals("name=Alice age=30 "),
            equals("age=30 name=Alice "), // Map order may vary
          ]),
        );
      });

      test("nested each blocks", () {
        final template = hb.compile("{{#each rows}}{{#each .}}{{.}}{{/each}}|{{/each}}");
        expect(
          template({
            "rows": [
              ["a", "b"],
              ["c", "d"],
            ],
          }),
          equals("ab|cd|"),
        );
      });

      test("each block with else", () {
        final template = hb.compile("{{#each items}}{{.}}{{else}}empty{{/each}}");
        expect(template({"items": <dynamic>[]}), equals("empty"));
        expect(
          template({
            "items": ["a"],
          }),
          equals("a"),
        );
      });
    });

    group("custom block helpers", () {
      test("ifEquals helper", () {
        hb.registerHelper("ifEquals", (args, options) {
          if (args[0] == args[1]) {
            return options.fn(options.context);
          } else {
            return options.inverse(options.context);
          }
        });

        final template = hb.compile('{{#ifEquals status "active"}}Active{{else}}Inactive{{/ifEquals}}');
        expect(template({"status": "active"}), equals("Active"));
        expect(template({"status": "pending"}), equals("Inactive"));
      });

      test("unlessEquals helper", () {
        hb.registerHelper("unlessEquals", (args, options) {
          if (args[0] != args[1]) {
            return options.fn(options.context);
          } else {
            return options.inverse(options.context);
          }
        });

        final template = hb.compile('{{#unlessEquals status "active"}}Not Active{{else}}Active{{/unlessEquals}}');
        expect(template({"status": "pending"}), equals("Not Active"));
        expect(template({"status": "active"}), equals("Active"));
      });
    });

    group("partials", () {
      test("simple partial", () {
        hb.registerPartial("greeting", "Hello {{name}}!");

        final template = hb.compile("{{> greeting}}");
        expect(template({"name": "World"}), equals("Hello World!"));
      });

      test("partial with context", () {
        hb.registerPartial("userCard", "Name: {{name}}, Email: {{email}}");

        final template = hb.compile("{{> userCard user}}");
        expect(
          template({
            "user": {"name": "Alice", "email": "alice@example.com"},
          }),
          equals("Name: Alice, Email: alice@example.com"),
        );
      });
    });

    group("comments", () {
      test("short comment is ignored", () {
        final template = hb.compile("Hello {{! this is a comment }}World");
        expect(template(<String, dynamic>{}), equals("Hello World"));
      });

      test("long comment is ignored", () {
        final template = hb.compile("Hello {{!-- long comment --}}World");
        expect(template(<String, dynamic>{}), equals("Hello World"));
      });
    });

    group("dotprompt helpers", () {
      test("role helper", () {
        hb.registerHelper("role", (args, options) => SafeString("<<<dotprompt:role:${args[0]}>>>"));

        final template = hb.compile('{{role "system"}}This is system');
        expect(template(<String, dynamic>{}), equals("<<<dotprompt:role:system>>>This is system"));
      });

      test("history helper", () {
        hb.registerHelper("history", (args, options) => const SafeString("<<<dotprompt:history>>>"));

        final template = hb.compile("Before {{history}} After");
        expect(template(<String, dynamic>{}), equals("Before <<<dotprompt:history>>> After"));
      });

      test("media helper with hash args", () {
        hb.registerHelper("media", (args, options) {
          final url = options.hash["url"];
          final contentType = (options.hash["contentType"] as String?) ?? "";
          return SafeString("<<<dotprompt:media:url $url${contentType.isNotEmpty ? " $contentType" : ""}>>>");
        });

        final template = hb.compile('{{media url="https://example.com/image.png" contentType="image/png"}}');
        expect(
          template(<String, dynamic>{}),
          equals("<<<dotprompt:media:url https://example.com/image.png image/png>>>"),
        );
      });

      test("section helper", () {
        hb.registerHelper("section", (args, options) => SafeString("<<<dotprompt:section ${args[0]}>>>"));

        final template = hb.compile('{{section "code"}}');
        expect(template(<String, dynamic>{}), equals("<<<dotprompt:section code>>>"));
      });

      test("json helper", () {
        hb.registerHelper("json", (args, options) => SafeString(args[0].toString()));

        final template = hb.compile("{{json data}}");
        expect(
          template({
            "data": {"key": "value"},
          }),
          equals("{key: value}"),
        );
      });
    });

    group("escape sequences", () {
      test("backslash-brace outputs literal braces", () {
        // \{{ should output literal {{
        const source = r"Show \{{name}} literally";
        final template = hb.compile(source);
        expect(template({"name": "World"}), equals("Show {{name}} literally"));
      });

      test("double backslash before variable is literal", () {
        // \\ is not a special escape in Handlebars, so \\{{name}} outputs \\World
        final template = hb.compile(r"\\{{name}}");
        expect(template({"name": "World"}), equals(r"\\World"));
      });

      test("escape at end of text", () {
        // \{{ at the end should output {{
        final template = hb.compile(r"End: \{{");
        expect(template(<String, dynamic>{}), equals("End: {{"));
      });
    });

    group("ampersand unescaped", () {
      test("{{&var}} disables escaping", () {
        final template = hb.compile("{{&content}}");
        expect(template({"content": "<b>bold</b>"}), equals("<b>bold</b>"));
      });
    });

    group("whitespace control", () {
      test("{{~var}} strips leading whitespace", () {
        final template = hb.compile("Hello   {{~name}}!");
        expect(template({"name": "World"}), equals("HelloWorld!"));
      });

      test("{{var~}} strips trailing whitespace", () {
        final template = hb.compile("{{name~}}   World!");
        expect(template({"name": "Hello"}), equals("HelloWorld!"));
      });

      test("{{~var~}} strips both", () {
        final template = hb.compile("Hello   {{~name~}}   World");
        expect(template({"name": "Beautiful"}), equals("HelloBeautifulWorld"));
      });

      test("{{~#if}}...{{/if~}} strips around block", () {
        final template = hb.compile("Hello   {{~#if show}}Visible{{/if~}}   World");
        expect(template({"show": true}), equals("HelloVisibleWorld"));
        expect(template({"show": false}), equals("HelloWorld"));
      });

      test("whitespace control in each loop", () {
        // Block-level whitespace control is more complex and applies to content
        // inside the block. This is a simpler test of adjacent text stripping.
        final template = hb.compile("Items: {{#each items}}{{.}}{{/each~}}   Done");
        expect(
          template({
            "items": ["a", "b"],
          }),
          equals("Items: abDone"),
        );
      });
    });

    group("subexpressions", () {
      test("basic subexpression", () {
        hb
          ..registerHelper("upper", (args, options) => args[0].toString().toUpperCase())
          ..registerHelper("wrap", (args, options) => "[${args[0]}]");

        final template = hb.compile("{{wrap (upper name)}}");
        expect(template({"name": "hello"}), equals("[HELLO]"));
      });

      test("nested subexpressions", () {
        hb
          ..registerHelper("add", (args, options) => (args[0] as num) + (args[1] as num))
          ..registerHelper("mult", (args, options) => (args[0] as num) * (args[1] as num));

        // (2 + 3) * 4 = 20
        final template = hb.compile("{{mult (add 2 3) 4}}");
        expect(template(<String, dynamic>{}), equals("20"));
      });

      test("subexpression with hash args", () {
        hb
          ..registerHelper("format", (args, options) {
            final prefix = options.hash["prefix"] ?? "";
            return "$prefix${args[0]}";
          })
          ..registerHelper("wrap", (args, options) => SafeString("<${args[0]}>"));

        final template = hb.compile('{{wrap (format name prefix="Dr. ")}}');
        expect(template({"name": "Smith"}), equals("<Dr. Smith>"));
      });
    });

    group("data variables", () {
      test("@root accesses root context", () {
        final template = hb.compile("{{#with user}}{{name}} from {{@root.company}}{{/with}}");
        expect(
          template({
            "user": {"name": "Alice"},
            "company": "Acme",
          }),
          equals("Alice from Acme"),
        );
      });

      test("@index in nested each", () {
        final template = hb.compile("{{#each outer}}{{@index}}:[{{#each .}}{{@index}}{{/each}}]{{/each}}");
        expect(
          template({
            "outer": [
              ["a"],
              ["b", "c"],
            ],
          }),
          equals("0:[0]1:[01]"),
        );
      });
    });

    group("parent context", () {
      test("../name accesses parent context in each", () {
        final template = hb.compile("{{#each items}}{{.}}-{{../prefix}}{{/each}}");
        expect(
          template({
            "prefix": "X",
            "items": ["a", "b"],
          }),
          equals("a-Xb-X"),
        );
      });

      test("../name accesses parent context in with", () {
        final template = hb.compile("{{#with person}}{{name}} works at {{../company}}{{/with}}");
        expect(
          template({
            "company": "Acme",
            "person": {"name": "Alice"},
          }),
          equals("Alice works at Acme"),
        );
      });

      test("nested ../ accesses grandparent context", () {
        final template = hb.compile(
          "{{#with level1}}{{#with level2}}{{value}}-{{../name}}-{{../../root}}{{/with}}{{/with}}",
        );
        expect(
          template({
            "root": "ROOT",
            "level1": {
              "name": "L1",
              "level2": {"value": "L2"},
            },
          }),
          equals("L2-L1-ROOT"),
        );
      });

      test("../value in each loop with primitive values", () {
        final template = hb.compile("{{#each items}}Item {{.}} from {{../source}}; {{/each}}");
        expect(
          template({
            "source": "data",
            "items": ["a", "b"],
          }),
          equals("Item a from data; Item b from data; "),
        );
      });
    });

    group("built-in helpers", () {
      test("lookup helper with map", () {
        final template = hb.compile("{{lookup person name}}");
        expect(
          template({
            "person": {"Alice": "Engineer", "Bob": "Manager"},
            "name": "Alice",
          }),
          equals("Engineer"),
        );
      });

      test("lookup helper with list", () {
        final template = hb.compile("{{lookup items 1}}");
        expect(
          template({
            "items": ["a", "b", "c"],
          }),
          equals("b"),
        );
      });

      test("lookup helper with list and string index", () {
        final template = hb.compile("{{lookup items idx}}");
        expect(
          template({
            "items": ["a", "b", "c"],
            "idx": "2",
          }),
          equals("c"),
        );
      });

      test("lookup helper returns empty for missing key", () {
        final template = hb.compile("{{lookup person missing}}");
        expect(
          template({
            "person": {"name": "Alice"},
            "missing": "nonexistent",
          }),
          equals(""),
        );
      });

      test("log helper outputs to console and returns empty", () {
        // log helper returns empty string but prints to console
        final template = hb.compile("Value: {{log name}}end");
        expect(template({"name": "test"}), equals("Value: end"));
      });
    });

    group("block params", () {
      test("each with block params - item only", () {
        final template = hb.compile("{{#each items as |item|}}{{item}};{{/each}}");
        expect(
          template({
            "items": ["a", "b", "c"],
          }),
          equals("a;b;c;"),
        );
      });

      test("each with block params - item and index", () {
        final template = hb.compile("{{#each items as |item index|}}{{index}}:{{item}};{{/each}}");
        expect(
          template({
            "items": ["a", "b", "c"],
          }),
          equals("0:a;1:b;2:c;"),
        );
      });

      test("each over object with block params - value and key", () {
        final template = hb.compile("{{#each obj as |val key|}}{{key}}={{val}};{{/each}}");
        expect(
          template({
            "obj": {"x": 1, "y": 2},
          }),
          equals("x=1;y=2;"),
        );
      });
    });

    group("raw blocks", () {
      test("raw block outputs content literally", () {
        final template = hb.compile("Before {{{{raw}}}}{{name}} is literal{{{{/raw}}}} After");
        expect(template({"name": "World"}), equals("Before {{name}} is literal After"));
      });
    });

    group("partial blocks", () {
      test("partial block uses partial if found", () {
        hb.registerPartial("myPartial", "PARTIAL CONTENT");
        final template = hb.compile("{{#> myPartial}}Default{{/myPartial}}");
        expect(template(<String, dynamic>{}), equals("PARTIAL CONTENT"));
      });

      test("partial block uses default content if partial not found", () {
        final template = hb.compile("{{#> missingPartial}}Default Content{{/missingPartial}}");
        expect(template(<String, dynamic>{}), equals("Default Content"));
      });
    });

    group("inline partials", () {
      test("defines and uses inline partial", () {
        final template = hb.compile('''
{{#*inline "myPartial"}}Hello {{name}}!{{/inline}}
{{> myPartial}}''');
        expect(template({"name": "World"}).trim(), equals("Hello World!"));
      });

      test("inline partial can be used multiple times", () {
        final template = hb.compile('''
{{#*inline "greeting"}}Hi {{name}}{{/inline}}
{{> greeting}} and {{> greeting}}''');
        expect(template({"name": "Alice"}).trim(), equals("Hi Alice and Hi Alice"));
      });

      test("inline partial with different contexts", () {
        final template = hb.compile('''
{{#*inline "userCard"}}<div>{{name}}</div>{{/inline}}
{{#each users}}{{> userCard}}{{/each}}''');
        expect(
          template({
            "users": [
              {"name": "Alice"},
              {"name": "Bob"},
            ],
          }).trim(),
          equals("<div>Alice</div><div>Bob</div>"),
        );
      });

      test("inline partial overrides registered partial", () {
        hb.registerPartial("myPartial", "REGISTERED");
        final template = hb.compile('''
{{#*inline "myPartial"}}INLINE{{/inline}}
{{> myPartial}}''');
        // Inline partial should take precedence since it's defined at render time
        expect(template(<String, dynamic>{}).trim(), equals("INLINE"));
      });
    });

    group("literals", () {
      test("boolean literal true", () {
        hb.registerHelper("showBool", (args, options) => args[0] == true ? "yes" : "no");

        final template = hb.compile("{{showBool true}}");
        expect(template(<String, dynamic>{}), equals("yes"));
      });

      test("boolean literal false", () {
        hb.registerHelper("showBool", (args, options) => args[0] == false ? "yes" : "no");

        final template = hb.compile("{{showBool false}}");
        expect(template(<String, dynamic>{}), equals("yes"));
      });

      test("number literals", () {
        hb.registerHelper("add", (args, options) => (args[0] as num) + (args[1] as num));

        final template = hb.compile("{{add 10 20}}");
        expect(template(<String, dynamic>{}), equals("30"));
      });

      test("negative number literal", () {
        hb.registerHelper("add", (args, options) => (args[0] as num) + (args[1] as num));

        final template = hb.compile("{{add 10 -5}}");
        expect(template(<String, dynamic>{}), equals("5"));
      });

      test("string literals with single quotes", () {
        hb.registerHelper("greet", (args, options) => "Hi ${args[0]}!");

        final template = hb.compile("{{greet 'world'}}");
        expect(template(<String, dynamic>{}), equals("Hi world!"));
      });
    });

    group("edge cases", () {
      test("deeply nested path", () {
        final template = hb.compile("{{a.b.c.d.e}}");
        expect(
          template({
            "a": {
              "b": {
                "c": {
                  "d": {"e": "deep"},
                },
              },
            },
          }),
          equals("deep"),
        );
      });

      test("if with else chain", () {
        final template = hb.compile("{{#if a}}A{{else}}{{#if b}}B{{else}}C{{/if}}{{/if}}");
        expect(template({"a": true}), equals("A"));
        expect(template({"b": true}), equals("B"));
        expect(template({"a": false, "b": false}), equals("C"));
      });

      test("empty string is falsy in if", () {
        final template = hb.compile("{{#if val}}yes{{else}}no{{/if}}");
        expect(template({"val": ""}), equals("no"));
        expect(template({"val": "x"}), equals("yes"));
      });

      test("zero is falsy in if", () {
        // Handlebars treats 0 as falsy (same as JavaScript)
        final template = hb.compile("{{#if val}}yes{{else}}no{{/if}}");
        expect(template({"val": 0}), equals("no"));
      });

      test("null is falsy in if", () {
        final template = hb.compile("{{#if val}}yes{{else}}no{{/if}}");
        expect(template({"val": null}), equals("no"));
      });

      test("empty array is falsy in if", () {
        final template = hb.compile("{{#if items}}yes{{else}}no{{/if}}");
        expect(template({"items": <dynamic>[]}), equals("no"));
        expect(
          template({
            "items": [1],
          }),
          equals("yes"),
        );
      });
    });

    group("strict mode", () {
      late Handlebars strictHb;

      setUp(() {
        strictHb = Handlebars(strict: true);
      });

      test("throws on undefined variable", () {
        final template = strictHb.compile("Hello {{name}}!");
        expect(() => template(<String, dynamic>{}), throwsA(isA<StrictModeException>()));
      });

      test("throws on undefined nested path", () {
        final template = strictHb.compile("{{user.profile.name}}");
        expect(() => template({"user": <String, dynamic>{}}), throwsA(isA<StrictModeException>()));
      });

      test("throws on undefined path segment", () {
        final template = strictHb.compile("{{user.name}}");
        expect(() => template(<String, dynamic>{}), throwsA(isA<StrictModeException>()));
      });

      test("does not throw for defined variables", () {
        final template = strictHb.compile("Hello {{name}}!");
        expect(template({"name": "World"}), equals("Hello World!"));
      });

      test("does not throw for null values that exist", () {
        final template = strictHb.compile("{{#if name}}yes{{else}}no{{/if}}");
        // The key exists but is null - this is allowed
        expect(template({"name": null}), equals("no"));
      });

      test("non-strict mode returns empty for missing", () {
        final nonStrict = Handlebars(strict: false);
        final template = nonStrict.compile("Hello {{name}}!");
        expect(template(<String, dynamic>{}), equals("Hello !"));
      });

      test("exception contains path info", () {
        final template = strictHb.compile("{{user.name}}");
        try {
          template(<String, dynamic>{});
          fail("Should have thrown");
        } on StrictModeException catch (e) {
          expect(e.path, equals("user.name"));
          expect(e.message, contains("is not defined"));
        }
      });
    });
  });
}
