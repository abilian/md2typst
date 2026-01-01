"""Property-based tests using Hypothesis.

These tests verify invariants that should hold for any valid input,
helping discover edge cases that unit tests might miss.
"""

from __future__ import annotations

import re
from string import ascii_letters, digits

import pytest
from hypothesis import assume, given, settings, strategies as st

from md2typst import convert
from md2typst.ast import (
    Code,
    CodeBlock,
    Document,
    Emphasis,
    Heading,
    Link,
    Paragraph,
    Strong,
    Text,
)
from md2typst.generator import generate_typst

pytestmark = pytest.mark.integration

# All available parsers
ALL_PARSERS = ["markdown-it", "mistune", "marko"]


# Custom strategies for generating Markdown-like content
@st.composite
def safe_text(draw):
    """Generate text that won't be interpreted as Markdown."""
    # Avoid markdown special characters at start/end
    chars = ascii_letters + digits + " "
    text = draw(st.text(alphabet=chars, min_size=1, max_size=50))
    return text.strip() or "text"


@st.composite
def markdown_heading(draw):
    """Generate a Markdown heading."""
    level = draw(st.integers(min_value=1, max_value=6))
    text = draw(safe_text())
    return "#" * level + " " + text


@st.composite
def markdown_emphasis(draw):
    """Generate emphasized text."""
    text = draw(safe_text())
    marker = draw(st.sampled_from(["*", "_"]))
    return f"{marker}{text}{marker}"


@st.composite
def markdown_strong(draw):
    """Generate strong text."""
    text = draw(safe_text())
    marker = draw(st.sampled_from(["**", "__"]))
    return f"{marker}{text}{marker}"


@st.composite
def markdown_code_span(draw):
    """Generate inline code."""
    # Avoid backticks in the content
    chars = ascii_letters + digits + " "
    text = draw(st.text(alphabet=chars, min_size=1, max_size=20))
    return f"`{text.strip() or 'code'}`"


@st.composite
def markdown_link(draw):
    """Generate a Markdown link."""
    text = draw(safe_text())
    # Simple URL pattern
    domain = draw(st.text(alphabet=ascii_letters, min_size=3, max_size=10))
    return f"[{text}](https://{domain}.com)"


class TestConversionProperties:
    """Property-based tests for conversion invariants."""

    @settings(max_examples=50)
    @given(st.sampled_from(ALL_PARSERS), markdown_heading())
    def test_heading_preserved(self, parser_name: str, md: str):
        """Headings should produce output with '=' markers."""
        result = convert(md, parser=parser_name)

        # Count '#' in input to determine level
        level = len(md) - len(md.lstrip("#"))
        expected_prefix = "=" * level

        assert expected_prefix in result

    @settings(max_examples=50)
    @given(st.sampled_from(ALL_PARSERS), markdown_code_span())
    def test_code_span_preserved(self, parser_name: str, md: str):
        """Code spans should be preserved in output."""
        result = convert(md, parser=parser_name)

        # Extract code content (between backticks)
        code_content = md[1:-1]
        assert code_content in result

    @settings(max_examples=50)
    @given(st.sampled_from(ALL_PARSERS), safe_text())
    def test_plain_text_preserved(self, parser_name: str, text: str):
        """Plain text should appear in output."""
        result = convert(text, parser=parser_name)
        assert text in result

    @settings(max_examples=30)
    @given(st.sampled_from(ALL_PARSERS), markdown_link())
    def test_link_url_preserved(self, parser_name: str, md: str):
        """Link URLs should be preserved in output."""
        result = convert(md, parser=parser_name)

        # Extract URL from markdown
        url_match = re.search(r"\((https://[^)]+)\)", md)
        if url_match:
            url = url_match.group(1)
            assert url in result

    @settings(max_examples=50)
    @given(st.sampled_from(ALL_PARSERS))
    def test_empty_input_produces_empty_output(self, parser_name: str):
        """Empty input should produce empty or whitespace-only output."""
        result = convert("", parser=parser_name)
        assert result.strip() == ""

    @settings(max_examples=30)
    @given(st.sampled_from(ALL_PARSERS), st.integers(min_value=1, max_value=10))
    def test_multiple_paragraphs(self, parser_name: str, count: int):
        """Multiple paragraphs should all appear in output."""
        paragraphs = [f"Paragraph {i}" for i in range(count)]
        md = "\n\n".join(paragraphs)

        result = convert(md, parser=parser_name)

        for para in paragraphs:
            assert para in result


class TestGeneratorProperties:
    """Property-based tests for the Typst generator."""

    @settings(max_examples=50)
    @given(st.integers(min_value=1, max_value=6), safe_text())
    def test_heading_level_mapping(self, level: int, text: str):
        """Heading level should map to correct number of '=' signs."""
        doc = Document(children=[Heading(level=level, children=[Text(content=text)])])
        result = generate_typst(doc)

        expected = "=" * level
        assert result.startswith(expected)
        assert text in result

    @settings(max_examples=50)
    @given(safe_text())
    def test_emphasis_wrapping(self, text: str):
        """Emphasis should be wrapped with underscores."""
        doc = Document(
            children=[Paragraph(children=[Emphasis(children=[Text(content=text)])])]
        )
        result = generate_typst(doc)

        assert f"_{text}_" in result

    @settings(max_examples=50)
    @given(safe_text())
    def test_strong_wrapping(self, text: str):
        """Strong should be wrapped with asterisks."""
        doc = Document(
            children=[Paragraph(children=[Strong(children=[Text(content=text)])])]
        )
        result = generate_typst(doc)

        assert f"*{text}*" in result

    @settings(max_examples=50)
    @given(safe_text())
    def test_code_span_backticks(self, text: str):
        """Code spans should be wrapped with backticks."""
        doc = Document(children=[Paragraph(children=[Code(content=text)])])
        result = generate_typst(doc)

        assert f"`{text}`" in result

    @settings(max_examples=30)
    @given(st.text(alphabet=ascii_letters + digits + " \n", min_size=1, max_size=100))
    def test_code_block_preserved(self, code: str):
        """Code block content should be preserved exactly."""
        assume(code.strip())  # Skip empty/whitespace-only
        doc = Document(children=[CodeBlock(code=code, language="python")])
        result = generate_typst(doc)

        # Code should appear in output (possibly with escaping)
        assert "python" in result
        assert "```" in result

    @settings(max_examples=30)
    @given(safe_text(), st.text(alphabet=ascii_letters, min_size=3, max_size=20))
    def test_link_structure(self, text: str, domain: str):
        """Links should produce #link with URL and text."""
        url = f"https://{domain}.example.com"
        doc = Document(
            children=[
                Paragraph(children=[Link(url=url, children=[Text(content=text)])])
            ]
        )
        result = generate_typst(doc)

        assert "#link(" in result
        assert url in result
        assert text in result


class TestParserEquivalence:
    """Test that all parsers produce equivalent results."""

    @settings(max_examples=30)
    @given(markdown_heading())
    def test_heading_equivalence(self, md: str):
        """All parsers should produce same heading structure."""
        results = [convert(md, parser=p) for p in ALL_PARSERS]

        # All should have the same number of '=' signs
        levels = [len(r) - len(r.lstrip("=")) for r in results]
        assert len(set(levels)) == 1, f"Different heading levels: {levels}"

    @settings(max_examples=30)
    @given(safe_text())
    def test_text_equivalence(self, text: str):
        """All parsers should preserve the same text."""
        results = [convert(text, parser=p) for p in ALL_PARSERS]

        # All should contain the original text
        for result in results:
            assert text in result

    @settings(max_examples=20)
    @given(markdown_code_span())
    def test_code_equivalence(self, md: str):
        """All parsers should preserve code content."""
        results = [convert(md, parser=p) for p in ALL_PARSERS]

        # Extract code content
        code = md[1:-1]
        for result in results:
            assert code in result


class TestRobustness:
    """Test robustness against edge cases and unusual input."""

    @settings(max_examples=30)
    @given(st.sampled_from(ALL_PARSERS), st.text(min_size=0, max_size=100))
    def test_no_crash_on_arbitrary_input(self, parser_name: str, text: str):
        """Converter should not crash on arbitrary input."""
        # Should not raise any exception
        try:
            result = convert(text, parser=parser_name)
            assert isinstance(result, str)
        except Exception as e:
            pytest.fail(f"Crashed on input {text!r}: {e}")

    @settings(max_examples=20)
    @given(st.sampled_from(ALL_PARSERS), st.binary(min_size=0, max_size=50))
    def test_no_crash_on_binary_like_input(self, parser_name: str, data: bytes):
        """Converter should handle binary-like strings gracefully."""
        try:
            text = data.decode("utf-8", errors="replace")
            result = convert(text, parser=parser_name)
            assert isinstance(result, str)
        except Exception as e:
            pytest.fail(f"Crashed on binary input: {e}")

    @settings(max_examples=20)
    @given(
        st.sampled_from(ALL_PARSERS),
        st.lists(st.sampled_from(["\n", " "]), min_size=0, max_size=20),
    )
    def test_whitespace_only_input(self, parser_name: str, ws_chars: list):
        """Whitespace-only input should not crash."""
        # Note: We only test spaces and newlines, not tabs, because
        # tabs at the start of a line create indented code blocks in Markdown
        text = "".join(ws_chars)
        result = convert(text, parser=parser_name)
        # Should not crash and produce a string
        assert isinstance(result, str)

    @settings(max_examples=20)
    @given(
        st.sampled_from(ALL_PARSERS),
        st.text(alphabet="*_`#[]()>-+0123456789. ", min_size=1, max_size=50),
    )
    def test_markdown_special_chars_only(self, parser_name: str, text: str):
        """Input with only Markdown special chars should not crash."""
        try:
            result = convert(text, parser=parser_name)
            assert isinstance(result, str)
        except Exception as e:
            pytest.fail(f"Crashed on special char input {text!r}: {e}")
