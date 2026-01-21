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

	"github.com/mbleigh/raymond"
	"github.com/stretchr/testify/assert"
)

// Tests for role helper

func TestRoleFn(t *testing.T) {
	role := "admin"
	expected := "<<<dotprompt:role:admin>>>"
	result := RoleFn(role)
	assert.Equal(t, raymond.SafeString(expected), result)
}

func TestRoleFn_system(t *testing.T) {
	result := RoleFn("system")
	assert.Equal(t, raymond.SafeString("<<<dotprompt:role:system>>>"), result)
}

func TestRoleFn_user(t *testing.T) {
	result := RoleFn("user")
	assert.Equal(t, raymond.SafeString("<<<dotprompt:role:user>>>"), result)
}

func TestRoleFn_model(t *testing.T) {
	result := RoleFn("model")
	assert.Equal(t, raymond.SafeString("<<<dotprompt:role:model>>>"), result)
}

// Tests for history helper

func TestHistory(t *testing.T) {
	expected := "<<<dotprompt:history>>>"
	result := History()
	assert.Equal(t, raymond.SafeString(expected), result)
}

// Tests for section helper

func TestSection(t *testing.T) {
	name := "Introduction"
	expected := "<<<dotprompt:section Introduction>>>"
	result := Section(name)
	assert.Equal(t, raymond.SafeString(expected), result)
}

func TestSection_examples(t *testing.T) {
	result := Section("examples")
	assert.Equal(t, raymond.SafeString("<<<dotprompt:section examples>>>"), result)
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
