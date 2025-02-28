import { useFlow } from './use-flow.ts';

export interface Input {
  query: string;
  existingPrompt?: string;
}

export function useGeneratePrompt() {
  const { data, isLoading, stream } = useFlow<Input, string, string>(
    'https://generateprompt-niuqzqldsa-uc.a.run.app',
  );

  return {
    generate: stream,
    isLoading,
    data: data.output || data.latestChunk,
  };
}
