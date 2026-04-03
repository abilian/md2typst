"""AST node definitions for md2typst.

This module defines a parser-agnostic AST that serves as the intermediate
representation between Markdown parsing and Typst code generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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
    """Root node containing all block elements.

    Attributes:
        children: The block-level child nodes.
        metadata: Optional front matter metadata (from YAML).
    """

    children: tuple[Node, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        meta = f", {len(self.metadata)} meta" if self.metadata else ""
        return f"Document({len(self.children)} children{meta})"


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


@dataclass(frozen=True)
class FootnoteDef(Node):
    """Footnote definition (block-level).

    Contains the content of a footnote, referenced by label elsewhere in the
    document. The content can include multiple block elements (paragraphs,
    lists, etc.).

    Example Markdown:
        [^1]: This is a footnote with *formatting*.

            Indented paragraphs continue the footnote.
    """

    label: str  # The reference label (e.g., "1", "note")
    children: tuple[Node, ...] = ()  # Footnote content (can be multi-block)

    def __str__(self) -> str:
        return f"FootnoteDef(label={self.label!r}, {len(self.children)} children)"


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


@dataclass(frozen=True)
class FootnoteRef(Node):
    """Inline reference to a footnote.

    References a FootnoteDef by label. During generation, the reference is
    resolved and the footnote content is inlined.

    Example Markdown:
        Here is some text with a footnote[^1] and another[^note].
    """

    label: str  # The reference label (e.g., "1", "note")

    def __str__(self) -> str:
        return f"FootnoteRef(label={self.label!r})"


@dataclass(frozen=True)
class MathInline(Node):
    """Inline math expression.

    Example Markdown:
        The equation $E = mc^2$ is famous.

    Example Typst output (pass-through mode):
        The equation #mi("E = mc^2") is famous.
    """

    content: str  # LaTeX math content (without delimiters)

    def __str__(self) -> str:
        preview = self.content[:20] + "..." if len(self.content) > 20 else self.content
        return f"MathInline({preview!r})"


@dataclass(frozen=True)
class MathBlock(Node):
    """Display/block math expression.

    Example Markdown:
        $$
        \\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}
        $$

    Example Typst output (pass-through mode):
        #mitex(`\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}`)
    """

    content: str  # LaTeX math content (without delimiters)

    def __str__(self) -> str:
        lines = self.content.count("\n") + 1
        return f"MathBlock({lines} lines)"


@dataclass(frozen=True)
class MermaidBlock(Node):
    """A Mermaid diagram block.

    Example Markdown:
        ```mermaid
        graph TD; A-->B;
        ```

    Example Typst output:
        #mermaid("graph TD; A-->B;")

    Requires: #import "@preview/mmdr:0.2.1": mermaid
    """

    code: str  # Mermaid diagram source

    def __str__(self) -> str:
        lines = self.code.count("\n") + 1
        return f"MermaidBlock({lines} lines)"


@dataclass(frozen=True)
class IndexEntry(Node):
    """An index entry marker for document indexing.

    Marks a term for inclusion in a document index. The term appears in the
    text and is also registered for the index. Supports hierarchical entries
    with main terms and subterms.

    Example Markdown (Pandoc-style):
        The [Python]{.index} programming language...
        [functions]{.index key="Programming!Functions"}

    Example Typst output:
        #index("Python")Python
        #index("Programming", "Functions")functions
    """

    term: str  # Primary index term
    subterm: str | None = None  # Optional subterm for hierarchical entries
    see: str | None = None  # Cross-reference ("see also X")

    def __str__(self) -> str:
        if self.subterm:
            return f"IndexEntry(term={self.term!r}, subterm={self.subterm!r})"
        return f"IndexEntry(term={self.term!r})"
