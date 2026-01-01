# md2typst

A robust Markdown to [Typst](https://typst.app/) converter in Python with support for multiple Markdown parsers.

## Features

- **Multiple parser backends**: Choose from markdown-it-py, mistune, or marko at runtime
- **GFM support**: Tables, strikethrough, and other GitHub Flavored Markdown extensions
- **Configurable**: TOML configuration files and CLI options
- **Extensible**: Plugin support for parser-specific extensions
- **Well-tested**: Comprehensive test suite with TCK validation against CommonMark

## Installation

```bash
# Using pip
pip install md2typst

# Using uv
uv add md2typst
```

## Quick Start

### Command Line

```bash
# Convert a file
md2typst input.md -o output.typ

# Convert from stdin
echo "# Hello **World**" | md2typst

# Use a specific parser
md2typst --parser mistune input.md

# List available parsers
md2typst --list-parsers
```

### Python API

```python
from md2typst import convert

# Simple conversion
typst = convert("# Hello **World**")
print(typst)
# Output: = Hello *World*

# With specific parser
typst = convert("~~deleted~~", parser="mistune")
print(typst)
# Output: #strike[deleted]

# With configuration
from md2typst import convert_with_config
from md2typst.config import Config

config = Config(parser="marko", plugins=["gfm"])
typst = convert_with_config("| A | B |\n|---|---|\n| 1 | 2 |", config)
```

## Supported Parsers

| Parser | CLI Name | Description |
|--------|----------|-------------|
| [markdown-it-py](https://github.com/executablebooks/markdown-it-py) | `markdown-it` | Default. CommonMark compliant, extensible |
| [mistune](https://github.com/lepture/mistune) | `mistune` | Fast, pure Python |
| [marko](https://github.com/frostming/marko) | `marko` | CommonMark compliant, extensible |

All parsers have GFM extensions (tables, strikethrough) enabled by default.

## Markdown to Typst Mapping

| Markdown | Typst |
|----------|-------|
| `# Heading` | `= Heading` |
| `## Heading 2` | `== Heading 2` |
| `*italic*` | `_italic_` |
| `**bold**` | `*bold*` |
| `~~strike~~` | `#strike[strike]` |
| `` `code` `` | `` `code` `` |
| `[text](url)` | `#link("url")[text]` |
| `![alt](url)` | `#image("url", alt: "alt")` |
| `> quote` | `#block(...)[quote]` |
| `---` | `#line(length: 100%)` |
| GFM tables | `#table(...)` |

## Configuration

Configuration is loaded from multiple sources (highest priority first):

1. CLI arguments (`--parser`, `--plugin`)
2. Explicit config file (`--config path/to/config.toml`)
3. `.md2typst.toml` in the current or parent directories
4. `[tool.md2typst]` section in `pyproject.toml`

### Example Configuration

**.md2typst.toml**:
```toml
parser = "mistune"
plugins = ["strikethrough", "table"]

[parser_options]
html = true
```

**pyproject.toml**:
```toml
[tool.md2typst]
parser = "markdown-it"
plugins = ["gfm"]
```

### CLI Options

```bash
md2typst --help

Options:
  -o, --output FILE      Output file (default: stdout)
  -p, --parser NAME      Parser to use (markdown-it, mistune, marko)
  --plugin NAME          Load parser plugin (can be repeated)
  --config FILE          Path to configuration file
  --list-parsers         List available parsers
  --show-config          Show effective configuration
```

## Development

### Setup

```bash
git clone https://github.com/user/md2typst.git
cd md2typst
uv sync
```

### Running Tests

```bash
# Run all tests (benchmarks skipped by default)
uv run pytest

# Run by category
uv run pytest -m unit          # Unit tests (fast)
uv run pytest -m integration   # Integration tests
uv run pytest -m e2e          # End-to-end tests
uv run pytest -m benchmark    # Benchmark tests
```

### Test Structure

```
tests/
├── a_unit/           # Unit tests (AST, generator)
├── b_integration/    # Integration tests (parsers, config, TCK)
├── c_e2e/           # End-to-end tests
├── d_benchmark/     # Performance benchmarks
└── fixtures/        # Test fixtures (CommonMark, GFM)
```

### Code Quality

```bash
# Type checking
uv run mypy src/

# Linting
uv run ruff check src/

# Formatting
uv run ruff format src/
```

## Architecture

```
Markdown Input → Parser → AST → Generator → Typst Output
```

The converter uses a parser-agnostic AST (Abstract Syntax Tree) that decouples parsing from code generation. This allows:

- Swapping parsers without changing the generator
- Consistent output regardless of parser choice
- Easy extension with new parsers

## License

MIT

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request
