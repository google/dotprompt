/**
 * Copyright 2024 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Message, Part, RenderedPrompt } from '../types.js';

export interface OpenAIMessage {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content:
    | string
    | null
    | Array<{
        type: 'text' | 'image_url';
        text?: string;
        image_url?: {
          url: string;
          detail?: 'auto' | 'low' | 'high';
        };
      }>;
  name?: string;
  tool_calls?: Array<{
    id: string;
    type: 'function';
    function: {
      name: string;
      arguments: string;
    };
  }>;
  tool_call_id?: string;
}

export interface OpenAIToolDefintiion {
  type: 'function';
  function: {
    name: string;
    description?: string;
    parameters?: Record<string, unknown>;
  };
}

export interface OpenAIRequest {
  messages: Array<OpenAIMessage>;
  model: string;
  frequency_penalty?: number;
  logit_bias?: Record<string, number>;
  max_tokens?: number;
  n?: number;
  presence_penalty?: number;
  response_format?: {
    type: 'text' | 'json_object';
  };
  seed?: number;
  stop?: string | Array<string>;
  stream?: boolean;
  temperature?: number;
  tool_choice?:
    | 'none'
    | 'auto'
    | {
        type: 'function';
        function: {
          name: string;
        };
      };
  tools?: Array<OpenAIToolDefintiion>;
  top_p?: number;
  user?: string;
}

function convertRole(role: Message['role']): OpenAIMessage['role'] {
  if (role === 'model') {
    return 'assistant';
  }
  return role;
}

function convertContent(parts: Part[]): OpenAIMessage['content'] {
  const result: Array<{
    type: 'text' | 'image_url';
    text?: string;
    image_url?: { url: string; detail?: 'auto' };
  }> = [];

  for (const part of parts) {
    if (part.text) {
      result.push({ type: 'text', text: part.text });
    } else if (part.media) {
      result.push({
        type: 'image_url',
        image_url: {
          url: part.media.url,
          detail: 'auto',
        },
      });
    } else if (part.toolRequest) {
      // Tool requests are handled separately via tool_calls
      continue;
    }
  }

  return result;
}

function convertTools(
  prompt: RenderedPrompt
): OpenAIToolDefintiion[] | undefined {
  if (!prompt.toolDefs?.length) {
    return undefined;
  }

  return prompt.toolDefs.map((tool) => ({
    type: 'function',
    function: {
      name: tool.name,
      description: tool.description,
      parameters: tool.inputSchema,
    },
  }));
}

export function toOpenAIRequest(source: RenderedPrompt): OpenAIRequest {
  const messages: OpenAIMessage[] = source.messages.map((msg) => {
    const base: OpenAIMessage = {
      role: convertRole(msg.role),
      content: convertContent(msg.content),
    };

    // Handle tool requests
    const toolRequests = msg.content.filter(
      (p): p is Extract<Part, { toolRequest: any }> => 'toolRequest' in p
    );
    if (toolRequests.length > 0) {
      base.tool_calls = toolRequests.map((p, idx) => ({
        id: p.toolRequest.ref || `call_${idx}`,
        type: 'function',
        function: {
          name: p.toolRequest.name,
          arguments: JSON.stringify(p.toolRequest.input || {}),
        },
      }));
    }

    // Handle tool responses
    const toolResponse = msg.content.find(
      (p): p is Extract<Part, { toolResponse: any }> => 'toolResponse' in p
    );
    if (toolResponse) {
      base.tool_call_id = toolResponse.toolResponse.ref;
    }

    if (msg.metadata?.name) {
      base.name = msg.metadata.name;
    }

    return base;
  });

  const request: OpenAIRequest = {
    messages,
    model: source.model || 'gpt-4',
  };

  // Handle configuration options
  if (source.config) {
    Object.assign(request, {
      temperature: source.config.temperature,
      top_p: source.config.top_p,
      max_tokens: source.config.max_tokens,
      presence_penalty: source.config.presence_penalty,
      frequency_penalty: source.config.frequency_penalty,
      stop: source.config.stop,
      stream: source.config.stream,
      user: source.config.user,
    });
  }

  // Handle tools
  const tools = convertTools(source);
  if (tools) {
    request.tools = tools;
    request.tool_choice = 'auto';
  }

  // Handle output format
  if (source.output?.format === 'json') {
    request.response_format = { type: 'json_object' };
  }

  return request;
}
