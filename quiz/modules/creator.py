
import datetime
from pathlib import Path

from django.conf import settings
from weasyprint import HTML


PDF_NAME = str("test") + ".pdf"

def create_pdf(html: str):
    """HTMLをPDFに変換して保存する関数.  
    
    Args:
        html (str): PDFに変換するHTMLの文字列.
    """
    HTML(
        string=html, 
        base_url=settings.BASE_DIR
    ).write_pdf(
        Path(settings.OUTPUT_PDF_DIR, PDF_NAME)
    )