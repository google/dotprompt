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
 */

import { parse } from "yaml";
import {
  DataArgument,
  MediaPart,
  Message,
  ParsedPrompt,
  Part,
  PromptMetadata,
} from "./types";

const FRONTMATTER_REGEX = /^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$/;
const RESERVED_METADATA_KEYWORDS: (keyof PromptMetadata)[] = [
  "name",
  "variant",
  "version",
  "description",
  "model",
  "tools",
  "toolDefs",
  "config",
  "input",
  "output",
  "raw",
  "ext",
];

const BASE_METADATA: PromptMetadata<any> = {
  ext: {},
  metadata: {},
  config: {},
};

export function parseDocument<ModelConfig = Record<string, any>>(
  source: string
): ParsedPrompt<ModelConfig> {
  const match = source.match(FRONTMATTER_REGEX);
  if (match) {
    const [, frontmatter, content] = match;
    try {
      const parsedMetadata = parse(frontmatter) as PromptMetadata<ModelConfig>;
      const raw = { ...parsedMetadata };
      const pruned: PromptMetadata<ModelConfig> = { ...BASE_METADATA };
      const ext: PromptMetadata["ext"] = {};
      for (const k in raw) {
        const key = k as keyof PromptMetadata;
        if (RESERVED_METADATA_KEYWORDS.includes(key)) {
          pruned[key] = raw[key] as any;
        } else if (key.includes(".")) {
          const lastDotIndex = key.lastIndexOf(".");
          const namespace = key.substring(0, lastDotIndex);
          const fieldName = key.substring(lastDotIndex + 1);
          ext[namespace] = ext[namespace] || {};
          ext[namespace][fieldName] = raw[key];
        }
      }
      return { ...pruned, raw, ext, template: content.trim() };
    } catch (error) {
      console.error("Dotprompt: Error parsing YAML frontmatter:", error);
      return { ...BASE_METADATA, template: source.trim() };
    }
  }

  return { ...BASE_METADATA, template: source };
}

const ROLE_REGEX = /(<<<dotprompt:(?:role:[a-z]+|history))>>>/g;

export function toMessages<ModelConfig = Record<string, any>>(
  renderedString: string,
  data?: DataArgument
): Message[] {
  let currentMessage: { role: string; source: string } = {
    role: "user",
    source: "",
  };
  const messageSources: {
    role: string;
    source?: string;
    content?: Message["content"];
    metadata?: Record<string, unknown>;
  }[] = [currentMessage];

  for (const piece of renderedString.split(ROLE_REGEX).filter((s) => s.trim() !== "")) {
    if (piece.startsWith("<<<dotprompt:role:")) {
      const role = piece.substring(18);
      if (currentMessage.source.trim()) {
        currentMessage = { role, source: "" };
        messageSources.push(currentMessage);
      } else {
        currentMessage.role = role;
      }
    } else if (piece.startsWith("<<<dotprompt:history")) {
      messageSources.push(
        ...(data?.messages?.map((m) => {
          return {
            ...m,
            metadata: { ...(m.metadata || {}), purpose: "history" },
          };
        }) || [])
      );
      currentMessage = { role: "model", source: "" };
      messageSources.push(currentMessage);
    } else {
      currentMessage.source += piece;
    }
  }

  const messages: Message[] = messageSources
    .filter((ms) => ms.content || ms.source)
    .map((m) => {
      const out: Message = {
        role: m.role as Message["role"],
        content: m.content || toParts(m.source!),
      };
      if (m.metadata) out.metadata = m.metadata;
      return out;
    });

  return insertHistory(messages, data?.messages);
}

function insertHistory(messages: Message[], history: Message[] = []): Message[] {
  if (!history || messages.find((m) => m.metadata?.purpose === "history")) return messages;
  if (messages.at(-1)?.role === "user") {
    return [...messages.slice(0, -1)!, ...history!, messages.at(-1)!];
  }
  return [...messages, ...history];
}

const PART_REGEX = /(<<<dotprompt:(?:media:url|section).*?)>>>/g;

function toParts(source: string): Part[] {
  const parts: Part[] = [];
  const pieces = source.split(PART_REGEX).filter((s) => s.trim() !== "");
  for (let i = 0; i < pieces.length; i++) {
    const piece = pieces[i];
    if (piece.startsWith("<<<dotprompt:media:")) {
      const [_, url, contentType] = piece.split(" ");
      const part: MediaPart = { media: { url } };
      if (contentType) part.media.contentType = contentType;
      parts.push(part);
    } else if (piece.startsWith("<<<dotprompt:section")) {
      const [_, sectionType] = piece.split(" ");
      parts.push({ metadata: { purpose: sectionType, pending: true } });
    } else {
      parts.push({ text: piece });
    }
  }

  const apart: Part = { text: "foo" };

  return parts;
}
