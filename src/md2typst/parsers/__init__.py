"""Markdown parser adapters.

This module provides a registry and factory for Markdown parsers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import MarkdownParser

# Parser registry: name -> module path
_PARSERS: dict[str, str] = {
    "markdown-it": "md2typst.parsers.markdown_it",
    "markdown-it-py": "md2typst.parsers.markdown_it",  # Alias
    "mistune": "md2typst.parsers.mistune",
    "marko": "md2typst.parsers.marko",
}

DEFAULT_PARSER = "markdown-it"


def get_parser(name: str | None = None) -> MarkdownParser:
    """Get a parser instance by name.

    Args:
        name: Parser name. If None, uses the default parser.

    Returns:
        A MarkdownParser instance.

    Raises:
        ValueError: If the parser name is not recognized.
        ImportError: If the parser's dependencies are not installed.
    """
    if name is None:
        name = DEFAULT_PARSER

    if name not in _PARSERS:
        available = ", ".join(sorted(set(_PARSERS.keys())))
        msg = f"Unknown parser: {name!r}. Available: {available}"
        raise ValueError(msg)

    module_path = _PARSERS[name]

    import importlib

    module = importlib.import_module(module_path)
    return module.create_parser()


def list_parsers() -> list[str]:
    """List available parser names."""
    return sorted(set(_PARSERS.keys()))
