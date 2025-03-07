import { useFlow } from './use-flow.ts';
import { PromptExample } from '../types';
import { logEvent } from './firebase.ts';

export interface Input {
  query: string;
  existingPrompt?: string;
}

export interface GeneratePromptOutput {
  source: string;
  example?: PromptExample;
}

export function useGeneratePrompt() {
  const { data, isLoading, stream, error } = useFlow<
    Input,
    GeneratePromptOutput,
    GeneratePromptOutput
  >('https://generateprompt-niuqzqldsa-uc.a.run.app');

  const generate = (input: Input) => {
    logEvent('generate_prompt');
    return stream(input);
  };

  return {
    generate,
    isLoading,
    error,
    data: data.output || data.latestChunk,
  };
}
