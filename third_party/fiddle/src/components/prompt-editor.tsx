import MonacoEditor from '@monaco-editor/react';

interface PromptEditorProps {
  source: string;
  isDarkMode: boolean;
  isReadOnly: boolean;
  onChange: (value: string | undefined) => void;
}

export function PromptEditor({
  source,
  isDarkMode,
  isReadOnly,
  onChange,
}: PromptEditorProps) {
  return (
    <MonacoEditor
      className="absolute top-0 left-0 right-0 bottom-0"
      language="dotprompt"
      value={source}
      theme={isDarkMode ? 'night-owl' : 'light'}
      options={{
        automaticLayout: true,
        readOnly: isReadOnly,
      }}
      onChange={onChange}
    />
  );
}
