// Import the functions you need from the SDKs you need
import { initializeApp } from 'firebase/app';
import { getAnalytics } from 'firebase/analytics';
import { getFirestore } from 'firebase/firestore';
import {
  getAuth,
  GoogleAuthProvider,
  onAuthStateChanged,
  signInAnonymously,
  signInWithPopup,
  signOut as signOutRaw,
} from 'firebase/auth';

const firebaseConfig = {
  apiKey: 'AIzaSyDREHaQZ69jNCJ0nRPtpLoM5eg5qu5Qbo4',
  authDomain: 'promptfiddle.firebaseapp.com',
  projectId: 'promptfiddle',
  storageBucket: 'promptfiddle.firebasestorage.app',
  messagingSenderId: '17831120131',
  appId: '1:17831120131:web:dc2cedd8f4eb1724876d36',
  measurementId: 'G-DBGHGB9Q1L',
};

// Initialize Firebase
export const app = initializeApp(firebaseConfig);
export const analytics = getAnalytics(app);
export const auth = getAuth(app);
export const db = getFirestore(app);
export function signIn() {
  return signInWithPopup(auth, new GoogleAuthProvider());
}
export function signOut() {
  return signOutRaw(auth);
}

onAuthStateChanged(auth, (user) => {
  if (!user) return signInAnonymously(auth);
});
