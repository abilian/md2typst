"""Tests for the Typst generator."""

from __future__ import annotations

import pytest

from md2typst.ast import (
    BlockQuote,
    Code,
    CodeBlock,
    Document,
    Emphasis,
    FootnoteDef,
    FootnoteRef,
    HardBreak,
    Heading,
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
    Text,
    ThematicBreak,
)
from md2typst.generator import escape_typst, generate_typst

pytestmark = pytest.mark.unit


class TestEscaping:
    """Test character escaping functions."""

    def test_escape_asterisk(self):
        assert escape_typst("a*b") == r"a\*b"

    def test_escape_underscore(self):
        assert escape_typst("a_b") == r"a\_b"

    def test_escape_backtick(self):
        assert escape_typst("a`b") == r"a\`b"

    def test_escape_hash(self):
        assert escape_typst("#tag") == r"\#tag"

    def test_escape_at(self):
        assert escape_typst("@ref") == r"\@ref"

    def test_escape_dollar(self):
        assert escape_typst("$100") == r"\$100"

    def test_escape_backslash(self):
        assert escape_typst(r"a\b") == r"a\\b"

    def test_escape_multiple(self):
        assert escape_typst("*_`#") == r"\*\_\`\#"

    def test_no_escape_plain_text(self):
        assert escape_typst("Hello world") == "Hello world"


class TestGeneratorBasics:
    """Test basic generator functionality."""

    def test_empty_document(self):
        doc = Document(children=[])
        result = generate_typst(doc)
        assert result == ""

    def test_simple_paragraph(self):
        doc = Document(children=[Paragraph(children=[Text(content="Hello world")])])
        result = generate_typst(doc)
        assert result == "Hello world"

    def test_multiple_paragraphs(self):
        doc = Document(
            children=[
                Paragraph(children=[Text(content="First")]),
                Paragraph(children=[Text(content="Second")]),
            ]
        )
        result = generate_typst(doc)
        assert "First" in result
        assert "Second" in result
        assert "\n\n" in result  # Paragraphs separated by blank line


class TestHeadings:
    """Test heading generation."""

    @pytest.mark.parametrize(
        ("level", "prefix"),
        [
            (1, "= "),
            (2, "== "),
            (3, "=== "),
            (4, "==== "),
            (5, "===== "),
            (6, "====== "),
        ],
    )
    def test_heading_levels(self, level, prefix):
        doc = Document(
            children=[Heading(level=level, children=[Text(content="Title")])]
        )
        result = generate_typst(doc)
        assert result == f"{prefix}Title"

    def test_heading_with_emphasis(self):
        doc = Document(
            children=[
                Heading(
                    level=1,
                    children=[
                        Text(content="Hello "),
                        Emphasis(children=[Text(content="World")]),
                    ],
                )
            ]
        )
        result = generate_typst(doc)
        assert result == "= Hello _World_"


class TestInlineFormatting:
    """Test inline formatting elements."""

    def test_emphasis(self):
        doc = Document(
            children=[Paragraph(children=[Emphasis(children=[Text(content="italic")])])]
        )
        result = generate_typst(doc)
        assert result == "_italic_"

    def test_strong(self):
        doc = Document(
            children=[Paragraph(children=[Strong(children=[Text(content="bold")])])]
        )
        result = generate_typst(doc)
        assert result == "*bold*"

    def test_nested_formatting(self):
        # **_bold italic_**
        doc = Document(
            children=[
                Paragraph(
                    children=[
                        Strong(
                            children=[Emphasis(children=[Text(content="bold italic")])]
                        )
                    ]
                )
            ]
        )
        result = generate_typst(doc)
        assert result == "*_bold italic_*"

    def test_strikethrough(self):
        doc = Document(
            children=[
                Paragraph(children=[Strikethrough(children=[Text(content="deleted")])])
            ]
        )
        result = generate_typst(doc)
        assert result == "#strike[deleted]"

    def test_inline_code(self):
        doc = Document(children=[Paragraph(children=[Code(content="x = 1")])])
        result = generate_typst(doc)
        assert result == "`x = 1`"

    def test_inline_code_with_backticks(self):
        doc = Document(children=[Paragraph(children=[Code(content="a`b")])])
        result = generate_typst(doc)
        assert "``" in result  # Should use double backticks


class TestLinks:
    """Test link generation."""

    def test_simple_link(self):
        doc = Document(
            children=[
                Paragraph(
                    children=[
                        Link(
                            url="https://example.com",
                            children=[Text(content="Example")],
                        )
                    ]
                )
            ]
        )
        result = generate_typst(doc)
        assert result == '#link("https://example.com")[Example]'

    def test_link_with_special_chars_in_url(self):
        doc = Document(
            children=[
                Paragraph(
                    children=[
                        Link(
                            url='https://example.com/path?a=1&b="2"',
                            children=[Text(content="Link")],
                        )
                    ]
                )
            ]
        )
        result = generate_typst(doc)
        assert r"\"2\"" in result  # Quotes escaped in URL


class TestImages:
    """Test image generation."""

    def test_simple_image(self):
        doc = Document(
            children=[Paragraph(children=[Image(url="photo.jpg", alt="A photo")])]
        )
        result = generate_typst(doc)
        assert result == '#image("photo.jpg", alt: "A photo")'

    def test_image_without_alt(self):
        doc = Document(children=[Paragraph(children=[Image(url="photo.jpg")])])
        result = generate_typst(doc)
        assert result == '#image("photo.jpg")'


class TestCodeBlocks:
    """Test code block generation."""

    def test_fenced_code_block(self):
        doc = Document(
            children=[
                CodeBlock(code="def hello():\n    print('hi')", language="python")
            ]
        )
        result = generate_typst(doc)
        assert result == "```python\ndef hello():\n    print('hi')\n```"

    def test_code_block_no_language(self):
        doc = Document(children=[CodeBlock(code="some code")])
        result = generate_typst(doc)
        assert result == "```\nsome code\n```"


class TestLists:
    """Test list generation."""

    def test_unordered_list(self):
        doc = Document(
            children=[
                List(
                    ordered=False,
                    items=[
                        ListItem(
                            children=[Paragraph(children=[Text(content="Item 1")])]
                        ),
                        ListItem(
                            children=[Paragraph(children=[Text(content="Item 2")])]
                        ),
                    ],
                )
            ]
        )
        result = generate_typst(doc)
        assert "- Item 1" in result
        assert "- Item 2" in result

    def test_ordered_list(self):
        doc = Document(
            children=[
                List(
                    ordered=True,
                    items=[
                        ListItem(
                            children=[Paragraph(children=[Text(content="First")])]
                        ),
                        ListItem(
                            children=[Paragraph(children=[Text(content="Second")])]
                        ),
                    ],
                )
            ]
        )
        result = generate_typst(doc)
        assert "+ First" in result
        assert "+ Second" in result

    def test_ordered_list_custom_start(self):
        doc = Document(
            children=[
                List(
                    ordered=True,
                    start=5,
                    items=[
                        ListItem(children=[Paragraph(children=[Text(content="Five")])]),
                        ListItem(children=[Paragraph(children=[Text(content="Six")])]),
                    ],
                )
            ]
        )
        result = generate_typst(doc)
        assert "5. Five" in result
        assert "6. Six" in result


class TestBlockQuotes:
    """Test block quote generation."""

    def test_simple_blockquote(self):
        doc = Document(
            children=[
                BlockQuote(children=[Paragraph(children=[Text(content="A quote")])])
            ]
        )
        result = generate_typst(doc)
        assert "#block" in result
        assert "A quote" in result


class TestBreaks:
    """Test break elements."""

    def test_thematic_break(self):
        doc = Document(children=[ThematicBreak()])
        result = generate_typst(doc)
        assert result == "#line(length: 100%)"

    def test_soft_break(self):
        doc = Document(
            children=[
                Paragraph(
                    children=[
                        Text(content="Line 1"),
                        SoftBreak(),
                        Text(content="Line 2"),
                    ]
                )
            ]
        )
        result = generate_typst(doc)
        assert "Line 1\nLine 2" in result

    def test_hard_break(self):
        doc = Document(
            children=[
                Paragraph(
                    children=[
                        Text(content="Line 1"),
                        HardBreak(),
                        Text(content="Line 2"),
                    ]
                )
            ]
        )
        result = generate_typst(doc)
        # Typst uses \\ for hard breaks
        assert "\\" in result
        assert "Line 1" in result
        assert "Line 2" in result


class TestIntegration:
    """Integration tests combining multiple elements."""

    def test_mixed_content(self):
        doc = Document(
            children=[
                Heading(level=1, children=[Text(content="Title")]),
                Paragraph(
                    children=[
                        Text(content="This is "),
                        Strong(children=[Text(content="bold")]),
                        Text(content=" and "),
                        Emphasis(children=[Text(content="italic")]),
                        Text(content="."),
                    ]
                ),
                CodeBlock(code="print('hello')", language="python"),
            ]
        )
        result = generate_typst(doc)
        assert "= Title" in result
        assert "*bold*" in result
        assert "_italic_" in result
        assert "```python" in result


class TestFootnotes:
    """Test footnote generation."""

    def test_simple_footnote(self):
        """Test a simple footnote with reference and definition."""
        doc = Document(
            children=(
                Paragraph(
                    children=(
                        Text(content="Some text"),
                        FootnoteRef(label="1"),
                        Text(content="."),
                    )
                ),
                FootnoteDef(
                    label="1",
                    children=(Paragraph(children=(Text(content="The footnote."),)),),
                ),
            )
        )
        result = generate_typst(doc)
        assert "Some text" in result
        assert "#footnote[The footnote.]" in result
        assert result.endswith(".")

    def test_footnote_with_formatting(self):
        """Test footnote content with inline formatting."""
        doc = Document(
            children=(
                Paragraph(
                    children=(
                        Text(content="Text"),
                        FootnoteRef(label="note"),
                    )
                ),
                FootnoteDef(
                    label="note",
                    children=(
                        Paragraph(
                            children=(
                                Text(content="A "),
                                Strong(children=(Text(content="bold"),)),
                                Text(content=" footnote."),
                            )
                        ),
                    ),
                ),
            )
        )
        result = generate_typst(doc)
        assert "#footnote[A *bold* footnote.]" in result

    def test_multi_paragraph_footnote(self):
        """Test footnote with multiple paragraphs."""
        doc = Document(
            children=(
                Paragraph(
                    children=(
                        Text(content="Text"),
                        FootnoteRef(label="1"),
                    )
                ),
                FootnoteDef(
                    label="1",
                    children=(
                        Paragraph(children=(Text(content="First paragraph."),)),
                        Paragraph(children=(Text(content="Second paragraph."),)),
                    ),
                ),
            )
        )
        result = generate_typst(doc)
        assert "#footnote[First paragraph." in result
        assert "Second paragraph.]" in result

    def test_multiple_footnotes(self):
        """Test document with multiple footnotes."""
        doc = Document(
            children=(
                Paragraph(
                    children=(
                        Text(content="First"),
                        FootnoteRef(label="1"),
                        Text(content=" and second"),
                        FootnoteRef(label="2"),
                        Text(content="."),
                    )
                ),
                FootnoteDef(
                    label="1",
                    children=(Paragraph(children=(Text(content="Note one."),)),),
                ),
                FootnoteDef(
                    label="2",
                    children=(Paragraph(children=(Text(content="Note two."),)),),
                ),
            )
        )
        result = generate_typst(doc)
        assert "#footnote[Note one.]" in result
        assert "#footnote[Note two.]" in result

    def test_unresolved_footnote_ref(self):
        """Test that unresolved footnote refs are preserved as text."""
        doc = Document(
            children=(
                Paragraph(
                    children=(
                        Text(content="Text with missing ref"),
                        FootnoteRef(label="missing"),
                        Text(content="."),
                    )
                ),
            )
        )
        result = generate_typst(doc)
        # Should escape brackets (special chars) but not ^ (not special in Typst)
        assert r"\[^missing\]" in result

    def test_footnote_def_produces_no_output(self):
        """Test that FootnoteDef alone produces no output."""
        doc = Document(
            children=(
                FootnoteDef(
                    label="unused",
                    children=(Paragraph(children=(Text(content="Unused note."),)),),
                ),
            )
        )
        result = generate_typst(doc)
        assert result == ""

    def test_footnote_def_before_ref(self):
        """Test that definition can appear before reference in document."""
        doc = Document(
            children=(
                FootnoteDef(
                    label="1",
                    children=(Paragraph(children=(Text(content="The note."),)),),
                ),
                Paragraph(
                    children=(
                        Text(content="Text"),
                        FootnoteRef(label="1"),
                    )
                ),
            )
        )
        result = generate_typst(doc)
        assert "#footnote[The note.]" in result
        # FootnoteDef should not appear in output directly
        assert result.count("The note.") == 1


class TestEndnotes:
    """Test endnote generation (alternative to footnotes)."""

    def test_simple_endnote(self):
        """Test a simple endnote with reference and definition."""
        doc = Document(
            children=(
                Paragraph(
                    children=(
                        Text(content="Some text"),
                        FootnoteRef(label="1"),
                        Text(content="."),
                    )
                ),
                FootnoteDef(
                    label="1",
                    children=(Paragraph(children=(Text(content="The endnote."),)),),
                ),
            )
        )
        result = generate_typst(doc, note_style="endnote")
        # Should have superscript reference
        assert "#super[1]" in result
        # Should have Notes section at end
        assert "= Notes" in result
        assert "+ The endnote." in result

    def test_multiple_endnotes(self):
        """Test document with multiple endnotes."""
        doc = Document(
            children=(
                Paragraph(
                    children=(
                        Text(content="First"),
                        FootnoteRef(label="a"),
                        Text(content=" and second"),
                        FootnoteRef(label="b"),
                        Text(content="."),
                    )
                ),
                FootnoteDef(
                    label="a",
                    children=(Paragraph(children=(Text(content="Note A."),)),),
                ),
                FootnoteDef(
                    label="b",
                    children=(Paragraph(children=(Text(content="Note B."),)),),
                ),
            )
        )
        result = generate_typst(doc, note_style="endnote")
        # Should have numbered superscripts
        assert "#super[1]" in result
        assert "#super[2]" in result
        # Notes should appear in order
        assert "= Notes" in result
        lines = result.split("\n")
        notes_start = next(i for i, line in enumerate(lines) if "= Notes" in line)
        notes_section = "\n".join(lines[notes_start:])
        assert "+ Note A." in notes_section
        assert "+ Note B." in notes_section

    def test_repeated_endnote_ref(self):
        """Test that repeated references to same note use same number."""
        doc = Document(
            children=(
                Paragraph(
                    children=(
                        Text(content="First ref"),
                        FootnoteRef(label="x"),
                        Text(content=" and again"),
                        FootnoteRef(label="x"),
                        Text(content="."),
                    )
                ),
                FootnoteDef(
                    label="x",
                    children=(Paragraph(children=(Text(content="The note."),)),),
                ),
            )
        )
        result = generate_typst(doc, note_style="endnote")
        # Both refs should have the same number
        assert result.count("#super[1]") == 2
        # Only one note in the Notes section
        assert result.count("+ The note.") == 1

    def test_no_endnotes_no_section(self):
        """Test that documents without notes don't have a Notes section."""
        doc = Document(children=(Paragraph(children=(Text(content="Just text."),)),))
        result = generate_typst(doc, note_style="endnote")
        assert "= Notes" not in result

    def test_footnote_style_default(self):
        """Test that footnote style is the default."""
        doc = Document(
            children=(
                Paragraph(
                    children=(
                        Text(content="Text"),
                        FootnoteRef(label="1"),
                    )
                ),
                FootnoteDef(
                    label="1",
                    children=(Paragraph(children=(Text(content="Note."),)),),
                ),
            )
        )
        result = generate_typst(doc)
        # Default should be footnote style
        assert "#footnote[Note.]" in result
        assert "#super[" not in result


class TestIndexEntries:
    """Test index entry generation."""

    def test_simple_index_entry(self):
        """Test a simple index entry with just a term."""
        doc = Document(
            children=(
                Paragraph(
                    children=(
                        Text(content="The "),
                        IndexEntry(term="Python"),
                        Text(content=" programming language."),
                    )
                ),
            )
        )
        result = generate_typst(doc)
        assert '#index("Python")' in result
        assert "The " in result
        assert " programming language." in result

    def test_index_entry_with_subterm(self):
        """Test index entry with main term and subterm."""
        doc = Document(
            children=(
                Paragraph(
                    children=(
                        IndexEntry(term="Programming", subterm="Functions"),
                        Text(content="Functions are reusable code blocks."),
                    )
                ),
            )
        )
        result = generate_typst(doc)
        assert '#index("Programming", "Functions")' in result

    def test_multiple_index_entries(self):
        """Test document with multiple index entries."""
        doc = Document(
            children=(
                Paragraph(
                    children=(
                        Text(content="Learn about "),
                        IndexEntry(term="Python"),
                        Text(content=" and "),
                        IndexEntry(term="JavaScript"),
                        Text(content="."),
                    )
                ),
            )
        )
        result = generate_typst(doc)
        assert '#index("Python")' in result
        assert '#index("JavaScript")' in result

    def test_index_entry_special_chars(self):
        """Test index entry with special characters in term."""
        doc = Document(
            children=(Paragraph(children=(IndexEntry(term='C++ "Templates"'),)),)
        )
        result = generate_typst(doc)
        # Quotes should be escaped in the Typst string
        assert '#index("C++ \\"Templates\\"")' in result

    def test_index_entry_in_heading(self):
        """Test index entry within a heading."""
        doc = Document(
            children=(
                Heading(
                    level=2,
                    children=(
                        IndexEntry(term="Introduction"),
                        Text(content="Introduction"),
                    ),
                ),
            )
        )
        result = generate_typst(doc)
        assert result.startswith("== ")
        assert '#index("Introduction")' in result
        assert "Introduction" in result


class TestMath:
    """Test math generation."""

    def test_simple_inline_math(self):
        """Test simple inline math expression."""
        doc = Document(
            children=(
                Paragraph(
                    children=(
                        Text(content="The equation "),
                        MathInline(content="E = mc^2"),
                        Text(content=" is famous."),
                    )
                ),
            )
        )
        result = generate_typst(doc)
        assert '#mi("E = mc^2")' in result
        assert "The equation " in result
        assert " is famous." in result

    def test_inline_math_with_special_chars(self):
        """Test inline math with characters that need escaping."""
        doc = Document(
            children=(Paragraph(children=(MathInline(content='x "quoted"'),)),)
        )
        result = generate_typst(doc)
        # Quotes should be escaped in Typst string
        assert '#mi("x \\"quoted\\"")' in result

    def test_simple_block_math(self):
        """Test simple display math."""
        doc = Document(children=(MathBlock(content="\\int_0^\\infty e^{-x^2} dx"),))
        result = generate_typst(doc)
        assert "#mitex(`" in result
        assert "\\int_0^\\infty e^{-x^2} dx" in result
        assert "`)" in result

    def test_block_math_with_backticks(self):
        """Test display math containing backticks."""
        doc = Document(children=(MathBlock(content="x = `code`"),))
        result = generate_typst(doc)
        # Should use double backticks as delimiter
        assert "``" in result

    def test_multiline_block_math(self):
        """Test multiline display math."""
        doc = Document(children=(MathBlock(content="a = b\nc = d"),))
        result = generate_typst(doc)
        assert "#mitex(`a = b\nc = d`)" in result

    def test_math_in_paragraph(self):
        """Test math mixed with text."""
        doc = Document(
            children=(
                Paragraph(
                    children=(
                        Text(content="Given "),
                        MathInline(content="f(x) = x^2"),
                        Text(content=", we have "),
                        MathInline(content="g(x) = 2x"),
                        Text(content="."),
                    )
                ),
            )
        )
        result = generate_typst(doc)
        assert '#mi("f(x) = x^2")' in result
        assert '#mi("g(x) = 2x")' in result


class TestStylesheets:
    """Test stylesheet import generation."""

    def test_no_stylesheets(self):
        """Test generation without stylesheets."""
        doc = Document(children=(Paragraph(children=(Text(content="Hello"),)),))
        result = generate_typst(doc)
        assert not result.startswith("#import")

    def test_single_stylesheet(self):
        """Test single stylesheet import."""
        doc = Document(children=(Paragraph(children=(Text(content="Hello"),)),))
        result = generate_typst(doc, stylesheets=["mystyle"])
        assert '#import "mystyle.typ": *' in result
        assert "Hello" in result

    def test_multiple_stylesheets(self):
        """Test multiple stylesheet imports."""
        doc = Document(children=(Paragraph(children=(Text(content="Hello"),)),))
        result = generate_typst(doc, stylesheets=["style1", "style2", "style3"])

        lines = result.split("\n")
        assert lines[0] == '#import "style1.typ": *'
        assert lines[1] == '#import "style2.typ": *'
        assert lines[2] == '#import "style3.typ": *'

    def test_stylesheet_with_extension_not_duplicated(self):
        """Test that .typ extension is not added if already present."""
        doc = Document(children=(Paragraph(children=(Text(content="Hello"),)),))
        result = generate_typst(doc, stylesheets=["mystyle.typ"])
        assert '#import "mystyle.typ": *' in result
        assert "mystyle.typ.typ" not in result

    def test_stylesheets_before_content(self):
        """Test that imports come before document content."""
        doc = Document(
            children=(
                Heading(level=1, children=(Text(content="Title"),)),
                Paragraph(children=(Text(content="Body"),)),
            )
        )
        result = generate_typst(doc, stylesheets=["styles"])

        import_pos = result.find("#import")
        heading_pos = result.find("= Title")
        assert import_pos < heading_pos

    def test_stylesheets_with_endnotes(self):
        """Test stylesheets work correctly with endnote style."""
        doc = Document(
            children=(
                Paragraph(
                    children=(
                        Text(content="Text"),
                        FootnoteRef(label="1"),
                    )
                ),
                FootnoteDef(
                    label="1",
                    children=(Paragraph(children=(Text(content="Note"),)),),
                ),
            )
        )
        result = generate_typst(doc, note_style="endnote", stylesheets=["styles"])

        # Imports at start
        assert result.startswith('#import "styles.typ": *')
        # Endnotes at end
        assert result.endswith("+ Note")

    def test_empty_stylesheets_list(self):
        """Test that empty stylesheet list produces no imports."""
        doc = Document(children=(Paragraph(children=(Text(content="Hello"),)),))
        result = generate_typst(doc, stylesheets=[])
        assert "#import" not in result
