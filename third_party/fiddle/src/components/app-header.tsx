import { Button } from './ui/button.tsx';
import ModeToggle from '@/components/mode-toggle.tsx';
import React from 'react';
import {
  ChevronRight,
  Play,
  Check,
  Upload,
  CircleEllipsis,
  Loader2,
  Sparkles,
  Share2,
} from 'lucide-react';
import { toast } from 'sonner';
import { SidebarTrigger } from '@/components/ui/sidebar.tsx';
import { Fiddle } from '../types';

interface AppHeaderProps {
  fiddle: Fiddle | null;
  selectedPrompt: string | null;
  hasChanges: boolean;
  draftSaved: boolean;
  isOwner: boolean;
  isRunning: boolean;
  isDarkMode: boolean;
  fiddleId: string | null;
  setIsDarkMode: React.Dispatch<React.SetStateAction<boolean>>;
  onPublish: () => Promise<string | null>;
  onRun: () => Promise<void>;
  onOpenPromptGenerator: () => void;
}

export function AppHeader({
  fiddle,
  selectedPrompt,
  hasChanges,
  draftSaved,
  isOwner,
  isRunning,
  isDarkMode,
  fiddleId,
  setIsDarkMode,
  onPublish,
  onRun,
  onOpenPromptGenerator,
}: AppHeaderProps) {
  return (
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
              onClick={onOpenPromptGenerator}
              disabled={isRunning}
              title="Generate prompt"
            >
              {isRunning ? (
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
      {fiddle && (
        <Button
          variant="outline"
          className="text-s px-3 py-2 mr-2"
          onClick={() => {
            // Copy the current URL to clipboard
            navigator.clipboard.writeText(window.location.href);
            // Show toast notification
            toast('URL copied to clipboard');
          }}
        >
          <Share2 className="w-4 h-4 text-teal-500" />
          Share
        </Button>
      )}
      {isOwner && hasChanges && (
        <Button
          variant="outline"
          className="text-s px-3 py-2 mr-2"
          onClick={onPublish}
        >
          <Upload className="w-4 h-4 text-blue-500" />
          Publish
        </Button>
      )}
      <Button
        variant="outline"
        className="text-s px-3 py-2"
        onClick={onRun}
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
  );
}
