import { useState, useEffect, useMemo, useRef } from 'react';
import { useMonaco } from '@monaco-editor/react';
import { useFiddle } from './lib/use-fiddle-state.ts';
import {
  usePromptRunner,
  useDraftPromptRunner,
} from './lib/use-prompt-runner.ts';
import { useGeneratePrompt } from './lib/use-generate-prompt.ts';
import nightOwl from '@/themes/night-owl.json' with { type: 'json' };
import { SidebarProvider } from '@/components/ui/sidebar.tsx';
import AppSidebar from './app-sidebar.tsx';
import { Dotprompt, RenderedPrompt } from 'dotprompt';
import { Toaster } from './components/ui/sonner.tsx';
import SaveExampleDialog from './components/save-example-dialog.tsx';
import PromptGeneratorDialog from './components/prompt-generator-dialog.tsx';
import { registerDotpromptLanguage } from './lib/monaco-dotprompt.ts';
import { Fiddle } from './types';

import { AppHeader } from './components/app-header.tsx';
import { PromptEditor } from './components/prompt-editor.tsx';
import { DataInputEditor } from './components/data-input-editor.tsx';
import { OutputPreview } from './components/output-preview.tsx';
import { AppLayout } from './components/app-layout.tsx';

import { useParams, useNavigate } from 'react-router-dom';
import { usePromptSelection } from './hooks/use-prompt-selection.ts';
import { useExampleManagement } from './hooks/use-example-management.ts';
import { logEvent } from './lib/firebase.ts';
import { GoogleSignInDialog } from './components/google-sign-in-dialog.tsx';

function App() {
  // Use TanStack Router hooks for routing
  const params = useParams();
  const navigate = useNavigate();

  // Extract fiddleId and promptName from route params
  const fiddleId = params.fiddleId || null;
  const urlPromptName = params.promptName || null;

  // Function to update the URL when fiddleId changes
  const setFiddleId = (newFiddleId: string | null) => {
    if (newFiddleId) {
      navigate(`/${newFiddleId}`);
    } else {
      navigate('/');
    }
  };

  // UI state
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [renderedPrompt, setRenderedPrompt] = useState<
    RenderedPrompt | string | null
  >(null);
  const [signInDialogOpen, setSignInDialogOpen] = useState(false);

  // Prompt generation state
  const [dialogOpen, setDialogOpen] = useState(false);
  const promptGenerator = useGeneratePrompt();

  // Example management state
  const [saveExampleDialogOpen, setSaveExampleDialogOpen] = useState(false);
  const [exampleName, setExampleName] = useState('');

  // Use the fiddle hook for data management
  const {
    draft,
    published,
    isLoading,
    isOwner,
    draftSaved,
    hasChanges,
    updateDraft: updateDraftRaw,
    updateStoredDraft,
    publish,
  } = useFiddle(fiddleId, urlPromptName);

  const prompter = useMemo(() => {
    const fiddle = draft || published;
    const partials = fiddle?.prompts
      .filter((p) => p.partial)
      .reduce(
        (acc, p) => {
          acc[p.name] = p.source;
          return acc;
        },
        {} as Record<string, string>,
      );
    return new Dotprompt({
      defaultModel: 'googleai/gemini-2.0-flash',
      partials,
    });
  }, [draft, published]);

  const updateDraft = (newDraft: Fiddle) => {
    updateDraftRaw(newDraft);
  };

  // Always show draft if available, otherwise show published
  const fiddle = draft || published;
  useEffect(() => {
    console.log('FIDDLE:', fiddle?.name, fiddle?.id);
  }, [fiddle]);

  // Use our custom hooks
  const { selectedPrompt, setSelectedPrompt, currentPrompt } =
    usePromptSelection(fiddle, urlPromptName);

  const {
    dataArgSource,
    setDataArgSource,
    dataArg,
    selectedExampleIndex,
    setSelectedExampleIndex,
    handleSelectExample,
  } = useExampleManagement(currentPrompt);

  // Monaco editor setup
  const monaco = useMonaco();
  useEffect(() => {
    monaco?.editor.defineTheme('night-owl', nightOwl as any);
    if (isDarkMode) monaco?.editor.setTheme('night-owl');
    if (monaco) registerDotpromptLanguage(monaco);
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
  }, [currentPrompt, dataArg, prompter]);

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

  // Add keyboard shortcut for Cmd+S (Ctrl+S) to trigger publish
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Check for Cmd+S (macOS) or Ctrl+S (Windows/Linux)
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault(); // Prevent the browser's save dialog

        // Only publish if user is owner and there are changes
        if (isOwner && hasChanges) {
          publish().then((newId) => {
            if (newId && !fiddleId) {
              setFiddleId(newId);
            }
          });
        }
      }
    };

    // Add event listener
    window.addEventListener('keydown', handleKeyDown);

    // Clean up
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOwner, hasChanges, publish, fiddleId, setFiddleId]);

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
      if ((e as Error).message.includes('RESOURCE_EXHAUSTED')) {
        setSignInDialogOpen(true);
      }
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
      if ((e as Error).message.includes('RESOURCE_EXHAUSTED')) {
        setSignInDialogOpen(true);
      }
      console.error((e as Error).message);
    }
  };

  const handleFork = () => {
    if (fiddle) {
      logEvent('fork', { id: fiddle.id });
      updateStoredDraft({ ...fiddle, name: fiddle.name + ' (Fork)' });
      window.location.href = '/';
    }
  };

  return (
    <SidebarProvider>
      <Toaster />
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
      <AppLayout
        headerContent={
          <AppHeader
            fiddle={fiddle}
            selectedPrompt={selectedPrompt}
            hasChanges={hasChanges}
            draftSaved={draftSaved}
            isOwner={isOwner}
            isRunning={isRunning}
            isDarkMode={isDarkMode}
            fiddleId={fiddleId}
            setIsDarkMode={setIsDarkMode}
            onPublish={async () => {
              // Call publish and update fiddleId if a new ID is returned
              const newId = await publish();
              if (newId && !fiddleId) {
                setFiddleId(newId);
              }
              return newId || null;
            }}
            onRun={handleRunPrompt}
            onOpenPromptGenerator={() => setDialogOpen(true)}
            onFork={handleFork}
          />
        }
        promptEditorContent={
          <PromptEditor
            source={currentPrompt?.source || ''}
            isDarkMode={isDarkMode}
            isReadOnly={(!!published && !isOwner) || promptGenerator.isLoading}
            onChange={handlePromptChange}
          />
        }
        dataInputContent={
          <DataInputEditor
            dataSource={dataArgSource}
            examples={currentPrompt?.examples}
            selectedExampleIndex={selectedExampleIndex}
            isDarkMode={isDarkMode}
            isOwner={!published || isOwner}
            onExampleSelect={handleSelectExample}
            onSaveExampleClick={() => setSaveExampleDialogOpen(true)}
            onChange={handleDataArgChange}
          />
        }
        outputContent={
          <OutputPreview
            renderedPrompt={renderedPrompt}
            streamingOutput={streamingOutput}
            tokenUsage={tokenUsage}
            error={
              fiddleId
                ? promptRunner.error
                  ? new Error(promptRunner.error.message)
                  : null
                : draftPromptRunner.error
                  ? new Error(draftPromptRunner.error.message)
                  : null
            }
            isDarkMode={isDarkMode}
          />
        }
      />

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
      <GoogleSignInDialog
        open={signInDialogOpen}
        onOpenChange={setSignInDialogOpen}
      />
    </SidebarProvider>
  );
}

export default App;
