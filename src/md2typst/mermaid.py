"""Render Mermaid diagrams to PDF via the official mermaid-cli (``mmdc``).

This is the imperative shell for the ``cli`` mermaid backend. It shells out to
``mmdc`` (mermaid.js in headless Chrome), so diagrams are faithful to the
Mermaid spec -- including HTML labels like ``<b>`` -- unlike the pure-Typst
``mmdr`` package, whose Rust renderer has no ``htmlLabels`` support.

PDF (not SVG) is used deliberately: Typst's SVG renderer cannot draw the
``<foreignObject>`` that Mermaid emits for HTML labels (typst/typst#1421), so a
Chrome-rendered PDF is what preserves them.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


class MermaidCliError(RuntimeError):
    """``mmdc`` is unavailable or failed to render a diagram."""

    @classmethod
    def not_installed(cls) -> MermaidCliError:
        return cls(
            "mermaid-cli (mmdc) not found on PATH; install it with "
            "`npm install -g @mermaid-js/mermaid-cli`, or use the default "
            "--mermaid mmdr backend."
        )

    @classmethod
    def render_failed(cls, detail: str) -> MermaidCliError:
        return cls(f"mmdc failed to render diagram:\n{detail}")


class MermaidCliRenderer:
    """Callable that renders each Mermaid block to a PDF and returns Typst.

    PDFs are written into ``pdf_dir`` as ``<stem>-mermaid-<n>.pdf``; the emitted
    ``#image(...)`` path is relative to ``link_dir`` (the directory the ``.typ``
    lives in) so the output stays portable. Rendered files are tracked in
    ``written`` for callers that want to clean up (e.g. md2pdf).
    """

    def __init__(self, pdf_dir: Path, link_dir: Path, stem: str) -> None:
        mmdc = shutil.which("mmdc")
        if mmdc is None:
            raise MermaidCliError.not_installed()
        self._mmdc = mmdc
        self._pdf_dir = pdf_dir
        self._link_dir = link_dir
        self._stem = stem
        self._count = 0
        self.written: list[Path] = []

    def __call__(self, code: str) -> str:
        self._count += 1
        pdf = self._pdf_dir / f"{self._stem}-mermaid-{self._count}.pdf"
        _run_mmdc(self._mmdc, code, pdf)
        self.written.append(pdf)
        rel = os.path.relpath(pdf, self._link_dir)
        return f'#image("{rel}")'


def _run_mmdc(mmdc: str, code: str, out_pdf: Path) -> None:
    """Render ``code`` to ``out_pdf`` via mmdc; raise MermaidCliError on failure."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as tmp:
        tmp.write(code)
        mmd_path = Path(tmp.name)
    try:
        result = subprocess.run(  # noqa: S603
            [mmdc, "-i", str(mmd_path), "-o", str(out_pdf), "-b", "white"],
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        mmd_path.unlink(missing_ok=True)

    if result.returncode != 0 or not out_pdf.exists():
        raise MermaidCliError.render_failed(result.stderr or result.stdout)
