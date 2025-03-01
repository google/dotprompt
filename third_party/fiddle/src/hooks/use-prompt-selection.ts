import { useState, useEffect, useMemo } from 'react';
import { Fiddle } from '../types';

interface Prompt {
  name: string;
  source: string;
  partial?: boolean;
  examples?: {
    name: string;
    data: {
      input: any;
      context?: any;
    };
  }[];
}

export function usePromptSelection(
  fiddle: Fiddle | null,
  urlPromptName: string | null,
) {
  const [selectedPrompt, setSelectedPrompt] = useState<string | null>(null);

  // Update selected prompt when fiddle changes or on initial load
  useEffect(() => {
    // Skip if no fiddle or no prompts
    if (!fiddle || !fiddle.prompts || fiddle.prompts.length === 0) return;

    // If URL contains a prompt name, try to select it
    if (urlPromptName) {
      const promptExists = fiddle.prompts.some((p) => p.name === urlPromptName);
      if (promptExists) {
        setSelectedPrompt(urlPromptName);
        return;
      }
    }

    // If no prompt is selected or the selected one doesn't exist in this fiddle
    if (
      !selectedPrompt ||
      !fiddle.prompts.find((p) => p.name === selectedPrompt)
    ) {
      // Default to the first prompt
      const firstPrompt = fiddle.prompts[0].name;
      setSelectedPrompt(firstPrompt);
    }
  }, [fiddle, selectedPrompt, urlPromptName]);

  // Get the current prompt
  const currentPrompt = useMemo<Prompt | null>(() => {
    const prompt =
      fiddle?.prompts?.find((p) => p.name === selectedPrompt) || null;
    return prompt;
  }, [fiddle, selectedPrompt]);

  return { selectedPrompt, setSelectedPrompt, currentPrompt };
}
