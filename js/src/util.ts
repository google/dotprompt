/**
 * Copyright 2024 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export function removeUndefinedFields(obj: any): any {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }

  if (Array.isArray(obj)) {
    return obj.map((item) => removeUndefinedFields(item));
  }

  const result: { [key: string]: any } = {};
  for (const [key, value] of Object.entries(obj)) {
    if (value !== undefined) {
      result[key] = removeUndefinedFields(value);
    }
  }
  return result;
}
