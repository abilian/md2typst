# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

- **Index entries support**: Mark terms for inclusion in a document index (markdown-it only)
  - New AST node: `IndexEntry(term, subterm, see)`
  - Pandoc-style syntax: `[Python]{.index}` or `[text]{.index key="Term!Subterm"}`
  - Generator produces Typst `#index("term")` or `#index("term", "subterm")`
  - Requires `mdit_py_plugins.attrs` plugin with markdown-it parser

- Added `mdit-py-plugins` as a dev dependency for footnote and index entry support

- New integration tests:
  - `tests/b_integration/test_footnotes.py` - footnote parsing and generation
  - `tests/b_integration/test_index.py` - index entry parsing and generation

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
  - TOML config files (`.md2typst.toml`)
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
