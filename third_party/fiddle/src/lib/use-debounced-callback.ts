import { useCallback, useEffect, useRef } from 'react';

export function useDebouncedCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number,
): (...args: Parameters<T>) => void {
  const timeoutRef = useRef<any>(null);

  // useCallback is crucial here. It ensures that the 'debouncedCallback'
  // function's identity remains stable across renders *unless* the callback
  // or delay changes.  This prevents unnecessary re-renders of components
  // that depend on this debounced function.
  const debouncedCallback = useCallback(
    (...args: Parameters<T>) => {
      // Clear any existing timeout.  This is the debouncing part!
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      // Set a new timeout.
      timeoutRef.current = setTimeout(() => {
        callback(...args);
        timeoutRef.current = null; // Clean up after execution
      }, delay);
    },
    [callback, delay], // Dependency array: Recreate the debounced function if callback or delay changes.
  );

  // Cleanup on unmount:  VERY IMPORTANT!
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []); // Empty dependency array: This effect runs only once, on mount.

  return debouncedCallback;
}
