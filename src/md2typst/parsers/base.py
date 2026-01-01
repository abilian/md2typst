"""Abstract base class for Markdown parsers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from md2typst.ast import Document


class MarkdownParser(ABC):
    """Abstract base class for Markdown parsers.

    This class defines the interface that all parser adapters must implement.
    Each adapter wraps a concrete Markdown parsing library and converts its
    output to our parser-agnostic AST.
    """

    @abstractmethod
    def parse(self, text: str) -> Document:
        """Parse Markdown text into an AST Document.

        Args:
            text: The Markdown source text to parse.

        Returns:
            A Document node containing the parsed AST.
        """

    def configure(self, options: dict[str, Any]) -> None:
        """Apply parser-specific configuration options.

        Args:
            options: A dictionary of parser-specific options.

        The default implementation does nothing. Subclasses should override
        this method to handle their specific configuration options.
        """

    def load_plugin(self, plugin: str, **kwargs: Any) -> None:
        """Load a parser-specific plugin or extension.

        Args:
            plugin: The name or path of the plugin to load.
            **kwargs: Plugin-specific configuration options.

        The default implementation raises NotImplementedError.
        Subclasses should override this method if they support plugins.
        """
        msg = f"{self.__class__.__name__} does not support plugins"
        raise NotImplementedError(msg)

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this parser."""
