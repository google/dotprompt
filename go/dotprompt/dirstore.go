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
	"crypto/sha1"
	"encoding/hex"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// DirStore is a file-system based prompt store.
// It organizes prompts as files in a directory structure.
// Prompts are stored as `.prompt` files.
// Partials are stored as `_name.prompt` files.
// Variants are stored as `name.variant.prompt` files.
type DirStore struct {
	Root string
}

// NewDirStore creates a new DirStore rooted at the given directory.
// The root path is resolved to an absolute path.
func NewDirStore(root string) (*DirStore, error) {
	absRoot, err := filepath.Abs(root)
	if err != nil {
		return nil, err
	}
	return &DirStore{Root: absRoot}, nil
}

func (ds *DirStore) verifyPathContainment(name string) (string, error) {
	if err := ValidatePromptName(name); err != nil {
		return "", err
	}

	fullPath := filepath.Join(ds.Root, name)
	cleanedPath := filepath.Clean(fullPath)

	if !strings.HasPrefix(cleanedPath, ds.Root) {
		return "", fmt.Errorf("path traversal attempt detected: %s", name)
	}

	return cleanedPath, nil
}

func calculateVersion(content string) string {
	h := sha1.New()
	h.Write([]byte(content))
	return hex.EncodeToString(h.Sum(nil))
}

const (
	promptExtension = ".prompt"
	partialPrefix   = "_"
)

// List enumerates all prompts in the store that match the given options.
// It traverses the directory structure recursively.
// It ignores files starting with `_` (partials) and directories starting with `.` (hidden).
func (ds *DirStore) List(options ListPromptsOptions) (ListPromptsResult[PromptRef], error) {
	var prompts []PromptRef

	err := filepath.WalkDir(ds.Root, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() {
			if strings.HasPrefix(d.Name(), ".") && d.Name() != "." {
				return filepath.SkipDir
			}
			return nil
		}

		if !strings.HasSuffix(d.Name(), promptExtension) {
			return nil
		}

		relPath, err := filepath.Rel(ds.Root, path)
		if err != nil {
			return err
		}

		// Handle windows paths
		relPath = filepath.ToSlash(relPath)

		name := strings.TrimSuffix(relPath, promptExtension)
		fileName := filepath.Base(name)

		if strings.HasPrefix(fileName, partialPrefix) {
			return nil
		}

		parts := strings.Split(name, ".")
		promptName := parts[0]
		variant := ""
		if len(parts) > 1 {
			variant = parts[len(parts)-1]
			promptName = strings.TrimSuffix(name, "."+variant)
		}

		if options.Variant != "" && variant != options.Variant {
			return nil
		}

		prompts = append(prompts, PromptRef{
			Name:    promptName,
			Variant: variant,
		})
		return nil
	})

	if err != nil {
		return ListPromptsResult[PromptRef]{}, err
	}

	// Simple pagination
	sort.Slice(prompts, func(i, j int) bool {
		if prompts[i].Name == prompts[j].Name {
			return prompts[i].Variant < prompts[j].Variant
		}
		return prompts[i].Name < prompts[j].Name
	})

	result := ListPromptsResult[PromptRef]{
		Items: prompts,
	}
	// TODO: meaningful cursor/limit implementation
	// For now returns all as simple implementation

	if options.Limit > 0 && len(result.Items) > options.Limit {
		result.Cursor = "more" // Dummy cursor for now
		result.Items = result.Items[:options.Limit]
	}

	return result, nil
}

// ListPartials enumerates all partials in the store that match the given options.
// It searches for files starting with `_` and ending with `.prompt`.
func (ds *DirStore) ListPartials(options ListPartialsOptions) (ListPartialsResult[PartialRef], error) {
	var partials []PartialRef

	err := filepath.WalkDir(ds.Root, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() {
			if strings.HasPrefix(d.Name(), ".") && d.Name() != "." {
				return filepath.SkipDir
			}
			return nil
		}

		if !strings.HasSuffix(d.Name(), promptExtension) {
			return nil
		}

		relPath, err := filepath.Rel(ds.Root, path)
		if err != nil {
			return err
		}
		relPath = filepath.ToSlash(relPath)

		name := strings.TrimSuffix(relPath, promptExtension)
		fileName := filepath.Base(name)

		if !strings.HasPrefix(fileName, partialPrefix) {
			return nil
		}

		// Remove partial prefix from filename for the exposed name
		dir := filepath.Dir(name)
		baseName := strings.TrimPrefix(fileName, partialPrefix)

		cleanName := baseName
		if dir != "." {
			cleanName = dir + "/" + baseName
		}

		parts := strings.Split(cleanName, ".")
		partialName := parts[0]
		variant := ""
		if len(parts) > 1 {
			variant = parts[len(parts)-1]
			partialName = strings.TrimSuffix(cleanName, "."+variant)
		}

		if options.Variant != "" && variant != options.Variant {
			return nil
		}

		partials = append(partials, PartialRef{
			Name:    partialName,
			Variant: variant,
		})
		return nil
	})

	if err != nil {
		return ListPartialsResult[PartialRef]{}, err
	}

	sort.Slice(partials, func(i, j int) bool {
		if partials[i].Name == partials[j].Name {
			return partials[i].Variant < partials[j].Variant
		}
		return partials[i].Name < partials[j].Name
	})

	result := ListPartialsResult[PartialRef]{
		Items: partials,
	}

	if options.Limit > 0 && len(result.Items) > options.Limit {
		result.Cursor = "more"
		result.Items = result.Items[:options.Limit]
	}

	return result, nil

}

// Load retrieves a prompt by name from the store.
// It checks for variant-specific files if a variant is requested.
// It verifies that the resolved file path is contained within the store's root directory.
func (ds *DirStore) Load(name string, options LoadPromptOptions) (PromptData, error) {
	filePath, err := ds.verifyPathContainment(name)
	if err != nil {
		return PromptData{}, err
	}

	possiblePaths := []string{}
	if options.Variant != "" {
		possiblePaths = append(possiblePaths, filePath+"."+options.Variant+promptExtension)
	}
	possiblePaths = append(possiblePaths, filePath+promptExtension)

	var content []byte
	var loadedPath string
	found := false

	for _, p := range possiblePaths {
		b, err := os.ReadFile(p)
		if err == nil {
			content = b
			loadedPath = p
			found = true
			break
		} else if !os.IsNotExist(err) {
			return PromptData{}, err
		}
	}

	if !found {
		return PromptData{}, fmt.Errorf("prompt not found: %s", name)
	}

	// determine variant from loaded path
	// path relative to root
	relPath, _ := filepath.Rel(ds.Root, loadedPath)
	relPath = filepath.ToSlash(relPath)
	trimmed := strings.TrimSuffix(relPath, promptExtension)

	variant := ""
	if trimmed != name {
		// name.variant -> variant
		// check if trimmed ends with .variant
		// careful if name itself has dot?
		// But verifyPathContainment takes 'name'.
		// Actually typical use: Load('folder/foo', variant='bar') -> folder/foo.bar.prompt
		// Load('folder/foo') -> folder/foo.prompt

		if after, ok := strings.CutPrefix(trimmed, name+"."); ok {
			variant = after
		}
	}

	source := string(content)
	return PromptData{
		PromptRef: PromptRef{
			Name:    name,
			Variant: variant,
			Version: calculateVersion(source),
		},
		Source: source,
	}, nil
}

// LoadPartial retrieves a partial by name from the store.
// It automatically handles the `_` prefix convention for partial filenames.
// It verifies path containment security.
func (ds *DirStore) LoadPartial(name string, options LoadPartialOptions) (PartialData, error) {
	// Partials are stored as _name.prompt
	dir := filepath.Dir(name)
	base := filepath.Base(name)

	// We reuse logic but correct the name passed to containment check?
	// verifyPathContainment takes the name provided.
	// We need to construct the actual file path we are looking for.

	if err := ValidatePromptName(name); err != nil {
		return PartialData{}, err
	}

	// Construct potential full paths with variant
	// If name is "foo/bar" -> root/foo/_bar.prompt or root/foo/_bar.variant.prompt

	searchBase := filepath.Join(ds.Root, dir, partialPrefix+base)
	// verify containment of "foo/_bar" effectively

	// Let's rely on standard path construction

	possiblePaths := []string{}
	if options.Variant != "" {
		possiblePaths = append(possiblePaths, searchBase+"."+options.Variant+promptExtension)
	}
	possiblePaths = append(possiblePaths, searchBase+promptExtension)

	var content []byte
	var loadedPath string
	found := false

	for _, p := range possiblePaths {
		// Verify containment for safety for each path we try
		// Though we constructed it from root + dir + safe-ish components.
		// It's safer to check the resulting path is in root.
		cleanP := filepath.Clean(p)
		if !strings.HasPrefix(cleanP, ds.Root) {
			continue
		}

		b, err := os.ReadFile(cleanP)
		if err == nil {
			content = b
			loadedPath = p
			found = true
			break
		} else if !os.IsNotExist(err) {
			return PartialData{}, err
		}
	}

	if !found {
		return PartialData{}, fmt.Errorf("partial not found: %s", name)
	}

	source := string(content)

	// Determine variant
	relPath, _ := filepath.Rel(ds.Root, loadedPath)
	relPath = filepath.ToSlash(relPath)

	// relPath is like "foo/_bar.variant.prompt"
	// name is "foo/bar"

	variant := ""
	trimmed := strings.TrimSuffix(relPath, promptExtension)
	// trimmed: foo/_bar.variant or foo/_bar

	expectedBase := filepath.Join(dir, partialPrefix+base)
	expectedBaseSlash := filepath.ToSlash(expectedBase)

	if after, ok := strings.CutPrefix(trimmed, expectedBaseSlash+"."); ok {
		variant = after
	}

	return PartialData{
		PartialRef: PartialRef{
			Name:    name,
			Variant: variant,
			Version: calculateVersion(source),
		},
		Source: source,
	}, nil
}

// Save persists a prompt to the store.
// It writes the prompt source to a file, creating necessary parent directories.
// It ensures the target path is safe and within the store root.
func (ds *DirStore) Save(prompt PromptData) error {
	pathName := prompt.Name
	if prompt.Variant != "" {
		pathName += "." + prompt.Variant
	}

	filePath, err := ds.verifyPathContainment(pathName)
	if err != nil {
		return err
	}

	fullPath := filePath + promptExtension

	if err := os.MkdirAll(filepath.Dir(fullPath), 0755); err != nil {
		return err
	}

	return os.WriteFile(fullPath, []byte(prompt.Source), 0644)
}

// Delete removes a prompt file from the store.
func (ds *DirStore) Delete(name string, options PromptStoreDeleteOptions) error {
	pathName := name
	if options.Variant != "" {
		pathName += "." + options.Variant
	}

	filePath, err := ds.verifyPathContainment(pathName)
	if err != nil {
		return err
	}

	fullPath := filePath + promptExtension
	return os.Remove(fullPath)
}
