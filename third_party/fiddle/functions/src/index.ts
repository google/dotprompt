/**
 * Import function triggers from their respective submodules:
 *
 * import {onCall} from "firebase-functions/v2/https";
 * import {onDocumentWritten} from "firebase-functions/v2/firestore";
 *
 * See a full list of supported triggers at https://firebase.google.com/docs/functions
 */

const geminiApiKey = defineSecret('GEMINI_API_KEY');

import {
  FunctionsErrorCode,
  HttpsError,
  onCallGenkit,
} from 'firebase-functions/https';
import { initializeApp } from 'firebase-admin/app';
import { getFirestore } from 'firebase-admin/firestore';
import { defineSecret } from 'firebase-functions/params';
import { ai, z } from './genkit.js';
import { GenkitError, UserFacingError } from 'genkit';
import { Dotprompt } from 'dotprompt';

const admin = initializeApp();
const db = getFirestore(admin);

export interface Fiddle {
  id: string;
  owner: string;
  name: string;
  prompts: Prompt[];
}

export interface Prompt {
  name: string;
  source: string;
  partial?: boolean;
}

async function executePrompt({
  fiddle,
  prompt: promptName,
  data,
  sendChunk,
}: {
  fiddle: Fiddle;
  prompt?: string;
  data?: { input?: any; context?: any };
  sendChunk: (chunk: any) => void;
}) {
  const prompt = fiddle.prompts.find(
    (p) => !p.partial && p.name === (promptName || 'main'),
  );
  if (!prompt) {
    throw new HttpsError(
      'not-found',
      `Fiddle '${fiddle.id}' does not have a prompt called '${promptName}'.`,
    );
  }

  const dotprompt = new Dotprompt({
    defaultModel: 'googleai/gemini-2.0-flash',
  });

  for (const partial of fiddle.prompts.filter((p) => p.partial)) {
    dotprompt.definePartial(partial.name, partial.source);
  }

  const rendered = await dotprompt.render(prompt.source, data);

  const output = rendered.output
    ? {
        ...rendered.output,
        schema: undefined,
        jsonSchema: rendered.output.schema,
      }
    : undefined;

  try {
    const response = ai.generate({
      config: rendered.config,
      messages: rendered.messages,
      output,
      onChunk: (chunk) => {
        sendChunk(chunk.output || chunk.text);
      },
    });
    const result = await response;

    return {
      usage: {
        inputTokens: result.usage.inputTokens,
        outputTokens: result.usage.outputTokens,
      },
      output: result.output || result.text,
    };
  } catch (e) {
    if (e instanceof GenkitError) {
      throw new HttpsError(
        e.status.toLowerCase().replace('_', '-') as FunctionsErrorCode,
        e.message,
      );
    } else if (e instanceof Error) {
      throw new HttpsError('unknown', e.message);
    }
    throw e;
  }
}

const runFiddleFlow = ai.defineFlow(
  {
    name: 'runFiddlePrompt',
    inputSchema: z.object({
      fiddle: z.string(),
      prompt: z.string().optional(),
      version: z.string().optional(),
      input: z.any().optional(),
      context: z.any().optional(),
    }),
  },
  async (
    {
      fiddle: fiddleId,
      prompt: promptName,
      version,
      input,
      context: contextArg,
    },
    { sendChunk, context },
  ) => {
    const snap = await db
      .doc(`fiddles/${fiddleId}${version ? `/versions/${version}` : ''}`)
      .get();
    if (!snap.exists) {
      throw new UserFacingError(
        'NOT_FOUND',
        `Fiddle '${fiddleId}' could not be found.`,
      );
    }
    const fiddle = { ...snap.data(), id: snap.id } as Fiddle;

    return executePrompt({
      fiddle,
      data: { input, context: contextArg },
      prompt: promptName,
      sendChunk,
    });
  },
);

export const runDraftPromptFlow = ai.defineFlow(
  {
    name: 'runDraftPrompt',
    inputSchema: z.object({
      fiddle: z.any(),
      prompt: z.string().optional(),
      input: z.any().optional(),
      context: z.any().optional(),
    }),
  },
  async (input, { context, sendChunk }) => {
    return executePrompt({
      fiddle: input.fiddle,
      prompt: input.prompt,
      data: { input: input.input, context: input.context },
      sendChunk,
    });
  },
);

export const runFiddlePrompt = onCallGenkit(
  {
    secrets: [geminiApiKey],
    cors: true,
  },
  runFiddleFlow,
);

export const runDraftPrompt = onCallGenkit(
  {
    secrets: [geminiApiKey],
    cors: true,
  },
  runDraftPromptFlow,
);
