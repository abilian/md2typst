"""Typst code generator.

This module converts the parser-agnostic AST to Typst source code.
"""

# ruff: noqa: N802

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ast import Node

from .ast import (
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
    Paragraph,
    SoftBreak,
    Strikethrough,
    Strong,
    Table,
    Text,
    ThematicBreak,
)

# Characters that need escaping in Typst content mode
TYPST_SPECIAL_CHARS = re.compile(r"([*_`#@$\\<>\[\]])")


def escape_typst(text: str) -> str:
    """Escape special Typst characters in text."""
    return TYPST_SPECIAL_CHARS.sub(r"\\\1", text)


def escape_typst_string(text: str) -> str:
    """Escape text for use inside Typst strings (quoted)."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


class TypstGenerator:
    """Generates Typst code from AST."""

    def __init__(self) -> None:
        self._indent_level = 0
        self._in_list = False

    def generate(self, doc: Document) -> str:
        """Convert a Document AST to Typst source code."""
        parts: list[str] = []
        for child in doc.children:
            result = self.visit(child)
            if result:
                parts.append(result)
        return "\n\n".join(parts)

    def visit(self, node: Node) -> str:
        """Dispatch to the appropriate visitor method."""
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.visit_unknown)
        return method(node)

    def visit_unknown(self, node: Node) -> str:
        """Handle unknown node types."""
        return f"/* Unknown node: {type(node).__name__} */"

    # =========================================================================
    # Block visitors
    # =========================================================================

    def visit_Paragraph(self, node: Paragraph) -> str:
        """Convert paragraph to Typst."""
        return self._visit_children_inline(node.children)

    def visit_Heading(self, node: Heading) -> str:
        """Convert heading to Typst.

        Markdown: # Heading
        Typst: = Heading
        """
        prefix = "=" * node.level + " "
        content = self._visit_children_inline(node.children)
        return prefix + content

    def visit_CodeBlock(self, node: CodeBlock) -> str:
        """Convert code block to Typst.

        Uses Typst's raw block syntax with optional language.
        """
        lang = node.language or ""
        code = node.code.rstrip("\n")
        return f"```{lang}\n{code}\n```"

    def visit_BlockQuote(self, node: BlockQuote) -> str:
        """Convert block quote to Typst.

        Uses Typst's #quote block or #block with custom styling.
        """
        content_parts: list[str] = []
        for child in node.children:
            result = self.visit(child)
            if result:
                content_parts.append(result)
        content = "\n\n".join(content_parts)

        # Use #blockquote or styled block
        # For now, use a simple approach with #block
        return f"#block(inset: (left: 1em), stroke: (left: 2pt + luma(200)))[\n{content}\n]"

    def visit_List(self, node: List) -> str:
        """Convert list to Typst."""
        items: list[str] = []
        old_in_list = self._in_list
        self._in_list = True

        for i, item in enumerate(node.items):
            if node.ordered:
                # Typst uses + for auto-numbered, or explicit numbers
                if node.start is not None and node.start != 1:
                    marker = f"{node.start + i}. "
                else:
                    marker = "+ "
            else:
                marker = "- "

            item_content = self._visit_list_item(item)
            items.append(marker + item_content)

        self._in_list = old_in_list
        return "\n".join(items)

    def _visit_list_item(self, node: ListItem) -> str:
        """Convert a list item's content."""
        parts: list[str] = []
        for i, child in enumerate(node.children):
            result = self.visit(child)
            if result:
                # Nested lists need to be indented
                if isinstance(child, List):
                    # Indent each line of the nested list
                    result = "  " + result.replace("\n", "\n  ")
                elif i > 0:
                    # For other nested blocks after the first, indent them
                    result = "  " + result.replace("\n", "\n  ")
                parts.append(result)

        if not parts:
            return ""
        if len(parts) == 1:
            return parts[0]
        return parts[0] + "\n" + "\n".join(parts[1:])

    def visit_ThematicBreak(self, node: ThematicBreak) -> str:
        """Convert thematic break to Typst."""
        return "#line(length: 100%)"

    def visit_Table(self, node: Table) -> str:
        """Convert table to Typst."""
        num_cols = len(node.header)
        if num_cols == 0:
            return ""

        # Build column specification
        col_specs = []
        for align in node.alignments:
            if align == "left":
                col_specs.append("left")
            elif align == "right":
                col_specs.append("right")
            elif align == "center":
                col_specs.append("center")
            else:
                col_specs.append("auto")

        columns = ", ".join(col_specs) if col_specs else "auto, " * num_cols
        columns = columns.rstrip(", ")

        lines = [f"#table(columns: ({columns}),"]

        # Header row - all cells in a single table.header() call
        header_cells = []
        for cell in node.header:
            cell_content = self._visit_children_inline(cell.children)
            header_cells.append(f"[{cell_content}]")
        if header_cells:
            lines.append(f"  table.header({', '.join(header_cells)}),")

        # Body rows
        for row in node.rows:
            row_cells: list[str] = []
            for cell in row:
                cell_content = self._visit_children_inline(cell.children)
                row_cells.append(f"[{cell_content}]")
            lines.append(f"  {', '.join(row_cells)},")

        lines.append(")")
        return "\n".join(lines)

    def visit_HtmlBlock(self, node: HtmlBlock) -> str:
        """Convert HTML block - emit as comment since Typst doesn't support HTML."""
        escaped = node.content.replace("*/", "* /")
        return f"/* HTML block:\n{escaped}\n*/"

    # =========================================================================
    # Inline visitors
    # =========================================================================

    def _visit_children_inline(self, children: list[Node]) -> str:
        """Visit all children and concatenate results."""
        parts: list[str] = []
        for child in children:
            result = self.visit(child)
            parts.append(result)
        return "".join(parts)

    def visit_Text(self, node: Text) -> str:
        """Convert text node, escaping special characters."""
        return escape_typst(node.content)

    def visit_Emphasis(self, node: Emphasis) -> str:
        """Convert emphasis to Typst.

        Markdown: *text* or _text_
        Typst: _text_
        """
        content = self._visit_children_inline(node.children)
        return f"_{content}_"

    def visit_Strong(self, node: Strong) -> str:
        """Convert strong to Typst.

        Markdown: **text**
        Typst: *text*
        """
        content = self._visit_children_inline(node.children)
        return f"*{content}*"

    def visit_Strikethrough(self, node: Strikethrough) -> str:
        """Convert strikethrough to Typst.

        Markdown: ~~text~~
        Typst: #strike[text]
        """
        content = self._visit_children_inline(node.children)
        return f"#strike[{content}]"

    def visit_Code(self, node: Code) -> str:
        """Convert inline code to Typst.

        Both Markdown and Typst use backticks for inline code.
        """
        # If code contains backticks, we need to use more backticks
        content = node.content
        if "`" in content:
            # Find number of consecutive backticks in content
            max_ticks = 0
            current = 0
            for char in content:
                if char == "`":
                    current += 1
                    max_ticks = max(max_ticks, current)
                else:
                    current = 0
            delim = "`" * (max_ticks + 1)
            # Add space if content starts/ends with backtick
            if content.startswith("`") or content.endswith("`"):
                return f"{delim} {content} {delim}"
            return f"{delim}{content}{delim}"
        return f"`{content}`"

    def visit_Link(self, node: Link) -> str:
        """Convert link to Typst.

        Markdown: [text](url)
        Typst: #link("url")[text]
        """
        url = escape_typst_string(node.url)
        content = self._visit_children_inline(node.children)
        return f'#link("{url}")[{content}]'

    def visit_Image(self, node: Image) -> str:
        """Convert image to Typst.

        Markdown: ![alt](url)
        Typst: #image("url", alt: "alt")
        """
        url = escape_typst_string(node.url)
        alt = escape_typst_string(node.alt) if node.alt else ""
        if alt:
            return f'#image("{url}", alt: "{alt}")'
        return f'#image("{url}")'

    def visit_SoftBreak(self, node: SoftBreak) -> str:
        """Convert soft break - typically just a space or newline."""
        return "\n"

    def visit_HardBreak(self, node: HardBreak) -> str:
        """Convert hard break to Typst.

        Typst uses \\ for line breaks within a paragraph.
        """
        return " \\\n"

    def visit_HtmlInline(self, node: HtmlInline) -> str:
        """Convert inline HTML - emit as-is or as comment."""
        # Common HTML entities that we can convert
        html_entities = {
            "&lt;": "<",
            "&gt;": ">",
            "&amp;": "&",
            "&quot;": '"',
            "&nbsp;": "~",  # Non-breaking space in Typst
        }

        content = node.content
        for entity, replacement in html_entities.items():
            content = content.replace(entity, replacement)

        # If it's a simple tag, emit as comment
        if content.startswith("<") and content.endswith(">"):
            return f"/* {content} */"

        return escape_typst(content)


def generate_typst(doc: Document) -> str:
    """Convenience function to generate Typst from a Document."""
    generator = TypstGenerator()
    return generator.generate(doc)
