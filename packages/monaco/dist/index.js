"use strict";
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/index.ts
var index_exports = {};
__export(index_exports, {
  LANGUAGE_ID: () => LANGUAGE_ID,
  createCompletionProvider: () => createCompletionProvider,
  createDotpromptTheme: () => createDotpromptTheme,
  createHoverProvider: () => createHoverProvider,
  dotpromptThemeRules: () => dotpromptThemeRules,
  languageConfiguration: () => languageConfiguration,
  monarchLanguage: () => monarchLanguage,
  registerDotpromptLanguage: () => registerDotpromptLanguage
});
module.exports = __toCommonJS(index_exports);

// src/completions.ts
var HANDLEBARS_HELPERS = [
  {
    label: "if",
    kind: 1,
    // Function
    insertText: "{{#if ${1:condition}}}\n	$0\n{{/if}}",
    insertTextRules: 4,
    // InsertAsSnippet
    documentation: "Conditionally renders content when the condition is truthy."
  },
  {
    label: "unless",
    kind: 1,
    insertText: "{{#unless ${1:condition}}}\n	$0\n{{/unless}}",
    insertTextRules: 4,
    documentation: "Inverse of if - renders content when the condition is falsy."
  },
  {
    label: "each",
    kind: 1,
    insertText: "{{#each ${1:items}}}\n	$0\n{{/each}}",
    insertTextRules: 4,
    documentation: "Iterates over arrays or objects. Use @index, @first, @last inside."
  },
  {
    label: "with",
    kind: 1,
    insertText: "{{#with ${1:context}}}\n	$0\n{{/with}}",
    insertTextRules: 4,
    documentation: "Changes the current context for the enclosed block."
  },
  {
    label: "else",
    kind: 14,
    // Keyword
    insertText: "{{else}}",
    documentation: "Else branch for if/unless blocks."
  },
  {
    label: "log",
    kind: 1,
    insertText: "{{log ${1:value}}}",
    insertTextRules: 4,
    documentation: "Logs a value to the console for debugging."
  },
  {
    label: "lookup",
    kind: 1,
    insertText: "{{lookup ${1:object} ${2:key}}}",
    insertTextRules: 4,
    documentation: "Dynamically looks up a value by key from an object."
  }
];
var DOTPROMPT_HELPERS = [
  {
    label: "role",
    kind: 1,
    insertText: '{{#role "${1|system,user,model|}"}}}\n	$0\n{{/role}}',
    insertTextRules: 4,
    documentation: "Defines a message with a specific role (system, user, or model)."
  },
  {
    label: "json",
    kind: 1,
    insertText: "{{ json ${1:value} }}",
    insertTextRules: 4,
    documentation: "Serializes a value to JSON format."
  },
  {
    label: "history",
    kind: 1,
    insertText: "{{history}}",
    documentation: "Inserts the conversation history at this point."
  },
  {
    label: "section",
    kind: 1,
    insertText: '{{#section "${1:name}"}}\n	$0\n{{/section}}',
    insertTextRules: 4,
    documentation: "Defines a named section that can be referenced elsewhere."
  },
  {
    label: "media",
    kind: 1,
    insertText: "{{media url=${1:url}}}",
    insertTextRules: 4,
    documentation: "Embeds media content (images, audio, video) by URL."
  },
  {
    label: "ifEquals",
    kind: 1,
    insertText: "{{#ifEquals ${1:value1} ${2:value2}}}\n	$0\n{{/ifEquals}}",
    insertTextRules: 4,
    documentation: "Renders content when two values are equal."
  },
  {
    label: "unlessEquals",
    kind: 1,
    insertText: "{{#unlessEquals ${1:value1} ${2:value2}}}\n	$0\n{{/unlessEquals}}",
    insertTextRules: 4,
    documentation: "Renders content when two values are NOT equal."
  }
];
var ROLE_SNIPPETS = [
  {
    label: "system",
    kind: 15,
    // Snippet
    insertText: '{{#role "system"}}\n	$0\n{{/role}}',
    insertTextRules: 4,
    documentation: "System role block - sets the AI's behavior and context."
  },
  {
    label: "user",
    kind: 15,
    insertText: '{{#role "user"}}\n	$0\n{{/role}}',
    insertTextRules: 4,
    documentation: "User role block - represents user input."
  },
  {
    label: "model",
    kind: 15,
    insertText: '{{#role "model"}}\n	$0\n{{/role}}',
    insertTextRules: 4,
    documentation: "Model role block - represents AI responses (for few-shot examples)."
  }
];
var FRONTMATTER_FIELDS = [
  {
    label: "model",
    kind: 5,
    // Field
    insertText: "model: ${1:gemini-2.0-flash}",
    insertTextRules: 4,
    documentation: "The AI model to use for this prompt."
  },
  {
    label: "config",
    kind: 5,
    insertText: "config:\n  temperature: ${1:0.7}",
    insertTextRules: 4,
    documentation: "Model configuration options."
  },
  {
    label: "input",
    kind: 5,
    insertText: "input:\n  schema:\n    ${1:name}: ${2:string}",
    insertTextRules: 4,
    documentation: "Input schema definition for the prompt."
  },
  {
    label: "output",
    kind: 5,
    insertText: "output:\n  format: ${1|json,text,media|}",
    insertTextRules: 4,
    documentation: "Output format and schema."
  },
  {
    label: "tools",
    kind: 5,
    insertText: "tools:\n  - ${1:toolName}",
    insertTextRules: 4,
    documentation: "Tools/functions available to the model."
  },
  {
    label: "temperature",
    kind: 5,
    insertText: "temperature: ${1:0.7}",
    insertTextRules: 4,
    documentation: "Controls randomness (0.0-2.0). Lower = more deterministic."
  },
  {
    label: "maxOutputTokens",
    kind: 5,
    insertText: "maxOutputTokens: ${1:1024}",
    insertTextRules: 4,
    documentation: "Maximum number of tokens in the response."
  }
];
var MODEL_NAMES = [
  {
    label: "gemini-2.0-flash",
    documentation: "Fast Gemini 2.0 model (1M context)"
  },
  {
    label: "gemini-2.0-flash-lite",
    documentation: "Lightweight Gemini 2.0 model"
  },
  { label: "gemini-1.5-pro", documentation: "Gemini 1.5 Pro (2M context)" },
  { label: "gemini-1.5-flash", documentation: "Fast Gemini 1.5 model" },
  { label: "gpt-4o", documentation: "OpenAI GPT-4o (128K context)" },
  { label: "gpt-4o-mini", documentation: "OpenAI GPT-4o Mini" },
  { label: "gpt-4-turbo", documentation: "OpenAI GPT-4 Turbo" },
  { label: "claude-3-5-sonnet", documentation: "Anthropic Claude 3.5 Sonnet" },
  { label: "claude-3-opus", documentation: "Anthropic Claude 3 Opus" }
].map((m) => ({
  ...m,
  kind: 12,
  // Value
  insertText: m.label
}));
function createCompletionProvider(monacoInstance) {
  return {
    triggerCharacters: ["{", ":", " ", '"'],
    provideCompletionItems(model, position) {
      const textUntilPosition = model.getValueInRange({
        startLineNumber: 1,
        startColumn: 1,
        endLineNumber: position.lineNumber,
        endColumn: position.column
      });
      const lineContent = model.getLineContent(position.lineNumber);
      const linePrefix = lineContent.substring(0, position.column - 1);
      const range = {
        startLineNumber: position.lineNumber,
        startColumn: position.column,
        endLineNumber: position.lineNumber,
        endColumn: position.column
      };
      const frontmatterMatch = textUntilPosition.match(/^---\n[\s\S]*?(?!---)/);
      const isInFrontmatter = frontmatterMatch && !textUntilPosition.includes("---\n---");
      if (isInFrontmatter) {
        if (/model:\s*$/.test(linePrefix)) {
          return {
            suggestions: MODEL_NAMES.map((item) => ({
              ...item,
              range
            }))
          };
        }
        if (/^\s*$/.test(linePrefix) || /^\s+$/.test(linePrefix)) {
          return {
            suggestions: FRONTMATTER_FIELDS.map((item) => ({
              ...item,
              range
            }))
          };
        }
        return { suggestions: [] };
      }
      const isInHandlebars = /\{\{[^}]*$/.test(linePrefix);
      if (isInHandlebars) {
        if (/\{\{#\s*$/.test(linePrefix)) {
          const blockHelpers = [
            ...HANDLEBARS_HELPERS.filter(
              (h) => ["if", "unless", "each", "with"].includes(h.label)
            ),
            ...DOTPROMPT_HELPERS.filter(
              (h) => ["role", "section", "ifEquals", "unlessEquals"].includes(h.label)
            )
          ].map((item) => ({
            ...item,
            insertText: item.label,
            range
          }));
          return { suggestions: blockHelpers };
        }
        if (/\{\{>\s*$/.test(linePrefix)) {
          return {
            suggestions: [
              {
                label: "partial",
                kind: 15,
                insertText: "${1:partialName}",
                insertTextRules: 4,
                documentation: "Reference a partial template",
                range
              }
            ]
          };
        }
        return {
          suggestions: [...HANDLEBARS_HELPERS, ...DOTPROMPT_HELPERS].map(
            (item) => ({ ...item, range })
          )
        };
      }
      if (linePrefix.endsWith("{")) {
        return {
          suggestions: [
            {
              label: "{{",
              kind: 15,
              insertText: "{$0}}",
              insertTextRules: 4,
              documentation: "Start a Handlebars expression",
              range
            },
            {
              label: "{{#",
              kind: 15,
              insertText: "{#$0}}",
              insertTextRules: 4,
              documentation: "Start a Handlebars block",
              range
            },
            {
              label: "{{>",
              kind: 15,
              insertText: "{> $0}}",
              insertTextRules: 4,
              documentation: "Include a partial",
              range
            },
            {
              label: "{{!",
              kind: 15,
              insertText: "{! $0 }}",
              insertTextRules: 4,
              documentation: "Add a comment",
              range
            }
          ]
        };
      }
      return {
        suggestions: [...ROLE_SNIPPETS].map((item) => ({ ...item, range }))
      };
    }
  };
}

// src/hover.ts
var HELPER_DOCS = {
  if: {
    description: "Conditionally renders content when the condition is truthy.",
    example: "{{#if isLoggedIn}}\n  Welcome back!\n{{/if}}"
  },
  unless: {
    description: "Inverse of `if` - renders content when the condition is falsy.",
    example: "{{#unless isLoggedIn}}\n  Please log in.\n{{/unless}}"
  },
  each: {
    description: "Iterates over arrays or objects. Inside the block, `this` refers to the current item. Use `@index`, `@first`, `@last`, `@key` for metadata.",
    example: "{{#each items}}\n  - {{this.name}} (index: {{@index}})\n{{/each}}"
  },
  with: {
    description: "Changes the current context for the enclosed block.",
    example: "{{#with user}}\n  Hello, {{name}}!\n{{/with}}"
  },
  else: {
    description: "Provides an else branch for `if` or `unless` blocks.",
    example: "{{#if condition}}\n  True\n{{else}}\n  False\n{{/if}}"
  },
  log: {
    description: "Logs a value to the console for debugging purposes.",
    example: "{{log user.name}}"
  },
  lookup: {
    description: "Dynamically looks up a value by key from an object.",
    example: '{{lookup user "name"}}'
  }
};
var DOTPROMPT_DOCS = {
  role: {
    description: "Defines a message with a specific role. Valid roles are `system`, `user`, and `model`.",
    example: '{{#role "system"}}\nYou are a helpful assistant.\n{{/role}}\n\n{{#role "user"}}\nHello!\n{{/role}}'
  },
  json: {
    description: "Serializes a value to JSON format for structured output.",
    example: "Here is the data: {{ json userData }}"
  },
  history: {
    description: "Inserts the conversation history at this point. Used for multi-turn conversations.",
    example: "{{history}}"
  },
  section: {
    description: "Defines a named section that can be extracted or referenced elsewhere.",
    example: '{{#section "instructions"}}\nFollow these rules...\n{{/section}}'
  },
  media: {
    description: "Embeds media content (images, audio, video) by URL. The AI model will process this media.",
    example: "{{media url=imageUrl}}"
  },
  ifEquals: {
    description: "Renders content when two values are equal.",
    example: '{{#ifEquals status "active"}}\n  Account is active\n{{/ifEquals}}'
  },
  unlessEquals: {
    description: "Renders content when two values are NOT equal.",
    example: '{{#unlessEquals role "admin"}}\n  Access denied\n{{/unlessEquals}}'
  }
};
var FRONTMATTER_DOCS = {
  model: {
    description: "The AI model to use for this prompt.",
    type: "string"
  },
  config: {
    description: "Model configuration options.",
    type: "object"
  },
  temperature: {
    description: "Controls randomness in output generation (0.0-2.0). Lower values are more deterministic, higher values are more creative.",
    type: "number"
  },
  maxOutputTokens: {
    description: "Maximum number of tokens in the response.",
    type: "number"
  },
  topP: {
    description: "Nucleus sampling parameter (0.0-1.0).",
    type: "number"
  },
  topK: {
    description: "Top-k sampling parameter.",
    type: "number"
  },
  input: {
    description: "Input schema definition for the prompt variables.",
    type: "object"
  },
  output: {
    description: "Output format and schema specification.",
    type: "object"
  },
  format: {
    description: "Output format: `json`, `text`, or `media`.",
    type: "string"
  },
  schema: {
    description: "Type schema for input or output.",
    type: "object"
  },
  tools: {
    description: "Tools/functions available to the model for function calling.",
    type: "array"
  },
  metadata: {
    description: "Custom metadata for the prompt.",
    type: "object"
  },
  default: {
    description: "Default values for input variables.",
    type: "object"
  }
};
function createHoverProvider(monacoInstance) {
  return {
    provideHover(model, position) {
      const word = model.getWordAtPosition(position);
      if (!word) {
        return null;
      }
      const wordText = word.word;
      const lineContent = model.getLineContent(position.lineNumber);
      const textUntilPosition = model.getValueInRange({
        startLineNumber: 1,
        startColumn: 1,
        endLineNumber: position.lineNumber,
        endColumn: position.column
      });
      const isInFrontmatter = textUntilPosition.split("---").length === 2 && textUntilPosition.startsWith("---");
      if (isInFrontmatter) {
        const frontmatterDoc = FRONTMATTER_DOCS[wordText];
        if (frontmatterDoc) {
          const contents = [
            {
              value: `**${wordText}**${frontmatterDoc.type ? `: \`${frontmatterDoc.type}\`` : ""}`
            },
            { value: frontmatterDoc.description }
          ];
          return {
            range: {
              startLineNumber: position.lineNumber,
              startColumn: word.startColumn,
              endLineNumber: position.lineNumber,
              endColumn: word.endColumn
            },
            contents
          };
        }
      }
      const isInHandlebars = /\{\{[^}]*$/.test(lineContent.substring(0, position.column)) || /\{\{#\w*$/.test(lineContent.substring(0, position.column)) || /\{\{\/\w*$/.test(lineContent.substring(0, position.column));
      if (isInHandlebars || /\{\{[#/]?\s*\w+/.test(lineContent)) {
        const dotpromptDoc = DOTPROMPT_DOCS[wordText];
        if (dotpromptDoc) {
          const contents = [
            { value: `**${wordText}** (Dotprompt helper)` },
            { value: dotpromptDoc.description }
          ];
          if (dotpromptDoc.example) {
            contents.push({
              value: `\`\`\`handlebars
${dotpromptDoc.example}
\`\`\``
            });
          }
          return {
            range: {
              startLineNumber: position.lineNumber,
              startColumn: word.startColumn,
              endLineNumber: position.lineNumber,
              endColumn: word.endColumn
            },
            contents
          };
        }
        const helperDoc = HELPER_DOCS[wordText];
        if (helperDoc) {
          const contents = [
            { value: `**${wordText}** (Handlebars helper)` },
            { value: helperDoc.description }
          ];
          if (helperDoc.example) {
            contents.push({
              value: `\`\`\`handlebars
${helperDoc.example}
\`\`\``
            });
          }
          return {
            range: {
              startLineNumber: position.lineNumber,
              startColumn: word.startColumn,
              endLineNumber: position.lineNumber,
              endColumn: word.endColumn
            },
            contents
          };
        }
      }
      return null;
    }
  };
}

// src/language.ts
var LANGUAGE_ID = "dotprompt";
var monarchLanguage = {
  defaultToken: "",
  tokenPostfix: ".dotprompt",
  // Handlebars keywords
  keywords: ["if", "unless", "each", "with", "else", "log", "lookup"],
  // Dotprompt-specific helpers
  dotpromptHelpers: [
    "json",
    "role",
    "history",
    "section",
    "media",
    "ifEquals",
    "unlessEquals"
  ],
  // YAML frontmatter keys
  yamlKeys: [
    "model",
    "config",
    "input",
    "output",
    "tools",
    "metadata",
    "default",
    "schema",
    "format",
    "temperature",
    "maxOutputTokens",
    "topP",
    "topK"
  ],
  // Operators and brackets
  brackets: [
    { open: "{{", close: "}}", token: "delimiter.handlebars" },
    { open: "{{#", close: "}}", token: "delimiter.handlebars.block" },
    { open: "{{/", close: "}}", token: "delimiter.handlebars.block" },
    { open: "{", close: "}", token: "delimiter.curly" },
    { open: "[", close: "]", token: "delimiter.square" }
  ],
  tokenizer: {
    root: [
      // License header comments (lines starting with #)
      [/^#.*$/, "comment.line"],
      // Frontmatter delimiter
      [/^---\s*$/, { token: "delimiter.frontmatter", next: "@frontmatter" }],
      // Dotprompt markers <<<dotprompt:...>>>
      [/<<<dotprompt:[^>]+>>>/, "keyword.marker"],
      // Include template tokens
      { include: "@template" }
    ],
    frontmatter: [
      // End of frontmatter
      [/^---\s*$/, { token: "delimiter.frontmatter", next: "@root" }],
      // YAML comments
      [/#.*$/, "comment.yaml"],
      // YAML keys
      [
        /([a-zA-Z_][a-zA-Z0-9_-]*)(\s*)(:)/,
        [
          {
            cases: {
              "@yamlKeys": "keyword.yaml",
              "@default": "variable.yaml"
            }
          },
          "",
          "delimiter.colon"
        ]
      ],
      // YAML strings
      [/"([^"\\]|\\.)*$/, "string.invalid"],
      // non-terminated string
      [/"/, { token: "string.quote", next: "@yamlDoubleString" }],
      [/'/, { token: "string.quote", next: "@yamlSingleString" }],
      // YAML numbers
      [/\d+(\.\d+)?/, "number"],
      // YAML booleans
      [/\b(true|false|null)\b/, "constant.language"],
      // Everything else in frontmatter
      [/./, "source.yaml"]
    ],
    yamlDoubleString: [
      [/[^\\"]+/, "string"],
      [/\\./, "string.escape"],
      [/"/, { token: "string.quote", next: "@pop" }]
    ],
    yamlSingleString: [
      [/[^\\']+/, "string"],
      [/\\./, "string.escape"],
      [/'/, { token: "string.quote", next: "@pop" }]
    ],
    template: [
      // Handlebars comments {{! ... }}
      [/\{\{!--/, { token: "comment.block", next: "@handlebarsBlockComment" }],
      [/\{\{!/, { token: "comment.block", next: "@handlebarsComment" }],
      // Handlebars block start {{#helper ...}}
      [
        /(\{\{#)(\s*)(\w+)/,
        [
          "delimiter.handlebars.block",
          "",
          {
            cases: {
              "@keywords": "keyword.handlebars",
              "@dotpromptHelpers": "keyword.dotprompt",
              "@default": "variable.handlebars"
            }
          }
        ]
      ],
      // Handlebars block end {{/helper}}
      [
        /(\{\{\/)(\s*)(\w+)(\s*)(\}\})/,
        [
          "delimiter.handlebars.block",
          "",
          {
            cases: {
              "@keywords": "keyword.handlebars",
              "@dotpromptHelpers": "keyword.dotprompt",
              "@default": "variable.handlebars"
            }
          },
          "",
          "delimiter.handlebars.block"
        ]
      ],
      // Handlebars else {{else}}
      [/\{\{else\}\}/, "keyword.handlebars"],
      // Partials {{> partialName}}
      [
        /(\{\{>)(\s*)([a-zA-Z_][a-zA-Z0-9_-]*)(\s*)(\}\})/,
        [
          "delimiter.handlebars",
          "",
          "variable.partial",
          "",
          "delimiter.handlebars"
        ]
      ],
      // Handlebars expressions {{ ... }}
      [
        /\{\{/,
        { token: "delimiter.handlebars", next: "@handlebarsExpression" }
      ],
      // Plain text
      [/[^{<]+/, ""],
      [/./, ""]
    ],
    handlebarsExpression: [
      // Close expression
      [/\}\}/, { token: "delimiter.handlebars", next: "@pop" }],
      // Helpers
      [
        /\b(\w+)\b/,
        {
          cases: {
            "@keywords": "keyword.handlebars",
            "@dotpromptHelpers": "keyword.dotprompt",
            "@default": "variable"
          }
        }
      ],
      // Strings in expressions
      [/"([^"\\]|\\.)*"/, "string"],
      [/'([^'\\]|\\.)*'/, "string"],
      // Numbers
      [/\d+/, "number"],
      // Operators
      [/[=]/, "operator"],
      // Dotted paths
      [/\./, "delimiter.dot"],
      // @ variables (@index, @first, etc.)
      [/@\w+/, "variable.special"],
      // Whitespace
      [/\s+/, ""]
    ],
    handlebarsComment: [
      [/\}\}/, { token: "comment.block", next: "@pop" }],
      [/./, "comment.block"]
    ],
    handlebarsBlockComment: [
      [/--\}\}/, { token: "comment.block", next: "@pop" }],
      [/./, "comment.block"]
    ]
  }
};
var languageConfiguration = {
  comments: {
    blockComment: ["{{!", "}}"]
  },
  brackets: [
    ["{{", "}}"],
    ["{{#", "}}"],
    ["{{/", "}}"],
    ["{", "}"],
    ["[", "]"],
    ["(", ")"]
  ],
  autoClosingPairs: [
    { open: "{{", close: "}}" },
    { open: "{", close: "}" },
    { open: "[", close: "]" },
    { open: "(", close: ")" },
    { open: '"', close: '"' },
    { open: "'", close: "'" }
  ],
  surroundingPairs: [
    { open: "{{", close: "}}" },
    { open: "{", close: "}" },
    { open: "[", close: "]" },
    { open: "(", close: ")" },
    { open: '"', close: '"' },
    { open: "'", close: "'" }
  ],
  folding: {
    markers: {
      start: /^\s*\{\{#/,
      end: /^\s*\{\{\//
    }
  },
  indentationRules: {
    increaseIndentPattern: /^\s*\{\{#(if|unless|each|with|role|section)/,
    decreaseIndentPattern: /^\s*\{\{\/(if|unless|each|with|role|section)/
  }
};

// src/index.ts
function registerDotpromptLanguage(monacoInstance, options = {}) {
  const { completions = true, hover = true, themes } = options;
  const disposables = [];
  monacoInstance.languages.register({
    id: LANGUAGE_ID,
    extensions: [".prompt"],
    aliases: ["Dotprompt", "dotprompt"],
    mimetypes: ["text/x-dotprompt"]
  });
  monacoInstance.languages.setMonarchTokensProvider(
    LANGUAGE_ID,
    monarchLanguage
  );
  monacoInstance.languages.setLanguageConfiguration(
    LANGUAGE_ID,
    languageConfiguration
  );
  if (completions) {
    disposables.push(
      monacoInstance.languages.registerCompletionItemProvider(
        LANGUAGE_ID,
        createCompletionProvider(monacoInstance)
      )
    );
  }
  if (hover) {
    disposables.push(
      monacoInstance.languages.registerHoverProvider(
        LANGUAGE_ID,
        createHoverProvider(monacoInstance)
      )
    );
  }
  if (themes) {
    for (const [themeName, themeData] of Object.entries(themes)) {
      monacoInstance.editor.defineTheme(themeName, themeData);
    }
  }
  return {
    dispose() {
      for (const disposable of disposables) {
        disposable.dispose();
      }
    }
  };
}
var dotpromptThemeRules = [
  // Frontmatter
  { token: "delimiter.frontmatter", foreground: "6A9955" },
  { token: "keyword.yaml", foreground: "569CD6" },
  { token: "variable.yaml", foreground: "9CDCFE" },
  { token: "source.yaml", foreground: "D4D4D4" },
  // Handlebars
  { token: "delimiter.handlebars", foreground: "DCDCAA" },
  { token: "delimiter.handlebars.block", foreground: "DCDCAA" },
  { token: "keyword.handlebars", foreground: "C586C0" },
  { token: "keyword.dotprompt", foreground: "4EC9B0" },
  { token: "variable", foreground: "9CDCFE" },
  { token: "variable.partial", foreground: "CE9178" },
  { token: "variable.special", foreground: "4FC1FF" },
  // Markers
  { token: "keyword.marker", foreground: "569CD6", fontStyle: "bold" },
  // Comments
  { token: "comment.block", foreground: "6A9955", fontStyle: "italic" },
  { token: "comment.line", foreground: "6A9955", fontStyle: "italic" },
  { token: "comment.yaml", foreground: "6A9955", fontStyle: "italic" },
  // Literals
  { token: "string", foreground: "CE9178" },
  { token: "string.quote", foreground: "CE9178" },
  { token: "string.escape", foreground: "D7BA7D" },
  { token: "number", foreground: "B5CEA8" },
  { token: "constant.language", foreground: "569CD6" }
];
function createDotpromptTheme(base = "vs-dark", name = "dotprompt-dark") {
  return {
    base,
    inherit: true,
    rules: dotpromptThemeRules,
    colors: {}
  };
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  LANGUAGE_ID,
  createCompletionProvider,
  createDotpromptTheme,
  createHoverProvider,
  dotpromptThemeRules,
  languageConfiguration,
  monarchLanguage,
  registerDotpromptLanguage
});
