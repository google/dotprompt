# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Shim class for JS2py transpiled Handlebars."""

from __future__ import annotations

from typing import Any, TypeVar

import structlog
from handlebars import Handlebars as JSHandlebars  # type: ignore

from .typing import (
    CompileOptions,
    Decorator,
    HelperDelegate,
    PrecompileOptions,
    RuntimeOptions,
    Template,
    TemplateDelegate,
    TemplateSpecification,
)

logger = structlog.get_logger(__name__)

T = TypeVar('T')

class Handlebars:
    """Shim class for Handlebars."""

    @staticmethod
    def register_helper(name: str, helper: HelperDelegate) -> None:
        """Register a helper function with the Handlebars object."""
        JSHandlebars.registerHelper(name, helper)

    @staticmethod
    def unregister_helper(name: str) -> None:
        """Unregister a helper function from the Handlebars object."""
        JSHandlebars.unregisterHelper(name)

    @staticmethod
    def register_partial[T](name: str, fn: Template[T]) -> None:
        """Register a partial function with the Handlebars object."""
        JSHandlebars.registerPartial(name, fn)

    @staticmethod
    def unregister_partial(name: str) -> None:
        """Unregister a partial function from the Handlebars object."""
        JSHandlebars.unregisterPartial(name)

    @staticmethod
    def register_decorator(name: str, decorator: Decorator) -> None:
        """Register a decorator function with the Handlebars object."""
        JSHandlebars.registerDecorator(name, decorator)

    @staticmethod
    def unregister_decorator(name: str) -> None:
        """Unregister a decorator function from the Handlebars object."""
        JSHandlebars.unregisterDecorator(name)

    @staticmethod
    def compile[T](
        s: str, options: CompileOptions | None = None
    ) -> TemplateDelegate[T]:
        """Compile a template string into a template function.

        Args:
            s: The template string to compile.
            options: Optional compile options.

        Returns:
            A template function that can be used to render the template.
        """
        return JSHandlebars.compile(s, options)  # type: ignore[no-any-return]

    @staticmethod
    def precompile(
        s: str, options: PrecompileOptions | None = None
    ) -> TemplateSpecification:
        """Precompile a template string into a template function.

        Args:
            s: The template string to compile.
            options: Optional compile options.

        Returns:
            A template function that can be used to render the template.
        """
        return JSHandlebars.precompile(s, options)

    @staticmethod
    def template[T](
        precompilation: TemplateSpecification,
    ) -> TemplateDelegate[T]:
        """Create a template function from a precompiled template.

        Args:
            precompilation: The precompiled template.

        Returns:
            A template function that can be used to render the template.
        """
        return JSHandlebars.template(precompilation)  # type: ignore[no-any-return]

    @staticmethod
    def create() -> Handlebars:
        """Factory method to create a new Handlebars instance."""
        return Handlebars()

    @staticmethod
    def log(level: int, event: str, *args: Any, **kwargs: Any) -> None:
        """Log a message.

        Args:
            level: The logging level.
            event: The event to log.
            *args: Additional arguments to pass to the logger.
            **kwargs: Additional keyword arguments to pass to the logger.

        Returns:
            None
        """
        # NOTE: We don't call the underlying JS2py logger because we want to use
        # structured logging. This function differs in signature from the
        # underlying JS2py log method.
        logger.log(level, event, *args, **kwargs)

    @staticmethod
    async def alog(level: int, event: str, *args: Any, **kwargs: Any) -> None:
        """Log a message asynchronously.

        Args:
            level: The logging level.
            event: The event to log.
            *args: Additional arguments to pass to the logger.
            **kwargs: Additional keyword arguments to pass to the logger.

        Returns:
            None
        """
        # NOTE: We don't call the underlying JS2py logger because we want to use
        # structured logging. This function differs in signature from the
        # underlying JS2py log method and the underlying JS implementation does
        # not provide an asynchronous logger.
        await logger.alog(level, event, *args, **kwargs)

    @staticmethod
    def render[T](
        template: str,
        data: T,
        options: RuntimeOptions[T] | None = None,
    ) -> str:
        """Render a template with the given data.

        Args:
            template: The template to render.
            data: The data to render the template with.
            options: Optional runtime options.

        Returns:
            The rendered template.
        """
        delegate: TemplateDelegate[T] = Handlebars.compile(template)
        return delegate(data, options)
