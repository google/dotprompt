# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Python wrapper for the Handlebars templating language using handlebars-rust.

This module provides a Pythonic interface to the Handlebars templating system
implemented in Rust. It supports full Handlebars functionality including
template registration, rendering, partials, block helpers, custom helpers,
subexpressions, inline partials, and various configuration options.

## Features:

- Template registration (strings, files, directories)
- Partial templates and blocks
- Custom helper functions
- Built-in helpers (each, if, unless, with, lookup, log)
- Block helpers with inverse sections (else blocks)
- Context navigation (this, ../parent, @root)
- Subexpressions and parameter literals
- HTML escaping options and customization
- Strict mode for missing fields
- Development mode for automatic template reloading
- Whitespace control with ~ operator

## Typical usage example:

```python
# Using the Template class
from handlebarrz import Template

template = Template()
template.register_template("hello", "Hello {{name}}!")
result = template.render("hello", {"name": "World"})
# result = "Hello World!"

# Using the Handlebars alias.
# Import is placed here as an example. In real usage, import at the top
from handlebarrz import Handlebars

handlebars = Handlebars()
handlebars.register_template("greeting", "Hello {{name}}!")
result = handlebars.render("greeting", {"name": "World"})
# result = "Hello World!"

# Using custom helpers
def format_name(params, hash, ctx):
    name = params[0]
    return name.upper() if hash.get("uppercase") else name

handlebars.register_helper("format", format_name)
handlebars.register_template(
    "formatted", "Hello {{format name uppercase=true}}!"
)
result = handlebars.render("formatted", {"name": "World"})
# result = "Hello WORLD!"
```
"""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import structlog

from ._native import (
    HandlebarrzTemplate as _HandlebarrzTemplate,
)
from ._native import (
    html_escape,
    no_escape,
)

logger = structlog.get_logger(__name__)


class EscapeFunction:
    """Enumeration of built-in escape functions for Handlebars templates.

    These constants define how content is escaped when rendered in templates.
    By default, Handlebars escapes HTML entities in variables to prevent XSS
    attacks, but this behavior can be customized.

    Attributes:
        HTML_ESCAPE: Escapes HTML entities (default, converts &<>"' to entities)
        NO_ESCAPE: Passes content through without any escaping
    """

    HTML_ESCAPE = 'html_escape'
    NO_ESCAPE = 'no_escape'


class Template:
    """A Handlebars template engine that can register and render templates.

    This class wraps the Rust implementation of Handlebars and provides a
    Pythonic interface for template registration, rendering, and configuration.

    The Handlebars template language extends basic templating with expressions,
    helpers, partials, block expressions, and more. This implementation supports
    the full range of Handlebars features including:

    * Expressions: `{{var}}`, `{{{var}}}`, `{{&var}}`
    * Block Expressions: `{{#block}}...{{/block}}`
    * Partials: `{{> partial}}`
    * Comments: `{{! comment }}`
    * Helpers: `{{helper param1 param2 key=value}}`
    * Block Helpers: `{{#helper}}...{{else}}...{{/helper}}`
    * Path Navigation: `{{../parent}}`, `{{this}}`, `{{@root}}`
    * Literals: `{{helper "string" 123 true null undefined}}`
    * Subexpressions: `{{helper (subhelper param) param2}}`
    * Whitespace Control: `{{~helper}}` or `{{helper~}}`

    Attributes:
        strict_mode: Whether to raise errors for missing fields in templates
        dev_mode: Whether to enable development mode features for auto-reloading
    """

    def __init__(self) -> None:
        """Initialize a new Handlebars template engine.

        Creates a fresh template registry with default settings:
        - HTML escaping enabled.
        - Strict mode disabled.
        - Development mode disabled.
        - Built-in helpers registered (if, unless, each, with, lookup, log,
          etc.).
        """
        self._template = _HandlebarrzTemplate()

    @property
    def strict_mode(self) -> bool:
        """Get the current strict mode setting.

        Returns:
            bool: True if strict mode is enabled, False otherwise
        """
        return self._template.get_strict_mode()

    @strict_mode.setter
    def strict_mode(self, enabled: bool) -> None:
        """Set strict mode for this template engine.

        In strict mode, accessing missing fields raises an error instead of
        returning an empty string. This helps catch typos and undefined
        variables during development.

        Args:
            enabled: Whether to enable strict mode
        """
        self._template.set_strict_mode(enabled)
        logger.debug({'event': 'strict_mode_changed', 'enabled': enabled})

    @property
    def dev_mode(self) -> bool:
        """Get the current dev mode setting.

        Returns:
            bool: True if dev mode is enabled, False otherwise
        """
        return self._template.get_dev_mode()

    @dev_mode.setter
    def dev_mode(self, enabled: bool) -> None:
        """Set development mode for this template engine.

        In dev mode, templates are automatically reloaded from file when
        modified. This is useful during development to see changes without
        restarting the application.

        Args:
            enabled: Whether to enable development mode
        """
        self._template.set_dev_mode(enabled)
        logger.debug({'event': 'dev_mode_changed', 'enabled': enabled})

    def set_escape_function(self, escape_fn: str) -> None:
        """Set the escape function used for HTML escaping.

        Controls how variable values are escaped when rendered in templates with
        the `{{var}}` syntax (triple stache `{{{var}}}` and ampersand `{{&var}}`
        will still render unescaped).

        Args:
            escape_fn: The escape function to use, one of the values from
                EscapeFunction

        Raises:
            ValueError: If the escape function is not recognized
        """
        try:
            self._template.set_escape_fn(escape_fn)
            logger.debug(
                {'event': 'escape_function_changed', 'function': escape_fn}
            )
        except ValueError as e:
            logger.error({'event': 'escape_function_error', 'error': str(e)})
            raise

    def register_template(self, name: str, template_string: str) -> None:
        """Register a template with the given name.

        Templates are parsed and validated at registration time, which allows
        for early detection of syntax errors. Registered templates can be
        rendered multiple times with different contexts without reparsing.

        Args:
            name: The name to register the template under
            template_string: The template string to register

        Raises:
            ValueError: If there is a syntax error in the template
        """
        try:
            self._template.register_template(name, template_string)
            logger.debug({'event': 'template_registered', 'name': name})
        except ValueError as e:
            logger.error(
                {
                    'event': 'template_registration_error',
                    'name': name,
                    'error': str(e),
                }
            )
            raise

    def register_partial(self, name: str, template_string: str) -> None:
        """Register a partial with the given name.

        Partials are templates that can be included in other templates using the
        `{{> partial_name}}` syntax. They can receive the current context or a
        custom context.

        Args:
            name: The name to register the partial under
            template_string: The partial template string

        Raises:
            ValueError: If there is a syntax error in the template
        """
        try:
            self._template.register_partial(name, template_string)
            logger.debug({'event': 'partial_registered', 'name': name})
        except ValueError as e:
            logger.error(
                {
                    'event': 'partial_registration_error',
                    'name': name,
                    'error': str(e),
                }
            )
            raise

    def register_template_file(self, name: str, file_path: str | Path) -> None:
        """Register a template from a file.

        Reads the template from the specified file and registers it under the
        given name. In development mode, the template will be automatically
        reloaded when the file changes.

        Args:
            name: The name to register the template under
            file_path: Path to the template file

        Raises:
            FileNotFoundError: If the template file does not exist
            ValueError: If there is a syntax error in the template
        """
        file_path_str = str(file_path)
        try:
            self._template.register_template_file(name, file_path_str)
            logger.debug(
                {
                    'event': 'template_file_registered',
                    'name': name,
                    'path': file_path_str,
                }
            )
        except (FileNotFoundError, ValueError) as e:
            logger.error(
                {
                    'event': 'template_file_registration_error',
                    'name': name,
                    'path': file_path_str,
                    'error': str(e),
                }
            )
            raise

    def register_templates_directory(
        self, dir_path: str | Path, extension: str = '.hbs'
    ) -> None:
        """Register all templates in a directory.

        Recursively finds all files with the specified extension in the
        directory and registers them as templates. The template name will be the
        file path relative to the directory, without the extension.

        Args:
            dir_path: Path to the directory containing templates
            extension: File extension for templates, defaults to ".hbs"

        Raises:
            FileNotFoundError: If the directory does not exist
            ValueError: If there is a syntax error in any template
        """
        dir_path_str = str(dir_path)
        try:
            self._template.register_templates_directory(dir_path_str, extension)
            logger.debug(
                {
                    'event': 'templates_directory_registered',
                    'path': dir_path_str,
                    'extension': extension,
                }
            )
        except (FileNotFoundError, ValueError) as e:
            logger.error(
                {
                    'event': 'templates_directory_registration_error',
                    'path': dir_path_str,
                    'extension': extension,
                    'error': str(e),
                }
            )
            raise

    def register_helper(
        self,
        name: str,
        helper_fn: Callable[[list[Any], dict[str, Any], dict[str, Any]], str],
    ) -> None:
        """Register a helper function.

        Helpers extend the templating engine with custom functionality. They can
        be called from templates using the `{{helper_name arg1 arg2 key=value}}`
        syntax.

        The helper function should take three parameters:
        - params: List of positional parameters passed to the helper
        - hash: Dictionary of named parameters (hash) passed to the helper
        - context: Dictionary containing the current context

        It should return a string that will be inserted into the template.

        Examples:
            ```python
            # A helper that formats a date
            def format_date(params, hash, ctx):
                date_obj = params[0]
                format_str = hash.get("format", "%Y-%m-%d")
                return date_obj.strftime(format_str)

            template.register_helper("formatDate", format_date)

            # Usage in template:
            # {{formatDate date format="%-d %B %Y"}}
            ```

        Args:
            name: The name to register the helper under
            helper_fn: The helper function
        """
        try:
            # TODO: Fix this type error.
            self._template.register_helper(name, create_helper(helper_fn))  # type: ignore[arg-type]
            logger.debug({'event': 'helper_registered', 'name': name})
        except Exception as e:
            logger.error(
                {
                    'event': 'helper_registration_error',
                    'name': name,
                    'error': str(e),
                }
            )
            raise

    def has_template(self, name: str) -> bool:
        """Check if a template with the given name exists.

        Args:
            name: The name of the template to check

        Returns:
            bool: True if the template exists, False otherwise
        """
        return self._template.has_template(name)

    def unregister_template(self, name: str) -> None:
        """Unregister a template with the given name.

        Removes the template from the registry. If the template doesn't exist,
        this is a no-op.

        Args:
            name: The name of the template to unregister
        """
        self._template.unregister_template(name)
        logger.debug({'event': 'template_unregistered', 'name': name})

    def render(self, name: str, data: dict[str, Any]) -> str:
        """Render a template with the given data.

        Renders a previously registered template using the provided data
        context. The data is converted to JSON before being passed to the
        template engine.

        Args:
            name: The name of the template to render
            data: The data to render the template with

        Returns:
            str: The rendered template string

        Raises:
            ValueError: If the template does not exist or there is a rendering
                error.
        """
        try:
            result = self._template.render(name, json.dumps(data))
            logger.debug({'event': 'template_rendered', 'name': name})
            return result
        except ValueError as e:
            logger.error(
                {
                    'event': 'template_rendering_error',
                    'name': name,
                    'error': str(e),
                }
            )
            raise

    def render_template(
        self, template_string: str, data: dict[str, Any]
    ) -> str:
        """Render a template string directly without registering it.

        Parses and renders the template string in one step. This is useful for
        one-off template rendering, but for templates that will be rendered
        multiple times, it's more efficient to register them first.

        Args:
            template_string: The template string to render
            data: The data to render the template with

        Returns:
            str: The rendered template string

        Raises:
            ValueError: If there is a syntax error in the template or a
                rendering error.
        """
        try:
            result = self._template.render_template(
                template_string, json.dumps(data)
            )
            logger.debug({'event': 'template_string_rendered'})
            return result
        except ValueError as e:
            logger.error(
                {'event': 'template_string_rendering_error', 'error': str(e)}
            )
            raise


def create_helper(
    fn: Callable[[list[Any], dict[str, Any], dict[str, Any]], str],
) -> Callable[[str, str, str], str]:
    """Create a helper function compatible with the Rust interface.

    This function adapts a Python function with typed parameters to the format
    expected by the Rust bindings. It handles the serialization and
    deserialization of JSON data between Rust and Python.

    Helper functions in Handlebars can be used for various purposes:
    - Formatting data (dates, numbers, strings)
    - Conditional rendering with custom logic
    - Transforming data (sorting, filtering, mapping)
    - Generating HTML or other output formats
    - Implementing custom block helpers

    Args:
        fn: A function taking (params, hash, context) and returning a string
            - params: List of positional parameters
            - hash: Dictionary of named parameters
            - context: The current template context

    Returns:
        Callable: A function compatible with the Rust interface
    """

    def wrapper(params_json: str, hash_json: str, ctx_json: str) -> str:
        params = json.loads(params_json)
        hash = json.loads(hash_json)
        ctx = json.loads(ctx_json)

        result = fn(params, hash, ctx)
        return result

    return wrapper


# Alias Template as Handlebars.
Handlebars = Template


__all__ = [
    'Template',
    'Handlebars',
    'EscapeFunction',
    'create_helper',
    'html_escape',
    'no_escape',
]
