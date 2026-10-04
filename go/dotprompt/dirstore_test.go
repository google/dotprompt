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
	"math"
	"os"
	"path/filepath"
	"slices"
	"strings"
	"testing"
)

func TestDirStorePagination(t *testing.T) {
	for _, partials := range []bool{false, true} {
		name := "prompts"
		if partials {
			name = "partials"
		}
		t.Run(name, func(t *testing.T) {
			root := t.TempDir()
			store, err := NewDirStore(root)
			if err != nil {
				t.Fatal(err)
			}
			for _, name := range []string{"b.v1", "a.v2", "nested/c", "a", "a.v1"} {
				if partials {
					name = filepath.Join(filepath.Dir(name), "_"+filepath.Base(name))
				}
				path := filepath.Join(root, name+".prompt")
				if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
					t.Fatal(err)
				}
				if err := os.WriteFile(path, []byte("content"), 0644); err != nil {
					t.Fatal(err)
				}
			}

			list := func(cursor string, limit int, variant string) ([]string, string, error) {
				var names []string
				if partials {
					result, err := store.ListPartials(ListPartialsOptions{Cursor: cursor, Limit: limit, Variant: variant})
					for _, item := range result.Items {
						name := item.Name
						if item.Variant != "" {
							name += "." + item.Variant
						}
						names = append(names, name)
					}
					return names, result.Cursor, err
				}
				result, err := store.List(ListPromptsOptions{Cursor: cursor, Limit: limit, Variant: variant})
				for _, item := range result.Items {
					name := item.Name
					if item.Variant != "" {
						name += "." + item.Variant
					}
					names = append(names, name)
				}
				return names, result.Cursor, err
			}

			for _, tc := range []struct {
				name    string
				limit   int
				variant string
				pages   [][]string
			}{
				{"single", 1, "", [][]string{{"a"}, {"a.v1"}, {"a.v2"}, {"b.v1"}, {"nested/c"}}},
				{"uneven", 2, "", [][]string{{"a", "a.v1"}, {"a.v2", "b.v1"}, {"nested/c"}}},
				{"exact", 5, "", [][]string{{"a", "a.v1", "a.v2", "b.v1", "nested/c"}}},
				{"larger", 10, "", [][]string{{"a", "a.v1", "a.v2", "b.v1", "nested/c"}}},
				{"unlimited", 0, "", [][]string{{"a", "a.v1", "a.v2", "b.v1", "nested/c"}}},
				{"negative limit", -1, "", [][]string{{"a", "a.v1", "a.v2", "b.v1", "nested/c"}}},
				{"variant filter", 1, "v1", [][]string{{"a.v1"}, {"b.v1"}}},
				{"no matches", 1, "missing", [][]string{{}}},
			} {
				t.Run(tc.name, func(t *testing.T) {
					cursor := ""
					for i, want := range tc.pages {
						got, next, err := list(cursor, tc.limit, tc.variant)
						if err != nil {
							t.Fatal(err)
						}
						if !slices.Equal(got, want) {
							t.Fatalf("page %d = %v, want %v", i, got, want)
						}
						if (next == "") != (i == len(tc.pages)-1) {
							t.Fatalf("page %d cursor = %q", i, next)
						}
						cursor = next
					}
				})
			}

			t.Run("remaining items", func(t *testing.T) {
				_, cursor, err := list("", 1, "")
				if err != nil {
					t.Fatal(err)
				}
				for _, limit := range []int{0, -1, math.MaxInt} {
					got, next, err := list(cursor, limit, "")
					if err != nil {
						t.Fatal(err)
					}
					if want := []string{"a.v1", "a.v2", "b.v1", "nested/c"}; !slices.Equal(got, want) || next != "" {
						t.Errorf("limit %d: items = %v, cursor = %q; want %v and no cursor", limit, got, next, want)
					}
				}
			})

			t.Run("invalid cursor", func(t *testing.T) {
				for _, cursor := range []string{"invalid", "-1", "999999999999999999999999999999999"} {
					if _, _, err := list(cursor, 1, ""); err == nil {
						t.Errorf("cursor %q: expected an error", cursor)
					}
				}
			})

			t.Run("listing shrinks", func(t *testing.T) {
				_, cursor, err := list("", 4, "")
				if err != nil {
					t.Fatal(err)
				}
				if err := os.RemoveAll(root); err != nil {
					t.Fatal(err)
				}
				if err := os.Mkdir(root, 0755); err != nil {
					t.Fatal(err)
				}
				for _, cursor := range []string{cursor, ""} {
					got, next, err := list(cursor, 1, "")
					if err != nil || len(got) != 0 || next != "" {
						t.Errorf("cursor %q: items = %v, cursor = %q, error = %v; want an empty page", cursor, got, next, err)
					}
				}
			})
		})
	}
}

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
