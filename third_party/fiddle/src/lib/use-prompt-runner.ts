import { useFlow } from './use-flow.ts';
import { Fiddle } from '../types';

// For published fiddles with an ID
export interface RunPromptOptions {
  fiddle: string;
  prompt: string;
  version?: string;
  input?: any;
  context?: any;
}

// For unpublished fiddles without an ID
export interface RunDraftPromptOptions {
  fiddle: Fiddle;
  prompt: string;
  input?: any;
  context?: any;
}

// Hook for published fiddles (with ID)
export function usePromptRunner() {
  return useFlow<
    RunPromptOptions,
    { usage: { inputTokens: number; outputTokens: number }; output: any },
    any
  >(
    'https://runfiddleprompt-niuqzqldsa-uc.a.run.app',
    // 'http://127.0.0.1:5001/promptfiddle/us-central1/runFiddlePrompt',
  );
}

// Hook for unpublished fiddles (without ID)
export function useDraftPromptRunner() {
  return useFlow<
    RunDraftPromptOptions,
    { usage: { inputTokens: number; outputTokens: number }; output: any },
    any
  >(
    'https://rundraftprompt-niuqzqldsa-uc.a.run.app',
    // 'http://127.0.0.1:5001/promptfiddle/us-central1/runDraftPrompt',
  );
}
