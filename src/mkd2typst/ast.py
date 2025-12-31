"""AST node definitions for mkd2typst.

This module defines a parser-agnostic AST that serves as the intermediate
representation between Markdown parsing and Typst code generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Node:
    """Base AST node."""

    def __str__(self) -> str:
        return f"{self.__class__.__name__}()"


# =============================================================================
# Block Nodes
# =============================================================================


@dataclass
class Document(Node):
    """Root node containing all block elements."""

    children: list[Node] = field(default_factory=list)

    def __str__(self) -> str:
        return f"Document({len(self.children)} children)"


@dataclass
class Paragraph(Node):
    """A paragraph containing inline elements."""

    children: list[Node] = field(default_factory=list)

    def __str__(self) -> str:
        return f"Paragraph({len(self.children)} children)"


@dataclass
class Heading(Node):
    """A heading with level 1-6."""

    level: int
    children: list[Node] = field(default_factory=list)

    def __str__(self) -> str:
        return f"Heading(level={self.level}, {len(self.children)} children)"


@dataclass
class CodeBlock(Node):
    """A fenced or indented code block."""

    code: str
    language: str | None = None

    def __str__(self) -> str:
        lang = self.language or "none"
        lines = self.code.count("\n") + 1
        return f"CodeBlock(lang={lang}, {lines} lines)"


@dataclass
class BlockQuote(Node):
    """A block quote containing other block elements."""

    children: list[Node] = field(default_factory=list)

    def __str__(self) -> str:
        return f"BlockQuote({len(self.children)} children)"


@dataclass
class List(Node):
    """An ordered or unordered list."""

    ordered: bool
    items: list[ListItem] = field(default_factory=list)
    start: int | None = None  # Starting number for ordered lists

    def __str__(self) -> str:
        kind = "ordered" if self.ordered else "unordered"
        return f"List({kind}, {len(self.items)} items)"


@dataclass
class ListItem(Node):
    """A single item in a list."""

    children: list[Node] = field(default_factory=list)

    def __str__(self) -> str:
        return f"ListItem({len(self.children)} children)"


@dataclass
class ThematicBreak(Node):
    """A horizontal rule / thematic break."""

    def __str__(self) -> str:
        return "ThematicBreak()"


@dataclass
class Table(Node):
    """A table with header and body rows."""

    header: list[TableCell] = field(default_factory=list)
    rows: list[list[TableCell]] = field(default_factory=list)
    alignments: list[str | None] = field(
        default_factory=list
    )  # 'left', 'right', 'center', None

    def __str__(self) -> str:
        return f"Table({len(self.header)} cols, {len(self.rows)} rows)"


@dataclass
class TableCell(Node):
    """A single cell in a table."""

    children: list[Node] = field(default_factory=list)

    def __str__(self) -> str:
        return f"TableCell({len(self.children)} children)"


# =============================================================================
# Inline Nodes
# =============================================================================


@dataclass
class Text(Node):
    """Plain text content."""

    content: str

    def __str__(self) -> str:
        preview = self.content[:20] + "..." if len(self.content) > 20 else self.content
        return f"Text({preview!r})"


@dataclass
class Emphasis(Node):
    """Emphasized (italic) text."""

    children: list[Node] = field(default_factory=list)

    def __str__(self) -> str:
        return f"Emphasis({len(self.children)} children)"


@dataclass
class Strong(Node):
    """Strong (bold) text."""

    children: list[Node] = field(default_factory=list)

    def __str__(self) -> str:
        return f"Strong({len(self.children)} children)"


@dataclass
class Strikethrough(Node):
    """Strikethrough text (GFM extension)."""

    children: list[Node] = field(default_factory=list)

    def __str__(self) -> str:
        return f"Strikethrough({len(self.children)} children)"


@dataclass
class Code(Node):
    """Inline code span."""

    content: str

    def __str__(self) -> str:
        preview = self.content[:20] + "..." if len(self.content) > 20 else self.content
        return f"Code({preview!r})"


@dataclass
class Link(Node):
    """A hyperlink."""

    url: str
    children: list[Node] = field(default_factory=list)
    title: str | None = None

    def __str__(self) -> str:
        return f"Link(url={self.url!r})"


@dataclass
class Image(Node):
    """An image."""

    url: str
    alt: str = ""
    title: str | None = None

    def __str__(self) -> str:
        return f"Image(url={self.url!r})"


@dataclass
class SoftBreak(Node):
    """A soft line break (typically rendered as space)."""

    def __str__(self) -> str:
        return "SoftBreak()"


@dataclass
class HardBreak(Node):
    """A hard line break."""

    def __str__(self) -> str:
        return "HardBreak()"


@dataclass
class HtmlBlock(Node):
    """Raw HTML block (preserved but may not render in Typst)."""

    content: str

    def __str__(self) -> str:
        lines = self.content.count("\n") + 1
        return f"HtmlBlock({lines} lines)"


@dataclass
class HtmlInline(Node):
    """Inline HTML (preserved but may not render in Typst)."""

    content: str

    def __str__(self) -> str:
        preview = self.content[:20] + "..." if len(self.content) > 20 else self.content
        return f"HtmlInline({preview!r})"
