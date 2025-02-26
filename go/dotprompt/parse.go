package dotprompt

import (
	"fmt"
	"reflect"
	"regexp"
	"strings"

	"gopkg.in/yaml.v3"
)

var (
	FRONTMATTER_REGEX          = regexp.MustCompile(`^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$`)
	RESERVED_METADATA_KEYWORDS = []string{
		"name", "variant", "version", "description", "model", "tools", "toolDefs", "config", "input", "output", "raw", "ext",
	}
	BASE_METADATA = PromptMetadata{
		Ext:         make(map[string]map[string]interface{}),
		HasMetadata: HasMetadata{},
		Config:      make(map[string]interface{}),
	}
	ROLE_REGEX = regexp.MustCompile(`(<<<dotprompt:(?:role:[a-z]+|history))>>>`)
	PART_REGEX = regexp.MustCompile(`(<<<dotprompt:(?:media:url|section).*?)>>>`)
)

// trimSpaces trims only the leading and trailing spaces but preserves newline characters.
func trimSpaces(s string) string {
	return strings.Trim(s, " \t")
}

// ParseDocument parses the source string into a ParsedPrompt.
func ParseDocument(source string) ParsedPrompt {
	match := FRONTMATTER_REGEX.FindStringSubmatch(source)
	if match != nil {
		frontmatter := match[1]
		content := match[2]
		var parsedMetadata map[string]interface{}
		err := yaml.Unmarshal([]byte(frontmatter), &parsedMetadata)
		if err != nil {
			fmt.Println("Dotprompt: Error parsing YAML frontmatter:", err)
			return ParsedPrompt{
				PromptMetadata: BASE_METADATA,
				Template:       trimSpaces(source),
			}
		}
		raw := parsedMetadata
		pruned := BASE_METADATA
		ext := make(map[string]map[string]interface{})

		for k, v := range raw {
			if contains(RESERVED_METADATA_KEYWORDS, k) {
				prunedVal := reflect.ValueOf(&pruned).Elem()
				fieldVal := prunedVal.FieldByName(strings.Title(k))
				if fieldVal.IsValid() && fieldVal.CanSet() {
					fieldVal.Set(reflect.ValueOf(v))
				}
			} else if strings.Contains(k, ".") {
				lastDotIndex := strings.LastIndex(k, ".")
				namespace := k[:lastDotIndex]
				fieldName := k[lastDotIndex+1:]
				if ext[namespace] == nil {
					ext[namespace] = make(map[string]interface{})
				}
				ext[namespace][fieldName] = v
			}
		}
		pruned.Raw = parsedMetadata
		pruned.Ext = ext
		return ParsedPrompt{
			PromptMetadata: pruned,
			Template:       trimSpaces(content),
		}
	}
	return ParsedPrompt{
		PromptMetadata: BASE_METADATA,
		Template:       trimSpaces(source),
	}
}

// contains checks if a slice contains a string.
func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

type MessageSource struct {
	Role     string                 `json:"role"`
	Source   string                 `json:"source,omitempty"`
	Content  []Part                 `json:"content,omitempty"`
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// ToMessages converts a rendered string into a slice of messages.
func ToMessages(renderedString string, data DataArgument) []Message {
	currentMessage := &MessageSource{
		Role:   "user",
		Source: "",
	}
	messageSources := []*MessageSource{currentMessage}

	pieces := ROLE_REGEX.Split(renderedString, -1)
	for _, piece := range pieces {
		if strings.HasPrefix(piece, "<<<dotprompt:role:") {
			role := piece[18:]
			if trimSpaces(currentMessage.Source) != "" {
				currentMessage = &MessageSource{Role: role, Source: ""}
				messageSources = append(messageSources, currentMessage)
			} else {
				currentMessage.Role = role
			}
		} else if strings.HasPrefix(piece, "<<<dotprompt:history") {
			if data.Messages != nil {
				for _, m := range data.Messages {
					m.HasMetadata.Metadata["purpose"] = "history"
					messageSources = append(messageSources, &MessageSource{
						Role:     m.Role,
						Content:  m.Content,
						Metadata: m.HasMetadata.Metadata,
					})
				}
			}
			currentMessage = &MessageSource{
				Role:   "model",
				Source: "",
			}
			messageSources = append(messageSources, currentMessage)
		} else {
			currentMessage.Source += piece
		}
	}

	var messages []Message
	for _, m := range messageSources {
		if m.Content != nil || m.Source != "" {
			message := Message{
				Role:    m.Role,
				Content: toParts(m.Source),
			}
			if m.Metadata != nil {
				message.HasMetadata.Metadata = m.Metadata
			}
			messages = append(messages, message)
		}
	}

	return insertHistory(messages, data.Messages)
}

// insertHistory inserts history messages into the messages slice.
func insertHistory(messages []Message, history []Message) []Message {
	if len(history) == 0 || containsHistory(messages) {
		return messages
	}
	if messages[len(messages)-1].Role == "user" {
		return append(append(messages[:len(messages)-1], history...), messages[len(messages)-1])
	}
	return append(messages, history...)
}

// containsHistory checks if the messages slice contains history messages.
func containsHistory(messages []Message) bool {
	for _, m := range messages {
		if m.HasMetadata.Metadata != nil && m.HasMetadata.Metadata["purpose"] == "history" {
			return true
		}
	}
	return false
}

// toParts converts a source string into a slice of parts.
func toParts(source string) []Part {
	var parts []Part
	pieces := PART_REGEX.Split(source, -1)
	for _, piece := range pieces {
		if strings.HasPrefix(piece, "<<<dotprompt:media:") {
			parts = append(parts, parseMediaPart(piece))
		} else if strings.HasPrefix(piece, "<<<dotprompt:section") {
			parts = append(parts, parseSectionPart(piece))
		} else {
			parts = append(parts, Part{
				Text: TextPart{
					Text: piece,
				},
			})
		}
	}
	return parts
}

// parseMediaPart parses a media part from a string.
func parseMediaPart(piece string) Part {
	parts := strings.Split(piece, " ")
	url := parts[1]
	var contentType string
	if len(parts) > 2 {
		contentType = parts[2]
	}
	return Part{
		Media: MediaPart{
			Media: MediaType{
				URL:         url,
				ContentType: contentType,
			},
		},
	}
}

// parseSectionPart parses a section part from a string.
func parseSectionPart(piece string) Part {
	parts := strings.Split(piece, " ")
	sectionType := parts[1]
	return Part{
		Metadata: map[string]interface{}{
			"purpose": sectionType,
			"pending": true,
		},
	}
}
