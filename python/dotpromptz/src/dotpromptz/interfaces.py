# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Data models and interfaces definition."""

from dataclasses import dataclass, field
from typing import Any, Generic, Literal, Protocol, TypeVar

T = TypeVar('T')


type Schema = dict[str, Any]


@dataclass
class ToolDefinition:
    """Definition of a tool that can be used in a prompt.

    Attributes:
        name: The name of the tool.
        description: A description of the tool.
        input_schema: The input schema of the tool.
        output_schema: The output schema of the tool.
    """

    name: str
    description: str | None
    input_schema: Schema = field(default_factory=dict)
    output_schema: Schema | None = None


type ToolArgument = str | ToolDefinition


@dataclass
class HasMetadata:
    """Whether contains metadata.

    Attributes:
        metadata: Arbitrary metadata to be used by tooling or for informational
            purposes.
    """

    metadata: dict[str, Any] | None = None


@dataclass(kw_only=True)
class PromptRef:
    """Reference to a prompt with optional variant.

    Attributes:
        name: The name of the prompt.
        variant: The variant name for the prompt.
        version: The version of the prompt.
    """

    name: str
    variant: str | None = None
    version: str | None = None


@dataclass(kw_only=True)
class PromptData(PromptRef):
    """Prompt data containing source and metadata.

    Attributes:
        source: The source of the prompt.
    """

    source: str


@dataclass
class PromptMetadata(HasMetadata, Generic[T]):
    """Prompt metadata.

    Attributes:
        name: The name of the prompt.
        variant: The variant name for the prompt.
        version: The version of the prompt.
        description: A description of the prompt.
        model: The name of the model to use for this prompt, e.g.
            `vertexai/gemini-1.0-pro`.
        tools: Names of tools (registered separately) to allow use of in this
            prompt.
        tool_defs: Definitions of tools to allow use of in this prompt.
        config: Model configuration. Not all models support all options.
        input: Configuration for input variables.
        output: Defines the expected model output format.
        raw: This field will contain the raw frontmatter as parsed with no
            additional processing or substitutions. If your implementation
            requires custom fields they will be available here.
        ext: Fields that contain a period will be considered "extension fields"
            in the frontmatter and will be gathered by namespace. For example,
            `myext.foo: 123` would be available at `parsedPrompt.ext.myext.foo`.
            Nested namespaces will be flattened, so `myext.foo.bar: 123` would
            be available at `parsedPrompt.ext["myext.foo"].bar`.
    """

    name: str | None = None
    variant: str | None = None
    version: str | None = None
    description: str | None = None
    model: str | None = None
    tools: list[str] | None = None
    tool_defs: list[ToolDefinition] | None = None
    config: T | None = None
    input: dict[str, Any] | None = None
    output: dict[str, Any] | None = None
    raw: dict[str, Any] | None = None
    ext: dict[str, dict[str, Any]] | None = None


@dataclass(kw_only=True)
class ParsedPrompt(PromptMetadata[T]):
    """Parsed prompt containing template and metadata.

    Attributes:
        template: The template of the prompt.
    """

    template: str


@dataclass
class EmptyPart(HasMetadata):
    """Base class for all parts with metadata."""


@dataclass(kw_only=True)
class TextPart(EmptyPart):
    """Part containing text content.

    Attributes:
        text: The text content of the part.
    """

    text: str


@dataclass(kw_only=True)
class DataPart(EmptyPart):
    """Part containing arbitrary data.

    Attributes:
        data: The data of the part.
    """

    data: dict[str, Any]


@dataclass(kw_only=True)
class MediaPart(EmptyPart):
    """Part containing media references.

    Attributes:
        media: The media references of the part.
    """

    media: dict[str, str | None]


@dataclass(kw_only=True)
class ToolRequestPart(EmptyPart, Generic[T]):
    """Part containing a tool request.

    Attributes:
        tool_request: The tool request of the part.
    """

    tool_request: dict[str, T | None]


@dataclass(kw_only=True)
class ToolResponsePart(EmptyPart, Generic[T]):
    """Part containing a tool response.

    Attributes:
        tool_response: The tool response of the part.
    """

    tool_response: dict[str, T | None]


@dataclass(kw_only=True)
class PendingPart(EmptyPart):
    """Part representing pending content.

    Attributes:
        metadata: The metadata of the part.
    """

    metadata: dict[str, Any] = field(default_factory=lambda: {'pending': True})


type Part = (
    TextPart
    | DataPart
    | MediaPart
    | ToolRequestPart[Any]
    | ToolResponsePart[Any]
    | PendingPart
)


@dataclass(kw_only=True)
class Message(HasMetadata):
    """Message with role and content parts.

    Attributes:
        role: The role of the message.
        content: The content of the message.
    """

    role: Literal['user', 'model', 'tool', 'system']
    content: list[Part]


@dataclass(kw_only=True)
class Document(HasMetadata):
    """Document containing content parts.

    Attributes:
        content: The content of the document.
    """

    content: list[Part]


@dataclass
class DataArgument(Generic[T]):
    """Provides information needed to render a template at runtime.

    Attributes:
        data: The data to use for rendering.
        history: Optional message history.
        tools: Optional tool definitions.
        schemas: Optional JSON schemas.
    """

    data: dict[str, T]
    history: list[Message] | None = None
    tools: dict[str, ToolDefinition] | None = None
    schemas: dict[str, Any] | None = None


type JSONSchema = Any


class SchemaLookup(Protocol):
    """Protocol for looking up JSON schemas."""

    def __call__(self, schema_name: str) -> JSONSchema | None:
        """Look up a JSON schema by name.

        Args:
            schema_name: Name of the schema to look up.

        Returns:
            The JSON schema or None if not found.
        """
        ...


class ToolLookup(Protocol):
    """Protocol for looking up tool definitions."""

    def __call__(self, tool_name: str) -> ToolDefinition | None:
        """Look up a tool definition by name.

        Args:
            tool_name: Name of the tool to look up.

        Returns:
            The tool definition or None if not found.
        """
        ...


class PromptRenderer(Protocol[T]):
    """Protocol for rendering prompts."""

    prompt: ParsedPrompt[T]

    def __call__(
        self,
        data: DataArgument[Any],
        schema_lookup: SchemaLookup | None = None,
        tool_lookup: ToolLookup | None = None,
    ) -> Document:
        """Render a prompt with the given data and lookups.

        Args:
            data: Data to use for rendering.
            schema_lookup: Optional schema lookup function.
            tool_lookup: Optional tool lookup function.

        Returns:
            The rendered document.
        """
        ...


class PartialRenderer(Protocol[T]):
    """Protocol for rendering partial templates."""

    def __call__(
        self,
        data: DataArgument[Any],
        schema_lookup: SchemaLookup | None = None,
        tool_lookup: ToolLookup | None = None,
    ) -> Document:
        """Render a partial template with the given data and lookups.

        Args:
            data: Data to use for rendering.
            schema_lookup: Optional schema lookup function.
            tool_lookup: Optional tool lookup function.

        Returns:
            The rendered document.
        """
        ...


@dataclass(kw_only=True)
class RenderedPrompt(PromptMetadata[T]):
    """The final result of rendering a Dotprompt template.

    It includes all of the prompt metadata as well as a set of `messages` to be
    sent to the  model.

    Attributes:
        messages: The rendered messages of the prompt.
    """

    messages: list[Message]


class PromptFunction(Protocol, Generic[T]):
    """Takes runtime data/context and returns a rendered prompt result.

    Args:
        data: Data to use for rendering.
        options: Optional prompt metadata.

    Returns:
        The rendered prompt.
    """

    prompt: ParsedPrompt[T]

    def __call__(
        self,
        data: DataArgument[Any],
        options: PromptMetadata[T] | None = None,
    ) -> RenderedPrompt[T]:
        """Render a prompt with the given data and options.

        Args:
            data: Data to use for rendering.
            options: Optional prompt metadata.

        Returns:
            The rendered prompt.
        """
        ...


class PromptRefFunction(Protocol, Generic[T]):
    """Takes runtime data / context and returns a rendered prompt result.

    The difference in comparison to PromptFunction is that a promp is loaded via
    reference.

    Args:
        data: Data to use for rendering.
        options: Optional prompt metadata.

    Returns:
        The rendered prompt.
    """

    def __call__(
        self,
        data: DataArgument[Any],
        options: PromptMetadata[T] | None = None,
    ) -> RenderedPrompt[T]:
        """Render a prompt with the given data and options.

        Args:
            data: Data to use for rendering.
            options: Optional prompt metadata.

        Returns:
            The rendered prompt.
        """
        ...

    prompt_ref: PromptRef


@dataclass
class PaginatedResponse:
    """Response containing pagination cursor.

    Attributes:
        cursor: The pagination cursor.
    """

    cursor: str | None = None


@dataclass(kw_only=True)
class PartialRef:
    """Reference to a partial template.

    Attributes:
        name: The name of the partial template.
        variant: The variant name for the partial template.
        version: The version of the partial template.
    """

    name: str
    variant: str | None = None
    version: str | None = None


@dataclass(kw_only=True)
class PartialData(PartialRef):
    """Partial template data containing source.

    Attributes:
        source: The source of the partial template.
    """

    source: str


class PromptStore(Protocol):
    """PromptStore is a common interface that provides for.

    Args:
        options: Optional options for the operation.

    Returns:
        The result of the operation.
    """

    def list(self, options: dict[str, Any] | None = None) -> dict[str, Any]:
        """Return a list of all prompts in the store (optionally paginated).

        Be aware that some store providers may return limited metadata.
        """

    def list_partials(
        self, options: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Return a list of partial names available in this store."""

    def load(
        self, name: str, options: dict[str, Any] | None = None
    ) -> PromptData:
        """Retrieve a prompt from the store."""

    def load_partial(
        self, name: str, options: dict[str, Any] | None = None
    ) -> PromptData:
        """Retrieve a partial from the store."""


class PromptStoreWritable(PromptStore, Protocol):
    """PromptStore that also has built-in methods for writing prompts.

    Args:
        prompt: The prompt to save.
        name: The name of the prompt to delete.
        options: Optional options for the operation.

    Returns:
        None
    """

    def save(self, prompt: PromptData) -> None:
        """Save a prompt in the store.

        May be destructive for prompt stores without versioning.
        """

    def delete(self, name: str, options: dict[str, Any] | None = None) -> None:
        """Delete a prompt from the store."""


@dataclass
class PromptBundle:
    """Bundle containing prompts and partial templates.

    Attributes:
        partials: The partial templates in the bundle.
        prompts: The prompts in the bundle.
    """

    partials: list[PartialData]
    prompts: list[PromptData]
