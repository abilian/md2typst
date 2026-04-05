# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Style configuration system**: New `[style]` section in config files for customizing Typst output defaults
  - Fields: `font` (string or list for fallback), `font_size`, `language`, `paper`, `margin`, `preamble`
  - Translated to `#set text(...)` and `#set page(...)` directives automatically
  - Font fallback lists are emitted as Typst tuples, e.g. `font: ("Libertinus Serif", "New Computer Modern")`

- **User-level config file**: `~/.config/md2typst/config.toml` (via `platformdirs`, cross-platform)
  - Lowest priority after built-in defaults
  - Purpose: set your preferred default styling (font, language, page setup) once for all documents

- **Extended cascade ordering** (lowest to highest priority):
  1. Built-in defaults
  2. User config (`~/.config/md2typst/config.toml`)
  3. `pyproject.toml` `[tool.md2typst]`
  4. `md2typst.toml` (searched up from input)
  5. Explicit `--config file.toml`
  6. Front matter in the document
  7. CLI flags

- **Front matter style overrides**: Style fields can be set directly in YAML front matter
  - Keys: `font`, `font_size`, `language`, `paper`, `margin`
  - These override the config `[style]` section at the document level
  - Config `style.preamble` and front matter `preamble` are concatenated (config first)

### Changed

- **Added `platformdirs` dependency** for cross-platform user config directory discovery

## [0.3.1] - 2026-04-03

### Fixed

- **Missing dependency**: Added `mdit-py-plugins` to package dependencies (required for math support via dollarmath plugin)

## [0.3.0] - 2026-04-03

### Added

- **Mermaid diagram support**: ```` ```mermaid ```` code blocks are converted to `#mermaid("...")` calls using the [mmdr](https://typst.app/universe/package/mmdr/) Typst package
  - Supported by all three parsers (markdown-it, mistune, marko)
  - New `MermaidBlock` AST node
  - Package import (`#import "@preview/mmdr:0.2.1": mermaid`) is auto-generated when Mermaid blocks are present

- **Auto-import of Typst packages**: Required package imports are now automatically prepended based on AST content
  - `mitex` for math expressions (`MathInline`, `MathBlock`)
  - `mmdr` for Mermaid diagrams (`MermaidBlock`)

- **Math enabled by default**: Dollar-sign math syntax (`$...$` and `$$...$$`) is now parsed out of the box
  - markdown-it: dollarmath plugin loaded automatically
  - mistune: math plugin loaded automatically
  - marko: not supported (no math extension)

### Fixed

- **Updated mitex package** from 0.2.0 to 0.2.6, fixing `duplicate key: int` error at compile time

## [0.2.5] - 2026-04-03

### Changed

- **Default output to file**: `md2typst input.md` now writes `input.typ` by default (previously wrote to stdout). Use `-o -` to output to stdout. Consistent with `md2pdf` behavior.
- **Refactored CLI into separate module**: Split `__init__.py` into `cli.py` (CLI entry points) and `converter.py` (conversion logic). Public API unchanged.
- **Version from package metadata**: Version is now read via `importlib.metadata` instead of being hardcoded.

## [0.2.4] - 2026-03-27

### Added

- **`md2pdf` command**: Convert Markdown directly to PDF via Typst
  - Runs `md2typst` then `typst compile` in sequence
  - Uses a temporary `.typ` file (automatically cleaned up)
  - Output defaults to input filename with `.pdf` extension
  - Supports all `md2typst` options (`--parser`, `--plugin`, `--stylesheet`, `--config`)

- **Front matter preamble**: Include raw Typst code via `preamble:` in YAML front matter
  - Supports `#set`, `#show`, and any Typst declarations
  - Inserted after stylesheet imports, before document content
  - Output ordering: variables → imports → preamble → content

### Fixed

- Soft breaks now produce Typst linebreaks (`\`), preserving single newlines from the source as visible line breaks in the rendered output

## [0.2.2] - 2025-02-12

### Added

- **YAML front matter support**: Extract metadata from Markdown files
  - Parses YAML between `---` delimiters at document start
  - Generates Typst variables (`#let doc-title = "..."`)
  - Supports strings, numbers, booleans, lists, and null values
  - Keys with underscores/spaces converted to hyphens (`my_key` → `doc-my-key`)

- **Stylesheet imports**: Import Typst modules for styling
  - CLI option: `--stylesheet NAME` (can be used multiple times)
  - Config file: `stylesheets = ["style1", "style2"]`
  - Front matter: `stylesheet: my-style` or `stylesheets: [style1, style2]`
  - Generates `#import "name.typ": *` statements

- **Preamble support**: Include raw Typst code in front matter
  - Use `preamble: |` in front matter for multi-line Typst code
  - Inserted after imports, before document content
  - Enables `#show: apply-style` pattern for template functions

### Fixed

- Fixed parentheses after links causing Typst syntax errors
  - `[link](url)(text)` now correctly escapes the opening parenthesis

## [0.2.1] - 2025-02-12

### Added

- **Index entries support**: Mark terms for inclusion in a document index (markdown-it only)
  - New AST node: `IndexEntry(term, subterm, see)`
  - Pandoc-style syntax: `[Python]{.index}` or `[text]{.index key="Term!Subterm"}`
  - Generator produces Typst `#index("term")` or `#index("term", "subterm")`
  - Requires `mdit_py_plugins.attrs` plugin with markdown-it parser

- **Math support**: LaTeX math syntax with pass-through to Typst's mitex package
  - New AST nodes: `MathInline` and `MathBlock`
  - Inline math (`$...$`) outputs `#mi("...")`
  - Display math (`$$...$$`) outputs `#mitex(`...`)`
  - Parser support:
    - markdown-it-py: `mdit_py_plugins.dollarmath`
    - mistune: `math` plugin
    - marko: Not supported (no math extension)
  - Requires `#import "@preview/mitex:0.2.0": *` in Typst document

### Fixed

- Fixed table generation producing invalid Typst markup.

## [0.2.0] - 2025-01-06

### Added

- **Footnotes support**: Full support for Markdown footnotes across all three parsers
  - New AST nodes: `FootnoteRef` (inline reference) and `FootnoteDef` (block definition)
  - Generator produces Typst `#footnote[...]` output
  - Supports named footnotes (`[^note]`) and numbered footnotes (`[^1]`)
  - Supports multi-paragraph footnotes
  - Parser plugins:
    - markdown-it-py: `mdit_py_plugins.footnote`
    - mistune: `footnotes` (built-in)
    - marko: `footnote` (built-in)

- **Endnotes support**: Alternative to footnotes that collects notes at end of document
  - Configure via `output_options.note_style = "endnote"` in config file
  - Or via API: `generate_typst(doc, note_style="endnote")`
  - Produces superscript references (`#super[1]`) and a "Notes" section with numbered list
  - Repeated references to the same note use the same number

- Added `mdit-py-plugins` as a dev dependency for footnote support

- New integration tests:
  - `tests/b_integration/test_footnotes.py` - footnote parsing and generation

### Changed

- AST dataclasses are now frozen (`@dataclass(frozen=True)`) with tuple fields for immutability
- Updated `_visit_children_inline` to accept `tuple[Node, ...]` instead of `list[Node]`
- `convert()` function now accepts `output_options` parameter for generator configuration
- `convert_with_config()` now passes `output_options` from config to the generator

### Fixed

- Fixed various typing issues with tuple vs list arguments
- Fixed empty children initialization to use tuples (`()`) instead of lists (`[]`)

## [0.1.0] - 2025-01-01

### Added

- Initial release
- Core Markdown to Typst conversion
- Support for three Markdown parsers:
  - markdown-it-py (default, CommonMark compliant)
  - mistune (fast, pure Python)
  - marko (CommonMark compliant)
- Parser-agnostic AST representation
- Typst code generator with visitor pattern
- GFM extensions support:
  - Tables with column alignment
  - Strikethrough (`~~text~~`)
- Configuration system:
  - CLI arguments
  - TOML config files (`md2typst.toml`)
  - pyproject.toml `[tool.md2typst]` section
- Comprehensive test suite:
  - Unit tests
  - Integration tests
  - End-to-end tests
  - Property-based testing with Hypothesis
  - TCK (Technology Compatibility Kit) for spec compliance
  - Benchmarks

### Supported Markdown Elements

- Headings (levels 1-6)
- Paragraphs
- Emphasis (italic) and strong (bold)
- Inline code and code blocks with syntax highlighting
- Links and images
- Block quotes
- Ordered and unordered lists
- Thematic breaks (horizontal rules)
- Hard and soft line breaks
- HTML blocks and inline HTML (preserved as comments)
