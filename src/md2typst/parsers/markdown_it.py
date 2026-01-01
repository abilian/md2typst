"""Markdown-it-py parser adapter.

This module adapts the markdown-it-py library to our parser interface,
converting its token stream to our AST representation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from markdown_it import MarkdownIt

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

if TYPE_CHECKING:
    from markdown_it.token import Token


class MarkdownItParser(MarkdownParser):
    """Parser adapter for markdown-it-py."""

    def __init__(self, gfm: bool = True) -> None:
        self._md = MarkdownIt("commonmark")
        if gfm:
            self._enable_gfm()

    @property
    def name(self) -> str:
        return "markdown-it-py"

    def _enable_gfm(self) -> None:
        """Enable GFM extensions (tables, strikethrough)."""
        self._md.enable("table")
        self._md.enable("strikethrough")

    def configure(self, options: dict[str, Any]) -> None:
        """Configure the parser.

        Supported options:
            - preset: Parser preset ('commonmark', 'gfm-like', 'js-default')
            - gfm: Enable GFM extensions (default: True)
            - html: Enable HTML parsing (default: True)
            - linkify: Auto-convert URLs to links (default: False)
            - typographer: Enable typographic replacements (default: False)
        """
        preset = options.pop("preset", None)
        if preset:
            self._md = MarkdownIt(preset)

        gfm = options.pop("gfm", None)
        if gfm is True:
            self._enable_gfm()

        if options:
            self._md.options.update(options)

    def load_plugin(self, plugin: str, **kwargs: Any) -> None:
        """Load a markdown-it-py plugin.

        Args:
            plugin: Plugin module path (e.g., 'mdit_py_plugins.footnote')
            **kwargs: Plugin-specific options
        """
        import importlib

        module = importlib.import_module(plugin)

        # Most plugins have a _plugin attribute or are callable
        if hasattr(module, "footnote_plugin"):
            self._md.use(module.footnote_plugin, **kwargs)
        elif hasattr(module, "plugin"):
            self._md.use(module.plugin, **kwargs)
        else:
            # Try to find any *_plugin function
            for attr_name in dir(module):
                if attr_name.endswith("_plugin"):
                    plugin_func = getattr(module, attr_name)
                    self._md.use(plugin_func, **kwargs)
                    return
            msg = f"Could not find plugin function in {plugin}"
            raise ValueError(msg)

    def parse(self, text: str) -> Document:
        """Parse Markdown text into AST."""
        tokens = self._md.parse(text)
        return self._convert_document(tokens)

    def _convert_document(self, tokens: list[Token]) -> Document:
        """Convert top-level tokens to Document."""
        children = self._convert_blocks(tokens)
        return Document(children=tuple(children))

    def _convert_blocks(self, tokens: list[Token]) -> list[Node]:
        """Convert a list of block tokens to AST nodes."""
        nodes: list[Node] = []
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token.type == "paragraph_open":
                # Find content and closing
                i += 1
                inline_token = tokens[i]
                i += 1  # Skip paragraph_close
                i += 1
                children = self._convert_inline(inline_token.children or [])
                nodes.append(Paragraph(children=tuple(children)))

            elif token.type == "heading_open":
                level = int(token.tag[1])  # h1 -> 1, h2 -> 2, etc.
                i += 1
                inline_token = tokens[i]
                i += 1  # Skip heading_close
                i += 1
                children = self._convert_inline(inline_token.children or [])
                nodes.append(Heading(level=level, children=tuple(children)))

            elif token.type == "fence":
                lang = token.info.strip() if token.info else None
                nodes.append(CodeBlock(code=token.content, language=lang))
                i += 1

            elif token.type == "code_block":
                nodes.append(CodeBlock(code=token.content))
                i += 1

            elif token.type == "blockquote_open":
                i += 1
                # Collect tokens until blockquote_close
                inner_tokens: list[Token] = []
                depth = 1
                while i < len(tokens) and depth > 0:
                    if tokens[i].type == "blockquote_open":
                        depth += 1
                    elif tokens[i].type == "blockquote_close":
                        depth -= 1
                    if depth > 0:
                        inner_tokens.append(tokens[i])
                    i += 1
                children = self._convert_blocks(inner_tokens)
                nodes.append(BlockQuote(children=tuple(children)))

            elif token.type == "bullet_list_open":
                i, list_node = self._convert_list(tokens, i, ordered=False)
                nodes.append(list_node)

            elif token.type == "ordered_list_open":
                start = token.attrGet("start")
                start_num = int(start) if start else 1
                i, list_node = self._convert_list(
                    tokens, i, ordered=True, start=start_num
                )
                nodes.append(list_node)

            elif token.type == "hr":
                nodes.append(ThematicBreak())
                i += 1

            elif token.type == "html_block":
                nodes.append(HtmlBlock(content=token.content))
                i += 1

            elif token.type == "table_open":
                i, table_node = self._convert_table(tokens, i)
                nodes.append(table_node)

            else:
                # Skip unknown tokens
                i += 1

        return nodes

    def _convert_table(self, tokens: list[Token], start_idx: int) -> tuple[int, Table]:
        """Convert table tokens to Table node."""
        header: list[TableCell] = []
        rows: list[list[TableCell]] = []
        alignments: list[str | None] = []

        i = start_idx + 1  # Skip table_open

        while i < len(tokens) and tokens[i].type != "table_close":
            token = tokens[i]

            if token.type == "thead_open":
                i += 1
                # Process header row
                while i < len(tokens) and tokens[i].type != "thead_close":
                    if tokens[i].type == "tr_open":
                        i += 1
                        while i < len(tokens) and tokens[i].type != "tr_close":
                            if tokens[i].type == "th_open":
                                # Get alignment from style attribute
                                style = str(tokens[i].attrGet("style") or "")
                                if "text-align:left" in style:
                                    alignments.append("left")
                                elif "text-align:right" in style:
                                    alignments.append("right")
                                elif "text-align:center" in style:
                                    alignments.append("center")
                                else:
                                    alignments.append(None)
                                i += 1
                                # Get inline content
                                if i < len(tokens) and tokens[i].type == "inline":
                                    children = self._convert_inline(
                                        tokens[i].children or []
                                    )
                                    header.append(TableCell(children=tuple(children)))
                                    i += 1
                                else:
                                    header.append(TableCell(children=[]))
                                # Skip th_close
                                if i < len(tokens) and tokens[i].type == "th_close":
                                    i += 1
                            else:
                                i += 1
                        i += 1  # Skip tr_close
                    else:
                        i += 1
                i += 1  # Skip thead_close

            elif token.type == "tbody_open":
                i += 1
                # Process body rows
                while i < len(tokens) and tokens[i].type != "tbody_close":
                    if tokens[i].type == "tr_open":
                        i += 1
                        row: list[TableCell] = []
                        while i < len(tokens) and tokens[i].type != "tr_close":
                            if tokens[i].type == "td_open":
                                i += 1
                                # Get inline content
                                if i < len(tokens) and tokens[i].type == "inline":
                                    children = self._convert_inline(
                                        tokens[i].children or []
                                    )
                                    row.append(TableCell(children=tuple(children)))
                                    i += 1
                                else:
                                    row.append(TableCell(children=[]))
                                # Skip td_close
                                if i < len(tokens) and tokens[i].type == "td_close":
                                    i += 1
                            else:
                                i += 1
                        rows.append(row)
                        i += 1  # Skip tr_close
                    else:
                        i += 1
                i += 1  # Skip tbody_close

            else:
                i += 1

        i += 1  # Skip table_close
        return i, Table(
            header=tuple(header),
            rows=tuple(tuple(r) for r in rows),
            alignments=tuple(alignments),
        )

    def _convert_list(
        self,
        tokens: list[Token],
        start_idx: int,
        ordered: bool,
        start: int | None = None,
    ) -> tuple[int, List]:
        """Convert list tokens to List node."""
        items: list[ListItem] = []
        i = start_idx + 1  # Skip list_open

        close_type = "ordered_list_close" if ordered else "bullet_list_close"

        while i < len(tokens) and tokens[i].type != close_type:
            token = tokens[i]

            if token.type == "list_item_open":
                i += 1
                # Collect tokens until list_item_close
                inner_tokens: list[Token] = []
                depth = 1
                while i < len(tokens) and depth > 0:
                    if tokens[i].type == "list_item_open":
                        depth += 1
                    elif tokens[i].type == "list_item_close":
                        depth -= 1
                    if depth > 0:
                        inner_tokens.append(tokens[i])
                    i += 1
                children = self._convert_blocks(inner_tokens)
                items.append(ListItem(children=tuple(children)))
            else:
                i += 1

        i += 1  # Skip list_close
        return i, List(
            ordered=ordered, items=tuple(items), start=start if ordered else None
        )

    def _convert_inline(self, tokens: list[Token]) -> list[Node]:
        """Convert inline tokens to AST nodes."""
        nodes: list[Node] = []
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token.type == "text":
                nodes.append(Text(content=token.content))
                i += 1

            elif token.type == "code_inline":
                nodes.append(Code(content=token.content))
                i += 1

            elif token.type == "softbreak":
                nodes.append(SoftBreak())
                i += 1

            elif token.type == "hardbreak":
                nodes.append(HardBreak())
                i += 1

            elif token.type == "em_open":
                i += 1
                children, i = self._collect_until(tokens, i, "em_close")
                nodes.append(Emphasis(children=tuple(children)))

            elif token.type == "strong_open":
                i += 1
                children, i = self._collect_until(tokens, i, "strong_close")
                nodes.append(Strong(children=tuple(children)))

            elif token.type == "s_open":
                i += 1
                children, i = self._collect_until(tokens, i, "s_close")
                nodes.append(Strikethrough(children=tuple(children)))

            elif token.type == "link_open":
                href = str(token.attrGet("href") or "")
                title_attr = token.attrGet("title")
                title = str(title_attr) if title_attr is not None else None
                i += 1
                children, i = self._collect_until(tokens, i, "link_close")
                nodes.append(Link(url=href, children=tuple(children), title=title))

            elif token.type == "image":
                src = str(token.attrGet("src") or "")
                alt = token.content or ""
                title_attr = token.attrGet("title")
                title = str(title_attr) if title_attr is not None else None
                nodes.append(Image(url=src, alt=alt, title=title))
                i += 1

            elif token.type == "html_inline":
                nodes.append(HtmlInline(content=token.content))
                i += 1

            else:
                # Skip unknown inline tokens
                i += 1

        return nodes

    def _collect_until(
        self, tokens: list[Token], start: int, close_type: str
    ) -> tuple[list[Node], int]:
        """Collect and convert tokens until a closing token is found."""
        collected: list[Token] = []
        i = start
        depth = 1

        # Determine matching open type
        open_type = close_type.replace("_close", "_open")

        while i < len(tokens) and depth > 0:
            if tokens[i].type == open_type:
                depth += 1
            elif tokens[i].type == close_type:
                depth -= 1

            if depth > 0:
                collected.append(tokens[i])
            i += 1

        children = self._convert_inline(collected)
        return children, i


def create_parser() -> MarkdownItParser:
    """Factory function to create a MarkdownItParser instance."""
    return MarkdownItParser()
