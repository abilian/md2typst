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
from md2typst.mermaid import MermaidCliError, MermaidCliRenderer
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


def _build_mermaid_renderer(
    config: Config, pdf_dir: Path, stem: str
) -> MermaidCliRenderer | None:
    """Build a mermaid-cli renderer when the ``cli`` backend is selected.

    PDFs are written into (and referenced relative to) ``pdf_dir`` -- the
    directory the ``.typ`` lives in -- so the output stays portable.
    """
    if config.mermaid_backend != "cli":
        return None
    return MermaidCliRenderer(pdf_dir=pdf_dir, link_dir=pdf_dir, stem=stem)


def _convert_one(
    input_path: Path,
    output: str | None,
    config: Config,
    debug: bool,
) -> None:
    """Convert a single Markdown file to Typst."""
    if debug:
        _print_debug_config(config, input_path)

    to_stdout = output == "-"
    out_path = None if to_stdout else Path(output or input_path.with_suffix(".typ"))
    link_dir = out_path.parent if out_path else Path.cwd()
    stem = out_path.stem if out_path else input_path.stem
    render = _build_mermaid_renderer(config, link_dir, stem)

    text = input_path.read_text()
    result = convert_with_config(text, config, mermaid_render=render)

    if out_path is None:
        click.echo(result)
    elif output:
        out_path.write_text(result)
    else:
        out_path.write_text(result)
        click.echo(f"Wrote {out_path}", err=True)


def main() -> None:
    """CLI entry point for md2typst."""

    @click.command()
    @click.argument("inputs", nargs=-1, type=click.Path(exists=True))
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
    @click.option(
        "--mermaid",
        "mermaid_backend",
        type=click.Choice(["mmdr", "cli"]),
        default=None,
        help="Mermaid backend: 'mmdr' (default) or 'cli' (mermaid-cli PDF)",
    )
    @click.option("--list-parsers", is_flag=True, help="List available parsers")
    @click.option("--show-config", is_flag=True, help="Show effective configuration")
    @click.option("--debug", is_flag=True, help="Show debug info (config, sources)")
    @click.version_option(__version__)
    def cli(
        inputs: tuple[str, ...],
        output: str | None,
        parser: str | None,
        config_file: str | None,
        plugin: tuple[str, ...],
        stylesheet: tuple[str, ...],
        doc_class: str | None = None,
        mermaid_backend: str | None = None,
        list_parsers: bool = False,
        show_config: bool = False,
        debug: bool = False,
    ) -> None:
        """Convert Markdown to Typst.

        INPUTS are Markdown files to convert. Reads from stdin if none given.
        """
        if list_parsers:
            click.echo("Available parsers:")
            for name in get_available_parsers():
                click.echo(f"  - {name}")
            return

        if len(inputs) > 1 and output and output != "-":
            click.echo(
                "Error: -o/--output cannot be used with multiple input files.",
                err=True,
            )
            sys.exit(1)

        # Determine start directory for config search
        if inputs:
            start_dir = Path(inputs[0]).parent
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
        if mermaid_backend:
            cli_overrides["mermaid_backend"] = mermaid_backend

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
            click.echo(f"  mermaid_backend: {config.mermaid_backend}")
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

        try:
            if not inputs:
                # stdin mode
                text = sys.stdin.read()
                out_file = Path(output) if output and output != "-" else None
                link_dir = out_file.parent if out_file else Path.cwd()
                stem = out_file.stem if out_file else "diagram"
                render = _build_mermaid_renderer(config, link_dir, stem)
                result = convert_with_config(text, config, mermaid_render=render)
                if out_file:
                    out_file.write_text(result)
                else:
                    click.echo(result)
                return

            for inp in inputs:
                _convert_one(Path(inp), output, config, debug)
        except MermaidCliError as e:
            raise click.ClickException(str(e)) from e

    cli()


def _compile_one_pdf(
    input_path: Path,
    output: str | None,
    config: Config,
    debug: bool,
) -> bool:
    """Convert a single Markdown file to PDF. Returns True on success."""
    output_path = Path(output) if output else input_path.with_suffix(".pdf")

    if debug:
        _print_debug_config(config, input_path)

    # Mermaid PDFs are pre-rendered next to the temp .typ (same directory) so
    # they resolve during compile; they are intermediate, so we delete them after.
    render = _build_mermaid_renderer(config, input_path.parent, output_path.stem)

    text = input_path.read_text()
    typst_source = convert_with_config(text, config, mermaid_render=render)

    if debug:
        click.echo("--- Generated Typst source ---", err=True)
        click.echo(typst_source, err=True)
        click.echo("--- End Typst source ---", err=True)

    try:
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
    finally:
        if render:
            for pdf in render.written:
                pdf.unlink(missing_ok=True)

    if result.returncode != 0:
        click.echo(f"typst compile failed for {input_path}:\n{result.stderr}", err=True)
        return False

    if debug:
        click.echo(f"Wrote {output_path}", err=True)
    return True


def main_pdf() -> None:
    """CLI entry point for md2pdf: convert Markdown to PDF via Typst."""

    @click.command()
    @click.argument("inputs", nargs=-1, type=click.Path(exists=True), required=True)
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
        "--mermaid",
        "mermaid_backend",
        type=click.Choice(["mmdr", "cli"]),
        default=None,
        help="Mermaid backend: 'mmdr' (default) or 'cli' (mermaid-cli PDF)",
    )
    @click.option(
        "--debug", is_flag=True, help="Show debug info (config, Typst source)"
    )
    @click.version_option(__version__)
    def cli(
        inputs: tuple[str, ...],
        output: str | None,
        parser: str | None,
        config_file: str | None,
        plugin: tuple[str, ...],
        stylesheet: tuple[str, ...],
        doc_class: str | None = None,
        mermaid_backend: str | None = None,
        debug: bool = False,
    ) -> None:
        """Convert Markdown to PDF via Typst.

        INPUTS are Markdown files to convert.
        """
        if len(inputs) > 1 and output:
            click.echo(
                "Error: -o/--output cannot be used with multiple input files.",
                err=True,
            )
            sys.exit(1)

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
        if mermaid_backend:
            cli_overrides["mermaid_backend"] = mermaid_backend

        # Load configuration (use first input's directory for config search)
        config = load_config(
            config_file=Path(config_file) if config_file else None,
            start_dir=Path(inputs[0]).parent,
            cli_overrides=cli_overrides,
        )

        failed = False
        try:
            for inp in inputs:
                if not _compile_one_pdf(Path(inp), output, config, debug):
                    failed = True
        except MermaidCliError as e:
            raise click.ClickException(str(e)) from e

        if failed:
            sys.exit(1)

    cli()
