// src/completions.ts
var HANDLEBARS_HELPERS = [
  {
    label: "if",
    type: "keyword",
    info: "Conditionally renders content when the condition is truthy.",
    apply: "{{#if ${condition}}}\n	\n{{/if}}"
  },
  {
    label: "unless",
    type: "keyword",
    info: "Inverse of if - renders content when the condition is falsy.",
    apply: "{{#unless ${condition}}}\n	\n{{/unless}}"
  },
  {
    label: "each",
    type: "keyword",
    info: "Iterates over arrays or objects.",
    apply: "{{#each ${items}}}\n	{{this}}\n{{/each}}"
  },
  {
    label: "with",
    type: "keyword",
    info: "Changes the current context for the enclosed block.",
    apply: "{{#with ${context}}}\n	\n{{/with}}"
  },
  {
    label: "else",
    type: "keyword",
    info: "Else branch for if/unless blocks.",
    apply: "{{else}}"
  },
  {
    label: "log",
    type: "function",
    info: "Logs a value to the console for debugging.",
    apply: "{{log ${value}}}"
  },
  {
    label: "lookup",
    type: "function",
    info: "Dynamically looks up a value by key from an object.",
    apply: "{{lookup ${object} ${key}}}"
  }
];
var DOTPROMPT_HELPERS = [
  {
    label: "role",
    type: "keyword",
    info: "Defines a message with a specific role (system, user, model).",
    apply: '{{#role "${role}"}}\n	\n{{/role}}',
    boost: 10
  },
  {
    label: "json",
    type: "function",
    info: "Serializes a value to JSON format.",
    apply: "{{ json ${value} }}"
  },
  {
    label: "history",
    type: "function",
    info: "Inserts the conversation history at this point.",
    apply: "{{history}}"
  },
  {
    label: "section",
    type: "keyword",
    info: "Defines a named section that can be referenced elsewhere.",
    apply: '{{#section "${name}"}}\n	\n{{/section}}'
  },
  {
    label: "media",
    type: "function",
    info: "Embeds media content (images, audio, video) by URL.",
    apply: "{{media url=${url}}}"
  },
  {
    label: "ifEquals",
    type: "keyword",
    info: "Renders content when two values are equal.",
    apply: "{{#ifEquals ${value1} ${value2}}}\n	\n{{/ifEquals}}"
  },
  {
    label: "unlessEquals",
    type: "keyword",
    info: "Renders content when two values are NOT equal.",
    apply: "{{#unlessEquals ${value1} ${value2}}}\n	\n{{/unlessEquals}}"
  }
];
var ROLE_SNIPPETS = [
  {
    label: "system",
    type: "text",
    info: "System role block - sets the AI's behavior and context.",
    apply: '{{#role "system"}}\n	\n{{/role}}',
    boost: 5
  },
  {
    label: "user",
    type: "text",
    info: "User role block - represents user input.",
    apply: '{{#role "user"}}\n	\n{{/role}}',
    boost: 5
  },
  {
    label: "model",
    type: "text",
    info: "Model role block - represents AI responses (for few-shot examples).",
    apply: '{{#role "model"}}\n	\n{{/role}}',
    boost: 5
  }
];
var FRONTMATTER_FIELDS = [
  {
    label: "model",
    type: "property",
    info: "The AI model to use for this prompt.",
    apply: "model: "
  },
  {
    label: "config",
    type: "property",
    info: "Model configuration options.",
    apply: "config:\n  temperature: 0.7"
  },
  {
    label: "input",
    type: "property",
    info: "Input schema definition.",
    apply: "input:\n  schema:\n    name: string"
  },
  {
    label: "output",
    type: "property",
    info: "Output format and schema.",
    apply: "output:\n  format: json"
  },
  {
    label: "tools",
    type: "property",
    info: "Tools/functions available to the model.",
    apply: "tools:\n  - "
  },
  {
    label: "temperature",
    type: "property",
    info: "Controls randomness (0.0-2.0).",
    apply: "temperature: 0.7"
  },
  {
    label: "maxOutputTokens",
    type: "property",
    info: "Maximum number of tokens in the response.",
    apply: "maxOutputTokens: 1024"
  }
];
var MODEL_NAMES = [
  {
    label: "gemini-2.0-flash",
    type: "constant",
    info: "Fast Gemini 2.0 model"
  },
  {
    label: "gemini-2.0-flash-lite",
    type: "constant",
    info: "Lightweight Gemini 2.0"
  },
  {
    label: "gemini-1.5-pro",
    type: "constant",
    info: "Gemini 1.5 Pro (2M context)"
  },
  {
    label: "gemini-1.5-flash",
    type: "constant",
    info: "Fast Gemini 1.5 model"
  },
  { label: "gpt-4o", type: "constant", info: "OpenAI GPT-4o" },
  { label: "gpt-4o-mini", type: "constant", info: "OpenAI GPT-4o Mini" },
  {
    label: "claude-3-5-sonnet",
    type: "constant",
    info: "Anthropic Claude 3.5 Sonnet"
  },
  { label: "claude-3-opus", type: "constant", info: "Anthropic Claude 3 Opus" }
];
function dotpromptCompletions(context) {
  const { state, pos } = context;
  const doc = state.doc;
  const text = doc.toString();
  const textBefore = text.slice(0, pos);
  const line = doc.lineAt(pos);
  const lineText = line.text;
  const lineBefore = lineText.slice(0, pos - line.from);
  const frontmatterMatches = textBefore.split("---");
  const isInFrontmatter = frontmatterMatches.length === 2;
  if (isInFrontmatter) {
    if (/model:\s*$/.test(lineBefore)) {
      return {
        from: pos,
        options: MODEL_NAMES
      };
    }
    if (/^\s*$/.test(lineBefore)) {
      return {
        from: pos,
        options: FRONTMATTER_FIELDS
      };
    }
    const fieldMatch = lineBefore.match(/^\s*(\w*)$/);
    if (fieldMatch) {
      return {
        from: pos - fieldMatch[1].length,
        options: FRONTMATTER_FIELDS
      };
    }
    return null;
  }
  const handlebarsMatch = lineBefore.match(/\{\{([#/]?)(\w*)$/);
  if (handlebarsMatch) {
    const [, prefix, word] = handlebarsMatch;
    const from = pos - word.length;
    if (prefix === "#") {
      const blockHelpers = [
        ...HANDLEBARS_HELPERS.filter(
          (h) => ["if", "unless", "each", "with"].includes(h.label)
        ),
        ...DOTPROMPT_HELPERS.filter(
          (h) => ["role", "section", "ifEquals", "unlessEquals"].includes(h.label)
        )
      ].map((h) => ({
        ...h,
        apply: h.label
        // Just insert the helper name after {{#
      }));
      return {
        from,
        options: blockHelpers
      };
    }
    if (prefix === "/") {
      const blockNames = [
        "if",
        "unless",
        "each",
        "with",
        "role",
        "section",
        "ifEquals",
        "unlessEquals"
      ].map((name) => ({
        label: name,
        type: "keyword",
        apply: name
      }));
      return {
        from,
        options: blockNames
      };
    }
    return {
      from,
      options: [...HANDLEBARS_HELPERS, ...DOTPROMPT_HELPERS]
    };
  }
  if (lineBefore.endsWith("{")) {
    return {
      from: pos,
      options: [
        {
          label: "{{",
          type: "text",
          info: "Start a Handlebars expression",
          apply: "{ }}"
        },
        {
          label: "{{#",
          type: "text",
          info: "Start a Handlebars block",
          apply: "{# }}"
        },
        {
          label: "{{>",
          type: "text",
          info: "Include a partial",
          apply: "{> }}"
        },
        {
          label: "{{!",
          type: "text",
          info: "Add a comment",
          apply: "{!  }}"
        }
      ]
    };
  }
  const wordMatch = lineBefore.match(/(\w+)$/);
  if (wordMatch) {
    const from = pos - wordMatch[1].length;
    return {
      from,
      options: ROLE_SNIPPETS
    };
  }
  return null;
}

// src/language.ts
import { StreamLanguage } from "@codemirror/language";
var dotpromptStreamParser = {
  name: "dotprompt",
  startState() {
    return {
      context: "root",
      inBlockComment: false,
      blockDepth: 0
    };
  },
  token(stream, state) {
    if (state.inBlockComment) {
      if (stream.match("--}}") || stream.match("}}")) {
        state.inBlockComment = false;
        return "comment";
      }
      stream.next();
      return "comment";
    }
    if (state.context === "root") {
      if (stream.sol() && stream.match(/^#.*/)) {
        return "comment";
      }
      if (stream.sol() && stream.match(/^---\s*$/)) {
        state.context = "frontmatter";
        return "meta";
      }
      state.context = "template";
    }
    if (state.context === "frontmatter") {
      if (stream.sol() && stream.match(/^---\s*$/)) {
        state.context = "template";
        return "meta";
      }
      if (stream.match(/#.*/)) {
        return "comment";
      }
      if (stream.sol() && stream.match(/[a-zA-Z_][a-zA-Z0-9_-]*(?=\s*:)/)) {
        return "property";
      }
      if (stream.match(":")) {
        return "operator";
      }
      if (stream.match(/"([^"\\]|\\.)*"/)) {
        return "string";
      }
      if (stream.match(/'([^'\\]|\\.)*'/)) {
        return "string";
      }
      if (stream.match(/\d+(\.\d+)?/)) {
        return "number";
      }
      if (stream.match(/\b(true|false|null)\b/)) {
        return "atom";
      }
      if (stream.match(/[a-zA-Z_][a-zA-Z0-9_-]*(?=\s*:)/)) {
        return "property";
      }
      stream.next();
      return null;
    }
    if (state.context === "template") {
      if (stream.match("{{!--")) {
        state.inBlockComment = true;
        return "comment";
      }
      if (stream.match("{{!")) {
        if (stream.match(/.*?\}\}/)) {
          return "comment";
        }
        state.inBlockComment = true;
        return "comment";
      }
      if (stream.match(/<<<dotprompt:[^>]+>>>/)) {
        return "keyword";
      }
      if (stream.match(/\{\{#/)) {
        state.context = "handlebars";
        state.blockDepth++;
        return "bracket";
      }
      if (stream.match(/\{\{\//)) {
        state.context = "handlebars";
        state.blockDepth = Math.max(0, state.blockDepth - 1);
        return "bracket";
      }
      if (stream.match(/\{\{>/)) {
        state.context = "handlebars";
        return "bracket";
      }
      if (stream.match("{{")) {
        state.context = "handlebars";
        return "bracket";
      }
      stream.next();
      return null;
    }
    if (state.context === "handlebars") {
      stream.eatSpace();
      if (stream.match("}}")) {
        state.context = "template";
        return "bracket";
      }
      if (stream.match(/\b(if|unless|each|with|else|log|lookup)\b/)) {
        return "keyword";
      }
      if (stream.match(
        /\b(json|role|history|section|media|ifEquals|unlessEquals)\b/
      )) {
        return "variable-2";
      }
      if (stream.match(/@[a-zA-Z_][a-zA-Z0-9_]*/)) {
        return "variable-3";
      }
      if (stream.match(/"([^"\\]|\\.)*"/)) {
        return "string";
      }
      if (stream.match(/'([^'\\]|\\.)*'/)) {
        return "string";
      }
      if (stream.match(/\d+/)) {
        return "number";
      }
      if (stream.match(/[=]/)) {
        return "operator";
      }
      if (stream.match(/[a-zA-Z_][a-zA-Z0-9_.]*/)) {
        return "variable";
      }
      stream.next();
      return null;
    }
    stream.next();
    return null;
  }
};
var dotpromptLanguage = StreamLanguage.define(dotpromptStreamParser);

// src/theme.ts
import { HighlightStyle, syntaxHighlighting } from "@codemirror/language";
import { tags } from "@lezer/highlight";
var dotpromptDarkHighlighting = HighlightStyle.define([
  // Comments
  { tag: tags.comment, color: "#6A9955", fontStyle: "italic" },
  // Keywords (if, each, etc.)
  { tag: tags.keyword, color: "#C586C0" },
  // Dotprompt helpers (role, json, etc.) - variable-2
  { tag: tags.special(tags.variableName), color: "#4EC9B0" },
  // Variables
  { tag: tags.variableName, color: "#9CDCFE" },
  // @ variables - variable-3
  { tag: tags.local(tags.variableName), color: "#4FC1FF" },
  // Strings
  { tag: tags.string, color: "#CE9178" },
  // Numbers
  { tag: tags.number, color: "#B5CEA8" },
  // Booleans and null
  { tag: tags.atom, color: "#569CD6" },
  // Property names (YAML keys)
  { tag: tags.propertyName, color: "#569CD6" },
  // Operators
  { tag: tags.operator, color: "#D4D4D4" },
  // Brackets/delimiters
  { tag: tags.bracket, color: "#DCDCAA" },
  // Meta (frontmatter delimiters)
  { tag: tags.meta, color: "#6A9955" }
]);
var dotpromptLightHighlighting = HighlightStyle.define([
  // Comments
  { tag: tags.comment, color: "#008000", fontStyle: "italic" },
  // Keywords
  { tag: tags.keyword, color: "#AF00DB" },
  // Dotprompt helpers
  { tag: tags.special(tags.variableName), color: "#267F99" },
  // Variables
  { tag: tags.variableName, color: "#001080" },
  // @ variables
  { tag: tags.local(tags.variableName), color: "#0070C1" },
  // Strings
  { tag: tags.string, color: "#A31515" },
  // Numbers
  { tag: tags.number, color: "#098658" },
  // Booleans and null
  { tag: tags.atom, color: "#0000FF" },
  // Property names
  { tag: tags.propertyName, color: "#0000FF" },
  // Operators
  { tag: tags.operator, color: "#000000" },
  // Brackets
  { tag: tags.bracket, color: "#795E26" },
  // Meta
  { tag: tags.meta, color: "#008000" }
]);
var dotpromptDarkTheme = syntaxHighlighting(dotpromptDarkHighlighting);
var dotpromptLightTheme = syntaxHighlighting(
  dotpromptLightHighlighting
);

// src/index.ts
function dotprompt() {
  return [
    dotpromptLanguage,
    dotpromptLanguage.data.of({
      autocomplete: dotpromptCompletions
    })
  ];
}
export {
  dotprompt,
  dotpromptCompletions,
  dotpromptDarkHighlighting,
  dotpromptDarkTheme,
  dotpromptLanguage,
  dotpromptLightHighlighting,
  dotpromptLightTheme,
  dotpromptStreamParser
};
