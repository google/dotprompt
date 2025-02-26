import React, { useState, useEffect } from 'react';
import MonacoEditor, { useMonaco } from '@monaco-editor/react';
import { Button } from './components/ui/button.tsx';
import { ScrollArea } from './components/ui/scroll-area.tsx';
import ModeToggle from '@/components/mode-toggle.tsx';
import { generateUniqueId, cn } from './utils.ts';
import nightOwl from '@/themes/night-owl.json' with { type: 'json' };
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable.tsx';
import { SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar.tsx';
import AppSidebar from './app-sidebar.tsx';
import { Fiddle } from './types';
import { Dotprompt, RenderedPrompt, DataArgument } from 'dotprompt';
import MessageCard from './components/message.tsx';
import { ChevronRight, Play } from 'lucide-react';
interface Prompt {
  name: string;
  source: string;
}

function App() {
  const prompter = new Dotprompt({
    defaultModel: 'googleai/gemini-2.0-flash',
  });

  const [fiddle, setFiddle] = useState<Fiddle>({
    id: '',
    name: 'Fiddle',
    prompts: [],
  });
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [selectedPrompt, setSelectedPrompt] = useState<string | null>(null);
  const currentPrompt: Prompt | null =
    fiddle.prompts.find((p) => p.name === selectedPrompt) || null;
  const [renderedPrompt, setRenderedPrompt] = useState<
    RenderedPrompt | string | null
  >(null);
  const [dataArgSource, setDataArgSource] = useState<string>(`{
  "input": {},
  "context": {}
}`);
  let dataArg: DataArgument = {};
  try {
    dataArg = JSON.parse(dataArgSource);
  } catch (e) {
    dataArg = { input: {}, context: {} };
  }

  const monaco = useMonaco();
  useEffect(() => {
    monaco?.editor.defineTheme('night-owl', nightOwl as any);
    if (isDarkMode) monaco?.editor.setTheme('night-owl');
    monaco?.languages.register({ id: 'dotprompt' });
  }, [monaco]);

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
  }, [currentPrompt, dataArgSource]);

  useEffect(() => {
    // Check system dark mode preference
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setIsDarkMode(true);
    }

    const fiddleId = generateUniqueId(10);
    const initialPrompt = {
      name: 'main',
      source: `---
input:
  schema:
    storeType: string, the type of store
output:
  schema:
    products:
      name: string, the name of the product
      description: string, a 3-sentence description
      price: number, the price of the product in US dollars (e.g. 9.99)
      color: string, the color of the product
---

Generate 5 products for a {{storeType}} store.
`,
    };
    const fiddle = {
      id: fiddleId,
      name: `Fiddle ${fiddleId}`,
      prompts: [initialPrompt],
    };
    setFiddle(fiddle);
    window.history.pushState({}, '', `/${fiddleId}`);
    setSelectedPrompt('main');
  }, []);

  const handlePromptChange = (value: string | undefined) => {
    if (selectedPrompt) {
      setFiddle({
        ...fiddle,
        prompts: fiddle.prompts.map((p) =>
          p.name === selectedPrompt ? { ...p, source: value || '' } : p,
        ),
      });
    }
  };

  const handleDataArgChange = (value: string | undefined) => {
    setDataArgSource(value || '{}');
  };

  const handleRunPrompt = () => {
    setPlaygroundOutput(currentPrompt?.source || '');
  };

  return (
    <SidebarProvider>
      <AppSidebar
        fiddle={fiddle}
        setFiddle={setFiddle}
        setSelectedPrompt={setSelectedPrompt}
        selectedPrompt={selectedPrompt}
      />
      <main className="w-full h-screen overflow-y-hidden">
        <div className="flex border-b p-2">
          <div className="flex-1 flex items-center">
            <SidebarTrigger />
            {selectedPrompt && (
              <h2 className="flex items-center text-sm">
                {fiddle.name} <ChevronRight className="w-4 h-4 mx-2" />{' '}
                <strong>{selectedPrompt}.prompt</strong>
              </h2>
            )}
          </div>
          <ModeToggle isDarkMode={isDarkMode} setIsDarkMode={setIsDarkMode} />
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
                  options={{ automaticLayout: true }}
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
                    renderedPrompt.messages.map((m) => (
                      <MessageCard message={m} />
                    ))}
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
