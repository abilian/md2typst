"""Tests for GFM extensions (tables, strikethrough)."""

from __future__ import annotations

import pytest

from md2typst import convert
from md2typst.ast import (
    Document,
    Paragraph,
    Strikethrough,
    Strong,
    Table,
    TableCell,
    Text,
)
from md2typst.generator import generate_typst
from md2typst.parsers import get_parser

pytestmark = pytest.mark.integration

# All available parsers for parametrized tests
ALL_PARSERS = ["markdown-it", "mistune", "marko"]


@pytest.fixture(params=ALL_PARSERS)
def parser(request):
    """Fixture that yields each parser in turn."""
    return get_parser(request.param)


class TestStrikethrough:
    """Test strikethrough parsing and generation."""

    def test_strikethrough_parsing(self, parser):
        """Test that all parsers correctly parse strikethrough."""
        doc = parser.parse("~~deleted~~")
        assert len(doc.children) == 1
        para = doc.children[0]
        assert isinstance(para, Paragraph)
        # Find strikethrough node
        strike_nodes = [c for c in para.children if isinstance(c, Strikethrough)]
        assert len(strike_nodes) == 1
        strike = strike_nodes[0]
        # Should have text content
        text_content = "".join(
            c.content for c in strike.children if isinstance(c, Text)
        )
        assert "deleted" in text_content

    def test_strikethrough_with_formatting(self, parser):
        """Test strikethrough with nested formatting."""
        doc = parser.parse("~~**bold deleted**~~")
        para = doc.children[0]
        strike_nodes = [c for c in para.children if isinstance(c, Strikethrough)]
        assert len(strike_nodes) >= 1

    def test_strikethrough_generation(self):
        """Test that strikethrough generates correct Typst."""
        doc = Document(
            children=[
                Paragraph(children=[Strikethrough(children=[Text(content="deleted")])])
            ]
        )
        result = generate_typst(doc)
        assert result == "#strike[deleted]"

    def test_strikethrough_end_to_end(self, parser):
        """Test full conversion of strikethrough."""
        result = convert("~~deleted text~~", parser=parser.name)
        assert "#strike[" in result
        assert "deleted text" in result


class TestTables:
    """Test table parsing and generation."""

    def test_simple_table_parsing(self, parser):
        """Test that all parsers correctly parse simple tables."""
        md = """| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |"""
        doc = parser.parse(md)

        # Find table node
        table_nodes = [c for c in doc.children if isinstance(c, Table)]
        assert len(table_nodes) == 1
        table = table_nodes[0]

        # Check header
        assert len(table.header) == 2
        header_text = [
            "".join(c.content for c in cell.children if isinstance(c, Text))
            for cell in table.header
        ]
        assert "Header 1" in header_text[0]
        assert "Header 2" in header_text[1]

        # Check body
        assert len(table.rows) == 1
        assert len(table.rows[0]) == 2

    def test_table_with_alignment(self, parser):
        """Test tables with column alignment."""
        md = """| Left | Center | Right |
|:-----|:------:|------:|
| L    | C      | R     |"""
        doc = parser.parse(md)

        table_nodes = [c for c in doc.children if isinstance(c, Table)]
        assert len(table_nodes) == 1
        table = table_nodes[0]

        # Check alignments
        assert len(table.alignments) == 3
        assert table.alignments[0] == "left"
        assert table.alignments[1] == "center"
        assert table.alignments[2] == "right"

    def test_table_with_multiple_rows(self, parser):
        """Test tables with multiple body rows."""
        md = """| A | B |
|---|---|
| 1 | 2 |
| 3 | 4 |
| 5 | 6 |"""
        doc = parser.parse(md)

        table_nodes = [c for c in doc.children if isinstance(c, Table)]
        assert len(table_nodes) == 1
        table = table_nodes[0]

        assert len(table.rows) == 3

    def test_table_with_formatting(self, parser):
        """Test tables with formatted content."""
        md = """| Header |
|--------|
| **bold** |"""
        doc = parser.parse(md)

        table_nodes = [c for c in doc.children if isinstance(c, Table)]
        assert len(table_nodes) == 1
        table = table_nodes[0]

        # Body cell should contain Strong
        cell = table.rows[0][0]
        strong_nodes = [c for c in cell.children if isinstance(c, Strong)]
        assert len(strong_nodes) >= 1

    def test_table_generation(self):
        """Test that tables generate correct Typst."""
        table = Table(
            header=[
                TableCell(children=[Text(content="Header 1")]),
                TableCell(children=[Text(content="Header 2")]),
            ],
            rows=[
                [
                    TableCell(children=[Text(content="Cell 1")]),
                    TableCell(children=[Text(content="Cell 2")]),
                ]
            ],
            alignments=[None, None],
        )
        doc = Document(children=[table])
        result = generate_typst(doc)

        assert "#table(" in result
        assert "Header 1" in result
        assert "Header 2" in result
        assert "Cell 1" in result
        assert "Cell 2" in result
        # Verify correct table.header format (all headers in one call)
        assert "table.header([Header 1], [Header 2])" in result

    def test_table_generation_with_alignment(self):
        """Test table generation with column alignment."""
        table = Table(
            header=[
                TableCell(children=[Text(content="Left")]),
                TableCell(children=[Text(content="Center")]),
                TableCell(children=[Text(content="Right")]),
            ],
            rows=[],
            alignments=["left", "center", "right"],
        )
        doc = Document(children=[table])
        result = generate_typst(doc)

        assert "columns: (left, center, right)" in result

    def test_table_end_to_end(self, parser):
        """Test full conversion of tables."""
        md = """| Name | Age |
|------|-----|
| Alice | 30 |
| Bob   | 25 |"""
        result = convert(md, parser=parser.name)

        assert "#table(" in result
        assert "Name" in result
        assert "Age" in result
        assert "Alice" in result
        assert "Bob" in result


class TestGFMCombined:
    """Test combined GFM features."""

    def test_strikethrough_in_table(self, parser):
        """Test strikethrough inside table cells."""
        md = """| Status |
|--------|
| ~~done~~ |"""
        doc = parser.parse(md)

        table_nodes = [c for c in doc.children if isinstance(c, Table)]
        assert len(table_nodes) == 1
        table = table_nodes[0]

        # Cell should contain strikethrough
        cell = table.rows[0][0]
        strike_nodes = [c for c in cell.children if isinstance(c, Strikethrough)]
        assert len(strike_nodes) >= 1

    def test_complex_document(self, parser):
        """Test document with multiple GFM features."""
        md = """# GFM Features

This text has ~~strikethrough~~ and **bold**.

| Feature | Status |
|---------|--------|
| Tables | Done |
| Strikethrough | Done |
"""
        doc = parser.parse(md)

        # Should have heading, paragraph, and table
        assert len(doc.children) >= 3

        # Find strikethrough
        para = doc.children[1]
        strike_nodes = [c for c in para.children if isinstance(c, Strikethrough)]
        assert len(strike_nodes) >= 1

        # Find table
        table_nodes = [c for c in doc.children if isinstance(c, Table)]
        assert len(table_nodes) == 1
