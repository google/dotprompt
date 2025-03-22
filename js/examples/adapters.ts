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
