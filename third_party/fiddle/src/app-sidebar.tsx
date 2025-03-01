import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar.tsx';
import { Button } from '@/components/ui/button.tsx';
import { Fiddle, Prompt } from './types';
import { useState, useRef, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { ChevronsUpDown, Plus, X } from 'lucide-react';
import Logo from '@/components/logo.tsx';

export default function AppSidebar({
  fiddle,
  setFiddle,
  setSelectedPrompt,
  selectedPrompt,
  isOwner = false,
  hasChanges = false,
}: {
  fiddle?: Fiddle | null;
  setFiddle: (fiddle: Fiddle) => void;
  selectedPrompt: string | null;
  setSelectedPrompt: (prompt: string) => void;
  isOwner?: boolean;
  publishFiddle?: () => Promise<string | undefined>;
  hasChanges?: boolean;
}) {
  const [addingPrompt, setAddingPrompt] = useState(false);
  const [newPromptName, setNewPromptName] = useState('');
  const newPromptInputRef = useRef<HTMLInputElement>(null);
  const [addingPartial, setAddingPartial] = useState(false);
  const [newPartialName, setNewPartialName] = useState('');
  const newPartialInputRef = useRef<HTMLInputElement>(null);
  const [editingPrompt, setEditingPrompt] = useState<string | null>(null);
  const [renamedPromptName, setRenamedPromptName] = useState('');
  const renamedPromptInputRef = useRef<HTMLInputElement>(null);
  const [editingFiddleName, setEditingFiddleName] = useState(false);
  const [newFiddleName, setNewFiddleName] = useState('');
  const fiddleNameInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (addingPrompt && newPromptInputRef.current) {
      newPromptInputRef.current.focus();
    }
  }, [addingPrompt]);

  useEffect(() => {
    if (addingPartial && newPartialInputRef.current) {
      newPartialInputRef.current.focus();
    }
  }, [addingPartial]);

  useEffect(() => {
    if (editingPrompt && renamedPromptInputRef.current) {
      renamedPromptInputRef.current.focus();
    }
  }, [editingPrompt]);

  useEffect(() => {
    if (editingFiddleName && fiddleNameInputRef.current) {
      fiddleNameInputRef.current.focus();
      fiddleNameInputRef.current.select();
    }
  }, [editingFiddleName]);

  const handleAddPrompt = () => {
    setAddingPrompt(true);
  };

  const handleAddPartial = () => {
    setAddingPartial(true);
  };

  const handleAddPromptConfirm = (e: React.FormEvent) => {
    e.preventDefault();
    if (newPromptName.trim()) {
      const newPrompt: Prompt = {
        name: newPromptName.trim(),
        source: '{{! your prompt here }}',
      };
      const updatedFiddle = {
        ...fiddle,
        prompts: [...(fiddle?.prompts || []), newPrompt],
      };
      setFiddle(updatedFiddle);
      setSelectedPrompt(newPrompt.name);
      setNewPromptName('');
      setAddingPrompt(false);
    }
  };

  const handleAddPartialConfirm = (e: React.FormEvent) => {
    e.preventDefault();
    if (newPartialName.trim()) {
      const newPartial: Prompt = {
        name: newPartialName.trim(),
        source: '{{! your partial here }}',
        partial: true,
      };
      const updatedFiddle = {
        ...fiddle,
        prompts: [...(fiddle?.prompts || []), newPartial],
      };
      setFiddle(updatedFiddle);
      setSelectedPrompt(newPartial.name);
      setNewPartialName('');
      setAddingPartial(false);
    }
  };

  const handleRenamePrompt = (prompt: Prompt) => {
    setEditingPrompt(prompt.name);
    setRenamedPromptName(prompt.name);
    setTimeout(() => {
      if (renamedPromptInputRef.current) {
        renamedPromptInputRef.current.select();
      }
    }, 0);
  };

  const handleRenamePromptConfirm = (e: React.FormEvent, oldName: string) => {
    e.preventDefault();
    if (renamedPromptName.trim() && oldName) {
      const updatedFiddle = {
        ...fiddle,
        prompts:
          fiddle?.prompts?.map((p) =>
            p.name === oldName ? { ...p, name: renamedPromptName.trim() } : p,
          ) || [],
      };
      setFiddle(updatedFiddle);
      setSelectedPrompt(renamedPromptName.trim());
      setEditingPrompt(null);
      setRenamedPromptName('');
    }
  };

  const handleDeletePrompt = (promptToDelete: Prompt) => {
    if (!fiddle) return;
    if (window.confirm(`Delete prompt "${promptToDelete.name}"?`)) {
      setFiddle({
        ...fiddle,
        prompts: fiddle.prompts.filter((p) => p.name !== promptToDelete.name),
      });
    }
  };

  const handleEditFiddleName = () => {
    if (!fiddle || (!isOwner && !hasChanges)) return;

    setEditingFiddleName(true);
    setNewFiddleName(fiddle.name || '');
  };

  const handleFiddleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setNewFiddleName(e.target.value);
  };

  const handleFiddleNameSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!fiddle) return;

    if (newFiddleName.trim()) {
      setFiddle({
        ...fiddle,
        name: newFiddleName.trim(),
      });
    }
    setEditingFiddleName(false);
  };

  const handleFiddleNameBlur = () => {
    setEditingFiddleName(false);
  };

  return (
    <Sidebar variant="sidebar">
      <SidebarHeader>
        <div className="border rounded-lg p-3 flex items-center">
          <img src="/icon.png" className="size-6 mr-2" />
          <div className="flex-1">
            <h1 className="font-bold text-sm">Dotprompt Fiddle</h1>
          </div>
          <ChevronsUpDown className="size-4" />
        </div>
        <div
          className="border rounded-lg py-2 px-3 text-center flex items-center"
          onClick={handleEditFiddleName}
          style={{ cursor: isOwner || hasChanges ? 'pointer' : 'default' }}
        >
          {editingFiddleName ? (
            <form onSubmit={handleFiddleNameSubmit} className="flex-1">
              <Input
                ref={fiddleNameInputRef}
                type="text"
                value={newFiddleName}
                onChange={handleFiddleNameChange}
                onBlur={handleFiddleNameBlur}
                className="text-sm text-center h-6 py-0"
              />
            </form>
          ) : (
            <h2 className="flex-1 text-sm">{fiddle?.name}</h2>
          )}
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>
            Prompts
            <Button
              variant="ghost"
              size="icon"
              className="ml-1"
              onClick={handleAddPrompt}
            >
              <Plus className="h-4 w-4" />
            </Button>
          </SidebarGroupLabel>
          <SidebarGroupContent>
            {addingPrompt && (
              <form onSubmit={handleAddPromptConfirm}>
                <Input
                  ref={newPromptInputRef}
                  type="text"
                  value={newPromptName}
                  onChange={(e) => setNewPromptName(e.target.value)}
                  onBlur={() => setAddingPrompt(false)}
                  placeholder="New prompt name"
                  className="mb-2 text-xs"
                />
              </form>
            )}
            <SidebarMenu>
              {fiddle?.prompts
                ?.filter((prompt) => !prompt.partial)
                .map((prompt) => (
                  <SidebarMenuItem
                    key={prompt.name}
                    className="flex items-center justify-between"
                  >
                    {editingPrompt === prompt.name ? (
                      <form
                        onSubmit={(e) =>
                          handleRenamePromptConfirm(e, prompt.name)
                        }
                      >
                        <Input
                          ref={renamedPromptInputRef}
                          type="text"
                          value={renamedPromptName}
                          onChange={(e) => setRenamedPromptName(e.target.value)}
                          onBlur={() => setEditingPrompt(null)}
                          className="text-xs"
                        />
                      </form>
                    ) : (
                      <SidebarMenuButton
                        onClick={() => {
                          setSelectedPrompt(prompt.name);
                          // Update URL with prompt name using replaceState
                          if (fiddle?.id) {
                            window.history.replaceState(
                              {},
                              '',
                              `/${fiddle.id}/${encodeURIComponent(prompt.name)}`,
                            );
                          }
                        }}
                        isActive={selectedPrompt === prompt.name}
                        onDoubleClick={() => handleRenamePrompt(prompt)}
                      >
                        {prompt.name}
                      </SidebarMenuButton>
                    )}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 opacity-0 group-hover:opacity-100 absolute right-0 top-1/2 -translate-y-1/2"
                      onClick={() => handleDeletePrompt(prompt)}
                    >
                      <X className="w-3 h-3" />
                    </Button>
                  </SidebarMenuItem>
                ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        <SidebarGroup className="flex-1">
          <SidebarGroupLabel>
            Partials
            <Button
              variant="ghost"
              size="icon"
              className="ml-1"
              onClick={handleAddPartial}
            >
              <Plus className="h-4 w-4" />
            </Button>
          </SidebarGroupLabel>
          <SidebarGroupContent>
            {addingPartial && (
              <form onSubmit={handleAddPartialConfirm}>
                <Input
                  ref={newPartialInputRef}
                  type="text"
                  value={newPartialName}
                  onChange={(e) => setNewPartialName(e.target.value)}
                  onBlur={() => setAddingPartial(false)}
                  placeholder="New partial name"
                  className="mb-2 text-xs"
                />
              </form>
            )}
            <SidebarMenu>
              {fiddle?.prompts
                ?.filter((prompt) => prompt.partial)
                .map((partial) => (
                  <SidebarMenuItem
                    key={partial.name}
                    className="flex items-center justify-between"
                  >
                    {editingPrompt === partial.name ? (
                      <form
                        onSubmit={(e) =>
                          handleRenamePromptConfirm(e, partial.name)
                        }
                      >
                        <Input
                          ref={renamedPromptInputRef}
                          type="text"
                          value={renamedPromptName}
                          onChange={(e) => setRenamedPromptName(e.target.value)}
                          onBlur={() => setEditingPrompt(null)}
                          className="text-xs"
                        />
                      </form>
                    ) : (
                      <SidebarMenuButton
                        onClick={() => {
                          setSelectedPrompt(partial.name);
                          // Update URL with partial name using replaceState
                          if (fiddle?.id) {
                            window.history.replaceState(
                              {},
                              '',
                              `/${fiddle.id}/${encodeURIComponent(partial.name)}`,
                            );
                          }
                        }}
                        isActive={selectedPrompt === partial.name}
                        onDoubleClick={() => handleRenamePrompt(partial)}
                      >
                        {partial.name}
                      </SidebarMenuButton>
                    )}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 opacity-0 group-hover:opacity-100 absolute right-0 top-1/2 -translate-y-1/2"
                      onClick={() => handleDeletePrompt(partial)}
                    >
                      <X className="w-3 h-3" />
                    </Button>
                  </SidebarMenuItem>
                ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        <SidebarFooter>
          <a
            href="https://google.github.io/dotprompt"
            target="_blank  "
            className="p-1 border rounded flex text-xs items-center justify-center"
          >
            powered by <Logo className="color-white h-6 w-24" />
          </a>
        </SidebarFooter>
      </SidebarContent>
    </Sidebar>
  );
}
