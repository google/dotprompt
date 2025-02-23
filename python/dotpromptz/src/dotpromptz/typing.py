# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Data models and interfaces type definitions."""

from dataclasses import dataclass, field
from typing import Any, Generic, Literal, Protocol, TypeVar

T = TypeVar('T')


type Schema = dict[str, Any]


@dataclass
class ToolDefinition:
    name: str
    description: str | None
    input_schema: Schema = field(default_factory=dict)
    output_schema: Schema | None = None


type ToolArgument = str | ToolDefinition


@dataclass
class HasMetadata:
    """
    Whether contains metadata.

    Attributes:
        metadata: Arbitrary metadata to be used by tooling or for informational
            purposes.
    """

    metadata: dict[str, Any] | None = None


@dataclass(kw_only=True)
class PromptRef:
    name: str
    variant: str | None = None
    version: str | None = None


@dataclass(kw_only=True)
class PromptData(PromptRef):
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
    template: str


@dataclass
class EmptyPart(HasMetadata):
    pass


@dataclass(kw_only=True)
class TextPart(EmptyPart):
    text: str


@dataclass(kw_only=True)
class DataPart(EmptyPart):
    data: dict[str, Any]


@dataclass(kw_only=True)
class MediaPart(EmptyPart):
    media: dict[str, str | None]


@dataclass(kw_only=True)
class ToolRequestPart(EmptyPart, Generic[T]):
    tool_request: dict[str, T | None]


@dataclass(kw_only=True)
class ToolResponsePart(EmptyPart, Generic[T]):
    tool_response: dict[str, T | None]


@dataclass(kw_only=True)
class PendingPart(EmptyPart):
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
    role: Literal['user', 'model', 'tool', 'system']
    content: list[Part]


@dataclass(kw_only=True)
class Document(HasMetadata):
    content: list[Part]


@dataclass
class DataArgument(Generic[T]):
    """
    Rrovides all of the information necessary to render a template at runtime.

    Attributes:
        input: Input variables for the prompt template.
        docs: Relevant documents.
        messages: Previous messages in the history of a multi-turn conversation.
        context: Items in the context argument are exposed as `@` variables,
            e.g. `context: {state: {...}}` is exposed as `@state`.
    """

    input: T | None = None
    docs: list[Document] | None = None
    messages: list[Message] | None = None
    context: dict[str, Any] | None = None


type JSONSchema = Any


class SchemaResolver(Protocol):
    """Resolves a provided schema name to an underlying JSON schema.

    Utilized for shorthand to a schema library provided by an external tool.
    """

    def __call__(self, schema_name: str) -> JSONSchema | None: ...


class ToolResolver(Protocol):
    """Resolves a provided tool name to an underlying ToolDefinition.

    Utilized for shorthand to a tool registry provided by an external library.
    """

    def __call__(self, tool_name: str) -> ToolDefinition | None: ...


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
    """Takes runtime data/context and returns a rendered prompt result."""

    prompt: ParsedPrompt[T]

    def __call__(
        self,
        data: DataArgument[Any],
        options: PromptMetadata[T] | None = None,
    ) -> RenderedPrompt[T]: ...


class PromptRefFunction(Protocol, Generic[T]):
    """Takes runtime data / context and returns a rendered prompt result.

    The difference in comparison to PromptFunction is that a promp is loaded via
    reference.
    """

    def __call__(
        self,
        data: DataArgument[Any],
        options: PromptMetadata[T] | None = None,
    ) -> RenderedPrompt[T]: ...

    prompt_ref: PromptRef


@dataclass
class PaginatedResponse:
    cursor: str | None = None


@dataclass(kw_only=True)
class PartialRef:
    name: str
    variant: str | None = None
    version: str | None = None


@dataclass(kw_only=True)
class PartialData(PartialRef):
    source: str


class PromptStore(Protocol):
    """PromptStore is a common interface that provides for."""

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
    """PromptStore that also has built-in methods for writing prompts."""

    def save(self, prompt: PromptData) -> None:
        """Save a prompt in the store.

        May be destructive for prompt stores without versioning.
        """

    def delete(self, name: str, options: dict[str, Any] | None = None) -> None:
        """Delete a prompt from the store."""


@dataclass
class PromptBundle:
    partials: list[PartialData]
    prompts: list[PromptData]
