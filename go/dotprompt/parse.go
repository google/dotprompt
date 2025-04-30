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
	"fmt"
	"regexp"
	"slices"
	"strings"

	"github.com/goccy/go-yaml"
)

// MessageSource is a message with a source string and optional content and
// metadata.
type MessageSource struct {
	Role     Role           `json:"role" yaml:"role"`
	Source   string         `json:"source" yaml:"source"`
	Content  []Part         `json:"content" yaml:"content"`
	Metadata map[string]any `json:"metadata" yaml:"metadata"`
}

const (
	// Prefixes for the role markers in the template.
	RoleMarkerPrefix = "<<<dotprompt:role:"

	// Prefixes for the history markers in the template.
	HistoryMarkerPrefix = "<<<dotprompt:history"

	// Prefixes for the media markers in the template.
	MediaMarkerPrefix = "<<<dotprompt:media:"

	// Prefixes for the section markers in the template.
	SectionMarkerPrefix = "<<<dotprompt:section"
)

var (
	// FrontmatterAndBodyRegex is a regular expression to match YAML frontmatter
	// delineated by `---` markers at the start of a .prompt content block.
	FrontmatterAndBodyRegex = regexp.MustCompile(
		`^---\s*(?:\r\n|\r|\n)([\s\S]*?)(?:\r\n|\r|\n)---\s*(?:\r\n|\r|\n)([\s\S]*)$`)

	// EmptyFrontmatterRegex is a regular expression to match empty YAML
	// frontmatter (where there's no content between the frontmatter markers).
	EmptyFrontmatterRegex = regexp.MustCompile(`^---\s*\n---\s*\n([\s\S]*)$`)

	// RoleAndHistoryMarkerRegex is a regular expression to match
	// <<<dotprompt:role:xxx>>> and <<<dotprompt:history>>> markers in the
	// template.
	//
	// Note: Only lowercase letters are allowed after 'role:'.
	//
	// Examples of matching patterns:
	// - <<<dotprompt:role:user>>>
	// - <<<dotprompt:role:system>>>
	// - <<<dotprompt:history>>>
	RoleAndHistoryMarkerRegex = regexp.MustCompile(
		`(<<<dotprompt:(?:role:[a-z]+|history))>>>`)

	// MediaAndSectionMarkerRegex is a regular expression to match
	// <<<dotprompt:media:url>>> and <<<dotprompt:section>>> markers in the
	// template.
	//
	// Examples of matching patterns:
	// - <<<dotprompt:media:url>>>
	// - <<<dotprompt:section>>>
	MediaAndSectionMarkerRegex = regexp.MustCompile(
		`(<<<dotprompt:(?:media:url|section).*?)>>>`)
)

// ReservedMetadataKeywords is a list of keywords that are reserved for metadata
// in the frontmatter of a .prompt file. These keys are processed differently
// from extension metadata.
var ReservedMetadataKeywords = []string{
	// NOTE: KEEP SORTED
	"config",
	"description",
	"ext",
	"input",
	"model",
	"name",
	"output",
	"raw",
	"toolDefs",
	"tools",
	"variant",
	"version",
}

// splitByRegex splits a string by a regular expression and includes the matched
// regex patterns in the result while filtering out empty/whitespace-only
// pieces.
//
// NOTE: Since the behavior of regexp.Split is different in Python, JS, and Go,
// this function handles the different behavior between the specialized marker
// regexes and simple splitting regexes to mimic their behavior.
//
// For marker regexes with capturing groups (delineated by parens), it includes
// the capturing group in the result.  For simple regexes, it behaves like
// regexp.Split, removing the matched separators.
func splitByRegex(source string, regex *regexp.Regexp) []string {
	// Check if the regex is one of the marker regexes by looking for capturing
	// groups in the pattern.
	hasCapturingGroups := strings.Contains(regex.String(), "(")

	if !hasCapturingGroups {
		pieces := regex.Split(source, -1)

		// Filter out empty or whitespace-only pieces.
		var result []string
		for _, s := range pieces {
			if strings.TrimSpace(s) != "" {
				result = append(result, s)
			}
		}
		return result
	}

	// For marker regexes with capturing groups, include the matched portions.
	matches := regex.FindAllStringSubmatchIndex(source, -1)
	if len(matches) == 0 {
		if strings.TrimSpace(source) != "" {
			return []string{source}
		}
		return []string{}
	}

	var result []string
	lastEnd := 0

	// Process each match and the text before it
	for _, match := range matches {
		start := match[0] // Start of the full match.
		end := match[1]   // End of the full match.

		// If there's text before the match that isn't empty...
		if start > lastEnd {
			textBefore := source[lastEnd:start]
			if strings.TrimSpace(textBefore) != "" {
				result = append(result, textBefore)
			}
		}

		// Add the capturing group (not the full match).
		groupStart := match[2] // Start of first capturing group.
		groupEnd := match[3]   // End of first capturing group.

		if groupStart >= 0 && groupEnd >= 0 {
			matchText := source[groupStart:groupEnd]
			if strings.TrimSpace(matchText) != "" {
				result = append(result, matchText)
			}
		}

		lastEnd = end
	}

	// If there's text after the last match that isn't empty...
	if lastEnd < len(source) {
		textAfter := source[lastEnd:]
		if strings.TrimSpace(textAfter) != "" {
			result = append(result, textAfter)
		}
	}

	return result
}

// splitByRoleAndHistoryMarkers splits a string by role and history markers.
func splitByRoleAndHistoryMarkers(source string) []string {
	return splitByRegex(source, RoleAndHistoryMarkerRegex)
}

// splitByMediaAndSectionMarkers splits a string by media and section markers.
func splitByMediaAndSectionMarkers(source string) []string {
	return splitByRegex(source, MediaAndSectionMarkerRegex)
}

// convertNamespacedEntryToNestedObject converts a namespaced entry to a nested
// object.
//
// For example, 'foo.bar': 'value' becomes { foo: { bar: 'value' } }
func convertNamespacedEntryToNestedObject(
	key string,
	value any,
	obj map[string]map[string]any) map[string]map[string]any {
	// NOTE: Goes only a single level deep.
	if obj == nil {
		obj = make(map[string]map[string]any)
	}

	lastDotIndex := strings.LastIndex(key, ".")
	ns := key[:lastDotIndex]
	field := key[lastDotIndex+1:]

	// Ensure the namespace exists.
	if _, exists := obj[ns]; !exists {
		obj[ns] = make(map[string]any)
	}

	obj[ns][field] = value
	return obj
}

// extractFrontmatterAndBody extracts the frontmatter and body from a .prompt
// file.
func extractFrontmatterAndBody(source string) (string, string) {
	match := FrontmatterAndBodyRegex.FindStringSubmatch(source)
	if match == nil {
		// Try the empty frontmatter pattern
		match = EmptyFrontmatterRegex.FindStringSubmatch(source)
		if match == nil {
			return "", ""
		}
		return "", match[1]
	}
	frontmatter, body := match[1], match[2]
	return frontmatter, body
}

// ParseDocument parses a document containing YAML frontmatter and a template
// content section.  The frontmatter contains metadata and configuration for the
// prompt.
func ParseDocument(source string) (ParsedPrompt, error) {
	frontmatter, body := extractFrontmatterAndBody(source)
	promptMetadata := PromptMetadata{
		Ext: make(map[string]map[string]any),
	}

	if frontmatter != "" {
		var parsedMetadata map[string]any
		// The github.com/goccy/go-yaml library can panic on certain malformed YAML
		// so we need to use a custom error handler to recover from panics
		var err error
		func() {
			defer func() {
				if r := recover(); r != nil {
					err = fmt.Errorf("panic while parsing YAML: %v", r)
				}
			}()
			err = yaml.Unmarshal([]byte(frontmatter), &parsedMetadata)
		}()

		if err != nil {
			fmt.Printf("Dotprompt: Error parsing YAML frontmatter: %v\n", err)
			// Return a basic ParsedPrompt with just the template
			return ParsedPrompt{
				PromptMetadata: promptMetadata,
				Template:       trimUnicodeSpacesExceptNewlines(source),
			}, nil
		}

		raw := copyMapping(parsedMetadata)
		pruned := PromptMetadata{
			Ext: make(map[string]map[string]any),
		}
		ext := make(map[string]map[string]any)

		for key, value := range raw {
			if slices.Contains(ReservedMetadataKeywords, key) {
				// Add to pruned metadata.
				switch key {
				case "name":
					pruned.Name = stringOrEmpty(value)
				case "description":
					pruned.Description = stringOrEmpty(value)
				case "variant":
					pruned.Variant = stringOrEmpty(value)
				case "version":
					pruned.Version = stringOrEmpty(value)
				case "model":
					pruned.Model = stringOrEmpty(value)
				case "config":
					if configMap, ok := value.(map[string]any); ok {
						pruned.Config = configMap
					}
				case "tools":
					if toolsSlice, ok := value.([]any); ok {
						tools := make([]string, 0, len(toolsSlice))
						for _, t := range toolsSlice {
							if toolStr, ok := t.(string); ok {
								tools = append(tools, toolStr)
							}
						}
						pruned.Tools = tools
					}
				case "toolDefs":
					if toolDefsSlice, ok := value.([]any); ok {
						toolDefs := make([]ToolDefinition, 0, len(toolDefsSlice))
						for _, td := range toolDefsSlice {
							if tdMap, ok := td.(map[string]any); ok {
								toolDef := ToolDefinition{
									Name:        stringOrEmpty(tdMap["name"]),
									Description: stringOrEmpty(tdMap["description"]),
								}
								if inputSchema, ok := tdMap["inputSchema"].(map[string]any); ok {
									toolDef.InputSchema = inputSchema
								}
								if outputSchema, ok := tdMap["outputSchema"].(map[string]any); ok {
									toolDef.OutputSchema = outputSchema
								}
								toolDefs = append(toolDefs, toolDef)
							}
						}
						pruned.ToolDefs = toolDefs
					}
				case "input":
					if inputMap, ok := value.(map[string]any); ok {
						if defaultMap, ok := inputMap["default"].(map[string]any); ok {
							pruned.Input.Default = defaultMap
						}
						if schemaMap, ok := inputMap["schema"].(map[string]any); ok {
							pruned.Input.Schema = schemaMap
						}
						if schemaMap, ok := inputMap["schema"].(string); ok {
							pruned.Input.Schema = schemaMap
						}
					}
				case "output":
					if outputMap, ok := value.(map[string]any); ok {
						if formatMap, ok := outputMap["format"].(string); ok {
							pruned.Output.Format = formatMap
						}
						if schemaMap, ok := outputMap["schema"].(map[string]any); ok {
							pruned.Output.Schema = schemaMap
						}
						if schemaMap, ok := outputMap["schema"].(string); ok {
							pruned.Output.Schema = schemaMap
						}
					}
				}
			} else if strings.Contains(key, ".") {
				convertNamespacedEntryToNestedObject(key, value, ext)
			}
		}

		// Set the raw and ext fields
		pruned.Raw = raw
		pruned.Ext = ext

		return ParsedPrompt{
			PromptMetadata: pruned,
			Template:       strings.TrimSpace(body),
		}, nil
	}

	// If we have a body from frontmatter extraction, use it
	if body != "" {
		return ParsedPrompt{
			PromptMetadata: promptMetadata,
			Template:       trimUnicodeSpacesExceptNewlines(body),
		}, nil
	}

	// No frontmatter or body extracted, return the original source as template
	return ParsedPrompt{
		PromptMetadata: promptMetadata,
		Template:       source,
	}, nil
}

// ToMessages converts a rendered template string into an array of messages.
func ToMessages(renderedString string, data *DataArgument) ([]Message, error) {
	// Create the initial message source with empty content.
	ms := &MessageSource{
		Role:   RoleUser,
		Source: "",
	}
	messageSources := []*MessageSource{ms}

	for _, piece := range splitByRoleAndHistoryMarkers(renderedString) {
		if strings.HasPrefix(piece, RoleMarkerPrefix) {
			roleStr := piece[len(RoleMarkerPrefix):]
			role := Role(roleStr)

			if messageSources[len(messageSources)-1].Source != "" &&
				trimUnicodeSpacesExceptNewlines(messageSources[len(messageSources)-1].Source) != "" {
				// If the current message has content, create a new message.
				newMs := &MessageSource{
					Role:   role,
					Source: "",
				}
				messageSources = append(messageSources, newMs)
			} else {
				// Otherwise, update the role of the current message.
				messageSources[len(messageSources)-1].Role = role
			}
		} else if strings.HasPrefix(piece, HistoryMarkerPrefix) {
			// Add the history messages to the message sources.
			var msgs []Message
			if data != nil && data.Messages != nil {
				msgs = data.Messages
			}

			historyMessages, err := transformMessagesToHistory(msgs)
			if err != nil {
				return nil, err
			}

			if len(historyMessages) > 0 {
				for _, msg := range historyMessages {
					messageSources = append(messageSources, &MessageSource{
						Role:     msg.Role,
						Content:  msg.Content,
						Metadata: msg.Metadata,
					})
				}
			}

			newMs := &MessageSource{
				Role:   RoleModel,
				Source: "",
			}
			messageSources = append(messageSources, newMs)
		} else {
			// Otherwise, add the piece to the current message source.
			messageSources[len(messageSources)-1].Source += piece
		}
	}

	messages, err := messageSourcesToMessages(messageSources)
	if err != nil {
		return nil, err
	}

	if data != nil {
		return insertHistory(messages, data.Messages)
	}
	return insertHistory(messages, []Message{})
}

// messageSourcesToMessages converts an array of message sources to an array of
// messages.
func messageSourcesToMessages(
	messageSources []*MessageSource) ([]Message, error) {
	messages := []Message{}

	for _, m := range messageSources {
		// Only skip messages that have both empty Content and empty Source.
		if m.Content == nil && strings.TrimSpace(m.Source) == "" {
			continue
		}

		out := Message{
			Role: m.Role,
		}

		if m.Content != nil {
			out.Content = m.Content
		} else {
			parts, err := toParts(m.Source)
			if err != nil {
				return nil, err
			}
			out.Content = parts
		}

		if m.Metadata != nil {
			out.Metadata = m.Metadata
		}

		messages = append(messages, out)
	}

	return messages, nil
}

// transformMessagesToHistory adds history metadata to an array of messages.
func transformMessagesToHistory(messages []Message) ([]Message, error) {
	result := make([]Message, len(messages))

	for i, message := range messages {
		newMetadata := copyMapping(message.Metadata)
		newMetadata["purpose"] = "history"
		result[i] = Message{
			Role:        message.Role,
			Content:     message.Content,
			HasMetadata: HasMetadata{Metadata: newMetadata},
		}
	}

	return result, nil
}

// messagesHaveHistory checks if the messages have history metadata.
func messagesHaveHistory(messages []Message) bool {
	for _, msg := range messages {
		if msg.Metadata != nil {
			if purpose, ok := msg.Metadata["purpose"]; ok {
				if purpose == "history" {
					return true
				}
			}
		}
	}

	return false
}

// insertHistory inserts historical messages into the conversation.
//
// The history is inserted at:
// - The end of the conversation if there is no history or no user message.
// - Before the last user message if there is a user message.
//
// The history is not inserted:
// - If it already exists in the messages.
// - If there is no user message.
func insertHistory(messages []Message, history []Message) ([]Message, error) {
	// If we have no history or find an existing instance of history, return the
	// original messages.
	h := len(history)
	if h == 0 || messagesHaveHistory(messages) {
		return messages, nil
	}

	// If there are no messages, return the history.
	if len(messages) == 0 {
		return history, nil
	}

	// If the last message is a user message, insert history before it.
	lastMessage := messages[len(messages)-1]
	if lastMessage.Role == RoleUser {
		m := len(messages)
		result := make([]Message, 0, m-1+h+1)

		// Sandwich the history between the last user message and the new user
		// message.
		result = append(result, messages[:m-1]...)
		result = append(result, history...)
		result = append(result, lastMessage)

		return result, nil
	}

	// Otherwise, append history to the end of the messages.
	return append(messages, history...), nil
}

// toParts converts a source string into an array of parts (text, media, or
// metadata).
//
// Also processes media and section markers.
func toParts(source string) ([]Part, error) {
	parts := []Part{}

	for _, piece := range splitByMediaAndSectionMarkers(source) {
		part, err := parsePart(piece)
		if err != nil {
			return nil, err
		}
		parts = append(parts, part)
	}

	return parts, nil
}

// parsePart parses a part from piece of rendered template.
func parsePart(piece string) (Part, error) {
	if strings.HasPrefix(piece, MediaMarkerPrefix) {
		return parseMediaPart(piece)
	} else if strings.HasPrefix(piece, SectionMarkerPrefix) {
		return parseSectionPart(piece)
	} else {
		return parseTextPart(piece)
	}
}

// parseMediaPart parses a media part from a piece of rendered template.
func parseMediaPart(piece string) (*MediaPart, error) {
	if !strings.HasPrefix(piece, MediaMarkerPrefix) {
		return nil, fmt.Errorf(
			"invalid media piece: %s; expected prefix %s",
			piece, MediaMarkerPrefix)
	}

	fields := strings.Split(piece, " ")
	n := len(fields)

	var url, contentType string
	switch n {
	case 3:
		url, contentType = fields[1], fields[2]
	case 2:
		url = fields[1]
	default:
		return nil, fmt.Errorf(
			"invalid media piece: %s; expected 2 or 3 fields, found %d",
			piece, n)
	}

	mediaPart := &MediaPart{
		Media: Media{
			URL:         url,
			ContentType: contentType,
		},
		HasMetadata: HasMetadata{},
	}

	if contentType != "" && strings.TrimSpace(contentType) != "" {
		mediaPart.Media.ContentType = contentType
	}

	return mediaPart, nil
}

// parseSectionPart parses a section part from a piece of rendered template.
func parseSectionPart(piece string) (*PendingPart, error) {
	if !strings.HasPrefix(piece, SectionMarkerPrefix) {
		return nil, fmt.Errorf(
			"invalid section piece: %s; expected prefix %s",
			piece, SectionMarkerPrefix)
	}

	fields := strings.Split(piece, " ")
	n := len(fields)
	if n != 2 {
		return nil, fmt.Errorf(
			"invalid section piece: %s; expected 2 fields, found %d", piece, n)
	}

	sectionType := strings.TrimSpace(fields[1])
	pendingPart := NewPendingPart()
	pendingPart.SetMetadata("purpose", sectionType)

	return pendingPart, nil
}

// parseTextPart parses a text part from a piece of rendered template.
func parseTextPart(piece string) (*TextPart, error) {
	return &TextPart{
		HasMetadata: HasMetadata{},
		Text:        piece,
	}, nil
}
