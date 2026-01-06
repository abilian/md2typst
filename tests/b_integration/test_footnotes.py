"""Tests for footnote parsing and generation."""

from __future__ import annotations

import pytest

from md2typst.ast import (
    Document,
    FootnoteDef,
    FootnoteRef,
    Paragraph,
    Text,
)
from md2typst.generator import generate_typst
from md2typst.parsers import get_parser

pytestmark = pytest.mark.integration


@pytest.fixture
def markdown_it_parser():
    """Create markdown-it parser with footnote plugin."""
    parser = get_parser("markdown-it")
    parser.load_plugin("mdit_py_plugins.footnote")
    return parser


@pytest.fixture
def mistune_parser():
    """Create mistune parser with footnotes plugin."""
    parser = get_parser("mistune")
    parser.load_plugin("footnotes")
    return parser


@pytest.fixture
def marko_parser():
    """Create marko parser with footnote extension."""
    parser = get_parser("marko")
    parser.load_plugin("footnote")
    return parser


class TestMarkdownItFootnotes:
    """Test footnote parsing with markdown-it-py."""

    def test_simple_footnote(self, markdown_it_parser):
        """Test parsing a simple footnote."""
        md = """Text with footnote[^1].

[^1]: This is the footnote."""
        doc = markdown_it_parser.parse(md)

        # Should have paragraph and footnote def
        assert len(doc.children) >= 1

        # Find footnote ref in paragraph
        para = doc.children[0]
        assert isinstance(para, Paragraph)
        refs = [c for c in para.children if isinstance(c, FootnoteRef)]
        assert len(refs) == 1
        assert refs[0].label == "1"

        # Find footnote def
        defs = [c for c in doc.children if isinstance(c, FootnoteDef)]
        assert len(defs) == 1
        assert defs[0].label == "1"

    def test_multiple_footnotes(self, markdown_it_parser):
        """Test parsing multiple footnotes."""
        md = """First[^1] and second[^2].

[^1]: Note one.
[^2]: Note two."""
        doc = markdown_it_parser.parse(md)

        # Find refs
        para = doc.children[0]
        refs = [c for c in para.children if isinstance(c, FootnoteRef)]
        assert len(refs) == 2
        labels = {r.label for r in refs}
        assert labels == {"1", "2"}

        # Find defs
        defs = [c for c in doc.children if isinstance(c, FootnoteDef)]
        assert len(defs) == 2

    def test_named_footnote(self, markdown_it_parser):
        """Test parsing named footnote."""
        md = """Text[^note].

[^note]: Named footnote."""
        doc = markdown_it_parser.parse(md)

        para = doc.children[0]
        refs = [c for c in para.children if isinstance(c, FootnoteRef)]
        assert len(refs) == 1
        assert refs[0].label == "note"

    def test_footnote_generation(self, markdown_it_parser):
        """Test end-to-end footnote conversion."""
        md = """Text[^1].

[^1]: The footnote."""
        doc = markdown_it_parser.parse(md)
        result = generate_typst(doc)

        assert "Text" in result
        assert "#footnote[" in result
        assert "The footnote" in result


class TestMistuneFootnotes:
    """Test footnote parsing with mistune."""

    def test_simple_footnote(self, mistune_parser):
        """Test parsing a simple footnote."""
        md = """Text with footnote[^1].

[^1]: This is the footnote."""
        doc = mistune_parser.parse(md)

        # Should have paragraph and footnote def
        assert len(doc.children) >= 1

        # Find footnote ref in paragraph
        para = doc.children[0]
        assert isinstance(para, Paragraph)
        refs = [c for c in para.children if isinstance(c, FootnoteRef)]
        assert len(refs) == 1

        # Find footnote def
        defs = [c for c in doc.children if isinstance(c, FootnoteDef)]
        assert len(defs) == 1

    def test_footnote_generation(self, mistune_parser):
        """Test end-to-end footnote conversion."""
        md = """Text[^1].

[^1]: The footnote."""
        doc = mistune_parser.parse(md)
        result = generate_typst(doc)

        assert "Text" in result
        assert "#footnote[" in result


class TestMarkoFootnotes:
    """Test footnote parsing with marko."""

    def test_simple_footnote(self, marko_parser):
        """Test parsing a simple footnote."""
        md = """Text with footnote[^1].

[^1]: This is the footnote."""
        doc = marko_parser.parse(md)

        # Should have paragraph and footnote def
        assert len(doc.children) >= 1

        # Find footnote ref in paragraph
        para = doc.children[0]
        assert isinstance(para, Paragraph)
        refs = [c for c in para.children if isinstance(c, FootnoteRef)]
        assert len(refs) == 1

        # Find footnote def
        defs = [c for c in doc.children if isinstance(c, FootnoteDef)]
        assert len(defs) == 1

    def test_footnote_generation(self, marko_parser):
        """Test end-to-end footnote conversion."""
        md = """Text[^1].

[^1]: The footnote."""
        doc = marko_parser.parse(md)
        result = generate_typst(doc)

        assert "Text" in result
        assert "#footnote[" in result


class TestFootnoteGeneration:
    """Test footnote Typst generation."""

    def test_simple_footnote_output(self):
        """Test generated Typst for simple footnote."""
        doc = Document(
            children=(
                Paragraph(
                    children=(
                        Text(content="Text"),
                        FootnoteRef(label="1"),
                        Text(content="."),
                    )
                ),
                FootnoteDef(
                    label="1",
                    children=(Paragraph(children=(Text(content="The note."),)),),
                ),
            )
        )
        result = generate_typst(doc)

        assert result == "Text#footnote[The note.]."

    def test_multiple_footnotes_output(self):
        """Test generated Typst for multiple footnotes."""
        doc = Document(
            children=(
                Paragraph(
                    children=(
                        Text(content="First"),
                        FootnoteRef(label="1"),
                        Text(content=" second"),
                        FootnoteRef(label="2"),
                    )
                ),
                FootnoteDef(
                    label="1",
                    children=(Paragraph(children=(Text(content="Note 1."),)),),
                ),
                FootnoteDef(
                    label="2",
                    children=(Paragraph(children=(Text(content="Note 2."),)),),
                ),
            )
        )
        result = generate_typst(doc)

        assert "#footnote[Note 1.]" in result
        assert "#footnote[Note 2.]" in result
