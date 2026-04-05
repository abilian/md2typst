"""Tests for the Style config and generator directive emission."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from md2typst import convert_with_config
from md2typst.config import Config, Style, load_config

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.integration


class TestStyleMerge:
    """Test Style.merge() logic."""

    def test_empty_merge(self) -> None:
        base = Style(font=["A"], language="en")
        merged = base.merge({})
        assert merged.font == ["A"]
        assert merged.language == "en"

    def test_override_scalar(self) -> None:
        base = Style(language="en")
        merged = base.merge({"language": "fr"})
        assert merged.language == "fr"

    def test_font_coercion_string(self) -> None:
        merged = Style().merge({"font": "Libertinus Serif"})
        assert merged.font == ["Libertinus Serif"]

    def test_font_coercion_list(self) -> None:
        merged = Style().merge({"font": ["A", "B"]})
        assert merged.font == ["A", "B"]

    def test_preamble_concatenation(self) -> None:
        base = Style(preamble="#set par(justify: true)")
        merged = base.merge({"preamble": "#set text(weight: 400)"})
        assert "#set par(justify: true)" in merged.preamble
        assert "#set text(weight: 400)" in merged.preamble

    def test_unset_fields_inherit(self) -> None:
        base = Style(font=["A"], language="en", paper="a4")
        merged = base.merge({"language": "fr"})
        assert merged.font == ["A"]
        assert merged.language == "fr"
        assert merged.paper == "a4"


class TestStyleDirectives:
    """Test that Style fields produce #set text/#set page directives."""

    def test_no_style_no_directives(self) -> None:
        config = Config()
        result = convert_with_config("# Hello\n", config)
        assert "#set text" not in result
        assert "#set page" not in result

    def test_language_emits_text_directive(self) -> None:
        config = Config(style=Style(language="fr"))
        result = convert_with_config("# Hello\n", config)
        assert '#set text(lang: "fr")' in result

    def test_font_single(self) -> None:
        config = Config(style=Style(font=["Libertinus Serif"]))
        result = convert_with_config("# Hello\n", config)
        assert '#set text(font: "Libertinus Serif")' in result

    def test_font_fallback_list(self) -> None:
        config = Config(style=Style(font=["Primary", "Fallback"]))
        result = convert_with_config("# Hello\n", config)
        assert '#set text(font: ("Primary", "Fallback"))' in result

    def test_combined_text_fields(self) -> None:
        config = Config(style=Style(font=["A"], font_size="12pt", language="en"))
        result = convert_with_config("# Hello\n", config)
        # All three should be in one #set text(...) call
        assert "#set text(" in result
        assert 'font: "A"' in result
        assert "size: 12pt" in result
        assert 'lang: "en"' in result

    def test_page_directives(self) -> None:
        config = Config(style=Style(paper="a4", margin="2.5cm"))
        result = convert_with_config("# Hello\n", config)
        assert '#set page(paper: "a4", margin: 2.5cm)' in result

    def test_preamble_emitted(self) -> None:
        config = Config(style=Style(preamble="#show heading: it => [*#it*]"))
        result = convert_with_config("# Hello\n", config)
        assert "#show heading: it => [*#it*]" in result


class TestFrontMatterStyleOverride:
    """Test that front matter can override style fields."""

    def test_language_override(self) -> None:
        config = Config(style=Style(language="en"))
        md = "---\nlanguage: fr\n---\n# Hello\n"
        result = convert_with_config(md, config)
        assert '#set text(lang: "fr")' in result
        assert '#set text(lang: "en")' not in result

    def test_font_override_from_front_matter(self) -> None:
        config = Config(style=Style(font=["Default"]))
        md = "---\nfont: Override\n---\n# Hello\n"
        result = convert_with_config(md, config)
        assert 'font: "Override"' in result

    def test_inherited_fields_kept(self) -> None:
        config = Config(style=Style(font=["Default"], paper="a4"))
        md = "---\nlanguage: fr\n---\n# Hello\n"
        result = convert_with_config(md, config)
        # font and paper still from config
        assert 'font: "Default"' in result
        assert 'paper: "a4"' in result
        # language from front matter
        assert 'lang: "fr"' in result

    def test_style_keys_not_emitted_as_variables(self) -> None:
        """Style keys in front matter must not leak as #let doc-* variables."""
        md = "---\ntitle: My Doc\nlanguage: fr\n---\n# Hello\n"
        result = convert_with_config(md, Config())
        assert '#let doc-title = "My Doc"' in result
        assert "#let doc-language" not in result

    def test_front_matter_preamble_merged_with_config(self) -> None:
        config = Config(style=Style(preamble="#set par(justify: true)"))
        md = "---\npreamble: |\n  #set text(weight: 400)\n---\n# Hello\n"
        result = convert_with_config(md, config)
        assert "#set par(justify: true)" in result
        assert "#set text(weight: 400)" in result
        # Config preamble appears before front matter preamble
        assert result.index("justify") < result.index("weight")


class TestUserConfigLoading:
    """Test that user-level config is discovered and merged."""

    def test_user_config_loaded(self, tmp_path: Path) -> None:
        """A user config file should be found and merged into load_config."""
        user_config = tmp_path / "config.toml"
        user_config.write_text('[style]\nlanguage = "fr"\nfont = "EB Garamond"\n')
        # Patch find_user_config to return our tmp file
        with patch("md2typst.config.find_user_config", return_value=user_config):
            config = load_config(start_dir=tmp_path)
        assert config.style.language == "fr"
        assert config.style.font == ["EB Garamond"]

    def test_user_config_overridden_by_local(self, tmp_path: Path) -> None:
        """Local md2typst.toml should override user config."""
        user_config = tmp_path / "user.toml"
        user_config.write_text('[style]\nlanguage = "fr"\n')
        local_config = tmp_path / "md2typst.toml"
        local_config.write_text('[style]\nlanguage = "de"\n')
        with patch("md2typst.config.find_user_config", return_value=user_config):
            config = load_config(start_dir=tmp_path)
        assert config.style.language == "de"
