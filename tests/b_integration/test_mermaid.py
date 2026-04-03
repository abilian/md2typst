"""Integration tests for Mermaid diagram support."""

from __future__ import annotations

import pytest

from md2typst import convert

MERMAID_SIMPLE = """\
```mermaid
graph TD; A-->B;
```
"""

MERMAID_FLOWCHART = """\
```mermaid
graph LR
    A[Start] --> B{Decision}
    B -->|Yes| C[OK]
    B -->|No| D[End]
```
"""


@pytest.mark.integration
class TestMermaidParsing:
    """Test that mermaid code blocks produce MermaidBlock AST nodes."""

    @pytest.mark.parametrize("parser", ["markdown-it", "mistune", "marko"])
    def test_simple_mermaid(self, parser: str) -> None:
        result = convert(MERMAID_SIMPLE, parser=parser)
        assert '#mermaid("' in result
        assert "graph TD; A-->B;" in result

    @pytest.mark.parametrize("parser", ["markdown-it", "mistune", "marko"])
    def test_multiline_mermaid(self, parser: str) -> None:
        result = convert(MERMAID_FLOWCHART, parser=parser)
        assert '#mermaid("' in result
        assert "graph LR" in result
        assert "A[Start]" in result

    @pytest.mark.parametrize("parser", ["markdown-it", "mistune", "marko"])
    def test_mermaid_not_code_block(self, parser: str) -> None:
        """Mermaid blocks should not be rendered as code blocks."""
        result = convert(MERMAID_SIMPLE, parser=parser)
        assert "```mermaid" not in result

    @pytest.mark.parametrize("parser", ["markdown-it", "mistune", "marko"])
    def test_auto_import(self, parser: str) -> None:
        """Mermaid blocks should auto-import the mmdr package."""
        result = convert(MERMAID_SIMPLE, parser=parser)
        assert '#import "@preview/mmdr:0.2.1": mermaid' in result

    @pytest.mark.parametrize("parser", ["markdown-it", "mistune", "marko"])
    def test_no_import_without_mermaid(self, parser: str) -> None:
        """No mmdr import when there are no mermaid blocks."""
        md = "```python\nprint('hello')\n```\n"
        result = convert(md, parser=parser)
        assert "mmdr" not in result

    @pytest.mark.parametrize("parser", ["markdown-it", "mistune", "marko"])
    def test_non_mermaid_code_block_unchanged(self, parser: str) -> None:
        """Regular code blocks should still work normally."""
        md = "```python\nprint('hello')\n```\n"
        result = convert(md, parser=parser)
        assert "```python" in result
        assert "#mermaid" not in result
