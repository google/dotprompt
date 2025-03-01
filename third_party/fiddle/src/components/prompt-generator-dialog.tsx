import { useState, useEffect } from 'react';
import { Sparkles } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog.tsx';
import { Button } from './ui/button.tsx';
import { Textarea } from './ui/textarea.tsx';

interface PromptGeneratorDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onGenerate: (promptIdea: string) => Promise<void>;
  isGenerating: boolean;
}

export function PromptGeneratorDialog({
  open,
  onOpenChange,
  onGenerate,
  isGenerating,
}: PromptGeneratorDialogProps) {
  const [promptIdea, setPromptIdea] = useState('');

  // Reset the prompt idea when the dialog opens
  useEffect(() => {
    if (open) {
      setPromptIdea('');
    }
  }, [open]);

  const handleGeneratePrompt = async () => {
    if (!promptIdea || isGenerating) return;

    // Close dialog immediately
    onOpenChange(false);

    // Generate the prompt
    await onGenerate(promptIdea);

    // Reset the prompt idea
    setPromptIdea('');
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Prompt Generator</DialogTitle>
          <DialogDescription className="text-xs">
            I heard you like prompts, so I made a prompt generator that will
            generate a prompt based on the prompt that you type. Give it a try!
          </DialogDescription>
        </DialogHeader>
        <div className="flex items-center space-x-2 py-4">
          <div className="grid flex-1 gap-2">
            <Textarea
              placeholder="Describe your prompt idea..."
              value={promptIdea}
              onChange={(e) => setPromptIdea(e.target.value)}
              disabled={isGenerating}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleGeneratePrompt();
                }
              }}
            />
          </div>
        </div>
        <DialogFooter className="sm:justify-start">
          <Button
            type="submit"
            onClick={handleGeneratePrompt}
            disabled={!promptIdea || isGenerating}
            className="flex items-center min-w-full"
          >
            <Sparkles className="h-4 w-4 mr-2" />
            Generate Prompt
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default PromptGeneratorDialog;
