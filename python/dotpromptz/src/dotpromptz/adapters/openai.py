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

import sys  # noqa

from typing import Any, Literal

from pydantic import BaseModel

from dotpromptz.typing import Role

if sys.version_info < (3, 11):  # noqa
    from strenum import StrEnum  # noqa
else:  # noqa
    from enum import StrEnum  # noqa


class DetailKind(StrEnum):
    """The kind of Image URL detail."""

    AUTO = 'auto'
    LOW = 'low'
    HIGH = 'high'


# Define TypedDicts to represent the interfaces
class ImageURLDetail(BaseModel):
    """Image URL Detail."""

    url: str
    detail: DetailKind | None = None


class ContentItemType(StrEnum):
    """Enumveration variants for content item type."""

    TEXT = 'text'
    IMAGE_URL = 'image_url'


class ContentItem(BaseModel):
    """Content Item: can be text or image."""

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


ToolChoiceOptions = Literal['none', 'auto']


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
