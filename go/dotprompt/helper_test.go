// Copyright 2025 Google LLC
// SPDX-License-Identifier: Apache-2.0

package dotprompt

import (
	"testing"

	"github.com/aymerick/raymond"
	"github.com/stretchr/testify/assert"
)

// JSON, Media, IfEquals and UnlessEquals functions cannot be tested directly.
// These functions are tested as part of spec tests present under go/test dir.
func TestRoleFn(t *testing.T) {
	role := "admin"
	expected := "<<<dotprompt:role:admin>>>"
	result := RoleFn(role)
	assert.Equal(t, raymond.SafeString(expected), result)
}

func TestHistory(t *testing.T) {
	expected := "<<<dotprompt:history>>>"
	result := History()
	assert.Equal(t, raymond.SafeString(expected), result)
}

func TestSection(t *testing.T) {
	name := "Introduction"
	expected := "<<<dotprompt:section Introduction>>>"
	result := Section(name)
	assert.Equal(t, raymond.SafeString(expected), result)
}
