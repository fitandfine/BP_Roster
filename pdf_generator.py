# pdf_generator.py  ─────────────────────────────────────────────────────────
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

def generate_roster_pdf(table_data, *, filename, title=None):
    """
    table_data : list[list[str]]
        A 2‑D array of strings already prepared by dashboard.py
        (the first row may be a one‑cell title – see below).
    filename   : str
        Target PDF file (will be overwritten).
    title      : str | None
        Optional document title; drawn in bold above the table.
    """
    doc  = SimpleDocTemplate(
        filename,
        pagesize=landscape(A4),
        rightMargin=20, leftMargin=20,
        topMargin=25,  bottomMargin=25
    )

    story = []
    styles = getSampleStyleSheet()

    if title:                                        # top‑of‑page title
        story.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
        story.append(Spacer(1, 12))                  # 12 pt gap

    # Detect a single‑cell title row (the patch in dashboard.py adds it)
    first_row_is_heading = (
        len(table_data) > 0
        and len(set(map(len, table_data))) == 1      # all rows equal length
        and any(table_data[0][1:]) is False          # only first cell populated
    )

    tbl = Table(table_data)

    ts  = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),   # Header background color
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),     # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),                 # Center align all cells
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),       # Bold header font
        ('FONTSIZE', (0, 0), (-1, 0), 14),                     # Header font size
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)            # Grid lines
    ])

    if first_row_is_heading:
        n_cols = len(table_data[0])
        ts.add("SPAN",  (0, 0), (n_cols - 1, 0))     # span the heading row
        ts.add("BACKGROUND", (0, 0), (0, 0), colors.lightgrey)
        ts.add("ALIGN",      (0, 0), (0, 0), "CENTER")
        ts.add("FONTSIZE",   (0, 0), (0, 0), 12)
        ts.add("BOTTOMPADDING", (0, 0), (0, 0), 6)

    tbl.setStyle(ts)
    story.append(tbl)
    doc.build(story)
