// Copyright 2025 Google LLC
// SPDX-License-Identifier: Apache-2.0

package dotprompt

import (
	"regexp"
	"strings"

	"gopkg.in/yaml.v3"
)

var (
	// FrontmatterAndBodyRegex matches YAML frontmatter delineated by `---` markers
	FrontmatterAndBodyRegex = regexp.MustCompile(`^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$`)

	// RoleAndHistoryMarkerRegex matches role and history markers
	RoleAndHistoryMarkerRegex = regexp.MustCompile(`(<<<dotprompt:(?:role:[a-z]+|history))>>>`)

	// MediaAndSectionMarkerRegex matches media and section markers
	MediaAndSectionMarkerRegex = regexp.MustCompile(`(<<<dotprompt:(?:media:url|section).*?)>>>`)

	// ReservedMetadataKeywords are handled specially in the metadata
	ReservedMetadataKeywords = []string{
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

	// BaseMetadata is the default metadata structure
	BaseMetadata = PromptMetadata[any]{
		Ext:      map[string]map[string]interface{}{},
		Metadata: map[string]interface{}{},
		Config:   nil,
	}
)

// SplitByRegex splits a string by a regular expression while filtering out
// empty/whitespace-only pieces.
func SplitByRegex(source string, regex *regexp.Regexp) []string {
	parts := regex.Split(source, -1)
	result := make([]string, 0, len(parts))
	for _, part := range parts {
		if strings.TrimSpace(part) != "" {
			result = append(result, part)
		}
	}
	return result
}

// SplitByRoleAndHistoryMarkers splits a rendered template string into pieces
// based on role and history markers.
func SplitByRoleAndHistoryMarkers(renderedString string) []string {
	return SplitByRegex(renderedString, RoleAndHistoryMarkerRegex)
}

// SplitByMediaAndSectionMarkers splits the source into pieces based on media
// and section markers.
func SplitByMediaAndSectionMarkers(source string) []string {
	return SplitByRegex(source, MediaAndSectionMarkerRegex)
}

// ConvertNamespacedEntryToNestedObject processes a namespaced key-value pair into
// a nested object structure.
func ConvertNamespacedEntryToNestedObject(key string, value interface{}, obj map[string]map[string]interface{}) map[string]map[string]interface{} {
	if obj == nil {
		obj = make(map[string]map[string]interface{})
	}

	lastDotIndex := strings.LastIndex(key, ".")
	if lastDotIndex == -1 {
		return obj
	}

	ns := key[:lastDotIndex]
	field := key[lastDotIndex+1:]

	if obj[ns] == nil {
		obj[ns] = make(map[string]interface{})
	}
	obj[ns][field] = value
	return obj
}

// ExtractFrontmatterAndBody extracts the YAML frontmatter and body from a document.
func ExtractFrontmatterAndBody(source string) (frontmatter, body string) {
	matches := FrontmatterAndBodyRegex.FindStringSubmatch(source)
	if len(matches) == 3 {
		return matches[1], matches[2]
	}
	return "", ""
}

// ParseDocument parses a document containing YAML frontmatter and a template content section.
func ParseDocument[ModelConfig any](source string) ParsedPrompt[ModelConfig] {
	frontmatter, body := ExtractFrontmatterAndBody(source)
	if frontmatter != "" {
		var parsedMetadata map[string]interface{}
		if err := yaml.Unmarshal([]byte(frontmatter), &parsedMetadata); err != nil {
			return ParsedPrompt[ModelConfig]{
				PromptMetadata: BaseMetadata,
				Template:       strings.TrimSpace(source),
			}
		}

		raw := make(map[string]interface{})
		for k, v := range parsedMetadata {
			raw[k] = v
		}

		pruned := BaseMetadata
		ext := make(map[string]map[string]interface{})

		for key, value := range parsedMetadata {
			isReserved := false
			for _, reserved := range ReservedMetadataKeywords {
				if key == reserved {
					isReserved = true
					break
				}
			}

			if isReserved {
				switch key {
				case "config":
					if cfg, ok := value.(ModelConfig); ok {
						pruned.Config = &cfg
					}
				case "description":
					if str, ok := value.(string); ok {
						pruned.Description = &str
					}
				case "model":
					if str, ok := value.(string); ok {
						pruned.Model = &str
					}
				case "name":
					if str, ok := value.(string); ok {
						pruned.Name = &str
					}
				case "variant":
					if str, ok := value.(string); ok {
						pruned.Variant = &str
					}
				case "version":
					if str, ok := value.(string); ok {
						pruned.Version = &str
					}
				case "tools":
					if arr, ok := value.([]string); ok {
						pruned.Tools = arr
					}
				case "toolDefs":
					if arr, ok := value.([]ToolDefinition); ok {
						pruned.ToolDefs = arr
					}
				case "input":
					if m, ok := value.(map[string]interface{}); ok {
						pruned.Input = &struct {
							Default *map[string]interface{} `json:"default,omitempty"`
							Schema  *Schema                 `json:"schema,omitempty"`
						}{}
						if def, ok := m["default"].(map[string]interface{}); ok {
							pruned.Input.Default = &def
						}
						if schema, ok := m["schema"].(Schema); ok {
							pruned.Input.Schema = &schema
						}
					}
				case "output":
					if m, ok := value.(map[string]interface{}); ok {
						pruned.Output = &struct {
							Format *string `json:"format,omitempty"`
							Schema *Schema `json:"schema,omitempty"`
						}{}
						if format, ok := m["format"].(string); ok {
							pruned.Output.Format = &format
						}
						if schema, ok := m["schema"].(Schema); ok {
							pruned.Output.Schema = &schema
						}
					}
				}
			} else if strings.Contains(key, ".") {
				ConvertNamespacedEntryToNestedObject(key, value, ext)
			}
		}

		pruned.Raw = raw
		pruned.Ext = ext

		return ParsedPrompt[ModelConfig]{
			PromptMetadata: pruned,
			Template:       strings.TrimSpace(body),
		}
	}

	return ParsedPrompt[ModelConfig]{
		PromptMetadata: BaseMetadata,
		Template:       strings.TrimSpace(source),
	}
}

// ToMessages converts a rendered template string into an array of messages.
func ToMessages[ModelConfig any](renderedString string, data *DataArgument[interface{}, interface{}]) []Message {
	type messageSource struct {
		Role     string
		Source   string
		Content  []Part
		Metadata map[string]interface{}
	}

	currentMessage := messageSource{Role: "user"}
	messageSources := []messageSource{currentMessage}

	for _, piece := range SplitByRoleAndHistoryMarkers(renderedString) {
		if strings.HasPrefix(piece, "<<<dotprompt:role:") {
			role := piece[18:]
			if strings.TrimSpace(currentMessage.Source) != "" {
				currentMessage = messageSource{Role: role}
				messageSources = append(messageSources, currentMessage)
			} else {
				currentMessage.Role = role
			}
		} else if strings.HasPrefix(piece, "<<<dotprompt:history") {
			if data != nil && data.Messages != nil {
				messageSources = append(messageSources, transformMessagesToHistory(data.Messages)...)
			}
			currentMessage = messageSource{Role: "model"}
			messageSources = append(messageSources, currentMessage)
		} else {
			currentMessage.Source += piece
		}
	}

	messages := make([]Message, 0, len(messageSources))
	for _, ms := range messageSources {
		if len(ms.Content) > 0 || ms.Source != "" {
			msg := Message{Role: Role(ms.Role)}
			if len(ms.Content) > 0 {
				msg.Content = ms.Content
			} else {
				msg.Content = ToParts(ms.Source)
			}
			if ms.Metadata != nil {
				msg.Metadata = ms.Metadata
			}
			messages = append(messages, msg)
		}
	}

	if data != nil {
		return InsertHistory(messages, data.Messages)
	}
	return messages
}

// TransformMessagesToHistory transforms an array of messages by adding history metadata.
func transformMessagesToHistory(messages []Message) []messageSource {
	sources := make([]messageSource, len(messages))
	for i, m := range messages {
		metadata := make(map[string]interface{})
		if m.Metadata != nil {
			for k, v := range m.Metadata {
				metadata[k] = v
			}
		}
		metadata["purpose"] = "history"
		sources[i] = messageSource{
			Role:     string(m.Role),
			Content:  m.Content,
			Metadata: metadata,
		}
	}
	return sources
}

// InsertHistory inserts historical messages into the conversation.
func InsertHistory(messages []Message, history []Message) []Message {
	if len(history) == 0 {
		return messages
	}

	for _, m := range messages {
		if m.Metadata != nil {
			if _, ok := m.Metadata["purpose"]; ok && m.Metadata["purpose"] == "history" {
				return messages
			}
		}
	}

	if len(messages) > 0 && messages[len(messages)-1].Role == RoleUser {
		result := make([]Message, 0, len(messages)+len(history))
		result = append(result, messages[:len(messages)-1]...)
		result = append(result, history...)
		result = append(result, messages[len(messages)-1])
		return result
	}

	return append(messages, history...)
}

// ToParts converts a source string into an array of parts.
func ToParts(source string) []Part {
	parts := make([]Part, 0)
	pieces := SplitByMediaAndSectionMarkers(source)

	for _, piece := range pieces {
		if strings.HasPrefix(piece, "<<<dotprompt:media:") {
			fields := strings.Fields(piece)
			if len(fields) >= 2 {
				part := &MediaPart{
					Media: struct {
						URL         string  `json:"url"`
						ContentType *string `json:"contentType,omitempty"`
					}{
						URL: fields[1],
					},
				}
				if len(fields) >= 3 {
					contentType := fields[2]
					part.Media.ContentType = &contentType
				}
				parts = append(parts, part)
			}
		} else if strings.HasPrefix(piece, "<<<dotprompt:section") {
			fields := strings.Fields(piece)
			metadata := map[string]interface{}{
				"pending": true,
			}
			if len(fields) >= 2 {
				metadata["purpose"] = fields[1]
			}
			parts = append(parts, &PendingPart{
				HasMetadata: HasMetadata{
					Metadata: metadata,
				},
			})
		} else {
			parts = append(parts, &TextPart{Text: piece})
		}
	}

	return parts
}
