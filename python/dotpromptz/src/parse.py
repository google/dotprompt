from dataclasses import dataclass, field
from typing import Any, TypeVar

import yaml

ModelConfig = TypeVar('ModelConfig', bound=dict[str, Any])


@dataclass
class MediaPart:
    url: str
    content_type: str | None = None


@dataclass
class Part:
    text: str | None = None
    media: MediaPart | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class Message:
    role: str
    content: list[Part]
    metadata: dict[str, Any] | None = None


@dataclass
class PromptMetadata:
    name: str | None = None
    variant: str | None = None
    version: str | None = None
    description: str | None = None
    model: str | None = None
    tools: list[Any] | None = None
    tool_defs: dict[str, Any] | None = None
    config: dict[str, Any] = field(default_factory=dict)
    input: dict[str, Any] | None = None
    output: dict[str, Any] | None = None
    raw: dict[str, Any] | None = None
    ext: dict[str, dict[str, Any]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedPrompt:
    metadata: dict[str, Any]
    config: dict[str, Any]
    ext: dict[str, dict[str, Any]]
    template: str
    raw: dict[str, Any] | None = None


@dataclass
class DataArgument:
    messages: list[Message] | None = None


FRONTMATTER_REGEX = r'^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$'
ROLE_REGEX = r'(<<<dotprompt:(?:role:[a-z]+|history))>>>'
PART_REGEX = r'(<<<dotprompt:(?:media:url|section).*?)>>>'

RESERVED_METADATA_KEYWORDS = [
    'name',
    'variant',
    'version',
    'description',
    'model',
    'tools',
    'tool_defs',
    'config',
    'input',
    'output',
    'raw',
    'ext',
]

BASE_METADATA = {'ext': {}, 'metadata': {}, 'config': {}}


def parse_document(source: str) -> ParsedPrompt:
    """Parse a document containing YAML frontmatter and template content."""
    match = re.match(FRONTMATTER_REGEX, source, re.MULTILINE)

    if match:
        frontmatter, content = match.groups()
        try:
            parsed_metadata = yaml.safe_load(frontmatter)
            raw = dict(parsed_metadata)
            pruned = dict(BASE_METADATA)
            ext: dict[str, dict[str, Any]] = {}

            for key, value in raw.items():
                if key in RESERVED_METADATA_KEYWORDS:
                    pruned[key] = value
                elif '.' in key:
                    namespace, field_name = key.rsplit('.', 1)
                    ext.setdefault(namespace, {})
                    ext[namespace][field_name] = value

            return ParsedPrompt(
                metadata=pruned.get('metadata', {}),
                config=pruned.get('config', {}),
                ext=ext,
                template=content.strip(),
                raw=raw,
            )
        except Exception as error:
            print(f'Dotprompt: Error parsing YAML frontmatter: {error}')
            return ParsedPrompt(
                metadata={}, config={}, ext={}, template=source.strip()
            )

    return ParsedPrompt(metadata={}, config={}, ext={}, template=source)
