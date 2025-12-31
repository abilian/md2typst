"""Tests for AST node definitions."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

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
    Strong,
    Text,
    ThematicBreak,
)


class TestNodeStr:
    """Test __str__ methods for debugging."""

    def test_document_str(self):
        doc = Document(children=[Paragraph(), Paragraph()])
        assert "2 children" in str(doc)

    def test_paragraph_str(self):
        p = Paragraph(children=[Text(content="hello")])
        assert "1 children" in str(p)

    def test_heading_str(self):
        h = Heading(level=2, children=[Text(content="Title")])
        assert "level=2" in str(h)

    def test_code_block_str(self):
        cb = CodeBlock(code="print('hi')\nprint('bye')", language="python")
        assert "python" in str(cb)
        assert "2 lines" in str(cb)

    def test_text_str(self):
        t = Text(content="short")
        assert "short" in str(t)

        long_text = Text(content="a" * 50)
        assert "..." in str(long_text)

    def test_link_str(self):
        link = Link(url="https://example.com", children=[Text(content="Example")])
        assert "https://example.com" in str(link)

    def test_image_str(self):
        img = Image(url="image.png", alt="An image")
        assert "image.png" in str(img)


class TestNodeConstruction:
    """Test that nodes can be constructed properly."""

    def test_document_with_children(self):
        doc = Document(
            children=[
                Paragraph(children=[Text(content="Hello")]),
                Heading(level=1, children=[Text(content="Title")]),
            ]
        )
        assert len(doc.children) == 2
        assert isinstance(doc.children[0], Paragraph)
        assert isinstance(doc.children[1], Heading)

    def test_nested_emphasis(self):
        # *_italic bold_*
        node = Strong(children=[Emphasis(children=[Text(content="italic bold")])])
        assert isinstance(node.children[0], Emphasis)
        assert isinstance(node.children[0].children[0], Text)

    def test_list_construction(self):
        lst = List(
            ordered=True,
            start=5,
            items=[
                ListItem(children=[Paragraph(children=[Text(content="Item 5")])]),
                ListItem(children=[Paragraph(children=[Text(content="Item 6")])]),
            ],
        )
        assert lst.ordered is True
        assert lst.start == 5
        assert len(lst.items) == 2

    def test_link_with_title(self):
        link = Link(
            url="https://example.com",
            title="Example Site",
            children=[Text(content="Click here")],
        )
        assert link.url == "https://example.com"
        assert link.title == "Example Site"

    def test_code_block_without_language(self):
        cb = CodeBlock(code="some code")
        assert cb.language is None
        assert cb.code == "some code"

    def test_thematic_break(self):
        tb = ThematicBreak()
        assert str(tb) == "ThematicBreak()"

    def test_breaks(self):
        soft = SoftBreak()
        hard = HardBreak()
        assert str(soft) == "SoftBreak()"
        assert str(hard) == "HardBreak()"

    def test_blockquote(self):
        bq = BlockQuote(children=[Paragraph(children=[Text(content="A quote")])])
        assert len(bq.children) == 1

    def test_inline_code(self):
        code = Code(content="x = 1")
        assert code.content == "x = 1"
