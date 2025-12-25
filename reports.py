import pandas as pd
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def generate_excel_report(data: list):
    """Senior Logic: Converts list of dicts to an Excel buffer."""
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='KPI_Report')
    return output.getvalue()

def generate_pdf_report(data: list):
    """Senior Logic: Basic PDF generation for achievements."""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 750, "KPI Performance Report")
    y = 700
    for item in data[:20]:  # Limit rows for sample PDF
        text = f"User ID: {item.get('user_id')} | Score: {item.get('score')}"
        p.drawString(100, y, text)
        y -= 20
    p.showPage()
    p.save()
    return buffer.getvalue()