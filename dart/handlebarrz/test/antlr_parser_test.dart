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

/// Tests for the ANTLR-based Handlebars parser.
///
/// These tests verify that the ANTLR parser produces equivalent AST nodes
/// to the hand-written parser.
library;

import "package:handlebarrz/src/antlr_parser.dart";
import "package:handlebarrz/src/parser.dart";
import "package:handlebarrz/src/parser_facade.dart";
import "package:test/test.dart";

/// Helper to convert a node to a debugging string.
String _nodeToString(AstNode node) {
  switch (node) {
    case TextNode():
      return 'TextNode("${node.text}")';
    case MustacheNode():
      return "MustacheNode(path: ${node.path.path}, escaped: ${node.escaped})";
    case BlockNode():
      return "BlockNode(path: ${node.path.path}, isInverse: ${node.isInverse}, "
          "program: ${node.program.body.length} nodes, "
          'inverse: ${node.inverse?.body.length ?? "null"} nodes)';
    case CommentNode():
      return 'CommentNode("${node.text.substring(0, node.text.length.clamp(0, 20))}...")';
    case PartialNode():
      return "PartialNode(name: ${node.name})";
    default:
      return node.runtimeType.toString();
  }
}

void main() {
  group("ANTLR Parser", () {
    group("Basic expressions", () {
      test("plain text", () {
        final ast = AntlrParser.parse("Hello World");
        expect(ast.body, hasLength(1));
        expect(ast.body.first, isA<TextNode>());
        expect((ast.body.first as TextNode).text, equals("Hello World"));
      });

      test("simple variable", () {
        final ast = AntlrParser.parse("{{name}}");
        expect(ast.body, hasLength(1));
        expect(ast.body.first, isA<MustacheNode>());
        final mustache = ast.body.first as MustacheNode;
        expect(mustache.path.path, equals("name"));
        expect(mustache.escaped, isTrue);
      });

      test("unescaped variable triple braces", () {
        final ast = AntlrParser.parse("{{{content}}}");
        expect(ast.body, hasLength(1));
        expect(ast.body.first, isA<MustacheNode>());
        final mustache = ast.body.first as MustacheNode;
        expect(mustache.path.path, equals("content"));
        expect(mustache.escaped, isFalse);
      });

      test("text with variable", () {
        final ast = AntlrParser.parse("Hello {{name}}!");
        expect(ast.body, hasLength(3));
        expect((ast.body[0] as TextNode).text, equals("Hello "));
        expect((ast.body[1] as MustacheNode).path.path, equals("name"));
        expect((ast.body[2] as TextNode).text, equals("!"));
      });

      test("path expression", () {
        final ast = AntlrParser.parse("{{user.profile.name}}");
        expect(ast.body, hasLength(1));
        final mustache = ast.body.first as MustacheNode;
        expect(mustache.path.parts, equals(["user", "profile", "name"]));
      });

      test("helper with params", () {
        final ast = AntlrParser.parse('{{link "Home" url}}');
        expect(ast.body, hasLength(1));
        final mustache = ast.body.first as MustacheNode;
        expect(mustache.path.path, equals("link"));
        expect(mustache.params, hasLength(2));
        expect((mustache.params[0] as StringNode).value, equals("Home"));
        expect((mustache.params[1] as PathNode).path, equals("url"));
      });

      test("helper with hash params", () {
        final ast = AntlrParser.parse('{{input name="user" type="text"}}');
        expect(ast.body, hasLength(1));
        final mustache = ast.body.first as MustacheNode;
        expect(mustache.path.path, equals("input"));
        expect(mustache.hash["name"], isA<StringNode>());
        expect(mustache.hash["type"], isA<StringNode>());
        expect((mustache.hash["name"]! as StringNode).value, equals("user"));
        expect((mustache.hash["type"]! as StringNode).value, equals("text"));
      });
    });

    group("Block helpers", () {
      test("if block", () {
        final ast = AntlrParser.parse("{{#if condition}}yes{{/if}}");
        expect(ast.body, hasLength(1));
        expect(ast.body.first, isA<BlockNode>());
        final block = ast.body.first as BlockNode;
        expect(block.path.path, equals("if"));
        expect(block.program.body, hasLength(1));
        expect((block.program.body.first as TextNode).text, equals("yes"));
      });

      test("if-else block", () {
        final ast = AntlrParser.parse("{{#if cond}}yes{{else}}no{{/if}}");
        expect(ast.body, hasLength(1));
        final block = ast.body.first as BlockNode;
        expect(block.path.path, equals("if"));
        expect(block.program.body.first, isA<TextNode>());
        expect(block.inverse, isNotNull);
        expect(block.inverse!.body, hasLength(1));
        expect((block.inverse!.body.first as TextNode).text, equals("no"));
      });

      test("else-if chain", () {
        final ast = AntlrParser.parse("{{#if a}}one{{else if b}}two{{else}}three{{/if}}");
        expect(ast.body, hasLength(1));
        final block = ast.body.first as BlockNode;
        expect(block.path.path, equals("if"));
        expect(block.program.body.first, isA<TextNode>());
        expect(block.inverse, isNotNull);
        // The inverse should contain an else-if block
        expect(block.inverse!.body, hasLength(1));
        final elseIfBlock = block.inverse!.body.first as BlockNode;
        expect(elseIfBlock.path.path, equals("if"));
        expect(elseIfBlock.inverse, isNotNull);
      });

      test("nested blocks", () {
        final ast = AntlrParser.parse("{{#if outer}}{{#each items}}{{this}}{{/each}}{{/if}}");
        expect(ast.body, hasLength(1));
        final block = ast.body.first as BlockNode;
        expect(block.path.path, equals("if"));
        expect(block.program.body.first, isA<BlockNode>());
        final innerBlock = block.program.body.first as BlockNode;
        expect(innerBlock.path.path, equals("each"));
      });

      test("each block", () {
        final ast = AntlrParser.parse("{{#each items}}{{this}}{{/each}}");
        expect(ast.body, hasLength(1));
        final block = ast.body.first as BlockNode;
        expect(block.path.path, equals("each"));
        expect(block.params, hasLength(1));
      });

      test("each with block params", () {
        final ast = AntlrParser.parse("{{#each items as |item index|}}{{item}}{{/each}}");
        expect(ast.body, hasLength(1));
        final block = ast.body.first as BlockNode;
        expect(block.path.path, equals("each"));
        expect(block.blockParams, equals(["item", "index"]));
      });

      test("inverse block", () {
        final ast = AntlrParser.parse("{{^if condition}}no{{/if}}");
        expect(ast.body, hasLength(1));
        final block = ast.body.first as BlockNode;
        expect(block.isInverse, isTrue);
      });

      test("unless block (inverse of if)", () {
        final ast = AntlrParser.parse("{{#unless hidden}}visible{{/unless}}");
        expect(ast.body, hasLength(1));
        final block = ast.body.first as BlockNode;
        expect(block.path.path, equals("unless"));
      });

      test("with block", () {
        final ast = AntlrParser.parse("{{#with user}}{{name}}{{/with}}");
        expect(ast.body, hasLength(1));
        final block = ast.body.first as BlockNode;
        expect(block.path.path, equals("with"));
        expect(block.params, hasLength(1));
      });
    });

    group("Comments", () {
      test("simple comment", () {
        final ast = AntlrParser.parse("{{! This is a comment }}");
        expect(ast.body, hasLength(1));
        expect(ast.body.first, isA<CommentNode>());
      });

      test("long comment", () {
        final ast = AntlrParser.parse("{{!-- Long comment --}}");
        expect(ast.body, hasLength(1));
        expect(ast.body.first, isA<CommentNode>());
      });
    });

    group("Partials", () {
      test("simple partial", () {
        final ast = AntlrParser.parse("{{> header}}");
        expect(ast.body, hasLength(1));
        expect(ast.body.first, isA<PartialNode>());
        final partial = ast.body.first as PartialNode;
        expect(partial.name, equals("header"));
      });

      test("partial with context", () {
        final ast = AntlrParser.parse("{{> userCard user}}");
        expect(ast.body, hasLength(1));
        final partial = ast.body.first as PartialNode;
        expect(partial.name, equals("userCard"));
        expect(partial.context, isA<PathNode>());
      });
    });

    group("Data variables", () {
      test("@root", () {
        final ast = AntlrParser.parse("{{@root.title}}");
        expect(ast.body, hasLength(1));
        final mustache = ast.body.first as MustacheNode;
        expect(mustache.path.isData, isTrue);
        expect(mustache.path.parts, contains("root"));
      });

      test("@index", () {
        final ast = AntlrParser.parse("{{@index}}");
        expect(ast.body, hasLength(1));
        final mustache = ast.body.first as MustacheNode;
        expect(mustache.path.isData, isTrue);
      });
    });

    group("Subexpressions", () {
      test("nested helper call", () {
        final ast = AntlrParser.parse("{{outer (inner arg)}}");
        expect(ast.body, hasLength(1));
        final mustache = ast.body.first as MustacheNode;
        expect(mustache.path.path, equals("outer"));
        expect(mustache.params, hasLength(1));
        expect(mustache.params.first, isA<SubExpressionNode>());
        final subexpr = mustache.params.first as SubExpressionNode;
        expect(subexpr.path.path, equals("inner"));
      });
    });

    group("Literals", () {
      test("string literal", () {
        final ast = AntlrParser.parse('{{helper "string"}}');
        final mustache = ast.body.first as MustacheNode;
        expect(mustache.params.first, isA<StringNode>());
        expect((mustache.params.first as StringNode).value, equals("string"));
      });

      test("number literal", () {
        final ast = AntlrParser.parse("{{helper 42}}");
        final mustache = ast.body.first as MustacheNode;
        expect(mustache.params.first, isA<NumberNode>());
        expect((mustache.params.first as NumberNode).value, equals(42));
      });

      test("boolean literal", () {
        final ast = AntlrParser.parse("{{helper true}}");
        final mustache = ast.body.first as MustacheNode;
        expect(mustache.params.first, isA<BooleanNode>());
        expect((mustache.params.first as BooleanNode).value, isTrue);
      });
    });
  });

  group("Parser parity", () {
    final testCases = [
      "Hello World",
      "{{name}}",
      "{{{content}}}",
      "Hello {{name}}!",
      "{{user.profile.name}}",
      "{{#if condition}}yes{{/if}}",
      "{{#if cond}}yes{{else}}no{{/if}}",
      "{{#each items}}{{this}}{{/each}}",
      "{{> header}}",
      "{{! comment }}",
      '{{link "Home" url}}',
      '{{input name="user"}}',
    ];

    for (final template in testCases) {
      test('parity: "$template"', () {
        final result = ParserFacade.parseAndCompare(template);
        if (!result.equivalent) {
          final buffer = StringBuffer();
          final hwAst = result.handwritten;
          final antlrAst = result.antlr;
          buffer
            ..writeln("Template: $template")
            ..writeln("Handwritten body length: ${hwAst.body.length}")
            ..writeln("ANTLR body length: ${antlrAst.body.length}");
          for (var i = 0; i < hwAst.body.length; i++) {
            buffer.writeln("HW[$i]: ${_nodeToString(hwAst.body[i])}");
          }
          for (var i = 0; i < antlrAst.body.length; i++) {
            buffer.writeln("ANTLR[$i]: ${_nodeToString(antlrAst.body[i])}");
          }
          fail("ASTs should be equivalent for: $template\n$buffer");
        }
      });
    }
  });

  group("ParserFacade", () {
    test("default parser is handwritten", () {
      expect(ParserFacade.defaultParser, equals(ParserType.handwritten));
    });

    test("useAntlr=true forces ANTLR parser", () {
      final ast = ParserFacade.parse("{{name}}", useAntlr: true);
      expect(ast.body, hasLength(1));
      expect(ast.body.first, isA<MustacheNode>());
    });

    test("useAntlr=false forces handwritten parser", () {
      final ast = ParserFacade.parse("{{name}}", useAntlr: false);
      expect(ast.body, hasLength(1));
      expect(ast.body.first, isA<MustacheNode>());
    });

    test("can switch default parser", () {
      final oldDefault = ParserFacade.defaultParser;
      try {
        ParserFacade.defaultParser = ParserType.antlr;
        expect(ParserFacade.defaultParser, equals(ParserType.antlr));
      } finally {
        ParserFacade.defaultParser = oldDefault;
      }
    });
  });
}
