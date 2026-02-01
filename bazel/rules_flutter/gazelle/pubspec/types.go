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
	Dependencies    map[string]interface{} `yaml:"dependencies"`
	DevDependencies map[string]interface{} `yaml:"dev_dependencies"`
	Environment     map[string]string      `yaml:"environment"`
	Flutter         map[string]interface{} `yaml:"flutter,omitempty"`
}

// IsFlutterPackage returns true if the package depends on flutter or has a flutter section
func (p *Pubspec) IsFlutterPackage() bool {
	if p.Flutter != nil {
		return true
	}
	if _, ok := p.Dependencies["flutter"]; ok {
		return true
	}
	return false
}
