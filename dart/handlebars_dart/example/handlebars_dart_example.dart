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

void main() {
  final hb = Handlebars()
    // A custom helper that upper-cases its first argument.
    ..registerHelper("upper", (args, options) => args.first.toString().toUpperCase())
    // A reusable partial.
    ..registerPartial("greeting", "Hello {{upper name}}!");

  // Compose a template that uses the partial, a block helper, and iteration.
  final template = hb.compile(
    "{{> greeting}}\n"
    "{{#if items}}Your items:\n{{#each items}}  {{@index}}. {{this}}\n{{/each}}{{else}}No items yet.\n{{/if}}",
  );

  final output = template({
    "name": "world",
    "items": ["apples", "oranges", "pears"],
  });

  // ignore: avoid_print
  print(output);
}
