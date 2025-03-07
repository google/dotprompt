import { runFlow, streamFlow } from 'genkit/beta/client';
import { useState } from 'react';
import { useUser } from './use-user.ts';

export interface FlowState<Input = any, Output = any, Chunk = any> {
  run: (input: Input) => Promise<Output>;
  stream: (input: Input) => Promise<Output>;
  isLoading: boolean;
  error?: {
    status: string;
    message: string;
  };
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
  error?: {
    status: string;
    message: string;
  };
}

export function useFlow<Input = any, Output = any, Chunk = any>(
  url: string,
  options?: { before?: (input: Input) => void },
): FlowState<Input, Output, Chunk> {
  const [{ isLoading, chunks, output, error }, setCurrent] = useState<
    FlowData<Output, Chunk>
  >({
    isLoading: false,
    chunks: [],
    output: undefined,
    error: undefined,
  });
  const { data: currentUser } = useUser();

  const run = async (input: Input) => {
    if (isLoading)
      throw new Error(`Cannot run flow while it's already running.`);
    // Reset error at the start of each run
    setCurrent({
      chunks: [],
      isLoading: true,
      output: undefined,
      error: undefined,
    });
    const headers: Record<string, string> = {};
    if (currentUser)
      headers['authorization'] = `Bearer ${await currentUser.getIdToken()}`;
    if (options?.before) options.before(input);
    try {
      const newOutput = await runFlow({
        url,
        input,
        headers,
      });
      setCurrent({
        isLoading: false,
        chunks: [],
        output: newOutput,
        error: undefined,
      });
      return await newOutput;
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : String(e);
      const errorStatus = (e as any).status || 'unknown';
      console.log('SETTING ERROR:', {
        status: errorStatus,
        message: errorMessage,
      });
      setCurrent({
        isLoading: false,
        chunks: [],
        output: undefined,
        error: {
          status: errorStatus,
          message: errorMessage,
        },
      });
      throw e;
    }
  };

  const stream = async (input: Input) => {
    if (isLoading)
      throw new Error(`Cannot stream flow while it's already running.`);
    // Reset error at the start of each stream
    setCurrent({
      chunks: [],
      isLoading: true,
      output: undefined,
      error: undefined,
    });
    const headers: Record<string, string> = {};
    if (currentUser)
      headers['authorization'] = `Bearer ${await currentUser.getIdToken()}`;

    try {
      const { stream, output } = streamFlow<Output, Chunk>({
        url,
        input,
        headers,
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
        error: undefined,
      }));
      return finalOutput;
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : String(e);
      const errorStatus = (e as any).status || 'unknown';
      setCurrent((current) => ({
        ...current,
        isLoading: false,
        error: {
          status: errorStatus,
          message: errorMessage,
        },
      }));
      throw e;
    }
  };

  return {
    run,
    stream,
    isLoading,
    error,
    data: {
      output,
      chunks,
      latestChunk: chunks.at(-1),
    },
  };
}
