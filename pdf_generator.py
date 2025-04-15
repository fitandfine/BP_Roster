# pdf_generator.py
"""
This module generates a PDF roster using ReportLab.
The PDF is generated in landscape mode.
"""

from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

def generate_roster_pdf(roster_data, filename="final_roster.pdf"):
    """
    Generates a PDF using the provided roster_data.
    
    :param roster_data: A list of lists representing table rows and columns.
    :param filename: The name for the output PDF file.
    """
    # Create the document using a landscape letter page size
    doc = SimpleDocTemplate(filename, pagesize=landscape(letter))
    table = Table(roster_data)
    
    # Define table style
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),   # Header row background
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),     # Header row text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),                 # Center alignment for all cells
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),       # Bold header font
        ('FONTSIZE', (0, 0), (-1, 0), 14),                     # Header font size
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)            # Add grid lines
    ])
    table.setStyle(style)
    
    # Build the PDF
    doc.build([table])
