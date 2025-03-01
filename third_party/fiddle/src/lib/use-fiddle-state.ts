import { useMemo, useCallback, useState, useEffect, useRef } from 'react';
import { useDoc } from './use-doc.ts';
import { useUser } from './use-user.ts';
import { Fiddle } from '../types';
import { useDebouncedCallback } from './use-debounced-callback.ts';
import { doc, serverTimestamp, setDoc } from 'firebase/firestore';
import { generateUniqueId } from '../utils.ts';
import { db } from './firebase.ts';

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
  publish: () => Promise<string | undefined>;
}

const DEFAULT_FIDDLE_PROMPT = {
  name: 'main',
  source: `{{! your prompt goes here }}`,
};

export function useFiddle(id?: string | null): UseFiddleResult {
  // Get current user
  const { data: currentUser } = useUser();

  // If no ID is provided, use empty strings for paths but return no-ops
  const effectiveId = id || '';

  // Load published data - always call hooks in the same order
  const { data: published, isLoading: publishedLoading } =
    useDoc<Fiddle | null>(effectiveId ? `fiddles/${effectiveId}` : '');

  // Load draft if owner - always call hooks in the same order
  const {
    data: savedDraft,
    isLoading: draftLoading,
    update: updateDraftRaw,
  } = useDoc<Fiddle | null>(
    effectiveId ? `fiddles/${effectiveId}/versions/draft` : '',
    () => id || '',
  );

  // Initialize local draft state - used for both local-only fiddles and Firebase drafts
  const [draft, setLocalDraft] = useState<Fiddle | null>(() => {
    // If no ID is provided, create a new in-memory fiddle with default prompt
    if (!id) {
      return {
        name: 'Untitled Prompt',
        prompts: [DEFAULT_FIDDLE_PROMPT],
      };
    }
    return null;
  });

  const isLocalUpdate = useRef(false);

  useEffect(() => {
    // Skip this effect for local-only fiddles (no ID)
    if (!id) return;

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
  }, [savedDraft, id]);

  // Determine ownership - for published fiddles, owner must match
  // For drafts, anyone with the ID can edit
  const isOwner = useMemo(() => {
    // For published fiddles, require authentication and ownership
    if (published) {
      return currentUser?.uid === published.owner;
    }

    // For drafts, anyone can edit if they have the ID
    return true;
  }, [currentUser, published]);

  const isLoading = useMemo(() => {
    return publishedLoading || draftLoading;
  }, [publishedLoading, draftLoading]);

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

  const updateDraft = useCallback(
    async (fiddle: Fiddle) => {
      console.log('updateDraft called', {
        fiddle,
        id,
        isLocalUpdate: isLocalUpdate.current,
      });

      // For local-only fiddles (no ID), just update the local state
      if (!id) {
        // Use functional update to ensure state is updated correctly
        setLocalDraft((prevDraft) => {
          return fiddle;
        });
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

  // Publish draft to published version
  const publish = useCallback(async () => {
    // Require authentication for publishing
    if (!currentUser || !draft) return;

    // Generate ID if needed
    const effectiveId = id || generateUniqueId(10);

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
      window.history.pushState({}, '', `/${effectiveId}`);
    }

    // Return the ID so the app component can update its state
    return effectiveId;
  }, [id, currentUser, draft]);

  useEffect(() => {
    if (id && !isLoading && !published && !savedDraft && !draft) {
      setLocalDraft({
        id,
        name: 'Prompt ' + id,
        prompts: [DEFAULT_FIDDLE_PROMPT],
      });
    }
  }, [id, published, savedDraft, draft, isLoading]);

  return {
    published,
    isOwner,
    draft,
    isLoading,
    hasChanges,
    draftSaved,
    updateDraft,
    publish,
  };
}
