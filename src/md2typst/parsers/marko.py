"""Marko parser adapter.

This module adapts the marko library to our parser interface,
converting its AST to our AST representation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable

import marko
from marko import block as marko_block, inline as marko_inline

from md2typst.ast import (
    BlockQuote,
    Code,
    CodeBlock,
    Document,
    Emphasis,
    HardBreak,
    Heading,
    HtmlBlock,
    HtmlInline,
    Image,
    Link,
    List,
    ListItem,
    Node,
    Paragraph,
    SoftBreak,
    Strikethrough,
    Strong,
    Table,
    TableCell,
    Text,
    ThematicBreak,
)

from .base import MarkdownParser


class MarkoParser(MarkdownParser):
    """Parser adapter for marko."""

    def __init__(self, gfm: bool = True) -> None:
        extensions = ["gfm"] if gfm else []
        self._md = marko.Markdown(extensions=extensions)

    @property
    def name(self) -> str:
        return "marko"

    def configure(self, options: dict[str, Any]) -> None:
        """Configure the parser.

        Supported options:
            - extensions: List of extension names to enable
        """
        extensions = options.get("extensions", [])
        if extensions:
            self._md = marko.Markdown(extensions=extensions)

    def load_plugin(self, plugin: str, **kwargs: Any) -> None:
        """Load a marko extension.

        Args:
            plugin: Extension name (e.g., 'gfm', 'codehilite', 'toc')
            **kwargs: Extension-specific options
        """
        self._md.use(plugin)

    def parse(self, text: str) -> Document:
        """Parse Markdown text into AST."""
        doc = self._md.parse(text)
        return self._convert_document(doc)

    def _convert_document(self, doc: marko_block.Document) -> Document:
        """Convert marko Document to our Document."""
        children = self._convert_children(doc.children)
        return Document(children=tuple(children))

    def _convert_children(self, children: Iterable[Any]) -> list[Node]:
        """Convert a list of marko elements to AST nodes."""
        nodes: list[Node] = []

        for child in children:
            node = self._convert_element(child)
            if node is not None:
                nodes.append(node)

        return nodes

    def _convert_element(self, element: Any) -> Node | None:
        """Convert a marko element to AST node."""
        element_type = type(element).__name__

        # Block elements
        if isinstance(element, marko_block.Paragraph):
            children = self._convert_inline_children(element.children)
            return Paragraph(children=tuple(children))

        if isinstance(element, marko_block.Heading):
            level = element.level
            children = self._convert_inline_children(element.children)
            return Heading(level=level, children=tuple(children))

        if isinstance(element, marko_block.FencedCode):
            lang = element.lang if element.lang else None
            # Get the raw code content
            code = self._get_raw_text(element.children)
            return CodeBlock(code=code, language=lang)

        if isinstance(element, marko_block.CodeBlock):
            code = self._get_raw_text(element.children)
            return CodeBlock(code=code)

        if isinstance(element, marko_block.Quote):
            children = self._convert_children(element.children)
            return BlockQuote(children=tuple(children))

        if isinstance(element, marko_block.List):
            ordered = element.ordered
            start = element.start if ordered else None
            items = []
            for child in element.children:
                if isinstance(child, marko_block.ListItem):
                    item_children = self._convert_children(child.children)
                    items.append(ListItem(children=tuple(item_children)))
            return List(ordered=ordered, items=tuple(items), start=start)

        if isinstance(element, marko_block.ThematicBreak):
            return ThematicBreak()

        if isinstance(element, marko_block.HTMLBlock):
            return HtmlBlock(content=self._get_raw_text(element.children))

        if isinstance(element, marko_block.BlankLine):
            return None

        # Handle GFM Table
        element_type = type(element).__name__
        if element_type == "Table":
            return self._convert_table(element)

        # Handle any inline elements at block level
        if hasattr(element, "children"):
            children = self._convert_inline_children(element.children)
            if children:
                return Paragraph(children=tuple(children))

        return None

    def _convert_table(self, element: Any) -> Table:
        """Convert a marko GFM Table to our Table node."""
        header: list[TableCell] = []
        rows: list[list[TableCell]] = []
        alignments: list[str | None] = []

        # Process header row
        if hasattr(element, "head") and element.head:
            head_row = element.head
            for cell in head_row.children:
                align = getattr(cell, "align", None)
                alignments.append(align)
                cell_children = self._convert_inline_children(cell.children)
                header.append(TableCell(children=tuple(cell_children)))

        # Process body rows (skip the first child as it's the header)
        body_rows = element.children[1:] if element.head else element.children
        for row in body_rows:
            row_type = type(row).__name__
            if row_type == "TableRow":
                row_cells: list[TableCell] = []
                for cell in row.children:
                    cell_children = self._convert_inline_children(cell.children)
                    row_cells.append(TableCell(children=tuple(cell_children)))
                rows.append(row_cells)

        return Table(
            header=tuple(header),
            rows=tuple(tuple(r) for r in rows),
            alignments=tuple(alignments),
        )

    def _convert_inline_children(self, children: Iterable[Any]) -> list[Node]:
        """Convert inline elements."""
        nodes: list[Node] = []

        for child in children:
            node = self._convert_inline(child)
            if node is not None:
                nodes.append(node)

        return nodes

    def _convert_inline(self, element: Any) -> Node | None:
        """Convert a marko inline element to AST node."""
        # Handle raw text
        if isinstance(element, marko_inline.RawText):
            return Text(content=element.children)

        if isinstance(element, str):
            return Text(content=element)

        if isinstance(element, marko_inline.CodeSpan):
            return Code(content=self._get_raw_text(element.children))

        if isinstance(element, marko_inline.LineBreak):
            if element.soft:
                return SoftBreak()
            return HardBreak()

        if isinstance(element, marko_inline.Emphasis):
            children = self._convert_inline_children(element.children)
            return Emphasis(children=tuple(children))

        if isinstance(element, marko_inline.StrongEmphasis):
            children = self._convert_inline_children(element.children)
            return Strong(children=tuple(children))

        # Handle GFM Strikethrough
        element_type = type(element).__name__
        if element_type == "Strikethrough":
            children = self._convert_inline_children(element.children)
            return Strikethrough(children=tuple(children))

        if isinstance(element, marko_inline.Link):
            url = element.dest or ""
            title = element.title
            children = self._convert_inline_children(element.children)
            return Link(url=url, children=tuple(children), title=title)

        if isinstance(element, marko_inline.Image):
            url = element.dest or ""
            # Get alt text from children
            alt = self._get_raw_text(element.children)
            title = element.title
            return Image(url=url, alt=alt, title=title)

        if isinstance(element, marko_inline.InlineHTML):
            return HtmlInline(content=self._get_raw_text(element.children))

        # Fallback for text-like elements
        if hasattr(element, "children"):
            text = self._get_raw_text(element.children)
            if text:
                return Text(content=text)

        return None

    def _get_raw_text(self, children: Any) -> str:
        """Extract raw text from children."""
        if isinstance(children, str):
            return children

        if isinstance(children, list):
            parts: list[str] = []
            for child in children:
                if isinstance(child, str):
                    parts.append(child)
                elif isinstance(child, marko_inline.RawText):
                    parts.append(child.children)
                elif hasattr(child, "children"):
                    parts.append(self._get_raw_text(child.children))
            return "".join(parts)

        return ""


def create_parser() -> MarkoParser:
    """Factory function to create a MarkoParser instance."""
    return MarkoParser()
