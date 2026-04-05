"""Core conversion functions for md2typst."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

from md2typst.generator import generate_typst

if TYPE_CHECKING:
    from md2typst.config import Config
from md2typst.parsers import get_parser


def convert(
    markdown: str,
    parser: str | None = None,
    parser_options: dict[str, Any] | None = None,
    plugins: list[str] | None = None,
    output_options: dict[str, Any] | None = None,
    stylesheets: list[str] | None = None,
) -> str:
    """Convert Markdown text to Typst.

    Args:
        markdown: The Markdown source text.
        parser: Optional parser name. Uses default if not specified.
        parser_options: Optional parser-specific options.
        plugins: Optional list of parser plugins to load.
        output_options: Optional output generation options (e.g., note_style).
        stylesheets: Optional list of Typst stylesheet modules to import.

    Returns:
        The generated Typst source code.
    """
    p = get_parser(parser)

    if parser_options:
        p.configure(parser_options)

    if plugins:
        for plugin in plugins:
            with contextlib.suppress(NotImplementedError):
                p.load_plugin(plugin)

    doc = p.parse(markdown)

    # Extract generator options
    note_style = (output_options or {}).get("note_style", "footnote")
    return generate_typst(doc, note_style=note_style, stylesheets=stylesheets)


def convert_with_config(markdown: str, config: Config) -> str:
    """Convert Markdown text to Typst using a Config object.

    Args:
        markdown: The Markdown source text.
        config: Configuration object.

    Returns:
        The generated Typst source code.
    """
    p = get_parser(config.parser)

    if config.parser_options:
        p.configure(config.parser_options)

    if config.plugins:
        for plugin in config.plugins:
            with contextlib.suppress(NotImplementedError):
                p.load_plugin(plugin)

    doc = p.parse(markdown)

    # Extract generator options
    note_style = config.output_options.get("note_style", "footnote")
    return generate_typst(
        doc,
        note_style=note_style,
        stylesheets=config.stylesheets,
        style=config.style,
    )
