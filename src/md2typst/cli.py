"""CLI entry points for md2typst and md2pdf."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path
from typing import Any

import click

from md2typst.config import Config, find_user_config, load_config
from md2typst.converter import convert_with_config
from md2typst.parsers import list_parsers as get_available_parsers

__version__ = version("md2typst")


def _print_debug_config(config: Config, input_path: Path) -> None:
    """Print debug info about effective configuration to stderr."""
    click.echo("--- Debug: effective configuration ---", err=True)
    click.echo(f"  input: {input_path}", err=True)
    user_cfg = find_user_config()
    click.echo(f"  user config: {user_cfg or '(not found)'}", err=True)
    click.echo(f"  parser: {config.parser}", err=True)
    click.echo(f"  plugins: {config.plugins}", err=True)
    click.echo(f"  stylesheets: {config.stylesheets}", err=True)
    s = config.style
    click.echo(f"  style.font: {s.font or '(default)'}", err=True)
    click.echo(f"  style.font_size: {s.font_size or '(default)'}", err=True)
    click.echo(f"  style.language: {s.language or '(default)'}", err=True)
    click.echo(f"  style.paper: {s.paper or '(default)'}", err=True)
    click.echo(f"  style.margin: {s.margin or '(default)'}", err=True)
    if s.preamble:
        lines = s.preamble.strip().splitlines()
        click.echo(f"  style.preamble: ({len(lines)} lines)", err=True)
    else:
        click.echo("  style.preamble: (empty)", err=True)
    click.echo("---", err=True)


def main() -> None:
    """CLI entry point for md2typst."""

    @click.command()
    @click.argument("input", type=click.Path(exists=True), required=False)
    @click.option(
        "-o", "--output", type=click.Path(), help="Output file (default: <input>.typ)"
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
    @click.option(
        "--stylesheet",
        multiple=True,
        help="Import Typst stylesheet module (can be repeated)",
    )
    @click.option(
        "--class",
        "doc_class",
        default=None,
        help="Document class (article, report, book)",
    )
    @click.option("--list-parsers", is_flag=True, help="List available parsers")
    @click.option("--show-config", is_flag=True, help="Show effective configuration")
    @click.option("--debug", is_flag=True, help="Show debug info (config, sources)")
    @click.version_option(__version__)
    def cli(
        input: str | None,
        output: str | None,
        parser: str | None,
        config_file: str | None,
        plugin: tuple[str, ...],
        stylesheet: tuple[str, ...],
        doc_class: str | None = None,
        list_parsers: bool = False,
        show_config: bool = False,
        debug: bool = False,
    ) -> None:
        """Convert Markdown to Typst.

        INPUT is the Markdown file to convert. Use - for stdin.
        """
        if list_parsers:
            click.echo("Available parsers:")
            for name in get_available_parsers():
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
        if stylesheet:
            cli_overrides["stylesheets"] = list(stylesheet)
        if doc_class:
            cli_overrides["default_class"] = doc_class

        # Load configuration
        config = load_config(
            config_file=Path(config_file) if config_file else None,
            start_dir=start_dir,
            cli_overrides=cli_overrides,
        )

        if debug:
            input_path = Path(input) if input and input != "-" else Path.cwd()
            _print_debug_config(config, input_path)

        if show_config:
            click.echo("Effective configuration:")
            click.echo(f"  parser: {config.parser}")
            click.echo(f"  plugins: {config.plugins}")
            click.echo(f"  stylesheets: {config.stylesheets}")
            click.echo(f"  parser_options: {config.parser_options}")
            click.echo(f"  output_options: {config.output_options}")
            click.echo(f"  style.font: {config.style.font or '(default)'}")
            click.echo(f"  style.language: {config.style.language or '(default)'}")
            click.echo(f"  style.paper: {config.style.paper or '(default)'}")
            click.echo(
                f"  style.preamble: {'yes' if config.style.preamble else '(empty)'}"
            )
            return

        if input is None or input == "-":
            text = sys.stdin.read()
        else:
            with Path(input).open() as f:
                text = f.read()

        result = convert_with_config(text, config)

        # Default output: <input>.typ for file input, stdout for stdin
        if output == "-":
            click.echo(result)
        elif output:
            with Path(output).open("w") as f:
                f.write(result)
        elif input and input != "-":
            out_path = Path(input).with_suffix(".typ")
            with out_path.open("w") as f:
                f.write(result)
            click.echo(f"Wrote {out_path}", err=True)
        else:
            click.echo(result)

    cli()


def main_pdf() -> None:
    """CLI entry point for md2pdf: convert Markdown to PDF via Typst."""

    @click.command()
    @click.argument("input", type=click.Path(exists=True))
    @click.option(
        "-o",
        "--output",
        type=click.Path(),
        help="Output PDF file (default: input with .pdf extension)",
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
    @click.option(
        "--stylesheet",
        multiple=True,
        help="Import Typst stylesheet module (can be repeated)",
    )
    @click.option(
        "--class",
        "doc_class",
        default=None,
        help="Document class (article, report, book)",
    )
    @click.option(
        "--debug", is_flag=True, help="Show debug info (config, Typst source)"
    )
    @click.version_option(__version__)
    def cli(
        input: str,
        output: str | None,
        parser: str | None,
        config_file: str | None,
        plugin: tuple[str, ...],
        stylesheet: tuple[str, ...],
        doc_class: str | None = None,
        debug: bool = False,
    ) -> None:
        """Convert Markdown to PDF via Typst.

        INPUT is the Markdown file to convert.
        """
        input_path = Path(input)
        output_path = Path(output) if output else input_path.with_suffix(".pdf")

        # Build CLI overrides
        cli_overrides: dict[str, Any] = {}
        if parser:
            cli_overrides["parser"] = parser
        if plugin:
            cli_overrides["plugins"] = list(plugin)
        if stylesheet:
            cli_overrides["stylesheets"] = list(stylesheet)
        if doc_class:
            cli_overrides["default_class"] = doc_class

        # Load configuration
        config = load_config(
            config_file=Path(config_file) if config_file else None,
            start_dir=input_path.parent,
            cli_overrides=cli_overrides,
        )

        if debug:
            _print_debug_config(config, input_path)

        # Convert Markdown to Typst
        text = input_path.read_text()
        typst_source = convert_with_config(text, config)

        if debug:
            click.echo("--- Generated Typst source ---", err=True)
            click.echo(typst_source, err=True)
            click.echo("--- End Typst source ---", err=True)

        # Write to a temporary .typ file and compile to PDF
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".typ", dir=input_path.parent, delete=True
        ) as tmp:
            tmp.write(typst_source)
            tmp.flush()

            if debug:
                click.echo(f"Temp file: {tmp.name}", err=True)

            result = subprocess.run(  # noqa: S603
                ["typst", "compile", tmp.name, str(output_path)],  # noqa: S607
                capture_output=True,
                text=True,
                check=False,
            )

        if result.returncode != 0:
            click.echo(f"typst compile failed:\n{result.stderr}", err=True)
            sys.exit(result.returncode)

        if debug:
            click.echo(f"Wrote {output_path}", err=True)

    cli()
