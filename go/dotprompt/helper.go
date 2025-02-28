// Copyright 2025 Google LLC
// SPDX-License-Identifier: Apache-2.0

package dotprompt

import (
	"encoding/json"
	"fmt"

	"github.com/aymerick/raymond"
)

type hash struct {
	indent int
}

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
func JSON(serializable interface{}, options struct {
	Hash hash
}) raymond.SafeString {

	jsonData, err := json.MarshalIndent(serializable, "", string(make([]byte, options.Hash.indent)))
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
func IfEquals(arg1, arg2 interface{}, options *raymond.Options) string {
	if arg1 == arg2 {
		return options.Fn()
	}
	return options.Inverse()
}

// UnlessEquals compares two values and returns the appropriate template content.
func UnlessEquals(arg1, arg2 interface{}, options *raymond.Options) string {
	if arg1 != arg2 {
		return options.Fn()
	}
	return options.Inverse()
}

// func init() {
// 	raymond.RegisterHelper("json", JSON)
// 	raymond.RegisterHelper("role", Role)
// 	raymond.RegisterHelper("history", History)
// 	raymond.RegisterHelper("section", Section)
// 	raymond.RegisterHelper("media", Media)
// 	raymond.RegisterHelper("ifEquals", IfEquals)
// 	raymond.RegisterHelper("unlessEquals", UnlessEquals)
// }
