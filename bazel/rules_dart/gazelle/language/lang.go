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

package language

import (
	"flag"
	"io/fs"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/bazelbuild/bazel-gazelle/config"
	"github.com/bazelbuild/bazel-gazelle/label"
	"github.com/bazelbuild/bazel-gazelle/language"
	"github.com/bazelbuild/bazel-gazelle/repo"
	"github.com/bazelbuild/bazel-gazelle/resolve"
	"github.com/bazelbuild/bazel-gazelle/rule"

	"github.com/google/rules_dart/gazelle/pubspec"
)

const dartName = "dart"

type dartLang struct{}

func NewLanguage() language.Language {
	return &dartLang{}
}

func (d *dartLang) Name() string { return dartName }

func (d *dartLang) RegisterFlags(fs *flag.FlagSet, cmd string, c *config.Config) {}

func (d *dartLang) CheckFlags(fs *flag.FlagSet, c *config.Config) error { return nil }

func (d *dartLang) KnownDirectives() []string { return nil }

func (d *dartLang) Kinds() map[string]rule.KindInfo {
	return map[string]rule.KindInfo{
		"dart_library": {
			NonEmptyAttrs:  map[string]bool{"srcs": true},
			MergeableAttrs: map[string]bool{"srcs": true, "deps": true},
			ResolveAttrs:   map[string]bool{"deps": true},
		},
		"dart_test": {
			NonEmptyAttrs:  map[string]bool{"srcs": true},
			MergeableAttrs: map[string]bool{"srcs": true, "deps": true},
			ResolveAttrs:   map[string]bool{"deps": true},
		},
		"dart_pub_get":     {},
		"dart_pub_publish": {},
	}
}

func (d *dartLang) Loads() []rule.LoadInfo {
	return []rule.LoadInfo{
		{
			Name:    "@rules_dart//:defs.bzl",
			Symbols: []string{"dart_library", "dart_pub_get", "dart_pub_publish", "dart_test"},
		},
	}
}

func (d *dartLang) Fix(c *config.Config, f *rule.File) {}

func (d *dartLang) Configure(c *config.Config, rel string, f *rule.File) {}

func (d *dartLang) Imports(c *config.Config, r *rule.Rule, f *rule.File) []resolve.ImportSpec {
	if r.Kind() == "dart_library" {
		return []resolve.ImportSpec{{Lang: dartName, Imp: r.Name()}}
	}
	return nil
}

func (d *dartLang) Embeds(r *rule.Rule, from label.Label) []label.Label { return nil }

func (d *dartLang) Resolve(c *config.Config, ix *resolve.RuleIndex, rc *repo.RemoteCache, r *rule.Rule, imports interface{}, from label.Label) {
	deps := r.AttrStrings("deps")
	importList := imports.([]string)

	for _, imp := range importList {
		matches := ix.FindRulesByImportWithConfig(c, resolve.ImportSpec{Lang: dartName, Imp: imp}, dartName)
		if len(matches) > 0 {
			deps = append(deps, matches[0].Label.String())
		} else {
			l := label.Label{Repo: "dart_deps_" + imp, Name: imp}
			deps = append(deps, l.String())
		}
	}

	sort.Strings(deps)
	// Unique
	if len(deps) > 0 {
		uniqueDeps := make([]string, 0, len(deps))
		seen := make(map[string]bool)
		for _, dep := range deps {
			if !seen[dep] {
				seen[dep] = true
				uniqueDeps = append(uniqueDeps, dep)
			}
		}
		r.SetAttr("deps", uniqueDeps)
	}
}

func (d *dartLang) GenerateRules(args language.GenerateArgs) language.GenerateResult {
	res := language.GenerateResult{}

	// Look for pubspec.yaml
	pubspecPath := filepath.Join(args.Dir, "pubspec.yaml")
	p, err := pubspec.ParsePubspec(pubspecPath)
	if err != nil {
		return res
	}

	// Generate dart_library
	r := rule.NewRule("dart_library", p.Name)

	// Collect srcs (pubspec.yaml + lib/**/*.dart)
	srcs := []string{"pubspec.yaml"}
	libDir := filepath.Join(args.Dir, "lib")
	filepath.WalkDir(libDir, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		if !d.IsDir() && strings.HasSuffix(d.Name(), ".dart") {
			rel, err := filepath.Rel(args.Dir, path)
			if err == nil {
				srcs = append(srcs, rel)
			}
		}
		return nil
	})
	sort.Strings(srcs)
	r.SetAttr("srcs", srcs)

	r.SetAttr("pubspec", "pubspec.yaml")

	// Add imports (dependencies)
	var imports []string
	for dep := range p.Dependencies {
		imports = append(imports, dep)
	}
	sort.Strings(imports)
	r.SetPrivateAttr(config.GazelleImportsKey, imports)

	res.Gen = append(res.Gen, r)
	res.Imports = append(res.Imports, imports)

	// Generate dart_test targets
	testDir := filepath.Join(args.Dir, "test")
	entries, err := os.ReadDir(testDir)
	if err == nil {
		for _, entry := range entries {
			if !entry.IsDir() && strings.HasSuffix(entry.Name(), "_test.dart") {
				name := strings.TrimSuffix(entry.Name(), ".dart")
				t := rule.NewRule("dart_test", name)
				t.SetAttr("main", "test/"+entry.Name())
				t.SetAttr("deps", []string{":" + p.Name})
				res.Gen = append(res.Gen, t)
				res.Imports = append(res.Imports, []string{})
			}
		}
	}

	// Generate dart_pub_get target (always, for dependency resolution)
	pubGet := rule.NewRule("dart_pub_get", "pub_get")
	res.Gen = append(res.Gen, pubGet)
	res.Imports = append(res.Imports, []string{})

	// Generate dart_pub_publish target (only if package is publishable)
	if p.IsPublishable() {
		pubPublish := rule.NewRule("dart_pub_publish", "publish")
		res.Gen = append(res.Gen, pubPublish)
		res.Imports = append(res.Imports, []string{})
	}

	return res
}
