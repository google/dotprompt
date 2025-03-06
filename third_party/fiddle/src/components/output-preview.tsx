import { ScrollArea } from './ui/scroll-area.tsx';
import MonacoEditor from '@monaco-editor/react';
import ReactMarkdown from 'react-markdown';
import MessageCard from './message.tsx';
import { RenderedPrompt } from 'dotprompt';

interface OutputPreviewProps {
  renderedPrompt: RenderedPrompt | string | null;
  streamingOutput: string | object | null;
  tokenUsage: {
    input: string;
    output: string;
    total: string;
  } | null;
  error: Error | null;
  isDarkMode: boolean;
}

export function OutputPreview({
  renderedPrompt,
  streamingOutput,
  tokenUsage,
  error,
  isDarkMode,
}: OutputPreviewProps) {
  return (
    <div className="p-2">
      <ScrollArea className="h-[calc(100vh-120px)]">
        {renderedPrompt && typeof renderedPrompt === 'string' && (
          <div className="dark:bg-slate-800 bg-gray-100 border-2 border-red-600 dark:text-white text-gray-900 p-4 rounded-lg my-4">
            {renderedPrompt}
          </div>
        )}
        <div className="p-4">
          {renderedPrompt &&
            typeof renderedPrompt === 'object' &&
            renderedPrompt.messages?.map((m, i) => (
              <MessageCard key={i} message={m} />
            ))}

          {/* Display streaming output */}
          {streamingOutput && (
            <>
              <div className="text-center my-4 text-xs uppercase text-foreground/50 flex items-center">
                <div className="border border-foreground/50 h-0 flex-1"></div>
                <div className="mx-4">
                  Prompt executed with Gemini 2.0 Flash
                </div>
                <div className="border border-foreground/50 h-0 flex-1"></div>
              </div>
              <div className="mt-4 p-4 border rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-sm font-bold">Output:</h3>
                  {tokenUsage && null && (
                    <div className="text-xs text-gray-500">
                      Tokens: {tokenUsage.input} in / {tokenUsage.output} out /{' '}
                      {tokenUsage.total} total
                    </div>
                  )}
                </div>
                {typeof streamingOutput === 'string' ? (
                  <div className="prose prose-sm dark:prose-invert">
                    <ReactMarkdown>{streamingOutput}</ReactMarkdown>
                  </div>
                ) : (
                  <div className="h-[400px] relative">
                    <MonacoEditor
                      className="absolute top-0 left-0 right-0 bottom-0"
                      language="json"
                      value={JSON.stringify(streamingOutput, null, 2)}
                      theme={isDarkMode ? 'night-owl' : 'light'}
                      options={{
                        readOnly: true,
                        minimap: { enabled: false },
                        lineNumbers: 'off',
                        folding: false,
                        automaticLayout: true,
                        wordWrap: 'on',
                      }}
                    />
                  </div>
                )}
              </div>
            </>
          )}

          {/* Display errors */}
          {error && (
            <div className="dark:bg-slate-900 bg-gray-100 border-2 border-red-400 dark:text-white text-gray-900 p-4 rounded-lg my-4">
              <h3 className="dark:text-red-300 text-red-500 mb-2">
                Generation Error
              </h3>
              <div className="text-sm font-mono">{error.message}</div>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
