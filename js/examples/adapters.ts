/**
 * Copyright 2024 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { toGeminiRequest } from '../src/adapters/gemini.js';
import { toOpenAIRequest } from '../src/adapters/openai.js';
import { Dotprompt } from '../src/index.js';

const prompts = new Dotprompt();

async function main() {
  const rendered = await prompts.render(
    `---
model: gemini-1.5-flash
input:
  schema:
    subject: string
---
{{role "user"}}Tell me a story about {{subject}}.
  `,
    { input: { subject: 'a birthday party' } }
  );

  const geminiFormat = toGeminiRequest(rendered);
  console.log(
    '> sending to gemini endpoint:',
    JSON.stringify(geminiFormat.request, null, 2)
  );
  const geminiResponse = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${geminiFormat.model}:generateContent?key=${process.env.GOOGLE_GENAI_API_KEY}`,
    {
      method: 'POST',
      body: JSON.stringify(geminiFormat.request),
      headers: { 'content-type': 'application/json' },
    }
  );
  console.log(geminiResponse.status, await geminiResponse.text());

  const openaiFormat = toOpenAIRequest(rendered);
  console.log(
    'sending to openai endpoint:',
    JSON.stringify(openaiFormat, null, 2)
  );

  const openaiResponse = await fetch(
    'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions',
    {
      method: 'POST',
      body: JSON.stringify(openaiFormat),
      headers: {
        'content-type': 'application/json',
        authorization: `Bearer ${process.env.GOOGLE_GENAI_API_KEY}`,
      },
    }
  );
  console.log(openaiResponse.status, await openaiResponse.text());
}

main();
