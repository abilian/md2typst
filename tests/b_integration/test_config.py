"""Tests for the configuration system."""

from __future__ import annotations

import pytest

from md2typst.config import (
    Config,
    find_config_file,
    find_pyproject_toml,
    load_config,
    load_config_from_file,
    load_config_from_pyproject,
)

pytestmark = pytest.mark.integration


class TestConfig:
    """Test the Config dataclass."""

    def test_default_values(self):
        config = Config()
        assert config.parser == "markdown-it"
        assert config.parser_options == {}
        assert config.plugins == []
        assert config.output_options == {}

    def test_custom_values(self):
        config = Config(
            parser="mistune",
            parser_options={"html": True},
            plugins=["strikethrough"],
            output_options={"indent": 2},
        )
        assert config.parser == "mistune"
        assert config.parser_options == {"html": True}
        assert config.plugins == ["strikethrough"]
        assert config.output_options == {"indent": 2}

    def test_merge_parser(self):
        config = Config(parser="markdown-it")
        merged = config.merge({"parser": "mistune"})
        assert merged.parser == "mistune"
        # Original unchanged
        assert config.parser == "markdown-it"

    def test_merge_parser_options(self):
        config = Config(parser_options={"a": 1, "b": 2})
        merged = config.merge({"parser_options": {"b": 3, "c": 4}})
        assert merged.parser_options == {"a": 1, "b": 3, "c": 4}

    def test_merge_plugins(self):
        config = Config(plugins=["a", "b"])
        merged = config.merge({"plugins": ["c", "d"]})
        assert merged.plugins == ["c", "d"]

    def test_merge_empty_plugins_keeps_original(self):
        config = Config(plugins=["a", "b"])
        merged = config.merge({"plugins": []})
        # Empty list should keep original
        assert merged.plugins == ["a", "b"]

    def test_merge_none_plugins_keeps_original(self):
        config = Config(plugins=["a", "b"])
        merged = config.merge({})
        assert merged.plugins == ["a", "b"]

    def test_from_dict(self):
        data = {
            "parser": "marko",
            "parser_options": {"linkify": True},
            "plugins": ["gfm"],
        }
        config = Config.from_dict(data)
        assert config.parser == "marko"
        assert config.parser_options == {"linkify": True}
        assert config.plugins == ["gfm"]

    def test_from_dict_partial(self):
        config = Config.from_dict({"parser": "mistune"})
        assert config.parser == "mistune"
        assert config.parser_options == {}
        assert config.plugins == []


class TestFindConfigFile:
    """Test finding configuration files."""

    def test_find_in_current_dir(self, tmp_path):
        config_file = tmp_path / ".md2typst.toml"
        config_file.write_text('parser = "mistune"\n')

        result = find_config_file(tmp_path)
        assert result == config_file

    def test_find_in_parent_dir(self, tmp_path):
        config_file = tmp_path / ".md2typst.toml"
        config_file.write_text('parser = "mistune"\n')

        subdir = tmp_path / "subdir"
        subdir.mkdir()

        result = find_config_file(subdir)
        assert result == config_file

    def test_not_found(self, tmp_path):
        result = find_config_file(tmp_path)
        assert result is None

    def test_find_pyproject_in_current_dir(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\n')

        result = find_pyproject_toml(tmp_path)
        assert result == pyproject

    def test_find_pyproject_in_parent_dir(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\n')

        subdir = tmp_path / "src" / "pkg"
        subdir.mkdir(parents=True)

        result = find_pyproject_toml(subdir)
        assert result == pyproject


class TestLoadConfigFromFile:
    """Test loading config from .md2typst.toml."""

    def test_load_basic_config(self, tmp_path):
        config_file = tmp_path / ".md2typst.toml"
        config_file.write_text("""
parser = "mistune"
plugins = ["strikethrough", "table"]

[parser_options]
html = true
linkify = false
""")
        result = load_config_from_file(config_file)
        assert result["parser"] == "mistune"
        assert result["plugins"] == ["strikethrough", "table"]
        assert result["parser_options"]["html"] is True
        assert result["parser_options"]["linkify"] is False

    def test_load_empty_config(self, tmp_path):
        config_file = tmp_path / ".md2typst.toml"
        config_file.write_text("")
        result = load_config_from_file(config_file)
        assert result == {}


class TestLoadConfigFromPyproject:
    """Test loading config from pyproject.toml."""

    def test_load_tool_section(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "myproject"

[tool.md2typst]
parser = "marko"
plugins = ["gfm"]
""")
        result = load_config_from_pyproject(pyproject)
        assert result["parser"] == "marko"
        assert result["plugins"] == ["gfm"]

    def test_no_tool_section(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "myproject"
""")
        result = load_config_from_pyproject(pyproject)
        assert result == {}

    def test_empty_tool_section(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.other]
setting = true
""")
        result = load_config_from_pyproject(pyproject)
        assert result == {}


class TestLoadConfig:
    """Test the full configuration loading with precedence."""

    def test_defaults_only(self, tmp_path):
        config = load_config(start_dir=tmp_path)
        assert config.parser == "markdown-it"
        assert config.plugins == []

    def test_pyproject_config(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.md2typst]
parser = "marko"
""")
        config = load_config(start_dir=tmp_path)
        assert config.parser == "marko"

    def test_md2typst_toml_overrides_pyproject(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.md2typst]
parser = "marko"
plugins = ["a"]
""")

        config_file = tmp_path / ".md2typst.toml"
        config_file.write_text("""
parser = "mistune"
""")

        config = load_config(start_dir=tmp_path)
        assert config.parser == "mistune"
        # Plugins from pyproject should still be there since not overridden
        assert config.plugins == ["a"]

    def test_cli_overrides_all(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.md2typst]
parser = "marko"
""")

        config_file = tmp_path / ".md2typst.toml"
        config_file.write_text("""
parser = "mistune"
""")

        config = load_config(
            start_dir=tmp_path,
            cli_overrides={"parser": "markdown-it"},
        )
        assert config.parser == "markdown-it"

    def test_explicit_config_file(self, tmp_path):
        # Create a config file in a different location
        other_dir = tmp_path / "other"
        other_dir.mkdir()
        config_file = other_dir / "custom.toml"
        config_file.write_text("""
parser = "mistune"
""")

        config = load_config(
            config_file=config_file,
            start_dir=tmp_path,
        )
        assert config.parser == "mistune"

    def test_cli_none_values_ignored(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.md2typst]
parser = "marko"
""")

        config = load_config(
            start_dir=tmp_path,
            cli_overrides={"parser": None},  # None should be ignored
        )
        assert config.parser == "marko"

    def test_plugins_from_cli(self, tmp_path):
        config = load_config(
            start_dir=tmp_path,
            cli_overrides={"plugins": ["strikethrough", "table"]},
        )
        assert config.plugins == ["strikethrough", "table"]

    def test_parser_options_merge(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.md2typst.parser_options]
html = true
linkify = false
""")

        config_file = tmp_path / ".md2typst.toml"
        config_file.write_text("""
[parser_options]
linkify = true
typographer = true
""")

        config = load_config(start_dir=tmp_path)
        assert config.parser_options == {
            "html": True,
            "linkify": True,  # Overridden
            "typographer": True,  # Added
        }


class TestConfigIntegration:
    """Integration tests for config with the converter."""

    def test_convert_with_config(self):
        from md2typst import convert_with_config

        config = Config(parser="mistune")
        result = convert_with_config("# Hello", config)
        assert "= Hello" in result

    def test_convert_with_different_parsers(self):
        from md2typst import convert_with_config

        md = "**bold** and *italic*"

        for parser_name in ["markdown-it", "mistune", "marko"]:
            config = Config(parser=parser_name)
            result = convert_with_config(md, config)
            assert "*bold*" in result
            assert "_italic_" in result
