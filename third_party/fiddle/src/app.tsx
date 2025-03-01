import { useState, useEffect, useMemo, useRef } from 'react';
import MonacoEditor, { useMonaco } from '@monaco-editor/react';
import { Button } from './components/ui/button.tsx';
import { ScrollArea } from './components/ui/scroll-area.tsx';
import ModeToggle from '@/components/mode-toggle.tsx';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu.tsx';
import { useFiddle } from './lib/use-fiddle-state.ts';
import {
  usePromptRunner,
  useDraftPromptRunner,
} from './lib/use-prompt-runner.ts';
import { useGeneratePrompt } from './lib/use-generate-prompt.ts';
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
  CircleEllipsis,
  Loader2,
  Sparkles,
  Save,
  ChevronDown,
} from 'lucide-react';
import SaveExampleDialog from './components/save-example-dialog.tsx';
import PromptGeneratorDialog from './components/prompt-generator-dialog.tsx';
import { registerDotpromptLanguage } from './lib/monaco-dotprompt.ts';
import { Fiddle } from './types';

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

  // Prompt generation state
  const [dialogOpen, setDialogOpen] = useState(false);
  const promptGenerator = useGeneratePrompt();

  // Example management state
  const [saveExampleDialogOpen, setSaveExampleDialogOpen] = useState(false);
  const [exampleName, setExampleName] = useState('');
  const [selectedExampleIndex, setSelectedExampleIndex] = useState<
    number | null
  >(null);

  // Use the fiddle hook for data management
  // Always call hooks in the same order - pass fiddleId directly, even if null
  const {
    draft,
    published,
    isLoading,
    isOwner,
    draftSaved,
    hasChanges,
    updateDraft: updateDraftRaw,
    publish,
  } = useFiddle(fiddleId);

  const updateDraft = (newDraft: Fiddle) => {
    updateDraftRaw(newDraft);
  };

  // Always show draft if available, otherwise show published
  const fiddle = useMemo(() => {
    if (draft) {
      return draft;
    }
    return published;
  }, [draft, published, fiddleId, isLoading]);

  // Update selected prompt when fiddle changes or on initial load
  useEffect(() => {
    // If we have a fiddle with prompts, select the first one if none is selected
    if (fiddle && fiddle.prompts && fiddle.prompts.length > 0) {
      const firstPrompt = fiddle.prompts[0].name;
      // If no prompt is selected or the selected one doesn't exist in this fiddle
      if (
        !selectedPrompt ||
        !fiddle.prompts.find((p) => p.name === selectedPrompt)
      ) {
        setSelectedPrompt(firstPrompt);
      }
    }
  }, [fiddle, selectedPrompt]);

  // Get the current prompt
  const currentPrompt = useMemo<Prompt | null>(() => {
    const prompt =
      fiddle?.prompts?.find((p) => p.name === selectedPrompt) || null;
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
    if (monaco) registerDotpromptLanguage(monaco);
  }, [monaco, isDarkMode]);

  // Load example when prompt changes
  useEffect(() => {
    if (currentPrompt?.examples?.length) {
      // If there's exactly one example, load it automatically
      setDataArgSource(JSON.stringify(currentPrompt.examples[0].data, null, 2));
      setSelectedExampleIndex(0);
    }
  }, [currentPrompt]);

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
    if (!selectedPrompt || !fiddle) return;
    const updatedFiddle = {
      ...fiddle,
      prompts: fiddle.prompts.map((p) =>
        p.name === selectedPrompt ? { ...p, source: value || '' } : p,
      ),
    };

    // Anyone can update drafts, but only owner can update published fiddles
    if (!published || isOwner) {
      updateDraft(updatedFiddle);
    }
  };

  const handleDataArgChange = (value: string | undefined) => {
    setDataArgSource(value || '{}');
  };

  // Handle saving the current input as an example
  const handleSaveExample = () => {
    if (!selectedPrompt || !fiddle || !currentPrompt) return;

    // If a name was provided, save the example
    if (exampleName) {
      // Create a copy of the current prompt
      const updatedPrompt = { ...currentPrompt };

      // Initialize examples array if it doesn't exist
      if (!updatedPrompt.examples) {
        updatedPrompt.examples = [];
      }

      // Create the new example
      const newExample = {
        name: exampleName,
        data: {
          input: dataArg.input || {},
          context: dataArg.context || {},
        },
      };

      // If we're replacing an existing example
      if (
        selectedExampleIndex !== null &&
        updatedPrompt.examples[selectedExampleIndex]
      ) {
        // Replace the existing example
        updatedPrompt.examples[selectedExampleIndex] = newExample;
      } else {
        // Add as a new example
        updatedPrompt.examples.push(newExample);
      }

      // Update the fiddle with the new prompt
      const updatedFiddle = {
        ...fiddle,
        prompts: fiddle.prompts.map((p) =>
          p.name === selectedPrompt ? updatedPrompt : p,
        ),
      };

      // Update the draft
      if (!published || isOwner) {
        updateDraft(updatedFiddle);
      }

      // Reset state
      setExampleName('');
      setSelectedExampleIndex(null);
    }

    // Close the dialog
    setSaveExampleDialogOpen(false);
  };

  // Handle selecting an example from the dropdown
  const handleSelectExample = (index: number) => {
    if (!currentPrompt?.examples || !currentPrompt.examples[index]) return;

    const example = currentPrompt.examples[index];
    setDataArgSource(JSON.stringify(example.data, null, 2));
    setSelectedExampleIndex(index);
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

  // Check if a prompt is currently running
  const isRunning = useMemo(() => {
    return (
      promptRunner.isLoading ||
      draftPromptRunner.isLoading ||
      promptGenerator.isLoading
    );
  }, [
    promptRunner.isLoading,
    draftPromptRunner.isLoading,
    promptGenerator.isLoading,
  ]);

  // Track the last generated content to avoid duplicate updates
  const lastGeneratedContentRef = useRef<string | null>(null);

  // Update prompt content when generator produces new data
  useEffect(() => {
    // Only update during generation or when generation just completed
    if (
      promptGenerator.isLoading &&
      promptGenerator.data?.source &&
      selectedPrompt &&
      fiddle &&
      (!published || isOwner)
    ) {
      // Get the data in a type-safe way
      const { source, example } = promptGenerator.data;

      // Store the current data for comparison
      lastGeneratedContentRef.current = source;

      // Create a copy of the fiddle with the updated prompt (source only during streaming)
      const updatedPrompts = fiddle.prompts.map((p) => {
        if (p.name === selectedPrompt) {
          // Create a new prompt object with the updated source
          return {
            ...p,
            source,
            examples: example ? [example] : [],
          };
        }
        return p;
      });

      // Create the updated fiddle with the correct type
      const updatedFiddle = {
        ...fiddle,
        prompts: updatedPrompts,
      };

      updateDraft(updatedFiddle);
    }
    // When generation completes, make one final update with the latest content
    else if (
      !promptGenerator.isLoading &&
      promptGenerator.data &&
      typeof promptGenerator.data === 'object' &&
      'source' in promptGenerator.data &&
      typeof promptGenerator.data.source === 'string' &&
      lastGeneratedContentRef.current !== promptGenerator.data.source &&
      selectedPrompt &&
      fiddle &&
      (!published || isOwner)
    ) {
      // Get the data in a type-safe way - ensure we're properly extracting the example
      const { source } = promptGenerator.data;
      const example = promptGenerator.data.example;

      // Update the last generated content
      lastGeneratedContentRef.current = source;

      // Create a copy of the fiddle with the final prompt
      const updatedPrompts = fiddle.prompts.map((p) => {
        if (p.name === selectedPrompt) {
          // Create a new prompt object with the updated source
          const updatedPrompt = {
            ...p,
            source,
          };

          // Add the example if it exists
          if (example) {
            // Initialize examples array if it doesn't exist
            if (!updatedPrompt.examples) {
              updatedPrompt.examples = [];
            }

            // Check if we should replace an existing example or add a new one
            const existingExampleIndex = updatedPrompt.examples.findIndex(
              (ex) => ex.name === example.name,
            );

            if (existingExampleIndex >= 0) {
              // Replace existing example
              updatedPrompt.examples[existingExampleIndex] = example;
            } else {
              // Add new example
              updatedPrompt.examples.push(example);
            }
          }

          return updatedPrompt;
        }
        return p;
      });

      // Create the updated fiddle with the correct type
      const updatedFiddle = {
        ...fiddle,
        prompts: updatedPrompts,
      };

      updateDraft(updatedFiddle);

      // If an example was provided, update the input pane with it and select it
      if (example) {
        setDataArgSource(JSON.stringify(example.data, null, 2));

        // Find the index of the example in the updated prompt's examples array
        const updatedPrompt = updatedPrompts.find(
          (p) => p.name === selectedPrompt,
        );
        if (updatedPrompt?.examples) {
          const exampleIndex = updatedPrompt.examples.findIndex(
            (ex) => ex.name === example.name,
          );
          if (exampleIndex >= 0) {
            setSelectedExampleIndex(exampleIndex);
          }
        }
      }
    }
  }, [
    promptGenerator.data,
    promptGenerator.isLoading,
    selectedPrompt,
    fiddle,
    published,
    isOwner,
    updateDraft,
  ]);
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

  // Handle prompt generation
  const handleGeneratePrompt = async (promptIdea: string) => {
    if (!promptIdea || !currentPrompt || !fiddle) return;

    try {
      // Start generating the prompt
      await promptGenerator.generate({
        query: promptIdea,
        existingPrompt: currentPrompt.source,
      });
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
                {fiddleId && hasChanges && (
                  <>
                    <span className="ml-2 text-xs text-gray-500">(Draft)</span>
                    {draftSaved ? (
                      <Check className="w-4 h-4 ml-1 text-slate-500" />
                    ) : (
                      <CircleEllipsis className="w-4 h-4 ml-1 text-slate-500" />
                    )}
                  </>
                )}
                {/* Sparkle button for prompt generation */}
                <Button
                  variant="outline"
                  size="sm"
                  className="ml-3"
                  onClick={() => setDialogOpen(true)}
                  disabled={isRunning}
                  title="Generate prompt"
                >
                  {promptGenerator.isLoading ? (
                    <>
                      <Loader2 className="h-3 w-3 text-purple-500 animate-spin" />
                      Generating&hellip;
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-3 w-3 text-purple-500" />
                      Generate
                    </>
                  )}
                </Button>
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
            disabled={isRunning}
          >
            {isRunning ? (
              <>
                <Loader2 className="w-4 h-4 text-blue-400 animate-spin mr-1" />
                Running...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 text-green-400" />
                Run
              </>
            )}
          </Button>
        </div>
        <ResizablePanelGroup direction="horizontal">
          <ResizablePanel defaultSize={60}>
            <ResizablePanelGroup direction="vertical">
              <ResizablePanel defaultSize={67}>
                <MonacoEditor
                  className="absolute top-0 left-0 right-0 bottom-0"
                  language="dotprompt"
                  value={currentPrompt?.source || ''}
                  theme={isDarkMode ? 'night-owl' : 'light'}
                  options={{
                    automaticLayout: true,
                    readOnly:
                      (!!published && !isOwner) || promptGenerator.isLoading, // Read-only if it's a published fiddle and user is not the owner, or during prompt generation
                  }}
                  onChange={handlePromptChange}
                />
              </ResizablePanel>
              <ResizableHandle />
              <ResizablePanel>
                <div className="flex flex-col size-full">
                  <div className="border-y p-2 text-sm font-bold flex justify-between items-center">
                    <div className="flex items-center">
                      Prompt Input
                      {currentPrompt?.examples &&
                        currentPrompt.examples.length > 1 && (
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 ml-2 px-2"
                              >
                                <span className="text-xs">
                                  {selectedExampleIndex !== null
                                    ? currentPrompt.examples[
                                        selectedExampleIndex
                                      ].name
                                    : 'Select Example'}
                                </span>
                                <ChevronDown className="ml-1 h-3 w-3" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="start">
                              {currentPrompt.examples.map((example, index) => (
                                <DropdownMenuItem
                                  key={index}
                                  onClick={() => handleSelectExample(index)}
                                >
                                  {example.name}
                                </DropdownMenuItem>
                              ))}
                            </DropdownMenuContent>
                          </DropdownMenu>
                        )}
                    </div>
                    {(!published || isOwner) && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 px-2"
                        onClick={() => setSaveExampleDialogOpen(true)}
                      >
                        <Save className="h-3 w-3 mr-1" />
                        <span className="text-xs">Save Example</span>
                      </Button>
                    )}
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

                  {/* Display errors from prompt runners */}
                  {(fiddleId
                    ? promptRunner.error
                    : draftPromptRunner.error) && (
                    <div className="dark:bg-slate-900 bg-gray-100 border-2 border-red-400 dark:text-white text-gray-900 p-4 rounded-lg my-4">
                      <h3 className="dark:text-red-300 text-red-500 mb-2">
                        Generation Error
                      </h3>
                      <div className="text-sm font-mono">
                        {
                          (fiddleId
                            ? promptRunner.error
                            : draftPromptRunner.error
                          )?.message
                        }
                      </div>
                    </div>
                  )}
                  {/* Display errors from prompt generator */}
                  {promptGenerator.error && (
                    <div className="bg-slate-800 border-2 border-red-600 text-white p-4 rounded-lg my-4">
                      {promptGenerator.error.message}
                    </div>
                  )}
                </div>
              </ScrollArea>
            </div>
          </ResizablePanel>
        </ResizablePanelGroup>
      </main>

      {/* Save Example Dialog */}
      <SaveExampleDialog
        open={saveExampleDialogOpen}
        onOpenChange={setSaveExampleDialogOpen}
        onSave={handleSaveExample}
        existingExamples={currentPrompt?.examples?.map((ex) => ex.name) || []}
      />

      {/* Prompt Generation Dialog */}
      <PromptGeneratorDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onGenerate={handleGeneratePrompt}
        isGenerating={promptGenerator.isLoading}
      />
    </SidebarProvider>
  );
}

export default App;
