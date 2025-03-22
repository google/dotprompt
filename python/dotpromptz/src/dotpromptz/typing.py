# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Data models and interfaces type definitions using Pydantic v2."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Callable, Generic, Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar('T')

# Type alias
Schema = dict[str, Any]


class Role(StrEnum):
    """The role of a message in a conversation."""

    ASSISTANT = 'assistant'
    MODEL = 'model'
    SYSTEM = 'system'
    TOOL = 'tool'
    USER = 'user'


class ToolDefinition(BaseModel):
    """A tool definition."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra='forbid',
    )

    name: str
    description: str | None = None
    input_schema: dict[str, Any] = Field(
        default_factory=dict, alias='inputSchema'
    )
    output_schema: dict[str, Any] | None = Field(None, alias='outputSchema')


# Type alias
ToolArgument = str | ToolDefinition


class HasMetadata(BaseModel):
    """
    Whether contains metadata.

    Attributes:
        metadata: Arbitrary metadata to be used by tooling or for informational purposes.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        extra='forbid',
    )

    metadata: dict[str, Any] | None = None


class PromptRef(BaseModel):
    """A reference to a prompt in a store."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra='forbid',
    )

    name: str
    variant: str | None = None
    version: str | None = None


class PromptData(PromptRef):
    """A prompt in a store."""

    source: str


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

    model_config = ConfigDict(
        populate_by_name=True,
        extra='forbid',
    )

    name: str | None = None
    variant: str | None = None
    version: str | None = None
    description: str | None = None
    model: str | None = None
    tools: list[str] | None = None
    tool_defs: list[ToolDefinition] | None = Field(None, alias='toolDefs')
    config: T | None = None
    input: dict[str, Any] | None = None
    output: dict[str, Any] | None = None
    raw: dict[str, Any] | None = None
    ext: dict[str, dict[str, Any]] | None = None


class ParsedPrompt(PromptMetadata[T], Generic[T]):
    """A parsed prompt."""

    template: str


class EmptyPart(HasMetadata):
    """An empty part in a conversation."""

    pass


class TextPart(EmptyPart):
    """A text part in a conversation."""

    text: str


class DataPart(EmptyPart):
    """A data part in a conversation."""

    data: dict[str, Any]


class MediaPart(EmptyPart):
    """A media part in a conversation."""

    media: dict[str, str | None]


class ToolRequestPart(EmptyPart, Generic[T]):
    """A tool request part in a conversation."""

    tool_request: dict[str, T | None] = Field(alias='toolRequest')


class ToolResponsePart(EmptyPart, Generic[T]):
    """A tool response part in a conversation."""

    tool_response: dict[str, T | None] = Field(alias='toolResponse')


class PendingPart(EmptyPart):
    """A pending part in a conversation."""

    metadata: dict[str, Any] = Field(default_factory=lambda: {'pending': True})


# Union type for Part
Part = (
    TextPart
    | DataPart
    | MediaPart
    | ToolRequestPart[Any]
    | ToolResponsePart[Any]
    | PendingPart
)


class Message(HasMetadata):
    """A message in a conversation."""

    role: Role
    content: list[Part]


class Document(HasMetadata):
    """A document in a conversation."""

    content: list[Part]


class DataArgument(BaseModel, Generic[T]):
    """
    Provides all of the information necessary to render a template at runtime.

    Attributes:
        input: Input variables for the prompt template.
        docs: Relevant documents.
        messages: Previous messages in the history of a multi-turn conversation.
        context: Items in the context argument are exposed as `@` variables,
            e.g. `context: {state: {...}}` is exposed as `@state`.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        extra='forbid',
    )

    input: T | None = None
    docs: list[Document] | None = None
    messages: list[Message] | None = None
    context: dict[str, Any] | None = None


# Type alias
JsonSchema = dict[str, Any]


SchemaResolver = Callable[[str], JsonSchema | None]


@runtime_checkable
class ToolResolver(Protocol):
    """Resolves a provided tool name to an underlying ToolDefinition.

    Utilized for shorthand to a tool registry provided by an external library.
    """

    def __call__(self, tool_name: str) -> ToolDefinition | None: ...


class RenderedPrompt(PromptMetadata[T], Generic[T]):
    """The final result of rendering a Dotprompt template.

    It includes all of the prompt metadata as well as a set of `messages` to be
    sent to the model.

    Attributes:
        messages: The rendered messages of the prompt.
    """

    messages: list[Message]


@runtime_checkable
class PromptFunction(Protocol, Generic[T]):
    """Takes runtime data/context and returns a rendered prompt result."""

    prompt: ParsedPrompt[T]

    def __call__(
        self,
        data: DataArgument[Any],
        options: PromptMetadata[T] | None = None,
    ) -> RenderedPrompt[T]: ...


@runtime_checkable
class PromptRefFunction(Protocol, Generic[T]):
    """Takes runtime data / context and returns a rendered prompt result.

    The difference in comparison to PromptFunction is that a prompt is loaded
    via reference.
    """

    def __call__(
        self,
        data: DataArgument[Any],
        options: PromptMetadata[T] | None = None,
    ) -> RenderedPrompt[T]:
        """Takes runtime data / context and returns a rendered prompt result."""
        ...

    prompt_ref: PromptRef


class PaginatedResponse(BaseModel):
    """A paginated response."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra='forbid',
    )

    cursor: str | None = None


class PartialRef(BaseModel):
    """A partial reference."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra='forbid',
    )

    name: str
    variant: str | None = None
    version: str | None = None


class PartialData(PartialRef):
    """A partial in a store."""

    source: str


class PromptBundle(BaseModel):
    """A bundle of prompts and partials."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra='forbid',
    )

    partials: list[PartialData]
    prompts: list[PromptData]


@runtime_checkable
class PromptStore(Protocol):
    """PromptStore is a common interface that provides for."""

    def list(self, options: dict[str, Any] | None = None) -> dict[str, Any]:
        """Return a list of all prompts in the store (optionally paginated).

        Be aware that some store providers may return limited metadata.
        """
        ...

    def list_partials(
        self, options: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Return a list of partial names available in this store."""
        ...

    def load(
        self, name: str, options: dict[str, Any] | None = None
    ) -> PromptData:
        """Retrieve a prompt from the store."""
        ...

    def load_partial(
        self, name: str, options: dict[str, Any] | None = None
    ) -> PromptData:
        """Retrieve a partial from the store."""
        ...


@runtime_checkable
class PromptStoreWritable(PromptStore, Protocol):
    """PromptStore that also has built-in methods for writing prompts."""

    def save(self, prompt: PromptData) -> None:
        """Save a prompt in the store.

        May be destructive for prompt stores without versioning.
        """
        ...

    def delete(self, name: str, options: dict[str, Any] | None = None) -> None:
        """Delete a prompt from the store."""
        ...
