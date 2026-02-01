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

	"github.com/google/rules_flutter/gazelle/pubspec"
)

const flutterName = "flutter"

type flutterLang struct{}

func NewLanguage() language.Language {
	return &flutterLang{}
}

func (d *flutterLang) Name() string { return flutterName }

func (d *flutterLang) RegisterFlags(fs *flag.FlagSet, cmd string, c *config.Config) {}

func (d *flutterLang) CheckFlags(fs *flag.FlagSet, c *config.Config) error { return nil }

func (d *flutterLang) KnownDirectives() []string { return nil }

func (d *flutterLang) Kinds() map[string]rule.KindInfo {
	return map[string]rule.KindInfo{
		"flutter_library": {
			NonEmptyAttrs:  map[string]bool{"srcs": true},
			MergeableAttrs: map[string]bool{"srcs": true, "deps": true, "assets": true},
			ResolveAttrs:   map[string]bool{"deps": true},
		},
		"flutter_test": {
			NonEmptyAttrs:  map[string]bool{"srcs": true},
			MergeableAttrs: map[string]bool{"srcs": true, "deps": true},
			ResolveAttrs:   map[string]bool{"deps": true},
		},
		"dart_library": {
			NonEmptyAttrs:  map[string]bool{"srcs": true},
			MergeableAttrs: map[string]bool{"srcs": true, "deps": true},
			ResolveAttrs:   map[string]bool{"deps": true},
		},
	}
}

func (d *flutterLang) Loads() []rule.LoadInfo {
	return []rule.LoadInfo{
		{
			Name:    "@rules_flutter//:defs.bzl",
			Symbols: []string{"flutter_library", "flutter_test"},
		},
		{
			Name:    "@rules_dart//:defs.bzl",
			Symbols: []string{"dart_library"},
		},
	}
}

func (d *flutterLang) Fix(c *config.Config, f *rule.File) {}

func (d *flutterLang) Configure(c *config.Config, rel string, f *rule.File) {}

func (d *flutterLang) Imports(c *config.Config, r *rule.Rule, f *rule.File) []resolve.ImportSpec {
	if r.Kind() == "flutter_library" || r.Kind() == "dart_library" {
		return []resolve.ImportSpec{{Lang: flutterName, Imp: r.Name()}}
	}
	return nil
}

func (d *flutterLang) Embeds(r *rule.Rule, from label.Label) []label.Label { return nil }

func (d *flutterLang) Resolve(c *config.Config, ix *resolve.RuleIndex, rc *repo.RemoteCache, r *rule.Rule, imports interface{}, from label.Label) {
	deps := r.AttrStrings("deps")
	importList := imports.([]string)

	for _, imp := range importList {
		matches := ix.FindRulesByImportWithConfig(c, resolve.ImportSpec{Lang: flutterName, Imp: imp}, flutterName)
		if len(matches) > 0 {
			deps = append(deps, matches[0].Label.String())
		} else {
			// Assume external dependency managed by dart_deps/flutter_deps
			// Note: rules_flutter might share dependency namespace or have its own
			// For now, let's assume it resolves to dart_deps_PACKAGE
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

func (d *flutterLang) GenerateRules(args language.GenerateArgs) language.GenerateResult {
	res := language.GenerateResult{}

	// Look for pubspec.yaml
	pubspecPath := filepath.Join(args.Dir, "pubspec.yaml")
	p, err := pubspec.ParsePubspec(pubspecPath)
	if err != nil {
		return res
	}

	isFlutter := p.IsFlutterPackage()
	ruleKind := "dart_library"
	if isFlutter {
		ruleKind = "flutter_library"
	}

	// Generate library rule
	r := rule.NewRule(ruleKind, p.Name)

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
	
	// Collect assets if Flutter
	if isFlutter {
		assets := []string{}
		assetsDir := filepath.Join(args.Dir, "assets")
		filepath.WalkDir(assetsDir, func(path string, d fs.DirEntry, err error) error {
			if err != nil {
				return nil
			}
			if !d.IsDir() {
				rel, err := filepath.Rel(args.Dir, path)
				if err == nil {
					assets = append(assets, rel)
				}
			}
			return nil
		})
		sort.Strings(assets)
		if len(assets) > 0 {
			r.SetAttr("assets", assets)
		}
	}

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

	// Generate test targets
	testDir := filepath.Join(args.Dir, "test")
	entries, err := os.ReadDir(testDir)
	if err == nil {
		for _, entry := range entries {
			if !entry.IsDir() && strings.HasSuffix(entry.Name(), "_test.dart") {
				name := strings.TrimSuffix(entry.Name(), ".dart")
				// Use flutter_test if package is flutter, else dart_test?
				// Actually flutter_test handles pure dart tests too usually, but safe to stick to ruleKind or flutter_test for flutter packages.
				testKind := "dart_test"
				if isFlutter {
					testKind = "flutter_test"
				}
				
				t := rule.NewRule(testKind, name)
				t.SetAttr("main", "test/"+entry.Name())
				t.SetAttr("deps", []string{":" + p.Name})
				res.Gen = append(res.Gen, t)
				res.Imports = append(res.Imports, []string{})
			}
		}
	}

	return res
}
