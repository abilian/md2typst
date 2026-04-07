"""Integration tests for diagram (unbreakable) block support."""

from __future__ import annotations

import pytest

from md2typst import convert

DIAGRAM_SIMPLE = """\
```diagram
+---------+
| Server  |
+---------+
```
"""


@pytest.mark.integration
class TestDiagramBlock:
    """Test that ```diagram blocks produce unbreakable Typst output."""

    @pytest.mark.parametrize("parser", ["markdown-it", "mistune", "marko"])
    def test_wrapped_in_unbreakable_block(self, parser: str) -> None:
        result = convert(DIAGRAM_SIMPLE, parser=parser)
        assert "#block(breakable: false)" in result
        assert "Server" in result

    @pytest.mark.parametrize("parser", ["markdown-it", "mistune", "marko"])
    def test_rendered_as_raw_block(self, parser: str) -> None:
        """Content should be inside a Typst raw block (triple backticks)."""
        result = convert(DIAGRAM_SIMPLE, parser=parser)
        assert "```\n+---------+" in result

    @pytest.mark.parametrize("parser", ["markdown-it", "mistune", "marko"])
    def test_not_a_regular_code_block(self, parser: str) -> None:
        """Should not be rendered as ```diagram."""
        result = convert(DIAGRAM_SIMPLE, parser=parser)
        assert "```diagram" not in result

    @pytest.mark.parametrize("parser", ["markdown-it", "mistune", "marko"])
    def test_regular_code_unaffected(self, parser: str) -> None:
        """Regular code blocks should not get the unbreakable wrapper."""
        md = "```python\nprint('hello')\n```\n"
        result = convert(md, parser=parser)
        assert "#block(breakable: false)" not in result
