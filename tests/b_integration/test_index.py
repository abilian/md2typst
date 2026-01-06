"""Integration tests for index entry parsing and generation."""

from __future__ import annotations

import pytest

from md2typst.ast import IndexEntry
from md2typst.generator import generate_typst

pytestmark = pytest.mark.integration


class TestMarkdownItIndexEntries:
    """Test index entry parsing with markdown-it-py parser."""

    @pytest.fixture
    def parser(self):
        """Create a markdown-it parser with attrs plugin enabled."""
        from md2typst.parsers.markdown_it import MarkdownItParser

        p = MarkdownItParser()
        p.load_plugin("mdit_py_plugins.attrs")
        return p

    def test_simple_index_entry(self, parser):
        """Test parsing a simple index entry."""
        doc = parser.parse("The [Python]{.index} programming language.")

        # Find the index entry
        para = doc.children[0]
        index_entries = [c for c in para.children if isinstance(c, IndexEntry)]
        assert len(index_entries) == 1
        assert index_entries[0].term == "Python"
        assert index_entries[0].subterm is None

    def test_index_entry_with_key(self, parser):
        """Test parsing an index entry with explicit key (term override)."""
        doc = parser.parse('[functions]{.index key="Programming"}')

        para = doc.children[0]
        index_entries = [c for c in para.children if isinstance(c, IndexEntry)]
        assert len(index_entries) == 1
        assert index_entries[0].term == "Programming"

    def test_index_entry_with_subterm(self, parser):
        """Test parsing a hierarchical index entry."""
        doc = parser.parse('[functions]{.index key="Programming!Functions"}')

        para = doc.children[0]
        index_entries = [c for c in para.children if isinstance(c, IndexEntry)]
        assert len(index_entries) == 1
        assert index_entries[0].term == "Programming"
        assert index_entries[0].subterm == "Functions"

    def test_multiple_index_entries(self, parser):
        """Test parsing multiple index entries in one document."""
        doc = parser.parse("Learn [Python]{.index} and [JavaScript]{.index}.")

        para = doc.children[0]
        index_entries = [c for c in para.children if isinstance(c, IndexEntry)]
        assert len(index_entries) == 2
        assert index_entries[0].term == "Python"
        assert index_entries[1].term == "JavaScript"

    def test_index_entry_roundtrip(self, parser):
        """Test full conversion from Markdown to Typst."""
        doc = parser.parse("The [Python]{.index} language.")
        result = generate_typst(doc)
        assert '#index("Python")' in result
        assert "The " in result
        assert " language." in result

    def test_index_entry_with_subterm_roundtrip(self, parser):
        """Test hierarchical index entry conversion."""
        doc = parser.parse('[OOP]{.index key="Programming!OOP"}')
        result = generate_typst(doc)
        assert '#index("Programming", "OOP")' in result


class TestIndexEntryWithoutPlugin:
    """Test that index syntax is ignored without the attrs plugin."""

    def test_index_syntax_without_plugin(self):
        """Without attrs plugin, index syntax should remain as plain text."""
        from md2typst.parsers.markdown_it import MarkdownItParser

        parser = MarkdownItParser()
        # No attrs plugin loaded
        doc = parser.parse("The [Python]{.index} language.")

        # Should be treated as literal text
        result = generate_typst(doc)
        # The syntax should be present as literal text (or partially parsed)
        assert "Python" in result
