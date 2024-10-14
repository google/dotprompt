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

import {
  FileDataPart,
  FunctionCallPart,
  FunctionDeclaration,
  FunctionResponsePart,
  GenerateContentCandidate as GeminiCandidate,
  Content as GeminiMessage,
  Part as GeminiPart,
  GenerateContentResponse,
  GenerationConfig,
  GoogleGenerativeAI as OriginalGoogleGenerativeAI,
  InlineDataPart,
  RequestOptions,
  StartChatParams,
  Tool,
  FunctionDeclarationSchema,
  SchemaType,
  FunctionDeclarationSchemaProperty,
  CodeExecutionTool,
  ExecutableCodePart,
} from "@google/generative-ai";
import {
  DataArgument,
  MediaPart,
  Message,
  Part,
  PromptMetadata,
  ToolDefinition,
  ToolRequestPart,
  ToolResponsePart,
} from "../types";
import { DotpromptEnvironment } from "../environment";

export class GoogleGenerativeAI extends OriginalGoogleGenerativeAI {
  dotprompt?: DotpromptEnvironment;

  constructor(apiKey: string, options?: { dotprompt?: DotpromptEnvironment }) {
    super(apiKey);
    this.dotprompt = options?.dotprompt;
  }

  generatePrompt<Variables = Record<string, any>, ModelConfig = Record<string, any>>(
    source: string,
    data: DataArgument<Variables> = {},
    options?: PromptMetadata<ModelConfig>
  ) {
    if (!this.dotprompt) throw new Error("Must initialize with a Dotprompt environment.");
    const rendered = this.dotprompt.render(source, data, options);
    const model = this.getGenerativeModel({
      model: rendered.model!,
      ...rendered.config,
    });
    return model.generateContent({
      contents: rendered.messages.map((m) => toGeminiMessage(m)),
    });
  }

  generatePromptStream<Variables = Record<string, any>, ModelConfig = Record<string, any>>(
    source: string,
    data: DataArgument<Variables> = {},
    options?: PromptMetadata<ModelConfig>
  ) {
    if (!this.dotprompt) throw new Error("Must initialize with a Dotprompt environment.");
    const rendered = this.dotprompt.render(source, data, options);
    const model = this.getGenerativeModel({
      model: rendered.model!,
      ...rendered.config,
    });
    return model.generateContentStream({
      contents: rendered.messages.map((m) => toGeminiMessage(m)),
    });
  }
}

function toGeminiRole(role: Message["role"]): string {
  switch (role) {
    case "user":
      return "user";
    case "model":
      return "model";
    case "tool":
      return "function";
    default:
      return "user";
  }
}

function convertSchemaProperty(
  property: Record<string, any>
): FunctionDeclarationSchema | FunctionDeclarationSchemaProperty | undefined {
  if (!property) {
    return undefined;
  }
  if (property.type === "object") {
    const nestedProperties: Record<string, any> = {};
    Object.keys(property.properties).forEach((key) => {
      nestedProperties[key] = convertSchemaProperty(property.properties[key]);
    });
    return {
      type: SchemaType.OBJECT,
      properties: nestedProperties,
      required: property.required,
    };
  } else if (property.type === "array") {
    return {
      type: SchemaType.ARRAY,
      items: convertSchemaProperty(property.items),
    };
  } else {
    return {
      type: property.type.toUppercase() as SchemaType,
    };
  }
}

function toGeminiTool(tool: ToolDefinition): FunctionDeclaration {
  const declaration: FunctionDeclaration = {
    name: tool.name.replace(/\//g, "__"), // Gemini throws on '/' in tool name
    description: tool.description,
    parameters: convertSchemaProperty(tool.inputSchema) as FunctionDeclarationSchema,
  };
  return declaration;
}

function toInlineData(part: MediaPart): InlineDataPart {
  const dataUrl = part.media.url;
  const b64Data = dataUrl.substring(dataUrl.indexOf(",")! + 1);
  const contentType =
    part.media.contentType || dataUrl.substring(dataUrl.indexOf(":")! + 1, dataUrl.indexOf(";"));
  return { inlineData: { mimeType: contentType, data: b64Data } };
}

function toFileData(part: MediaPart): FileDataPart {
  if (!part.media.contentType)
    throw new Error("Must supply a `contentType` when sending File URIs to Gemini.");
  return {
    fileData: { mimeType: part.media.contentType, fileUri: part.media.url },
  };
}

function fromInlineData(inlinePart: InlineDataPart): MediaPart {
  // Check if the required properties exist
  if (
    !inlinePart.inlineData ||
    !inlinePart.inlineData.hasOwnProperty("mimeType") ||
    !inlinePart.inlineData.hasOwnProperty("data")
  ) {
    throw new Error("Invalid InlineDataPart: missing required properties");
  }
  const { mimeType, data } = inlinePart.inlineData;
  // Combine data and mimeType into a data URL
  const dataUrl = `data:${mimeType};base64,${data}`;
  return {
    media: {
      url: dataUrl,
      contentType: mimeType,
    },
  };
}

function toFunctionCall(part: ToolRequestPart): FunctionCallPart {
  if (!part?.toolRequest?.input) {
    throw Error("Invalid ToolRequestPart: input was missing.");
  }
  return {
    functionCall: {
      name: part.toolRequest.name,
      args: part.toolRequest.input,
    },
  };
}

function fromFunctionCall(part: FunctionCallPart): ToolRequestPart {
  if (!part.functionCall) {
    throw Error("Invalid FunctionCallPart");
  }
  return {
    toolRequest: {
      name: part.functionCall.name,
      input: part.functionCall.args,
    },
  };
}

function toFunctionResponse(part: ToolResponsePart): FunctionResponsePart {
  if (!part?.toolResponse?.output) {
    throw Error("Invalid ToolResponsePart: output was missing.");
  }
  return {
    functionResponse: {
      name: part.toolResponse.name,
      response: {
        name: part.toolResponse.name,
        content: part.toolResponse.output,
      },
    },
  };
}

function fromFunctionResponse(part: FunctionResponsePart): ToolResponsePart {
  if (!part.functionResponse) {
    throw new Error("Invalid FunctionResponsePart.");
  }
  return {
    toolResponse: {
      name: part.functionResponse.name.replace(/__/g, "/"), // restore slashes
      output: part.functionResponse.response,
    },
  };
}

function fromExecutableCode(part: GeminiPart): Part {
  if (!part.executableCode) {
    throw new Error("Invalid GeminiPart: missing executableCode");
  }
  return {
    toolRequest: {
      name: "executableCode",
      input: {
        language: part.executableCode.language,
        code: part.executableCode.code,
      },
    },
    metadata: { type: "executableCode" },
  };
}

function fromCodeExecutionResult(part: GeminiPart): Part {
  if (!part.codeExecutionResult) {
    throw new Error("Invalid GeminiPart: missing codeExecutionResult");
  }
  return {
    toolResponse: {
      name: "executableCode",
      output: {
        outcome: part.codeExecutionResult.outcome,
        output: part.codeExecutionResult.output,
      },
    },
    metadata: { type: "executableCode" },
  };
}

function toGeminiCodeExecution(part: ToolRequestPart): ExecutableCodePart {
  return {
    executableCode: {
      language: part.toolRequest.input.language,
      code: part.toolRequest.input.code,
    },
  };
}

function toGeminiPart(part: Part): GeminiPart {
  if (part.text !== undefined) return { text: part.text };
  if (part.media) {
    if (part.media.url.startsWith("data:")) return toInlineData(part);
    return toFileData(part);
  }
  if (part.toolRequest && part.metadata?.type === "executableCode")
    return toGeminiCodeExecution(part);
  if (part.toolRequest) return toFunctionCall(part);
  if (part.toolResponse) return toFunctionResponse(part);
  throw new Error("Unsupported Part type");
}

function fromGeminiPart(part: GeminiPart, jsonMode: boolean): Part {
  if (jsonMode && part.text !== undefined) {
    return { data: JSON.parse(part.text) };
  }
  if (part.text !== undefined) return { text: part.text };
  if (part.inlineData) return fromInlineData(part);
  if (part.functionCall) return fromFunctionCall(part);
  if (part.functionResponse) return fromFunctionResponse(part);
  if (part.executableCode) return fromExecutableCode(part);
  if (part.codeExecutionResult) return fromCodeExecutionResult(part);
  throw new Error("Unsupported GeminiPart type");
}

export function toGeminiMessage(message: Message): GeminiMessage {
  return {
    role: toGeminiRole(message.role),
    parts: message.content.map(toGeminiPart),
  };
}

export function toGeminiSystemInstruction(message: Message): GeminiMessage {
  return {
    role: "user",
    parts: message.content.map(toGeminiPart),
  };
}
