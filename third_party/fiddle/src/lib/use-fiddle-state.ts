import { useMemo, useCallback, useState, useEffect, useRef } from 'react';
import { useDoc } from './use-doc.ts';
import { useUser } from './use-user.ts';
import { Fiddle } from '../types';
import { useDebouncedCallback } from './use-debounced-callback.ts';
import { doc, serverTimestamp, setDoc } from 'firebase/firestore';
import { generateUniqueId } from '../utils.ts';
import { db, logEvent } from './firebase.ts';

/**
 * Compares two fiddles for equality based on their content
 * Only compares name and prompts fields
 */
function fiddleEq(a: Fiddle | null, b: Fiddle | null): boolean {
  // If both are null or undefined, they're equal
  if (!a && !b) return true;
  // If only one is null or undefined, they're not equal
  if (!a || !b) return false;

  // Compare names
  if (a.name !== b.name) return false;

  // Compare prompts array length
  if (a.prompts.length !== b.prompts.length) return false;

  // Compare each prompt in the array
  for (let i = 0; i < a.prompts.length; i++) {
    const promptA = a.prompts[i];
    const promptB = b.prompts[i];

    if (
      promptA.name !== promptB.name ||
      promptA.source !== promptB.source ||
      promptA.partial !== promptB.partial
    ) {
      return false;
    }
  }

  // If we got here, the fiddles are equal
  return true;
}

interface UseFiddleResult {
  draft: Fiddle | null;
  published: Fiddle | null;
  isLoading: boolean;
  isOwner: boolean;
  hasChanges: boolean;
  draftSaved: boolean;
  updateDraft: (updatedFiddle: Fiddle) => void;
  updateStoredDraft: (fiddle: Fiddle) => boolean;
  publish: () => Promise<string | undefined>;
}

const DEFAULT_FIDDLE_PROMPT = {
  name: 'main',
  source: `{{! your prompt goes here }}`,
};

const DRAFT_STORAGE_KEY = 'fiddle_draft';
function loadLocalDraft() {
  try {
    const storedDraft = localStorage.getItem(DRAFT_STORAGE_KEY);
    if (storedDraft) {
      return JSON.parse(storedDraft);
    }
  } catch (error) {
    console.error('Error reading draft from localStorage:', error);
  }

  // If no stored draft or error, create a new default fiddle
  return {
    name: 'Untitled Prompt',
    prompts: [DEFAULT_FIDDLE_PROMPT],
  };
}

export function useFiddle(
  id?: string | null,
  promptName?: string | null,
): UseFiddleResult {
  // Get current user
  const { data: currentUser } = useUser();

  // Load published data - always call hooks in the same order
  const { data: published, isLoading: publishedLoading } =
    useDoc<Fiddle | null>(id ? `fiddles/${id}` : '');

  // Load draft if owner - always call hooks in the same order
  const {
    data: savedDraft,
    isLoading: draftLoading,
    update: updateDraftRaw,
  } = useDoc<Fiddle | null>(
    id ? `fiddles/${id}/versions/draft` : '',
    () => id || '',
  );

  // Initialize local draft state - used for both local-only fiddles and Firebase drafts
  const [draft, setLocalDraft] = useState<Fiddle | null>(null);

  const isLocalUpdate = useRef(false);

  // Track previous ID to detect changes
  const prevIdRef = useRef<string | null | undefined>(id);

  useEffect(() => {
    // Only update from savedDraft if it exists and it's not a local update
    if (savedDraft && !isLocalUpdate.current) {
      setLocalDraft(savedDraft);
    } else if (!savedDraft && !isLocalUpdate.current) {
      // If there's no savedDraft and no local update, keep the existing draft
      // This preserves the bootstrapped draft while Firebase confirms there's no saved draft
      return;
    } else if (isLocalUpdate.current) {
      // Only reset the flag if it was a local update
      isLocalUpdate.current = false;
    }

    // Update the previous ID reference
    prevIdRef.current = id;
  }, [savedDraft, id]);

  useEffect(() => {
    if (!id) {
      console.log('RESETTING LOCAL DRAFT TO:', loadLocalDraft());
      setLocalDraft(loadLocalDraft());
    }
  }, [id]);

  const isLoading = publishedLoading || draftLoading;
  const isOwner =
    !isLoading && (!published || published.owner === currentUser?.uid);

  // Compare draft with published version to check for unpublished changes
  const { hasChanges, draftSaved } = useMemo(() => {
    // Check if draft is saved (local draft equals saved draft)
    const isDraftSaved = fiddleEq(draft, savedDraft);

    // If there's no published version, any draft has changes
    if (!published) {
      return { hasChanges: !!draft, draftSaved: isDraftSaved };
    }

    // If there's no draft, there can't be changes
    if (!draft) {
      return { hasChanges: false, draftSaved: true };
    }

    // Compare published and draft using the equality function
    const hasUnpublishedChanges = !fiddleEq(published, draft);

    return {
      hasChanges: hasUnpublishedChanges,
      draftSaved: isDraftSaved,
    };
  }, [published, draft, savedDraft]);

  const saveDraft = useDebouncedCallback(updateDraftRaw, 700);

  // Create a debounced function for saving to localStorage
  const saveToLocalStorage = useDebouncedCallback((draftToSave: Fiddle) => {
    try {
      localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(draftToSave));
    } catch (error) {
      console.error('Error saving draft to localStorage:', error);
    }
  }, 700); // Use the same debounce time as for Firestore

  // Effect to save draft to localStorage when it changes (only for local-only fiddles)
  useEffect(() => {
    if (!id && draft) {
      saveToLocalStorage(draft);
    }
  }, [id, draft, saveToLocalStorage]);

  const updateDraft = useCallback(
    async (fiddle: Fiddle) => {
      console.log('updateDraft called', {
        fiddle,
        id,
        isLocalUpdate: isLocalUpdate.current,
      });

      // For local-only fiddles (no ID), update the local state and localStorage
      if (!id) {
        setLocalDraft(fiddle);
        return;
      }

      // For fiddles with IDs, update both local state and Firebase
      // Ensure all required fields are present
      const completeData = {
        ...fiddle,
        id: id || fiddle.id, // Ensure id is preserved
        name: fiddle.name || 'Prompt ' + id, // Ensure name is preserved
      };

      // Remove owner field for drafts - drafts don't need an owner
      if (completeData.owner) {
        delete completeData.owner;
      }

      setLocalDraft(completeData);
      // Set the flag before saving to Firestore
      isLocalUpdate.current = true;
      saveDraft(completeData);
    },
    [id],
  );

  // Function to update the stored draft in localStorage
  const updateStoredDraft = useCallback((fiddle: Fiddle) => {
    try {
      // Create a copy of the fiddle without the ID
      const storedFiddle = {
        ...fiddle,
        id: undefined, // Remove the ID
      };

      // Save to localStorage
      localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(storedFiddle));
      return true;
    } catch (error) {
      console.error('Error saving fiddle to localStorage:', error);
      return false;
    }
  }, []);

  // Publish draft to published version
  const publish = useCallback(async () => {
    // Require authentication for publishing
    if (!currentUser || !draft) return;

    // Generate ID if needed
    const effectiveId = id || generateUniqueId(10);

    logEvent('publish_fiddle', { id: effectiveId });
    // Copy draft to published and set owner
    await setDoc(
      doc(db, `fiddles/${effectiveId}`),
      {
        ...draft,
        owner: currentUser.uid,
        publishTime: serverTimestamp(),
        id: effectiveId,
      },
      { merge: true },
    );
    await setDoc(
      doc(db, `fiddles/${effectiveId}/versions/draft`),
      {
        ...draft,
        updateTime: serverTimestamp(),
      },
      { merge: true },
    );
    setLocalDraft({ ...draft });

    // If this is a new fiddle (no ID), update the URL
    if (!id) {
      // Clear localStorage since we're publishing a previously local-only fiddle
      localStorage.removeItem(DRAFT_STORAGE_KEY);

      // If there are prompts, include the first one in the URL
      if (draft.prompts && draft.prompts.length > 0) {
        const firstPromptName = draft.prompts[0].name;
        window.history.pushState(
          {},
          '',
          `/${effectiveId}/${encodeURIComponent(firstPromptName)}`,
        );
      } else {
        window.history.pushState({}, '', `/${effectiveId}`);
      }
    }

    // Return the ID so the app component can update its state
    return effectiveId;
  }, [id, currentUser, draft]);

  // Effect to initialize draft when no data is available
  useEffect(() => {
    if (id && !isLoading && !published && !savedDraft && !draft) {
      setLocalDraft({
        id,
        name: 'Prompt ' + id,
        prompts: [DEFAULT_FIDDLE_PROMPT],
      });
    }
  }, [id, published, savedDraft, draft, isLoading]);

  // Effect to handle prompt selection from URL
  useEffect(() => {
    // Skip if no fiddle data is available yet
    if (!draft || isLoading) return;

    // If promptName is provided in the URL, select it
    if (promptName) {
      // Find the prompt with the matching name
      const promptExists = draft.prompts.some((p) => p.name === promptName);
      if (promptExists) {
        // The App component will handle setting the selected prompt
        return;
      }
    }

    // If no promptName is provided or it doesn't exist, we don't need to do anything
    // The App component will default to the first prompt
  }, [draft, promptName, isLoading]);

  return {
    published,
    isOwner,
    draft: isOwner ? draft : null,
    isLoading,
    hasChanges: isOwner ? hasChanges : false,
    draftSaved: isOwner ? draftSaved : true,
    updateDraft,
    updateStoredDraft,
    publish,
  };
}
