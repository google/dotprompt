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
	"fmt"

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

// TODO: Add pending: true for section helper
// JSON serializes the given data to a JSON string with optional indentation.
func JSON(serializable any, options *raymond.Options) raymond.SafeString {
	var jsonData []byte
	var err error
	if options.HashProp("indent") == nil {
		jsonData, err = json.Marshal(serializable)
	} else {
		indent := options.HashProp("indent").(int)
		indentStr := ""
		for range indent {
			indentStr += " "
		}
		jsonData, err = json.MarshalIndent(serializable, "", indentStr)
	}

	if err != nil {
		return ""
	}
	return raymond.SafeString(string(jsonData))
}

// Role returns a formatted role string.
func RoleFn(role string) raymond.SafeString {
	return raymond.SafeString(fmt.Sprintf("<<<dotprompt:role:%s>>>", role))
}

// History returns a formatted history string.
func History() raymond.SafeString {
	return raymond.SafeString("<<<dotprompt:history>>>")
}

// Section returns a formatted section string.
func Section(name string) raymond.SafeString {
	return raymond.SafeString(fmt.Sprintf("<<<dotprompt:section %s>>>", name))
}

// Media returns a formatted media string.
func MediaFn(options *raymond.Options) raymond.SafeString {
	url := options.HashStr("url")
	contentType := options.HashStr("contentType")
	if contentType != "" {
		return raymond.SafeString(fmt.Sprintf("<<<dotprompt:media:url %s %s>>>", url, contentType))
	}
	return raymond.SafeString(fmt.Sprintf("<<<dotprompt:media:url %s>>>", url))
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
