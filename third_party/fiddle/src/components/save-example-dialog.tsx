import { useState, useEffect } from 'react';
import { Save } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog.tsx';
import { Button } from './ui/button.tsx';
import { Input } from './ui/input.tsx';

interface SaveExampleDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (exampleName: string) => void;
  existingExamples?: string[];
}

export function SaveExampleDialog({
  open,
  onOpenChange,
  onSave,
  existingExamples = [],
}: SaveExampleDialogProps) {
  const [exampleName, setExampleName] = useState('');

  // Reset the example name when the dialog opens
  useEffect(() => {
    if (open) {
      setExampleName('');
    }
  }, [open]);

  const handleSaveExample = () => {
    if (exampleName) {
      onSave(exampleName);
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Save Example</DialogTitle>
          <DialogDescription className="text-xs">
            Save the current input as an example for this prompt.
          </DialogDescription>
        </DialogHeader>
        <div className="flex items-center space-x-2 py-4">
          <div className="grid flex-1 gap-2">
            <Input
              placeholder="Example name"
              value={exampleName}
              onChange={(e) => setExampleName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSaveExample();
                }
              }}
            />
            {existingExamples.length > 0 && (
              <div className="text-xs text-gray-500 mt-2">
                Existing examples: {existingExamples.join(', ')}
              </div>
            )}
          </div>
        </div>
        <DialogFooter className="sm:justify-start">
          <Button
            type="submit"
            onClick={handleSaveExample}
            disabled={!exampleName}
            className="flex items-center min-w-full"
          >
            <Save className="h-4 w-4 mr-2" />
            Save Example
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default SaveExampleDialog;
