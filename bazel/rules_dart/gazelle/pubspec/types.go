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

package pubspec

// Pubspec represents pubspec.yaml
type Pubspec struct {
	Name            string                 `yaml:"name"`
	PublishTo       string                 `yaml:"publish_to"`
	Dependencies    map[string]interface{} `yaml:"dependencies"`
	DevDependencies map[string]interface{} `yaml:"dev_dependencies"`
	Environment     map[string]string      `yaml:"environment"`
}

// IsPublishable returns true if the package can be published to pub.dev.
// A package is publishable unless publish_to is explicitly set to "none".
func (p *Pubspec) IsPublishable() bool {
	return p.PublishTo != "none"
}

// Lockfile represents pubspec.lock
type Lockfile struct {
	Packages map[string]PackageEntry `yaml:"packages"`
}

// PackageEntry represents a single package in pubspec.lock
type PackageEntry struct {
	Dependency  string      `yaml:"dependency"`
	Description interface{} `yaml:"description"` // Map for hosted/git, String for path?
	Source      string      `yaml:"source"`
	Version     string      `yaml:"version"`
}

// HostedDescription represents the description block for source: hosted
type HostedDescription struct {
	Name   string `yaml:"name"`
	Url    string `yaml:"url"`
	Sha256 string `yaml:"sha256"`
}

// GitDescription represents the description block for source: git
type GitDescription struct {
	Path        string `yaml:"path"`
	Ref         string `yaml:"ref"`
	ResolvedRef string `yaml:"resolved-ref"`
	Url         string `yaml:"url"`
}
