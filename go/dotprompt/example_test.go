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

func TestSkipAllFailing(t *testing.T) {
	// Currently, since the Go runtime is catching up to the JS runtime implementation
	// we skip all failing tests. This test will fail because 2*2 = 4, not 5
	// but the CI/pre-commits will not complain.
	//
	// TODO: Remove this test when the runtime implementation is complete.
	assert.Equal(t, 5, Square(2), "This test should fail because 2*2 = 4, not 5")
}
