import yaml
from typing import List, Dict, Any, TypeVar, Optional, Union
from dataclasses import dataclass, field

ModelConfig = TypeVar('ModelConfig', bound=Dict[str, Any])

@dataclass
class MediaPart:
    url: str
    content_type: Optional[str] = None

@dataclass
class Part:
    text: Optional[str] = None
    media: Optional[MediaPart] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Message:
    role: str
    content: List[Part]
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class PromptMetadata:
    name: Optional[str] = None
    variant: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    model: Optional[str] = None
    tools: Optional[List[Any]] = None
    tool_defs: Optional[Dict[str, Any]] = None
    config: Dict[str, Any] = field(default_factory=dict)
    input: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None
    raw: Optional[Dict[str, Any]] = None
    ext: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ParsedPrompt:
    metadata: Dict[str, Any]
    config: Dict[str, Any]
    ext: Dict[str, Dict[str, Any]]
    template: str
    raw: Optional[Dict[str, Any]] = None

@dataclass
class DataArgument:
    messages: Optional[List[Message]] = None

FRONTMATTER_REGEX = r'^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$'
ROLE_REGEX = r'(<<<dotprompt:(?:role:[a-z]+|history))>>>'
PART_REGEX = r'(<<<dotprompt:(?:media:url|section).*?)>>>'

RESERVED_METADATA_KEYWORDS = [
    'name', 'variant', 'version', 'description', 'model',
    'tools', 'tool_defs', 'config', 'input', 'output', 'raw', 'ext'
]

BASE_METADATA = {
    'ext': {},
    'metadata': {},
    'config': {}
}

def parse_document(source: str) -> ParsedPrompt:
    """Parse a document containing YAML frontmatter and template content."""
    match = re.match(FRONTMATTER_REGEX, source, re.MULTILINE)
    
    if match:
        frontmatter, content = match.groups()
        try:
            parsed_metadata = yaml.safe_load(frontmatter)
            raw = dict(parsed_metadata)
            pruned = dict(BASE_METADATA)
            ext: Dict[str, Dict[str, Any]] = {}

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
                raw=raw
            )
        except Exception as error:
            print(f"Dotprompt: Error parsing YAML frontmatter: {error}")
            return ParsedPrompt(
                metadata={},
                config={},
                ext={},
                template=source.strip()
            )

    return ParsedPrompt(
        metadata={},
        config={},
        ext={},
        template=source)