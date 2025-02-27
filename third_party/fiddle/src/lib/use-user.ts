import { onAuthStateChanged, type User } from 'firebase/auth';
import { auth } from './firebase.ts';
import { useEffect, useState } from 'react';

export function useUser() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const dispose = onAuthStateChanged(auth, (user) => {
      setIsLoading(false);
      setUser(user || null);
    });
    return dispose;
  }, []);

  return { data: user, isLoading };
}
