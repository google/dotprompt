import { doc, DocumentSnapshot, onSnapshot, setDoc } from 'firebase/firestore';
import { db } from './firebase.ts';
import { useEffect, useState } from 'react';

export function useDoc<T = any>(
  path?: string,
  idFunc?: (doc: DocumentSnapshot) => string,
) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  useEffect(() => {
    if (!path) return;
    const unsub = onSnapshot(doc(db, path), (snap) => {
      if (!snap.exists()) {
        setData(null);
      } else {
        const data: any = snap.data();
        data.id = idFunc ? idFunc(snap) : snap.id;
        setData(data as T | null);
      }
      setIsLoading(false);
    });
    return unsub;
  }, [path]);

  const update = (newValue: Partial<T> & Record<string, any>) => {
    if (!path) return;
    return setDoc(doc(db, path), newValue, { merge: true });
  };

  return { data, isLoading, update };
}
