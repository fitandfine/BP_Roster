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
    # Create the document with a landscape letter page size
    doc = SimpleDocTemplate(filename, pagesize=landscape(letter))
    table = Table(roster_data)
    
    # Define the table style
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),   # Header background color
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),     # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),                 # Center align all cells
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),       # Bold header font
        ('FONTSIZE', (0, 0), (-1, 0), 14),                     # Header font size
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)            # Grid lines
    ])
    table.setStyle(style)
    
    # Build the PDF document
    try:
        doc.build([table])
    except Exception as e:
        print("Error generating PDF:", e)

# For testing: Uncomment to generate a sample PDF.
# if __name__ == '__main__':
#     sample_data = [
#         ["Day/Name", "Alice", "Bob", "Weekly Total"],
#         ["Monday", "8", "6", "14"],
#         ["Tuesday", "7", "5", "12"],
#         ["Weekly Total", "15", "11", ""]
#     ]
#     generate_roster_pdf(sample_data, filename="test_roster.pdf")
