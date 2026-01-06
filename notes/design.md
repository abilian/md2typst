# md2typst Design and Architecture

## Overview

md2typst converts Markdown documents to Typst format. The design prioritizes:

1. **Parser flexibility** - Support multiple Markdown parsers via abstraction
2. **Correctness** - Validated against CommonMark spec and Pandoc output
3. **Extensibility** - Plugin support for parser-specific extensions

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Markdown      │     │   Intermediate   │     │     Typst       │
│   Input         │────▶│   Representation │────▶│     Output      │
│                 │     │   (AST)          │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                        ▲
        ▼                        │
┌─────────────────┐              │
│  Parser Layer   │──────────────┘
│  (Abstraction)  │
└─────────────────┘
        │
        ▼
┌─────────────────────────────────────────┐
│         Concrete Parsers                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ mistune  │ │ markdown │ │ marko    │ │
│  │          │ │ -it-py   │ │          │ │
│  └──────────┘ └──────────┘ └──────────┘ │
└─────────────────────────────────────────┘
```

## Core Components

### 1. Parser Abstraction Layer

```python
from abc import ABC, abstractmethod
from typing import Any

class MarkdownParser(ABC):
    """Abstract base class for Markdown parsers."""

    @abstractmethod
    def parse(self, text: str) -> "Document":
        """Parse Markdown text into AST."""
        pass

    @abstractmethod
    def configure(self, config: dict[str, Any]) -> None:
        """Apply parser-specific configuration."""
        pass

    @abstractmethod
    def load_plugin(self, plugin: str) -> None:
        """Load a parser-specific plugin/extension."""
        pass
```

**Candidate parsers to support:**

| Parser | Pros | Cons |
|--------|------|------|
| `mistune` | Fast, extensible, pure Python | Less CommonMark compliant |
| `markdown-it-py` | CommonMark compliant, plugin ecosystem | Slower |
| `marko` | CommonMark compliant, extensible | Smaller community |
| `commonmark` | Reference implementation | Limited extensions |

### 2. Intermediate Representation (AST)

A parser-agnostic AST that all parsers convert to. This decouples parsing from code generation.

```python
from dataclasses import dataclass
from typing import Union

@dataclass
class Node:
    """Base AST node."""
    pass

@dataclass
class Document(Node):
    children: list["BlockNode"]

# Block nodes
@dataclass
class Paragraph(Node):
    children: list["InlineNode"]

@dataclass
class Heading(Node):
    level: int  # 1-6
    children: list["InlineNode"]

@dataclass
class CodeBlock(Node):
    code: str
    language: str | None = None

@dataclass
class BlockQuote(Node):
    children: list["BlockNode"]

@dataclass
class List(Node):
    ordered: bool
    start: int | None  # For ordered lists
    items: list["ListItem"]

@dataclass
class ListItem(Node):
    children: list["BlockNode"]

@dataclass
class ThematicBreak(Node):
    pass

# Inline nodes
@dataclass
class Text(Node):
    content: str

@dataclass
class Emphasis(Node):
    children: list["InlineNode"]

@dataclass
class Strong(Node):
    children: list["InlineNode"]

@dataclass
class Code(Node):
    content: str

@dataclass
class Link(Node):
    url: str
    title: str | None
    children: list["InlineNode"]

@dataclass
class Image(Node):
    url: str
    alt: str
    title: str | None = None

@dataclass
class SoftBreak(Node):
    pass

@dataclass
class HardBreak(Node):
    pass

# Type aliases
BlockNode = Union[Paragraph, Heading, CodeBlock, BlockQuote, List, ThematicBreak]
InlineNode = Union[Text, Emphasis, Strong, Code, Link, Image, SoftBreak, HardBreak]
```

### 3. Typst Code Generator

Traverses the AST and emits Typst code.

```python
class TypstGenerator:
    """Generates Typst code from AST."""

    def generate(self, doc: Document) -> str:
        """Convert AST to Typst string."""
        pass

    def visit(self, node: Node) -> str:
        """Dispatch to appropriate visitor method."""
        method = f"visit_{type(node).__name__}"
        return getattr(self, method)(node)
```

**Markdown to Typst mapping:**

| Markdown | Typst |
|----------|-------|
| `# Heading` | `= Heading` |
| `## Heading` | `== Heading` |
| `*emphasis*` | `_emphasis_` |
| `**strong**` | `*strong*` |
| `` `code` `` | `` `code` `` |
| `[text](url)` | `#link("url")[text]` |
| `![alt](url)` | `#image("url", alt: "alt")` |
| `> quote` | `#quote[...]` or `#block[...]` |
| ` ```lang ` | ` ```lang ` |
| `---` | `#line(length: 100%)` |
| `- item` | `- item` |
| `1. item` | `+ item` or `1. item` |

### 4. Configuration System

```python
from dataclasses import dataclass, field

@dataclass
class Config:
    """Runtime configuration."""
    parser: str = "markdown-it-py"  # Default parser
    parser_options: dict = field(default_factory=dict)
    plugins: list[str] = field(default_factory=list)

    # Output options
    typst_options: dict = field(default_factory=dict)
```

Configuration sources (in priority order):
1. CLI arguments
2. Project config file (`.md2typst.toml` or in `pyproject.toml`)
3. Defaults

### 5. CLI Interface

```
md2typst [OPTIONS] INPUT [OUTPUT]

Arguments:
  INPUT   Input Markdown file (- for stdin)
  OUTPUT  Output Typst file (default: stdout)

Options:
  -p, --parser NAME     Parser to use (default: markdown-it-py)
  -c, --config FILE     Configuration file
  --plugin NAME         Load parser plugin (can be repeated)
  -o, --option KEY=VAL  Set parser option (can be repeated)
```

## Module Structure

```
src/md2typst/
├── __init__.py          # CLI entry point, main()
├── cli.py               # Argument parsing
├── config.py            # Configuration loading
├── ast.py               # AST node definitions
├── generator.py         # Typst code generator
├── parsers/
│   ├── __init__.py      # Parser registry, factory
│   ├── base.py          # Abstract parser class
│   ├── mistune.py       # mistune adapter
│   ├── markdown_it.py   # markdown-it-py adapter
│   └── marko.py         # marko adapter
└── plugins/             # Built-in plugin adapters
    └── __init__.py
```

## Error Handling

- **Parse errors**: Report with line/column from source parser
- **Unsupported features**: Warn and emit comment in Typst output
- **Configuration errors**: Fail fast with clear message

## Testing Strategy

1. **Unit tests**: Individual component testing
2. **Integration tests**: End-to-end conversion tests
3. **Validation suite**: CommonMark spec examples with Pandoc-generated expected output
   - Store in `tests/fixtures/commonmark/`
   - Format: `example-NNN.md` + `example-NNN.typ`
   - Manual corrections tracked in `tests/fixtures/corrections.yaml`

## Future Extensions

- **Tables** (GFM extension)
- **Footnotes**
- **Task lists**
- **Math** (LaTeX to Typst math)
- **Front matter** (YAML metadata)
- **Custom directives**
