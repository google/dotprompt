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
  examples?: PromptExample[];
}

export interface PromptExample {
  name: string;
  data: {
    input: any;
    context?: any;
  };
}
