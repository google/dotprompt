Dotprompt (the `.prompt` file format) is used by creating `.prompt` files with YAML frontmatter and Handlebars to provide rich content for LLMs. A simple example:

```handlebars generate_character.prompt
---
model: googleai/gemini-2.5-flash
input:
  schema:
    setting: string, where the character lives
    personality?: string, the personality of the character
output:
  schema:
    name: string, the name of the character
    skills(array, list of character skills): string
    attributes:
      strength: number, strength [0-5]
      dexterity: number, dexterity [0-10]
---

Generate a character who lives in {{setting}}{{#if personality}} with personality {{personality}}{{/if}}.
```

- Dotprompt uses a special YAML-optimized schema definition format. Scalars: `string`, `number`, `boolean`. For arrys use parens: `fieldName(array, desc goes here):`, add descriptions after a comma e.g. `fieldName: boolean, desc goes here`.
- Always use Handlebars syntax for expressions `{{#if ... }}`, NEVER use `{% if ... %}`.
- Available helpers (# for block): `{{#if ...}}`, `{{#unless ...}}`, `{{#each ...}}`, {{json ...}}` (render object as json), `{{role "system"}}` (change message role), `{{media url="..."}}` (insert multimodal content).
- Partials can be created with `_partial_name.prompt` and included with `{{> partial_name}}` inside the prompts directory.