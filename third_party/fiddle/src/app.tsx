import React, { useState, useEffect, useMemo, useRef } from 'react';
import MonacoEditor, { useMonaco } from '@monaco-editor/react';
import { Button } from './components/ui/button.tsx';
import { ScrollArea } from './components/ui/scroll-area.tsx';
import ModeToggle from '@/components/mode-toggle.tsx';
import { useFiddle } from './lib/use-fiddle-state.ts';
import {
  usePromptRunner,
  useDraftPromptRunner,
} from './lib/use-prompt-runner.ts';
import nightOwl from '@/themes/night-owl.json' with { type: 'json' };
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable.tsx';
import { SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar.tsx';
import AppSidebar from './app-sidebar.tsx';
import { Dotprompt, RenderedPrompt, DataArgument } from 'dotprompt';
import MessageCard from './components/message.tsx';
import ReactMarkdown from 'react-markdown';
import {
  ChevronRight,
  Play,
  Check,
  Upload,
  Circle,
  CircleEllipsis,
} from 'lucide-react';

interface Prompt {
  name: string;
  source: string;
}

function App() {
  const prompter = useMemo(
    () =>
      new Dotprompt({
        defaultModel: 'googleai/gemini-2.0-flash',
      }),
    [],
  );

  // Handle routing
  const idInitializedRef = useRef(false);
  const [fiddleId, setFiddleId] = useState<string | null>(null);

  // Effect to handle routing - only run once
  useEffect(() => {
    // Skip if we've already initialized the ID
    if (idInitializedRef.current) {
      return;
    }

    idInitializedRef.current = true;

    // Extract ID from URL if it exists
    const path = window.location.pathname;
    const extractedId = path.substring(1); // Remove leading slash

    // Only set ID if it exists in the URL
    if (extractedId) {
      setFiddleId(extractedId);
    }
    // Otherwise, leave fiddleId as null for in-memory mode
  }, []);

  // UI state
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [selectedPrompt, setSelectedPrompt] = useState<string | null>(null);
  const [renderedPrompt, setRenderedPrompt] = useState<
    RenderedPrompt | string | null
  >(null);
  const [dataArgSource, setDataArgSource] = useState<string>(`{
  "input": {},
  "context": {}
}`);

  // Use the fiddle hook for data management
  // Always call hooks in the same order - pass fiddleId directly, even if null
  const {
    draft,
    published,
    isLoading,
    isOwner,
    draftSaved,
    hasChanges,
    updateDraft,
    publish,
  } = useFiddle(fiddleId);
  useEffect(() => {
    console.log('draft:', draft?.id, draft?.name, draft?.prompts[0]);
  }, [draft]);

  // Always show draft if available, otherwise show published
  const fiddle = useMemo(() => {
    console.log('fiddle memo recalculating', {
      draft,
      published,
      fiddleId,
      isLoading,
    });
    if (draft) {
      console.log('USING DRAFT PROMPT', draft);
      return draft;
    }
    console.log('USING PUBLISHED PROMPT', published);
    return published;
  }, [draft, published, fiddleId, isLoading]);

  // Update selected prompt when fiddle changes or on initial load
  useEffect(() => {
    console.log('prompt selection effect', {
      fiddle,
      isLoading,
      selectedPrompt,
    });
    // If we have a fiddle with prompts, select the first one if none is selected
    if (fiddle && fiddle.prompts && fiddle.prompts.length > 0) {
      const firstPrompt = fiddle.prompts[0].name;
      // If no prompt is selected or the selected one doesn't exist in this fiddle
      if (
        !selectedPrompt ||
        !fiddle.prompts.find((p) => p.name === selectedPrompt)
      ) {
        console.log('Setting selected prompt to:', firstPrompt);
        setSelectedPrompt(firstPrompt);
      }
    }
  }, [fiddle, selectedPrompt]);

  // Get the current prompt
  const currentPrompt = useMemo<Prompt | null>(() => {
    console.log('currentPrompt memo recalculating', { fiddle, selectedPrompt });
    const prompt =
      fiddle?.prompts?.find((p) => p.name === selectedPrompt) || null;
    console.log('currentPrompt result', prompt);
    return prompt;
  }, [fiddle, selectedPrompt]);

  // Parse data argument
  const dataArg: DataArgument = useMemo(() => {
    try {
      return JSON.parse(dataArgSource);
    } catch (e) {
      return { input: {}, context: {} };
    }
  }, [dataArgSource]);

  // Monaco editor setup
  const monaco = useMonaco();
  useEffect(() => {
    monaco?.editor.defineTheme('night-owl', nightOwl as any);
    if (isDarkMode) monaco?.editor.setTheme('night-owl');
    monaco?.languages.register({ id: 'dotprompt' });
  }, [monaco, isDarkMode]);

  // Render prompt when it changes
  useEffect(() => {
    (async () => {
      if (currentPrompt) {
        try {
          setRenderedPrompt(
            await prompter.render(currentPrompt.source, dataArg),
          );
        } catch (e) {
          setRenderedPrompt((e as Error).message);
        }
      }
    })();
  }, [currentPrompt, dataArg]); // removed prompter from dependencies since it's stable

  // Check system dark mode preference
  useEffect(() => {
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setIsDarkMode(true);
    }
  }, []);

  const handlePromptChange = (value: string | undefined) => {
    console.log('handlePromptChange', {
      value,
      selectedPrompt,
      fiddle,
      currentPrompt,
    });
    if (!selectedPrompt || !fiddle) return;
    const updatedFiddle = {
      ...fiddle,
      prompts: fiddle.prompts.map((p) =>
        p.name === selectedPrompt ? { ...p, source: value || '' } : p,
      ),
    };

    console.log('updatedFiddle', updatedFiddle);
    // Anyone can update drafts, but only owner can update published fiddles
    if (!published || isOwner) {
      updateDraft(updatedFiddle);
    }
  };

  const handleDataArgChange = (value: string | undefined) => {
    setDataArgSource(value || '{}');
  };

  // Initialize the prompt runners
  const promptRunner = usePromptRunner();
  const draftPromptRunner = useDraftPromptRunner();

  // Format token count in XX.YYK format (measured in thousands)
  const formatTokenCount = (count: number): string => {
    const inThousands = count / 1000;
    return `${inThousands.toFixed(2)}K`;
  };

  // Extract token usage and output - handle both prompt runners
  const streamingOutput = useMemo<string | object | null>(() => {
    // Check which runner has data
    const runnerData = fiddleId ? promptRunner.data : draftPromptRunner.data;
    if (!runnerData) return null;

    if (runnerData.output) return runnerData.output.output;
    if (typeof runnerData.chunks[0] === 'string') {
      return runnerData.chunks.join('');
    }
    return runnerData.latestChunk;
  }, [fiddleId, promptRunner.data, draftPromptRunner.data]);

  // Get token usage information - handle both prompt runners
  const tokenUsage = useMemo(() => {
    // Check which runner has data
    const runnerData = fiddleId ? promptRunner.data : draftPromptRunner.data;
    if (!runnerData?.output?.usage) return null;

    const { inputTokens, outputTokens } = runnerData.output.usage;
    return {
      input: formatTokenCount(inputTokens),
      output: formatTokenCount(outputTokens),
      total: formatTokenCount(inputTokens + outputTokens),
    };
  }, [
    fiddleId,
    promptRunner.data?.output?.usage,
    draftPromptRunner.data?.output?.usage,
  ]);

  const handleRunPrompt = async () => {
    // Run the prompt
    if (!currentPrompt || !fiddle) return;

    try {
      if (fiddleId) {
        // For fiddles with IDs, use the regular prompt runner
        await promptRunner.stream({
          fiddle: fiddleId,
          prompt: currentPrompt.name,
          // Include version: "draft" if there's a draft version
          ...(draft ? { version: 'draft' } : {}),
          input: dataArg.input,
          context: dataArg.context,
        });
      } else {
        // For local-only fiddles, use the draft prompt runner
        await draftPromptRunner.stream({
          fiddle: fiddle, // Send the entire fiddle object
          prompt: currentPrompt.name,
          input: dataArg.input,
          context: dataArg.context,
        });
      }
    } catch (e) {
      console.error((e as Error).message);
    }
  };

  return (
    <SidebarProvider>
      <AppSidebar
        fiddle={fiddle}
        setFiddle={(updatedFiddle) => {
          // Anyone can update drafts, but only owner can update published fiddles
          if (!published || isOwner) {
            updateDraft(updatedFiddle);
          }
        }}
        setSelectedPrompt={setSelectedPrompt}
        selectedPrompt={selectedPrompt}
        isOwner={!published || isOwner} // Allow editing for drafts or if owner of published
        publishFiddle={publish}
        hasChanges={hasChanges}
      />
      <main className="w-full h-screen overflow-y-hidden">
        <div className="flex border-b p-2">
          <div className="flex-1 flex items-center">
            <SidebarTrigger />
            {selectedPrompt && fiddle && (
              <h2 className="flex items-center text-sm">
                {fiddle.name} <ChevronRight className="w-4 h-4 mx-2" />{' '}
                <strong>{selectedPrompt}.prompt</strong>
                {hasChanges && (
                  <>
                    <span className="ml-2 text-xs text-gray-500">(Draft)</span>
                    {draftSaved ? (
                      <Check className="w-4 h-4 ml-1 text-slate-500" />
                    ) : (
                      <CircleEllipsis className="w-4 h-4 ml-1 text-slate-500" />
                    )}
                  </>
                )}
              </h2>
            )}
          </div>
          <ModeToggle isDarkMode={isDarkMode} setIsDarkMode={setIsDarkMode} />
          {isOwner && hasChanges && (
            <Button
              variant="outline"
              className="text-s px-3 py-2 mr-2"
              onClick={async () => {
                // Call publish and update fiddleId if a new ID is returned
                const newId = await publish();
                if (newId && !fiddleId) {
                  setFiddleId(newId);
                }
              }}
            >
              <Upload className="w-4 h-4 text-blue-500" />
              Publish
            </Button>
          )}
          <Button
            variant="outline"
            className="text-s px-3 py-2"
            onClick={handleRunPrompt}
          >
            <Play className="w-4 h-4 text-green-400" />
            Run
          </Button>
        </div>
        <ResizablePanelGroup direction="horizontal">
          <ResizablePanel defaultSize={60}>
            <ResizablePanelGroup direction="vertical">
              <ResizablePanel defaultSize={67}>
                <MonacoEditor
                  className="absolute top-0 left-0 right-0 bottom-0"
                  language="handlebars"
                  value={currentPrompt?.source || ''}
                  theme={isDarkMode ? 'night-owl' : 'light'}
                  options={{
                    automaticLayout: true,
                    readOnly: !!published && !isOwner, // Read-only if it's a published fiddle and user is not the owner
                  }}
                  onChange={handlePromptChange}
                />
              </ResizablePanel>
              <ResizableHandle />
              <ResizablePanel>
                <div className="flex flex-col size-full">
                  <div className="border-y p-2 text-sm font-bold">
                    Prompt Input
                  </div>
                  <div className="flex-1 relative">
                    <MonacoEditor
                      className="absolute top-0 left-0 right-0 bottom-0"
                      language="json"
                      value={dataArgSource}
                      theme={isDarkMode ? 'night-owl' : 'light'}
                      options={{ automaticLayout: true }}
                      onChange={handleDataArgChange}
                    />
                  </div>
                </div>
              </ResizablePanel>
            </ResizablePanelGroup>
          </ResizablePanel>
          <ResizableHandle />
          <ResizablePanel>
            {/* Title Bar */}
            <div className="p-2">
              <ScrollArea className="h-[calc(100vh-120px)]">
                {renderedPrompt && typeof renderedPrompt === 'string' && (
                  <div className="bg-red-600 text-white p-4 rounded-lg my-4">
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
                    <div className="mt-4 p-4 border rounded-lg">
                      <div className="flex justify-between items-center mb-2">
                        <h3 className="text-sm font-bold">Output:</h3>
                        {tokenUsage && null && (
                          <div className="text-xs text-gray-500">
                            Tokens: {tokenUsage.input} in / {tokenUsage.output}{' '}
                            out / {tokenUsage.total} total
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
                  )}
                </div>
              </ScrollArea>
            </div>
          </ResizablePanel>
        </ResizablePanelGroup>
      </main>
    </SidebarProvider>
  );
}

export default App;
