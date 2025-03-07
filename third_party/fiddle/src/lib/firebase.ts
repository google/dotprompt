// Import the functions you need from the SDKs you need
import { FirebaseError, initializeApp } from 'firebase/app';
import {
  Analytics,
  getAnalytics,
  logEvent as analyticsLogEvent,
  setUserId,
} from 'firebase/analytics';
import { getFirestore } from 'firebase/firestore';
import {
  getAuth,
  GoogleAuthProvider,
  onAuthStateChanged,
  signInAnonymously,
  signInWithPopup,
  linkWithPopup,
  signOut as signOutRaw,
  signInWithCredential,
  UserCredential,
  updateProfile,
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
export const auth = getAuth(app);
export const db = getFirestore(app);

export async function signIn() {
  const provider = new GoogleAuthProvider();
  const user = auth.currentUser;

  if (user?.isAnonymous) {
    let credential: UserCredential | undefined;
    let linkConflict = false;
    try {
      credential = await linkWithPopup(user, provider);
    } catch (e) {
      if (e instanceof FirebaseError) {
        linkConflict = true;
        const googleCredential = GoogleAuthProvider.credentialFromError(e);
        if (googleCredential) {
          credential = await signInWithCredential(auth, googleCredential);
        }
      }
    }

    logEvent('sign_in', { conflict: linkConflict });

    if (credential) {
      const googInfo = credential.user.providerData.find(
        (d) => d.providerId === 'google.com',
      );
      await updateProfile(credential.user, {
        displayName: googInfo?.displayName,
        photoURL: googInfo?.photoURL,
      });
      await auth.currentUser?.reload();
    }
  }

  // Otherwise do a normal sign in
  return signInWithPopup(auth, provider);
}
export function signOut() {
  logEvent('sign_out');
  return signOutRaw(auth);
}

let analytics: Analytics;
if (typeof window !== 'undefined') {
  analytics = getAnalytics(app);
}

onAuthStateChanged(auth, (user) => {
  if (!user) return signInAnonymously(auth);
  setUserId(analytics, user.uid);
});
export function logEvent(name: string, props?: Record<string, any>) {
  if (!analytics) analytics = getAnalytics(app);
  analyticsLogEvent(analytics, name, props);
}
export function setCurrentScreen(name: string) {
  if (!analytics) analytics = getAnalytics(app);
}
