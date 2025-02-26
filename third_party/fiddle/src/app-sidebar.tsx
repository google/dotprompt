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
} from "@/components/ui/sidebar.tsx";
import { Button } from "@/components/ui/button.tsx";
import { Fiddle, Prompt } from "./types";
import { useState, useRef, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { ChevronsUpDown, Plus, X } from "lucide-react";
import Logo from "@/components/logo.tsx";
import Dot from "./components/dot.tsx";

export default function AppSidebar({
  fiddle,
  setFiddle,
  setSelectedPrompt,
  selectedPrompt,
}: {
  fiddle: Fiddle;
  setFiddle: (fiddle: Fiddle) => void;
  selectedPrompt: string | null;
  setSelectedPrompt: (prompt: string) => void;
}) {
  const [addingPrompt, setAddingPrompt] = useState(false);
  const [newPromptName, setNewPromptName] = useState("");
  const newPromptInputRef = useRef<HTMLInputElement>(null);
  const [editingPrompt, setEditingPrompt] = useState<string | null>(null);
  const [renamedPromptName, setRenamedPromptName] = useState("");
  const renamedPromptInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (addingPrompt && newPromptInputRef.current) {
      newPromptInputRef.current.focus();
    }
  }, [addingPrompt]);

  useEffect(() => {
    if (editingPrompt && renamedPromptInputRef.current) {
      renamedPromptInputRef.current.focus();
    }
  }, [editingPrompt]);

  const handleAddPrompt = () => {
    setAddingPrompt(true);
  };

  const handleAddPromptConfirm = (e: React.FormEvent) => {
    e.preventDefault();
    if (newPromptName.trim()) {
      const newPrompt: Prompt = { name: newPromptName.trim(), source: "{{! your prompt here }}" };
      const updatedFiddle = { ...fiddle, prompts: [...fiddle.prompts, newPrompt] };
      setFiddle(updatedFiddle);
      setSelectedPrompt(newPrompt.name);
      setNewPromptName("");
      setAddingPrompt(false);
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
        prompts: fiddle.prompts.map((p) =>
          p.name === oldName ? { ...p, name: renamedPromptName.trim() } : p
        ),
      };
      setFiddle(updatedFiddle);
      setSelectedPrompt(renamedPromptName.trim());
      setEditingPrompt(null);
      setRenamedPromptName("");
    }
  };

  const handleDeletePrompt = (promptToDelete: Prompt) => {
    if (window.confirm(`Delete prompt "${promptToDelete.name}"?`)) {
      setFiddle({
        ...fiddle,
        prompts: fiddle.prompts.filter((p) => p.name !== promptToDelete.name),
      });
    }
  };

  const [editingFiddleName, setEditingFiddleName] = useState(false);
  const [newFiddleName, setNewFiddleName] = useState(fiddle.name);
  const newFiddleNameInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editingFiddleName && newFiddleNameInputRef.current) {
      newFiddleNameInputRef.current.focus();
      newFiddleNameInputRef.current.select();
    }
  }, [editingFiddleName]);

  const handleRenameFiddle = () => {
    setEditingFiddleName(true);
  };

  const handleRenameFiddleConfirm = (e: React.FormEvent) => {
    e.preventDefault();
    if (newFiddleName.trim()) {
      setFiddle({ ...fiddle, name: newFiddleName.trim() });
      setEditingFiddleName(false);
    }
  };

  return (
    <Sidebar variant="sidebar">
      <SidebarHeader onDoubleClick={handleRenameFiddle}>
        <div className="border rounded-lg p-3 flex items-center">
          <Dot className="w-6 h-6 mr-2" />
          <div className="flex-1">
            <h1 className="font-bold text-sm">Prompt Fiddle</h1>
            <h2 className="text-xs">{fiddle.name}</h2>
          </div>
          <ChevronsUpDown className="w-4 h-4" />
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>
            Prompts
            <Button variant="ghost" size="icon" className="ml-1" onClick={handleAddPrompt}>
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
              {fiddle.prompts.map((prompt) => (
                <SidebarMenuItem key={prompt.name} className="flex items-center justify-between">
                  {editingPrompt === prompt.name ? (
                    <form onSubmit={(e) => handleRenamePromptConfirm(e, prompt.name)}>
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
                      onClick={() => setSelectedPrompt(prompt.name)}
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
            <Button variant="ghost" size="icon" className="ml-1">
              <Plus className="h-4 w-4" />
            </Button>
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>{/* TODO: Add partials here */}</SidebarMenu>
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
