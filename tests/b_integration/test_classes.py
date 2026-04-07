"""Integration tests for document class support."""

from __future__ import annotations

import pytest

from md2typst import convert_with_config
from md2typst.config import Config, Style

pytestmark = pytest.mark.integration

ARTICLE_PREAMBLE = '#set heading(numbering: "1.")'
REPORT_PREAMBLE = "#show heading.where(level: 2): it => { pagebreak(weak: true); it }"
BOOK_PREAMBLE = "#set page(margin: (inside: 3cm, outside: 2cm))"


def _config_with_classes(default: str | None = None) -> Config:
    return Config(
        default_class=default,
        classes={
            "article": {"preamble": ARTICLE_PREAMBLE},
            "report": {"preamble": REPORT_PREAMBLE},
            "book": {"preamble": BOOK_PREAMBLE, "margin": "auto"},
        },
        style=Style(font=["TestFont"], preamble="BASE PREAMBLE"),
    )


class TestClassResolution:
    """Test Config.resolve_class() logic."""

    def test_no_class_returns_base(self) -> None:
        config = _config_with_classes()
        resolved = config.resolve_class()
        assert "BASE PREAMBLE" in resolved.style.preamble

    def test_default_class_applied(self) -> None:
        config = _config_with_classes("report")
        resolved = config.resolve_class()
        assert "pagebreak" in resolved.style.preamble
        # Class preamble replaces base, not concatenates
        assert "BASE PREAMBLE" not in resolved.style.preamble

    def test_explicit_class_overrides_default(self) -> None:
        config = _config_with_classes("report")
        resolved = config.resolve_class("article")
        assert "numbering" in resolved.style.preamble
        assert "pagebreak" not in resolved.style.preamble

    def test_base_font_inherited(self) -> None:
        config = _config_with_classes("article")
        resolved = config.resolve_class()
        assert resolved.style.font == ["TestFont"]

    def test_class_can_override_scalar(self) -> None:
        config = _config_with_classes("book")
        resolved = config.resolve_class()
        assert resolved.style.margin == "auto"

    def test_unknown_class_returns_base(self) -> None:
        config = _config_with_classes("nonexistent")
        resolved = config.resolve_class()
        assert "BASE PREAMBLE" in resolved.style.preamble


class TestFrontMatterClassSelection:
    """Test that front matter `class:` selects a document class."""

    def test_class_from_front_matter(self) -> None:
        config = _config_with_classes("report")
        md = "---\nclass: article\n---\n# Hello\n"
        result = convert_with_config(md, config)
        assert "numbering" in result
        assert "pagebreak" not in result

    def test_class_not_emitted_as_variable(self) -> None:
        config = _config_with_classes("article")
        md = "---\nclass: article\ntitle: Test\n---\n# Hello\n"
        result = convert_with_config(md, config)
        assert "#let doc-class" not in result
        assert '#let doc-title = "Test"' in result
