"""md2typst - Markdown to Typst converter."""

from __future__ import annotations

import contextlib
from pathlib import Path
from typing import Any

from md2typst.ast import Document
from md2typst.config import Config, load_config
from md2typst.generator import TypstGenerator, generate_typst
from md2typst.parsers import get_parser, list_parsers

__version__ = "0.1.0"

__all__ = [
    "Config",
    "Document",
    "TypstGenerator",
    "convert",
    "convert_with_config",
    "generate_typst",
    "get_parser",
    "list_parsers",
    "main",
]


def convert(
    markdown: str,
    parser: str | None = None,
    parser_options: dict[str, Any] | None = None,
    plugins: list[str] | None = None,
) -> str:
    """Convert Markdown text to Typst.

    Args:
        markdown: The Markdown source text.
        parser: Optional parser name. Uses default if not specified.
        parser_options: Optional parser-specific options.
        plugins: Optional list of parser plugins to load.

    Returns:
        The generated Typst source code.
    """
    p = get_parser(parser)

    if parser_options:
        p.configure(parser_options)

    if plugins:
        for plugin in plugins:
            with contextlib.suppress(NotImplementedError):
                p.load_plugin(plugin)

    doc = p.parse(markdown)
    return generate_typst(doc)


def convert_with_config(markdown: str, config: Config) -> str:
    """Convert Markdown text to Typst using a Config object.

    Args:
        markdown: The Markdown source text.
        config: Configuration object.

    Returns:
        The generated Typst source code.
    """
    return convert(
        markdown,
        parser=config.parser,
        parser_options=config.parser_options,
        plugins=config.plugins,
    )


def main() -> None:
    """CLI entry point."""
    import sys

    import click

    @click.command()
    @click.argument("input", type=click.Path(exists=True), required=False)
    @click.option(
        "-o", "--output", type=click.Path(), help="Output file (default: stdout)"
    )
    @click.option("-p", "--parser", default=None, help="Parser to use")
    @click.option(
        "-c",
        "--config",
        "config_file",
        type=click.Path(exists=True),
        help="Config file path",
    )
    @click.option(
        "--plugin", multiple=True, help="Load parser plugin (can be repeated)"
    )
    @click.option("--list-parsers", is_flag=True, help="List available parsers")
    @click.option("--show-config", is_flag=True, help="Show effective configuration")
    @click.version_option(__version__)
    def cli(
        input: str | None,
        output: str | None,
        parser: str | None,
        config_file: str | None,
        plugin: tuple[str, ...],
        list_parsers: bool,
        show_config: bool,
    ) -> None:
        """Convert Markdown to Typst.

        INPUT is the Markdown file to convert. Use - for stdin.
        """
        if list_parsers:
            from md2typst.parsers import list_parsers as lp

            click.echo("Available parsers:")
            for name in lp():
                click.echo(f"  - {name}")
            return

        # Determine start directory for config search
        if input and input != "-":
            start_dir = Path(input).parent
        else:
            start_dir = Path.cwd()

        # Build CLI overrides
        cli_overrides: dict[str, Any] = {}
        if parser:
            cli_overrides["parser"] = parser
        if plugin:
            cli_overrides["plugins"] = list(plugin)

        # Load configuration
        config = load_config(
            config_file=Path(config_file) if config_file else None,
            start_dir=start_dir,
            cli_overrides=cli_overrides,
        )

        if show_config:
            click.echo("Effective configuration:")
            click.echo(f"  parser: {config.parser}")
            click.echo(f"  plugins: {config.plugins}")
            click.echo(f"  parser_options: {config.parser_options}")
            click.echo(f"  output_options: {config.output_options}")
            return

        if input is None:
            # Read from stdin
            text = sys.stdin.read()
        elif input == "-":
            text = sys.stdin.read()
        else:
            with Path(input).open() as f:
                text = f.read()

        result = convert_with_config(text, config)

        if output:
            with Path(output).open("w") as f:
                f.write(result)
        else:
            click.echo(result)

    cli()
