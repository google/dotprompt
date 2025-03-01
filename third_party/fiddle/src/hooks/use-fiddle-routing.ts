import { useState, useEffect, useRef } from 'react';

export function useFiddleRouting() {
  const [fiddleId, setFiddleId] = useState<string | null>(null);
  const [urlPromptName, setUrlPromptName] = useState<string | null>(null);
  const idInitializedRef = useRef(false);

  // Effect to handle routing - only run once
  useEffect(() => {
    // Skip if we've already initialized the ID
    if (idInitializedRef.current) {
      return;
    }

    idInitializedRef.current = true;

    // Extract ID and prompt name from URL if they exist
    const path = window.location.pathname;
    if (path.length <= 1) return; // No ID in URL

    // Split the path by slashes and remove empty segments
    const segments = path.split('/').filter(Boolean);

    if (segments.length >= 1) {
      // First segment is the fiddle ID
      setFiddleId(segments[0]);

      // Second segment (if exists) is the prompt name
      if (segments.length >= 2) {
        setUrlPromptName(decodeURIComponent(segments[1]));
      }
    }
    // Otherwise, leave fiddleId as null for in-memory mode
  }, []);

  return { fiddleId, setFiddleId, urlPromptName };
}
