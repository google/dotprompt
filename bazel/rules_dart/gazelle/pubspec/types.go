package pubspec

// Pubspec represents pubspec.yaml
type Pubspec struct {
	Name            string                 `yaml:"name"`
	Dependencies    map[string]interface{} `yaml:"dependencies"`
	DevDependencies map[string]interface{} `yaml:"dev_dependencies"`
	Environment     map[string]string      `yaml:"environment"`
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
