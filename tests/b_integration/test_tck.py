"""Technology Compatibility Kit (TCK) tests.

These tests validate conversion against CommonMark and GFM specifications
by testing against fixture files with expected outputs.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.integration

from mkd2typst import convert
from mkd2typst.parsers import get_parser

# Test fixture directories
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
COMMONMARK_DIR = FIXTURES_DIR / "commonmark"
GFM_DIR = FIXTURES_DIR / "gfm"

# All available parsers
ALL_PARSERS = ["markdown-it", "mistune", "marko"]


def normalize_typst(text: str) -> str:
    """Normalize Typst output for comparison.

    This handles stylistic differences that are semantically equivalent:
    - #emph[x] vs _x_
    - #strong[x] vs *x*
    - Whitespace normalization
    - Trailing newlines
    """
    # Normalize emphasis variants
    text = re.sub(r"#emph\[([^\]]+)\]", r"_\1_", text)
    text = re.sub(r"#strong\[([^\]]+)\]", r"*\1*", text)

    # Normalize quote variants
    text = re.sub(r"#quote\(block:\s*true\)\[", "#quote[", text)

    # Normalize thematic breaks
    text = text.replace("#horizontalrule", "#line(length: 100%)")

    # Normalize whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text


def extract_semantic_content(text: str) -> set[str]:
    """Extract semantic content tokens for comparison.

    This extracts the actual content (headings, text, links, etc.)
    regardless of exact formatting.
    """
    tokens = set()

    # Extract headings
    for match in re.finditer(r"^(=+)\s*(.+)$", text, re.MULTILINE):
        level = len(match.group(1))
        content = match.group(2).strip()
        tokens.add(f"heading:{level}:{content}")

    # Extract emphasized text
    for match in re.finditer(r"_([^_]+)_", text):
        tokens.add(f"emphasis:{match.group(1)}")
    for match in re.finditer(r"#emph\[([^\]]+)\]", text):
        tokens.add(f"emphasis:{match.group(1)}")

    # Extract strong text
    for match in re.finditer(r"\*([^*]+)\*", text):
        # Avoid matching thematic breaks
        if match.group(1).strip():
            tokens.add(f"strong:{match.group(1)}")
    for match in re.finditer(r"#strong\[([^\]]+)\]", text):
        tokens.add(f"strong:{match.group(1)}")

    # Extract links
    for match in re.finditer(r'#link\("([^"]+)"\)', text):
        tokens.add(f"link:{match.group(1)}")

    # Extract code spans
    for match in re.finditer(r"`([^`]+)`", text):
        tokens.add(f"code:{match.group(1)}")

    # Extract strikethrough
    for match in re.finditer(r"#strike\[([^\]]+)\]", text):
        tokens.add(f"strike:{match.group(1)}")

    return tokens


def load_fixture_pairs(directory: Path) -> list[tuple[str, str, str]]:
    """Load markdown/typst pairs from a directory.

    Returns list of (name, markdown_content, typst_content) tuples.
    """
    pairs = []
    for md_file in sorted(directory.glob("*.md")):
        typ_file = md_file.with_suffix(".typ")
        if typ_file.exists():
            name = md_file.stem
            md_content = md_file.read_text()
            typ_content = typ_file.read_text()
            pairs.append((name, md_content, typ_content))
    return pairs


class TestCommonMarkTCK:
    """TCK tests for CommonMark compliance."""

    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_headings(self, parser_name: str):
        """Test heading conversion."""
        md = "# H1\n\n## H2\n\n### H3"
        result = convert(md, parser=parser_name)

        assert "= H1" in result
        assert "== H2" in result
        assert "=== H3" in result

    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_emphasis(self, parser_name: str):
        """Test emphasis conversion."""
        md = "*italic* and **bold**"
        result = convert(md, parser=parser_name)

        # Check for either style
        assert ("_italic_" in result) or ("#emph[italic]" in result)
        assert ("*bold*" in result) or ("#strong[bold]" in result)

    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_code_inline(self, parser_name: str):
        """Test inline code conversion."""
        md = "Use `print()` function."
        result = convert(md, parser=parser_name)

        assert "`print()`" in result

    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_code_block_fenced(self, parser_name: str):
        """Test fenced code block conversion."""
        md = "```python\nprint('hello')\n```"
        result = convert(md, parser=parser_name)

        assert "```python" in result
        assert "print('hello')" in result

    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_links(self, parser_name: str):
        """Test link conversion."""
        md = "[Click here](https://example.com)"
        result = convert(md, parser=parser_name)

        assert "#link(" in result
        assert "https://example.com" in result
        assert "Click here" in result

    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_images(self, parser_name: str):
        """Test image conversion."""
        md = "![Alt text](image.png)"
        result = convert(md, parser=parser_name)

        assert "#image(" in result
        assert "image.png" in result

    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_unordered_list(self, parser_name: str):
        """Test unordered list conversion."""
        md = "- Item 1\n- Item 2\n- Item 3"
        result = convert(md, parser=parser_name)

        assert "- Item 1" in result
        assert "- Item 2" in result
        assert "- Item 3" in result

    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_ordered_list(self, parser_name: str):
        """Test ordered list conversion."""
        md = "1. First\n2. Second\n3. Third"
        result = convert(md, parser=parser_name)

        # Check for numbered list markers
        assert "1." in result or "+ " in result
        assert "First" in result
        assert "Second" in result
        assert "Third" in result

    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_blockquote(self, parser_name: str):
        """Test blockquote conversion."""
        md = "> This is a quote."
        result = convert(md, parser=parser_name)

        # We use #block for blockquotes (styled like a quote)
        assert "#block(" in result or "#quote[" in result
        assert "This is a quote." in result

    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_thematic_break(self, parser_name: str):
        """Test thematic break conversion."""
        md = "Above\n\n---\n\nBelow"
        result = convert(md, parser=parser_name)

        # Check for either style of horizontal rule
        assert ("#line(" in result) or ("#horizontalrule" in result)

    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_paragraphs(self, parser_name: str):
        """Test paragraph separation."""
        md = "First paragraph.\n\nSecond paragraph."
        result = convert(md, parser=parser_name)

        assert "First paragraph." in result
        assert "Second paragraph." in result
        # Should have blank line between paragraphs
        assert "\n\n" in result or result.count("\n") >= 1


class TestGFMTCK:
    """TCK tests for GFM (GitHub Flavored Markdown) compliance."""

    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_strikethrough(self, parser_name: str):
        """Test strikethrough conversion."""
        md = "This is ~~deleted~~ text."
        result = convert(md, parser=parser_name)

        assert "#strike[" in result
        assert "deleted" in result

    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_table_basic(self, parser_name: str):
        """Test basic table conversion."""
        md = """| A | B |
|---|---|
| 1 | 2 |"""
        result = convert(md, parser=parser_name)

        assert "#table(" in result
        assert "A" in result
        assert "B" in result
        assert "1" in result
        assert "2" in result

    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_table_alignment(self, parser_name: str):
        """Test table with column alignment."""
        md = """| Left | Center | Right |
|:-----|:------:|------:|
| L    | C      | R     |"""
        result = convert(md, parser=parser_name)

        assert "#table(" in result
        assert "left" in result
        assert "center" in result
        assert "right" in result


class TestSemanticEquivalence:
    """Test semantic equivalence across parsers.

    These tests ensure all parsers produce semantically equivalent output,
    even if the exact formatting differs slightly.
    """

    @pytest.mark.parametrize(
        "md",
        [
            "# Heading",
            "*emphasis*",
            "**strong**",
            "`code`",
            "[link](url)",
            "- list item",
            "> quote",
        ],
    )
    def test_all_parsers_produce_equivalent_output(self, md: str):
        """Verify all parsers produce semantically equivalent output."""
        results = {}
        for parser_name in ALL_PARSERS:
            results[parser_name] = convert(md, parser=parser_name)

        # Extract semantic content from each
        semantic_contents = {
            name: extract_semantic_content(result)
            for name, result in results.items()
        }

        # All parsers should extract the same semantic content
        first_content = semantic_contents[ALL_PARSERS[0]]
        for parser_name in ALL_PARSERS[1:]:
            assert semantic_contents[parser_name] == first_content, (
                f"Parser {parser_name} produced different semantic content "
                f"than {ALL_PARSERS[0]}"
            )


class TestFixtureValidation:
    """Validate that fixtures are properly formatted."""

    def test_commonmark_fixtures_exist(self):
        """Verify CommonMark fixtures exist."""
        assert COMMONMARK_DIR.exists()
        md_files = list(COMMONMARK_DIR.glob("*.md"))
        assert len(md_files) > 0, "No CommonMark fixture files found"

    def test_gfm_fixtures_exist(self):
        """Verify GFM fixtures exist."""
        assert GFM_DIR.exists()
        md_files = list(GFM_DIR.glob("*.md"))
        assert len(md_files) > 0, "No GFM fixture files found"

    def test_all_md_have_typ_pairs(self):
        """Verify each .md file has a corresponding .typ file."""
        for directory in [COMMONMARK_DIR, GFM_DIR]:
            for md_file in directory.glob("*.md"):
                typ_file = md_file.with_suffix(".typ")
                assert typ_file.exists(), f"Missing .typ for {md_file.name}"

    def test_corrections_file_valid(self):
        """Verify corrections.yaml is valid YAML."""
        corrections_file = FIXTURES_DIR / "corrections.yaml"
        if corrections_file.exists():
            content = corrections_file.read_text()
            data = yaml.safe_load(content)
            assert "style_mappings" in data


# Get fixture names for parametrization
def get_commonmark_fixture_names() -> list[str]:
    """Get list of CommonMark fixture names."""
    return [f.stem for f in sorted(COMMONMARK_DIR.glob("*.md"))]


def get_gfm_fixture_names() -> list[str]:
    """Get list of GFM fixture names."""
    return [f.stem for f in sorted(GFM_DIR.glob("*.md"))]


class TestCommonMarkFixtures:
    """Test conversion against CommonMark fixture files.

    These tests load actual .md files and verify conversion produces
    semantically correct output (not exact match with Pandoc due to
    style differences documented in corrections.yaml).
    """

    @pytest.mark.parametrize("fixture_name", get_commonmark_fixture_names())
    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_fixture_converts_without_error(
        self, fixture_name: str, parser_name: str
    ):
        """Verify each fixture converts without errors."""
        md_file = COMMONMARK_DIR / f"{fixture_name}.md"
        md_content = md_file.read_text()

        # Should not raise any exception
        result = convert(md_content, parser=parser_name)
        assert isinstance(result, str)
        assert len(result) > 0 or len(md_content.strip()) == 0

    @pytest.mark.parametrize("fixture_name", get_commonmark_fixture_names())
    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_fixture_semantic_content(self, fixture_name: str, parser_name: str):
        """Verify fixture conversion preserves semantic content."""
        md_file = COMMONMARK_DIR / f"{fixture_name}.md"
        typ_file = COMMONMARK_DIR / f"{fixture_name}.typ"

        md_content = md_file.read_text()
        expected_content = typ_file.read_text()

        result = convert(md_content, parser=parser_name)

        # Extract semantic tokens from both
        result_tokens = extract_semantic_content(result)
        expected_tokens = extract_semantic_content(expected_content)

        # Key content should be preserved (allowing for style differences)
        # Check that most expected tokens are present
        if expected_tokens:
            matching = result_tokens & expected_tokens
            coverage = len(matching) / len(expected_tokens) if expected_tokens else 1.0
            assert coverage >= 0.5, (
                f"Low semantic coverage ({coverage:.0%}) for {fixture_name} "
                f"with {parser_name}.\n"
                f"Expected: {expected_tokens}\n"
                f"Got: {result_tokens}"
            )


class TestGFMFixtures:
    """Test conversion against GFM fixture files."""

    @pytest.mark.parametrize("fixture_name", get_gfm_fixture_names())
    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_fixture_converts_without_error(
        self, fixture_name: str, parser_name: str
    ):
        """Verify each GFM fixture converts without errors."""
        md_file = GFM_DIR / f"{fixture_name}.md"
        md_content = md_file.read_text()

        # Should not raise any exception
        result = convert(md_content, parser=parser_name)
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize("fixture_name", get_gfm_fixture_names())
    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_fixture_semantic_content(self, fixture_name: str, parser_name: str):
        """Verify GFM fixture conversion preserves semantic content."""
        md_file = GFM_DIR / f"{fixture_name}.md"
        typ_file = GFM_DIR / f"{fixture_name}.typ"

        md_content = md_file.read_text()
        expected_content = typ_file.read_text()

        result = convert(md_content, parser=parser_name)

        # For GFM features, check key markers are present
        if "strikethrough" in fixture_name:
            assert "#strike[" in result, f"Missing strikethrough in {parser_name} output"

        if "table" in fixture_name:
            assert "#table(" in result, f"Missing table in {parser_name} output"

        # Extract and compare semantic content
        result_tokens = extract_semantic_content(result)
        expected_tokens = extract_semantic_content(expected_content)

        if expected_tokens:
            matching = result_tokens & expected_tokens
            coverage = len(matching) / len(expected_tokens) if expected_tokens else 1.0
            assert coverage >= 0.3, (
                f"Low semantic coverage ({coverage:.0%}) for {fixture_name} "
                f"with {parser_name}"
            )


class TestRegressionSuite:
    """Regression tests for specific edge cases.

    Add tests here for bugs that have been fixed to prevent regression.
    """

    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_nested_emphasis(self, parser_name: str):
        """Test nested emphasis handling."""
        md = "***bold italic***"
        result = convert(md, parser=parser_name)

        # Should have both emphasis and strong markers
        normalized = normalize_typst(result)
        assert "_" in normalized or "#emph" in result
        assert "*" in normalized or "#strong" in result

    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_code_with_special_chars(self, parser_name: str):
        """Test code with special Typst characters."""
        md = "Use `#function` and `@ref`."
        result = convert(md, parser=parser_name)

        # Code content should be preserved
        assert "#function" in result
        assert "@ref" in result

    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_link_with_special_chars(self, parser_name: str):
        """Test links containing special characters."""
        md = "[Link](https://example.com/path?a=1&b=2)"
        result = convert(md, parser=parser_name)

        assert "https://example.com/path?a=1&b=2" in result

    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_empty_document(self, parser_name: str):
        """Test empty document handling."""
        result = convert("", parser=parser_name)
        assert result.strip() == ""

    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_whitespace_only_document(self, parser_name: str):
        """Test whitespace-only document handling."""
        result = convert("   \n\n   \n", parser=parser_name)
        assert result.strip() == ""

    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_deeply_nested_list(self, parser_name: str):
        """Test deeply nested list handling."""
        md = """- Level 1
  - Level 2
    - Level 3"""
        result = convert(md, parser=parser_name)

        assert "Level 1" in result
        assert "Level 2" in result
        assert "Level 3" in result

    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_table_with_empty_cells(self, parser_name: str):
        """Test table with empty cells."""
        md = """| A | B |
|---|---|
|   | X |"""
        result = convert(md, parser=parser_name)

        assert "#table(" in result
        assert "X" in result

    @pytest.mark.parametrize("parser_name", ALL_PARSERS)
    def test_consecutive_code_blocks(self, parser_name: str):
        """Test consecutive code blocks."""
        md = """```python
code1
```

```javascript
code2
```"""
        result = convert(md, parser=parser_name)

        assert "python" in result
        assert "javascript" in result
        assert "code1" in result
        assert "code2" in result
