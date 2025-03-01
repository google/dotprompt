import React from 'react';
import MonacoEditor from '@monaco-editor/react';
import { Button } from './ui/button.tsx';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu.tsx';
import { Save, ChevronDown } from 'lucide-react';

interface Example {
  name: string;
  data: {
    input: any;
    context?: any;
  };
}

interface DataInputEditorProps {
  dataSource: string;
  examples?: Example[];
  selectedExampleIndex: number | null;
  isDarkMode: boolean;
  isOwner: boolean;
  onExampleSelect: (index: number) => void;
  onSaveExampleClick: () => void;
  onChange: (value: string | undefined) => void;
}

export function DataInputEditor({
  dataSource,
  examples,
  selectedExampleIndex,
  isDarkMode,
  isOwner,
  onExampleSelect,
  onSaveExampleClick,
  onChange,
}: DataInputEditorProps) {
  return (
    <div className="flex flex-col size-full">
      <div className="border-y p-2 text-sm font-bold flex justify-between items-center">
        <div className="flex items-center">
          Prompt Input
          {examples && examples.length > 1 && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="h-6 ml-2 px-2">
                  <span className="text-xs">
                    {selectedExampleIndex !== null
                      ? examples[selectedExampleIndex].name
                      : 'Select Example'}
                  </span>
                  <ChevronDown className="ml-1 h-3 w-3" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start">
                {examples.map((example, index) => (
                  <DropdownMenuItem
                    key={index}
                    onClick={() => onExampleSelect(index)}
                  >
                    {example.name}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
        {isOwner && (
          <Button
            variant="ghost"
            size="sm"
            className="h-6 px-2"
            onClick={onSaveExampleClick}
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
          value={dataSource}
          theme={isDarkMode ? 'night-owl' : 'light'}
          options={{ automaticLayout: true }}
          onChange={onChange}
        />
      </div>
    </div>
  );
}
