import * as React from 'react';
import { Moon, Sun } from 'lucide-react';
import { Button } from './ui/button';

interface ModeToggleProps {
  isDarkMode: boolean;
  setIsDarkMode: React.Dispatch<React.SetStateAction<boolean>>;
}

export default function ModeToggle({
  isDarkMode,
  setIsDarkMode,
}: ModeToggleProps) {
  React.useEffect(() => {
    const root = window.document.documentElement;
    if (isDarkMode) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [isDarkMode]);

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setIsDarkMode(!isDarkMode)}
    >
      {isDarkMode ? <Sun /> : <Moon />}
      <span className="sr-only">Toggle theme</span>
    </Button>
  );
}
