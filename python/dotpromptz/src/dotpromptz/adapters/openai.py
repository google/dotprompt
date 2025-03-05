# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Data models and interfaces type definitions using Pydantic v2."""

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel

from dotpromptz.typing import Role


class DetailKind(StrEnum):
    """The kind of Image URL detail."""

    AUTO = 'auto'
    LOW = 'low'
    HIGH = 'high'


# Define TypedDicts to represent the interfaces
class ImageURLDetail(BaseModel):
    """Image URL Detail"""

    url: str
    detail: DetailKind | None = None


class ContentItemType(StrEnum):
    """Enumveration variants for content item type."""

    TEXT = 'text'
    IMAGE_URL = 'image_url'


class ContentItem(BaseModel):
    """Content Item: can be text or image"""

    type: ContentItemType
    text: str | None = None
    image_url: ImageURLDetail | None = None


class ToolFunction(BaseModel):
    name: str
    arguments: str


class ToolCallType(StrEnum):
    """Enumeration variants for tool call type."""

    FUNCTION = 'function'


class ToolCall(BaseModel):
    id: str
    type: ToolCallType
    function: ToolFunction


class OpenAIMessage(BaseModel):
    """Open AI Message"""

    role: Role
    content: str | list[ContentItem] | None = None
    name: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None


class OpenAIToolFunction(BaseModel):
    name: str
    description: str | None = None
    parameters: dict[str, Any] | None = None


class OpenAIToolDefinition(BaseModel):
    type: ToolCallType
    function: OpenAIToolFunction


class ToolChoiceFunction(BaseModel):
    name: str


class ToolChoice(BaseModel):
    """Tool Choice"""

    type: ToolCallType
    function: ToolChoiceFunction


class ResponseFormatType(StrEnum):
    """Enum variants for response format type."""

    TEXT = 'text'
    JSON_OBJECT = 'json_object'


class ResponseFormat(BaseModel):
    """Expected Response Format"""

    type: ResponseFormatType


type ToolChoiceOptions = Literal['none', 'auto']


class OpenAIRequest(BaseModel):
    """Open AI Request"""

    messages: list[OpenAIMessage]
    model: str
    frequency_penalty: float | None = None
    logit_bias: dict[str, int] | None = None
    max_tokens: int | None = None
    n: int | None = None
    presence_penalty: float | None = None
    response_format: ResponseFormat | None = None
    seed: int | None = None
    stop: str | list[str] | None = None
    stream: bool | None = None
    temperature: float | None = None
    tool_choice: ToolChoiceOptions | ToolChoice | None = None
    tools: list[OpenAIToolDefinition] | None = None
    top_p: float | None = None
    user: str | None = None


# Functions
