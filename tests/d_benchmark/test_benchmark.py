"""Benchmark tests for parser performance comparison.

Run with: pytest -m benchmark tests/d_benchmark/
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from md2typst import convert
from md2typst.parsers import get_parser

pytestmark = pytest.mark.benchmark

# Sample documents of varying sizes
SMALL_DOC = """# Hello

This is a **paragraph** with *emphasis*.
"""

MEDIUM_DOC = """# Document Title

## Introduction

This is the introduction paragraph with some **bold** and *italic* text.
We also have `inline code` and [links](https://example.com).

## Features

- Feature 1: Description of feature one
- Feature 2: Description of feature two
- Feature 3: Description of feature three
  - Sub-feature A
  - Sub-feature B

### Code Example

```python
def hello():
    print("Hello, World!")
```

## Table

| Column A | Column B | Column C |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |

> This is a blockquote with some important information.

## Conclusion

This is the conclusion with ~~strikethrough~~ text.
"""

LARGE_DOC = MEDIUM_DOC * 10  # Repeat medium doc 10 times


class TestParserBenchmarks:
    """Benchmark tests comparing parser performance."""

    # Small document benchmarks
    def test_markdown_it_small(self, benchmark):
        """Benchmark markdown-it-py with small document."""
        benchmark(convert, SMALL_DOC, parser="markdown-it")

    def test_mistune_small(self, benchmark):
        """Benchmark mistune with small document."""
        benchmark(convert, SMALL_DOC, parser="mistune")

    def test_marko_small(self, benchmark):
        """Benchmark marko with small document."""
        benchmark(convert, SMALL_DOC, parser="marko")

    # Medium document benchmarks
    def test_markdown_it_medium(self, benchmark):
        """Benchmark markdown-it-py with medium document."""
        benchmark(convert, MEDIUM_DOC, parser="markdown-it")

    def test_mistune_medium(self, benchmark):
        """Benchmark mistune with medium document."""
        benchmark(convert, MEDIUM_DOC, parser="mistune")

    def test_marko_medium(self, benchmark):
        """Benchmark marko with medium document."""
        benchmark(convert, MEDIUM_DOC, parser="marko")

    # Large document benchmarks
    def test_markdown_it_large(self, benchmark):
        """Benchmark markdown-it-py with large document."""
        benchmark(convert, LARGE_DOC, parser="markdown-it")

    def test_mistune_large(self, benchmark):
        """Benchmark mistune with large document."""
        benchmark(convert, LARGE_DOC, parser="mistune")

    def test_marko_large(self, benchmark):
        """Benchmark marko with large document."""
        benchmark(convert, LARGE_DOC, parser="marko")


class TestParserInitBenchmarks:
    """Benchmark parser initialization time."""

    def test_markdown_it_init(self, benchmark):
        """Benchmark markdown-it-py parser initialization."""
        benchmark(get_parser, "markdown-it")

    def test_mistune_init(self, benchmark):
        """Benchmark mistune parser initialization."""
        benchmark(get_parser, "mistune")

    def test_marko_init(self, benchmark):
        """Benchmark marko parser initialization."""
        benchmark(get_parser, "marko")


class TestSpecificOperations:
    """Benchmark specific Markdown operations."""

    @pytest.fixture(params=["markdown-it", "mistune", "marko"])
    def parser_name(self, request):
        return request.param

    def test_headings(self, benchmark, parser_name):
        """Benchmark heading parsing."""
        doc = "\n\n".join([f"{'#' * i} Heading {i}" for i in range(1, 7)])
        benchmark(convert, doc, parser=parser_name)

    def test_emphasis(self, benchmark, parser_name):
        """Benchmark emphasis parsing."""
        doc = "\n".join([f"This is *emphasized {i}* text." for i in range(50)])
        benchmark(convert, doc, parser=parser_name)

    def test_lists(self, benchmark, parser_name):
        """Benchmark list parsing."""
        doc = "\n".join([f"- Item {i}" for i in range(100)])
        benchmark(convert, doc, parser=parser_name)

    def test_code_blocks(self, benchmark, parser_name):
        """Benchmark code block parsing."""
        code_block = "```python\nprint('hello')\n```\n\n"
        doc = code_block * 20
        benchmark(convert, doc, parser=parser_name)

    def test_tables(self, benchmark, parser_name):
        """Benchmark table parsing."""
        header = "| A | B | C |\n|---|---|---|\n"
        rows = "\n".join([f"| {i} | {i * 2} | {i * 3} |" for i in range(50)])
        doc = header + rows
        benchmark(convert, doc, parser=parser_name)

    def test_links(self, benchmark, parser_name):
        """Benchmark link parsing."""
        doc = "\n".join([f"[Link {i}](https://example.com/{i})" for i in range(100)])
        benchmark(convert, doc, parser=parser_name)


class TestThroughput:
    """Measure throughput in characters per second."""

    @pytest.fixture(params=["markdown-it", "mistune", "marko"])
    def parser_name(self, request):
        return request.param

    def test_throughput_1k(self, benchmark, parser_name):
        """Measure throughput for ~1KB document."""
        # Create a document that's approximately 1KB
        paragraph = "This is a test paragraph with some text. " * 10
        doc = paragraph * 3  # ~1200 chars

        def run():
            return convert(doc, parser=parser_name)

        _result = benchmark(run)
        # Note: benchmark will measure iterations/sec automatically

    def test_throughput_10k(self, benchmark, parser_name):
        """Measure throughput for ~10KB document."""
        paragraph = "This is a test paragraph with some text. " * 10
        doc = paragraph * 30  # ~12000 chars

        def run():
            return convert(doc, parser=parser_name)

        benchmark(run)


# Utility to generate benchmark comparison report
def generate_report():
    """Generate a markdown report comparing parser performance.

    This is meant to be called manually after running benchmarks:
        pytest tests/test_benchmark.py --benchmark-json=benchmark.json
        python -c "from tests.test_benchmark import generate_report; generate_report()"
    """
    benchmark_file = Path("benchmark.json")
    if not benchmark_file.exists():
        print("No benchmark.json found. Run benchmarks with --benchmark-json first.")
        return

    with benchmark_file.open() as f:
        data = json.load(f)

    print("# Parser Performance Comparison\n")
    print("| Test | Parser | Mean (ms) | StdDev (ms) | Ops/sec |")
    print("|------|--------|-----------|-------------|---------|")

    for bench in sorted(data["benchmarks"], key=lambda x: x["name"]):
        name = bench["name"]
        mean_ms = bench["stats"]["mean"] * 1000
        stddev_ms = bench["stats"]["stddev"] * 1000
        ops_per_sec = bench["stats"]["ops"]
        print(f"| {name} | {mean_ms:.3f} | {stddev_ms:.3f} | {ops_per_sec:.1f} |")
