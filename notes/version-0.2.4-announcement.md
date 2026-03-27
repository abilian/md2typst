Announcing **md2typst** 0.2.4 — an open-source Markdown to Typst converter in Python.

[Typst](https://typst.app/) is a modern typesetting system designed as a faster, more approachable alternative to LaTeX. It compiles documents almost instantly and uses a clean, readable markup language for producing professional PDFs — research papers, reports, books, slide decks, and more.

**md2typst** bridges the gap between Markdown — the lingua franca of technical writing — and Typst's powerful typesetting engine. Write in Markdown, get publication-quality PDFs.

Key features:

- **3 parser backends** (markdown-it-py, mistune, marko) — choose the one that fits your needs
- **YAML front matter** — define metadata, stylesheets, and raw Typst preamble (`#set`, `#show` rules) directly in your Markdown files
- **`md2pdf` command** — one-step Markdown to PDF conversion via Typst
- **GFM support** — tables, strikethrough, footnotes, math (LaTeX pass-through), and more
- **Configurable** — TOML config files, CLI options, or Python API

Example workflow:

```
md2pdf report.md
```

That's it. Markdown in, PDF out.

The project is available on PyPI (`pip install md2typst`) and on GitHub:
https://github.com/abilian/md2typst

Feedback and contributions welcome!

#opensource #python #typst #markdown #typesetting #devtools
