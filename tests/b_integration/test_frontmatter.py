"""Tests for YAML front matter extraction and generation."""

from __future__ import annotations

import pytest

from md2typst import convert
from md2typst.frontmatter import extract_frontmatter
from md2typst.parsers import get_parser

pytestmark = pytest.mark.integration


class TestFrontmatterExtraction:
    """Test the extract_frontmatter function."""

    def test_extract_simple_metadata(self):
        """Test extracting simple key-value pairs."""
        text = """---
title: Test Document
author: John Doe
---

# Content here"""
        metadata, remaining = extract_frontmatter(text)
        assert metadata["title"] == "Test Document"
        assert metadata["author"] == "John Doe"
        assert remaining.strip().startswith("# Content")

    def test_extract_with_quotes(self):
        """Test extracting quoted values."""
        text = """---
title: "Document with: colon"
subtitle: 'Single quotes work too'
---

Content"""
        metadata, remaining = extract_frontmatter(text)
        assert metadata["title"] == "Document with: colon"
        assert metadata["subtitle"] == "Single quotes work too"

    def test_extract_list_values(self):
        """Test extracting list values."""
        text = """---
keywords:
  - python
  - markdown
  - typst
---

Content"""
        metadata, remaining = extract_frontmatter(text)
        assert metadata["keywords"] == ["python", "markdown", "typst"]

    def test_extract_nested_values(self):
        """Test extracting nested values."""
        text = """---
author:
  name: John Doe
  email: john@example.com
---

Content"""
        metadata, remaining = extract_frontmatter(text)
        assert metadata["author"]["name"] == "John Doe"
        assert metadata["author"]["email"] == "john@example.com"

    def test_no_frontmatter(self):
        """Test handling documents without front matter."""
        text = "# No metadata\n\nJust content"
        metadata, remaining = extract_frontmatter(text)
        assert metadata == {}
        assert remaining == text

    def test_frontmatter_not_at_start(self):
        """Test that front matter must be at the start."""
        text = """Some text first

---
title: Not valid
---

Content"""
        metadata, remaining = extract_frontmatter(text)
        assert metadata == {}
        assert remaining == text

    def test_empty_frontmatter(self):
        """Test handling empty front matter block."""
        text = """---
---

Content"""
        metadata, remaining = extract_frontmatter(text)
        assert metadata == {}
        assert remaining.strip() == "Content"

    def test_invalid_yaml(self):
        """Test handling invalid YAML gracefully."""
        text = """---
title: [unclosed bracket
---

Content"""
        metadata, remaining = extract_frontmatter(text)
        # Should return empty metadata and original text on parse error
        assert metadata == {}
        assert remaining == text


class TestFrontmatterInParsers:
    """Test front matter extraction in each parser."""

    @pytest.mark.parametrize("parser_name", ["markdown-it", "mistune", "marko"])
    def test_parser_extracts_metadata(self, parser_name):
        """Test that all parsers extract front matter."""
        text = """---
title: Parser Test
version: 1
---

# Hello"""
        parser = get_parser(parser_name)
        doc = parser.parse(text)

        assert doc.metadata["title"] == "Parser Test"
        assert doc.metadata["version"] == 1
        assert len(doc.children) > 0

    @pytest.mark.parametrize("parser_name", ["markdown-it", "mistune", "marko"])
    def test_parser_without_frontmatter(self, parser_name):
        """Test parsers handle documents without front matter."""
        text = "# Just Content\n\nNo metadata here."
        parser = get_parser(parser_name)
        doc = parser.parse(text)

        assert doc.metadata == {}
        assert len(doc.children) > 0


class TestFrontmatterGeneration:
    """Test Typst variable generation from front matter."""

    def test_generate_string_variable(self):
        """Test generating string variables."""
        markdown = """---
title: My Document
---

# Hello"""
        result = convert(markdown)
        assert '#let doc-title = "My Document"' in result
        assert "= Hello" in result

    def test_generate_number_variables(self):
        """Test generating number variables."""
        markdown = """---
version: 42
price: 19.99
---

Content"""
        result = convert(markdown)
        assert "#let doc-version = 42" in result
        assert "#let doc-price = 19.99" in result

    def test_generate_boolean_variables(self):
        """Test generating boolean variables."""
        markdown = """---
draft: true
published: false
---

Content"""
        result = convert(markdown)
        assert "#let doc-draft = true" in result
        assert "#let doc-published = false" in result

    def test_generate_list_variable(self):
        """Test generating list/array variables."""
        markdown = """---
tags:
  - python
  - typst
---

Content"""
        result = convert(markdown)
        assert '#let doc-tags = ("python", "typst",)' in result

    def test_escape_special_characters(self):
        """Test escaping special characters in strings."""
        markdown = """---
title: 'Document with "quotes" and \\backslash'
---

Content"""
        result = convert(markdown)
        assert 'doc-title = "Document with \\"quotes\\" and \\\\backslash"' in result

    def test_frontmatter_before_stylesheet(self):
        """Test that front matter comes before stylesheet imports."""
        markdown = """---
title: Test
---

# Content"""
        result = convert(markdown, stylesheets=["mystyle"])

        # Find positions
        title_pos = result.find("#let doc-title")
        import_pos = result.find("#import")

        assert title_pos < import_pos, "Front matter should come before imports"

    def test_key_with_underscores(self):
        """Test that underscores in keys are converted to hyphens."""
        markdown = """---
document_title: Test
---

Content"""
        result = convert(markdown)
        assert "#let doc-document-title" in result

    def test_no_frontmatter_no_variables(self):
        """Test that no variables are generated without front matter."""
        markdown = "# Just content\n\nNo metadata"
        result = convert(markdown)
        assert "#let doc-" not in result


class TestFrontmatterIntegration:
    """Integration tests for the complete front matter workflow."""

    def test_full_document_with_metadata(self):
        """Test a complete document with metadata and stylesheet."""
        markdown = """---
title: "Technical Proposal"
author: "Abilian SAS"
date: "February 2026"
version: 1.0
draft: false
---

# Introduction

This is the introduction.

## Section 1

Content here.
"""
        result = convert(markdown, stylesheets=["proposal-style"])

        # Check front matter variables
        assert '#let doc-title = "Technical Proposal"' in result
        assert '#let doc-author = "Abilian SAS"' in result
        assert '#let doc-date = "February 2026"' in result
        assert "#let doc-version = 1.0" in result
        assert "#let doc-draft = false" in result

        # Check stylesheet import
        assert '#import "proposal-style.typ": *' in result

        # Check content
        assert "= Introduction" in result
        assert "== Section 1" in result

    def test_frontmatter_with_french_content(self):
        """Test front matter with French characters."""
        markdown = """---
title: "Proposition Technique et Financière"
client: "Académie des Sciences"
---

## Présentation

Contenu avec des accents: é, è, à, ù.
"""
        result = convert(markdown)
        assert "Proposition Technique et Financière" in result
        assert "Académie des Sciences" in result

    def test_preamble_in_frontmatter(self):
        """Test that preamble is output as raw Typst code."""
        markdown = """---
title: My Document
preamble: |
  #cover-page(doc-title)
  #toc-page()
---

# Content
"""
        result = convert(markdown)
        # Preamble should be present as raw code
        assert "#cover-page(doc-title)" in result
        assert "#toc-page()" in result
        # Preamble should NOT be converted to a variable
        assert "doc-preamble" not in result
        # Title should still be a variable
        assert '#let doc-title = "My Document"' in result

    def test_stylesheet_in_frontmatter(self):
        """Test that stylesheet in front matter is imported."""
        markdown = """---
title: Test
stylesheet: my-style
---

Content
"""
        result = convert(markdown)
        assert '#import "my-style.typ": *' in result

    def test_stylesheets_list_in_frontmatter(self):
        """Test multiple stylesheets in front matter."""
        markdown = """---
title: Test
stylesheets:
  - style1
  - style2
---

Content
"""
        result = convert(markdown)
        assert '#import "style1.typ": *' in result
        assert '#import "style2.typ": *' in result

    def test_stylesheet_and_preamble_order(self):
        """Test that order is: variables, imports, preamble, content."""
        markdown = """---
title: Test
stylesheet: my-style
preamble: |
  #setup()
---

# Hello
"""
        result = convert(markdown)
        # Find positions
        var_pos = result.find("#let doc-title")
        import_pos = result.find("#import")
        preamble_pos = result.find("#setup()")
        content_pos = result.find("= Hello")

        assert var_pos < import_pos, "Variables should come before imports"
        assert import_pos < preamble_pos, "Imports should come before preamble"
        assert preamble_pos < content_pos, "Preamble should come before content"

    def test_stylesheet_frontmatter_merged_with_config(self):
        """Test that front matter stylesheets are merged with config."""
        markdown = """---
title: Test
stylesheet: fm-style
---

Content
"""
        # Config stylesheet + front matter stylesheet
        result = convert(markdown, stylesheets=["config-style"])
        assert '#import "config-style.typ": *' in result
        assert '#import "fm-style.typ": *' in result
