export interface Fiddle {
  id: string;
  name: string;
  prompts: Prompt[];
}

export interface Prompt {
  name: string;
  source: string;
  partial?: boolean;
}
