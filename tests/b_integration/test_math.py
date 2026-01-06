"""Integration tests for math parsing and generation."""

from __future__ import annotations

import pytest

from md2typst.ast import MathBlock, MathInline
from md2typst.generator import generate_typst

pytestmark = pytest.mark.integration


class TestMarkdownItMath:
    """Test math parsing with markdown-it-py parser."""

    @pytest.fixture
    def parser(self):
        """Create a markdown-it parser with dollarmath plugin enabled."""
        from md2typst.parsers.markdown_it import MarkdownItParser

        p = MarkdownItParser()
        p.load_plugin("mdit_py_plugins.dollarmath")
        return p

    def test_inline_math(self, parser):
        """Test parsing inline math."""
        doc = parser.parse("The equation $E = mc^2$ is famous.")

        para = doc.children[0]
        math_nodes = [c for c in para.children if isinstance(c, MathInline)]
        assert len(math_nodes) == 1
        assert math_nodes[0].content == "E = mc^2"

    def test_block_math(self, parser):
        """Test parsing display math."""
        doc = parser.parse("""Some text.

$$
\\int_0^\\infty e^{-x^2} dx
$$

More text.
""")

        # Find the MathBlock
        math_blocks = [c for c in doc.children if isinstance(c, MathBlock)]
        assert len(math_blocks) == 1
        assert "\\int_0^\\infty" in math_blocks[0].content

    def test_multiple_inline_math(self, parser):
        """Test parsing multiple inline math expressions."""
        doc = parser.parse("Given $x = 1$ and $y = 2$, then $x + y = 3$.")

        para = doc.children[0]
        math_nodes = [c for c in para.children if isinstance(c, MathInline)]
        assert len(math_nodes) == 3

    def test_inline_math_roundtrip(self, parser):
        """Test full conversion from Markdown to Typst."""
        doc = parser.parse("The equation $E = mc^2$ is famous.")
        result = generate_typst(doc)
        assert '#mi("E = mc^2")' in result

    def test_block_math_roundtrip(self, parser):
        """Test block math conversion."""
        doc = parser.parse("$$\nx^2 + y^2 = z^2\n$$")
        result = generate_typst(doc)
        assert "#mitex(`" in result
        assert "x^2 + y^2 = z^2" in result


class TestMistuneMath:
    """Test math parsing with mistune parser."""

    @pytest.fixture
    def parser(self):
        """Create a mistune parser with math plugin enabled."""
        from md2typst.parsers.mistune import MistuneParser

        p = MistuneParser()
        p.load_plugin("math")
        return p

    def test_inline_math(self, parser):
        """Test parsing inline math."""
        doc = parser.parse("The equation $E = mc^2$ is famous.")

        para = doc.children[0]
        math_nodes = [c for c in para.children if isinstance(c, MathInline)]
        assert len(math_nodes) == 1
        assert math_nodes[0].content == "E = mc^2"

    def test_block_math(self, parser):
        """Test parsing display math."""
        doc = parser.parse("""Some text.

$$
\\int_0^\\infty e^{-x^2} dx
$$

More text.
""")

        # Find the MathBlock
        math_blocks = [c for c in doc.children if isinstance(c, MathBlock)]
        assert len(math_blocks) == 1
        assert "\\int_0^\\infty" in math_blocks[0].content

    def test_inline_math_roundtrip(self, parser):
        """Test full conversion from Markdown to Typst."""
        doc = parser.parse("The equation $E = mc^2$ is famous.")
        result = generate_typst(doc)
        assert '#mi("E = mc^2")' in result


class TestMathWithoutPlugin:
    """Test that math syntax is ignored without the plugin."""

    def test_math_syntax_without_plugin_markdown_it(self):
        """Without dollarmath plugin, $ should be literal."""
        from md2typst.parsers.markdown_it import MarkdownItParser

        parser = MarkdownItParser()
        # No dollarmath plugin loaded
        doc = parser.parse("The cost is $100.")

        result = generate_typst(doc)
        # Should be treated as literal text ($ escaped)
        assert "\\$100" in result

    def test_math_syntax_without_plugin_mistune(self):
        """Without math plugin, $ should be literal."""
        from md2typst.parsers.mistune import MistuneParser

        parser = MistuneParser()
        # No math plugin loaded
        doc = parser.parse("The cost is $100.")

        result = generate_typst(doc)
        # Should be treated as literal text ($ escaped)
        assert "\\$100" in result
