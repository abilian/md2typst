"""Tests for the markdown-it-py parser adapter."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

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
from mkd2typst.parsers.markdown_it import MarkdownItParser


class TestParserRegistry:
    """Test parser registry functions."""

    def test_list_parsers(self):
        parsers = list_parsers()
        assert "markdown-it" in parsers

    def test_get_default_parser(self):
        parser = get_parser()
        assert parser is not None
        assert parser.name == "markdown-it-py"

    def test_get_parser_by_name(self):
        parser = get_parser("markdown-it")
        assert parser.name == "markdown-it-py"

    def test_get_unknown_parser(self):
        with pytest.raises(ValueError, match="Unknown parser"):
            get_parser("nonexistent-parser")


class TestMarkdownItParser:
    """Test the markdown-it-py parser adapter."""

    @pytest.fixture
    def parser(self):
        return MarkdownItParser()

    def test_parser_name(self, parser):
        assert parser.name == "markdown-it-py"

    def test_empty_input(self, parser):
        doc = parser.parse("")
        assert isinstance(doc, Document)
        assert len(doc.children) == 0

    def test_simple_paragraph(self, parser):
        doc = parser.parse("Hello world")
        assert len(doc.children) == 1
        assert isinstance(doc.children[0], Paragraph)
        para = doc.children[0]
        assert len(para.children) == 1
        assert isinstance(para.children[0], Text)
        assert para.children[0].content == "Hello world"

    def test_multiple_paragraphs(self, parser):
        doc = parser.parse("First paragraph.\n\nSecond paragraph.")
        assert len(doc.children) == 2
        assert all(isinstance(c, Paragraph) for c in doc.children)

    def test_heading_atx(self, parser):
        doc = parser.parse("# Heading 1\n\n## Heading 2")
        assert len(doc.children) == 2
        h1, h2 = doc.children
        assert isinstance(h1, Heading) and h1.level == 1
        assert isinstance(h2, Heading) and h2.level == 2

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
        assert any(isinstance(c, Code) for c in para.children)
        code_node = next(c for c in para.children if isinstance(c, Code))
        assert code_node.content == "code"

    def test_fenced_code_block(self, parser):
        doc = parser.parse("```python\nprint('hello')\n```")
        assert len(doc.children) == 1
        cb = doc.children[0]
        assert isinstance(cb, CodeBlock)
        assert cb.language == "python"
        assert "print" in cb.code

    def test_code_block_no_language(self, parser):
        doc = parser.parse("```\nsome code\n```")
        cb = doc.children[0]
        assert isinstance(cb, CodeBlock)
        assert cb.language is None or cb.language == ""

    def test_link(self, parser):
        doc = parser.parse("[Example](https://example.com)")
        para = doc.children[0]
        link = para.children[0]
        assert isinstance(link, Link)
        assert link.url == "https://example.com"
        assert isinstance(link.children[0], Text)
        assert link.children[0].content == "Example"

    def test_image(self, parser):
        doc = parser.parse("![Alt text](image.png)")
        para = doc.children[0]
        img = para.children[0]
        assert isinstance(img, Image)
        assert img.url == "image.png"
        assert img.alt == "Alt text"

    def test_unordered_list(self, parser):
        doc = parser.parse("- Item 1\n- Item 2\n- Item 3")
        assert len(doc.children) == 1
        lst = doc.children[0]
        assert isinstance(lst, List)
        assert lst.ordered is False
        assert len(lst.items) == 3

    def test_ordered_list(self, parser):
        doc = parser.parse("1. First\n2. Second\n3. Third")
        lst = doc.children[0]
        assert isinstance(lst, List)
        assert lst.ordered is True
        assert len(lst.items) == 3

    def test_blockquote(self, parser):
        doc = parser.parse("> This is a quote")
        assert len(doc.children) == 1
        bq = doc.children[0]
        assert isinstance(bq, BlockQuote)
        assert len(bq.children) >= 1

    def test_thematic_break(self, parser):
        doc = parser.parse("---")
        assert len(doc.children) == 1
        assert isinstance(doc.children[0], ThematicBreak)

    def test_nested_list(self, parser):
        md = """- Item 1
  - Nested 1
  - Nested 2
- Item 2"""
        doc = parser.parse(md)
        lst = doc.children[0]
        assert isinstance(lst, List)
        # First item should contain a nested list
        first_item = lst.items[0]
        assert any(isinstance(c, List) for c in first_item.children)

    def test_complex_document(self, parser):
        md = """# Title

This is a paragraph with **bold** and *italic* text.

## Code Example

```python
def hello():
    print("Hello, World!")
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

        # Check types in order
        assert isinstance(doc.children[0], Heading)
        assert isinstance(doc.children[1], Paragraph)
        assert isinstance(doc.children[2], Heading)
        assert isinstance(doc.children[3], CodeBlock)
