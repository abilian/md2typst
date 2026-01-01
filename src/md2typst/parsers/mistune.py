"""Mistune parser adapter.

This module adapts the mistune library to our parser interface,
converting its AST to our AST representation.
"""

from __future__ import annotations

from typing import Any

import mistune

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

# Default GFM plugins to enable
GFM_PLUGINS = ["strikethrough", "table"]


class MistuneParser(MarkdownParser):
    """Parser adapter for mistune."""

    def __init__(self, gfm: bool = True) -> None:
        plugins = GFM_PLUGINS if gfm else []
        self._md = mistune.create_markdown(renderer=None, plugins=plugins)
        self._plugins = list(plugins)

    @property
    def name(self) -> str:
        return "mistune"

    def configure(self, options: dict[str, Any]) -> None:
        """Configure the parser.

        Supported options:
            - plugins: List of plugin names to enable
        """
        plugins = options.get("plugins", [])
        self._md = mistune.create_markdown(renderer=None, plugins=plugins)

    def load_plugin(self, plugin: str, **kwargs: Any) -> None:
        """Load a mistune plugin.

        Args:
            plugin: Plugin name (e.g., 'strikethrough', 'table', 'footnotes')
            **kwargs: Plugin-specific options (unused for mistune built-ins)
        """
        # Rebuild with the plugin if not already loaded
        if plugin not in self._plugins:
            self._plugins.append(plugin)
            self._md = mistune.create_markdown(renderer=None, plugins=self._plugins)

    def parse(self, text: str) -> Document:
        """Parse Markdown text into AST."""
        tokens = self._md(text)
        if not isinstance(tokens, list):
            return Document(children=[])
        return self._convert_document(tokens)

    def _convert_document(self, tokens: list[dict]) -> Document:
        """Convert top-level tokens to Document."""
        children = self._convert_blocks(tokens)
        return Document(children=tuple(children))

    def _convert_blocks(self, tokens: list[dict]) -> list[Node]:
        """Convert a list of block tokens to AST nodes."""
        nodes: list[Node] = []

        for token in tokens:
            node = self._convert_block(token)
            if node is not None:
                nodes.append(node)

        return nodes

    def _convert_block(self, token: dict) -> Node | None:
        """Convert a single block token to AST node."""
        token_type = token.get("type")

        if token_type == "paragraph":
            children = self._convert_inline(token.get("children", []))
            return Paragraph(children=tuple(children))

        if token_type == "heading":
            level = token.get("attrs", {}).get("level", 1)
            children = self._convert_inline(token.get("children", []))
            return Heading(level=level, children=tuple(children))

        if token_type in ("code_block", "block_code"):
            info = token.get("attrs", {}).get("info")
            raw = token.get("raw", "")
            return CodeBlock(code=raw, language=info if info else None)

        if token_type == "block_quote":
            children = self._convert_blocks(token.get("children", []))
            return BlockQuote(children=tuple(children))

        if token_type == "list":
            ordered = token.get("attrs", {}).get("ordered", False)
            start = token.get("attrs", {}).get("start")
            items = []
            for child in token.get("children", []):
                if child.get("type") == "list_item":
                    item_children = self._convert_blocks(child.get("children", []))
                    items.append(ListItem(children=tuple(item_children)))
            return List(
                ordered=ordered, items=tuple(items), start=start if ordered else None
            )

        if token_type == "thematic_break":
            return ThematicBreak()

        if token_type == "block_html":
            return HtmlBlock(content=token.get("raw", ""))

        if token_type == "block_text":
            # Block text is typically inside list items
            children = self._convert_inline(token.get("children", []))
            return Paragraph(children=tuple(children))

        if token_type == "table":
            return self._convert_table(token)

        return None

    def _convert_table(self, token: dict) -> Table:
        """Convert a mistune table token to Table node."""
        header: list[TableCell] = []
        rows: list[list[TableCell]] = []
        alignments: list[str | None] = []

        for child in token.get("children", []):
            child_type = child.get("type")

            if child_type == "table_head":
                # Process header cells
                for cell in child.get("children", []):
                    if cell.get("type") == "table_cell":
                        attrs = cell.get("attrs", {})
                        align = attrs.get("align")
                        alignments.append(align)
                        cell_children = self._convert_inline(cell.get("children", []))
                        header.append(TableCell(children=tuple(cell_children)))

            elif child_type == "table_body":
                # Process body rows
                for row in child.get("children", []):
                    if row.get("type") == "table_row":
                        row_cells: list[TableCell] = []
                        for cell in row.get("children", []):
                            if cell.get("type") == "table_cell":
                                cell_children = self._convert_inline(
                                    cell.get("children", [])
                                )
                                row_cells.append(
                                    TableCell(children=tuple(cell_children))
                                )
                        rows.append(row_cells)

        return Table(
            header=tuple(header),
            rows=tuple(tuple(r) for r in rows),
            alignments=tuple(alignments),
        )

    def _convert_inline(self, tokens: list[dict]) -> list[Node]:
        """Convert inline tokens to AST nodes."""
        nodes: list[Node] = []

        for token in tokens:
            node = self._convert_inline_token(token)
            if node is not None:
                nodes.append(node)

        return nodes

    def _convert_inline_token(self, token: dict) -> Node | None:
        """Convert a single inline token to AST node."""
        token_type = token.get("type")

        if token_type == "text":
            return Text(content=token.get("raw", ""))

        if token_type == "codespan":
            return Code(content=token.get("raw", ""))

        if token_type == "softbreak":
            return SoftBreak()

        if token_type == "linebreak":
            return HardBreak()

        if token_type == "emphasis":
            children = self._convert_inline(token.get("children", []))
            return Emphasis(children=tuple(children))

        if token_type == "strong":
            children = self._convert_inline(token.get("children", []))
            return Strong(children=tuple(children))

        if token_type == "strikethrough":
            children = self._convert_inline(token.get("children", []))
            return Strikethrough(children=tuple(children))

        if token_type == "link":
            attrs = token.get("attrs", {})
            url = attrs.get("url", "")
            title = attrs.get("title")
            children = self._convert_inline(token.get("children", []))
            return Link(url=url, children=tuple(children), title=title)

        if token_type == "image":
            attrs = token.get("attrs", {})
            url = attrs.get("url", "")
            # Alt text can be in attrs or in children as text
            alt = attrs.get("alt", "")
            if not alt:
                # Extract alt text from children
                children = token.get("children", [])
                alt = "".join(
                    child.get("raw", "")
                    for child in children
                    if child.get("type") == "text"
                )
            title = attrs.get("title")
            return Image(url=url, alt=alt, title=title)

        if token_type == "inline_html":
            return HtmlInline(content=token.get("raw", ""))

        return None


def create_parser() -> MistuneParser:
    """Factory function to create a MistuneParser instance."""
    return MistuneParser()
