#!/usr/bin/env python3
"""
make_diary_pdf.py — convert the VoiceFront Store Major Project Diary (Weeks 07-12)
markdown into a print-ready A4 PDF (one week per page).

Usage (from anywhere):
    python docs/_planning_audit/make_diary_pdf.py

Reads : 04_MAJOR_PROJECT_DIARY_WEEKS_07-12.md  (same folder as this script)
Writes: 04_MAJOR_PROJECT_DIARY_WEEKS_07-12.pdf (same folder)

Tries three backends, best first; uses whichever is installed:
  1. markdown + weasyprint  (best — real tables/CSS, clean page breaks)
  2. markdown + xhtml2pdf   (good, lighter deps)
  3. reportlab              (pure-Python fallback, basic layout)

This is a documentation helper for producing the diary deliverable — it does not
touch any project source code.
"""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
MD = HERE / "04_MAJOR_PROJECT_DIARY_WEEKS_07-12.md"
PDF = HERE / "04_MAJOR_PROJECT_DIARY_WEEKS_07-12.pdf"

CSS = """
@page { size: A4; margin: 18mm 16mm; }
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', 'DejaVu Sans', Arial, sans-serif; font-size: 10.5pt;
       line-height: 1.42; color: #1b1b1b; }
h1 { font-size: 17pt; margin: 0 0 6pt; }
h2 { font-size: 13.5pt; margin: 0 0 6pt; padding-top: 2pt;
     border-bottom: 1.5px solid #333; page-break-before: always; }
h2:first-of-type { page-break-before: avoid; }
h3 { font-size: 11.5pt; margin: 10pt 0 4pt; }
p  { margin: 4pt 0; }
ul, ol { margin: 3pt 0 6pt 18pt; padding: 0; }
li { margin: 1.5pt 0; }
em { color: #444; }
code { font-family: 'Consolas','DejaVu Sans Mono',monospace; background:#f3f3f3;
       padding:0 2px; border-radius:3px; font-size:9.5pt; }
hr { border: 0; border-top: 1px solid #ccc; margin: 8pt 0; }
blockquote { margin: 6pt 0; padding: 4pt 10pt; border-left: 3px solid #bbb;
             background: #f7f7f7; color: #333; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0; font-size: 9.5pt; }
th, td { border: 1px solid #999; padding: 3pt 5pt; text-align: left; vertical-align: top; }
th { background: #efefef; }
"""


def md_to_html(md_text: str) -> str:
    import markdown  # may raise ImportError -> caller moves to next backend
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "sane_lists"])
    return (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<style>{CSS}</style></head><body>{body}</body></html>")


def via_weasyprint(md_text: str) -> bool:
    from weasyprint import HTML
    HTML(string=md_to_html(md_text)).write_pdf(str(PDF))
    return True


def via_xhtml2pdf(md_text: str) -> bool:
    from xhtml2pdf import pisa
    with open(PDF, "wb") as f:
        result = pisa.CreatePDF(md_to_html(md_text), dest=f)
    return not result.err


def via_reportlab(md_text: str) -> bool:
    import re
    import html as _html
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    PageBreak, Table, TableStyle, HRFlowable)

    def inline(t: str) -> str:
        t = _html.escape(t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        t = re.sub(r"`(.+?)`", r'<font face="Courier">\1</font>', t)
        t = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", t)
        return t

    styles = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=10, leading=13.5)
    h1 = ParagraphStyle("h1", parent=styles["Title"], fontSize=16, spaceAfter=6)
    h2 = ParagraphStyle("h2", parent=styles["Heading1"], fontSize=13, spaceBefore=4, spaceAfter=4)
    h3 = ParagraphStyle("h3", parent=styles["Heading2"], fontSize=11, spaceBefore=6, spaceAfter=3)
    quote = ParagraphStyle("quote", parent=body, leftIndent=10, textColor=colors.HexColor("#444"))

    doc = SimpleDocTemplate(str(PDF), pagesize=A4,
                            leftMargin=16 * mm, rightMargin=16 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm,
                            title="VoiceFront Store - Major Project Diary (Weeks 07-12)")
    story = []
    table_buf: list[str] = []
    first_h2 = True

    def flush_table():
        nonlocal table_buf
        if not table_buf:
            return
        rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in table_buf]
        rows = [r for r in rows if not all(set(c) <= set("-: ") for c in r)]
        data = [[Paragraph(inline(c), body) for c in r] for r in rows]
        if data:
            t = Table(data, hAlign="LEFT")
            t.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#efefef")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            story.append(t)
            story.append(Spacer(1, 6))
        table_buf = []

    for raw in md_text.splitlines():
        line = raw.rstrip("\n")
        if line.lstrip().startswith("|") and line.rstrip().endswith("|"):
            table_buf.append(line)
            continue
        flush_table()
        s = line.strip()
        if not s:
            story.append(Spacer(1, 4)); continue
        if s.startswith("# "):
            story.append(Paragraph(inline(s[2:]), h1)); continue
        if s.startswith("## "):
            if not first_h2:
                story.append(PageBreak())
            first_h2 = False
            story.append(Paragraph(inline(s[3:]), h2)); continue
        if s.startswith("### "):
            story.append(Paragraph(inline(s[4:]), h3)); continue
        if s.startswith("---"):
            story.append(HRFlowable(width="100%", color=colors.HexColor("#cccccc"),
                                    spaceBefore=4, spaceAfter=4)); continue
        if s.startswith(">"):
            story.append(Paragraph(inline(s.lstrip(">").strip()), quote)); continue
        m = re.match(r"^(\d+)\.\s+(.*)", s)
        if m:
            story.append(Paragraph(f"{m.group(1)}.&nbsp;&nbsp;{inline(m.group(2))}", body)); continue
        if s.startswith("- ") or s.startswith("* "):
            story.append(Paragraph(f"&bull;&nbsp;&nbsp;{inline(s[2:])}", body)); continue
        story.append(Paragraph(inline(s), body))

    flush_table()
    doc.build(story)
    return True


def main() -> int:
    if not MD.exists():
        print(f"ERROR: diary markdown not found at {MD}")
        return 2
    md_text = MD.read_text(encoding="utf-8")
    for name, fn in (("weasyprint", via_weasyprint),
                     ("xhtml2pdf", via_xhtml2pdf),
                     ("reportlab", via_reportlab)):
        try:
            if fn(md_text):
                print(f"OK: wrote {PDF}  (backend: {name})")
                return 0
        except ImportError as e:
            print(f"[{name}] not available: {e}")
        except Exception as e:
            print(f"[{name}] failed: {e}")
    print("\nNo PDF backend available. Install one of these, then re-run:")
    print("   pip install markdown weasyprint   # best (tables + CSS)")
    print("   pip install markdown xhtml2pdf     # lighter fallback")
    print("   pip install reportlab              # basic fallback")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
