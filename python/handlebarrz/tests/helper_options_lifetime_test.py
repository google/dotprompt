# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

import asyncio
import gc
import importlib
import threading
import unittest
from collections.abc import Callable
from typing import Any

from handlebarrz._native import HandlebarrzHelperOptions, HandlebarrzTemplate

from handlebarrz import HelperOptions, Template

EXPIRED_ERROR = 'helper options are only available while the helper callback is running'
REENTRANT_ERROR = 'helper options cannot be accessed while one of its branches is rendering'
THREAD_ERROR = 'helper options can only be accessed from the helper callback thread'


class HelperOptionsLifetimeTest(unittest.TestCase):
    def assert_expired(self, options: HelperOptions) -> None:
        accessors: tuple[Callable[[], object], ...] = (
            options.context,
            lambda: options.hash_value('value'),
            options.fn,
            options.inverse,
        )
        for accessor in accessors:
            with self.subTest(accessor=accessor), self.assertRaisesRegex(RuntimeError, f'^{EXPIRED_ERROR}$'):
                accessor()

    def test_helper_options_cannot_be_constructed_by_callers(self) -> None:
        public_helper_options = vars(importlib.import_module('handlebarrz'))['HelperOptions']
        with self.assertRaises(TypeError):
            public_helper_options()
        with self.assertRaises(TypeError):
            HandlebarrzHelperOptions()

    def test_active_options_expose_context_hash_and_both_branches_repeatedly(self) -> None:
        template = Template()
        seen: list[HelperOptions] = []

        def inspect(params: list[Any], options: HelperOptions) -> str:
            seen.append(options)
            self.assertEqual(options.context(), {'name': 'Ada'})
            self.assertEqual(options.hash_value('present'), 'yes')
            self.assertEqual(options.hash_value('missing'), '')
            self.assertIsNone(options.hash_value('null_value'))
            self.assertEqual(options.fn(), 'main')
            self.assertEqual(options.fn(), 'main')
            self.assertEqual(options.inverse(), 'other')
            self.assertEqual(options.inverse(), 'other')
            return 'done'

        template.register_helper('inspect', inspect)

        result = template.render_template(
            '{{#inspect present="yes" null_value=null}}main{{else}}other{{/inspect}}',
            {'name': 'Ada'},
        )

        self.assertEqual(result, 'done')
        self.assert_expired(seen[0])

    def test_missing_block_branches_return_empty_while_active(self) -> None:
        template = Template()
        results: list[tuple[str, str]] = []
        seen: list[HelperOptions] = []

        def inspect(params: list[Any], options: HelperOptions) -> str:
            seen.append(options)
            results.append((options.fn(), options.inverse()))
            return 'ok'

        template.register_helper('inspect', inspect)

        self.assertEqual(template.render_template('{{inspect}}', {}), 'ok')
        self.assertEqual(results, [('', '')])
        self.assert_expired(seen[0])

    def test_plain_helper_options_expire_after_direct_render(self) -> None:
        template = Template()
        seen: list[HelperOptions] = []
        template.register_helper('retain', lambda params, options: seen.append(options) or 'ok')

        self.assertEqual(template.render_template('{{retain}}', {}), 'ok')

        self.assert_expired(seen[0])

    def test_block_helper_options_expire_after_registered_template_render(self) -> None:
        template = Template()
        seen: list[HelperOptions] = []

        def retain(params: list[Any], options: HelperOptions) -> str:
            seen.append(options)
            return options.fn()

        template.register_helper('retain', retain)
        template.register_template('compiled', '{{#retain}}body{{/retain}}')

        self.assertEqual(template.render('compiled', {}), 'body')

        self.assert_expired(seen[0])

    def test_inverse_helper_options_expire_after_render(self) -> None:
        template = Template()
        seen: list[HelperOptions] = []

        def retain(params: list[Any], options: HelperOptions) -> str:
            seen.append(options)
            return options.inverse()

        template.register_helper('retain', retain)

        self.assertEqual(template.render_template('{{#retain}}main{{else}}inverse{{/retain}}', {}), 'inverse')
        self.assert_expired(seen[0])

    def test_raw_native_options_expire_after_native_callback(self) -> None:
        template = HandlebarrzTemplate()
        seen: list[HandlebarrzHelperOptions] = []

        def retain(params_json: str, options: HandlebarrzHelperOptions) -> str:
            seen.append(options)
            self.assertEqual(options.context_json(), '{}')
            return 'raw'

        template.register_helper('retain', retain)

        self.assertEqual(template.render_template('{{retain}}', '{}', '{}'), 'raw')
        with self.assertRaisesRegex(RuntimeError, f'^{EXPIRED_ERROR}$'):
            seen[0].context_json()

    def _retain_and_raise(
        self,
        error: BaseException,
    ) -> tuple[Template, list[HelperOptions]]:
        template = Template()
        seen: list[HelperOptions] = []

        def fail(params: list[Any], options: HelperOptions) -> str:
            seen.append(options)
            raise error

        template.register_helper('fail', fail)
        return template, seen

    def test_helper_runtime_error_is_render_value_error(self) -> None:
        """Ordinary helper exceptions stay a render ValueError."""
        template, seen = self._retain_and_raise(RuntimeError('ordinary'))
        with self.assertRaises(ValueError):
            template.render_template('{{fail}}', {})
        self.assert_expired(seen[0])

    def test_helper_keyboard_interrupt_reaches_render(self) -> None:
        """Ctrl-C from a helper is KeyboardInterrupt, not a render ValueError."""
        template, seen = self._retain_and_raise(KeyboardInterrupt())
        with self.assertRaises(KeyboardInterrupt):
            template.render_template('{{fail}}', {})
        self.assert_expired(seen[0])

    def test_helper_system_exit_reaches_render(self) -> None:
        """sys.exit from a helper is SystemExit with the same code."""
        template, seen = self._retain_and_raise(SystemExit(7))
        with self.assertRaises(SystemExit) as ctx:
            template.render_template('{{fail}}', {})
        self.assertEqual(ctx.exception.code, 7)
        self.assert_expired(seen[0])

    def test_helper_generator_exit_reaches_render(self) -> None:
        """GeneratorExit from a helper is GeneratorExit, not a render ValueError."""
        template, seen = self._retain_and_raise(GeneratorExit())
        with self.assertRaises(GeneratorExit):
            template.render_template('{{fail}}', {})
        self.assert_expired(seen[0])

    def test_helper_custom_base_exception_reaches_render(self) -> None:
        """A custom BaseException from a helper is that exception, not ValueError."""

        class CustomBaseException(BaseException):
            pass

        template, seen = self._retain_and_raise(CustomBaseException('custom'))
        with self.assertRaises(CustomBaseException):
            template.render_template('{{fail}}', {})
        self.assert_expired(seen[0])

    def test_registered_template_render_raises_keyboard_interrupt(self) -> None:
        """render() of a registered template also surfaces helper KeyboardInterrupt."""
        template, seen = self._retain_and_raise(KeyboardInterrupt())
        template.register_template('compiled', '{{fail}}')
        with self.assertRaises(KeyboardInterrupt):
            template.render('compiled', {})
        self.assert_expired(seen[0])

    def test_native_render_template_raises_keyboard_interrupt(self) -> None:
        """The native engine raises KeyboardInterrupt from a helper too."""
        template = HandlebarrzTemplate()
        seen: list[HandlebarrzHelperOptions] = []

        def fail(params_json: str, options: HandlebarrzHelperOptions) -> str:
            seen.append(options)
            raise KeyboardInterrupt()

        template.register_helper('fail', fail)
        with self.assertRaises(KeyboardInterrupt):
            template.render_template('{{fail}}', '{}', '{}')
        with self.assertRaisesRegex(RuntimeError, f'^{EXPIRED_ERROR}$'):
            seen[0].context_json()

    def test_block_fn_raises_inner_keyboard_interrupt(self) -> None:
        """options.fn() raises KeyboardInterrupt when the inner helper does."""
        template = Template()
        seen: list[HelperOptions] = []

        def outer(params: list[Any], options: HelperOptions) -> str:
            seen.append(options)
            with self.assertRaises(KeyboardInterrupt):
                options.fn()
            return 'recovered'

        def fail(params: list[Any], options: HelperOptions) -> str:
            raise KeyboardInterrupt()

        template.register_helper('outer', outer)
        template.register_helper('fail', fail)
        self.assertEqual(template.render_template('{{#outer}}{{fail}}{{/outer}}', {}), 'recovered')
        self.assert_expired(seen[0])

    def test_block_inverse_raises_inner_keyboard_interrupt(self) -> None:
        """options.inverse() raises KeyboardInterrupt when the else helper does."""
        template = Template()
        seen: list[HelperOptions] = []

        def outer(params: list[Any], options: HelperOptions) -> str:
            seen.append(options)
            with self.assertRaises(KeyboardInterrupt):
                options.inverse()
            return 'recovered'

        def fail(params: list[Any], options: HelperOptions) -> str:
            raise KeyboardInterrupt()

        template.register_helper('outer', outer)
        template.register_helper('fail', fail)
        self.assertEqual(
            template.render_template('{{#outer}}main{{else}}{{fail}}{{/outer}}', {}),
            'recovered',
        )
        self.assert_expired(seen[0])

    def test_uncaught_inner_keyboard_interrupt_reaches_render(self) -> None:
        """An uncaught KeyboardInterrupt from options.fn() is what render raises."""
        template = Template()
        seen: list[HelperOptions] = []

        def outer(params: list[Any], options: HelperOptions) -> str:
            seen.append(options)
            return options.fn()

        def fail(params: list[Any], options: HelperOptions) -> str:
            raise KeyboardInterrupt()

        template.register_helper('outer', outer)
        template.register_helper('fail', fail)
        with self.assertRaises(KeyboardInterrupt):
            template.render_template('{{#outer}}{{fail}}{{/outer}}', {})
        self.assert_expired(seen[0])

    def test_render_after_keyboard_interrupt_still_renders(self) -> None:
        """A later render is not stuck on the previous helper KeyboardInterrupt."""
        template, seen = self._retain_and_raise(KeyboardInterrupt())
        with self.assertRaises(KeyboardInterrupt):
            template.render_template('{{fail}}', {})
        self.assert_expired(seen[0])

        template.register_helper('ok', lambda params, options: 'ok')
        self.assertEqual(template.render_template('{{ok}}', {}), 'ok')

    def test_invalid_callback_return_expires_retained_options(self) -> None:
        template = Template()
        seen: list[HelperOptions] = []

        def invalid(params: list[Any], options: HelperOptions) -> Any:
            seen.append(options)
            return object()

        template.register_helper('invalid', invalid)

        with self.assertRaises(ValueError):
            template.render_template('{{invalid}}', {})
        self.assert_expired(seen[0])

    def test_caught_inner_render_error_restores_options_until_callback_returns(self) -> None:
        template = Template()
        seen: list[HelperOptions] = []

        def outer(params: list[Any], options: HelperOptions) -> str:
            seen.append(options)
            with self.assertRaises(ValueError):
                options.fn()
            self.assertEqual(options.context(), {'name': 'Ada'})
            return 'recovered'

        def fail(params: list[Any], options: HelperOptions) -> str:
            raise RuntimeError('inner failed')

        template.register_helper('outer', outer)
        template.register_helper('fail', fail)

        self.assertEqual(template.render_template('{{#outer}}{{fail}}{{/outer}}', {'name': 'Ada'}), 'recovered')
        self.assert_expired(seen[0])

    def test_nested_helpers_receive_independent_stack_disciplined_options(self) -> None:
        template = Template()
        seen: list[tuple[str, HelperOptions]] = []

        def helper(name: str) -> Callable[[list[Any], HelperOptions], str]:
            def render(params: list[Any], options: HelperOptions) -> str:
                seen.append((name, options))
                return options.fn()

            return render

        template.register_helper('one', helper('one'))
        template.register_helper('two', helper('two'))
        template.register_helper('three', helper('three'))

        result = template.render_template('{{#one}}1{{#two}}2{{#three}}3{{/three}}{{/two}}{{/one}}', {})

        self.assertEqual(result, '123')
        self.assertEqual([name for name, _ in seen], ['one', 'two', 'three'])
        self.assertEqual(len({id(options) for _, options in seen}), 3)
        for _, options in seen:
            self.assert_expired(options)

    def test_nested_inverse_helpers_have_independent_options(self) -> None:
        template = Template()
        seen: list[HelperOptions] = []

        def invert(params: list[Any], options: HelperOptions) -> str:
            seen.append(options)
            return options.inverse()

        template.register_helper('outer', invert)
        template.register_helper('inner', invert)

        result = template.render_template(
            '{{#outer}}unused{{else}}outer-{{#inner}}unused{{else}}inner{{/inner}}{{/outer}}',
            {},
        )

        self.assertEqual(result, 'outer-inner')
        self.assertEqual(len(seen), 2)
        self.assertIsNot(seen[0], seen[1])
        for options in seen:
            self.assert_expired(options)

    def test_parent_access_during_branch_render_fails_stably_then_recovers(self) -> None:
        template = Template()
        parent: list[HelperOptions] = []

        def outer(params: list[Any], options: HelperOptions) -> str:
            parent.append(options)
            branch = options.fn()
            self.assertEqual(options.context(), {'value': 'safe'})
            return branch

        def inner(params: list[Any], options: HelperOptions) -> str:
            accessors: tuple[Callable[[], object], ...] = (
                parent[0].context,
                lambda: parent[0].hash_value('value'),
                parent[0].fn,
                parent[0].inverse,
            )
            for accessor in accessors:
                with self.assertRaisesRegex(RuntimeError, f'^{REENTRANT_ERROR}$'):
                    accessor()
            return 'nested'

        template.register_helper('outer', outer)
        template.register_helper('inner', inner)

        self.assertEqual(template.render_template('{{#outer}}{{inner}}{{/outer}}', {'value': 'safe'}), 'nested')
        self.assert_expired(parent[0])

    def test_finite_recursive_helper_calls_receive_distinct_options(self) -> None:
        template = Template()
        seen: list[HelperOptions] = []

        def recurse(params: list[Any], options: HelperOptions) -> str:
            seen.append(options)
            return options.fn()

        template.register_helper('recurse', recurse)

        result = template.render_template(
            '{{#recurse}}a{{#recurse}}b{{#recurse}}c{{/recurse}}{{/recurse}}{{/recurse}}',
            {},
        )

        self.assertEqual(result, 'abc')
        self.assertEqual(len({id(options) for options in seen}), 3)
        for options in seen:
            self.assert_expired(options)

    def test_later_helpers_and_renders_never_reactivate_old_options(self) -> None:
        template = Template()
        seen: list[HelperOptions] = []
        template.register_helper('retain_a', lambda params, options: seen.append(options) or 'a')
        template.register_helper('retain_b', lambda params, options: seen.append(options) or 'b')

        for _ in range(4):
            self.assertEqual(template.render_template('{{retain_a}}{{retain_b}}', {}), 'ab')
            for options in seen:
                self.assert_expired(options)

        self.assertEqual(len(seen), 8)
        self.assertEqual(len({id(options) for options in seen}), 8)

    def test_options_survive_cycles_gc_and_template_deletion_only_as_expired_values(self) -> None:
        template = Template()
        seen: list[HelperOptions] = []
        cycles: list[list[object]] = []

        def retain(params: list[Any], options: HelperOptions) -> str:
            seen.append(options)
            cycle: list[object] = [options]
            cycle.append(cycle)
            cycles.append(cycle)
            return 'ok'

        template.register_helper('retain', retain)
        self.assertEqual(template.render_template('{{retain}}', {}), 'ok')
        del template
        cycles.clear()
        gc.collect()

        self.assert_expired(seen[0])
        del seen[:]
        gc.collect()

    def test_async_task_can_retain_only_expired_options(self) -> None:
        async def render_and_check() -> None:
            template = Template()
            seen: list[HelperOptions] = []
            template.register_helper('retain', lambda params, options: seen.append(options) or 'ok')

            self.assertEqual(template.render_template('{{retain}}', {}), 'ok')
            await asyncio.sleep(0)

            self.assert_expired(seen[0])

        asyncio.run(render_and_check())

    def test_expired_options_return_stable_errors_after_foreign_thread_transfer(self) -> None:
        template = Template()
        seen: list[HelperOptions] = []
        template.register_helper('retain', lambda params, options: seen.append(options) or 'ok')
        self.assertEqual(template.render_template('{{retain}}', {}), 'ok')
        transferred = [seen.pop()]
        errors: list[str] = []

        def access_and_drop() -> None:
            options = transferred.pop()
            accessors: tuple[Callable[[], object], ...] = (
                options.context,
                lambda current=options: current.hash_value('value'),
                options.fn,
                options.inverse,
            )
            for accessor in accessors:
                try:
                    accessor()
                except RuntimeError as error:
                    errors.append(str(error))
            del options
            del accessors

        thread = threading.Thread(target=access_and_drop)
        thread.start()
        thread.join()
        gc.collect()

        self.assertEqual(errors, [EXPIRED_ERROR] * 4)
        self.assertEqual(transferred, [])

    def test_active_options_reject_foreign_thread_access_without_ending_callback(self) -> None:
        template = Template()
        errors: list[str] = []

        def inspect(params: list[Any], options: HelperOptions) -> str:
            def access() -> None:
                try:
                    options.context()
                except RuntimeError as error:
                    errors.append(str(error))

            thread = threading.Thread(target=access)
            thread.start()
            thread.join()
            self.assertEqual(options.context(), {'value': 'safe'})
            return 'ok'

        template.register_helper('inspect', inspect)

        self.assertEqual(template.render_template('{{inspect}}', {'value': 'safe'}), 'ok')
        self.assertEqual(errors, [THREAD_ERROR])
