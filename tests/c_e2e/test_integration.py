"""End-to-end integration tests."""
# ruff: noqa: S603, S607

from __future__ import annotations

import shutil
import subprocess

import pytest

from md2typst import convert

pytestmark = pytest.mark.e2e


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


class TestMd2Pdf:
    """Test the md2pdf CLI command."""

    @pytest.fixture
    def has_typst(self):
        """Skip tests if typst is not installed."""
        if not shutil.which("typst"):
            pytest.skip("typst CLI not installed")

    def test_md2pdf_basic(self, tmp_path, has_typst):
        """Test basic Markdown to PDF conversion."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Hello\n\nWorld.\n")
        pdf_file = tmp_path / "test.pdf"

        result = subprocess.run(
            ["uv", "run", "md2pdf", str(md_file)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"md2pdf failed: {result.stderr}"
        assert pdf_file.exists()
        assert pdf_file.stat().st_size > 0

    def test_md2pdf_custom_output(self, tmp_path, has_typst):
        """Test md2pdf with custom output path."""
        md_file = tmp_path / "input.md"
        md_file.write_text("# Title\n\nContent.\n")
        pdf_file = tmp_path / "custom.pdf"

        result = subprocess.run(
            ["uv", "run", "md2pdf", str(md_file), "-o", str(pdf_file)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"md2pdf failed: {result.stderr}"
        assert pdf_file.exists()

    def test_md2pdf_with_preamble(self, tmp_path, has_typst):
        """Test md2pdf with front matter preamble."""
        md_file = tmp_path / "preamble.md"
        md_file.write_text("""---
preamble: |
  #set text(lang: "fr")
  #set par(justify: true)
---

# Bonjour

Contenu du document.
""")
        pdf_file = tmp_path / "preamble.pdf"

        result = subprocess.run(
            ["uv", "run", "md2pdf", str(md_file)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"md2pdf failed: {result.stderr}"
        assert pdf_file.exists()

    def test_md2pdf_no_temp_file_left(self, tmp_path, has_typst):
        """Test that no temporary .typ file is left behind."""
        md_file = tmp_path / "clean.md"
        md_file.write_text("# Clean\n\nNo temp files.\n")

        subprocess.run(
            ["uv", "run", "md2pdf", str(md_file)],
            capture_output=True,
            text=True,
            check=False,
        )
        typ_files = list(tmp_path.glob("*.typ"))
        assert typ_files == [], f"Temporary .typ files left behind: {typ_files}"


class TestPreambleConversion:
    """Test preamble front matter in conversion."""

    def test_preamble_set_rules(self):
        """Test preamble with #set rules."""
        md = """---
preamble: |
  #set text(lang: "fr", hyphenate: true)
  #set par(justify: true)
---

# Hello
"""
        result = convert(md)
        assert '#set text(lang: "fr", hyphenate: true)' in result
        assert "#set par(justify: true)" in result
        assert "= Hello" in result

    def test_preamble_show_rules(self):
        """Test preamble with #show rules."""
        md = """---
preamble: |
  #show heading.where(level: 1): it => { it; v(0.5em) }
  #show heading.where(level: 2): set text(size: 18pt)
---

# Title

## Section
"""
        result = convert(md)
        assert "#show heading.where(level: 1)" in result
        assert "#show heading.where(level: 2)" in result

    def test_preamble_not_a_variable(self):
        """Test that preamble key is not emitted as a #let variable."""
        md = """---
title: Test
preamble: |
  #set page(margin: 2cm)
---

Content
"""
        result = convert(md)
        assert "doc-preamble" not in result
        assert '#let doc-title = "Test"' in result
        assert "#set page(margin: 2cm)" in result

    def test_preamble_ordering(self):
        """Test that preamble comes after imports but before content."""
        md = """---
title: Test
stylesheet: mystyle
preamble: |
  #set page(margin: 2cm)
---

# Content
"""
        result = convert(md)
        var_pos = result.find("#let doc-title")
        import_pos = result.find("#import")
        preamble_pos = result.find("#set page(margin: 2cm)")
        content_pos = result.find("= Content")

        assert var_pos < import_pos
        assert import_pos < preamble_pos
        assert preamble_pos < content_pos

    def test_empty_preamble(self):
        """Test that empty preamble is ignored."""
        md = """---
title: Test
preamble: ""
---

# Hello
"""
        result = convert(md)
        assert '#let doc-title = "Test"' in result
        assert "= Hello" in result
