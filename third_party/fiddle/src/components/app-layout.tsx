import React, { ReactNode } from 'react';
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable.tsx';

interface AppLayoutProps {
  headerContent: ReactNode;
  promptEditorContent: ReactNode;
  dataInputContent: ReactNode;
  outputContent: ReactNode;
}

export function AppLayout({
  headerContent,
  promptEditorContent,
  dataInputContent,
  outputContent,
}: AppLayoutProps) {
  return (
    <main className="w-full h-screen overflow-y-hidden">
      {headerContent}
      <ResizablePanelGroup direction="horizontal">
        <ResizablePanel defaultSize={60}>
          <ResizablePanelGroup direction="vertical">
            <ResizablePanel defaultSize={67}>
              {promptEditorContent}
            </ResizablePanel>
            <ResizableHandle />
            <ResizablePanel>{dataInputContent}</ResizablePanel>
          </ResizablePanelGroup>
        </ResizablePanel>
        <ResizableHandle />
        <ResizablePanel>{outputContent}</ResizablePanel>
      </ResizablePanelGroup>
    </main>
  );
}
