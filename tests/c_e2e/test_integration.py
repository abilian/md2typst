"""End-to-end integration tests."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.e2e

from mkd2typst import convert


class TestConvert:
    """Test the high-level convert function."""

    def test_simple_conversion(self):
        md = "Hello, **world**!"
        result = convert(md)
        assert "Hello" in result
        assert "*world*" in result  # Bold in Typst

    def test_heading_conversion(self):
        md = "# Title\n\nContent here."
        result = convert(md)
        assert "= Title" in result
        assert "Content here" in result

    def test_emphasis_mapping(self):
        """Verify Markdown emphasis maps to correct Typst syntax."""
        # Markdown *text* -> Typst _text_
        result = convert("*italic*")
        assert "_italic_" in result

        # Markdown **text** -> Typst *text*
        result = convert("**bold**")
        assert "*bold*" in result

    def test_link_conversion(self):
        md = "[Click here](https://example.com)"
        result = convert(md)
        assert '#link("https://example.com")' in result
        assert "[Click here]" in result

    def test_image_conversion(self):
        md = "![Alt text](image.png)"
        result = convert(md)
        assert '#image("image.png"' in result

    def test_code_block_conversion(self):
        md = """```python
def hello():
    pass
```"""
        result = convert(md)
        assert "```python" in result
        assert "def hello():" in result
        assert "```" in result

    def test_list_conversion(self):
        md = """- Item 1
- Item 2
- Item 3"""
        result = convert(md)
        assert "- Item 1" in result
        assert "- Item 2" in result
        assert "- Item 3" in result

    def test_ordered_list_conversion(self):
        md = """1. First
2. Second
3. Third"""
        result = convert(md)
        # Typst uses + for auto-numbered lists
        assert "+ First" in result or "1. First" in result

    def test_blockquote_conversion(self):
        md = "> This is a quote"
        result = convert(md)
        assert "This is a quote" in result
        assert "#block" in result

    def test_thematic_break_conversion(self):
        md = "---"
        result = convert(md)
        assert "#line" in result

    def test_escaping_special_chars(self):
        md = "Use the #hashtag and @mention"
        result = convert(md)
        assert r"\#hashtag" in result
        assert r"\@mention" in result

    def test_complex_document(self):
        md = """# My Document

This is an introductory paragraph with **bold** and *italic* text.

## Section 1

Here's some code:

```python
print("Hello, World!")
```

### Subsection

- Point A
- Point B
- Point C

> A wise quote

---

Check out [this link](https://example.com)!
"""
        result = convert(md)

        # Check structure
        assert "= My Document" in result
        assert "== Section 1" in result
        assert "=== Subsection" in result

        # Check formatting
        assert "*bold*" in result
        assert "_italic_" in result

        # Check code
        assert "```python" in result

        # Check list
        assert "- Point A" in result

        # Check quote
        assert "#block" in result

        # Check link
        assert '#link("https://example.com")' in result


class TestParserSelection:
    """Test parser selection in convert function."""

    def test_default_parser(self):
        # Should work with default parser
        result = convert("Hello")
        assert "Hello" in result

    def test_explicit_parser(self):
        result = convert("Hello", parser="markdown-it")
        assert "Hello" in result

    def test_invalid_parser(self):
        with pytest.raises(ValueError, match="Unknown parser"):
            convert("Hello", parser="nonexistent")
