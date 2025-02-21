/**
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { getEntries } from "astro:content";
import type { APIRoute } from "astro";

export const GET: APIRoute = async ({ params, request }) => {
  const docs = await getEntries([
    { collection: "docs", slug: "reference" },
    { collection: "docs", slug: "reference/frontmatter" },
    { collection: "docs", slug: "reference/picoschema" },
    { collection: "docs", slug: "reference/template" },
    { collection: "docs", slug: "reference/model" },
  ]);

  return new Response(
    `=== Dotprompt Template Format Documentation ===\n\nThe following is a complete reference to authoring files using the Dotprompt executable template format. This reference contains only information about the Dotprompt text format, not surrounding language or framework implementations.\n\n${docs
      .map((doc) => {
        return `# ${doc.data.title} (/${doc.slug})\n\n${doc.body}`;
      })
      .join("")}`,
    { headers: { "Content-Type": "text/plain; charset=utf-8" } },
  );
};
