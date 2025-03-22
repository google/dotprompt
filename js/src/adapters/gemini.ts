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

export interface GeminiContent {
  role: 'user' | 'model';
  parts: Array<
    | {
        text: string;
      }
    | {
        inlineData: {
          mimeType: string;
          data: string;
        };
      }
  >;
}

export interface GeminiTool {
  functionDeclarations: Array<{
    name: string;
    description?: string;
    parameters: Record<string, unknown>;
  }>;
}

export interface GeminiSafetySetting {
  category:
    | 'HARM_CATEGORY_HARASSMENT'
    | 'HARM_CATEGORY_HATE_SPEECH'
    | 'HARM_CATEGORY_SEXUALLY_EXPLICIT'
    | 'HARM_CATEGORY_DANGEROUS_CONTENT';
  threshold:
    | 'BLOCK_NONE'
    | 'BLOCK_LOW_AND_ABOVE'
    | 'BLOCK_MEDIUM_AND_ABOVE'
    | 'BLOCK_HIGH_AND_ABOVE';
}

export interface GeminiRequest {
  model: string;
  request: {
    contents: GeminiContent[];
    systemInstruction?: { parts: GeminiContent['parts'] };
    tools?: GeminiTool;
    safetySettings?: GeminiSafetySetting[];
    generationConfig?: {
      temperature?: number;
      topP?: number;
      topK?: number;
      maxOutputTokens?: number;
      stopSequences?: string[];
      candidateCount?: number;
    };
  };
}

function convertRole(role: Message['role']): GeminiContent['role'] {
  if (role === 'user') return 'user';
  return 'model';
}

function extractBase64FromDataUrl(dataUrl: string): {
  mimeType: string;
  data: string;
} {
  const matches = dataUrl.match(/^data:([^;]+);base64,(.+)$/);
  if (!matches) {
    throw new Error('Invalid data URL format');
  }
  return {
    mimeType: matches[1],
    data: matches[2],
  };
}

function convertContent(parts: Part[]): GeminiContent['parts'] {
  const result: GeminiContent['parts'] = [];

  for (const part of parts) {
    if (part.text) {
      result.push({ text: part.text });
    } else if (part.media) {
      if (part.media.url.startsWith('data:')) {
        const { mimeType, data } = extractBase64FromDataUrl(part.media.url);
        result.push({
          inlineData: {
            mimeType: part.media.contentType || mimeType,
            data,
          },
        });
      } else {
        // For non-data URLs, we might need to fetch and convert to base64
        // This would require additional handling
        console.warn('Non-data URLs are not supported for media content');
      }
    }
  }

  return result;
}

function convertTools(prompt: RenderedPrompt): GeminiTool | undefined {
  if (!prompt.toolDefs?.length) return undefined;

  return {
    functionDeclarations: prompt.toolDefs.map((tool) => ({
      name: tool.name,
      description: tool.description,
      parameters: tool.inputSchema,
    })),
  };
}

export function toGeminiRequest(source: RenderedPrompt): GeminiRequest {
  const contents: GeminiContent[] = [];
  const systemInstruction: { parts: GeminiContent['parts'] } = { parts: [] };

  for (const msg of source.messages) {
    // Handle system messages separately
    if (msg.role === 'system') {
      systemInstruction.parts.push(...convertContent(msg.content));
      continue;
    }

    // Skip tool responses as they're handled differently in Gemini
    if (msg.role === 'tool') continue;

    const content: GeminiContent = {
      role: convertRole(msg.role),
      parts: convertContent(msg.content),
    };

    contents.push(content);
  }

  const request: GeminiRequest['request'] = {
    contents,
  };

  // Add system instructions if present
  if (systemInstruction.parts.length > 0) {
    request.systemInstruction = systemInstruction;
  }

  // Handle configuration options
  if (source.config) {
    request.generationConfig = {
      temperature: source.config.temperature,
      topP: source.config.top_p,
      maxOutputTokens: source.config.max_tokens,
      stopSequences: Array.isArray(source.config.stop)
        ? source.config.stop
        : source.config.stop
          ? [source.config.stop]
          : undefined,
      candidateCount: source.config.n,
    };
  }

  // Handle tools
  const tools = convertTools(source);
  if (tools) {
    request.tools = tools;
  }

  return { model: source.model!, request };
}
