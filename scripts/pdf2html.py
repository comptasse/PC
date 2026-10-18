"""Convert PCG source PDFs to HTML.

Usage:
    uv run pdf2html.py [--year YEAR] [--all] [--output-dir DIR]

Examples:
    uv run pdf2html.py --year 2026          # Convert PDFs for a specific year
    uv run pdf2html.py --all                # Convert all PDFs across all years
    uv run pdf2html.py --all --output-dir out  # Specify a custom output directory
"""

from __future__ import annotations

import argparse
import re
import sys
from html import escape
from pathlib import Path

import pymupdf


SOURCES_DIR = Path(__file__).resolve().parent.parent / "PCG" / "sources"

# PDF-internal font names → web-safe CSS font stacks.
# PyMuPDF's get_text("html") emits font-family values like "SymbolMT" or
# "TrebuchetMS" which browsers don't recognise.  We map them to standard
# CSS font stacks.
_FONT_MAP: dict[str, str] = {
    "SymbolMT": "Symbol, 'Noto Sans Symbols', sans-serif",
    "TrebuchetMS": "'Trebuchet MS', Helvetica, sans-serif",
}

# Matches the full font-family declaration in inline CSS (up to the semicolon).
# Group 1 captures the primary font name (before the first comma or semicolon).
_CSS_FONT_RE = re.compile(r"font-family:([^;,]+)[^;]*")

# Matches the opening <p tag so we can inject italic style.
_P_OPEN_RE = re.compile(r"<p\s+style=\"")


def _fix_html_fonts(html: str) -> str:
    """Replace PDF-internal font names with web-safe equivalents in HTML."""

    def _replace_font(m: re.Match[str]) -> str:
        name = m.group(1)
        replacement = _FONT_MAP.get(name)
        if replacement is not None:
            # Replace the entire font-family declaration
            return f"font-family:{replacement}"
        return m.group(0)

    return _CSS_FONT_RE.sub(_replace_font, html)


def _fix_html_positions(page_html: str) -> str:
    """Add position:absolute to <p> elements so they honour top/left."""
    return page_html.replace(
        '<p style="',
        '<p style="position:absolute;margin:0;',
    )


def _detect_sheared_lines(page: pymupdf.Page) -> list[bool]:
    """Detect which text lines use a synthetic italic (shear transform).

    PDF can apply a skew matrix to text (e.g. ``[9.96 0 3.32 9.96 x y] Tm``)
    to fake italic without using an actual italic font.  PyMuPDF's
    ``get_text("html")`` does **not** flag these as italic.

    We detect them by comparing the first character's origin x with its
    bounding-box x0: the shear pushes the bbox leftward, creating a
    measurable offset (> 0.5 pt).

    Returns a flat list of booleans, one per text line across all blocks
    (in the same order as ``rawdict`` blocks → lines), indicating whether
    the line is synthetically italic.  Image blocks are skipped.
    """
    raw_blocks = page.get_text("rawdict")["blocks"]
    result: list[bool] = []

    for block in raw_blocks:
        if block.get("type") != 0:
            # Image or other non-text block — not a line.
            continue
        for line in block["lines"]:
            is_sheared = False
            for span in line["spans"]:
                chars = span.get("chars")
                if not chars:
                    continue
                c0 = chars[0]
                if c0["origin"][0] - c0["bbox"][0] > 0.5:
                    is_sheared = True
                    break
            result.append(is_sheared)

    return result


def _inject_italic(page_html: str, sheared: list[bool]) -> str:
    """Wrap lines flagged as synthetically italic with ``font-style:italic``.

    ``page_html`` is the raw output of ``page.get_text("html")``, with one
    ``<p>`` per text line (in the same order as *sheared*).
    """
    if not any(sheared):
        return page_html

    shear_iter = iter(sheared)

    def _maybe_italicise(m: re.Match[str]) -> str:
        try:
            is_italic = next(shear_iter)
        except StopIteration:
            return m.group(0)
        if is_italic:
            return '<p style="font-style:italic;'
        return m.group(0)

    return _P_OPEN_RE.sub(_maybe_italicise, page_html)


def _build_link_overlays(page: pymupdf.Page, page_num: int) -> list[str]:
    """Create transparent link overlays for internal/external links."""
    overlays: list[str] = []
    for link in page.get_links():
        kind = link.get("kind")
        rect = link.get("from")
        if rect is None:
            continue

        x0, y0, x1, y1 = rect
        w = x1 - x0
        h = y1 - y0

        style = (
            f"position:absolute;"
            f"left:{x0:.1f}pt;top:{y0:.1f}pt;"
            f"width:{w:.1f}pt;height:{h:.1f}pt;"
            f"z-index:1;"
        )

        if kind == pymupdf.LINK_GOTO:
            target_page = link.get("page", 0)
            href = f"#page-{target_page + 1}"
            overlays.append(f'<a href="{href}" style="{style}"></a>')

        elif kind == pymupdf.LINK_URI:
            uri = escape(link.get("uri", ""), quote=True)
            overlays.append(
                f'<a href="{uri}" target="_blank" style="{style}"></a>'
            )

        elif kind == pymupdf.LINK_NAMED:
            name = link.get("name", "")
            if name:
                overlays.append(
                    f'<a href="#{escape(name)}" style="{style}"></a>'
                )

    return overlays


def convert_pdf_to_html(pdf_path: Path, html_path: Path) -> None:
    """Convert a single PDF file to HTML using PyMuPDF text extraction.

    Each page is rendered as a positioned-HTML div with selectable text,
    embedded images, and clickable link overlays.  Synthetic italic
    (shear-matrix text) is detected and preserved.
    """
    doc = pymupdf.open(pdf_path)

    parts: list[str] = [
        "<!DOCTYPE html>",
        '<html lang="fr">',
        "<head>",
        '<meta charset="utf-8">',
        f"<title>{escape(pdf_path.stem)}</title>",
        "<style>",
        "body { margin: 0; background: #f0f0f0; }",
        ".page { position: relative; margin: 20px auto; background: white;"
        " box-shadow: 0 2px 8px rgba(0,0,0,0.15); overflow: hidden; }",
        ".page a { display: block; }",
        ".page p { white-space: pre; }",
        "</style>",
        "</head>",
        "<body>",
    ]

    for page_num in range(len(doc)):
        page = doc[page_num]
        rect = page.rect

        # Detect synthetic-italic lines before getting the HTML.
        sheared = _detect_sheared_lines(page)

        # Get positioned HTML from PyMuPDF (uses pt units, inline styles)
        page_html = page.get_text("html")

        # Strip the wrapper <div id="pageN"> that PyMuPDF generates —
        # we supply our own with the correct id and class.
        page_html = re.sub(
            r'^<div id="page\d+"[^>]*>\s*', "", page_html, count=1
        )
        page_html = re.sub(r"\s*</div>\s*$", "", page_html, count=1)

        # Inject italic for sheared lines, fix fonts and positioning.
        page_html = _inject_italic(page_html, sheared)
        page_html = _fix_html_fonts(page_html)
        page_html = _fix_html_positions(page_html)

        # Build link overlays
        link_overlays = _build_link_overlays(page, page_num)

        parts.append(
            f'<div class="page" id="page-{page_num + 1}"'
            f' style="width:{rect.width:.1f}pt;height:{rect.height:.1f}pt">'
        )
        parts.append(page_html)
        parts.extend(link_overlays)
        parts.append("</div>")

    parts.append("</body>")
    parts.append("</html>")

    doc.close()

    html_path.write_text("\n".join(parts), encoding="utf-8")


def discover_pdfs(year: str | None) -> list[Path]:
    """Find PDF files in the sources directory, optionally filtered by year."""
    if year:
        year_dir = SOURCES_DIR / year
        if not year_dir.is_dir():
            print(
                f"Error: no source directory found for year {year} at {year_dir}",
                file=sys.stderr,
            )
            sys.exit(1)
        return sorted(year_dir.glob("*.pdf"))

    # All years
    return sorted(SOURCES_DIR.rglob("*.pdf"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert PCG source PDFs to HTML.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--year", help="Year to process (e.g. 2026)")
    group.add_argument("--all", action="store_true", help="Process all years")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for HTML files (default: same directory as source PDF)",
    )

    args = parser.parse_args()

    pdfs = discover_pdfs(args.year if not args.all else None)

    if not pdfs:
        print("No PDF files found.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(pdfs)} PDF(s) to convert.\n")

    for pdf_path in pdfs:
        if args.output_dir:
            out_dir = Path(args.output_dir)
            relative = pdf_path.relative_to(SOURCES_DIR)
            html_path = out_dir / relative.with_suffix(".html")
        else:
            html_path = pdf_path.with_suffix(".html")

        html_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"  {pdf_path.relative_to(SOURCES_DIR)} -> {html_path}")
        try:
            convert_pdf_to_html(pdf_path, html_path)
        except Exception as exc:
            print(f"    ERROR: {exc}", file=sys.stderr)
            continue

    print("\nDone.")


if __name__ == "__main__":
    main()
