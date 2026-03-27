"""Typst code generator.

This module converts the parser-agnostic AST to Typst source code.
"""

# ruff: noqa: N802

from __future__ import annotations

import re
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from .ast import Node

from .ast import (
    BlockQuote,
    Code,
    CodeBlock,
    Document,
    Emphasis,
    FootnoteDef,
    FootnoteRef,
    HardBreak,
    Heading,
    HtmlBlock,
    HtmlInline,
    Image,
    IndexEntry,
    Link,
    List,
    ListItem,
    MathBlock,
    MathInline,
    Paragraph,
    SoftBreak,
    Strikethrough,
    Strong,
    Table,
    Text,
    ThematicBreak,
)

# Characters that need escaping in Typst content mode
# Note: ( must be escaped to prevent interpretation as function call after ]
TYPST_SPECIAL_CHARS = re.compile(r"([*_`#@$\\<>\[\](])")


def escape_typst(text: str) -> str:
    """Escape special Typst characters in text."""
    return TYPST_SPECIAL_CHARS.sub(r"\\\1", text)


def escape_typst_string(text: str) -> str:
    """Escape text for use inside Typst strings (quoted)."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


class TypstGenerator:
    """Generates Typst code from AST."""

    def __init__(
        self,
        note_style: str = "footnote",
        stylesheets: list[str] | None = None,
    ) -> None:
        """Initialize the generator.

        Args:
            note_style: How to render footnotes. Options:
                - "footnote": Inline footnotes using Typst's #footnote[]
                - "endnote": Superscript numbers with notes collected at end
            stylesheets: List of Typst stylesheet modules to import.
        """
        self._indent_level = 0
        self._in_list = False
        self._footnotes: dict[str, FootnoteDef] = {}
        self._note_style = note_style
        self._stylesheets = stylesheets or []
        # Track endnote references in order for numbering
        self._endnote_refs: list[str] = []

    def generate(self, doc: Document) -> str:
        """Convert a Document AST to Typst source code.

        First collects all footnote definitions, then generates output.
        For footnote style: references are resolved inline using #footnote[].
        For endnote style: references become superscripts, notes at end.
        """
        # Reset endnote tracking for each generation
        self._endnote_refs = []

        # First pass: collect all footnote definitions
        self._collect_footnotes(doc)

        # Second pass: generate output (FootnoteDefs produce no output)
        parts: list[str] = []
        for child in doc.children:
            result = self.visit(child)
            if result:
                parts.append(result)

        result = "\n\n".join(parts)

        # For endnote style, append the notes section
        if self._note_style == "endnote" and self._endnote_refs:
            endnotes_section = self._generate_endnotes_section()
            if endnotes_section:
                result = result + "\n\n" + endnotes_section

        # Prepend front matter variables, stylesheet imports, and preamble
        prepended: list[str] = []

        # Extract preamble and stylesheets from metadata (if present)
        preamble = ""
        extra_stylesheets: list[str] = []
        if doc.metadata:
            preamble = doc.metadata.get("preamble", "")
            # Support both 'stylesheet' (single) and 'stylesheets' (list) in front matter
            fm_stylesheet = doc.metadata.get("stylesheet")
            fm_stylesheets = doc.metadata.get("stylesheets", [])
            if fm_stylesheet:
                extra_stylesheets.append(fm_stylesheet)
            if isinstance(fm_stylesheets, list):
                extra_stylesheets.extend(fm_stylesheets)
            elif fm_stylesheets:
                extra_stylesheets.append(str(fm_stylesheets))

        # Generate front matter variables (excluding reserved keys)
        if doc.metadata:
            frontmatter = self._generate_frontmatter_variables(doc.metadata)
            if frontmatter:
                prepended.append(frontmatter)

        # Merge stylesheets from config and front matter
        all_stylesheets = self._stylesheets + extra_stylesheets
        if all_stylesheets:
            imports = self._generate_stylesheet_imports_list(all_stylesheets)
            prepended.append(imports)

        # Add preamble (raw Typst code from front matter)
        if preamble and isinstance(preamble, str):
            prepended.append(preamble.strip())

        if prepended:
            result = "\n\n".join(prepended) + "\n\n" + result

        return result

    def _generate_endnotes_section(self) -> str:
        """Generate the endnotes section for endnote style."""
        if not self._endnote_refs:
            return ""

        lines = ["= Notes", ""]
        for _i, label in enumerate(self._endnote_refs, 1):
            footnote_def = self._footnotes.get(label)
            if footnote_def:
                content_parts: list[str] = []
                for child in footnote_def.children:
                    result = self.visit(child)
                    if result:
                        content_parts.append(result)
                content = " ".join(content_parts) if content_parts else ""
                lines.append(f"+ {content}")

        return "\n".join(lines)

    def _generate_stylesheet_imports(self) -> str:
        """Generate Typst import statements for stylesheets."""
        return self._generate_stylesheet_imports_list(self._stylesheets)

    def _generate_stylesheet_imports_list(self, stylesheets: list[str]) -> str:
        """Generate Typst import statements for a list of stylesheets."""
        lines = []
        for stylesheet in stylesheets:
            # Add .typ extension if not present
            name = stylesheet if stylesheet.endswith(".typ") else f"{stylesheet}.typ"
            lines.append(f'#import "{name}": *')
        return "\n".join(lines)

    # Reserved front matter keys that have special handling
    RESERVED_FRONTMATTER_KEYS: ClassVar[set[str]] = {
        "preamble",
        "stylesheet",
        "stylesheets",
    }

    def _generate_frontmatter_variables(self, metadata: dict) -> str:
        """Generate Typst variable declarations from front matter.

        Args:
            metadata: Dictionary of front matter fields.

        Returns:
            Typst code defining the variables as #let statements.

        Note:
            Reserved keys (preamble, stylesheet, stylesheets) are handled
            specially and not converted to variables.
        """
        lines = []
        for key, value in metadata.items():
            # Skip reserved keys that have special handling
            if key in self.RESERVED_FRONTMATTER_KEYS:
                continue

            # Sanitize key for Typst (use hyphens, which Typst allows)
            typst_key = key.replace("_", "-").replace(" ", "-")
            var_name = f"doc-{typst_key}"

            # Convert value to Typst literal
            if value is None:
                lines.append(f"#let {var_name} = none")
            elif isinstance(value, bool):
                lines.append(f"#let {var_name} = {str(value).lower()}")
            elif isinstance(value, int | float):
                lines.append(f"#let {var_name} = {value}")
            elif isinstance(value, str):
                escaped = self._escape_typst_string(value)
                lines.append(f'#let {var_name} = "{escaped}"')
            elif isinstance(value, list):
                # Convert list to Typst array
                items = []
                for item in value:
                    if isinstance(item, str):
                        escaped = self._escape_typst_string(item)
                        items.append(f'"{escaped}"')
                    elif isinstance(item, bool):
                        items.append(str(item).lower())
                    elif isinstance(item, int | float):
                        items.append(str(item))
                    else:
                        items.append(f'"{item}"')
                lines.append(f"#let {var_name} = ({', '.join(items)},)")
            else:
                # Fallback: convert to string
                escaped = self._escape_typst_string(str(value))
                lines.append(f'#let {var_name} = "{escaped}"')

        return "\n".join(lines)

    def _escape_typst_string(self, s: str) -> str:
        """Escape a string for use in Typst string literals."""
        # Escape backslashes first, then quotes
        return s.replace("\\", "\\\\").replace('"', '\\"')

    def _collect_footnotes(self, node: Node) -> None:
        """Recursively collect all FootnoteDef nodes."""
        if isinstance(node, FootnoteDef):
            self._footnotes[node.label] = node
        elif isinstance(node, Document):
            for child in node.children:
                self._collect_footnotes(child)

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

        # Build alignment specification
        align_specs = []
        for align in node.alignments:
            if align == "left":
                align_specs.append("left")
            elif align == "right":
                align_specs.append("right")
            elif align == "center":
                align_specs.append("center")
            else:
                align_specs.append("auto")

        # columns takes widths (auto), align takes alignment values
        if align_specs:
            align_str = ", ".join(align_specs)
            lines = [f"#table(columns: {num_cols}, align: ({align_str}),"]
        else:
            lines = [f"#table(columns: {num_cols},"]

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

    def visit_FootnoteDef(self, node: FootnoteDef) -> str:
        """Footnote definitions produce no direct output.

        The content is inlined at the FootnoteRef location using Typst's
        #footnote[] function. The definition is collected in the first pass
        and used when visiting FootnoteRef nodes.
        """
        # Footnote defs are consumed by refs, no direct output
        return ""

    # =========================================================================
    # Inline visitors
    # =========================================================================

    def _visit_children_inline(self, children: tuple[Node, ...]) -> str:
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
        """Convert soft break to Typst linebreak.

        In Typst, a single newline within a paragraph is treated as a space.
        We emit \\ + newline to preserve the line break from the source.
        """
        return " \\\n"

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

    def visit_FootnoteRef(self, node: FootnoteRef) -> str:
        """Convert footnote reference to Typst.

        For footnote style:
            Markdown: [^label]
            Typst: #footnote[content]

        For endnote style:
            Markdown: [^label]
            Typst: #super[N] (where N is the note number)

        Looks up the footnote definition by label and inlines its content.
        If the footnote is not found, emits the original reference as text.
        """
        footnote_def = self._footnotes.get(node.label)
        if footnote_def is None:
            # Unresolved reference - emit as escaped text
            return escape_typst(f"[^{node.label}]")

        if self._note_style == "endnote":
            # Track this reference for endnote numbering
            if node.label not in self._endnote_refs:
                self._endnote_refs.append(node.label)
            note_number = self._endnote_refs.index(node.label) + 1
            return f"#super[{note_number}]"

        # Default: footnote style - inline the content
        content_parts: list[str] = []
        for child in footnote_def.children:
            result = self.visit(child)
            if result:
                content_parts.append(result)

        # Join content - for simple footnotes it's a single paragraph,
        # for complex ones we join with double newlines
        if len(content_parts) == 1:
            content = content_parts[0]
        else:
            content = "\n\n".join(content_parts)

        return f"#footnote[{content}]"

    def visit_IndexEntry(self, node: IndexEntry) -> str:
        """Convert index entry to Typst.

        Markdown: [term]{.index} or [text]{.index key="term!subterm"}
        Typst: #index("term")term or #index("term", "subterm")text

        The index marker is invisible but registers the term in the index.
        The term text is displayed in the document.
        """
        term = escape_typst_string(node.term)

        if node.subterm:
            subterm = escape_typst_string(node.subterm)
            return f'#index("{term}", "{subterm}")'

        return f'#index("{term}")'

    def visit_MathInline(self, node: MathInline) -> str:
        """Convert inline math to Typst.

        Uses mitex for LaTeX pass-through.
        Markdown: $E = mc^2$
        Typst: #mi("E = mc^2")
        """
        # Escape for Typst string
        content = escape_typst_string(node.content)
        return f'#mi("{content}")'

    def visit_MathBlock(self, node: MathBlock) -> str:
        """Convert display math to Typst.

        Uses mitex for LaTeX pass-through.
        Markdown: $$...$$
        Typst: #mitex(`...`) in a block
        """
        # Use raw string (backticks) to avoid escaping issues
        content = node.content
        # If content contains backticks, we need to handle it
        if "`" in content:
            # Use more backticks as delimiter
            max_ticks = 0
            current = 0
            for char in content:
                if char == "`":
                    current += 1
                    max_ticks = max(max_ticks, current)
                else:
                    current = 0
            delim = "`" * (max_ticks + 1)
            return f"#mitex({delim}{content}{delim})"
        return f"#mitex(`{content}`)"


def generate_typst(
    doc: Document,
    note_style: str = "footnote",
    stylesheets: list[str] | None = None,
) -> str:
    """Convenience function to generate Typst from a Document.

    Args:
        doc: The Document AST to convert.
        note_style: How to render footnotes ("footnote" or "endnote").
        stylesheets: List of Typst stylesheet modules to import.
    """
    generator = TypstGenerator(note_style=note_style, stylesheets=stylesheets)
    return generator.generate(doc)
