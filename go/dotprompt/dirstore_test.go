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

package dotprompt

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestDirStore(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := NewDirStore(tmpDir)
	require.NoError(t, err)

	t.Run("Save and Load Simple", func(t *testing.T) {
		prompt := PromptData{
			PromptRef: PromptRef{
				Name: "simple",
			},
			Source: "simple content",
		}
		err := store.Save(prompt)
		assert.NoError(t, err)

		// Verify file exists
		content, err := os.ReadFile(filepath.Join(tmpDir, "simple.prompt"))
		assert.NoError(t, err)
		assert.Equal(t, "simple content", string(content))

		loaded, err := store.Load("simple", LoadPromptOptions{})
		assert.NoError(t, err)
		assert.Equal(t, "simple content", loaded.Source)
		assert.Equal(t, "simple", loaded.Name)
		assert.Empty(t, loaded.Variant)
		assert.NotEmpty(t, loaded.Version)
	})

	t.Run("Save and Load Variant", func(t *testing.T) {
		prompt := PromptData{
			PromptRef: PromptRef{
				Name:    "variant-test",
				Variant: "v1",
			},
			Source: "variant content",
		}
		err := store.Save(prompt)
		assert.NoError(t, err)

		loaded, err := store.Load("variant-test", LoadPromptOptions{Variant: "v1"})
		assert.NoError(t, err)
		assert.Equal(t, "variant content", loaded.Source)
		assert.Equal(t, "v1", loaded.Variant)
	})

	t.Run("List Prompts", func(t *testing.T) {
		// Cleanup
		if err := os.RemoveAll(tmpDir); err != nil {
			t.Fatal(err)
		}
		if err := os.Mkdir(tmpDir, 0755); err != nil {
			t.Fatal(err)
		}

		prompts := []PromptData{
			{PromptRef: PromptRef{Name: "a"}},
			{PromptRef: PromptRef{Name: "b"}},
			{PromptRef: PromptRef{Name: "c", Variant: "v1"}},
		}
		for _, p := range prompts {
			err := store.Save(p)
			if err != nil {
				t.Fatal(err)
			}
		}

		list, err := store.List(ListPromptsOptions{})
		assert.NoError(t, err)
		assert.Len(t, list.Items, 3)

		// sort order is a, b, c.v1
		assert.Equal(t, "a", list.Items[0].Name)
		assert.Equal(t, "b", list.Items[1].Name)
		assert.Equal(t, "c", list.Items[2].Name)
		assert.Equal(t, "v1", list.Items[2].Variant)
	})

	t.Run("List with Variant Filter", func(t *testing.T) {
		options := ListPromptsOptions{Variant: "v1"}
		list, err := store.List(options)
		assert.NoError(t, err)
		assert.Len(t, list.Items, 1)
		assert.Equal(t, "c", list.Items[0].Name)
		assert.Equal(t, "v1", list.Items[0].Variant)
	})

	t.Run("Partials", func(t *testing.T) {
		partialPath := filepath.Join(tmpDir, "_mypartial.prompt")
		err := os.WriteFile(partialPath, []byte("partial content"), 0644)
		require.NoError(t, err)

		loaded, err := store.LoadPartial("mypartial", LoadPartialOptions{})
		assert.NoError(t, err)
		assert.Equal(t, "partial content", loaded.Source)

		list, err := store.ListPartials(ListPartialsOptions{})
		assert.NoError(t, err)
		found := false
		for _, p := range list.Items {
			if p.Name == "mypartial" {
				found = true
				break
			}
		}
		assert.True(t, found, "partial should be listed")
	})

	t.Run("Delete", func(t *testing.T) {
		promptName := "to-delete"
		err := store.Save(PromptData{PromptRef: PromptRef{Name: promptName}, Source: "x"})
		require.NoError(t, err)

		err = store.Delete(promptName, PromptStoreDeleteOptions{})
		assert.NoError(t, err)

		_, err = store.Load(promptName, LoadPromptOptions{})
		assert.Error(t, err)
	})

	t.Run("Nested Directories", func(t *testing.T) {
		promptName := "sub/dir/prompt"
		err := store.Save(PromptData{PromptRef: PromptRef{Name: promptName}, Source: "nested"})
		assert.NoError(t, err)

		loaded, err := store.Load(promptName, LoadPromptOptions{})
		assert.NoError(t, err)
		assert.Equal(t, "nested", loaded.Source)

		// Check file location
		expectedPath := filepath.Join(tmpDir, "sub", "dir", "prompt.prompt")
		_, err = os.Stat(expectedPath)
		assert.NoError(t, err)
	})

	t.Run("Path Traversal Block", func(t *testing.T) {
		// Attempt to save outside root
		err := store.Save(PromptData{PromptRef: PromptRef{Name: "../outside"}, Source: "bad"})
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "invalid path") // From ValidatePromptName

		// Attempt to load absolute path (which ValidatePromptName catches or verifyPathContainment)
		_, err = store.Load("/etc/passwd", LoadPromptOptions{})
		assert.Error(t, err)
	})
}
