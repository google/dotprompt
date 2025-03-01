import { initializeApp } from 'firebase-admin/app';
import { getFirestore } from 'firebase-admin/firestore';

export const admin = initializeApp();
export const db = getFirestore(admin);
