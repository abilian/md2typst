"""AST node definitions for md2typst.

This module defines a parser-agnostic AST that serves as the intermediate
representation between Markdown parsing and Typst code generation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Node:
    """Base AST node."""

    def __str__(self) -> str:
        return f"{self.__class__.__name__}()"


# =============================================================================
# Block Nodes
# =============================================================================


@dataclass(frozen=True)
class Document(Node):
    """Root node containing all block elements."""

    children: tuple[Node, ...] = ()

    def __str__(self) -> str:
        return f"Document({len(self.children)} children)"


@dataclass(frozen=True)
class Paragraph(Node):
    """A paragraph containing inline elements."""

    children: tuple[Node, ...] = ()

    def __str__(self) -> str:
        return f"Paragraph({len(self.children)} children)"


@dataclass(frozen=True)
class Heading(Node):
    """A heading with level 1-6."""

    level: int
    children: tuple[Node, ...] = ()

    def __str__(self) -> str:
        return f"Heading(level={self.level}, {len(self.children)} children)"


@dataclass(frozen=True)
class CodeBlock(Node):
    """A fenced or indented code block."""

    code: str
    language: str | None = None

    def __str__(self) -> str:
        lang = self.language or "none"
        lines = self.code.count("\n") + 1
        return f"CodeBlock(lang={lang}, {lines} lines)"


@dataclass(frozen=True)
class BlockQuote(Node):
    """A block quote containing other block elements."""

    children: tuple[Node, ...] = ()

    def __str__(self) -> str:
        return f"BlockQuote({len(self.children)} children)"


@dataclass(frozen=True)
class List(Node):
    """An ordered or unordered list."""

    ordered: bool
    items: tuple[ListItem, ...] = ()
    start: int | None = None  # Starting number for ordered lists

    def __str__(self) -> str:
        kind = "ordered" if self.ordered else "unordered"
        return f"List({kind}, {len(self.items)} items)"


@dataclass(frozen=True)
class ListItem(Node):
    """A single item in a list."""

    children: tuple[Node, ...] = ()

    def __str__(self) -> str:
        return f"ListItem({len(self.children)} children)"


@dataclass(frozen=True)
class ThematicBreak(Node):
    """A horizontal rule / thematic break."""

    def __str__(self) -> str:
        return "ThematicBreak()"


@dataclass(frozen=True)
class Table(Node):
    """A table with header and body rows."""

    header: tuple[TableCell, ...] = ()
    rows: tuple[tuple[TableCell, ...], ...] = ()
    alignments: tuple[str | None, ...] = ()  # 'left', 'right', 'center', None

    def __str__(self) -> str:
        return f"Table({len(self.header)} cols, {len(self.rows)} rows)"


@dataclass(frozen=True)
class TableCell(Node):
    """A single cell in a table."""

    children: tuple[Node, ...] = ()

    def __str__(self) -> str:
        return f"TableCell({len(self.children)} children)"


# =============================================================================
# Inline Nodes
# =============================================================================


@dataclass(frozen=True)
class Text(Node):
    """Plain text content."""

    content: str

    def __str__(self) -> str:
        preview = self.content[:20] + "..." if len(self.content) > 20 else self.content
        return f"Text({preview!r})"


@dataclass(frozen=True)
class Emphasis(Node):
    """Emphasized (italic) text."""

    children: tuple[Node, ...] = ()

    def __str__(self) -> str:
        return f"Emphasis({len(self.children)} children)"


@dataclass(frozen=True)
class Strong(Node):
    """Strong (bold) text."""

    children: tuple[Node, ...] = ()

    def __str__(self) -> str:
        return f"Strong({len(self.children)} children)"


@dataclass(frozen=True)
class Strikethrough(Node):
    """Strikethrough text (GFM extension)."""

    children: tuple[Node, ...] = ()

    def __str__(self) -> str:
        return f"Strikethrough({len(self.children)} children)"


@dataclass(frozen=True)
class Code(Node):
    """Inline code span."""

    content: str

    def __str__(self) -> str:
        preview = self.content[:20] + "..." if len(self.content) > 20 else self.content
        return f"Code({preview!r})"


@dataclass(frozen=True)
class Link(Node):
    """A hyperlink."""

    url: str
    children: tuple[Node, ...] = ()
    title: str | None = None

    def __str__(self) -> str:
        return f"Link(url={self.url!r})"


@dataclass(frozen=True)
class Image(Node):
    """An image."""

    url: str
    alt: str = ""
    title: str | None = None

    def __str__(self) -> str:
        return f"Image(url={self.url!r})"


@dataclass(frozen=True)
class SoftBreak(Node):
    """A soft line break (typically rendered as space)."""

    def __str__(self) -> str:
        return "SoftBreak()"


@dataclass(frozen=True)
class HardBreak(Node):
    """A hard line break."""

    def __str__(self) -> str:
        return "HardBreak()"


@dataclass(frozen=True)
class HtmlBlock(Node):
    """Raw HTML block (preserved but may not render in Typst)."""

    content: str

    def __str__(self) -> str:
        lines = self.content.count("\n") + 1
        return f"HtmlBlock({lines} lines)"


@dataclass(frozen=True)
class HtmlInline(Node):
    """Inline HTML (preserved but may not render in Typst)."""

    content: str

    def __str__(self) -> str:
        preview = self.content[:20] + "..." if len(self.content) > 20 else self.content
        return f"HtmlInline({preview!r})"
