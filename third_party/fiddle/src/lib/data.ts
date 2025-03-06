import {
  collection,
  getDocs,
  orderBy,
  query,
  Timestamp,
  where,
} from 'firebase/firestore';
import { auth, db } from './firebase.ts';
import { Fiddle } from '@/types.js';

export async function myFiddles(): Promise<Fiddle[]> {
  if (!auth.currentUser) return [];
  const myFiddlesQuery = query(
    collection(db, 'fiddles'),
    where('owner', '==', auth.currentUser?.uid),
    orderBy('updateTime', 'desc'),
  );
  const fiddlesSnap = await getDocs(myFiddlesQuery);
  return fiddlesSnap.docs.map((snap) => {
    const data: any = { ...snap.data(), id: snap.id };
    for (const key in data) {
      if (data[key] instanceof Timestamp) {
        data[key] = data[key].toDate().toISOString();
      }
    }
    return data as Fiddle;
  });
}
