"""Integration tests for [TOC] table of contents support."""

from __future__ import annotations

import pytest

from md2typst import convert

pytestmark = pytest.mark.integration


class TestTOC:
    """Test that [TOC] produces #outline()."""

    @pytest.mark.parametrize("parser", ["markdown-it", "mistune", "marko"])
    def test_toc_converted(self, parser: str) -> None:
        md = "# Title\n\n[TOC]\n\n## Section\n"
        result = convert(md, parser=parser)
        assert "#outline(" in result

    @pytest.mark.parametrize("parser", ["markdown-it", "mistune", "marko"])
    def test_toc_not_in_text(self, parser: str) -> None:
        """[TOC] inside other text should NOT become #outline()."""
        md = "See [TOC] for details.\n"
        result = convert(md, parser=parser)
        assert "#outline(" not in result

    @pytest.mark.parametrize("parser", ["markdown-it", "mistune", "marko"])
    def test_toc_replaces_paragraph(self, parser: str) -> None:
        """The [TOC] paragraph should be fully replaced, not just appended."""
        md = "[TOC]\n"
        result = convert(md, parser=parser)
        assert result.strip() == "#outline(indent: auto, depth: 4)"
