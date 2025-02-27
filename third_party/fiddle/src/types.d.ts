export interface Fiddle {
  id?: string;
  name?: string;
  prompts: Prompt[];
  owner?: string;
}

export interface Prompt {
  name: string;
  source: string;
  partial?: boolean;
}
