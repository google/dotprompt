# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Handlebars typing stub while we don't have a working implementation
of handlebars."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypedDict

type TemplateDelegate[T] = Callable[[T, RuntimeOptions[T] | None], str]

type Template[T] = TemplateDelegate[T] | str


class RuntimeOptions[T](TypedDict, total=False):
    """Options passed to templates during runtime execution."""

    partial: bool
    depths: list[Any]
    helpers: dict[str, HelperDelegate]
    partials: dict[str, TemplateDelegate[T]]  # Fix: Added type parameter T
    decorators: dict[str, Decorator]
    data: Any
    blockParams: list[Any]
    allowCallsToHelperMissing: bool
    allowedProtoProperties: dict[str, bool]
    allowedProtoMethods: dict[str, bool]
    allowProtoPropertiesByDefault: bool
    allowProtoMethodsByDefault: bool


class HelperOptions[T](TypedDict, total=False):
    """Options passed to helper functions."""

    fn: TemplateDelegate[T]
    inverse: TemplateDelegate[T]
    hash: dict[str, Any]
    data: Any


# Helper delegate function type
type Context = Any
type HelperDelegateVariadic = Callable[..., Any]
type HelperDelegateNonVariadic = Callable[
    [Context | None, HelperOptions[Any] | None], Any
]
type HelperDelegate = HelperDelegateNonVariadic | HelperDelegateVariadic
type HelperDeclareSpec = dict[str, HelperDelegate]

type Decorator = Callable[[Any], Any]


type TemplateSpecification = Any

KnownHelpers = dict[str, bool]


class CompileOptions(TypedDict, total=False):
    """Options for compiling templates."""

    data: bool
    compat: bool
    knownHelpers: KnownHelpers
    knownHelpersOnly: bool
    noEscape: bool
    strict: bool
    assumeObjects: bool
    preventIndent: bool
    ignoreStandalone: bool
    explicitPartialContext: bool


class PrecompileOptions(CompileOptions, total=False):
    """Options for precompiling templates."""

    srcName: str
    destName: str


class ResolvePartialOptions(TypedDict):
    """Options for resolving partials."""

    name: str
    helpers: dict[str, Callable[..., Any]]
    partials: dict[str, TemplateDelegate[Any]]
    decorators: dict[str, Callable[..., Any]]
    data: Any


type ASTNode = Any


class HandlebarsException:
    """Exception class for Handlebars errors."""

    def __init__(self, message: str, node: ASTNode | None = None):
        """
        Initialize a new Handlebars exception.

        Args:
            message: Error message
            node: Optional AST node that caused the error
        """
        self.description: str = ''
        self.fileName: str = ''
        self.lineNumber: Any = None
        self.endLineNumber: Any = None
        self.message: str = message
        self.name: str = 'HandlebarsException'
        self.number: int = 0
        self.stack: str | None = None
        self.column: Any = None
        self.endColumn: Any = None
