// Copyright 2025 Google LLC
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

package dotprompt

import (
	"testing"
)

// Note: RoleFn requires raymond.Options which is complex to mock in unit tests.
// RoleFn is thoroughly tested via the spec tests in go/test/spec_test.go which
// exercise it through the full template rendering pipeline (see spec/helpers/role.yaml
// and spec/helpers/role_metadata.yaml).

// Tests for history helper

func TestHistory(t *testing.T) {
	expected := "<<<dotprompt:history>>>"
	result := History()
	if string(result) != expected {
		t.Errorf("History() = %q, want %q", result, expected)
	}
}

// Tests for section helper

func TestSection(t *testing.T) {
	name := "Introduction"
	expected := "<<<dotprompt:section Introduction>>>"
	result := Section(name)
	if string(result) != expected {
		t.Errorf("Section(%q) = %q, want %q", name, result, expected)
	}
}

func TestSection_examples(t *testing.T) {
	result := Section("examples")
	expected := "<<<dotprompt:section examples>>>"
	if string(result) != expected {
		t.Errorf("Section(\"examples\") = %q, want %q", result, expected)
	}
}

// Note: JSON, Media, IfEquals, UnlessEquals helpers require raymond.Options
// which is complex to mock in unit tests. These functions are thoroughly tested
// via the spec tests in go/test/spec_test.go which exercise them through the
// full template rendering pipeline.
//
// The spec tests cover:
// - json: basic objects, arrays, indent variations, nested objects, empty values
// - media: url only, url + contentType
// - ifEquals/unlessEquals: int/string equality, boolean, null comparisons, type safety
