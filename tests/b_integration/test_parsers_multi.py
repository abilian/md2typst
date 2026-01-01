"""Tests for all parser adapters.

This module tests that all parsers produce consistent AST output
for the same Markdown input.
"""

from __future__ import annotations

import pytest

from mkd2typst.ast import (
    BlockQuote,
    Code,
    CodeBlock,
    Document,
    Emphasis,
    Heading,
    Image,
    Link,
    List,
    Paragraph,
    Strong,
    Text,
    ThematicBreak,
)
from mkd2typst.parsers import get_parser, list_parsers

pytestmark = pytest.mark.integration

# All available parsers for parametrized tests
ALL_PARSERS = ["markdown-it", "mistune", "marko"]


@pytest.fixture(params=ALL_PARSERS)
def parser(request):
    """Fixture that yields each parser in turn."""
    return get_parser(request.param)


class TestParserRegistry:
    """Test that all parsers are registered."""

    def test_all_parsers_available(self):
        available = list_parsers()
        for parser_name in ALL_PARSERS:
            assert parser_name in available

    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_get_parser_by_name(self, parser_name):
        parser = get_parser(parser_name)
        assert parser is not None
        assert parser.name in [
            parser_name,
            "markdown-it-py",
        ]  # markdown-it returns markdown-it-py


class TestBasicParsing:
    """Test basic parsing functionality across all parsers."""

    def test_empty_input(self, parser):
        doc = parser.parse("")
        assert isinstance(doc, Document)
        assert len(doc.children) == 0

    def test_simple_paragraph(self, parser):
        doc = parser.parse("Hello world")
        assert len(doc.children) == 1
        assert isinstance(doc.children[0], Paragraph)
        para = doc.children[0]
        assert len(para.children) >= 1
        # First child should be text
        assert isinstance(para.children[0], Text)
        assert "Hello world" in para.children[0].content

    def test_multiple_paragraphs(self, parser):
        doc = parser.parse("First paragraph.\n\nSecond paragraph.")
        assert len(doc.children) == 2
        assert all(isinstance(c, Paragraph) for c in doc.children)


class TestHeadings:
    """Test heading parsing across all parsers."""

    @pytest.mark.parametrize("level", [1, 2, 3, 4, 5, 6])
    def test_heading_levels(self, parser, level):
        md = "#" * level + " Heading"
        doc = parser.parse(md)
        assert len(doc.children) == 1
        heading = doc.children[0]
        assert isinstance(heading, Heading)
        assert heading.level == level

    def test_heading_with_text(self, parser):
        doc = parser.parse("# Title Here")
        heading = doc.children[0]
        assert isinstance(heading, Heading)
        # Should have text content
        assert len(heading.children) >= 1
        text_content = "".join(
            c.content for c in heading.children if isinstance(c, Text)
        )
        assert "Title Here" in text_content


class TestInlineFormatting:
    """Test inline formatting across all parsers."""

    def test_emphasis(self, parser):
        doc = parser.parse("This is *emphasized* text.")
        para = doc.children[0]
        assert any(isinstance(c, Emphasis) for c in para.children)

    def test_strong(self, parser):
        doc = parser.parse("This is **bold** text.")
        para = doc.children[0]
        assert any(isinstance(c, Strong) for c in para.children)

    def test_inline_code(self, parser):
        doc = parser.parse("Use `code` here.")
        para = doc.children[0]
        code_nodes = [c for c in para.children if isinstance(c, Code)]
        assert len(code_nodes) >= 1
        assert code_nodes[0].content == "code"


class TestCodeBlocks:
    """Test code block parsing across all parsers."""

    def test_fenced_code_block(self, parser):
        md = "```python\nprint('hello')\n```"
        doc = parser.parse(md)
        assert len(doc.children) == 1
        cb = doc.children[0]
        assert isinstance(cb, CodeBlock)
        assert cb.language == "python"
        assert "print" in cb.code

    def test_fenced_code_block_no_language(self, parser):
        md = "```\nsome code\n```"
        doc = parser.parse(md)
        cb = doc.children[0]
        assert isinstance(cb, CodeBlock)
        assert cb.language is None or cb.language == ""


class TestLinks:
    """Test link parsing across all parsers."""

    def test_simple_link(self, parser):
        doc = parser.parse("[Example](https://example.com)")
        para = doc.children[0]
        link = para.children[0]
        assert isinstance(link, Link)
        assert link.url == "https://example.com"

    def test_link_text(self, parser):
        doc = parser.parse("[Click here](https://example.com)")
        para = doc.children[0]
        link = para.children[0]
        assert isinstance(link, Link)
        # Should have text children
        text_content = "".join(c.content for c in link.children if isinstance(c, Text))
        assert "Click here" in text_content


class TestImages:
    """Test image parsing across all parsers."""

    def test_simple_image(self, parser):
        doc = parser.parse("![Alt text](image.png)")
        para = doc.children[0]
        img = para.children[0]
        assert isinstance(img, Image)
        assert img.url == "image.png"
        assert img.alt == "Alt text"


class TestLists:
    """Test list parsing across all parsers."""

    def test_unordered_list(self, parser):
        md = "- Item 1\n- Item 2\n- Item 3"
        doc = parser.parse(md)
        assert len(doc.children) == 1
        lst = doc.children[0]
        assert isinstance(lst, List)
        assert lst.ordered is False
        assert len(lst.items) == 3

    def test_ordered_list(self, parser):
        md = "1. First\n2. Second\n3. Third"
        doc = parser.parse(md)
        lst = doc.children[0]
        assert isinstance(lst, List)
        assert lst.ordered is True
        assert len(lst.items) == 3


class TestBlockQuotes:
    """Test block quote parsing across all parsers."""

    def test_simple_blockquote(self, parser):
        doc = parser.parse("> This is a quote")
        assert len(doc.children) == 1
        bq = doc.children[0]
        assert isinstance(bq, BlockQuote)
        assert len(bq.children) >= 1


class TestThematicBreak:
    """Test thematic break parsing across all parsers."""

    def test_thematic_break(self, parser):
        doc = parser.parse("---")
        assert len(doc.children) == 1
        assert isinstance(doc.children[0], ThematicBreak)

    def test_thematic_break_asterisks(self, parser):
        doc = parser.parse("***")
        assert len(doc.children) == 1
        assert isinstance(doc.children[0], ThematicBreak)


class TestComplexDocuments:
    """Test parsing of complex documents across all parsers."""

    def test_mixed_content(self, parser):
        md = """# Title

This is a paragraph with **bold** and *italic* text.

## Code Example

```python
def hello():
    print("Hello!")
```

- Item 1
- Item 2

> A blockquote

---

[Link](https://example.com)
"""
        doc = parser.parse(md)

        # Should have multiple block elements
        assert len(doc.children) >= 6

        # Verify key elements exist
        headings = [c for c in doc.children if isinstance(c, Heading)]
        assert len(headings) >= 2

        code_blocks = [c for c in doc.children if isinstance(c, CodeBlock)]
        assert len(code_blocks) >= 1

        lists = [c for c in doc.children if isinstance(c, List)]
        assert len(lists) >= 1

        quotes = [c for c in doc.children if isinstance(c, BlockQuote)]
        assert len(quotes) >= 1
