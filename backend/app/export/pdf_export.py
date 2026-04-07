"""
Shared PDF export — generate a PDF document from markdown content.

Parameterized by a `theme` dataclass so both the Profile (blue) and
Transparency (green) endpoints can reuse the same logic.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass

from fastapi.responses import Response


# ── Theme configuration ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class PdfTheme:
    """Colour / label overrides for a PDF export."""

    header_label: str = "PIM Country Briefing"
    title_prefix: str = "Public Investment Management Context"
    filename_prefix: str = "PIM_Profile"
    # RGB tuples (0-255)
    accent_rgb: tuple[int, int, int] = (29, 78, 216)   # blue


PROFILE_THEME = PdfTheme()

TRANSPARENCY_THEME = PdfTheme(
    header_label="PIM Transparency Briefing",
    title_prefix="PIM Transparency Briefing",
    filename_prefix="PIM_Transparency",
    accent_rgb=(14, 124, 71),
)


# ── Public API ───────────────────────────────────────────────────────────────

def export_pdf(content: str, country_name: str, theme: PdfTheme = PROFILE_THEME) -> Response:
    """Generate a PDF from markdown *content* and return a FastAPI Response."""
    from fpdf import FPDF

    country_name = _sanitize_for_pdf(country_name)
    content = _sanitize_for_pdf(content)

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()

    r, g, b = theme.accent_rgb

    # Header
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 5, f"{theme.header_label} - {country_name}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(r, g, b)
    pdf.cell(0, 10, f"{theme.title_prefix}: {country_name}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(r, g, b)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)
    pdf.set_text_color(0, 0, 0)

    lines = content.split("\n")
    i = 0
    table_rows: list[list[str]] = []
    in_table = False

    while i < len(lines):
        line = lines[i]

        if line.startswith("## "):
            if in_table and table_rows:
                _add_table_to_pdf(pdf, table_rows, theme)
                table_rows, in_table = [], False
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 7, line[3:].strip(), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

        elif line.startswith("### "):
            if in_table and table_rows:
                _add_table_to_pdf(pdf, table_rows, theme)
                table_rows, in_table = [], False
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, line[4:].strip(), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)

        elif line.strip().startswith("|") and line.strip().endswith("|"):
            if re.match(r"^\|[\s\-:|]+\|$", line.strip()):
                i += 1
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            table_rows.append(cells)
            in_table = True

        elif line.strip().startswith("- ") or line.strip().startswith("* "):
            if in_table and table_rows:
                _add_table_to_pdf(pdf, table_rows, theme)
                table_rows, in_table = [], False
            text = re.sub(r"\*\*(.*?)\*\*", r"\1", line.strip().lstrip("-* ").strip())
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(5, 5, chr(8226))
            pdf.multi_cell(0, 5, f" {text}", new_x="LMARGIN", new_y="NEXT")

        elif line.strip():
            if in_table and table_rows:
                _add_table_to_pdf(pdf, table_rows, theme)
                table_rows, in_table = [], False
            text = re.sub(r"\*\*(.*?)\*\*", r"\1", line.strip())
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(0, 5, text, new_x="LMARGIN", new_y="NEXT")

        else:
            if in_table and table_rows:
                _add_table_to_pdf(pdf, table_rows, theme)
                table_rows, in_table = [], False
            pdf.ln(2)

        i += 1

    if table_rows:
        _add_table_to_pdf(pdf, table_rows, theme)

    # Footer
    pdf.set_y(-15)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 10, f"Page {pdf.page_no()}", align="C")

    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)

    filename = f"{theme.filename_prefix}_{country_name.replace(' ', '_')}.pdf"
    return Response(
        content=buf.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Helpers ──────────────────────────────────────────────────────────────────

def _sanitize_for_pdf(text: str) -> str:
    """Replace Unicode characters unsupported by fpdf2 built-in fonts (Latin-1)."""
    replacements = {
        "\u2014": "--",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "\u2022": "-",
        "\u00a0": " ",
        "\u200b": "",
    }
    for char, repl in replacements.items():
        text = text.replace(char, repl)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _add_table_to_pdf(pdf, rows: list[list[str]], theme: PdfTheme):
    """Add a table to the PDF."""
    if not rows:
        return

    r, g, b = theme.accent_rgb
    num_cols = max(len(r_) for r_ in rows)
    page_width = pdf.w - pdf.l_margin - pdf.r_margin
    col_width = page_width / num_cols

    for row_idx, row_data in enumerate(rows):
        if row_idx == 0:
            pdf.set_fill_color(r, g, b)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Helvetica", "B", 8)
        else:
            pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 8)

        row_height = 6
        for col_idx in range(num_cols):
            cell_text = row_data[col_idx] if col_idx < len(row_data) else ""
            clean = re.sub(r"\*\*(.*?)\*\*", r"\1", cell_text)
            lines_needed = max(1, len(clean) // int(col_width / 2) + 1)
            row_height = max(row_height, lines_needed * 5)

        x_start = pdf.get_x()
        y_start = pdf.get_y()

        if y_start + row_height > pdf.h - pdf.b_margin:
            pdf.add_page()
            y_start = pdf.get_y()

        for col_idx in range(num_cols):
            cell_text = row_data[col_idx] if col_idx < len(row_data) else ""
            clean = re.sub(r"\*\*(.*?)\*\*", r"\1", cell_text)
            pdf.set_xy(x_start + col_idx * col_width, y_start)
            pdf.multi_cell(
                col_width, 5, clean,
                border=1,
                fill=(row_idx == 0),
                new_x="RIGHT", new_y="TOP",
            )

        pdf.set_xy(x_start, y_start + row_height)

    pdf.ln(4)
