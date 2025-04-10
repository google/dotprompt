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

"""Pydantic V2 models mirroring the TypeScript types for Dotprompt.

This module provides Python equivalents of the core TypeScript types used in the
Dotprompt TS reference implementation.

A key difference from the TS implementation is that the PromptStore has 2
protocols: one for async and one for sync.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from enum import Enum
from typing import (
    Any,
    Generic,
    Literal,
    Protocol,
    TypeVar,
)

from pydantic import BaseModel, ConfigDict, Field

Schema = dict[str, Any]
"""Type alias for a generic schema, represented as a dictionary."""

JsonSchema = Any
"""Type alias for a JSON schema definition. 'Any' allows flexibility."""

ModelConfigT = TypeVar('ModelConfigT')
"""Generic TypeVar for model configuration within prompts."""

InputT = TypeVar('InputT')
"""Generic TypeVar for input types, typically used in ToolRequestPart."""

OutputT = TypeVar('OutputT')
"""Generic TypeVar for output types, typically used in ToolResponsePart."""

VariablesT = TypeVar('VariablesT')
"""Generic TypeVar for prompt input variables within DataArgument."""


class HasMetadata(BaseModel):
    """Base model for types that can include arbitrary metadata.

    Attributes:
        metadata: Arbitrary dictionary for tooling or informational
                  purposes.
    """

    metadata: dict[str, Any] | None = None
    model_config = ConfigDict(extra='allow')


class ToolDefinition(BaseModel):
    """Defines the structure and schemas for a tool callable by a model.

    Attributes:
        name: The unique identifier for the tool.
        description: A human-readable explanation of the tool's purpose
                     and function.
        input_schema: A schema definition for the expected input
                      parameters of the tool.
        output_schema: An optional schema definition for the structure of
                       the tool's output.
    """

    name: str
    description: str | None = None
    input_schema: Schema = Field(..., alias='inputSchema')
    output_schema: Schema | None = Field(default=None, alias='outputSchema')
    model_config = ConfigDict(populate_by_name=True)


ToolArgument = str | ToolDefinition
"""Type alias representing either a tool name or a full ToolDefinition."""


class PromptRef(BaseModel):
    """A reference to identify a specific prompt.

    Attributes:
        name: The base name identifying the prompt.
        variant: An optional identifier for a specific variation of the
                 prompt.
        version: An optional specific version hash or identifier of the
                 prompt content.
    """

    name: str
    variant: str | None = None
    version: str | None = None


class PromptData(PromptRef):
    """Represents the complete data of a prompt.

    Attributes:
        source: The raw source content (template string) of the prompt.
    """

    source: str


class PromptInputConfig(BaseModel):
    """Configuration settings related to the input variables of a prompt.

    Attributes:
        default: A dictionary providing default values for input variables
                 if not supplied at runtime.
        schema_: A schema definition constraining the expected input
                 variables. Aliased as 'schema'. Using `schema_` avoids
                 collision with Pydantic methods.
    """

    default: dict[str, Any] | None = None
    schema_: Schema | None = Field(default=None, alias='schema')
    model_config = ConfigDict(populate_by_name=True)


class PromptOutputConfig(BaseModel):
    """Configuration settings related to the expected output of a prompt.

    Attributes:
        format: Specifies the desired output format.
        schema_: A schema definition constraining the structure of the
                 expected output. Aliased as 'schema'.
    """

    format: Literal['json', 'text'] | str | None = None
    schema_: Schema | None = Field(default=None, alias='schema')
    model_config = ConfigDict(populate_by_name=True)


class PromptMetadata(Generic[ModelConfigT], HasMetadata):
    """Metadata associated with a prompt, including configuration.

    This is a generic model, allowing the `config` field to hold
    different types of model-specific configurations specified by
    `ModelConfigT`.

    Attributes:
        name: Optional name override within the metadata itself.
        variant: Optional variant override within the metadata.
        version: Optional version override within the metadata.
        description: A human-readable description of the prompt's purpose.
        model: The identifier of the language model to be used.
        tools: A list of names referring to tools available to the model.
        tool_defs: A list of inline `ToolDefinition` objects available to
                   the model.
        config: Model-specific configuration parameters.
        input: Configuration specific to the prompt's input variables.
        output: Configuration specific to the prompt's expected output.
        raw: A dictionary holding the raw, unprocessed frontmatter parsed
             from the source.
        ext: A nested dictionary holding extension fields from the
             frontmatter, organized by namespace.
    """

    name: str | None = None
    variant: str | None = None
    version: str | None = None
    description: str | None = None
    model: str | None = None
    tools: list[str] | None = None
    tool_defs: list[ToolDefinition] | None = Field(default=None, alias='toolDefs')
    config: ModelConfigT | None = None
    input: PromptInputConfig | None = None
    output: PromptOutputConfig | None = None
    raw: dict[str, Any] | None = None
    ext: dict[str, dict[str, Any]] | None = None
    model_config = ConfigDict(populate_by_name=True)


class ParsedPrompt(Generic[ModelConfigT], PromptMetadata[ModelConfigT]):
    """Represents a prompt after parsing its metadata and template.

    Attributes:
        template: The core template string, with frontmatter removed.
    """
    template: str
    prompt_metadata: PromptMetadata


class TextPart(HasMetadata):
    """A content part containing a plain text string.

    Attributes:
        text: The textual content of this part.
    """

    text: str


class DataPart(HasMetadata):
    """A content part containing arbitrary structured data.

    Attributes:
        data: A dictionary representing the structured data content.
    """

    data: dict[str, Any]


class MediaContent(BaseModel):
    """Describes the content details within a `MediaPart`.

    Attributes:
        url: The URL where the media resource can be accessed.
        content_type: The MIME type of the media.
    """

    url: str
    content_type: str | None = Field(default=None, alias='contentType')
    model_config = ConfigDict(populate_by_name=True)


class MediaPart(HasMetadata):
    """A content part representing media, like an image, audio, or video.

    Attributes:
        media: A `MediaContent` object with URL and type of the media.
    """

    media: MediaContent


class ToolRequestContent(Generic[InputT], BaseModel):
    """Describes the details of a tool request within a `ToolRequestPart`.

    Attributes:
        name: The name of the tool being requested.
        input: The input parameters for the tool request.
        ref: An optional reference identifier for tracking this request.
    """

    name: str
    input: InputT | None = None
    ref: str | None = None
    model_config = ConfigDict(arbitrary_types_allowed=True)


class ToolRequestPart(Generic[InputT], HasMetadata):
    """A content part representing a request to invoke a tool.

    Attributes:
        tool_request: A `ToolRequestContent` object with request details.
    """

    tool_request: ToolRequestContent[InputT] = Field(..., alias='toolRequest')
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


class ToolResponseContent(Generic[OutputT], BaseModel):
    """Describes the details of a tool response within a `ToolResponsePart`.

    Attributes:
        name: The name of the tool that produced this response.
        output: The output data returned by the tool.
        ref: An optional reference identifier matching the request.
    """

    name: str
    output: OutputT | None = None
    ref: str | None = None
    model_config = ConfigDict(arbitrary_types_allowed=True)


class ToolResponsePart(Generic[OutputT], HasMetadata):
    """A content part representing the result from a tool execution.

    Attributes:
        tool_response: A `ToolResponseContent` object with response details.
    """

    tool_response: ToolResponseContent[OutputT] = Field(..., alias='toolResponse')
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


class PendingMetadata(BaseModel):
    """Defines the required metadata structure for a `PendingPart`.

    Attributes:
        pending: A literal boolean True, indicating the pending state.
    """

    pending: Literal[True]
    model_config = ConfigDict(extra='allow')

    @classmethod
    def with_purpose(cls, purpose: str) -> PendingMetadata:
        """Create a PendingMetadata with a purpose field.

        Args:
            purpose: The purpose of the pending part

        Returns:
            A new PendingMetadata instance with the purpose set
        """
        instance = cls(pending=True)
        # Set purpose as an extra field
        object.__setattr__(instance, 'purpose', purpose)
        return instance


class PendingPart(HasMetadata):
    """A content part indicating content is pending or awaited.

    Attributes:
        metadata: Metadata object confirming the pending state.
    """

    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(
        extra='allow',
        populate_by_name=True,
    )

    def __init__(self, **data: Any) -> None:
        """Initialize a PendingPart.

        Args:
            **data: Data for the model, including a PendingMetadata object
                   under the 'metadata' key
        """
        if 'metadata' in data and isinstance(data['metadata'], PendingMetadata):
            # Convert PendingMetadata to dict for HasMetadata compatibility
            metadata_dict = data['metadata'].model_dump()
            data['metadata'] = metadata_dict
        super().__init__(**data)


Part = TextPart | DataPart | MediaPart | ToolRequestPart[Any] | ToolResponsePart[Any] | PendingPart
"""Type alias for any valid content part in a `Message` or `Document`."""


# Define Role as a proper enum to work with Pydantic models
class Role(str, Enum):
    """Defines the role of a participant in a conversation."""

    USER = 'user'
    MODEL = 'model'
    TOOL = 'tool'
    SYSTEM = 'system'


# Role constants with ROLE_ prefix for explicit imports
ROLE_USER = Role.USER
ROLE_MODEL = Role.MODEL
ROLE_TOOL = Role.TOOL
ROLE_SYSTEM = Role.SYSTEM


class Message(HasMetadata):
    """Represents a single turn or message in a conversation history.

    Attributes:
        role: The role of the originator of this message.
        content: A list of `Part` objects making up the message content.
    """

    role: Role
    content: list[Part]
    model_config = ConfigDict(arbitrary_types_allowed=True)


class Document(HasMetadata):
    """Represents an external document, often used for context.

    Attributes:
        content: A list of `Part` objects making up the document content.
    """

    content: list[Part]
    model_config = ConfigDict(arbitrary_types_allowed=True)


class DataArgument(Generic[VariablesT], BaseModel):
    """Encapsulates runtime information needed to render a prompt template.

    Attributes:
        input: Values for input variables required by the template.
        docs: List of relevant `Document` objects.
        messages: List of preceding `Message` objects in the history.
        context: Arbitrary dictionary of additional context items.
    """

    input: VariablesT | None = None
    docs: list[Document] | None = None
    messages: list[Message] | None = None
    context: dict[str, Any] | None = None


SchemaResolver = Callable[[str], JsonSchema | None | Awaitable[JsonSchema | None]]
"""Type alias for a function resolving a schema name to a JSON schema."""

ToolResolver = Callable[[str], ToolDefinition | None | Awaitable[ToolDefinition | None]]
"""Type alias for a function resolving a tool name to a ToolDefinition."""

PartialResolver = Callable[[str], str | None | Awaitable[str | None]]
"""Type alias for a function resolving a partial name to a template string."""


class RenderedPrompt(Generic[ModelConfigT], PromptMetadata[ModelConfigT]):
    """The final output after a prompt template is rendered.

    Attributes:
        messages: The list of `Message` objects resulting from rendering.
    """

    messages: list[Message]


class PromptFunction(Protocol[ModelConfigT]):
    """Protocol defining the interface for a callable async prompt function.

    Implementations are async callables taking runtime data and optional
    metadata overrides, returning a `RenderedPrompt`. They must also
    expose the parsed prompt structure via the `prompt` attribute.
    """

    prompt: ParsedPrompt[ModelConfigT]
    """The parsed prompt structure associated with this function."""

    async def __call__(
        self,
        data: DataArgument[Any],
        options: PromptMetadata[ModelConfigT] | None = None,
    ) -> RenderedPrompt[ModelConfigT]:
        """Asynchronously renders the prompt.

        Args:
            data: The runtime `DataArgument`.
            options: Optional `PromptMetadata` to merge/override.

        Returns:
            A `RenderedPrompt` object.
        """
        ...


class PromptRefFunction(Protocol[ModelConfigT]):
    """Protocol for a callable async prompt function loaded by reference.

    Implementations load the prompt based on `prompt_ref` before
    rendering.
    """

    model_config: ConfigDict = ConfigDict(populate_by_name=True)
    prompt_ref: PromptRef = Field(..., alias='promptRef')

    async def __call__(
        self,
        data: DataArgument[Any],
        options: PromptMetadata[ModelConfigT] | None = None,
    ) -> RenderedPrompt[ModelConfigT]:
        """Asynchronously loads and renders the referenced prompt.

        Args:
            data: The runtime `DataArgument`.
            options: Optional `PromptMetadata` to merge/override.

        Returns:
            A `RenderedPrompt` containing the rendered prompt.
        """
        ...


class PaginatedResponse(BaseModel):
    """Base model for responses supporting pagination via a cursor.

    Attributes:
        cursor: Optional token for requesting the next page of results.
    """

    cursor: str | None = None


class PartialRef(BaseModel):
    """A reference to identify a specific partial template.

    Attributes:
        name: The base name identifying the partial.
        variant: Optional identifier for a specific variation.
        version: Optional specific version hash or identifier.
    """

    name: str
    variant: str | None = None
    version: str | None = None


class PartialData(PartialRef):
    """Represents the complete data of a partial template.

    Attributes:
        source: The raw source content (template string) of the partial.
    """

    source: str


class ListPromptsOptions(BaseModel):
    """Options to control the listing of prompts (pagination).

    Attributes:
        cursor: The pagination cursor from a previous response.
        limit: The maximum number of references to return per page.
    """

    cursor: str | None = None
    limit: int | None = None


class ListPartialsOptions(BaseModel):
    """Options to control the listing of partials (pagination).

    Attributes:
        cursor: The pagination cursor from a previous response.
        limit: The maximum number of references to return per page.
    """

    cursor: str | None = None
    limit: int | None = None


class LoadPromptOptions(BaseModel):
    """Options for specifying which prompt version/variant to load.

    Attributes:
        variant: The specific variant identifier to retrieve.
        version: A specific version hash to load for validation.
    """

    variant: str | None = None
    version: str | None = None


class LoadPartialOptions(BaseModel):
    """Options for specifying which partial version/variant to load.

    Attributes:
        variant: The specific variant identifier to retrieve.
        version: A specific version hash to load for validation.
    """

    variant: str | None = None
    version: str | None = None


LoadOptions = LoadPromptOptions | LoadPartialOptions
"""Type alias for options when loading a prompt or a partial."""


class DeletePromptOrPartialOptions(BaseModel):
    """Options for specifying which variant to delete.

    Attributes:
        variant: The specific variant identifier to delete. Targets
                 default if omitted.
    """

    variant: str | None = None


class PaginatedPrompts(PaginatedResponse):
    """Represents a single page of results when listing prompts.

    Attributes:
        prompts: A list of `PromptRef` objects in this page.
    """

    prompts: list[PromptRef]


class PaginatedPartials(PaginatedResponse):
    """Represents a single page of results when listing partials.

    Attributes:
        partials: A list of `PartialRef` objects in this page.
    """

    partials: list[PartialRef]


class PromptStore(Protocol):
    """Protocol defining the standard async interface for reading prompts.

    Abstract base for different asynchronous storage implementations.
    """

    async def list(self, options: ListPromptsOptions | None = None) -> PaginatedPrompts:
        """Asynchronously retrieves a paginated list of prompts.

        Args:
            options: Optional parameters for pagination.

        Returns:
            A `PaginatedPrompts` object.
        """
        ...

    async def list_partials(self, options: ListPartialsOptions | None = None) -> PaginatedPartials:
        """Asynchronously retrieves a paginated list of partials.

        Args:
            options: Optional parameters for pagination.

        Returns:
            A `PaginatedPartials` object.
        """
        ...

    async def load(self, name: str, options: LoadPromptOptions | None = None) -> PromptData:
        """Asynchronously loads the data for a specific prompt.

        Args:
            name: The name of the prompt to load.
            options: Optional parameters for variant or version.

        Returns:
            A `PromptData` object.

        Raises:
            Exception: If the prompt is not found or cannot be loaded.
        """
        ...

    async def load_partial(self, name: str, options: LoadPartialOptions | None = None) -> PartialData:
        """Asynchronously loads the data for a specific partial.

        Args:
            name: The name of the partial to load.
            options: Optional parameters for variant or version.

        Returns:
            A `PartialData` object.

        Raises:
            Exception: If the partial is not found or cannot be loaded.
        """
        ...


class PromptStoreWritable(PromptStore, Protocol):
    """Protocol extending `PromptStore` with async write methods.

    Implementations supporting asynchronous writes should conform.
    """

    async def save(self, prompt: PromptData) -> None:
        """Asynchronously saves a prompt to the store.

        Args:
            prompt: The `PromptData` object to save.

        Returns:
            None. Should raise errors on failure.
        """
        ...

    async def delete(self, name: str, options: DeletePromptOrPartialOptions | None = None) -> None:
        """Asynchronously deletes a prompt from the store.

        Args:
            name: The name of the prompt to delete.
            options: Optional parameters to specify a `variant`.

        Returns:
            None. Should raise errors on failure.
        """
        ...


class PromptStoreSync(Protocol):
    """Protocol defining the standard sync interface for reading prompts.

    Abstract base for different synchronous storage implementations.
    """

    def list(self, options: ListPromptsOptions | None = None) -> PaginatedPrompts:
        """Synchronously retrieves a paginated list of prompts.

        Args:
            options: Optional parameters for pagination.

        Returns:
            A `PaginatedPrompts` object.
        """
        ...

    def list_partials(self, options: ListPartialsOptions | None = None) -> PaginatedPartials:
        """Synchronously retrieves a paginated list of partials.

        Args:
            options: Optional parameters for pagination.

        Returns:
            A `PaginatedPartials` object.
        """
        ...

    def load(self, name: str, options: LoadPromptOptions | None = None) -> PromptData:
        """Synchronously loads the data for a specific prompt.

        Args:
            name: The name of the prompt to load.
            options: Optional parameters for variant or version.

        Returns:
            A `PromptData` object.

        Raises:
            Exception: If the prompt is not found or cannot be loaded.
        """
        ...

    def load_partial(self, name: str, options: LoadPartialOptions | None = None) -> PartialData:
        """Synchronously loads the data for a specific partial.

        Args:
            name: The name of the partial to load.
            options: Optional parameters for variant or version.

        Returns:
            A `PartialData` object.

        Raises:
            Exception: If the partial is not found or cannot be loaded.
        """
        ...


class PromptStoreWritableSync(PromptStoreSync, Protocol):
    """Protocol extending `PromptStoreSync` with sync write methods.

    Implementations supporting synchronous writes should conform.
    """

    def save(self, prompt: PromptData) -> None:
        """Synchronously saves a prompt to the store.

        Args:
            prompt: The `PromptData` object to save.

        Returns:
            None. Should raise errors on failure.
        """
        ...

    def delete(self, name: str, options: DeletePromptOrPartialOptions | None = None) -> None:
        """Synchronously deletes a prompt from the store.

        Args:
            name: The name of the prompt to delete.
            options: Optional parameters to specify a `variant`.

        Returns:
            None. Should raise errors on failure.
        """
        ...


class PromptBundle(BaseModel):
    """A container for packaging multiple prompts and partials.

    Attributes:
        partials: A list of `PartialData` objects.
        prompts: A list of `PromptData` objects.
    """

    partials: list[PartialData]
    prompts: list[PromptData]
