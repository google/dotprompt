// Copyright 2025 Google LLC
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
	"strings"
	"testing"

	"github.com/mbleigh/raymond"
)

const testMarkerNonce = "0123456789abcdef0123456789abcdef"

// execWithMarkerHelpers renders source with the marker helpers registered and
// the given private data frame (nil for none).
func execWithMarkerHelpers(t *testing.T, source string, ctx map[string]any, df *raymond.DataFrame) (string, error) {
	t.Helper()
	tpl, err := raymond.Parse(source)
	if err != nil {
		t.Fatalf("raymond.Parse(%q) error: %v", source, err)
	}
	tpl.RegisterHelpers(map[string]any{
		"role":    RoleFn,
		"history": History,
		"section": Section,
		"media":   MediaFn,
	})
	tpl.RegisterPartial("turn", `{{role this.role}}{{this.text}}`)
	return tpl.ExecWith(ctx, df, &raymond.ExecOptions{NoEscape: true})
}

func nonceDataFrame() *raymond.DataFrame {
	df := raymond.NewDataFrame()
	df.Set(markerNonceDataKey, testMarkerNonce)
	return df
}

func TestMarkerHelpers(t *testing.T) {
	m := func(body string) string {
		return "<<<dotprompt:" + testMarkerNonce + ":" + body + ">>>"
	}
	testCases := []struct {
		name   string
		source string
		ctx    map[string]any
		want   string
	}{
		{name: "role admin", source: `{{role "admin"}}`, want: m("role:admin")},
		{name: "role system", source: `{{role "system"}}`, want: m("role:system")},
		{name: "role user", source: `{{role "user"}}`, want: m("role:user")},
		{name: "role model", source: `{{role "model"}}`, want: m("role:model")},
		{name: "history", source: `{{history}}`, want: m("history")},
		{name: "section", source: `{{section "Introduction"}}`, want: m("section Introduction")},
		{name: "section examples", source: `{{section "examples"}}`, want: m("section examples")},
		{
			name:   "media url",
			source: `{{media url="https://example.com/a.png"}}`,
			want:   m("media:url https://example.com/a.png"),
		},
		{
			name:   "media url and content type",
			source: `{{media url="https://example.com/a.png" contentType="image/png"}}`,
			want:   m("media:url https://example.com/a.png image/png"),
		},
		{
			name:   "inside each and partial",
			source: `{{#each turns}}{{> turn}}{{/each}}`,
			ctx: map[string]any{"turns": []map[string]any{
				{"role": "user", "text": "hi"},
				{"role": "model", "text": "hello"},
			}},
			want: m("role:user") + "hi" + m("role:model") + "hello",
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			got, err := execWithMarkerHelpers(t, tc.source, tc.ctx, nonceDataFrame())
			if err != nil {
				t.Fatalf("render error: %v", err)
			}
			if got != tc.want {
				t.Errorf("got %q, want %q", got, tc.want)
			}
		})
	}
}

func TestMarkerHelpers_missingNonce(t *testing.T) {
	sources := []string{
		`{{role "system"}}`,
		`{{history}}`,
		`{{section "output"}}`,
		`{{media url="https://example.com/a.png"}}`,
	}
	for _, source := range sources {
		t.Run(source, func(t *testing.T) {
			got, err := execWithMarkerHelpers(t, source, nil, nil)
			if err == nil {
				t.Fatalf("expected error, got output %q", got)
			}
			if !strings.Contains(err.Error(), "must be rendered via Dotprompt") {
				t.Errorf("unexpected error: %v", err)
			}
		})
	}
}

func TestMarkerHelpers_invalidNonce(t *testing.T) {
	df := raymond.NewDataFrame()
	df.Set(markerNonceDataKey, ".*")
	got, err := execWithMarkerHelpers(t, `{{role "system"}}`, nil, df)
	if err == nil {
		t.Fatalf("expected error, got output %q", got)
	}
}

// Note: JSON, IfEquals, UnlessEquals helpers require raymond.Options
// which is complex to mock in unit tests. These functions are thoroughly tested
// via the spec tests in go/test/spec_test.go which exercise them through the
// full template rendering pipeline.
//
// The spec tests cover:
// - json: basic objects, arrays, indent variations, nested objects, empty values
// - media: url only, url + contentType
// - ifEquals/unlessEquals: int/string equality, boolean, null comparisons, type safety
