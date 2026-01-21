/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import { describe, expect, it } from 'vitest';
import {
  history,
  ifEquals,
  json,
  media,
  role,
  section,
  unlessEquals,
} from './helpers';

describe('helpers', () => {
  describe('json', () => {
    it('should serialize an object to JSON', () => {
      const result = json({ foo: 'bar' }, { hash: {} });
      expect(result.toString()).toBe('{"foo":"bar"}');
    });

    it('should serialize with indent when specified', () => {
      const result = json({ foo: 'bar' }, { hash: { indent: 2 } });
      expect(result.toString()).toBe('{\n  "foo": "bar"\n}');
    });

    it('should serialize with 4-space indent when specified', () => {
      const result = json({ test: true }, { hash: { indent: 4 } });
      expect(result.toString()).toBe('{\n    "test": true\n}');
    });

    it('should serialize nested objects', () => {
      const result = json({ outer: { inner: { value: 42 } } }, { hash: {} });
      expect(result.toString()).toBe('{"outer":{"inner":{"value":42}}}');
    });

    it('should serialize arrays', () => {
      const result = json([1, 2, 3], { hash: {} });
      expect(result.toString()).toBe('[1,2,3]');
    });

    it('should serialize empty objects', () => {
      const result = json({}, { hash: {} });
      expect(result.toString()).toBe('{}');
    });

    it('should serialize empty arrays', () => {
      const result = json([], { hash: {} });
      expect(result.toString()).toBe('[]');
    });

    it('should throw on circular references (fail-fast behavior)', () => {
      const circular: Record<string, unknown> = { foo: 'bar' };
      circular.self = circular;

      expect(() => json(circular, { hash: {} })).toThrow(TypeError);
    });

    it('should throw on BigInt values (fail-fast behavior)', () => {
      // BigInt is not serializable to JSON
      expect(() => json({ value: BigInt(123) }, { hash: {} })).toThrow(
        TypeError
      );
    });
  });

  describe('role', () => {
    it('should return a role marker for system', () => {
      const result = role('system');
      expect(result.toString()).toBe('<<<dotprompt:role:system>>>');
    });

    it('should return a role marker for user', () => {
      const result = role('user');
      expect(result.toString()).toBe('<<<dotprompt:role:user>>>');
    });

    it('should return a role marker for model', () => {
      const result = role('model');
      expect(result.toString()).toBe('<<<dotprompt:role:model>>>');
    });
  });

  describe('history', () => {
    it('should return a history marker', () => {
      const result = history();
      expect(result.toString()).toBe('<<<dotprompt:history>>>');
    });
  });

  describe('section', () => {
    it('should return a section marker', () => {
      const result = section('examples');
      expect(result.toString()).toBe('<<<dotprompt:section examples>>>');
    });
  });

  describe('media', () => {
    it('should return a media marker with url only', () => {
      const result = media({
        hash: { url: 'https://example.com/image.png' },
      } as Handlebars.HelperOptions);
      expect(result.toString()).toBe(
        '<<<dotprompt:media:url https://example.com/image.png>>>'
      );
    });

    it('should return a media marker with url and contentType', () => {
      const result = media({
        hash: {
          url: 'https://example.com/image.png',
          contentType: 'image/png',
        },
      } as Handlebars.HelperOptions);
      expect(result.toString()).toBe(
        '<<<dotprompt:media:url https://example.com/image.png image/png>>>'
      );
    });
  });

  describe('ifEquals', () => {
    const mockContext = {};
    const createOptions = (fn: () => string, inverse: () => string) =>
      ({
        fn: () => fn(),
        inverse: () => inverse(),
      }) as unknown as Handlebars.HelperOptions;

    it('should return fn result when values are equal', () => {
      const options = createOptions(
        () => 'equal',
        () => 'not equal'
      );
      const result = ifEquals.call(mockContext, 5, 5, options);
      expect(result).toBe('equal');
    });

    it('should return inverse result when values are not equal', () => {
      const options = createOptions(
        () => 'equal',
        () => 'not equal'
      );
      const result = ifEquals.call(mockContext, 5, 6, options);
      expect(result).toBe('not equal');
    });

    it('should use strict equality (different types are not equal)', () => {
      const options = createOptions(
        () => 'equal',
        () => 'not equal'
      );
      // 5 !== "5" in strict equality
      const result = ifEquals.call(mockContext, 5, '5', options);
      expect(result).toBe('not equal');
    });

    it('should compare boolean values correctly', () => {
      const options = createOptions(
        () => 'equal',
        () => 'not equal'
      );
      expect(ifEquals.call(mockContext, true, true, options)).toBe('equal');
      expect(ifEquals.call(mockContext, false, false, options)).toBe('equal');
      expect(ifEquals.call(mockContext, true, false, options)).toBe(
        'not equal'
      );
    });

    it('should compare null values correctly', () => {
      const options = createOptions(
        () => 'equal',
        () => 'not equal'
      );
      expect(ifEquals.call(mockContext, null, null, options)).toBe('equal');
      expect(ifEquals.call(mockContext, null, 0, options)).toBe('not equal');
      expect(ifEquals.call(mockContext, null, undefined, options)).toBe(
        'not equal'
      );
    });
  });

  describe('unlessEquals', () => {
    const mockContext = {};
    const createOptions = (fn: () => string, inverse: () => string) =>
      ({
        fn: () => fn(),
        inverse: () => inverse(),
      }) as unknown as Handlebars.HelperOptions;

    it('should return fn result when values are not equal', () => {
      const options = createOptions(
        () => 'not equal',
        () => 'equal'
      );
      const result = unlessEquals.call(mockContext, 5, 6, options);
      expect(result).toBe('not equal');
    });

    it('should return inverse result when values are equal', () => {
      const options = createOptions(
        () => 'not equal',
        () => 'equal'
      );
      const result = unlessEquals.call(mockContext, 5, 5, options);
      expect(result).toBe('equal');
    });

    it('should use strict inequality (different types are not equal)', () => {
      const options = createOptions(
        () => 'not equal',
        () => 'equal'
      );
      // 5 !== "5" in strict comparison
      const result = unlessEquals.call(mockContext, 5, '5', options);
      expect(result).toBe('not equal');
    });

    it('should compare boolean values correctly', () => {
      const options = createOptions(
        () => 'not equal',
        () => 'equal'
      );
      expect(unlessEquals.call(mockContext, true, false, options)).toBe(
        'not equal'
      );
      expect(unlessEquals.call(mockContext, true, true, options)).toBe('equal');
    });

    it('should compare null values correctly', () => {
      const options = createOptions(
        () => 'not equal',
        () => 'equal'
      );
      expect(unlessEquals.call(mockContext, null, null, options)).toBe('equal');
      expect(unlessEquals.call(mockContext, null, 0, options)).toBe(
        'not equal'
      );
    });
  });
});
