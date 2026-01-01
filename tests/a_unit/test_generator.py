"""Tests for the Typst generator."""

from __future__ import annotations

import pytest

from mkd2typst.ast import (
    BlockQuote,
    Code,
    CodeBlock,
    Document,
    Emphasis,
    HardBreak,
    Heading,
    Image,
    Link,
    List,
    ListItem,
    Paragraph,
    SoftBreak,
    Strikethrough,
    Strong,
    Text,
    ThematicBreak,
)
from mkd2typst.generator import escape_typst, generate_typst

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
