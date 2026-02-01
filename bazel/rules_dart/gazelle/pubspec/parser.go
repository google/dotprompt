package pubspec

import (
	"fmt"
	"os"

	"gopkg.in/yaml.v3"
)

// ParsePubspec reads and parses a pubspec.yaml file
func ParsePubspec(path string) (*Pubspec, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read pubspec: %w", err)
	}

	var p Pubspec
	if err := yaml.Unmarshal(data, &p); err != nil {
		return nil, fmt.Errorf("failed to parse pubspec yaml: %w", err)
	}
	return &p, nil
}

// ParseLockfile reads and parses a pubspec.lock file
func ParseLockfile(path string) (*Lockfile, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read lockfile: %w", err)
	}

	var l Lockfile
	if err := yaml.Unmarshal(data, &l); err != nil {
		return nil, fmt.Errorf("failed to parse lockfile yaml: %w", err)
	}
	return &l, nil
}

// Helper methods to safe-cast Description

func (p PackageEntry) AsHosted() (*HostedDescription, error) {
	if p.Source != "hosted" {
		return nil, fmt.Errorf("not a hosted package")
	}
	// Convert map to struct
	// yaml.v3 decodes interface{} as map[string]interface{}
	m, ok := p.Description.(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("description is not a map")
	}

	h := &HostedDescription{}
	if val, ok := m["name"].(string); ok {
		h.Name = val
	}
	if val, ok := m["url"].(string); ok {
		h.Url = val
	}
	if val, ok := m["sha256"].(string); ok {
		h.Sha256 = val
	}

	return h, nil
}
