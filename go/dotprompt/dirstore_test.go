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
	"strings"
	"testing"
)

func TestDirStore(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := NewDirStore(tmpDir)
	if err != nil {
		t.Fatalf("NewDirStore() returned error: %v", err)
	}

	t.Run("Save and Load Simple", func(t *testing.T) {
		prompt := PromptData{
			PromptRef: PromptRef{
				Name: "simple",
			},
			Source: "simple content",
		}
		err := store.Save(prompt)
		if err != nil {
			t.Errorf("store.Save() returned error: %v", err)
		}

		// Verify file exists
		content, err := os.ReadFile(filepath.Join(tmpDir, "simple.prompt"))
		if err != nil {
			t.Errorf("os.ReadFile() returned error: %v", err)
		}
		if string(content) != "simple content" {
			t.Errorf("File content = %q, want \"simple content\"", string(content))
		}

		loaded, err := store.Load("simple", LoadPromptOptions{})
		if err != nil {
			t.Errorf("store.Load() returned error: %v", err)
		}
		if loaded.Source != "simple content" {
			t.Errorf("loaded.Source = %q, want \"simple content\"", loaded.Source)
		}
		if loaded.Name != "simple" {
			t.Errorf("loaded.Name = %q, want \"simple\"", loaded.Name)
		}
		if loaded.Variant != "" {
			t.Errorf("loaded.Variant = %q, want \"\"", loaded.Variant)
		}
		if loaded.Version == "" {
			t.Error("loaded.Version is empty")
		}
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
		if err != nil {
			t.Errorf("store.Save() returned error: %v", err)
		}

		loaded, err := store.Load("variant-test", LoadPromptOptions{Variant: "v1"})
		if err != nil {
			t.Errorf("store.Load() returned error: %v", err)
		}
		if loaded.Source != "variant content" {
			t.Errorf("loaded.Source = %q, want \"variant content\"", loaded.Source)
		}
		if loaded.Variant != "v1" {
			t.Errorf("loaded.Variant = %q, want \"v1\"", loaded.Variant)
		}
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
		if err != nil {
			t.Errorf("store.List() returned error: %v", err)
		}
		if len(list.Items) != 3 {
			t.Errorf("len(list.Items) = %d, want 3", len(list.Items))
		}

		// sort order is a, b, c.v1
		if list.Items[0].Name != "a" {
			t.Errorf("Items[0].Name = %q, want \"a\"", list.Items[0].Name)
		}
		if list.Items[1].Name != "b" {
			t.Errorf("Items[1].Name = %q, want \"b\"", list.Items[1].Name)
		}
		if list.Items[2].Name != "c" {
			t.Errorf("Items[2].Name = %q, want \"c\"", list.Items[2].Name)
		}
		if list.Items[2].Variant != "v1" {
			t.Errorf("Items[2].Variant = %q, want \"v1\"", list.Items[2].Variant)
		}
	})

	t.Run("List with Variant Filter", func(t *testing.T) {
		options := ListPromptsOptions{Variant: "v1"}
		list, err := store.List(options)
		if err != nil {
			t.Errorf("store.List() returned error: %v", err)
		}
		if len(list.Items) != 1 {
			t.Errorf("len(list.Items) = %d, want 1", len(list.Items))
		}
		if list.Items[0].Name != "c" {
			t.Errorf("Items[0].Name = %q, want \"c\"", list.Items[0].Name)
		}
		if list.Items[0].Variant != "v1" {
			t.Errorf("Items[0].Variant = %q, want \"v1\"", list.Items[0].Variant)
		}
	})

	t.Run("Partials", func(t *testing.T) {
		partialPath := filepath.Join(tmpDir, "_mypartial.prompt")
		err := os.WriteFile(partialPath, []byte("partial content"), 0644)
		if err != nil {
			t.Fatalf("os.WriteFile() returned error: %v", err)
		}

		loaded, err := store.LoadPartial("mypartial", LoadPartialOptions{})
		if err != nil {
			t.Errorf("store.LoadPartial() returned error: %v", err)
		}
		if loaded.Source != "partial content" {
			t.Errorf("loaded.Source = %q, want \"partial content\"", loaded.Source)
		}

		list, err := store.ListPartials(ListPartialsOptions{})
		if err != nil {
			t.Errorf("store.ListPartials() returned error: %v", err)
		}
		found := false
		for _, p := range list.Items {
			if p.Name == "mypartial" {
				found = true
				break
			}
		}
		if !found {
			t.Error("partial should be listed")
		}
	})

	t.Run("Delete", func(t *testing.T) {
		promptName := "to-delete"
		err := store.Save(PromptData{PromptRef: PromptRef{Name: promptName}, Source: "x"})
		if err != nil {
			t.Fatalf("store.Save() returned error: %v", err)
		}

		err = store.Delete(promptName, PromptStoreDeleteOptions{})
		if err != nil {
			t.Errorf("store.Delete() returned error: %v", err)
		}

		_, err = store.Load(promptName, LoadPromptOptions{})
		if err == nil {
			t.Error("store.Load() expected error, got nil")
		}
	})

	t.Run("Nested Directories", func(t *testing.T) {
		promptName := "sub/dir/prompt"
		err := store.Save(PromptData{PromptRef: PromptRef{Name: promptName}, Source: "nested"})
		if err != nil {
			t.Errorf("store.Save() returned error: %v", err)
		}

		loaded, err := store.Load(promptName, LoadPromptOptions{})
		if err != nil {
			t.Errorf("store.Load() returned error: %v", err)
		}
		if loaded.Source != "nested" {
			t.Errorf("loaded.Source = %q, want \"nested\"", loaded.Source)
		}

		// Check file location
		expectedPath := filepath.Join(tmpDir, "sub", "dir", "prompt.prompt")
		_, err = os.Stat(expectedPath)
		if err != nil {
			t.Errorf("os.Stat() returned error: %v", err)
		}
	})

	t.Run("Path Traversal Block", func(t *testing.T) {
		// Attempt to save outside root
		err := store.Save(PromptData{PromptRef: PromptRef{Name: "../outside"}, Source: "bad"})
		if err == nil {
			t.Error("store.Save() expected error, got nil")
		} else {
			if !strings.Contains(err.Error(), "invalid path") && !strings.Contains(err.Error(), "path traversal") {
				t.Errorf("Error message should contain 'invalid path' or 'path traversal', got: %s", err.Error())
			}
		}

		// Attempt to load absolute path (which ValidatePromptName catches or verifyPathContainment)
		_, err = store.Load("/etc/passwd", LoadPromptOptions{})
		if err == nil {
			t.Error("store.Load() expected error, got nil")
		}
	})
}
