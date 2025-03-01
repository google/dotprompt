import { useState, useEffect, useMemo } from 'react';
import { DataArgument } from 'dotprompt';

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

export function useExampleManagement(currentPrompt: Prompt | null) {
  const [dataArgSource, setDataArgSource] = useState<string>(`{
  "input": {},
  "context": {}
}`);
  const [selectedExampleIndex, setSelectedExampleIndex] = useState<
    number | null
  >(null);

  // Parse data argument
  const dataArg: DataArgument = useMemo(() => {
    try {
      return JSON.parse(dataArgSource);
    } catch (e) {
      return { input: {}, context: {} };
    }
  }, [dataArgSource]);

  // Load example when prompt changes
  useEffect(() => {
    if (currentPrompt?.examples?.length) {
      // If there's exactly one example, load it automatically
      setDataArgSource(JSON.stringify(currentPrompt.examples[0].data, null, 2));
      setSelectedExampleIndex(0);
    }
  }, [currentPrompt]);

  // Handle selecting an example from the dropdown
  const handleSelectExample = (index: number) => {
    if (!currentPrompt?.examples || !currentPrompt.examples[index]) return;

    const example = currentPrompt.examples[index];
    setDataArgSource(JSON.stringify(example.data, null, 2));
    setSelectedExampleIndex(index);
  };

  return {
    dataArgSource,
    setDataArgSource,
    dataArg,
    selectedExampleIndex,
    setSelectedExampleIndex,
    handleSelectExample,
  };
}
