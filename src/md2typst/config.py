"""Configuration management for md2typst.

This module handles loading and merging configuration from multiple sources
(lowest to highest priority):

1. Built-in defaults
2. User config (~/.config/md2typst/config.toml via platformdirs)
3. pyproject.toml [tool.md2typst] section
4. md2typst.toml file (searched up from input)
5. Explicit --config file
6. Front matter in the document (handled in generator)
7. CLI arguments (highest priority)
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir


@dataclass
class Style:
    """Typst styling options.

    All fields are optional. Unset fields inherit from upstream config.
    Used to generate #set text(...) / #set page(...) directives and
    additional raw Typst preamble code.
    """

    font: list[str] = field(default_factory=list)
    font_size: str | None = None
    language: str | None = None
    paper: str | None = None
    margin: str | None = None
    preamble: str = ""

    def merge(self, other: dict[str, Any]) -> Style:
        """Merge another style dict into this one, returning a new Style.

        Scalar fields from `other` override self when present.
        `preamble` is concatenated (self first, then other).
        `font` accepts str or list[str]; overrides if set.
        """
        font = self._coerce_font(other.get("font")) if "font" in other else self.font
        other_preamble = other.get("preamble", "")
        merged_preamble = "\n".join(p for p in (self.preamble, other_preamble) if p)
        return Style(
            font=font,
            font_size=other.get("font_size", self.font_size),
            language=other.get("language", self.language),
            paper=other.get("paper", self.paper),
            margin=other.get("margin", self.margin),
            preamble=merged_preamble,
        )

    @staticmethod
    def _coerce_font(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [str(v) for v in value]
        return [str(value)]


@dataclass
class Config:
    """Runtime configuration for md2typst.

    Attributes:
        parser: Name of the Markdown parser to use.
        parser_options: Parser-specific configuration options.
        plugins: List of parser plugins to load.
        stylesheets: List of Typst stylesheet modules to import.
        output_options: Options for Typst output generation.
        style: Typst styling options (font, language, page setup, preamble).
    """

    parser: str = "markdown-it"
    parser_options: dict[str, Any] = field(default_factory=dict)
    plugins: list[str] = field(default_factory=list)
    stylesheets: list[str] = field(default_factory=list)
    output_options: dict[str, Any] = field(default_factory=dict)
    style: Style = field(default_factory=Style)

    def merge(self, other: dict[str, Any]) -> Config:
        """Merge another config dict into this one, returning a new Config.

        Values from `other` override values in self.
        """
        return Config(
            parser=other.get("parser", self.parser),
            parser_options={**self.parser_options, **other.get("parser_options", {})},
            plugins=other.get("plugins", self.plugins) or self.plugins,
            stylesheets=other.get("stylesheets", self.stylesheets) or self.stylesheets,
            output_options={**self.output_options, **other.get("output_options", {})},
            style=self.style.merge(other.get("style", {})),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """Create a Config from a dictionary."""
        return cls().merge(data)


def find_config_file(start_dir: Path | None = None) -> Path | None:
    """Find md2typst.toml by searching up from start_dir.

    Args:
        start_dir: Directory to start searching from. Defaults to cwd.

    Returns:
        Path to config file if found, None otherwise.
    """
    if start_dir is None:
        start_dir = Path.cwd()

    current = start_dir.resolve()

    while True:
        config_path = current / "md2typst.toml"
        if config_path.is_file():
            return config_path

        parent = current.parent
        if parent == current:
            # Reached root
            break
        current = parent

    return None


def find_user_config() -> Path | None:
    """Find the user-level config file.

    Looks for config.toml in the platform-specific user config directory
    (e.g., ~/.config/md2typst/config.toml on Linux/macOS,
    %APPDATA%/md2typst/config.toml on Windows).

    Returns:
        Path to the user config file if it exists, None otherwise.
    """
    config_path = Path(user_config_dir("md2typst")) / "config.toml"
    return config_path if config_path.is_file() else None


def find_pyproject_toml(start_dir: Path | None = None) -> Path | None:
    """Find pyproject.toml by searching up from start_dir.

    Args:
        start_dir: Directory to start searching from. Defaults to cwd.

    Returns:
        Path to pyproject.toml if found, None otherwise.
    """
    if start_dir is None:
        start_dir = Path.cwd()

    current = start_dir.resolve()

    while True:
        pyproject_path = current / "pyproject.toml"
        if pyproject_path.is_file():
            return pyproject_path

        parent = current.parent
        if parent == current:
            # Reached root
            break
        current = parent

    return None


def load_toml_file(path: Path) -> dict[str, Any]:
    """Load a TOML file and return its contents.

    Args:
        path: Path to the TOML file.

    Returns:
        Parsed TOML contents as a dictionary.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        tomllib.TOMLDecodeError: If the file is not valid TOML.
    """
    with path.open("rb") as f:
        return tomllib.load(f)


def load_config_from_file(path: Path) -> dict[str, Any]:
    """Load md2typst config from a md2typst.toml file.

    Args:
        path: Path to the config file.

    Returns:
        Configuration dictionary.
    """
    return load_toml_file(path)


def load_config_from_pyproject(path: Path) -> dict[str, Any]:
    """Load md2typst config from pyproject.toml [tool.md2typst] section.

    Args:
        path: Path to pyproject.toml.

    Returns:
        Configuration dictionary, empty if section not found.
    """
    data = load_toml_file(path)
    return data.get("tool", {}).get("md2typst", {})


def load_config(
    config_file: Path | None = None,
    start_dir: Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> Config:
    """Load configuration from all sources with proper precedence.

    Precedence (highest to lowest):
    1. CLI arguments (cli_overrides)
    2. Explicit config file (config_file)
    3. md2typst.toml (found by searching up)
    4. pyproject.toml [tool.md2typst] (found by searching up)
    5. User config (~/.config/md2typst/config.toml via platformdirs)
    6. Default values

    Args:
        config_file: Explicit path to a config file.
        start_dir: Directory to start searching for config files.
        cli_overrides: Configuration from CLI arguments.

    Returns:
        Merged Config object.
    """
    config = Config()

    # Load from user config (lowest priority after defaults)
    user_config_path = find_user_config()
    if user_config_path:
        user_config_data = load_toml_file(user_config_path)
        if user_config_data:
            config = config.merge(user_config_data)

    # Load from pyproject.toml
    pyproject_path = find_pyproject_toml(start_dir)
    if pyproject_path:
        pyproject_config = load_config_from_pyproject(pyproject_path)
        if pyproject_config:
            config = config.merge(pyproject_config)

    # Load from md2typst.toml (higher priority)
    if config_file is None:
        config_file = find_config_file(start_dir)

    if config_file and config_file.is_file():
        file_config = load_config_from_file(config_file)
        config = config.merge(file_config)

    # Apply CLI overrides (highest priority)
    if cli_overrides:
        # Filter out None values from CLI
        filtered_overrides = {k: v for k, v in cli_overrides.items() if v is not None}
        config = config.merge(filtered_overrides)

    return config
