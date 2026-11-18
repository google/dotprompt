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
	"encoding/json"
	"errors"
	"fmt"
	"strings"

	"github.com/mbleigh/raymond"
)

var templateHelpers = map[string]any{
	"json":         JSON,
	"role":         RoleFn,
	"history":      History,
	"section":      Section,
	"media":        MediaFn,
	"ifEquals":     IfEquals,
	"unlessEquals": UnlessEquals,
}

// TODO(#494): Add pending: true for section helper
// JSON serializes the given data to a JSON string with optional indentation.
// Panics on serialization errors to match JavaScript's JSON.stringify fail-fast behavior.
func JSON(serializable any, options *raymond.Options) raymond.SafeString {
	var jsonData []byte
	var err error
	if options.HashProp("indent") == nil {
		jsonData, err = json.Marshal(serializable)
	} else {
		indent := options.HashProp("indent").(int)
		var indentStr strings.Builder
		for range indent {
			indentStr.WriteString(" ")
		}
		jsonData, err = json.MarshalIndent(serializable, "", indentStr.String())
	}

	if err != nil {
		panic(fmt.Sprintf("json helper: serialization failed: %v", err))
	}
	return raymond.SafeString(string(jsonData))
}

// markerHelperOutput formats a marker for body using the per-render nonce from
// the private data frame (see markers.go).
//
// Data frames are inherited by blocks (#each, #if, ...) and partials, so the
// nonce is only missing if the helper runs outside Dotprompt rendering or a
// custom block helper passes a fresh raymond.NewDataFrame() instead of
// options.NewDataFrame(). In that case it panics with an error, which
// raymond's Exec/ExecWith recover and return as the render error. Raymond
// helpers can't return errors directly.
func markerHelperOutput(options *raymond.Options, body string) raymond.SafeString {
	nonce, ok := options.Data(markerNonceDataKey).(string)
	if !ok {
		panic(errors.New("dotprompt: marker helpers (role, history, section, media) must be rendered via Dotprompt"))
	}
	marker, err := formatMarker(nonce, body)
	if err != nil {
		panic(err)
	}
	return raymond.SafeString(marker)
}

// RoleFn returns a role marker that starts a new message with the given role.
func RoleFn(role string, options *raymond.Options) raymond.SafeString {
	return markerHelperOutput(options, "role:"+role)
}

// History returns a history marker where the conversation history is inserted.
func History(options *raymond.Options) raymond.SafeString {
	return markerHelperOutput(options, "history")
}

// Section returns a section marker that becomes a pending part with the given
// purpose.
func Section(name string, options *raymond.Options) raymond.SafeString {
	return markerHelperOutput(options, "section "+name)
}

// MediaFn returns a media marker that becomes a media part with the given url
// and optional contentType hash arguments.
func MediaFn(options *raymond.Options) raymond.SafeString {
	body := "media:url " + options.HashStr("url")
	if contentType := options.HashStr("contentType"); contentType != "" {
		body += " " + contentType
	}
	return markerHelperOutput(options, body)
}

// IfEquals compares two values and returns the appropriate template content.
func IfEquals(arg1, arg2 any, options *raymond.Options) string {
	if arg1 == arg2 {
		return options.Fn()
	}
	return options.Inverse()
}

// UnlessEquals compares two values and returns the appropriate template content.
func UnlessEquals(arg1, arg2 any, options *raymond.Options) string {
	if arg1 != arg2 {
		return options.Fn()
	}
	return options.Inverse()
}
