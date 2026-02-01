package language

import (
	"flag"
	"path/filepath"
	"sort"

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
	}
}

func (d *dartLang) Loads() []rule.LoadInfo {
	return []rule.LoadInfo{
		{
			Name:    "@rules_dart//:defs.bzl",
			Symbols: []string{"dart_library", "dart_test"},
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
	r.SetAttr("srcs", []string{"glob([\"lib/**/*.dart\"])"}) // Simplified glob (string literal for now)
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
	return res
}
