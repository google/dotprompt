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
import { useState, useRef, useEffect, useCallback } from 'react';
import { Input } from '@/components/ui/input';
import {
  ChevronsUpDown,
  Plus,
  X,
  LogOut,
  FilePlus,
  FolderOpen,
  Bug,
} from 'lucide-react';
import Logo from '@/components/logo.tsx';
import { useUser } from '@/lib/use-user';
import { signIn, signOut } from '@/lib/firebase';
import { myFiddles } from '@/lib/data';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

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
  const { data: user } = useUser();
  const [showMyFiddles, setShowMyFiddles] = useState(false);
  const [userFiddles, setUserFiddles] = useState<Fiddle[]>([]);
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

  const handleNewFiddle = useCallback(() => {
    if (hasChanges) {
      if (
        !window.confirm('You have unsaved changes. Create a new fiddle anyway?')
      ) {
        return;
      }
    }
    window.location.href = '/';
  }, [hasChanges]);

  const handleMyFiddles = useCallback(async () => {
    const fiddles = await myFiddles();
    setUserFiddles(fiddles);
    setShowMyFiddles(true);
  }, []);

  const handleSelectFiddle = useCallback(
    (fiddle: Fiddle) => {
      if (hasChanges) {
        if (
          !window.confirm('You have unsaved changes. Open this fiddle anyway?')
        ) {
          return;
        }
      }
      window.location.href = `/${fiddle.id}`;
      setShowMyFiddles(false);
    },
    [hasChanges],
  );

  return (
    <Sidebar variant="sidebar">
      <SidebarHeader>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <div className="border rounded-lg p-3 flex items-center cursor-pointer">
              <img src="/icon.png" className="size-6 mr-2" />
              <div className="flex-1">
                <h1 className="font-bold text-sm">Dotprompt Fiddle</h1>
              </div>
              <ChevronsUpDown className="size-4" />
            </div>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-56">
            <>
              {user && !user.isAnonymous && (
                <>
                  <div className="flex items-center p-2">
                    {user.photoURL ? (
                      <img
                        src={user.photoURL}
                        alt={user.displayName || 'User'}
                        className="w-8 h-8 rounded-full mr-2"
                      />
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-gray-200 mr-2 flex items-center justify-center">
                        {user.displayName?.charAt(0) || 'U'}
                      </div>
                    )}
                    <div className="flex-1 overflow-hidden">
                      <p className="text-sm font-medium truncate">
                        {user.displayName || user.email || 'User'}
                      </p>
                      {user.email && (
                        <p className="text-xs text-muted-foreground truncate">
                          {user.email}
                        </p>
                      )}
                    </div>
                  </div>
                  <DropdownMenuSeparator />
                </>
              )}
              <DropdownMenuItem
                onClick={handleNewFiddle}
                className="cursor-pointer"
              >
                <FilePlus className="mr-2 h-4 w-4" />
                <span>New Fiddle</span>
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={handleMyFiddles}
                className="cursor-pointer"
              >
                <FolderOpen className="mr-2 h-4 w-4" />
                <span>My Fiddles</span>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              {user && !user.isAnonymous ? (
                <DropdownMenuItem
                  onClick={() => signOut()}
                  className="cursor-pointer"
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Sign out</span>
                </DropdownMenuItem>
              ) : (
                <DropdownMenuItem
                  onClick={() => signIn()}
                  className="cursor-pointer"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    height="16"
                    viewBox="0 0 24 24"
                    width="16"
                    className="mr-2"
                  >
                    <path
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      fill="#4285F4"
                    />
                    <path
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      fill="#34A853"
                    />
                    <path
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                      fill="#FBBC05"
                    />
                    <path
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                      fill="#EA4335"
                    />
                    <path d="M1 1h22v22H1z" fill="none" />
                  </svg>
                  <span>Sign in with Google</span>
                </DropdownMenuItem>
              )}
            </>
          </DropdownMenuContent>
        </DropdownMenu>
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
          <div className="space-y-2">
            <a
              href="https://github.com/google/dotprompt/labels/fiddle"
              target="_blank"
              className="p-2 border rounded flex text-xs items-center justify-center gap-2 hover:bg-accent"
            >
              <Bug className="h-4 w-4" />
              Bugs / Feature Requests
            </a>
            <a
              href="https://google.github.io/dotprompt/getting-started/"
              target="_blank"
              className="p-1 border rounded flex text-xs items-center justify-center"
            >
              powered by <Logo className="color-white h-6 w-24" />
            </a>
          </div>
        </SidebarFooter>
      </SidebarContent>
      <Dialog open={showMyFiddles} onOpenChange={setShowMyFiddles}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>My Fiddles</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            {userFiddles.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center">
                No fiddles found
              </p>
            ) : (
              <div className="space-y-2">
                {userFiddles.map((fiddle) => (
                  <div
                    key={fiddle.id}
                    onClick={() => handleSelectFiddle(fiddle)}
                    className="p-3 rounded-lg border hover:bg-accent cursor-pointer"
                  >
                    <h3 className="font-medium">
                      {fiddle.name || 'Untitled Fiddle'}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      Last updated:{' '}
                      {fiddle.updateTime
                        ? new Date(fiddle.updateTime).toLocaleDateString()
                        : 'Never'}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </Sidebar>
  );
}
