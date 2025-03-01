import { HttpsError } from 'firebase-functions/https';
import { db } from './firebase-admin.js';
import * as logger from 'firebase-functions/logger';

const ANON_USER_QUOTAS = {
  run: 10,
  generate: 5,
};

const GOOGLE_USER_QUOTAS = {
  run: 100,
  generate: 50,
};

export async function consumeQuota(
  quotaType: 'run' | 'generate',
  auth?: { uid: string; token: { provider_id: string } },
) {
  if (!auth)
    throw new HttpsError(
      'unauthenticated',
      'Must be authenticated to run or generate prompts.',
    );
  const month = new Date().toISOString().substring(0, 7);
  const usageSnap = await db.doc(`usage/${auth.uid}/month/${month}`).get();
  const used = usageSnap.get(quotaType) || 0;
  const isAnon = auth.token.provider_id === 'anonymous';
  const quotaPool = isAnon ? ANON_USER_QUOTAS : GOOGLE_USER_QUOTAS;
  if (used >= quotaPool[quotaType])
    throw new HttpsError(
      'resource-exhausted',
      isAnon
        ? 'You have reached the maximum monthly request limit for an anonymous user. Please sign in with Google to receive additional request quota.'
        : 'You have reached the maximum monthly request limit for a user. Please provide your own API key to continue using Dotprompt Fiddle.',
    );
  await usageSnap.ref.set({ [quotaType]: used + 1 }, { merge: true });
  logger.info(
    'User',
    auth.uid,
    'has consumed',
    used + 1,
    'units of',
    quotaType,
    'quota for month',
    month,
    '.',
  );
}
