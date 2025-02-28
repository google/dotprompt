import { runFlow, streamFlow } from 'genkit/beta/client';
import { useState } from 'react';

export interface FlowState<Input = any, Output = any, Chunk = any> {
  run: (input: Input) => Promise<Output>;
  stream: (input: Input) => Promise<Output>;
  isLoading: boolean;
  data: {
    /** The most recent chunk received from the flow. */
    latestChunk?: Chunk;
    /** All chunks from the current / most recent execution of the flow. */
    chunks: Chunk[];
    /** The output of the most recent execution of the flow. */
    output?: Output;
  };
}

interface FlowData<Output, Chunk> {
  chunks: Chunk[];
  isLoading: boolean;
  output?: Output;
}

export function useFlow<Input = any, Output = any, Chunk = any>(
  url: string,
): FlowState<Input, Output, Chunk> {
  const [{ isLoading, chunks, output }, setCurrent] = useState<
    FlowData<Output, Chunk>
  >({
    isLoading: false,
    chunks: [],
    output: undefined,
  });

  const run = async (input: Input) => {
    if (isLoading)
      throw new Error(`Cannot run flow while it's already running.`);
    setCurrent({ chunks: [], isLoading: true, output: undefined });
    const newOutput = await runFlow({ url, input });
    setCurrent({ isLoading: false, chunks: [], output: newOutput });
    return newOutput;
  };

  const stream = async (input: Input) => {
    if (isLoading)
      throw new Error(`Cannot stream flow while it's already running.`);
    setCurrent({ chunks: [], isLoading: true, output: undefined });
    const { stream, output } = streamFlow<Output, Chunk>({
      url,
      input,
    });

    for await (const chunk of stream) {
      setCurrent((current) => ({
        ...current,
        chunks: [...current.chunks, chunk],
      }));
    }

    const finalOutput = await output;
    setCurrent((current) => ({
      ...current,
      output: finalOutput,
      isLoading: false,
    }));
    return finalOutput;
  };

  return {
    run,
    stream,
    isLoading,
    data: {
      output,
      chunks,
      latestChunk: chunks.at(-1),
    },
  };
}
