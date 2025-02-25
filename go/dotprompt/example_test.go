// Copyright 2025 Google LLC
// SPDX-License-Identifier: Apache-2.0

package dotprompt

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

// Square computes the square of a number.
func Square(n int) int {
	return n * n
}

func TestSquare(t *testing.T) {
	assert.Equal(t, 4, Square(2))
}
